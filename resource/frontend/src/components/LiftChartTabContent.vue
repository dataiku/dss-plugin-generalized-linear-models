<template>
      <EmptyState
          class="empty-state"
          title="Lift Chart"
          subtitle="Select model in the left column to create chart"
          v-if="chartData.length == 0"/>
      <div class="tab-content" v-else>
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
                  @click="exportLiftChart">
                  <q-icon name="download" />
                  <q-tooltip>Export Lift Chart</q-tooltip>
              </BsButton>
          </div>
          <LiftChart
              v-if="chartData.length"
              :xaxisLabels="chartData.map(item => item.Category)"
              :barData="chartData.map(item => item.Value)"
              :observedData="chartData.map(item => item.observedAverage)"
              :predictedData="chartData.map(item => item.fittedAverage)"
              chartTitle="Lift Chart"
          />
      </div>
</template>

<script lang="ts">
import LiftChart from './LiftChart.vue'
import DocumentationContent from './DocumentationContent.vue'
import EmptyState from './EmptyState.vue';
import type { LiftDataPoint } from '../models';
import { defineComponent } from "vue";
import { BsButton, BsLayoutDefault, BsTable, BsCheckbox, BsSlider, BsToggle } from "quasar-ui-bs";
import { useModelStore } from '../stores/webapp';
import { useLiftChartStore } from '../stores/liftChartStore';


export default defineComponent({
    props: {
      reloadModels: {
        type: Boolean,
        default: false
      },
      chartData: {
        type: Array<LiftDataPoint>,
        default: []
      }
    },
    components: {
        LiftChart,
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
            store: useModelStore(),
            liftChartStore: useLiftChartStore(),
        };
    },
    methods: {
      async deployModel() {
        this.store.deployActiveModel();
      },
      async exportLiftChart() {
        this.liftChartStore.exportLiftChart();
      }
    }
})
</script>

<style lang="scss" scoped>

:deep(.toggle-left-button) {
    display: none;
}

.tab-content {
  padding-left: 0px;
  padding-right: 0px;
  padding-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: normal;
  gap: var(--bs-spacing-13, 52px);
  min-height: 350px;
  margin: 0 auto;
  padding: 2rem;
}

.export-buttons {
  display: flex;
  gap: 12px;
  align-self: flex-end;
}
</style>
