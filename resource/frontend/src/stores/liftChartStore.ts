import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import { useModelStore } from "./webapp";
import type { LiftDataPoint, ModelPoint } from '../models';

export const useLiftChartStore = defineStore("liftChart", {
    state: () => ({
        liftChartData: [] as LiftDataPoint[],
        isLoading: false,

        formOptions: {
            model: "",
            nbBins: 8,
            trainTest: true
        },
        
        chartOptions: {
            model: "",
            nbBins: 8,
            trainTest: true
        }
    }),

    actions: {
        // resetState() {
        //     this.$reset();
        // },

        handleError(error: any) {
            const errorMessage = error.message || "An unknown error occurred in the Lift Chart feature.";
            console.error("LiftChartStore Error:", error);
            useNotification("negative", errorMessage);
        },

        setModel(model: string) {
            this.formOptions.model = model;
        },
        
        setNbBins(nbBins: number) {
            this.formOptions.nbBins = nbBins;
        },

        setTrainTest(trainTest: boolean) {
            this.formOptions.trainTest = trainTest;
        },

        async fetchLiftData() {
            const modelName = this.chartOptions.model;
            if (!modelName) {
                this.liftChartData = [];
                return;
            }

            this.isLoading = true;
            try {
                const store = useModelStore();
                const model = store.models.filter( (v: ModelPoint) => v.name==modelName)[0];
                store.activeModel = model;
                const modelNbBins = { nbBins: this.chartOptions.nbBins, id: model.id, name: model.name, trainTest: this.chartOptions.trainTest};
                const response = await API.getLiftData(modelNbBins);
                this.liftChartData = response.data;
            } catch (err) {
                this.handleError(err);
                this.liftChartData = [];
            } finally {
                this.isLoading = false;
            }
        },

        async applyForm() {
            this.chartOptions.model = this.formOptions.model;
            this.chartOptions.nbBins = this.formOptions.nbBins;
            this.chartOptions.trainTest = this.formOptions.trainTest;
        },

        async exportLiftChart() {
            const store = useModelStore();
            if (!store.activeModel) {
                this.notifyError("No variable selected to export.");
                return;
            }
            try {
                const model = store.activeModel;
                const modelNbBins = { nbBins: this.chartOptions.nbBins, id: model.id, name: model.name, trainTest: this.chartOptions.trainTest};
                const response = await API.exportLiftChart(modelNbBins);
                this._triggerDownload(response.data, `lift_chart_${store.activeModel.name}.csv`);
            } catch (error) {
                this.handleError(error);
            }
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

        notifyError(message: string) {
            useNotification("negative", message);
        },
    }
});
