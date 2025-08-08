<template>
    <EmptyState
          class="empty-state"
          title="One-Way Variable"
          subtitle="Select variable in the left column to create chart"
          v-if="chartData.length==0"/>
      <div class="tab-content" v-else>
      <div class="top-row">
          <ModelMetrics
            :title="selectedModel"
            :items="metrics"
          />
          <ModelMetrics v-if="oneWayStore.chartOptions.comparisonModel.length > 0"
            :title="comparedModel"
            :items="comparedMetrics"
          />
          <div class="export-buttons">
            <BsButton 
                  dense
                  outline
                  @click="deployModel">
                  <q-icon name="rocket_launch" />
                  <q-tooltip>Deploy Model</q-tooltip>
              </BsButton>
            <BsButton   
                  dense
                  outline
                  @click="exportOneWay">
                  <q-icon name="download" />
                  <q-tooltip>Export One-Way</q-tooltip>
              </BsButton>
          </div>
        </div>
        <div class="chart-row">
          <BarChart
            v-if="chartData.length>0"
            :xaxisLabels="chartXaxisLabels"
            :xaxisType="chartXaxisType"
            :barData="chartData.map(item => item.Value)"
            :observedAverageLine="chartData.map(item => item.observedAverage)"
            :fittedAverageLine="chartData.map(item => item.fittedAverage)"
            :baseLevelPredictionLine="chartData.map(item => item.baseLevelPrediction)"
            :fittedAverageLine2="chartData2.map(item => item.fittedAverage)"
            :baseLevelPredictionLine2="chartData2.map(item => item.baseLevelPrediction)"
            :chartTitle="selectedVariable.variable"
            :levelOrder="levelOrder"
            />
          <BsTable v-if="selectedVariable.isInModel"
            :title="selectedVariable.variable"
            :rows="relativities"
            :columns="tableColumns"
            :globalSearch="false"
            row-key="name"
          />
      </div>
    </div>
</template>

<script lang="ts">
import BarChart from './BarChart.vue'
import DocumentationContent from './DocumentationContent.vue'
import EmptyState from './EmptyState.vue';
import ModelMetrics from './ModelMetrics.vue'
import { useModelStore } from "../stores/webapp";
import { useOneWayChartStore } from "../stores/oneWayChartStore";
import * as echarts from "echarts";
import type { DataPoint, VariablePoint, ModelMetricsDataPoint } from '../models';
import { defineComponent } from "vue";
import type {PropType} from "vue";
import { BsButton, BsLayoutDefault, BsTable, BsCheckbox, BsSlider, BsToggle } from "quasar-ui-bs";
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
      },
      chartData: {
        type: Array<DataPoint>,
        default: []
      },
      chartData2: {
        type: Array<DataPoint>,
        default: []
      },
      selectedVariable: {
        type: Object as PropType<VariablePoint>,
        required: true
      },
      relativities: {
        type: Array<Object>,
        default: rows
      },
      levelOrder: {
        type: String,
        required: true
      },
      selectedModel: {
        type: String,
        default: ""
      },
      metrics: {
        type: Object as PropType<ModelMetricsDataPoint>,
        default: {AIC: 0, BIC: 0, Deviance: 0}
      },
      comparedModel: {
        type: String,
        default: ""
      },
      comparedMetrics: {
        type: Object as PropType<ModelMetricsDataPoint>,
        default: {AIC: 0, BIC: 0, Deviance: 0}
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
        ModelMetrics
    },
    computed: {
        isBinned(): boolean {
            if (this.selectedVariable?.variableType !== 'categorical' && this.chartData.length > 0) {
                return typeof this.chartData[0].Category === 'string';
            }
            return false;
        },
        
        chartXaxisType(): 'category' | 'value' {
            if (this.isBinned || this.selectedVariable?.variableType === 'categorical') {
                return 'category';
            }
            return 'value';
        },

        chartXaxisLabels(): (string | number)[] {
            if (this.chartXaxisType === 'category') {
                return this.chartData.map(item => String(item.Category));
            }
            return this.chartData.map(item => Number(item.Category));
        },

        tableColumns(): QTableColumn[] {
            const baseColumns = [...columns];

            // If there is a compared model, add the extra column
            if (this.oneWayStore.chartOptions.comparisonModel && this.oneWayStore.chartOptions.comparisonModel.length > 0) {
                baseColumns.push({
                    name: 'compared_relativity',
                    align: 'center',
                    label: 'Compared Relativity',
                    field: 'compared_relativity',
                    sortable: true
                });
            }

            return baseColumns;
        }
    },
    methods: {
      async deployModel() {
        this.store.deployModel();
      },
      async exportOneWay() {
        this.oneWayStore.exportOneWayChart();
      }
    },
    data() {
        return {
          store: useModelStore(),
          oneWayStore: useOneWayChartStore(),
        };
    },
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
  align-items: flex-start;
  gap: var(--bs-spacing-13, 52px);
  min-height: 350px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
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

.top-row {
  display: flex;
  align-items: flex-start;
  gap: 52px;
  width: 100%;
}

.export-buttons {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.chart-row {
  display: flex;
  align-items: flex-start;
  gap: 52px;
}
</style>