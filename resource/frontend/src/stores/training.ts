import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import type { 
    AccType,
  ErrorPoint,
  ModelPoint
} from '../models';
import type { ColumnInput, Interaction, Column, APIResponse, SplineFeature, CategoricalGroup } from "../models";
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
        selectedPreviousModel: null as string | null,
        selectedDatasetString: "",
        selectedTargetVariable: "",
        selectedExposureVariable: null as string | null,
        selectedSampleWeightVariable: null as string | null,
        selectedOffsetVariables: [] as string[],
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
            if (this.selectedDistributionFunctionString === newDistribution) {
                return;
            }
            this.selectedDistributionFunctionString = newDistribution;

            const isCurrentLinkAllowed = this.allowedLinks.includes(this.selectedLinkFunctionString);

            if (!isCurrentLinkAllowed) {
                this.selectedLinkFunctionString = this.allowedLinks[0];
            }
            if (this.selectedLinkFunctionString !== "Log" && this.selectedExposureVariable !== null) {
                this.selectedExposureVariable = null;
            }
            this.syncFixedColumnRoles();
        },

        setLinkFunction(newLink: string) {
            if (this.selectedLinkFunctionString === newLink) {
                return;
            }
            this.selectedLinkFunctionString = newLink;
            if (this.selectedLinkFunctionString !== "Log" && this.selectedExposureVariable !== null) {
                this.selectedExposureVariable = null;
            }
            this.syncFixedColumnRoles();
        },
        setExposureVariable(newExposure: string | null) {
            const normalizedExposure = newExposure || null;
            let hasChanges = false;
            if (this.selectedExposureVariable !== normalizedExposure) {
                this.selectedExposureVariable = normalizedExposure;
                hasChanges = true;
            }
            if (this.selectedExposureVariable && this.selectedSampleWeightVariable === this.selectedExposureVariable) {
                this.selectedSampleWeightVariable = null;
                hasChanges = true;
            }
            const filteredOffsets = this.selectedOffsetVariables.filter((value) => value !== this.selectedExposureVariable);
            if (filteredOffsets.length !== this.selectedOffsetVariables.length) {
                this.selectedOffsetVariables = filteredOffsets;
                hasChanges = true;
            }
            if (hasChanges) {
                this.syncFixedColumnRoles();
            }
        },
        setSampleWeightVariable(newSampleWeight: string | null) {
            const normalizedSampleWeight = newSampleWeight || null;
            let hasChanges = false;
            if (this.selectedSampleWeightVariable !== normalizedSampleWeight) {
                this.selectedSampleWeightVariable = normalizedSampleWeight;
                hasChanges = true;
            }
            if (this.selectedSampleWeightVariable && this.selectedExposureVariable === this.selectedSampleWeightVariable) {
                this.selectedExposureVariable = null;
                hasChanges = true;
            }
            const filteredOffsets = this.selectedOffsetVariables.filter((value) => value !== this.selectedSampleWeightVariable);
            if (filteredOffsets.length !== this.selectedOffsetVariables.length) {
                this.selectedOffsetVariables = filteredOffsets;
                hasChanges = true;
            }
            if (hasChanges) {
                this.syncFixedColumnRoles();
            }
        },
        setOffsetVariables(newOffsets: string[]) {
            const normalizedOffsets = Array.from(new Set((newOffsets || []).filter(Boolean))).filter(
                (value) => value !== this.selectedExposureVariable && value !== this.selectedSampleWeightVariable
            );
            const hasSameLength = normalizedOffsets.length === this.selectedOffsetVariables.length;
            const hasSameValues = hasSameLength && normalizedOffsets.every((value, index) => value === this.selectedOffsetVariables[index]);
            if (hasSameValues) {
                return;
            }
            this.selectedOffsetVariables = normalizedOffsets;
            this.syncFixedColumnRoles();
        },
        syncFixedColumnRoles() {
            this.datasetColumns.forEach((column) => {
                if (column.name === this.selectedTargetVariable) {
                    if (column.role !== "Target") {
                        column.role = "Target";
                    }
                    return;
                }
                if (this.selectedLinkFunctionString === "Log" && column.name === this.selectedExposureVariable) {
                    if (column.role !== "Exposure") {
                        column.role = "Exposure";
                    }
                    if (!column.isIncluded) {
                        column.isIncluded = true;
                    }
                    return;
                }
                if (column.name === this.selectedSampleWeightVariable) {
                    if (column.role !== "SampleWeight") {
                        column.role = "SampleWeight";
                    }
                    if (!column.isIncluded) {
                        column.isIncluded = true;
                    }
                    return;
                }
                if ((this.selectedOffsetVariables || []).includes(column.name)) {
                    if (column.role !== "Offset") {
                        column.role = "Offset";
                    }
                    if (!column.isIncluded) {
                        column.isIncluded = true;
                    }
                    return;
                }
                if (column.role === "Exposure" || column.role === "SampleWeight" || column.role === "Offset") {
                    column.role = "REJECT";
                    if (column.isIncluded) {
                        column.isIncluded = false;
                    }
                }
            });
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

            const availableColumns = new Set(this.datasetColumns.map((column) => column.name));
            const defaultTarget = analysisStore.selectedMlTask.targetColumn || "";
            const defaultExposure = analysisStore.selectedMlTask.exposureColumn || null;
            const defaultSampleWeight = analysisStore.selectedMlTask.sampleWeightColumn || null;
            const defaultOffsets = Array.isArray(analysisStore.selectedMlTask.offsetColumns)
                ? analysisStore.selectedMlTask.offsetColumns.filter((name) => availableColumns.has(name))
                : [];

            if (!this.selectedTargetVariable || !availableColumns.has(this.selectedTargetVariable)) {
                this.selectedTargetVariable = defaultTarget;
            }

            if (this.selectedLinkFunctionString === "Log") {
                if (this.selectedExposureVariable && !availableColumns.has(this.selectedExposureVariable)) {
                    this.selectedExposureVariable = null;
                }
                if (
                    this.selectedExposureVariable === null &&
                    defaultExposure &&
                    availableColumns.has(defaultExposure) &&
                    this.selectedSampleWeightVariable !== defaultExposure &&
                    !this.selectedOffsetVariables.includes(defaultExposure)
                ) {
                    this.selectedExposureVariable = defaultExposure;
                }
            } else {
                this.selectedExposureVariable = null;
            }

            if (this.selectedSampleWeightVariable && !availableColumns.has(this.selectedSampleWeightVariable)) {
                this.selectedSampleWeightVariable = null;
            }
            if (this.selectedSampleWeightVariable === null && defaultSampleWeight && availableColumns.has(defaultSampleWeight)) {
                this.selectedSampleWeightVariable = defaultSampleWeight;
            }

            const normalizedOffsets = (this.selectedOffsetVariables || []).filter((name) => availableColumns.has(name));
            this.selectedOffsetVariables = normalizedOffsets.length > 0 ? normalizedOffsets : defaultOffsets;
            this.syncFixedColumnRoles();
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
            return false;
        }
        if (!this.selectedTargetVariable) {
            this.errorMessage = 'Please select a target variable.';
            return false;
        }
        if (this.selectedLinkFunctionString === "Log" && !this.selectedExposureVariable) {
            this.errorMessage = 'Please select an exposure variable for Log link.';
            return false;
        }
        const usedFixedColumns = [
            this.selectedTargetVariable,
            this.selectedLinkFunctionString === "Log" ? this.selectedExposureVariable : null,
            this.selectedSampleWeightVariable,
            ...(this.selectedOffsetVariables || []),
        ].filter((value): value is string => Boolean(value));
        if (new Set(usedFixedColumns).size !== usedFixedColumns.length) {
            this.errorMessage = 'Target, exposure, sample weight, and offset columns must be distinct.';
            return false;
        }
        for (const column of this.datasetColumns) {
            if (!column.isIncluded || column.type !== "numerical") {
                if (!column.isIncluded || column.type !== "categorical") {
                    continue;
                }
                const categoricalGroups = column.categoricalGroups || [];
                if (categoricalGroups.length > 5) {
                    this.errorMessage = `At most 5 modality groups are allowed for ${column.name}.`;
                    return false;
                }
                const seen = new Set<string>();
                for (const group of categoricalGroups) {
                    if (!Array.isArray(group) || group.length < 2) {
                        this.errorMessage = `Each categorical group must contain at least 2 modalities for ${column.name}.`;
                        return false;
                    }
                    for (const modality of group) {
                        const key = String(modality);
                        if (seen.has(key)) {
                            this.errorMessage = `Each modality can belong to only one group for ${column.name}.`;
                            return false;
                        }
                        seen.add(key);
                    }
                }
                continue;
            }
            const splineFeatures = column.splineFeatures || [];
            if (splineFeatures.length > 0 && (column.baseLevel === null || column.baseLevel === undefined || column.baseLevel === "")) {
                this.errorMessage = `Base level is required for spline configuration on ${column.name}.`;
                return false;
            }
            if (splineFeatures.length > 3) {
                this.errorMessage = `At most 3 spline features are allowed for ${column.name}.`;
                return false;
            }
            for (const feature of splineFeatures) {
                if (!Array.isArray(feature) || feature.length === 0) {
                    this.errorMessage = `Each spline feature must contain at least one segment for ${column.name}.`;
                    return false;
                }
                for (const segment of feature) {
                    if (
                        !Number.isFinite(segment.min_value) ||
                        !Number.isFinite(segment.max_value) ||
                        !Number.isFinite(segment.degree) ||
                        segment.min_value >= segment.max_value
                    ) {
                        this.errorMessage = `Invalid spline segment on ${column.name}.`;
                        return false;
                    }
                }
            }
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
    async getDatasetColumns(model_value: string | null = null) {
        const analysisStore = useAnalysisStore();
        if (model_value) {
            this.selectedPreviousModel = model_value;
            this.isLoading = true;
            this.datasetColumns = []
            const store = useModelStore();
            try {
                    const model = store.models.filter((v: ModelPoint) => v.name == model_value)[0];

                    const paramsResponse = await API.getLatestMLTaskParams(model)  as APIResponse;

                    const params = paramsResponse.data.params;
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
                    this.selectedTargetVariable = paramsResponse.data.target_column || analysisStore.selectedMlTask.targetColumn || "";
                    this.selectedExposureVariable = paramsResponse.data.exposure_column || null;
                    this.selectedSampleWeightVariable = paramsResponse.data.sample_weight_column || null;
                    this.selectedOffsetVariables = paramsResponse.data.offset_columns || [];

                    const effectiveExposure = this.selectedLinkFunctionString === "Log"
                        ? (this.selectedExposureVariable || null)
                        : null;
                    const response = await API.getDatasetColumns({
                        dataset: analysisStore.selectedMlTask.trainSet,
                        exposure: effectiveExposure,
                        weightingColumn: this.selectedSampleWeightVariable || effectiveExposure || null,
                    });
                    const responseColumns = response.data.map((column: ColumnInput) => column.column);
                    
                    this.datasetColumns = response.data.map((column: ColumnInput) => {
                        const columnName = column.column;
                        const options = column.options;
                        const param = params[columnName] || {} as any;
                        const isTargetColumn = columnName === paramsResponse.data.target_column;
                        const isExposureColumn = this.selectedLinkFunctionString === "Log"
                            && columnName === (paramsResponse.data.exposure_column || "");
                        const isSampleWeightColumn = columnName === (paramsResponse.data.sample_weight_column || "");
                        const isOffsetColumn = (paramsResponse.data.offset_columns || []).includes(columnName);

                        // Check if the column names match, excluding the specific column
                    const fixedColumns = new Set([
                        this.selectedLinkFunctionString === "Log" ? (this.selectedExposureVariable || "") : "",
                        this.selectedSampleWeightVariable || "",
                        ...this.selectedOffsetVariables,
                    ]);
                    const missingColumns = paramsColumns
                        .filter((col: string) => !fixedColumns.has(col))
                        .filter((col: string) => !responseColumns.includes(col));

                    const extraColumns = responseColumns
                        .filter((col: string) => !fixedColumns.has(col))
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
                            isIncluded: isTargetColumn || isExposureColumn || isSampleWeightColumn || isOffsetColumn || param.role !== 'REJECT',
                            role: isTargetColumn
                                ? 'Target'
                                : (isExposureColumn
                                    ? 'Exposure'
                                    : (isSampleWeightColumn
                                        ? 'SampleWeight'
                                        : (isOffsetColumn ? 'Offset' : (param.role || 'REJECT')))),
                            type: param.type ? (param.type === 'NUMERIC' ? 'numerical' : 'categorical') : column.type,
                            preprocessing: param.handling ? (param.handling === 'DUMMIFY' ? 'Dummy Encode' : param.handling) : 'Dummy Encode',
                            options: options,
                            baseLevel: param.baseLevel ? param.baseLevel : column.baseLevel,
                            minValue: column.minValue,
                            maxValue: column.maxValue,
                            splineFeatures: (param.splineFeatures || []) as SplineFeature[],
                            categoricalGroups: (param.categoricalGroups || []) as CategoricalGroup[]
                        };
                    });
                    this.syncFixedColumnRoles();
                    this.updateDatasetColumnsPreprocessing();

                } catch (error) {
                    console.error("Error fetching data:", error);
                } finally {
                    this.isLoading = false;
                }
                WT1iser.loadPreviousModel();

        } 
        else {
            this.selectedPreviousModel = null;
            try {
                this.isLoading = true;
                const defaultExposure = analysisStore.selectedMlTask.exposureColumn || null;
                const defaultSampleWeight = analysisStore.selectedMlTask.sampleWeightColumn || null;
                const effectiveExposure = this.selectedLinkFunctionString === "Log"
                    ? (this.selectedExposureVariable || defaultExposure || null)
                    : null;
                const response = await API.getDatasetColumns({
                    dataset: analysisStore.selectedMlTask.trainSet,
                    exposure: effectiveExposure,
                    weightingColumn: this.selectedSampleWeightVariable || defaultSampleWeight || effectiveExposure || null,
                });
                this.datasetColumns = response.data.map((column: ColumnInput) => ({
                    name: column.column,
                    isIncluded: false,
                    role: 'REJECT',
                    type: column.type,
                    preprocessing: 'Dummy Encode',
                    options: column.options,
                    baseLevel: column.baseLevel,
                    minValue: column.minValue ?? null,
                    maxValue: column.maxValue ?? null,
                    splineFeatures: [],
                    categoricalGroups: []
                }));
                await this.fetchExcludedColumns();
                this.syncFixedColumnRoles();
                this.updateDatasetColumnsPreprocessing();
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
        const variableParameters = this.datasetColumns.reduce<AccType>((acc, { name, role, type, preprocessing, isIncluded, baseLevel, splineFeatures, categoricalGroups }) => {
        acc[name] = {
            role: role,
            type: type.toLowerCase(),
            processing: type.toLowerCase() === 'numerical' || preprocessing == 'Dummy Encode' ? 'CUSTOM' : 'REGULAR',
            included: isIncluded,
            base_level: baseLevel,
            spline_features: (type.toLowerCase() === 'numerical' && splineFeatures.length > 0) ? splineFeatures : undefined,
            categorical_groups: (type.toLowerCase() === 'categorical' && categoricalGroups.length > 0) ? categoricalGroups : undefined
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
            targetColumn: this.selectedTargetVariable || analysisStore.selectedMlTask.targetColumn,
            exposureColumn: this.selectedLinkFunctionString === "Log" ? this.selectedExposureVariable : null,
            sampleWeightColumn: this.selectedSampleWeightVariable || null,
            offsetColumns: this.selectedOffsetVariables || []
        };
        
        try {
            const modelUID = await API.trainModel(payload);
            WT1iser.trainModel({
                distribution: this.selectedDistributionFunctionString,
                link: this.selectedLinkFunctionString,
                elasticNetPenalty: this.selectedElasticNetPenalty,
                l1Ratio: this.selectedL1Ratio
            });
            this.updateModels = !this.updateModels;
            // Handle successful submission here
        } catch (error) {
        if (isAxiosError(error)) {
            const axiosError = error as AxiosError<ErrorPoint>;
            
            if (axiosError.response) {
                if (axiosError.response.data && 'error' in axiosError.response.data) {
                    this.errorMessage = axiosError.response.data.error;
                } else {
                    this.errorMessage = `Server error: ${axiosError.response.status}`;
                }
            } else if (axiosError.request) {
                this.errorMessage = 'No response received from the server. Please try again later.';
            } else {
                this.errorMessage = 'An unexpected error occurred while training the model.';
            }
        } else {
            this.errorMessage = 'An unexpected error occurred.';
        }

        this.notifyError(this.errorMessage);
    } finally {
        this.isLoading = false;
    }
    }
},
});
