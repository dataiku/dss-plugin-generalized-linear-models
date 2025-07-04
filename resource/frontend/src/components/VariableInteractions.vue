<!-- <template>
    <div class="interactions-container">
      <div v-if="interactions.length === 0" class="add-initial">
        <BsButton 
        unelevated
          no-caps
          color="primary" 
          class="q-mt-md"
          label="Add an interaction?" 
          @click="addInteraction"
        />
      </div>
      
      <div v-else class="interactions-list">
        <div class="interaction-header-row">
          <BsLabel class="interaction-label" label="Interaction"></BsLabel>
          <BsLabel class="variable-header" label="Variable 1"></BsLabel>
          <BsLabel class="variable-header" label="Variable 2"></BsLabel>
          <div class="action-header"></div>
        </div>
  
        <div v-for="(interaction, index) in interactions" :key="index" class="interaction-row">
          <BsLabel class="interaction-label" :label="'Interaction ' + (index + 1)"></BsLabel>
          <BsSelect
                :modelValue="interaction.first"
                class="interaction-select"
                :all-options="(filteredColumns as Column[]).map(col => col.name).filter(name => name !== interaction.second)"
                @update:modelValue="value => updateInteraction(index, 'first', value)"
                placeholder="Select first variable"
            />

            <BsSelect
                :modelValue="interaction.second"
                class="interaction-select"
                :all-options="(filteredColumns as Column[]).map(col => col.name).filter(name => name !== interaction.first)"
                @update:modelValue="value => updateInteraction(index, 'second', value)"
                placeholder="Select second variable"
            />
  
          <q-btn 
            color="negative" 
            flat
            icon="mdi-delete"
            class="remove-btn"
            @click="removeInteraction(index)"
          >
            <BsTooltip>Remove interaction</BsTooltip>
          </q-btn>
        </div>
  
        <BsButton 
        unelevated
          no-caps
          color="primary" 
          class="q-mt-md"
          label="Add another interaction" 
          @click="addInteraction"
        />
      </div>
    </div>
  </template> -->
  
  <template>
    <q-card flat bordered>
      <q-card-section>
        <div class="text-h6">Variable Interactions</div>
      </q-card-section>

      <q-separator />
  
      <q-card-section>
        <div class="interactions-container">
          <div v-if="interactions.length === 0" class="add-initial">
            <BsButton 
              unelevated
              no-caps
              color="primary" 
              label="Add an interaction?" 
              @click="addInteraction"
            />
          </div>
          
          <div v-else class="interactions-list">
    
            <div v-for="(interaction, index) in interactions" :key="index" class="interaction-row">
              

            <div class="interaction-name-col">
              <div class="static-name">{{ `Interaction ${index + 1}` }}</div>
            </div>
            
              <div class="variable-col">
              <BsLabel label="Select First Variable" class="field-label" />
              <BsSelect
                dense
                borderless
                :modelValue="interaction.first"
                class="variable-col"
                :all-options="(filteredColumns as Column[]).map(col => col.name).filter(name => name !== interaction.second)"
                @update:modelValue="value => updateInteraction(index, 'first', value)"
                placeholder="Select variable"
              />
            </div>
            <div class="variable-col">
              <BsLabel label="Select Second Variable" class="field-label" />
              <BsSelect
                dense
                borderless
                :modelValue="interaction.second"
                class="variable-col"
                :all-options="(filteredColumns as Column[]).map(col => col.name).filter(name => name !== interaction.first)"
                @update:modelValue="value => updateInteraction(index, 'second', value)"
                placeholder="Select variable"
              />
            </div>
    
              <div class="action-col">
                <q-btn 
                  color="negative" 
                  flat
                  round
                  dense
                  icon="mdi-delete"
                  @click="removeInteraction(index)"
                >
                  <BsTooltip>Remove interaction</BsTooltip>
                </q-btn>
              </div>
            </div>
            
            <div class="row justify-end q-mt-md">
              <BsButton 
                unelevated
                no-caps
                color="primary"
                label="Add another interaction" 
                @click="addInteraction"
              />
            </div>
          </div>
        </div>
      </q-card-section>
    </q-card>
  </template>
  
  <script lang="ts">
  // Remove PropType import - we'll use type casting instead
  import { defineComponent } from 'vue';
  
  interface Column {
    name: string;
  }
  
  interface Interaction {
    first: string;
    second: string;
  }
  
  export default defineComponent({
    name: 'VariableInteractions',
    
    props: {
    filteredColumns: {
      type: Array,
      required: true
    },
    initialInteractions: {
      type: Array,
      default: () => []
    }
  },
  
    data() {
      return {
        interactions: [] as Interaction[],
        internalUpdate: false,
        lastEmittedInteractions: [] as Interaction[]
      }
    },
  
    watch: {
        initialInteractions: {
        handler(newInteractions) {
            if (!this.internalUpdate && JSON.stringify(newInteractions) !== JSON.stringify(this.lastEmittedInteractions)) {
            console.log("Initial interactions updated:", newInteractions);
            if (newInteractions && newInteractions.length > 0) {
                this.interactions = (newInteractions as Interaction[]).map(interaction => ({
                first: interaction.first || '',
                second: interaction.second || ''
                }));
            } else {
                this.interactions = [];
            }
            this.lastEmittedInteractions = [...newInteractions] as Interaction[];
            }
        },
        deep: true
        }
    },

    created() {
        if (this.initialInteractions && this.initialInteractions.length > 0) {
        this.interactions = (this.initialInteractions as Interaction[]).map(interaction => ({
            first: interaction.first || '',
            second: interaction.second || ''
        }));
        this.lastEmittedInteractions = [...this.initialInteractions] as Interaction[];
        }
    },

  
    methods: {
      addInteraction() {
        this.internalUpdate = true;
        try {
          this.interactions.push({
            first: '',
            second: ''
          });
        } finally {
          this.internalUpdate = false;
        }
      },
  
      removeInteraction(index: number) {
        this.internalUpdate = true;
        try {
          this.interactions.splice(index, 1);
          this.emitUpdate();
        } finally {
          this.internalUpdate = false;
        }
      },
  
      updateInteraction(index: number, field: keyof Interaction, value: string) {
        this.internalUpdate = true;
        try {
          this.interactions[index][field] = value;
          this.emitUpdate();
        } finally {
          this.internalUpdate = false;
        }
      },
  
      emitUpdate() {
        const completeInteractions = this.interactions
          .filter(interaction => interaction.first && interaction.second)
          .map(interaction => ({
            first: interaction.first,
            second: interaction.second
          }));
        
        this.lastEmittedInteractions = completeInteractions;
        
        const formattedInteractions = completeInteractions
          .map(interaction => `${interaction.first}:${interaction.second}`);
        
        this.$emit('update:interactions', formattedInteractions);
      }
    }
  });
  </script>
  
  <style scoped>
  .interactions-container {
    padding: 1rem;
  }
  
  .interaction-header-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: center;
    font-weight: 600;
    color: #666;
    padding: 0 0.5rem;
  }
  
  .interaction-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: center;
  }
  
  .interaction-label {
    width: 100px;
    font-weight: 500;
    color: #666;
  }
  
  .variable-header {
    width: 200px;
    padding: 0 0.5rem;
  }
  
  .action-header {
    width: 40px;
  }
  
  .interaction-select {
    width: 200px;
    flex-shrink: 0;
  }
  
  .remove-btn {
    width: 40px;
    flex-shrink: 0;
  }
  
  .add-initial {
    text-align: center;
    padding: 2rem;
  }
  
  :deep(.q-btn) {
    text-transform: none;
  }

  .interactions-list {
  display: flex;
  flex-direction: column;
  gap: 24px; /* More spacing between each interaction row */
}

.interaction-row {
  display: flex;
  flex-direction: row;
  align-items: flex-end; /* Align to bottom for better label alignment */
  gap: 24px; /* Spacing between elements in a row */
}

.interaction-name-col {
  flex: 1.5;
  min-width: 150px;
}

.variable-col {
  flex: 2;
  min-width: 200px;
}

.action-col {
  flex: 0 0 40px;
  text-align: right;
  padding-bottom: 8px; /* Align button with inputs */
}

.field-label {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 4px;
  display: block;
}

.editable-name-display {
  border-bottom: 1px solid transparent; /* Reserve space for border */
  padding: 6px 0;
  cursor: text;
  &:hover {
    background-color: #f5f5f5;
  }
}

.editable-name {
  font-weight: 500;
}

.name-input {
  /* Style to match the look of the other inputs */
  border-bottom: 1px solid var(--q-primary);
}

.add-initial {
  text-align: center;
  padding: 20px;
}
  </style>