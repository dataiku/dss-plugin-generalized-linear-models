<template>
    <div class="drawer-container">
        <div class="scrollable-content">
            <BsCollapsiblePanel title="Configure">
                <div class="variable-select-container">
                    <BsLabel label="Select model *" info-text="Charts will be generated with respect to this model" />
                    <BsSelect
                        :modelValue="store.activeModelName"
                        :all-options="store.modelOptions.filter(option => option !== store.comparedModelName)"
                        @update:modelValue="onPrimaryModelChange"
                    />

                    <BsLabel v-if="store.activeModelName" label="Select variable *" info-text="Charts will be generated with respect to this variable" />
                    <BsSelect
                        v-if="store.activeModelName"
                        v-model="oneWayStore.formOptions.selectedVariable"
                        :all-options="oneWayStore.variableOptions"
                        @update:modelValue="onVariableChange"
                    >
                        <template v-slot:selected-item="scope">
                            <q-item v-if="scope.opt">
                            {{ oneWayStore.formOptions.selectedVariable?.variable }}
                            </q-item>
                        </template>
                        <template #option="props">
                            <q-item v-if="props.opt.isInModel || oneWayStore.includeSuspectVariables" v-bind="props.itemProps" clickable>
                                <q-item-section side>
                                    <div v-if="props.opt.isInModel">selected</div>
                                    <div v-else>unselected</div>
                                </q-item-section>
                                    <q-item-section class="bs-font-medium-2-normal">
                                        {{ props.opt.variable }}
                                    </q-item-section>
                                </q-item>
                        </template>
                    </BsSelect>

                    <BsLabel v-if="store.activeModelName" label="Level order" info-text="Levels on the X-axis will be ordered as defined" />
                    <BsSelect v-if="store.activeModelName"
                        :modelValue="oneWayStore.formOptions.levelOrder"
                        :all-options="levelOrderOptions"
                        @update:model-value="onLevelOrderChange"
                    />
            
                    <BsLabel v-if="store.activeModelName" label="Chart distribution" info-text="Display the raw values or bin them" />
                    <BsSelect v-if="store.activeModelName" 
                        :modelValue="oneWayStore.formOptions.chartDistribution"
                        :all-options="chartDistributionOptions"
                        @update:model-value="onChartDistributionChange"
                    />

                    <BsLabel v-if="store.activeModelName && oneWayStore.formOptions.chartDistribution == 'Binning'" label="Select the number of bins" />
                    <BsSlider v-if="store.activeModelName && oneWayStore.formOptions.chartDistribution == 'Binning'" @update:modelValue="onNbBinsChange" v-model="oneWayStore.formOptions.nbBins" :min="2" :max="30" />
                    <BsLabel v-if="store.activeModelName" label="Chart rescaling" info-text="Rescale the chart on base level, or compute the ratio between predicted and observed" />
                    <BsSelect v-if="store.activeModelName" 
                        :modelValue="oneWayStore.formOptions.chartRescaling"
                        :all-options="chartRescalingOptions"
                        @update:model-value="onChartRescalingChange"
                    />
                    <BsCheckbox v-if="store.activeModelName" v-model="oneWayStore.includeSuspectVariables" label="Include Suspect Variables" />
                        <div class="train-test-wrapper">
                            <BsLabel v-if="store.activeModelName" label="Run analysis on dataset " />
                            <GLMToggle v-if="store.activeModelName" v-model="trainTestValue" @update:model-value="onTrainTestChange" option1="Train" option2="Test" />
                        </div>
                </div>
            </BsCollapsiblePanel>
            <BsCollapsiblePanel title="Compare (optional)">
                <div class="variable-select-container">
                    <BsLabel v-if="store.activeModelName" label="Select model" info-text="Second model to compare with the first one" />
                    <BsSelect
                        clearable
                        v-if="store.activeModelName"
                        :modelValue="store.comparedModelName"
                        :all-options="comparisonModelOptions"
                        @update:modelValue="onComparisonModelChange"
                    />
                    </div>
            </BsCollapsiblePanel>
            
        </div>
        <div class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps :disabled="isFormUnchanged" @click="onCreateChart">Create Chart</BsButton>
        </div>
    </div>
</template>
    
<script lang="ts">
import { defineComponent } from "vue";
import { useModelStore } from "../stores/webapp";
import { useOneWayChartStore } from "../stores/oneWayChartStore"
import { useLiftChartStore } from "../stores/liftChartStore"
import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore"
import { VariablePoint } from "../models";
import GLMToggle from './GLMToggle.vue'

export default defineComponent({
    components: {
        GLMToggle
    },
    data() {
        return {
            store: useModelStore(),
            oneWayStore: useOneWayChartStore(),
            liftChartStore: useLiftChartStore(),
            variableStatsStore: useVariableLevelStatsStore(),
            levelOrderOptions: ["Natural order", "Ascending observed", "Ascending predicted", "Descending observed", "Descending predicted"],
            chartDistributionOptions: ["Raw data", "Binning"],
            chartRescalingOptions: ["None", "Base level", "Ratio"]
        };
    },
    computed: {
        trainTestValue() {
        return this.store.trainTest ? 'Train' : 'Test';
        },
        isFormUnchanged() {
        const form = this.oneWayStore.formOptions;
        const chart = this.oneWayStore.chartOptions;
        return (
            form.selectedVariable?.variable === chart.selectedVariable?.variable &&
            form.levelOrder === chart.levelOrder &&
            form.chartDistribution === chart.chartDistribution &&
            form.nbBins === chart.nbBins &&
            form.chartRescaling === chart.chartRescaling &&
            form.trainTest === chart.trainTest &&
            form.comparisonModel === chart.comparisonModel
        );
        },
        comparisonModelOptions() {
            const availableModels = this.store.modelOptions.filter(
                option => option !== this.store.activeModelName
            );
            
            return availableModels;
        }
    },
    methods: {
        async onPrimaryModelChange(value: string) {
            this.store.resetState();
            this.oneWayStore.resetState();
            this.store.setActiveModel(value);
            this.oneWayStore.fetchVariablesForModel(value);
        },
        async onComparisonModelChange(value: string | null) {
            this.store.setComparedModel(value);
            this.oneWayStore.setComparisonModel(value);
            if (this.oneWayStore.formOptions.selectedVariable) {
                await this.oneWayStore.selectVariable(this.oneWayStore.formOptions.selectedVariable);
                if (this.oneWayStore.comparisonChartData.length == 0) {
                    await this.oneWayStore.processAndFilterData();
                }
            }
        },
        async onVariableChange(value: VariablePoint) {
            this.oneWayStore.selectVariable(value);
        },
        async onClickOneWay() {
            this.oneWayStore.exportOneWayChart();
        },
        async onClick() {
            this.store.exportActiveModel();
        },
        async onCreateChart() {
            await this.oneWayStore.createChart();
        },
        async onChartRescalingChange(value: string) {
            this.oneWayStore.setRescale(value);
        },
        async onChartDistributionChange(value: string) {
            this.oneWayStore.setChartDistribution(value);
        },
        async onNbBinsChange(value: number) {
            this.oneWayStore.setNbBins(value);
        },
        async onLevelOrderChange(value: string) {
            this.oneWayStore.setLevelOrder(value);
        },
        async onTrainTestChange(value: string) {
            this.oneWayStore.setTrainTest(value == 'Train' ? true : false);
            this.store.setTrainTest(value == 'Train' ? true : false);
        }
    },
    mounted() {
        this.store.loadModels();
    }
})
</script>

<style lang="scss" scoped>
.variable-select-container {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.drawer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 72px;
}

.button-container {
  position: sticky;
  bottom: 0;
  z-index: 1;
  background: #fff;
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
}

.train-test-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
}

.bs-primary-button {
    background-color:#2B66FF;
    color: white;
}
</style>