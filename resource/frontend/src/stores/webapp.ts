import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import type { ModelPoint, ModelMetricsDataPoint, BaseValue, RelativityPoint, ModelInfo } from '../models';
import { useAnalysisStore } from "./analysisStore";
import { WT1iser } from '../utilities/utils';

export const useModelStore = defineStore("ModelStore", {
    state: () => ({
        models: [] as ModelPoint[],

        activeModel: null as ModelPoint | null,
        comparedModel: null as ModelPoint | null,
        relativitiesData: [] as RelativityPoint[],
        relativitiesData2: [] as RelativityPoint[],

        modelMetrics1: {} as ModelMetricsDataPoint,
        modelMetrics2: {} as ModelMetricsDataPoint,
        baseValues1: [] as BaseValue[],
        baseValues2: [] as BaseValue[],

        projectKey: "",
        mlTaskId: "",
        analysisId: "",
        trainTest: true,

        isLoading: false,
    }),
    
    getters: {
        modelOptions: (state) => {
            return state.models.map(item => item.name);
        },
        activeModelName: (state): string => {
            return state.activeModel?.name || "";
        },
        comparedModelName: (state): string => {
            return state.comparedModel?.name || "";
        },
    },

    actions: {

        getModelByName(name: string) : ModelPoint | undefined {
            return this.models.find((obj: ModelPoint) => obj.name === name);
        },

        async loadModels() {
            this.isLoading = true;
            try {
                const store = useAnalysisStore();
                const response = await API.getModels({mlTaskId: store.selectedMlTask.mlTaskId, analysisId: store.selectedMlTask.analysisId});
                this.models = response.data;
                if (this.models.length > 0) {
                    this.projectKey = this.models[0].project_key;
                    this.mlTaskId = this.models[0].ml_task_id;
                    this.analysisId = this.models[0].analysis_id;
                }
            } catch (error) {
                this.handleError(error);
            } finally {
                this.isLoading = false;
            }
        },
        
        async setActiveModel(modelName: string) {
            const model = this.models.find(m => m.name === modelName);
            if (!model) {
                this.activeModel = null;
                return;
            }
            this.activeModel = model;
            WT1iser.selectModel();
            this.isLoading = true;
            try {
                // Fetch only the data directly related to this model.
                const [baseResponse, metricsResponse] = await Promise.all([
                    API.getBaseValues(model),
                    API.getModelMetrics(model)
                ]);
                this.baseValues1 = baseResponse.data;
                this.modelMetrics1 = metricsResponse.data;
                const relativityResponse = await API.getRelativities(model);
                this.relativitiesData = relativityResponse?.data;
            } catch (err) {
                this.handleError(err);
            } finally {
                this.isLoading = false;
            }
        },

        async setComparedModel(modelName: string | null) {
            if (!modelName) {
                this.comparedModel = null;
                this.modelMetrics2 = {} as ModelMetricsDataPoint;
                this.baseValues2 = [];
                return;
            }
            
            const model = this.models.find(m => m.name === modelName);
            if (!model) return;
            
            this.comparedModel = model;
            this.isLoading = true;
            try {
                const [baseResponse, metricsResponse] = await Promise.all([
                    API.getBaseValues(model),
                    API.getModelMetrics(model)
                ]);
                this.baseValues2 = baseResponse.data;
                this.modelMetrics2 = metricsResponse.data;
                const relativityResponse = await API.getRelativities(model);
                this.relativitiesData2 = relativityResponse?.data;
            } catch (err) {
                this.handleError(err);
            } finally {
                this.isLoading = false;
            }
        },

        setTrainTest(isTest: boolean) {
            this.trainTest = isTest;
        },

        async exportModel(model: ModelPoint) {
            try {
                const response = await API.exportModel(model);
                this._triggerDownload(response.data, `${model.name}.csv`);
            } catch (error) {
                this.handleError(error);
            }
        },
        
        async exportActiveModel() {
            if (!this.activeModel) {
                this.notifyError("No active model selected to export.");
                return;
            }
            const response = await this.exportModel(this.activeModel);
        },

        async deployModel(model: ModelInfo) {
            try {
                const response = await API.deployModel(model);
                WT1iser.deployModel();
                if (response.status == 200) {
                    this.notifyInfo("Model deployed.");
                } else {
                    this.handleError("Error deploying model.");
                }
                return response;
                
            } catch (error) {
                this.handleError(error);
            }
        },

        async deployActiveModel() {
            if (!this.activeModel) {
                this.notifyError("No active model selected to deploy.");
                return;
            }
            const analysisStore = useAnalysisStore();
            const response = await this.deployModel({id: this.activeModel.id, input_dataset: analysisStore.selectedMlTask.trainSet, experiment_name: analysisStore.selectedMlTask.analysisName});
        },

        async deleteModel(model: ModelInfo) {
            this.isLoading = true;
            try {
                const response = await API.deleteModel(model);
                WT1iser.deleteModel();
            } catch (error) {
                this.handleError(error);
            }
            this.isLoading = false;
        },

        _triggerDownload(data: any, filename: string) {
            const url = window.URL.createObjectURL(new Blob([data], { type: 'text/csv' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        },

        handleError(error: any) {
            const message = error.message || "An unknown error occurred.";
            console.error("SessionStore Error:", error);
            this.notifyError(message);
        },

        notifyError(message: string) {
            useNotification("negative", message);
        },

        notifyInfo(message: string) {
            useNotification("positive", message);
        },
    },
});
