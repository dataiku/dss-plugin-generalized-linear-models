<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Charts will be generated with respect to this model" />
        <BsSelect
            :modelValue="store.selectedModelString"
            :all-options="store.modelsString.filter(option => option !== store.selectedModelString2)"
            @update:modelValue="updateModelString"
        />
        <div v-if="store.selectedModelString" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClick">Export Full Model</BsButton>
        </div>
        <BsCheckbox v-if="store.selectedModelString" v-model="store.includeSuspectVariables" label="Include Suspect Variables" />
        
        <BsLabel v-if="store.selectedModelString" label="Select a Variable" info-text="Charts will be generated with respect to this variable" />
        <BsSelect
            v-if="store.selectedModelString"
            v-model="selectedVariable"
            :all-options="store.variablePoints"
            @update:modelValue="updateVariable">
            </BsSelect>
        
        <BsCheckbox v-if="store.selectedModelString" v-model="store.rescale" @update:modelValue="updateRescale" label="Rescale?" />
        
        <BsLabel v-if="store.selectedModelString" label="Run Analysis on" />
        <BsToggle v-if="store.selectedModelString" v-model="store.trainTest" @update:modelValue="updateTrainTest" labelRight="Test" labelLeft="Train" />
        
        <div v-if="store.selectedVariable.variable" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClickOneWay">Export One-Way Data</BsButton>
        </div>
    
        <BsLabel v-if="store.selectedModelString" label="Compare with model" info-text="Second model to compare with the first one" />
        <BsSelect
            v-if="store.selectedModelString"
            :modelValue="store.selectedModelString2"
            :all-options="store.modelsString.filter(option => option !== store.selectedModelString)"
            @update:modelValue="updateModelString2"
        />
    </div>
    </template>
    
    <script lang="ts">
    // Script content is almost identical to ModelVisualizationDrawer.vue
    // We remove logic for other tabs like nbBins for lift chart.
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    import type { VariablePoint } from '../models';
    import { useLoader } from "../composables/use-loader";
    import { useNotification } from "../composables/use-notification";
    import { BsButton, BsCheckbox, BsToggle } from "quasar-ui-bs";
    
    export default defineComponent({
        // Props and emits can remain if needed
        emits: ["update:loading"],
        data() {
            return {
                store: useModelStore(),
                selectedVariable: {} as VariablePoint,
                loading: false as boolean
            };
        },
        watch: {
          loading(newVal) { this.$emit("update:loading", newVal); },
          selectedVariable(newValue: VariablePoint) {
            this.loading = true;
            this.store.selectedVariable = newValue;
            this.store.updateChartData();
            this.loading = false;
          },
        },
        methods: {
            async updateVariable(value: VariablePoint) {
              this.loading = true;
              this.store.selectedVariable = value;
              this.loading = false;
            },
            async updateTrainTest(value: boolean) {
              this.loading = true;
              await this.store.updateTrainTest(value);
              this.loading = false;
            },
            async updateRescale(value: boolean) {
                this.loading = true;
              this.store.rescale = value;
              await this.store.updateChartData();
              this.loading = false;
            },
            async updateModelString(value: string) {
                this.loading = true;
                await this.store.updateModelString(value);
              this.loading = false;
            },
            async updateModelString2(value: string) {
                this.loading = true;
                await this.store.updateModelString2(value);
              this.loading = false;
            },
            async onClick() {
                this.loading = true;
                await this.store.exportModel();
              this.loading = false;
            },
            async onClickOneWay() {
                this.loading = true;
                await this.store.exportOneWay();
              this.loading = false;
            },
            notifyError(msg: string) {
                useNotification("negative", msg);
            },
            handleError(msg: any) {
                this.loading = false;
                this.notifyError(msg);
            },
        },
        mounted() {
            this.loading = true;
            this.store.loadModels();
            this.loading = false;
        }
    })
    </script>
    
    <style lang="scss" scoped>
        /* Copy styles from ModelVisualizationDrawer.vue */
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>