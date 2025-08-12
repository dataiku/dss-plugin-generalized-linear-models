<template>
    
    <div class="scrollable-content">
        <BsCollapsiblePanel title="Configure">
            <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Lift chart will be generated for this model" />
        <BsSelect
            :modelValue="store.activeModelName"
            :all-options="store.modelOptions"
            @update:modelValue="onModelChange"
        />
    
        <BsLabel v-if="store.activeModelName" label="Select the number of bins" />
        <BsSlider v-if="store.activeModelName" @update:modelValue="onNbBinsChange" v-model="liftChartStore.formOptions.nbBins" :min="2" :max="20" />
        
        <div class="train-test-wrapper">
            <BsLabel v-if="store.activeModelName" label="Run analysis on dataset " />
            <GLMToggle v-if="store.activeModelName" v-model="trainTestValue" @update:model-value="onTrainTestChange" option1="Train" option2="Test" />
        </div>

        <div class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" :disabled="isFormUnchanged" @click="onCreateChart">Create Chart</BsButton>
        </div>
        </div>
        </BsCollapsiblePanel>
    </div>
    
    </template>
    
<script lang="ts">
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    import { useOneWayChartStore } from "../stores/oneWayChartStore.ts"
    import { useLiftChartStore } from "../stores/liftChartStore.ts"
    import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore.ts"
    import GLMToggle from "./GLMToggle.vue";
    
    export default defineComponent({
        emits: ["update:loading"],
        components: {
            GLMToggle
        },
        data() { 
            return {
                store: useModelStore(),
                oneWayStore: useOneWayChartStore(),
                liftChartStore: useLiftChartStore(),
                variableStatsStore: useVariableLevelStatsStore()
            };  
        },
        computed: {
            trainTestValue() {
                return this.store.trainTest ? 'Train' : 'Test';
            },
            isFormUnchanged() {
                const form = this.liftChartStore.formOptions;
                const chart = this.liftChartStore.chartOptions;
                console.log(form);
                console.log(chart);
                return (
                    form.model === chart.model &&
                    form.nbBins === chart.nbBins &&
                    form.trainTest === chart.trainTest
                );
            },
            isLoading() { 
                return this.liftChartStore.isLoading;
            },
        },
        watch: {
          isLoading(newVal: any) { this.$emit("update:loading", newVal); },
          'store.activeModel': {
              handler(newModel) {
                  if (newModel?.id) {
                      this.oneWayStore.fetchVariablesForModel(newModel.id);
                      this.liftChartStore.fetchLiftData();
                      this.variableStatsStore.fetchStatsForModel(newModel.id);
                  }
              },
              deep: true
            },
            'store.trainTest': {
              handler(trainTest) {
                  this.liftChartStore.setTrainTest(trainTest);
              },
              deep: true
            }
        },
        methods: {
            async onModelChange(value: string) {
                console.log("on model change")
                this.liftChartStore.formOptions.model = value;
                this.store.setActiveModel(value);
                console.log(this.liftChartStore.formOptions);
            },
            async onNbBinsChange(value: number) {
                this.liftChartStore.setNbBins(value);
            },
            async onTrainTestChange(value: string) {
                this.store.setTrainTest(value == 'Train' ? true : false);
                this.liftChartStore.setTrainTest(value == 'Train' ? true : false);
            },
            async onCreateChart() {
                await this.liftChartStore.applyForm();
                await this.liftChartStore.fetchLiftData();
            },
        },
        mounted() {}
    })
    </script>
    
    <style lang="scss" scoped>
        .variable-select-container { padding: 20px }
        .button-container { margin-top: 12px; }

        .train-test-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .bs-primary-button {
            background-color:#2B66FF;
            color: white;
        }

        .button-container { display: flex;
                        justify-content: flex-end;
                        width: 100%; 
                        padding: 20px;
                        margin-bottom: 30px;}
    </style>