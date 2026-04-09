<template>
  <BsSelect
    class="analysis-fixed-select"
    :model-value="store.selectedMlTask"
    :all-options="store.mlTaskOptions"
    option-value="mlTaskId"
    @update:modelValue="handleSelect"
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
  emits: ['analysis-selected'],
  setup(props, { emit }) {
    const store = useAnalysisStore();
    function isTaskValid(mlTask: MlTask): boolean {
      return mlTask.isValid;
    }
    function handleSelect(value: MlTask) {
      if (!value) return; // Guard against null/undefined
      store.selectMlTask(value); // This is what it did before
      if (value.mlTaskId) {
        emit('analysis-selected'); // This emits the event to the parent
      }
    }
    return { store, isTaskValid, handleSelect };
  }
});
</script>

<style scoped>

.bs-select {
  min-width: 260px;
}

:deep(.analysis-fixed-select) {
  width: 620px;
  min-width: 620px;
  max-width: 620px;
}

:deep(.analysis-fixed-select .bs-selection-content) {
  display: block;
  max-width: calc(100% - 28px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

:deep(.analysis-fixed-select .q-field__native) {
  min-width: 0;
  padding-right: 28px;
}

:deep(.analysis-fixed-select .bs-selection-content > div) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

</style>
