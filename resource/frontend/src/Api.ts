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
    params: {
        [key: string]: {
            role: string;
            type: string;
            handling: string | null;
            chooseBaseLevel: boolean;
            baseLevel: string;
        }
    };
}


export let API = {
    sendWebappId: (data: any) => axios.post<number>("/api/send_webapp_id", data),
    getLatestMLTaskParams: (data:any) => axios.post<MLTaskParams>("/api/get_latest_mltask_params", data),
    getExcludedColumns: () => axios.get<ExcludedColumns>("/api/get_excluded_columns"),
    getPredictedBase: (data: ModelVariablePoint) => axios.post<DataPoint[]>("/api/predicted_base", data),
    getBaseValues: (data: ModelPoint) => axios.post<BaseValue[]>("/api/base_values", data),
    getLiftData: (data: ModelNbBins) => axios.post<LiftDataPoint[]>("/api/lift_data", data),
    updateData: (data: FeatureNbBin) => axios.post<DataPoint[]>("/api/update_bins", data),
    getRelativities: (data: ModelPoint) => axios.post<RelativityPoint[]>("/api/relativities", data),
    getModels: () => axios.get<ModelPoint[]>("/api/models"),
    getVariables: (data: ModelPoint) => axios.post<VariablePoint[]>("/api/variables", data),
    getDatasetColumns: () => axios.get("/api/get_dataset_columns", {}),
    trainModel: (payload: any) => 
        axios.post<string[]>("/api/train_model", payload)
        .catch((error: AxiosError<ErrorResponse>) => {
            throw error;
        }),
    deployModel: (model: ModelPoint) => axios.post<number>("/api/deploy_model", model),
    deleteModel: (model: ModelPoint) => axios.post<number>("/api/delete_model", model),
    getModelMetrics: (data: any) => axios.post<ModelMetricsDataPoint>("/api/get_model_metrics", data),
    exportModel: (model: ModelPoint) => axios.post<Blob>("/api/export_model", model),
    exportVariableLevelStats: (model: ModelPoint) => axios.post<Blob>("/api/export_variable_level_stats", model),
    exportLiftChart: (model: ModelNbBins) => axios.post<Blob>("/api/export_lift_chart", model),
    exportOneWay: (model: ModelVariablePoint) => axios.post<Blob>("/api/export_one_way", model),
    getVariableLevelStats: (data: ModelPoint) => axios.post<VariableLevelStatsPoint[]>("/api/get_variable_level_stats", data),
}

