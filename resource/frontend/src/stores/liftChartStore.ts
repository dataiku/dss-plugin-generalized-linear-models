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

        applyForm() {
            this.chartOptions.model = this.formOptions.model;
            this.chartOptions.nbBins = this.formOptions.nbBins;
            this.chartOptions.trainTest = this.formOptions.trainTest;
        },

        // async updateNbBins(newBinValue: number) {
        //     this.nbBins = newBinValue;
            
        //     const store = useModelStore();
        //     if (store.activeModel?.id) {
        //         await this.fetchLiftData(store.activeModel.id);
        //     }
        // },

        // async updateTrainTest(trainTest: boolean) {
        //     const store = useModelStore();
        //     store.setTrainTest(trainTest);
        //     if (store.activeModel?.id) {
        //         await this.fetchLiftData(store.activeModel.id);
        //     }
        // }
    }
});
