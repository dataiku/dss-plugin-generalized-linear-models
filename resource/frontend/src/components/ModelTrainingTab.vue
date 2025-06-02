<template>
    <BsTab name="Model Training" docTitle="GLM Analyzer" :docIcon="docLogo">
        <BsTabIcon>
            <img :src="trainingIcon" alt="Target Definition Icon" />
        </BsTabIcon>
        <BsHeader>
            <BsButton
                v-if="!layoutRef?.drawerOpen" flat round class="open-side-drawer-btn" size="15px"
                @click="closeSideDrawer" icon="mdi-arrow-right">
                <BsTooltip>Open sidebar</BsTooltip>
            </BsButton>
        </BsHeader>
        <BsDrawer>
            <q-scroll-area style="height: calc(100vh - 100px); max-width: 100%">
            <BsCollapsiblePanel
            title="Model Parameters">
                <div class="variable-select-container">
                <BsLabel
                    label="Load a previous model"
                    info-text="Charts will be generated with respect to this model">
                </BsLabel>
                <BsSelect
                    :modelValue="selectedModelString"
                    :all-options="modelsString"
                    @update:modelValue="value => getDatasetColumns(value)"
                    style="min-width: 250px">
                </BsSelect>
                <BsLabel
                        label="Select a Distribution Function"
                        info-text="Distribution function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="selectedDistributionFunctionString"
                    :all-options="distributionOptions"
                    @update:modelValue="value => updateModelProperty('selectedDistributionFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
                <BsLabel
                        label="Select a Link Function"
                        info-text="Link function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="selectedLinkFunctionString"
                    :all-options="linkOptions"
                    @update:modelValue="value => updateModelProperty('selectedLinkFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
            </div>
             </BsCollapsiblePanel>
            <BsCollapsiblePanel
            title="Regularization">
            <div class="variable-select-container">
            <BsLabel
                    label="Set the Elastic Net Penalty"
                    info-text="The overall level of regularization"
            ></BsLabel>
            <BsSlider
                v-model="selectedElasticNetPenalty"
                :min="0"
                :step="0.01"
                :max="1000"
                style="min-width: 150px">
            </BsSlider>
            <BsLabel
                    label="Set the L1 Ratio"
                    info-text="l1_ratio = 0 means Ridge (only L2), l1_ratio = 1 means LASSO (only L1)"
            ></BsLabel>
            <BsSlider
                v-model="selectedL1Ratio"
                :min="0"
                :max="1"
                :step="0.01"
                style="min-width: 150px">
            </BsSlider>
    
            </div>
            </BsCollapsiblePanel>
            <BsCollapsiblePanel
            title="Model Training"
            >
            <div class="model-name-input-container">
                <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
                <input
                v-model="modelName"
                type="text"
                id="modelNameInput"
                placeholder="Enter model name"
                class="model-name-input"
                />
            <q-btn 
            color="primary" 
            class="q-mt-md" 
            label="Train Model" 
            @click="submitVariables"></q-btn>
            
            </div>
            </BsCollapsiblePanel>
        </q-scroll-area>
            <BsButton
                flat
                round
                class="close-side-drawer-btn"
                size="15px"
                @click="closeSideDrawer"
                icon="mdi-arrow-left">
                <BsTooltip>Close sidebar</BsTooltip>
            </BsButton>
        
        </BsDrawer>
        <BsContent>
            <q-card-section>
                <h5>Feature Handling</h5>
            </q-card-section>
            <q-card class="q-pa-xl">
                <div v-for="(column, index) in filteredColumns" class="column-management row-spacing">
                    <div class="column-name-container">
                        <h6 class="column-name">{{ abbreviateColumnName(column.name) }}</h6>
                    </div>
                    <div class="checkbox-container">
                        <BsCheckbox v-model="column.isIncluded" label="Include?" class="custom-label-spacing"></BsCheckbox>
                    </div>
                    <div class="radio-group-container">
                        <div class="q-gutter-sm row items-center">
                            <q-radio v-model="column.type as any" val="numerical" label="Numerical" />
                        </div>
                        <div class="q-gutter-sm row items-center">
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
                <h5>Variable Interactions</h5>
            </q-card-section>
            <q-card class="q-pa-xl">
            <VariableInteractions
                :filtered-columns="filteredColumns"
                :initial-interactions="previousInteractions"
                 @update:interactions="updateInteractions"
            />
            </q-card>
        </BsContent>
    
    </BsTab>
    
    </template>
    
    <script lang="ts">
    type ColumnPropertyKeys = 'isIncluded' | 'role' | 'type' | 'preprocessing' | 'baseLevel' | 'options';
    type UpdatableProperties = 'selectedDatasetString' | 'selectedDistributionFunctionString' | 'selectedLinkFunctionString';
    interface MLTaskParams {
    params: {
        [key: string]: {
            role: string;
            type: string;
            handling: string;
            baseLevel?: string;
        }
    };
    target_column: string;
    exposure_column: string;
    distribution_function: string;
    link_function: string;
    elastic_net_penalty?: number;
    l1_ratio?: number;
    interactions?: Array<{
        first: string;
        second: string;
    }>;
    }
    interface APIResponse {
    data: MLTaskParams;
    }   
    interface TypeWithValue {
      value: string;
    }
    interface Interaction {
        first: string;
        second: string;
    }
    interface Model {
        id: string;
        name: string;
    }
    interface ErrorResponse {
        error: string;
    }
    interface Column {
            name: string;
            isIncluded: boolean;
            role: string;
            type: string;
            preprocessing: string;
            baseLevel: string;
            options: Array<string>;
            }
    interface ColumnInput {
            column: string;
            baseLevel: string;
            options: Array<string>;
            }
    interface SelectionOption {
    label: string;
    value: string; 
    }
    interface AccType {
    [key: string]: {
    role: string;
    type: string;
    processing: string;
    included: boolean;
    base_level: string;
    };
    }
    import { defineComponent } from "vue";
    import type { ModelPoint } from '../models';
    import EmptyState from './EmptyState.vue';
    import { BsTab, BsTabIcon, BsLayoutDefault, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip, BsSlider, BsCard } from "quasar-ui-bs";
    import docLogo from "../assets/images/doc-logo-example.svg";
    import trainingIcon from "../assets/images/training.svg";
    import { API } from '../Api';
    import { QRadio } from 'quasar';
    import { useLoader } from "../composables/use-loader";
    import { useNotification } from "../composables/use-notification";
    import type { AxiosError, AxiosResponse } from 'axios';
    import { isAxiosError } from 'axios';   
    import axios from "../api/index";
    import VariableInteractions from './VariableInteractions.vue'
    
    export default defineComponent({
    components: {
        EmptyState,
        VariableInteractions,
        BsTab,
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
            modelName: "",   
            errorMessage: "", 
            selectedModelString: "",
            models: [] as ModelPoint[],
            modelsString: [] as string[],
            interactions: [] as Interaction[],
            selectedDatasetString: "",
            selectedTargetVariable: "",
            selectedExposureVariable: "",
            selectedDistributionFunctionString: 'Gaussian' as string,
            selectedLinkFunctionString: 'Log' as string,
            datasetsString: [] as string[],
            chartData: [],  
            selectedElasticNetPenalty: 0 as number,
            selectedL1Ratio: 0 as number,
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            trainingIcon,
            docLogo,
            previousInteractions: [] as Array<{first: string, second: string}>, 
            distributionOptions: ['Binomial',
                'Gamma',
                'Gaussian',
                'Inverse Gaussian',
                'Poisson',
                'Negative Binomial', 
                'Tweedie',
            ],
            linkOptions: [
                'CLogLog',
                'Log',
                'Logit',
                'Cauchy',
                'Identity',
                'Power',
                'Inverse Power',
                'Inverse Squared'
            ],
            typeOptions: [
                'Categorical',
                'Numerical'
            ],
            preprocessingOptions: [
                'Dummy Encode',
                'Standard Rescaling',
            ],
            datasetColumns: [] as Column[], // Populate this based on your actual data
            loading: false,
        };
    },
    computed:{
        filteredColumns() {
                return this.datasetColumns.filter(column =>
                    column.role !== 'Target' &&
                    column.role !== 'Exposure')
            },
    },
    watch: {
        // previousInteractions: {
        //     handler(newVal) {
        //         console.log('interactions changed in parent:', newVal)
        //     },
        //     deep: true
        // },
        datasetColumns: {
            handler(newVal, oldVal) {
                console.log('datasetColumns changed:', newVal);
                this.updateDatasetColumnsPreprocessing();
            },
            deep: true
        },
        
        loading(newVal) {
            if (newVal) {
                useLoader("Loading...").show();
            } else {
                useLoader().hide();
            }
        },
        
        
    },
    methods: {
        updateInteractions(newInteractions: Array<string>) {
                // Convert the formatted strings back to interaction objects
                this.previousInteractions = newInteractions.map(interaction => {
                    const [first, second] = interaction.split(':');
                    return { first, second };
                });
            },
            async fetchExcludedColumns() {
            try {
            const excludedColumnsResponse = await API.getExcludedColumns();
            const { target_column, exposure_column } = excludedColumnsResponse.data;
            
            // Update selectedTargetVariable and selectedExposureVariable
            this.selectedTargetVariable = target_column;
            this.selectedExposureVariable = exposure_column;
            
            // Update the roles in datasetColumns
            this.datasetColumns.forEach(column => {
                if (column.name === target_column) {
                column.role = 'Target';
                } else if (column.name === exposure_column) {
                column.role = 'Exposure';
                } else {
                column.role = 'Variable';
                }
            });
            } catch (error) {
            console.error('Error fetching excluded columns:', error);
            }
        },
    
        async updateModelString(value: string) {
              this.loading = true;
              this.selectedModelString = value;
              const model = this.models.filter( (v: ModelPoint) => v.name==value)[0];
              this.loading = false;
            },
            notifyError(msg: string) {
                useNotification("negative", msg);
            },
            handleError(msg: any) {
                this.loading = false;
                console.error(msg);
                this.notifyError(msg);
            },
        validateSubmission() {
            this.errorMessage = ''; // Reset error message before validation
            if (!this.modelName) {
                this.errorMessage = 'Please enter a model name.';
                console.log('Error Message:', this.errorMessage);
        
                return false;
                }
            if (!this.selectedTargetVariable) {
                this.errorMessage = 'Please select a target variable.';
                return false;
            }

            const newName = this.modelName.trim().toLowerCase();
            const exists = this.modelsString.some(
                model => model.toLowerCase() === newName
            )
            
            if (exists) {
                this.errorMessage = 'This model name already exists';
                return false;
            }
            return true; // Validation passed
        },
        updateDatasetColumnsPreprocessing() {
            const updatedColumns = this.datasetColumns.map(column => {
                let preprocessing;
                if (column.type === "categorical") {
                    preprocessing = 'Dummy Encode';
                } else if (column.type === "numerical") {
                    preprocessing = 'Standard Rescaling';
                } else {
                    // Preserve the existing preprocessing if the type doesn't match
                    preprocessing = column.preprocessing;
                }
    
                // Only update preprocessing if it's different to avoid infinite loops
                if (JSON.stringify(column.preprocessing) !== JSON.stringify(preprocessing)) {
                    return { ...column, preprocessing };
                } else {
                    return column;
                }
            });
    
            // Check if the update is necessary to avoid unnecessary reactivity triggering
            if (JSON.stringify(this.datasetColumns) !== JSON.stringify(updatedColumns)) {
                this.datasetColumns = updatedColumns;
            }
        },
        abbreviateColumnName(name:string) {
            const maxLength = 12 ; // Maximum length of column name
            if (name.length > maxLength) {
            return `${name.substring(0, maxLength - 1)}...`; // 
            }
            return name; // Return the original name if it's short enough
        },
        closeSideDrawer() {
            if (this.layoutRef) {
                this.layoutRef.drawerOpen = !this.layoutRef.drawerOpen;
            }
        },
        updateModelProperty(property: UpdatableProperties, value: any): void{
            this[property] = value;
            localStorage.setItem(property, JSON.stringify(value));
            console.log(`updateModelProperty: Updating ${String(property)} to ${JSON.stringify(value)}`);
        },
        updatePreprocessing(index: number, newValue: any) {
            const column = this.datasetColumns[index];
            if (column) {
                column.preprocessing = newValue;
                // Since Vue 2 doesn't reactively update arrays on index, force update
                this.datasetColumns[index] = column;
            }
        },
        updateType(index:number, value: any) {
            const column = this.datasetColumns[index];
            if (column) {
                    column.type = value;
                }
                // Trigger a Vue reactivity update
                this.datasetColumns[index] = column;
            },
        async submitVariables() {
            this.loading = true;
            if (!this.validateSubmission()) {
                // If validation fails, stop execution
                this.loading = false;
                return;
            }
            // Define modelParameters outside of the reduce call to ensure it's accessible later
            const modelParameters = {
                model_name: this.modelName,
                distribution_function: this.selectedDistributionFunctionString,
                link_function: this.selectedLinkFunctionString,
                elastic_net_penalty: this.selectedElasticNetPenalty,
                l1_ratio: this.selectedL1Ratio
            };
    
            // Reduce function to construct Variables object    
            const variableParameters = this.datasetColumns.reduce<AccType>((acc, { name, role, type, preprocessing, isIncluded, baseLevel }) => {
            acc[name] = {
                role: role,
                type: type.toLowerCase(),
                processing: preprocessing == 'Dummy Encode' ? 'CUSTOM' : 'REGULAR',
                included: isIncluded,
                base_level: baseLevel
            };
            return acc;
            }, {});
            // Now modelParameters is available to be included in payload
            const payload = {
            model_parameters: modelParameters,
            variables: variableParameters,
            interaction_variables: this.previousInteractions.map(interaction => ({
                first: interaction.first,
                second: interaction.second
            }))
    };
            try {
                console.log("Payload:", payload);
                const modelUID = await API.trainModel(payload);
                // Handle successful submission here
            } catch (error) {
            if (isAxiosError(error)) {
                const axiosError = error as AxiosError<ErrorResponse>;
                
                if (axiosError.response) {
                    console.log('Error response:', axiosError.response);
                    console.log('Error response data:', axiosError.response.data);
                    console.log('Error response status:', axiosError.response.status);
                    console.log('Error response headers:', axiosError.response.headers);
    
                    if (axiosError.response.data && 'error' in axiosError.response.data) {
                        this.errorMessage = axiosError.response.data.error;
                    } else {
                        this.errorMessage = `Server error: ${axiosError.response.status}`;
                    }
                } else if (axiosError.request) {
                    console.log('Error request:', axiosError.request);
                    this.errorMessage = 'No response received from the server. Please try again later.';
                } else {
                    console.log('Error message:', axiosError.message);
                    this.errorMessage = 'An unexpected error occurred while training the model.';
                }
            } else {
                this.errorMessage = 'An unexpected error occurred.';
            }
    
            this.notifyError(this.errorMessage);
        } finally {
            this.updateModels = !this.updateModels;
            this.$emit("update-models", this.updateModels);
            this.loading = false;
        }
        },  
            async getDatasetColumns(model_value = null) {
                this.loading = true;
                console.log(model_value);
                if (model_value) {
                    console.log("model_id parameter provided:", model_value);
                    this.datasetColumns = []
                    try {
                            const response = await API.getDatasetColumns();
                            this.selectedModelString = model_value;
    
                            const model = this.models.filter((v: ModelPoint) => v.name == model_value)[0];
                            console.log("Filtered model:", model);
                            console.log("Making request with model Id :", model);
    
                            const paramsResponse = await API.getLatestMLTaskParams(model)  as APIResponse;
                            console.log("API.getLatestMLTaskParams response:", paramsResponse);
    
                            const params = paramsResponse.data.params;
                            console.log("Extracted params:", params);
    
                            const responseColumns = response.data.map((column: ColumnInput) => column.column);
                            console.log("responseColumns:", responseColumns);
    
                            const paramsColumns = Object.keys(params);
                            console.log("paramsColumns:", paramsColumns);
                            
                            this.previousInteractions = paramsResponse.data.interactions 
                                ? paramsResponse.data.interactions.map(interaction => ({
                                    first: interaction.first,
                                    second: interaction.second
                                }))
                                : [];
                            console.log("Interaction recieved in parent", this.previousInteractions)
                            this.selectedDistributionFunctionString = paramsResponse.data.distribution_function;
                            this.selectedLinkFunctionString = paramsResponse.data.link_function;
                            this.selectedElasticNetPenalty = paramsResponse.data.elastic_net_penalty ? paramsResponse.data.elastic_net_penalty : 0;
                            this.selectedL1Ratio = paramsResponse.data.l1_ratio ? paramsResponse.data.l1_ratio : 0;
                            
                            
                            console.log("paramsResponse:", paramsResponse.data);
                            this.datasetColumns = response.data.map((column: ColumnInput) => {
                                const columnName = column.column;
                                const options = column.options;
                                const param = params[columnName];
                                const isTargetColumn = columnName === paramsResponse.data.target_column;
                                const isExposureColumn = columnName === paramsResponse.data.exposure_column;
                                
                                // Set the selected target variable if this column is the target column
                                if (isTargetColumn) {
                                    this.selectedTargetVariable = columnName;
                                }
    
                                // Set the selected exposure variable if this column is the exposure column
                                if (isExposureColumn) {
                                    this.selectedExposureVariable = columnName;
                                }
    
                                // Check if the column names match, excluding the specific column
                            const missingColumns = paramsColumns
                                .filter((col: string) => col !== this.selectedExposureVariable)
                                .filter((col: string) => !responseColumns.includes(col));
                            console.log("missingColumns:", missingColumns);
    
                            const extraColumns = responseColumns
                                .filter((col: string) => col !== this.selectedExposureVariable)
                                .filter((col: string) => !paramsColumns.includes(col));
                            console.log("extraColumns:", extraColumns);
    
                            
                            if (missingColumns.length > 0 || extraColumns.length > 0) {
                                let errorMessage = "Column mismatch: Your training dataset does not contain the same variables as the model you requested.\n";
                                if (missingColumns.length > 0) {
                                    errorMessage += `Missing columns: ${missingColumns.join(", ")}\n`;
                                }
                                if (extraColumns.length > 0) {
                                    errorMessage += `Extra columns: ${extraColumns.join(", ")}`;
                                }
                                this.handleError(errorMessage);
                                return;
                            }
                                return {
                                    name: columnName,
                                    isIncluded: isTargetColumn || isExposureColumn || param.role !== 'REJECT',
                                    role: isTargetColumn ? 'Target' : (isExposureColumn ? 'Exposure' : (param.role || 'REJECT')),
                                    type: param.type ? (param.type === 'NUMERIC' ? 'numerical' : 'categorical') : 'categorical',
                                    preprocessing: param.handling ? (param.handling === 'DUMMIFY' ? 'Dummy Encode' : param.handling) : 'Dummy Encode',
                                    options: options,
                                    baseLevel: param.baseLevel ? param.baseLevel : column.baseLevel
                                };
                            });
    
                        } catch (error) {
                            console.error("Error fetching data:", error);
                        }finally {
                                this.loading = false;
                            }
                        
    
                } 
                else {
                    console.log("No model id provided:");
                    try {
                        const response = await API.getDatasetColumns();
    
                        this.datasetColumns = response.data.map((column: ColumnInput) => ({
                            name: column.column,
                            isIncluded: false,
                            role: 'Variable',
                            type: 'categorical',
                            preprocessing: 'Dummy Encode',
                            options: column.options,
                            baseLevel: column.baseLevel
                        }));
    
                    console.log("First assignment");
                    await this.fetchExcludedColumns();
                    } catch (error) {
                        console.error('Error fetching datasets:', error);
                        this.datasetColumns = [];
                    }
                }
                this.loading = false;
                },
            
        },
    
    async mounted() {
        API.getModels().then((data: any) => {
            this.models = data.data;
            this.modelsString = this.models.map(item => item.name);
            console.log("Models load are", this.models)
          });
        this.layoutRef = this.$refs.layout as InstanceType<typeof BsLayoutDefault>;
        const savedDistributionFunction = localStorage.getItem('DistributionFunction');
        const savedLinkFunction = localStorage.getItem('linkFunction');
        await this.getDatasetColumns();
    
        
    },
    emits: ['update:modelValue', 'update-models']
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
    </style>