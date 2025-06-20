<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Stats will be generated for this model" />
        <BsSelect
            :modelValue="store.activeModelName"
            :all-options="store.modelOptions"
            @update:modelValue="onModelChange"
        />
        <div v-if="store.activeModelName" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClickStats">Export</BsButton>
        </div>
    </div>
    </template>
    
    <script lang="ts">
    import { BsLayoutDefault } from "quasar-ui-bs";
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    import { useOneWayChartStore } from "../stores/oneWayChartStore.ts"
    import { useLiftChartStore } from "../stores/liftChartStore.ts"
    import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore.ts"
    
    export default defineComponent({
        emits: ["update:loading"],
        data() { 
            return {
                store: useModelStore(),
                variableStatsStore: useVariableLevelStatsStore(),
                oneWayStore: useOneWayChartStore(),
                liftChartStore: useLiftChartStore(),
                loading: false as boolean,
            };  
        },
        watch: {
          isLoading(newVal: any) { this.$emit("update:loading", newVal); },
          'store.activeModel': {
              handler(newModel) {
                  if (newModel?.id) {
                      this.oneWayStore.fetchVariablesForModel(newModel.id);
                      this.liftChartStore.fetchLiftData(newModel.id);
                      this.variableStatsStore.fetchStatsForModel(newModel.id);
                  }
              },
              deep: true
            }
        },
        methods: {
            async onModelChange(value: string) {
                this.store.setActiveModel(value);
            },
            async onClickStats() {
                this.variableStatsStore.exportVariableLevelStats();
            },
        },
        computed: {
          isLoading() { 
            return this.store.isLoading || this.variableStatsStore.isLoading;
          }
        },
        mounted() { 
         }
    })
    </script>
    
    <style lang="scss" scoped>
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>