<template>
<BsTab
            name="One Way Variable"
            docTitle="GLM Analyzer"
            :docIcon="docLogo"
        >
            <BsTabIcon>
                <img :src="oneWayIcon" alt="Target Definition Icon" />
            </BsTabIcon>
            <BsHeader>
                <BsButton
                    v-if="!layoutRef?.drawerOpen"
                    flat
                    round
                    class="open-side-drawer-btn"
                    size="15px"
                    @click="closeSideDrawer"
                    icon="mdi-arrow-right"
                >
                    <BsTooltip>Open sidebar</BsTooltip>
                </BsButton>
            </BsHeader>
            <BsDrawer>
              <div class="variable-select-container">
               <BsLabel
                  label="Select a model"
                  info-text="Charts will be generated with respect to this model">
               </BsLabel>
              <BsSelect
                  :modelValue="selectedModelString"
                  :all-options="modelsString"
                  @update:modelValue="updateModelString"
                  >
                  </BsSelect>
              <div v-if="selectedModelString" class="button-container">
              <BsButton
                  class="bs-primary-button" 
                  unelevated
                  dense
                  no-caps
                  padding="4"
                  @click="onClick">Export Full Model</BsButton>
                </div>
              <BsCheckbox v-if="selectedModelString" v-model="includeSuspectVariables" label="Include Suspect Variables">
              </BsCheckbox>
              <BsLabel v-if="selectedModelString"
                  label="Select a Variable"
                  info-text="Charts will be generated with respect to this variable">
               </BsLabel>
                <BsSelect
                  v-if="selectedModelString"
                      v-model="selectedVariable"
                      :all-options="variablePoints"
                      @update:modelValue="updateVariable">
                      <template v-slot:selected-item="scope">
                        <q-item v-if="scope.opt">
                          {{ selectedVariable.variable }}
                        </q-item>
                    </template>
                          <template #option="props">
                              <q-item v-if="props.opt.isInModel || includeSuspectVariables" v-bind="props.itemProps" clickable>
                                  <q-item-section side>
                                    <div v-if="props.opt.isInModel">selected</div>
                                    <div v-else>unselected</div>
                                  </q-item-section>
                                <q-item-section class="bs-font-medium-2-normal">
                                    {{ props.opt.variable }}
                                </q-item-section>
                              </q-item>
                        </template>
                  </BsSelect>
                  <BsCheckbox v-model="rescale" v-if="selectedModelString"
                  @update:modelValue="updateRescale" 
                  label="Rescale?"></BsCheckbox>
                  <BsLabel v-if="selectedModelString"
                    label="Run Analysis on">
                  </BsLabel>
                  <BsToggle v-if="selectedModelString" 
                  v-model="trainTest"
                  @update:modelValue="updateTrainTest"
                  labelRight="Test" 
                  labelLeft="Train"/>
                  <div v-if="selectedVariable.variable" class="button-container">
                    <BsButton class="bs-primary-button" 
                    unelevated
                    dense
                    no-caps
                    padding="4"
                    @click="onClickOneWay">Export One-Way Data</BsButton>
                  </div>
                </div>
                <BsButton
                    flat
                    round
                    class="close-side-drawer-btn"
                    size="15px"
                    @click="closeSideDrawer"
                    icon="mdi-arrow-left">
                    <BsTooltip>Close sidebar</BsTooltip>
                </BsButton>
            </BsDrawer>
            <BsContent>
              <EmptyState
                    class="tab-content"
                    title="One-Way Variable"
                    subtitle="Select variable in the left column to create chart"
                    v-if="chartData.length==0"/>
                <div class="tab-content" v-else>
                    <BarChart
                      v-if="selectedVariable"
                      :xaxisLabels="chartData.map(item => ((selectedVariable.variableType == 'categorical') ? item.Category : Number(item.Category)))"
                      :xaxisType="selectedVariable.variableType"
                      :barData="chartData.map(item => item.Value)"
                      :observedAverageLine="chartData.map(item => item.observedAverage)"
                      :fittedAverageLine="chartData.map(item => item.fittedAverage)"
                      :baseLevelPredictionLine="chartData.map(item => item.baseLevelPrediction)"
                      :chartTitle="selectedVariable.variable"
                      />
                    <BsTable v-if="selectedVariable.isInModel"
                      :title="selectedVariable.variable"
                      :rows="relativities"
                      :columns="relativitiesColumns"
                      :globalSearch="false"
                      row-key="name"
                    />
                </div>
            </BsContent>
        </BsTab>
    </template>

<script lang="ts">
import BarChart from './BarChart.vue'
import DocumentationContent from './DocumentationContent.vue'
import EmptyState from './EmptyState.vue';
import * as echarts from "echarts";
import type { DataPoint, ModelPoint, RelativityPoint, VariablePoint, ModelVariablePoint, BaseValue } from '../models';
import { isErrorPoint } from '../models';
import { defineComponent } from "vue";
import { API } from '../Api';
import { useLoader } from "../composables/use-loader";
import { useNotification } from "../composables/use-notification";
import { BsButton, BsLayoutDefault, BsTable, BsCheckbox, BsSlider, BsToggle } from "quasar-ui-bs";
import docLogo from "../assets/images/doc-logo-example.svg";
import oneWayIcon from "../assets/images/one-way.svg";
import type { QTableColumn } from 'quasar';

const columns: QTableColumn[] = [
        { name: 'class', align: 'center', label: 'Class', field: 'class',sortable: true},
        { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
      ]

const rows = [
    {
        class: 'January',
        relativity: 1.0,
    },
    {
        class: 'February',
        relativity: 1.087,
    },
    {
        class: 'March',
        relativity: 0.98,
    },
    {
        class: 'April',
        relativity: 1.12,
    }
  ]

export default defineComponent({
    props: {
      reloadModels: {
        type: Boolean,
        default: false
      }
    },
    components: {
        BarChart,
        DocumentationContent,
        BsButton,
        BsLayoutDefault,
        EmptyState,
        BsTable,
        BsCheckbox,
        BsSlider,
        BsToggle
    },
    data() {
        return {
            chartData: [] as DataPoint[],
            relativitiesData: [] as RelativityPoint[],
            relativitiesTable: [] as RelativityPoint[],
            models: [] as ModelPoint[],
            baseValues: [] as BaseValue[],
            selectedModel: {} as ModelPoint,
            modelsString: [] as string[],
            selectedModelString: "",
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            docLogo,
            oneWayIcon,
            variablePoints: [] as VariablePoint[],
            allVariables: [] as String[],
            variables: [] as VariablePoint[],
            selectedVariable: {} as VariablePoint,
            relativities: rows,
            relativitiesColumns: columns,
            inModelOnly: true,
            includeSuspectVariables: true,
            loading: false,
            active_model:  {} as ModelPoint,
            trainTest: false,
            rescale: false
        };
    },
    watch: {
      reloadModels: {
          handler() {
            API.getModels().then((data: any) => {
              this.models = data.data;
              this.modelsString = this.models.map(item => item.name);
            });
          },
      },
      loading(newVal) {
          if (newVal) {
              useLoader("Loading data..").show();
          } else {
              useLoader().hide();
          }
      },
      // selectedVariable(newValue: VariablePoint) {
      //   console.log("selected Variable")
      //   this.relativitiesTable = this.relativitiesData.filter(item => item.variable === newValue.variable);
      //   this.relativitiesColumns = columns;
      //   this.relativities = this.relativitiesTable.map( (point) => {
      //     const relativity = {'class': point.category, 'relativity': Math.round(point.relativity*1000)/1000};
      //     return relativity
      //   })
      //   if (this.rescale) {
      //       const baseCategory = this.baseValues.find(item => item.variable === newValue.variable);
      //       if (baseCategory) {
      //         const baseData = this.chartData.find(item => item.Category === baseCategory.base_level);
      //         if (baseData) {
      //           const baseLevelPrediction = baseData.baseLevelPrediction;
      //           const fittedAverage = baseData.fittedAverage;
      //           const observedAverage = baseData.observedAverage;
      //           this.chartData = this.chartData.map(item => ({
      //           ...item,
      //           baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
      //           fittedAverage: item.fittedAverage / fittedAverage,
      //           observedAverage: item.observedAverage / observedAverage
      //         }));
      //         }
      //       }
      //     }
      // },
      // allData(newValue: DataPoint[]) {
      //    this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
      //    if (this.rescale) {
      //       //const baseCategory = this.relativitiesTable.find(item => item.relativity === 1);
      //       const baseCategory = this.baseValues.find(item => item.variable === this.selectedVariable.variable);
      //       if (baseCategory) {
      //         const baseData = this.allData.find(item => item.Category === baseCategory.base_level && item.definingVariable === this.selectedVariable.variable);
      //         if (baseData) {
      //           const baseLevelPrediction = baseData.baseLevelPrediction;
      //           const fittedAverage = baseData.fittedAverage;
      //           const observedAverage = baseData.observedAverage;
      //       this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable).map(item => ({
      //           ...item,
      //           baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
      //           fittedAverage: item.fittedAverage / fittedAverage,
      //           observedAverage: item.observedAverage / observedAverage
      //         }));
      //         } else {
      //       this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
      //     }
      //       } else {
      //       this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
      //     }
      //     } else {
      //       this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
      //     }
      // }
    },
    methods: {
      closeSideDrawer() {
            if(this.layoutRef){
                this.layoutRef.drawerOpen = !this.layoutRef.drawerOpen;
            }
        },
        async updateVariable(value: VariablePoint) {          
          console.log("update variable");
          this.loading = true;
          this.selectedVariable = value;
          const modelTrainPoint = {id: this.active_model.id, name: this.active_model.name, trainTest: this.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
          const dataResponse = await API.getData(modelTrainPoint);
          this.chartData = dataResponse?.data;
          this.loading = false;
        },
        async updateTrainTest(value: boolean) {
          console.log("update train test");
          this.loading = true;
          this.trainTest = value;
          const modelTrainPoint = {id: this.active_model.id, name: this.active_model.name, trainTest: this.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
          const dataResponse = await API.getData(modelTrainPoint);
          this.chartData = dataResponse?.data;
          this.loading = false;
        },
        async updateRescale(value: boolean) {
          console.log("update rescale");
          this.loading = true;
          if (value) {
            const baseCategory = this.baseValues.find(item => item.variable === this.selectedVariable.variable);
            if (baseCategory) {
              const baseData = this.chartData.find(item => item.Category === baseCategory.base_level);
              console.log(baseData);
              if (baseData) {
                const baseLevelPrediction = baseData.baseLevelPrediction;
                const fittedAverage = baseData.fittedAverage;
                const observedAverage = baseData.observedAverage;
                  this.chartData = this.chartData.map(item => ({
                      ...item,
                      baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
                      fittedAverage: item.fittedAverage / fittedAverage,
                      observedAverage: item.observedAverage / observedAverage
                    }));
              }
            }
          } else {
            const modelTrainPoint = {id: this.active_model.id, name: this.active_model.name, trainTest: this.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
            const dataResponse = await API.getData(modelTrainPoint);
            this.chartData = dataResponse?.data;
          }
          this.loading = false;
        },
        async updateModelString(value: string) {
          console.log("update model");
          this.loading = true;
          this.chartData = [] as DataPoint[];
          try {
            this.selectedVariable = {} as VariablePoint;
            const model = this.models.filter( (v: ModelPoint) => v.name==value)[0];
            this.active_model = model
            const variableResponse = await API.getVariables(model)
            if (isErrorPoint(variableResponse?.data)) {
              this.handleError(variableResponse?.data.error);
            } else {
              this.variablePoints = variableResponse?.data;
              this.allVariables = this.variablePoints.map(item => item.variable);
              // const modelTrainPoint = {id: model.id, name: model.name, trainTest: this.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
              // const dataResponse = await API.getData(modelTrainPoint);
              // this.chartData = dataResponse?.data;
              const relativityResponse = await API.getRelativities(model);
              this.relativitiesData = relativityResponse?.data;
              const baseResponse = await API.getBaseValues(model);
              this.baseValues = baseResponse?.data;
              this.selectedModelString = value;
            }
        } catch (err) {
            this.handleError(err);
        } finally {
          this.loading = false;
        }
        },
        onClick: function() {
          API.exportModel(this.active_model).then(response => {
              const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', this.selectedModelString + '.csv'); // Set the filename for the download
              document.body.appendChild(link);
              link.click();
              window.URL.revokeObjectURL(url); // Clean up
          }).catch(error => {
              console.error('Error exporting model:', error);
          });
        },
        onClickOneWay: function() {
          API.exportOneWay({id: this.active_model.id, 
            name: this.active_model.name, 
            variable: this.selectedVariable.variable, 
            trainTest: this.trainTest,
            rescale: this.rescale}).then(response => {
              const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', this.selectedModelString + '_' + this.selectedVariable.variable + '_' + (this.trainTest ? "test" : "train") + (this.rescale ? "_rescaled" : "") + '.csv'); // Set the filename for the download
              document.body.appendChild(link);
              link.click();
              window.URL.revokeObjectURL(url); // Clean up
          }).catch(error => {
              console.error('Error exporting model:', error);
          });
        },
        notifyError(msg: string) {
            useNotification("negative", msg);
        },
        handleError(msg: any) {
            this.loading = false;
            console.error(msg);
            this.notifyError(msg);
        },
    },
    mounted() {
      API.getModels().then((data: any) => {
        this.models = data.data;
        this.modelsString = this.models.map(item => item.name);
      });
    }
})
</script>

<style lang="scss" scoped>

:deep(.toggle-left-button) {
    display: none;
}

header {
  line-height: 1.5;
}

.variable-select-container {
    padding: 20px;
}

.tab-content {
  padding-left: 0px;
  padding-right: 0px;
  padding-top: 20px;
  display: flex;
  align-items: flex-start;
  gap: var(--bs-spacing-13, 52px);
  min-height: 350px;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

.bs-btn {
  margin-top: 12px;
}

.button-container {
  margin-top: 12px
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}

.close-side-drawer-btn {
    color: var(--interactions-bs-color-interaction-primary, #2b66ff);
    position: absolute;
    top: 7px;
    right: 10px;
    z-index: 1000;
}
.open-side-drawer-btn {
    color: var(--interactions-bs-color-interaction-primary, #2b66ff);
    position: relative;
    top: 4px;
}
</style>