<template>
<div class="tab-content-wrapper">
    <div class="card-container">
                    <BsCard v-if="store.selectedModelString" :title=store.selectedModelString style="width: 600px">
                        <template #content>
                            <BsCardColItems
                            :items=store.modelMetrics1
                            ></BsCardColItems>
                        </template>
                      </BsCard>
                      <BsCard v-if="store.selectedModelString2" :title=store.selectedModelString2 style="width: 600px">
                        <template #content>
                            <BsCardColItems
                            :items=store.modelMetrics2
                            ></BsCardColItems>
                        </template>
                      </BsCard>
                    </div>
                    <div class="tab-content">
                        <div class="q-pa-lg">
                            <q-tabs
                            v-model="store.tab"
                            dense
                            class="bs-underline-tabs bs-font-medium-3-normal bs-colored-text"
                            active-color="primary"
                            indicator-color="primary"
                            align="left"
                            no-caps
                            >
                            <q-tab name="one-way-variable" label="One-Way Variable" />
                            <q-tab name="variable-level-stats" label="Variable-Level Stats" />
                            <q-tab name="lift-chart" label="Lift Chart" />
                            </q-tabs>
                    
                    
                            <q-tab-panels v-model="store.tab" animated class="bs-colored-text">
                            <q-tab-panel name="one-way-variable">
                                <OneWayTabContent
                                :chart-data=store.chartData
                                :chart-data2=store.chartData2
                                :selected-variable=store.selectedVariable
                                :relativities=store.relativities
                                :relativities-columns=store.relativitiesColumns
                                ></OneWayTabContent>
                            </q-tab-panel>
                    
                            <q-tab-panel name="variable-level-stats">
                                <VariableLevelStatsTabContent
                                :variable-level-stats-data=store.variableLevelStatsData
                                :columns=store.variableLevelStatsColumns
                                ></VariableLevelStatsTabContent>
                            </q-tab-panel>
                    
                            <q-tab-panel name="lift-chart">
                                <LiftChartTabContent
                                :chart-data=store.liftChartData
                                ></LiftChartTabContent>
                            </q-tab-panel>
                            </q-tab-panels>
                        </div>
                    </div>
                </div>
</template>

<script lang="ts">
    import BarChart from './BarChart.vue'
    import DocumentationContent from './DocumentationContent.vue'
    import EmptyState from './EmptyState.vue';
    import OneWayTabContent from './OneWayTabContent.vue'
    import VariableLevelStatsTabContent from './VariableLevelStatsTabContent.vue'
    import LiftChartTabContent from './LiftChartTabContent.vue'
    // import * as echarts from "echarts";
    import type { DataPoint, VariablePoint } from '../models';
    import { defineComponent } from "vue";
    import { useNotification } from "../composables/use-notification";
    import { BsButton, BsLayoutDefault, BsTable, BsCheckbox, BsSlider, BsToggle } from "quasar-ui-bs";
    import docLogo from "../assets/images/doc-logo-example.svg";
    import oneWayIcon from "../assets/images/one-way.svg";
    import { useModelStore } from "../stores/webapp";
    
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
            BsToggle,
            OneWayTabContent,
            VariableLevelStatsTabContent,
            LiftChartTabContent
        },
        data() {
            return {
                store: useModelStore(),
                layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
                docLogo,
                oneWayIcon,
                comparisonChartTitle: "Model Metrics",
                selectedVariable: {} as VariablePoint,
                // loading = false;
            };
        },
        watch: {
          selectedVariable(newValue: VariablePoint) {
            this.store.selectedVariable = newValue;
            this.store.updateChartData();
          },
          allData(newValue: DataPoint[]) {
            this.store.allData = newValue;
            this.store.updateChartData();
          }
        },
        methods: {
            
            async updateVariable(value: VariablePoint) {
              this.store.selectedVariable = value;
            },
            async updateTrainTest(value: boolean) {
              this.store.updateTrainTest(value);
            },
            async updateRescale(value: boolean) {
              this.store.rescale = value;
              this.store.updateChartData();
            },
            async updateModelString(value: string) {
              this.store.updateModelString(value);
            },
            async updateModelString2(value: string) {
              this.store.updateModelString2(value);
            },
            async updateNbBins(value: number) {
                this.store.updateNbBins(value);
            },
            onClick: function() {
              this.store.exportModel();
            },
            onClickOneWay: function() {
              this.store.exportOneWay();
            },
            onClickStats: function() {
                this.store.exportStats();
            },
            notifyError(msg: string) {
                useNotification("negative", msg);
            },
            // handleError(msg: any) {
            //     this.store.loading = false;
            //     console.error(msg);
            //     this.notifyError(msg);
            // },
        },
        // mounted() {
        //   this.store.loadModels();
        // }
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
    
    .q-pa-lg {
        padding: 0
    }

    .card-container {
      display: flex;
      gap: 20px; /* Adjust the gap value as needed */
    }

    .bs-card {
      max-width: 440px;
    }

    @media (min-width: 1024px) {
      header {
        display: flex;
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
    .tab-content-wrapper {
      padding-left: 0px;
      padding-top: 20px;
  }
    
    </style> 