<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Charts will be generated with respect to this model" />
        <BsSelect
            :modelValue="store.activeModelName"
            :all-options="store.modelOptions.filter(option => option !== store.comparedModelName)"
            @update:modelValue="onPrimaryModelChange"
        />
        <div v-if="store.comparedModelName" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClick">Export Full Model</BsButton>
        </div>
        <BsCheckbox v-if="store.activeModelName" v-model="oneWayStore.includeSuspectVariables" label="Include Suspect Variables" />
        
        <BsLabel v-if="store.activeModelName" label="Select a Variable" info-text="Charts will be generated with respect to this variable" />
        <BsSelect
              v-if="store.activeModelName"
                  v-model="oneWayStore.selectedVariable"
                  :all-options="oneWayStore.variableOptions"
                  @update:modelValue="onVariableChange">
                  <template v-slot:selected-item="scope">
                    <q-item v-if="scope.opt">
                      {{ oneWayStore.selectedVariable?.variable }}
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
        
        <BsCheckbox v-if="store.activeModelName" v-model="oneWayStore.rescale" @update:model-value="onRescaleChange" label="Rescale?" />
        
        <BsLabel v-if="store.activeModelName" label="Run Analysis on" />
        <BsToggle v-if="store.activeModelName" v-model="store.trainTest" @update:model-value="onTrainTestChange" labelRight="Test" labelLeft="Train" />
        
        <div v-if="store.activeModelName" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClickOneWay">Export One-Way Data</BsButton>
        </div>
    
        <BsLabel v-if="store.activeModelName" label="Compare with model" info-text="Second model to compare with the first one" />
        <BsSelect
            v-if="store.activeModelName"
            :modelValue="store.comparedModelName"
            :all-options="store.modelOptions.filter(option => option !== store.activeModelName)"
            @update:modelValue="onComparisonModelChange"
        />
    </div>
    </template>
    
    <script lang="ts">
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    import { useOneWayChartStore } from "../stores/oneWayChartStore.ts"
    import { useLiftChartStore } from "../stores/liftChartStore.ts"
    import { useVariableLevelStatsStore } from "../stores/variableLevelStatsStore.ts"
import { VariablePoint } from "src/models";
    
    export default defineComponent({
        emits: ["update:loading"],
        data() {
            return {
                store: useModelStore(),
                oneWayStore: useOneWayChartStore(),
                liftChartStore: useLiftChartStore(),
                variableStatsStore: useVariableLevelStatsStore(),
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
        computed: {
          isLoading() { 
            return this.store.isLoading || this.oneWayStore.isLoading;
          }
        },
        methods: {
            async onPrimaryModelChange(value: string) {
                this.store.setActiveModel(value);
            },
            async onComparisonModelChange(value: string | null) {
                this.store.setComparedModel(value);
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
            async onRescaleChange(value: boolean) {
                this.oneWayStore.setRescale(value)
                this.oneWayStore.processAndFilterData();
            },
            async onTrainTestChange(value: boolean) {
                if (this.oneWayStore.selectedVariable) {
                    this.store.setTrainTest(value)
                    this.oneWayStore.selectVariable(this.oneWayStore.selectedVariable)
                }
            }
        },
        mounted() {
            this.store.loadModels();
        }
    })
    </script>
    
    <style lang="scss" scoped>
        /* Copy styles from ModelVisualizationDrawer.vue */
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>