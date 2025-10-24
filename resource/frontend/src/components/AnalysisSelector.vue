<template>
  <BsSelect
    :model-value="store.selectedMlTask"
    :all-options="store.mlTaskOptions"
    option-value="mlTaskId"
    @update:modelValue="value => store.selectMlTask(value)"
    :disabled="disabled"
  >
    <template #selected-item>
      <div v-if="store.selectedMlTask.mlTaskId">{{store.selectedMlTask.analysisName}} ({{store.selectedMlTask.mlTaskId}})</div>
      <div v-else class="text-grey">
        Select an analysis...
      </div>
    </template>
    <template #option="props">
      <q-item
        v-bind="props.itemProps"
        clickable
        :disable="!isTaskValid(props.opt)"
      >
        <q-item-section>
          <q-item-label :class="{ 'text-grey-7': !isTaskValid(props.opt) }">
            {{ props.opt.analysisName }}
          </q-item-label>
          <q-item-label caption :class="{ 'text-grey-5': !isTaskValid(props.opt) }">
            Target: {{ props.opt.targetColumn }} | Dataset: {{ props.opt.trainSet }}
          </q-item-label>
          <q-item-label caption :class="{ 'text-grey-5': !isTaskValid(props.opt) }">
            ID: {{ props.opt.analysisId }} / {{ props.opt.mlTaskId }}
          </q-item-label>
        </q-item-section>
        <q-item-section v-if="!isTaskValid(props.opt)" side>
          <q-icon name="warning" color="grey-5" />
          <q-tooltip>This task is invalid or failed</q-tooltip>
        </q-item-section>
      </q-item>
    </template>
  </BsSelect>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { useAnalysisStore } from '../stores/analysisStore';
import { BsSelect } from 'quasar-ui-bs';
import type { MlTask } from '../models';

export default defineComponent({
  name: 'AnalysisSelector',
  components: { BsSelect },
  props: {
    disabled: {
      type: Boolean as PropType<boolean>,
      default: false
    }
  },
  setup() {
    const store = useAnalysisStore();
    function isTaskValid(mlTask: MlTask): boolean {
      return mlTask.isValid;
    }
    return { store, isTaskValid };
  }
});
</script>

<style scoped>

.bs-select {
  min-width: 260px;
}

::v-deep(.bs-selection-content) {
  max-width: 100% !important;
  white-space: nowrap;
}

</style>
