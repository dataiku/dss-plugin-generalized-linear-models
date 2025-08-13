<template>
    <BsTable
    title="Models"
    :rows="store.models"
    :columns="columns"
    :globalSearch="false"
    row-key="id"
    >
    <template #body-cell-model_name="props">
        <q-td :props="props">
            <a :href="getModelUrl(props.row)" class="table-link">
                {{ props.value }}
            </a>
        </q-td>
    </template>
    <template #body-cell-deploy="props">
            <q-td :props="props" style="text-align: center;">
                <BsButton 
                    flat 
                    round 
                    dense
                    @click="deployModel(props.row)">
                    <q-icon name="rocket_launch" />
                    <q-tooltip>Deploy Model</q-tooltip>
                </BsButton>
            </q-td>
        </template>
        <template #body-cell-export="props">
            <q-td :props="props" style="text-align: center;">
                <BsButton 
                    flat 
                    round 
                    dense
                    @click="exportModel(props.row)">
                    <q-icon name="download" />
                    <q-tooltip>Export Model</q-tooltip>
                </BsButton>
            </q-td>
        </template>
        <template #body-cell-delete="props">
            <q-td :props="props" style="text-align: center;">
                <BsButton 
                    flat 
                    round 
                    dense
                    @click="deleteModel(props.row)">
                    <q-icon name="delete" />
                    <q-tooltip>Delete Model</q-tooltip>
                </BsButton>
            </q-td>
        </template>
    </BsTable>
  </template>

<script lang="ts">
import EmptyState from './EmptyState.vue';
import type { ModelPoint } from '../models';
import { defineComponent } from "vue";
import { BsButton, BsLayoutDefault, BsTable } from "quasar-ui-bs";
import type { QTableColumn } from 'quasar';
import { QIcon, QTooltip, QTd } from 'quasar';
import { useModelStore } from '../stores/webapp';
import { useTrainingStore } from '../stores/training';

const columns: QTableColumn[] = [
      { name: 'model_name', align: 'center', label: 'Model Name', field: 'name', sortable: true},
      { name: 'model_id', align: 'center', label: 'Model Id', field: 'id', sortable: true},
      { name: 'model_date', align: 'center', label: 'Creation Date', field: 'date', sortable: true},
      { name: 'deploy', align: 'center', label: 'Deploy', field: '' },
      { name: 'export', align: 'center', label: 'Export', field: '' },
      { name: 'delete', align: 'center', label: 'Delete', field: '' }
    ]

export default defineComponent({
  props: {
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
      QIcon,
      QTooltip,
      QTd
  },
  data() {
      return {
          store: useModelStore(),
          trainingStore: useTrainingStore(),
      };
  },
  methods: {
    getModelUrl(model: ModelPoint): string {
        return `/projects/${this.store.projectKey}/analysis/${this.store.analysisId}/ml/p/${this.store.mlTaskId}/${model.id}/report/tabular-summary`;
    },
    async deployModel(model: ModelPoint) {
      await this.store.deployModel(model);
    },
    async deleteModel(model: ModelPoint) {
      await this.store.deleteModel(model);
      this.trainingStore.updateModels = true;
    },
    async exportModel(model: ModelPoint) {
      await this.store.exportModel(model);

    }
  },
  mounted() {
    this.store.loadModels();
  }
})
</script>

<style lang="scss" scoped>

.tab-content {
padding-left: 0px;
padding-right: 0px;
padding-top: 20px;
display: flex;
align-items: center;
gap: var(--bs-spacing-13, 52px);
min-height: 350px;
}

.table-link {
    text-decoration: none;
    color: black;
  }

  .table-link:hover {
    text-decoration: underline;
  }

</style>
