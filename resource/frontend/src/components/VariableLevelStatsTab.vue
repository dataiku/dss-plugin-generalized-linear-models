<template>
<BsTab
            name="Variable Level Stats"
            docTitle="GLM Analyzer"
            :docIcon="docLogo"
        >
            <BsTabIcon>
                <img :src="variableLevelIcon" alt="Target Definition Icon" />
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
                  style="min-width: 250px">
              </BsSelect>
              <div v-if="selectedModelString" class="button-container">
                  <BsButton class="bs-primary-button" 
                  unelevated
                  dense
                  no-caps
                  padding="4"
                  @click="onClick">Export</BsButton>
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
                    title="Variable Level Stats"
                    subtitle="Select model in the left column to create table"
                    v-if="variableLevelStatsData.length==0"/>
                <div class="tab-content" v-else>
                    <BsTable
                      title="Variable Level Stats"
                      :rows="variableLevelStatsData"
                      :columns="columns"
                      :globalSearch="false"
                      row-key="variable"
                    />
                </div>
            </BsContent>
        </BsTab>
    </template>

<script lang="ts">
import EmptyState from './EmptyState.vue';
import * as echarts from "echarts";
import type { ModelPoint, VariableLevelStatsPoint } from '../models';
import { defineComponent } from "vue";
import { API } from '../Api';
import { BsButton, BsLayoutDefault, BsTable } from "quasar-ui-bs";
import docLogo from "../assets/images/doc-logo-example.svg";
import variableLevelIcon from "../assets/images/variable-level-stats.svg";
import { useLoader } from "../composables/use-loader";
import type { QTableColumn } from 'quasar';

const columns: QTableColumn[] = [
        { name: 'variable', align: 'center', label: 'Variable', field: 'variable',sortable: true},
        { name: 'value', align: 'center', label: 'Value', field: 'value',sortable: true},
        { name: 'coefficient', align: 'center', label: 'Coefficient', field: 'coefficient',sortable: true},
        { name: 'standard_error', align: 'center', label: 'Standard Error', field: 'standard_error',sortable: true},
        { name: 'standard_error_pct', align: 'center', label: 'Standard Error PCT', field: 'standard_error_pct',sortable: true},
        { name: 'weight', align: 'center', label: 'Weight', field: 'weight',sortable: true},
        { name: 'weight_pct', align: 'center', label: 'Weight PCT', field: 'weight_pct',sortable: true},
        { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
      ]

const rows = [
    {
        variable: 'VehBrand',
        value: 'B10',
        coefficient: 0.89,
        standard_error: 0.12,
        standard_error_pct: 1.044,
        weight: 123,
        weight_pct: 45,
        relativity: 1.1297,
    },
    {
        variable: 'VehBrand',
        value: 'B12',
        coefficient: 0.22,
        standard_error: 0.37,
        standard_error_pct: 1.93,
        weight: 230,
        weight_pct: 36,
        relativity: 0.872,
    },
    {
        variable: 'VehBrand',
        value: 'B1',
        coefficient: 0,
        standard_error: 0.23,
        standard_error_pct: 1.43,
        weight: 63,
        weight_pct: 21,
        relativity: 1.0,
    },
    {
        variable: 'VehGas',
        value: 'Regular',
        coefficient: 0,
        standard_error: 0.37,
        standard_error_pct: 1.93,
        weight: 230,
        weight_pct: 36,
        relativity: 1.0,
    },
    {
        variable: 'VehGas',
        value: 'Diesel',
        coefficient: 0.234,
        standard_error: 0.23,
        standard_error_pct: 1.43,
        weight: 63,
        weight_pct: 21,
        relativity: 0.9898,
    }
  ]

function round_decimals(x : number) {
  return Math.round(x * 1000) / 1000
}

export default defineComponent({
    props: {
      reloadModels: {
        type: Boolean,
        default: false
      }
    },
    components: {
        BsButton,
        BsLayoutDefault,
        EmptyState,
        BsTable,
    },
    data() {
        return {
            variableLevelStatsData: [] as VariableLevelStatsPoint[],
            models: [] as ModelPoint[],
            active_model: {} as ModelPoint,
            selectedModel: {} as ModelPoint,
            modelsString: [] as string[],
            selectedModelString: "",
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            docLogo,
            variableLevelIcon,
            columns: columns,
            loading: false,
        };
    },
    watch: {
      reloadModels: {
          handler() {
            this.loading = true;
            API.getModels().then((data: any) => {
              this.models = data.data;
              this.modelsString = this.models.map(item => item.name);
            });
            this.loading = false;
          },
      },
      loading(newVal) {
        if (newVal) {
            useLoader("Loading data..").show();
        } else {
            useLoader().hide();
        }
    },
    },
    methods: {
      closeSideDrawer() {
            if(this.layoutRef){
                this.layoutRef.drawerOpen = !this.layoutRef.drawerOpen;
            }
        },
        async updateModelString(value: string) {
          this.loading = true;
          this.selectedModelString = value;
          const model = this.models.filter( (v: ModelPoint) => v.name==value)[0];
          const variableLevelStatsResponse = await API.getVariableLevelStats(model);
          this.active_model = model
          this.variableLevelStatsData = variableLevelStatsResponse?.data.map( (point) => {
              const variableLevelStats = {'variable': point.variable, 'value': point.value, 
                                          'coefficient': round_decimals(point.coefficient),
                                          'standard_error': round_decimals(point.standard_error), 
                                          'standard_error_pct': round_decimals(point.standard_error_pct),
                                          'weight': round_decimals(point.weight), 
                                          'weight_pct': round_decimals(point.weight_pct), 
                                          'relativity': round_decimals(point.relativity)};
              return variableLevelStats
          });
          this.loading = false;
        },
        onClick: function() {
          API.exportVariableLevelStats(this.active_model).then(response => {
              const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', 'variable_level_stats.csv'); // Set the filename for the download
              document.body.appendChild(link);
              link.click();
              window.URL.revokeObjectURL(url); // Clean up
          }).catch(error => {
              console.error('Error exporting model:', error);
          });
        },
    },
    mounted() {
      this.loading = true;
      API.getModels().then((data: any) => {
        this.models = data.data;
        this.modelsString = this.models.map(item => item.name);
      });
      this.loading = false;
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
  align-items: center;
  gap: var(--bs-spacing-13, 52px);
  min-height: 350px;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
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
