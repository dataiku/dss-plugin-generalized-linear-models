<template>
    <EmptyState
          class="empty-state"
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
            :fittedAverageLine2="chartData2.map(item => item.fittedAverage)"
            :baseLevelPredictionLine2="chartData2.map(item => item.baseLevelPrediction)"
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
</template>

<script lang="ts">
import BarChart from './BarChart.vue'
import DocumentationContent from './DocumentationContent.vue'
import EmptyState from './EmptyState.vue';
import * as echarts from "echarts";
import type { DataPoint, ModelPoint, RelativityPoint, VariablePoint, ModelVariablePoint } from '../models';
import { isErrorPoint } from '../models';
import { defineComponent } from "vue";
import type {PropType} from "vue";
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
      relativitiesColumns: {
        type: Array<QTableColumn>,
        default: columns
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