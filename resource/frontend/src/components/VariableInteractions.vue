    <template>
    <q-card flat bordered>
      <q-card-section class="title-section">
        <BsLabel class="section-title" label="Variable Interactions"/>
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
  import { BsLabel } from 'quasar-ui-bs';
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
    components: {
      BsLabel
    },
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
        },
        filteredColumns: {
          handler(newVal) {
            console.log("filteredColumns updated:", newVal);
          },
          immediate: true,
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
  
  .interaction-row {
    display: flex;
    margin-bottom: 1rem;
    /* align-items: center; */
    flex-direction: row;
    align-items: flex-end;
    gap: 24px;
  }
  
  :deep(.q-btn) {
    text-transform: none;
  }

  .interactions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  padding-bottom: 8px;
}

.field-label {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 4px;
  display: block;
}

.add-initial {
  text-align: center;
  padding: 20px;
}

.section-title {
    font-weight: 600;
    font-size: 16px;
    color: #333E48;
    margin-bottom: 6px;

}

.title-section {
  display: flex;
  justify-content: center;
}
  </style>