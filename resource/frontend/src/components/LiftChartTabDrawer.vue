<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Lift chart will be generated for this model" />
        <BsSelect
            :modelValue="store.selectedModelString"
            :all-options="store.modelsString"
            @update:modelValue="updateModelString"
        />
    
        <BsLabel v-if="store.selectedModelString" label="Select the number of bins" />
        <BsSlider v-if="store.selectedModelString" @update:modelValue="updateNbBins" v-model="store.nbBins" :min="2" :max="20" />
        
        <BsLabel v-if="store.selectedModelString" label="Run Analysis on" />
        <BsToggle v-if="store.selectedModelString" v-model="store.trainTest" @update:modelValue="updateTrainTest" labelRight="Test" labelLeft="Train"/>
    </div>
    </template>
    
<script lang="ts">
    import { BsLayoutDefault } from "quasar-ui-bs";
    import { defineComponent } from "vue";
    import EmptyState from './EmptyState.vue';
    import LiftChartTabContent from './LiftChartTabContent.vue'
    import { useModelStore } from "../stores/webapp";
    // ... other necessary imports
    
    export default defineComponent({
        components: {
            BsLayoutDefault,
            EmptyState,
            LiftChartTabContent
        },
        emits: ["update:loading"],
        data() { 
            return {
                store: useModelStore(),
                layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
                loading: false as boolean,
            };  
        },
        methods: {
            async updateModelString(value: string) {
                this.loading = true;
                await this.store.updateModelString(value);
              this.loading = false;
            },
            async updateNbBins(value: number) {
                this.loading = true;
                await this.store.updateNbBins(value);
                this.loading = false;
            },
            async updateTrainTest(value: boolean) {
              this.loading = true;
              await this.store.updateTrainTest(value);
              this.loading = false;
            },
        },
        mounted() { /* ... loadModels ... */ }
    })
    </script>
    
    <style lang="scss" scoped>
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>