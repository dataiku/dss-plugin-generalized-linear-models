<template>
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
              row-key="variable"
            />
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

const columns: QTableColumn[] = [
        { name: 'variable', align: 'center', label: 'Variable', field: 'variable',sortable: true},
        { name: 'value', align: 'center', label: 'Value', field: 'value',sortable: true},
        { name: 'coefficient', align: 'center', label: 'Coefficient', field: 'coefficient',sortable: true},
        { name: 'p_value', align: 'center', label: 'P-value', field: 'p_value',sortable: true},
        { name: 'standard_error', align: 'center', label: 'Standard Error', field: 'standard_error',sortable: true},
        { name: 'standard_error_pct', align: 'center', label: 'Standard Error PCT', field: 'standard_error_pct',sortable: true},
        { name: 'weight', align: 'center', label: 'Weight', field: 'weight',sortable: true},
        { name: 'weight_pct', align: 'center', label: 'Weight PCT', field: 'weight_pct',sortable: true},
        { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
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
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            docLogo,
            variableLevelIcon,
            loading: false,
        };
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
