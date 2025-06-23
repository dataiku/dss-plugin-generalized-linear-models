<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Lift chart will be generated for this model" />
        <BsSelect
            :modelValue="store.activeModelName"
            :all-options="store.modelOptions"
            @update:modelValue="onModelChange"
        />
    
        <BsLabel v-if="store.activeModelName" label="Select the number of bins" />
        <BsSlider v-if="store.activeModelName" @update:modelValue="onNbBinsChange" v-model="liftChartStore.nbBins" :min="2" :max="20" />
        
        <BsLabel v-if="store.activeModelName" label="Run Analysis on" />
        <BsToggle v-if="store.activeModelName" v-model="store.trainTest" @update:modelValue="onTrainTestChange" labelRight="Test" labelLeft="Train"/>
    </div>
    </template>
    
<script lang="ts">
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
                oneWayStore: useOneWayChartStore(),
                liftChartStore: useLiftChartStore(),
                variableStatsStore: useVariableLevelStatsStore()
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
            },
            'store.trainTest': {
              handler(trainTest) {
                  this.oneWayStore.processAndFilterData();
                  this.liftChartStore.updateTrainTest(trainTest);
              },
              deep: true
            }
        },
        methods: {
            async onModelChange(value: string) {
                this.store.setActiveModel(value);
            },
            async onNbBinsChange(value: number) {
                this.liftChartStore.updateNbBins(value);
            },
            async onTrainTestChange(value: boolean) {
                this.liftChartStore.updateTrainTest(value);
            }
        },
        mounted() {}
    })
    </script>
    
    <style lang="scss" scoped>
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>