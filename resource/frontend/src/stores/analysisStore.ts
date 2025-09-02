import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import type { MlTask } from '../models';
import { useModelStore } from "./webapp";
import { useTrainingStore } from "./training";
import { use } from "echarts";
import { useOneWayChartStore } from "./oneWayChartStore";
import { useLiftChartStore } from "./liftChartStore";
import { useVariableLevelStatsStore } from "./variableLevelStatsStore";

export const useAnalysisStore = defineStore("AnalysisStore", {
    state: () => ({
        projectKey: "" as string,
        mlTasks: [] as MlTask[],
        selectedMlTask: {} as MlTask,
        errorMessage: "",
        isLoading: false as boolean,
        datasets: [] as string[],
        splitPolicies: ["Random", "Explicit"] as string[],
        variables: [] as string[],
    }),
    getters: {
        mlTaskOptions: (state) => {
            return state.mlTasks;
        },
    },
    actions: {
        resetState() {
            this.$reset();
        },

        async getProject() {
            try {
                const response = await API.getProject();
                const data = response.data;
                this.projectKey = data.projectKey;
            } catch (error) {
                console.error("Failed to fetch project key:", error);
            } finally {
                this.isLoading = false;
            }
        },

        async fetchInitialData() {
            this.isLoading = true;
            try {
                const [mlTasks, datasets] = await Promise.all([
                    API.getMlTasks(),
                    API.getDatasets(),
                ]);
                this.mlTasks = mlTasks.data
                console.log(this.mlTasks);
                this.datasets = datasets.data.map(item => item.name);
            } catch (error) {
                console.error("Failed to fetch initial data:", error);
            } finally {
                this.isLoading = false;
            }
        },

        async fetchVariablesForDataset(datasetName: string) {
            if (!datasetName) {
                this.variables = [];
                return;
            }
            this.isLoading = true;
            try {
                const response = await API.getVariablesForDataset({name: datasetName});
                this.variables = response.data.map(item => item.name);
            } catch (error) {
                console.error("Failed to fetch variables:", error);
            } finally {
                this.isLoading = false;
            }
        },

        async createNewMlTask(formData: { analysisName: string, trainSet: string, splitPolicy: string, testSet: string, targetColumn: string, exposureColumn: string }) {
            this.isLoading = true;
            try {
                const response = await API.createMlTask(formData);
                const mlTask = response.data;
                this.mlTasks.push(mlTask);
                this.selectedMlTask = mlTask;
            } catch (error) {
                console.error("Failed to create analysis:", error);
                throw error;
            } finally {
                this.isLoading = false;
            }
        },

        resetAllStores() {
            const modelStore = useModelStore()
            const trainingStore = useTrainingStore();
            const oneWayChartStore = useOneWayChartStore();
            const liftChartStore = useLiftChartStore();
            const variableLevelStatsStore = useVariableLevelStatsStore();
            modelStore.$reset();
            trainingStore.$reset();
            oneWayChartStore.$reset();
            liftChartStore.$reset();
            variableLevelStatsStore.$reset();
        },

        selectMlTask(mlTask: MlTask) {
            this.resetAllStores();
            this.selectedMlTask = mlTask;
            if (this.selectedMlTask.mlTaskId) {
                const store = useModelStore();
                store.loadModels();
                const trainingStore = useTrainingStore();
                trainingStore.getDatasetColumns();
            }
        }
    },
});