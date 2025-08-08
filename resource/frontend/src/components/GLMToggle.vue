<template>
  <div class="segmented-control-container">
    <div class="button-group">
      <button 
        :class="{ 'active': modelValue === option1 }" 
        @click="selectOption(option1)"
      >
        {{ option1 }}
      </button>
      <button 
        :class="{ 'active': modelValue === option2 }" 
        @click="selectOption(option2)"
      >
        {{ option2 }}
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

export default defineComponent({
  name: 'GLMToggle',
  props: {
    modelValue: {
      type: String as PropType<string>,
      required: true,
    },
    option1: {
      type: String,
      default: 'Train',
    },
    option2: {
      type: String,
      default: 'Test',
    }
  },
  emits: ['update:modelValue'],
  methods: {
    selectOption(option: string) {
      this.$emit('update:modelValue', option);
    },
  },
});
</script>

<style lang="scss" scoped>
.segmented-control-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.button-group {
  display: flex;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
}

button {
  border: none;
  padding: 6px 12px;
  background-color: #ffffff;
  color: #24292f;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease-in-out;
  border-left: 1px solid #d0d7de;
}

button:first-child {
  border-left: none;
}

button.active {
  background-color: #e6f0ff; /* A light blue for the active state */
  color: #0969da;
  font-weight: 600;
}
</style>
