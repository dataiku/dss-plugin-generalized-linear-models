<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Stats will be generated for this model" />
        <BsSelect
            :modelValue="store.selectedModelString"
            :all-options="store.modelsString"
            @update:modelValue="updateModelString"
        />
        <div v-if="store.selectedModelString" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClickStats">Export</BsButton>
        </div>
    </div>
    </template>
    
    <script lang="ts">
    import { BsLayoutDefault } from "quasar-ui-bs";
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    
    export default defineComponent({
        emits: ["update:loading"],
        components: {
            BsLayoutDefault
        },
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
            async onClickStats() {
                this.loading = true;
                await this.store.exportStats();
                this.loading = false;
            },
        },
        mounted() { 
         }
    })
    </script>
    
    <style lang="scss" scoped>
        /* Copy styles from ModelVisualizationDrawer.vue */
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>