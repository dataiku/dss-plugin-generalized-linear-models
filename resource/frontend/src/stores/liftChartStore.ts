import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import { useModelStore } from "./webapp";
import type { LiftDataPoint, ModelPoint } from '../models';

export const useLiftChartStore = defineStore("liftChart", {
    state: () => ({
        liftChartData: [] as LiftDataPoint[],
        nbBins: 8,
        isLoading: false,
    }),

    actions: {
        handleError(error: any) {
            const errorMessage = error.message || "An unknown error occurred in the Lift Chart feature.";
            console.error("LiftChartStore Error:", error);
            useNotification("negative", errorMessage);
        },

        async fetchLiftData(modelId: string) {
            if (!modelId) {
                this.liftChartData = [];
                return;
            }

            this.isLoading = true;
            try {
                const store = useModelStore();
                const model = store.models.filter( (v: ModelPoint) => v.id==modelId)[0];
                store.activeModel = model;
                const modelNbBins = { nbBins: this.nbBins, id: model.id, name: model.name, trainTest: store.trainTest};
                const response = await API.getLiftData(modelNbBins);
                this.liftChartData = response.data;
            } catch (err) {
                this.handleError(err);
                this.liftChartData = [];
            } finally {
                this.isLoading = false;
            }
        },

        async updateNbBins(newBinValue: number) {
            this.nbBins = newBinValue;
            
            const store = useModelStore();
            if (store.activeModel?.id) {
                // Re-fetch data with the new bin value.
                await this.fetchLiftData(store.activeModel.id);
            }
        },

        async updateTrainTest(trainTest: boolean) {
            const store = useModelStore();
            store.setTrainTest(trainTest);
            if (store.activeModel?.id) {
                await this.fetchLiftData(store.activeModel.id);
            }
        }
    }
});
