<template>
    <div class="tab-content-wrapper">
    <q-card-section>
                <BsLabel class="bs-font-medium-4-semi-bold" label="Feature Handling"></BsLabel>
            </q-card-section>
            <q-card class="q-pa-xl">
                <div v-for="(column, index) in filteredColumns" class="column-management row-spacing">
                    <div class="column-name-container">
                        <BsLabel :label="store.abbreviateColumnName(column.name)"></BsLabel>
                    </div>
                    <div class="checkbox-container">
                        <BsCheckbox v-model="column.isIncluded" label="Include?" class="custom-label-spacing"></BsCheckbox>
                    </div>
                    <div class="radio-group-container">
                        <div class="q-gutter-sm row items-center bs-colored-text">
                            <q-radio v-model="column.type as any" val="numerical" label="Numerical" />
                        </div>
                        <div class="q-gutter-sm row items-center bs-colored-text">
                            <q-radio v-model="column.type as any" val="categorical" label="Categorical" />
                        </div>
                    </div>
                    <div class="radio-group-container">
                        <div class="q-gutter-sm row items-center">
                            <BsSelect
                                label=""
                                :modelValue="column.baseLevel"
                                :all-options="column.options"
                                @update:modelValue="value => column.baseLevel = value">
                            </BsSelect>
                        </div>
                    </div>
                </div>
                
            </q-card>
            <q-card-section>
                <BsLabel class="bs-font-medium-4-semi-bold" label="Variable Interactions"></BsLabel>
            </q-card-section>
            <q-card class="q-pa-xl">
            <VariableInteractions
                :filtered-columns="selectedColumns"
                :initial-interactions="store.previousInteractions"
                 @update:interactions="store.updateInteractions"
            />
            </q-card>
        </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import EmptyState from './EmptyState.vue';
    import { BsTab, BsLabel, BsTabIcon, BsLayoutDefault, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip, BsSlider, BsCard } from "quasar-ui-bs";
    import docLogo from "../assets/images/doc-logo-example.svg";
    import trainingIcon from "../assets/images/training.svg";
    import { QRadio } from 'quasar';
    import VariableInteractions from './VariableInteractions.vue'
    import { useTrainingStore } from "../stores/training";
    
    export default defineComponent({
    components: {
        EmptyState,
        VariableInteractions,
        BsTab,
        BsLabel,
        BsTabIcon,
        BsHeader,
        BsButton,
        BsDrawer,
        BsContent,
        BsTooltip,
        QRadio,
        BsSlider,
        BsCard,
    
    },
    props: [],
    data() {
        return {
            updateModels: false,
            store: useTrainingStore(),
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            trainingIcon,
            docLogo,
            errorMessage: "" as string,
        };
    },
    computed:{
        filteredColumns() {
                return this.store.datasetColumns.filter(column =>
                    column.role !== 'Target' &&
                    column.role !== 'Exposure')
            },
        selectedColumns() {
            return this.store.datasetColumns.filter(column =>
                column.role == 'Variable' && column.isIncluded == true)
            },
    },
    watch: {
        "store.datasetColumns": {
            handler(newVal) {
                this.store.updateDatasetColumnsPreprocessing();
            },
            deep: true
        },        
        
    }
})
</script>   
    <style scoped>
    .row-spacing {
    margin-bottom: 20px; /* Adjust this value as needed */
}
.column-management {
    display: flex;
    flex-direction: row;
    align-items: center; /* Align items vertically */
    gap: 10px; /* Spacing between each item */
    justify-content: space-between;
}
.custom-label-spacing {
    margin-right: 10px; /* Adjust the margin as needed */
    margin-left: 10px;
    padding: 5px;       /* Adjust padding for better alignment and spacing */
}
.radio-group-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: center;
    flex: 1;
}

.checkbox-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: left;
}
.column-name-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: left;
    min-width: 150px;
}
.tab-content-wrapper {
    padding-left: 20px;
    padding-top: 20px;
}
</style>