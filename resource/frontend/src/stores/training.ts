import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import type { 
    AccType,
  ErrorPoint,
  ModelPoint
} from '../models';
import type { ColumnInput, Interaction, Column, APIResponse } from "../models";
import { AxiosError, isAxiosError } from "axios";
import { useModelStore } from "./webapp";
import { useAnalysisStore } from "./analysisStore";
import { WT1iser } from '../utilities/utils';

type UpdatableProperties = 'selectedDatasetString' | 'selectedDistributionFunctionString' | 'selectedLinkFunctionString';

export const useTrainingStore = defineStore("TrainingStore", {
    state: () => ({
        modelName: "",   
        errorMessage: "", 
        interactions: [] as Interaction[],
        selectedDatasetString: "",
        selectedTargetVariable: "",
        selectedExposureVariable: "",
        selectedDistributionFunctionString: 'Poisson' as string,
        selectedLinkFunctionString: 'Log' as string,
        selectedTheta: 1.0 as number,
        selectedPower: 1.0 as number,
        selectedVariancePower: 1.5 as number,
        datasetsString: [] as string[],
        chartData: [],  
        selectedElasticNetPenalty: 0 as number,
        selectedL1Ratio: 0 as number,
        previousInteractions: [] as Array<{first: string, second: string}>, 
        distributionOptions: [
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
        datasetColumns: [] as Column[],
        isLoading: false as boolean,
        updateModels: false as boolean,
    }),
    getters: {
        isTrainingAvailable(state) {
            // Check for model name and variable included
            const store = useModelStore();

            const trimmedName = state.modelName.trim();
            
            if (trimmedName === '') {
                return { valid: false, reason: 'Model name cannot be empty.' };
            }
            
            if (store.models.length>0) { 
                if (store.modelOptions.includes(trimmedName)) {
                    return { valid: false, reason: 'This model name already exists.' };
                }
            }

            const variableIncluded = this.datasetColumns.some(colum => colum.isIncluded === true);

            if (variableIncluded) {
                return { valid: true, reason: '' };
            } else {
                return { valid: false, reason: 'At least one variable should be included. ' };
            }
        },
        allowedLinks(state) {
            switch (state.selectedDistributionFunctionString) {
                case "Gamma":
                    return ["Log", "Identity", "Inverse Power"];
                case "Gaussian":
                    return ["Log", "Identity", "Inverse Power"];
                case "Inverse Gaussian":
                    return ["Log", "Identity", "Inverse Squared", "Inverse Power"];
                case "Poisson":
                    return ["Log", "Identity"];
                case "Negative Binomial":
                    return ["Log", "CLogLog", "Identity", "Power"];
                case "Tweedie":
                    return ["Log", "Power"];
            }
            return [];
        }
    },
    actions: {

        setElasticNetPenalty(newValue: number) {
            if (isNaN(newValue)) {
                this.selectedElasticNetPenalty = 0;
                return;
            }

            if (newValue >= 0) {
                this.selectedElasticNetPenalty = newValue;
            } else {
                this.selectedElasticNetPenalty = 0;
            }
        },

        setTheta(newValue: number) {
            if (isNaN(newValue)) {
                this.selectedTheta = 1.0;
                return;
            }

            if (newValue > 0) {
                this.selectedTheta = newValue;
            } else {
                this.selectedTheta = 1.0;
            }
        },

        setDistribution(newDistribution: string) {
            this.selectedDistributionFunctionString = newDistribution;

            const isCurrentLinkAllowed = this.allowedLinks.includes(this.selectedLinkFunctionString);

            if (!isCurrentLinkAllowed) {
                this.selectedLinkFunctionString = this.allowedLinks[0];
            }
        },

        setLinkFunction(newLink: string) {
            this.selectedLinkFunctionString = newLink;
        },

        updateInteractions(newInteractions: Array<string>) {
            // Convert the formatted strings back to interaction objects
            this.previousInteractions = newInteractions.map(interaction => {
                const [first, second] = interaction.split(':');
                return { first, second };
            });
        },
        async fetchExcludedColumns() {
            const analysisStore = useAnalysisStore();
            
            this.selectedTargetVariable = analysisStore.selectedMlTask.targetColumn;
            this.selectedExposureVariable = analysisStore.selectedMlTask.exposureColumn;
            
            this.datasetColumns.forEach(column => {
                if (column.name === this.selectedTargetVariable) {
                column.role = 'Target';
                } else if (column.name === this.selectedExposureVariable) {
                column.role = 'Exposure';
                } else {
                column.role = 'REJECT';
                }
            });
        },
    
    notifyError(msg: string) {
        useNotification("negative", msg);
    },
    handleError(msg: any) {
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

    updatePreprocessing(index: number, newValue: any) {
        const column = this.datasetColumns[index];
        if (column) {
            column.preprocessing = newValue;
            this.datasetColumns[index] = column;
        }
    },
    updateType(index:number, value: any) {
        const column = this.datasetColumns[index];
        if (column) {
            column.type = value;
        }
        this.datasetColumns[index] = column;
    },  
    async getDatasetColumns(model_value = null) {
        const analysisStore = useAnalysisStore();
        if (model_value) {
            this.isLoading = true;
            this.datasetColumns = []
            const store = useModelStore();
            try {
                    const response = await API.getDatasetColumns({dataset: analysisStore.selectedMlTask.trainSet, exposure: analysisStore.selectedMlTask.exposureColumn});

                    const model = store.models.filter((v: ModelPoint) => v.name == model_value)[0];

                    const paramsResponse = await API.getLatestMLTaskParams(model)  as APIResponse;

                    const params = paramsResponse.data.params;

                    const responseColumns = response.data.map((column: ColumnInput) => column.column);

                    const paramsColumns = Object.keys(params);
                    
                    this.previousInteractions = paramsResponse.data.interactions 
                        ? paramsResponse.data.interactions.map(interaction => ({
                            first: interaction.first,
                            second: interaction.second
                        }))
                        : [];
                    this.selectedDistributionFunctionString = paramsResponse.data.distribution_function;
                    this.selectedLinkFunctionString = paramsResponse.data.link_function;
                    this.selectedElasticNetPenalty = paramsResponse.data.elastic_net_penalty ? paramsResponse.data.elastic_net_penalty : 0;
                    this.selectedL1Ratio = paramsResponse.data.l1_ratio ? paramsResponse.data.l1_ratio : 0;
                    this.selectedTheta = paramsResponse.data.theta ? paramsResponse.data.theta : 0;
                    this.selectedPower = paramsResponse.data.power ? paramsResponse.data.power : 0;
                    this.selectedVariancePower = paramsResponse.data.var_power ? paramsResponse.data.var_power : 0;
                    
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

                    const extraColumns = responseColumns
                        .filter((col: string) => col !== this.selectedExposureVariable)
                        .filter((col: string) => !paramsColumns.includes(col));
                    
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
                            type: param.type ? (param.type === 'NUMERIC' ? 'numerical' : 'categorical') : column.type,
                            preprocessing: param.handling ? (param.handling === 'DUMMIFY' ? 'Dummy Encode' : param.handling) : 'Dummy Encode',
                            options: options,
                            baseLevel: param.baseLevel ? param.baseLevel : column.baseLevel
                        };
                    });

                } catch (error) {
                    console.error("Error fetching data:", error);
                } finally {
                    this.isLoading = false;
                }
                WT1iser.loadPreviousModel();

        } 
        else {
            try {
                this.isLoading = true;
                const response = await API.getDatasetColumns({dataset: analysisStore.selectedMlTask.trainSet, exposure: analysisStore.selectedMlTask.exposureColumn});
                this.datasetColumns = response.data.map((column: ColumnInput) => ({
                    name: column.column,
                    isIncluded: false,
                    role: 'REJECT',
                    type: column.type,
                    preprocessing: 'Dummy Encode',
                    options: column.options,
                    baseLevel: column.baseLevel
                }));
                await this.fetchExcludedColumns();
            } catch (error) {
                console.error('Error fetching datasets:', error);
                this.datasetColumns = [];
            } finally {
                this.isLoading = false;
            }
        }
    },
    async trainModel() {
        this.isLoading = true;
        if (!this.validateSubmission()) {
            this.isLoading = false;
            return;
        }
        const analysisStore = useAnalysisStore();
        const modelParameters = {
            model_name: this.modelName,
            distribution_function: this.selectedDistributionFunctionString,
            link_function: this.selectedLinkFunctionString,
            elastic_net_penalty: this.selectedElasticNetPenalty,
            l1_ratio: this.selectedL1Ratio,
            theta: this.selectedTheta,
            power: this.selectedPower,
            variance_power: this.selectedVariancePower
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
            })),
            ml_task_id: analysisStore.selectedMlTask.mlTaskId,
            analysis_id: analysisStore.selectedMlTask.analysisId,
            targetColumn: analysisStore.selectedMlTask.targetColumn,
            exposureColumn: analysisStore.selectedMlTask.exposureColumn
        };
        
        try {
            const modelUID = await API.trainModel(payload);
            WT1iser.trainModel({
                distribution: this.selectedDistributionFunctionString,
                link: this.selectedLinkFunctionString,
                elasticNetPenalty: this.selectedElasticNetPenalty,
                l1Ratio: this.selectedL1Ratio
            });
            // Handle successful submission here
        } catch (error) {
        if (isAxiosError(error)) {
            const axiosError = error as AxiosError<ErrorPoint>;
            
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
        this.isLoading = false;
    }
    }
},
});