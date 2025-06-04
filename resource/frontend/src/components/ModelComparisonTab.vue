
<template>
<BsTab name="Model Comparison" docTitle="GLM Analyzer" :docIcon="docLogo">
    <BsTabIcon>
        <img :src="comparisonIcon" alt="Target Definition Icon" />
    </BsTabIcon>
    <BsHeader>
        <BsButton   
            v-if="!layoutRef?.drawerOpen" flat round class="open-side-drawer-btn" size="15px"
            @click="closeSideDrawer" icon="mdi-arrow-right">
            <BsTooltip>Open sidebar</BsTooltip>
        </BsButton>
    </BsHeader>
    <BsDrawer>
        <BsCollapsiblePanel
        title="Model Selection">
        <div class="variable-select-container">
            <BsLabel
                label="Select Model 1 for Comparison"
                info-text="Model 1">
            </BsLabel>
            <BsSelect
                :modelValue="selectedModelString"
                :all-options="modelsString"
                @update:modelValue="updateModelString"
                style="min-width: 250px">
            </BsSelect>
            <BsLabel
                label="Select Model 2 for Comparison"
                info-text="Model 2">
            </BsLabel>
            <BsSelect 
                :modelValue="selectedModelTwoString"
                :all-options="modelsString"
                @update:modelValue="updateModelTwoString"
                style="min-width: 250px">
            </BsSelect>
            <BsLabel v-if="isVariableSelectEnabled"
                label="Run Analysis on">
            </BsLabel>
            <BsToggle
             v-if="isVariableSelectEnabled"
              @update:modelValue="updateTrainTest"
              v-model="trainTest" 
              labelRight="Test" 
              labelLeft="Train"/>
        </div>
        </BsCollapsiblePanel>
        <BsCollapsiblePanel
        title="Variable Analysis"
        v-if="isVariableSelectEnabled">
        <div class="variable-select-container">
            <BsLabel
                label="Select a Variable For Investigation"
                info-text="Variable to Investigate">
            </BsLabel>
            <BsSelect
                :modelValue="selectedVariable"
                :all-options="datasetColumns"
                @update:modelValue="updateVariableString"
                style="min-width: 150px">
            </BsSelect>
        </div>
        </BsCollapsiblePanel>
    </BsDrawer>
    <BsContent>
        <EmptyState
                class="tab-content"
                title="Model Comparison"
                subtitle="Select two models in the left to comapre"
                v-if="modelComparisonData.length==0"/>
            <div class="tab-content" v-else>
                <div>
                    <ModelComparisonChart
                    v-if="selectedVariable"
                        :Category="modelComparisonData.map(item => item.Category)"
                        :model_1_fittedAverage="modelComparisonData.map(item => item.model_1_fittedAverage)"
                        :model_1_observedAverage="modelComparisonData.map(item => item.model_1_observedAverage)"
                        :model1_baseLevelPrediction="modelComparisonData.map(item => item.model1_baseLevelPrediction)"
                        :model_2_observedAverage="modelComparisonData.map(item => item.model_2_observedAverage)"
                        :model_2_fittedAverage="modelComparisonData.map(item => item.model_2_fittedAverage)"
                        :exposure="modelComparisonData.map(item => item.Value)"
                        :observedAverage ="modelComparisonData.map(item => item.model_1_observedAverage)" 
                        :chartTitle="selectedVariable"
                        />
                </div>

                <div>
                    <BsTable
                        :title="comparisonChartTitle"
                        :rows="tableData"
                        :columns="tableColumns"
                        :globalSearch="false"
                        row-key="model"
                    />
                </div>
            </div>
    </BsContent>
    
</BsTab>

</template>

<script lang="ts">
import { defineComponent } from "vue";
import EmptyState from './EmptyState.vue';
import { BsTab, BsTabIcon, BsLayoutDefault, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip ,BsTable, BsToggle,} from "quasar-ui-bs";
import docLogo from "../assets/images/doc-logo-example.svg";
import comparisonIcon from "../assets/images/comparator.svg";
import { API } from '../Api';
import ModelComparisonChart from './ModelComparisonChart.vue'
import { useLoader } from "../composables/use-loader";
import type { QTableColumn } from 'quasar';

export default defineComponent({
components: {
    ModelComparisonChart,
    EmptyState,
    BsTab,
    BsTabIcon,
    BsHeader,
    BsButton,
    BsDrawer,
    BsContent,
    BsTooltip,
    BsTable,
    BsToggle
},
props: {
      reloadModels: {
        type: Boolean,
        default: false
      }
    },
data() {
    return {    
        datasetsString: [] as string[],
        chartData: [] as chartDataItem[],  
        layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
        comparisonIcon,
        docLogo,
        models: [] as Model[],
        selectedModelString: "",
        selectedModelTwoString: "", 
        selectedVariable : "", 
        modelDictionary: {} as { [key: string]: string }, 
        datasetColumns: columns,
        modelsString: [] as string[],
        comparisonChartTitle: "Model Metrics",
        modelMetrics: {} as ModelMetrics,
        modelComparisonData: [] as chartDataItem[],
        tableColumns: columns,
        loading: false,
        trainTest: false,
    };
},
computed:{
    isVariableSelectEnabled() {
        return this.selectedModelString !== "" && this.selectedModelTwoString !== "";
    },
    tableData() {
        if (!this.modelMetrics || !this.modelMetrics.models) {
        return []; // Return an empty array if the data is not (yet) available
            }
        const modelsArray = Object.keys(this.modelMetrics.models).map(modelKey => {
        const modelMetrics = this.modelMetrics.models[modelKey];
        console.log("Model Metrics", modelMetrics);
        return {
            model: modelKey, // This will be "Model_1", "Model_2", etc.
            AIC: modelMetrics.AIC,
            BIC: modelMetrics.BIC,
            Deviance: modelMetrics.Deviance
        };
    });

    return modelsArray;
        

    },
    tableColumns() {
        return [

            { name: 'model', label: 'Model', field: 'model', align: 'center' },
            { name: 'AIC', label: 'AIC', field: 'AIC', align: 'center' },
            { name: 'BIC', label: 'BIC', field: 'BIC', align: 'center' },
            { name: 'Deviance', label: 'Deviance', field: 'Deviance', align: 'center' },
        ];

    }
},
watch: {
    reloadModels: {
        handler() {
            this.loading = true;
            API.getModels().then((data: any) => {
                this.models = data.data;
                this.modelsString = this.models.map((item: { name: string }) => item.name);
                this.modelDictionary = this.models.reduce((acc: { [key: string]: string }, model: Model) => {
                                        acc[model.name] = model.id;
                                        return acc;
                                    }, {});
            
            });
            this.loading = false;
        },
    },
    loading(newVal) {
        if (newVal) {
            useLoader("Loading data..").show();
        } else {
            useLoader().hide();
        }
    },
},
methods: {
    closeSideDrawer() {
        if (this.layoutRef) {
            this.layoutRef.drawerOpen = !this.layoutRef.drawerOpen;
        }
    },
    async updateVariableString(value: string) {
        this.loading = true;
        this.selectedVariable = value;
        const payload = {
        model1: this.modelDictionary[this.selectedModelString],
        model2: this.modelDictionary[this.selectedModelTwoString],
        selectedVariable: this.selectedVariable,
        trainTest:this.trainTest
        }
        const dataResponse = await API.getModelComparisonData(payload);
        this.modelComparisonData = dataResponse?.data;
        console.log("Model Comparison data:", this.modelComparisonData );
        const ModelMetricsResponse = await API.getModelMetrics(payload);
        this.modelMetrics = ModelMetricsResponse?.data as ModelMetrics;

        console.log("Model Metric data:", this.modelMetrics);
        this.loading = false;

    },
    async updateTrainTest(value: boolean) {
        this.trainTest = value;
        if (this.selectedVariable) {
        await this.updateVariableString(this.selectedVariable);
    }
        },
    async updateModelString(value: string) {
        this.selectedModelString = value;
    },
    async updateModelTwoString(value: string) {
        this.selectedModelTwoString = value;
    },
    async getDatasetColumnNames() {
    try {
    const response = await API.getTrainDatasetColumnNames();
    console.log("Datasets:", response.data);
    this.datasetColumns = response.data;
    console.log("First assignment:", this.datasetColumns);
    } catch (error) {
        console.error('Error fetching datasets:', error);
        this.datasetColumns = [];
    }
}, 
},

mounted() {
    this.loading = true;
    API.getModels().then((data: any) => {
        this.models = data.data;
        console.log("Retrieved models are:", this.models);
        this.modelsString = this.models.map((item: { name: string }) => item.name);
        this.modelDictionary = this.models.reduce((acc: { [key: string]: string }, model: Model) => {
                                acc[model.name] = model.id;
                                return acc;
                            }, {});
    
    });
    this.getDatasetColumnNames();
    this.loading = false;
},
emits: ['update:modelValue']
})
interface chartDataItem{
    definingVariable: any;
    Category: any;
    model_1_observedAverage: any;
    model_1_fittedAverage: any;
    Value: number;
    model1_baseLevelPrediction: any;
    model_2_observedAverage: any;
    model_2_fittedAverage: any;
    model2_baseLevelPrediction: any;
}
interface Model {
    name: string;
    id: string; // or number, depending on your id type
}

interface ModelMetricsDataPoint {
    AIC: number;
    BIC: number;
    Deviance: number;
}

interface ModelMetrics {
    models: {
        [models: string]: ModelMetricsDataPoint; // Use an index signature for dynamic keys
    },
}

const columns: QTableColumn[] = [
    { name: 'model', align: 'left', label: 'Model', field: 'model', sortable: true },
    { name: 'AIC', align: 'left', label: 'AIC', field: 'AIC', sortable: true },
    { name: 'BIC', align: 'left', label: 'BIC', field: 'BIC', sortable: true },
    { name: 'Deviance', align: 'left', label: 'Deviance', field: 'Deviance', sortable: true },
];

</script>   
<style scoped>s
.row-spacing {
margin-bottom: 20px; /* Adjust this value as needed */
}
.column-management {
display: flex;
align-items: center; /* Align items vertically */
gap: 20px; /* Spacing between each item */
}
.form-group {
display: flex;
flex-direction: column; /* Stack the label and select vertically */
margin-bottom: 15px; /* Spacing between each form group */
}

.form-group label {
margin-bottom: 5px; /* Space between label and select */
}

/* If you want the label and dropdown to be on the same line, switch .form-group to row */
.form-group.row {
flex-direction: row;
align-items: center; /* Align items vertically */
}

.form-group.row label {
margin-right: 10px; /* Space between label and select, when inline */
margin-bottom: 0; /* Remove bottom margin when inline */
}

.form-group.row select {
flex-grow: 1; /* Let the select take up available space */
}
.outline-box {
border: 2px solid #000; /* Solid black border, adjust as needed */
padding: 20px; /* Optional: Adds some spacing inside the box */
margin: 20px 0; /* Optional: Adds some spacing outside the box */
background-color: #f5f5f5; 
}
.close-side-drawer-btn {
color: var(--interactions-bs-color-interaction-primary, #2b66ff);
position: absolute;
top: 7px;
right: 10px;
z-index: 1000;
}
.open-side-drawer-btn {
color: var(--interactions-bs-color-interaction-primary, #2b66ff);
position: relative;
top: 4px;
}
.column-name {
min-width: 100px; /* Adjust based on your layout */
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
}
.h5-spacing {
margin-bottom: 10px;
margin-top: 5px;
}
.variable-select-container {
    padding: 20px;
}
.model-name-input-container {
    padding: 20px
}

.model-name-input {
    width: 87%;
    padding: 15px;
    border: 1px solid #ccc;
    border-radius: 4px;
}
.error-message {
    color: red;
    margin-top: 10px;
}
.tab-content {
padding-left: 0px;
flex-direction: row;
padding-right: 0px;
padding-top: 20px;
display: flex;
align-items: center;
gap: var(--bs-spacing-13, 52px);
min-height: 350px;
min-width: 700px;
}
</style>



