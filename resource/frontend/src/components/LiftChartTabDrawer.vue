<template> 
    <div class="scrollable-content">
        <BsCollapsiblePanel title="Configure">
            <div class="variable-select-container">
                <BsLabel label="Select a model" info-text="Lift chart will be generated for this model" />
                <BsSelect
                    :model-value="store.activeModelName"
                    :all-options="store.modelOptions"
                    @update:modelValue="onModelChange"
                />
    
                <BsLabel label="Select the number of bins" />
                <BsSlider @update:modelValue="onNbBinsChange" v-model="liftChartStore.formOptions.nbBins" :min="2" :max="20" />
        
                <div class="train-test-wrapper">
                    <BsLabel label="Run analysis on dataset " />
                    <GLMToggle v-model="trainTestValue" @update:model-value="onTrainTestChange" option1="Train" option2="Test" />
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
import { useOneWayChartStore } from "../stores/oneWayChartStore"
import { useLiftChartStore } from "../stores/liftChartStore"
import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore"
import GLMToggle from "./GLMToggle.vue";

export default defineComponent({
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
            return (
                form.model === chart.model &&
                form.nbBins === chart.nbBins &&
                form.trainTest === chart.trainTest
            );
        },
    },
    methods: {
        async onModelChange(value: string) {
            this.liftChartStore.formOptions.model = value;
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
    }
})
</script>

<style lang="scss" scoped>
.variable-select-container {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.button-container {
    margin-top: 12px;
}

 .train-test-wrapper {
     display: flex;
     align-items: center;
     justify-content: space-between;
     gap: 12px;
 }

.bs-primary-button {
    background-color:#2B66FF;
    color: white;
}

.button-container {
    display: flex;
    justify-content: flex-end;
    width: 100%; 
    padding: 16px 0;
    margin-bottom: 30px;
}
</style>