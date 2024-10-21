<template>
    <div class="variable-select-container">
      <BsButton @click="addInteraction" class="q-mt-md" label="Add Interaction" />
      <QCard v-if="interactions.length > 0" class="q-mt-md">
        <QCardSection v-for="(interaction, index) in interactions" :key="index">
          <div class="row q-col-gutter-md">
            <div class="col-5">
              <BsSelect
                v-model="interaction.first"
                :all-options="columnOptions"
                style="min-width: 150px"
              />
            </div>
            <div class="col-5">
              <BsSelect
                label=""
                v-model="interaction.second"
                :all-options="columnOptions"
                style="min-width: 150px"
              />
            </div>
            <div class="col-2">
              <BsButton @click="removeInteraction(index)" label="Remove" />
            </div>
          </div>
        </QCardSection>
      </QCard>
      <div v-else class="q-mt-md">No interactions added yet.</div>
    </div>
  </template>
  
  <script lang="ts">
  import { defineComponent } from 'vue';
  import type { PropType } from 'vue';
  import { BsButton, BsSelect } from 'quasar-ui-bs';
  import { QCard, QCardSection } from 'quasar';
  
  interface Column {
    name: string;
    // Add other properties if needed
  }
  
  interface Interaction {
    first: string;
    second: string;
  }
  
  export default defineComponent({
    name: 'VariableInteractions',
    components: {
      BsButton,
      BsSelect,
      QCard,
      QCardSection
    },
    props: {
      filteredColumns: {
        type: Array as PropType<Column[]>,
        required: true
      }
    },
    data() {
      return {
        interactions: [] as Interaction[]
      };
    },
    computed: {
      columnOptions(): string[] {
        return this.filteredColumns.map(column => column.name);
      },
      formattedInteractions(): string[] {
        return this.interactions.map(interaction => {
          return `${interaction.first}:${interaction.second}`;
        });
      }
    },
    methods: {
      addInteraction() {
        this.interactions.push({ first: '', second: '' });
      },
      removeInteraction(index: number) {
        this.interactions.splice(index, 1);
      }
    },
    watch: {
      interactions: {
        handler(newInteractions: Interaction[]) {
          this.$emit('update:interactions', this.formattedInteractions);
        },
        deep: true
      }
    }
  });
  </script>
  
  <style scoped>
  .interaction-variables {
    padding: 20px;
  }
  .variable-select-container {
    margin-top: 20px;
  }
  </style>