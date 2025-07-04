<template>
    <BsTable
    title="Models"
    :rows="store.models"
    :columns="columns"
    :globalSearch="false"
    row-key="id"
    >
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
import { useLoader } from "../composables/use-loader";
import type { QTableColumn } from 'quasar';
import { QIcon, QTooltip, QTd } from 'quasar';
import { useModelStore } from '../stores/webapp';
import { API } from "../Api";

const columns: QTableColumn[] = [
      { name: 'model_name', align: 'center', label: 'Model Name', field: 'name', sortable: true},
      { name: 'model_id', align: 'center', label: 'Model Id', field: 'id', sortable: true},
      { name: 'deploy', align: 'center', label: 'Deploy', field: '' },
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
          layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
          loading: false,
      };
  },
  methods: {
    async deployModel(model: ModelPoint) {
      console.log('Deploying model:', model.name, 'with ID:', model.id);
      this.store.loading = true;
      const status = API.deployModel(model);
      this.store.loading = false;
    },
    async deleteModel(model: ModelPoint) {
      console.log('Deleting model:', model.name, 'with ID:', model.id);
      this.store.loading = true;
      const status = API.deleteModel(model);
      this.store.loading = false;
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

</style>
