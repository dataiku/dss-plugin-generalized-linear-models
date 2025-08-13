<template>
  <div class="stats-container">
  <div class="top-row">
    <div class="model-selector">
      <BsLabel label="Select a model" info-text="Stats will be generated for this model" />
      <BsSelect
          :modelValue="store.activeModelName"
          :all-options="store.modelOptions"
          @update:modelValue="onModelChange"
      />
      </div>
          <div class="export-buttons" v-if="variableLevelStatsData.length>0">
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
                  @click="exportVariableLevelStats">
                  <q-icon name="download" />
                  <q-tooltip>Export Variable Stats</q-tooltip>
              </BsButton>
          </div>
        </div>
      <EmptyState
            class="empty-state"
            title="Variable Level Stats"
            subtitle="Select model in the left column to create table"
            v-if="variableLevelStatsData.length==0"/>
        <div class="tab-content" v-else>
            <BsTable
              title="Variable Level Stats"
              :rows="variableLevelStatsData"
              :columns="columns"
              :globalSearch="false"
              row-key="variable">
                <template v-slot:body-cell-p_value="props">
                  <q-td :props="props">
                    <span :class="{ 'table-value-highlight': props.row.p_value > p_value_threshold }">
                      {{ props.value }}
                    </span>
                  </q-td>
                </template>
                <template v-slot:body-cell-standard_error_pct="props">
                  <q-td :props="props">
                    <span :class="{ 'table-value-highlight': props.row.standard_error_pct > standard_error_pct_threshold }">
                      {{ props.value }}
                    </span>
                  </q-td>
                </template>
      </BsTable>
        </div>
      </div>
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
import { useModelStore } from "../stores/webapp";
import { useOneWayChartStore } from "../stores/oneWayChartStore.ts"
import { useLiftChartStore } from "../stores/liftChartStore.ts"
import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore.ts"

const columns: QTableColumn[] = [
        { name: 'variable', align: 'center', label: 'Variable', field: 'variable',sortable: true},
        { name: 'value', align: 'center', label: 'Value', field: 'value',sortable: true},
        { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
        { name: 'coefficient', align: 'center', label: 'Coefficient', field: 'coefficient',sortable: true},
        { name: 'p_value', align: 'center', label: 'P-value', field: 'p_value',sortable: true},
        { name: 'standard_error', align: 'center', label: 'Standard Error', field: 'standard_error',sortable: true},
        { name: 'standard_error_pct', align: 'center', label: 'Standard Error %', field: 'standard_error_pct',sortable: true},
        { name: 'weight', align: 'center', label: 'Weight', field: 'weight',sortable: true},
        { name: 'weight_pct', align: 'center', label: 'Weight %', field: 'weight_pct',sortable: true},
      ]

export default defineComponent({
    props: {
      reloadModels: {
        type: Boolean,
        default: false
      },
      variableLevelStatsData: {
        type: Array<VariableLevelStatsPoint>,
        default: []
      },
      columns: {
        type: Array<QTableColumn>,
        default: columns
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
            models: [] as ModelPoint[],
            active_model: {} as ModelPoint,
            selectedModel: {} as ModelPoint,
            modelsString: [] as string[],
            selectedModelString: "",
            store: useModelStore(),
            variableStatsStore: useVariableLevelStatsStore(),
            oneWayStore: useOneWayChartStore(),
            liftChartStore: useLiftChartStore(),
            p_value_threshold: 0.05,
            standard_error_pct_threshold: 100 
        };
    },
    watch: {
          'store.activeModel': {
              handler(newModel) {
                  if (newModel?.id) {
                      this.oneWayStore.fetchVariablesForModel(newModel.id);
                      this.liftChartStore.fetchLiftData();
                      this.variableStatsStore.fetchStatsForModel(newModel.id);
                  }
              },
              deep: true
            }
        },
        methods: {
            async onModelChange(value: string) {
                this.store.setActiveModel(value);
            },
            async deployModel() {
              this.store.deployModel();
            },
            async exportVariableLevelStats() {
              this.variableStatsStore.exportVariableLevelStats();
            }
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
  padding-top: 20px;
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

.top-row {
  display: flex;
  align-items: flex-start;
  gap: 52px;
  width: 100%;
  margin-top: 12px;
}

.export-buttons {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.table-value-highlight {
  background-color: #FEF5D3; /* A light yellow */
}

.stats-container {
  width: 100%;
}

.empty-state {
      display: flex;
      justify-content: flex-start; /* Aligns to the left */
      width: 100%;
    }
</style>
