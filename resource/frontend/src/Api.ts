import axios from "./api/index";
import type { AxiosError } from 'axios';

interface ErrorResponse {
    error: string;
}

interface DataPoint {
    definingVariable: string;
    Category: string;
    Value: number;
    observedAverage: number;
    fittedAverage: number;
    baseLevelPrediction: number;
}

interface LiftDataPoint {
    Category: string;
    Value: number;
    observedAverage: number;
    fittedAverage: number;
}

interface ModelMetricsDataPoint {
    AIC: number;
    BIC: number;
    Deviance: number;
}

interface ModelComparisonDataPoint {
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

interface RelativityPoint {
    variable: string;
    category: string;
    relativity: number;
}

interface BaseValue {
    variable: string;
    base_level: string;
}

interface ModelPoint {
    id: string;
    name: string;
    date: string;
    project_key: string;
    ml_task_id: string;
    analysis_id: string;
}

interface ModelInfo {
    id: string;
    experiment_name: string;
    input_dataset: string;
}

interface ModelVariablePoint {
    id: string;
    name: string;
    variable: string;
    trainTest: boolean;
    chartRescaling: string;
}

interface ModelNbBins {
    id: string;
    name: string;
    nbBins: number;
    trainTest: boolean;
}

interface ModelTrainPoint { 
    id: string;
    name: string;
    trainTest: boolean;
}

interface FeatureNbBin {
    feature: string;
    nbBin: number;
}

interface VariablePoint {
    variable: string;
    isInModel: boolean;
    variableType: string;
}


interface VariableName {
    name: string;
}

interface DatasetName {
    name: string;
}

interface VariableLevelStatsPoint {
    variable: string;
    value: string;
    coefficient: number;
    p_value: number;
    standard_error: number;
    standard_error_pct: number;
    weight: number;
    weight_pct: number;
    relativity: number;
}

interface ErrorPoint {
    error: string;
}
interface ExcludedColumns {
    target_column: string;
    exposure_column: string;
}
interface MLTaskParams {
    target_column: string;
    exposure_column: string;
    distribution_function: string;
    link_function: string;
    elastic_net_penalty: number;
    l1_ratio: number;
    theta: number;
    power: number;
    var_power: number;
    params: {
        [key: string]: {
            role: string;
            type: string;
            handling: string | null;
            chooseBaseLevel: boolean;
            baseLevel: string;
        }
    };
    interactions: Array<{
        first: string;
        second: string;
    }>;
}

interface Project {
    projectKey: string;
}

interface MlTask {
    analysisName: string;
    analysisId: string;
    mlTaskId: string;
    trainSet: string;
    splitPolicy: string;
    testSet: string;
    targetColumn: string;
    exposureColumn: string;
    isValid: boolean;
}

interface MlTaskConfiguration {
    analysisName: string;
    trainSet: string;
    splitPolicy: string;
    testSet: string;
    targetColumn: string;
    exposureColumn: string;
}

interface MlTaskIds {
    mlTaskId: string;
    analysisId: string;
}

interface DatasetExposure {
    dataset: string;
    exposure: string;
}

export let API = {
    getLatestMLTaskParams: (data:any) => axios.post<MLTaskParams>("/api/get_latest_mltask_params", data),
    getPredictedBase: (data: ModelVariablePoint) => axios.post<DataPoint[]>("/api/predicted_base", data),
    getBaseValues: (data: ModelPoint) => axios.post<BaseValue[]>("/api/base_values", data),
    getLiftData: (data: ModelNbBins) => axios.post<LiftDataPoint[]>("/api/lift_data", data),
    updateData: (data: FeatureNbBin) => axios.post<DataPoint[]>("/api/update_bins", data),
    getRelativities: (data: ModelPoint) => axios.post<RelativityPoint[]>("/api/relativities", data),
    getModels: (data: MlTaskIds) => axios.post<ModelPoint[]>("/api/models", data),
    getVariables: (data: ModelPoint) => axios.post<VariablePoint[]>("/api/variables", data),
    getDatasetColumns: (data: DatasetExposure) => axios.post("/api/get_dataset_columns", data),
    trainModel: (payload: any) => 
        axios.post<string[]>("/api/train_model", payload)
        .catch((error: AxiosError<ErrorResponse>) => {
            throw error;
        }),
    deployModel: (model: ModelInfo) => axios.post<number>("/api/deploy_model", model),
    deleteModel: (model: ModelInfo) => axios.post<number>("/api/delete_model", model),
    getModelMetrics: (data: any) => axios.post<ModelMetricsDataPoint>("/api/get_model_metrics", data),
    exportModel: (model: ModelPoint) => axios.post<Blob>("/api/export_model", model),
    exportVariableLevelStats: (model: ModelPoint) => axios.post<Blob>("/api/export_variable_level_stats", model),
    exportLiftChart: (model: ModelNbBins) => axios.post<Blob>("/api/export_lift_chart", model),
    exportOneWay: (model: ModelVariablePoint) => axios.post<Blob>("/api/export_one_way", model),
    getVariableLevelStats: (data: ModelPoint) => axios.post<VariableLevelStatsPoint[]>("/api/get_variable_level_stats", data),
    getProject: () => axios.get<Project>("api/get_project"),
    getMlTasks: () => axios.get<MlTask[]>("/api/get_ml_tasks"),
    getDatasets: () => axios.get<DatasetName[]>("/api/get_datasets"),
    getVariablesForDataset: (dataset: DatasetName) => axios.post<VariableName[]>("/api/get_variables_for_dataset", dataset),
    createMlTask: (mlTaskConfiguration: MlTaskConfiguration) => axios.post<MlTask>("/api/create_ml_task", mlTaskConfiguration)
}

