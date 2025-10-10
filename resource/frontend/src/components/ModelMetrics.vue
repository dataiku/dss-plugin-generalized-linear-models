<template>
    <q-card flat bordered class="metrics-card">
    <q-card-section>
      <div class="text-h6 text-center q-mb-md">{{ title }}</div>
      <div class="row items-center justify-around">
        <template v-for="(value, key, index) in items" :key="key">
          <!-- Add a separator before the item, but not for the first one -->
          <q-separator v-if="index > 0" vertical inset />

          <!-- Metric Item -->
          <div class="col text-center q-pa-sm">
            <div class="text-h5 text-weight-regular">
              <span>
                <q-tooltip anchor="bottom middle" self="top middle">
                  {{ formatFullNumber(value) }}
                </q-tooltip>
                {{ formatAbbreviatedNumber(value) }}
              </span>
            </div>
            <div class="text-caption text-grey">
              {{ key }}
            </div>
          </div>
        </template>
      </div>
    </q-card-section>
  </q-card>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

export default defineComponent({
  name: 'ModelMetricsCard',
  props: {
    title: {
      type: String,
      required: true,
    },
    items: {
      type: Object as PropType<Record<string, number>>,
      required: true,
    },
  },
  methods: {
    formatAbbreviatedNumber(value: number): string {
      if (value == null) return 'N/A';
      const absValue = Math.abs(value);
      if (absValue >= 1e9) return (value / 1e9).toFixed(2) + 'B';
      if (absValue >= 1e6) return (value / 1e6).toFixed(2) + 'M';
      if (absValue >= 1e3) return (value / 1e3).toFixed(2) + 'K';
      return value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    },
    formatFullNumber(value: number): string {
      if (value == null) return 'N/A';
      return value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    },
  },
});
</script>

<style lang="scss" scoped>
.metrics-card {
  min-width: 300px;
  width: fit-content;
}
</style>

