<template>
    <div class="layout">
        <div class="tab-content-wrapper">
            <div class="left-column">
            <ModelTrainingConfiguration/>
        </div>

        <div class="right-column">
            <VariableConfiguration/>
            <VariableInteractions
                :filtered-columns="selectedColumns"
                :initial-interactions="store.previousInteractions"
                @update:interactions="store.updateInteractions"
            />
            </div>
        </div>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import EmptyState from './EmptyState.vue';
    import ModelTrainingConfiguration from './ModelTrainingConfiguration.vue';
    import VariableConfiguration from './VariableConfiguration.vue';
    import { BsTab, BsLabel, BsTabIcon, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip, BsSlider, BsCard } from "quasar-ui-bs";
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
        ModelTrainingConfiguration,
        VariableConfiguration
    
    },
    props: [],
    data() {
        return {
            store: useTrainingStore(),
        };
    },
    computed:{
        filteredColumns() {
                return this.store.datasetColumns.filter(column =>
                    column.role !== 'Target' &&
                    column.role !== 'Exposure')
            },
        selectedColumns() {
            console.log("Selected columns computed:", this.store.datasetColumns);
            return this.store.datasetColumns.filter(column =>
                column.role != 'Target' && column.role != 'Exposure' && column.isIncluded == true)
            },
    },
    watch: {
        "store.datasetColumns": {
            handler(newVal) {
                this.store.updateDatasetColumnsPreprocessing();
            },
            deep: true
        }
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
    padding-left: 0;
    padding-top: 20px;
    display: flex;
    flex-direction: row;
    gap: 40px; /* Adjust spacing between columns */
    align-items: flex-start; /* Aligns items to the top */
}

.left-column {
    flex: 0 0 300px; /* Does not grow, does not shrink, base width is 350px */
}

.right-column {
    flex: 1; /* Takes up the remaining available space */
    display: flex;
    flex-direction: column;
    gap: 30px; /* Spacing between the cards in the right column */
}

.layout {
    margin: 0 auto;
    padding: 2rem;
}
</style>