import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import { useModelStore } from "./webapp";
import type { DataPoint, VariablePoint, ModelPoint } from '../models';
import { QTableColumn } from "quasar";

const RELATIVITIES_COLUMNS: QTableColumn[] = [
    { name: 'class', align: 'center', label: 'Class', field: 'class',sortable: true},
    { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
  ]

/**
 * Manages the state and logic exclusively for the "One-Way Variable" analysis tab.
 */
export const useOneWayChartStore = defineStore("oneWayChart", {
    state: () => ({
        availableVariables: [] as VariablePoint[],
        selectedVariable: null as VariablePoint | null,
        
        primaryModelRawData: [] as DataPoint[],
        comparisonModelRawData: [] as DataPoint[],

        primaryChartData: [] as DataPoint[],
        comparisonChartData: [] as DataPoint[],

        relativities: {},
        relativitiesColumns: RELATIVITIES_COLUMNS,

        includeSuspectVariables: true,
        rescale: false,
        isLoading: false,
    }),

    getters: {
        variableOptions: (state) => {
            return state.availableVariables
        },
        hasChartData(): boolean {
            return this.primaryChartData.length > 0;
        },
        selectedVariableName: (state): string => {
            return state.selectedVariable?.variable || "";
        }
    },

    actions: {
        handleError(error: any) {
            const errorMessage = error.message || "An unknown error occurred in the One-Way Chart feature.";
            console.error("OneWayChartStore Error:", error);
            useNotification("negative", errorMessage);
        },

        setRescale(shouldRescale: boolean) {
            this.rescale = shouldRescale;
        },
        
        async fetchVariablesForModel(modelId: string) {
            console.log('fetchVariables')
            console.log(modelId);
            if (!modelId) {
                this.availableVariables = [];
                this.selectedVariable = null;
                return;
            }
            this.isLoading = true;
            try {
                const store = useModelStore();
                const model = store.models.filter( (v: ModelPoint) => v.id==modelId)[0];
                const response = await API.getVariables(model);
                this.availableVariables = response.data;
                console.log(this.availableVariables);
            } catch (err) {
                this.handleError(err);
                this.availableVariables = [];
            } finally {
                this.isLoading = false;
            }
        },

        async selectVariable(variableName: string) {
            const store = useModelStore();
            this.selectedVariable = this.availableVariables.find(v => v === variableName);
            if (!this.selectedVariable || !store.activeModel?.id) {
                this.primaryChartData = [];
                this.comparisonChartData = [];
                return;
            }

            this.isLoading = true;
            try {
                const modelTrainPoint = {id: store.activeModel.id, name: store.activeModel.name, trainTest: store.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
                // Fetch data for both primary and comparison models in parallel for efficiency.
                const promises = [
                    API.getPredictedBase(modelTrainPoint)
                ];

                if (store.comparedModel?.id) {
                    const comparedModelTrainPoint = {id: store.comparedModel.id, name: store.comparedModel.name, trainTest: store.trainTest, variable: this.selectedVariable.variable, rescale: this.rescale};
                    promises.push(API.getPredictedBase(comparedModelTrainPoint));
                }

                const [primaryResponse, comparisonResponse] = await Promise.all(promises);
                
                this.primaryModelRawData = primaryResponse.data;
                this.comparisonModelRawData = comparisonResponse?.data || [];
                
                // After fetching, process the data for display.
                this.processAndFilterData();

            } catch (err) {
                this.handleError(err);
            } finally {
                this.isLoading = false;
            }
        },
        
        processAndFilterData() {
            const store = useModelStore();
            let filteredPrimary = this.primaryModelRawData;
            if (this.rescale) {
                console.log('rescaling')
                filteredPrimary = this._applyRescaling(this.primaryModelRawData, store.baseValues1);
            }
            this.primaryChartData = filteredPrimary;

            if (this.comparisonModelRawData.length > 0) {
                let filteredComparison = this.comparisonModelRawData;
                if (this.rescale) {
                    filteredComparison = this._applyRescaling(filteredComparison, store.baseValues2);
                }
                this.comparisonChartData = filteredComparison;
            } else {
                this.comparisonChartData = [];
            }

            if (this.selectedVariable?.isInModel) {
                const relativitiesTable = store.relativitiesData.filter(item => item.variable === this.selectedVariable?.variable);
                this.relativities = relativitiesTable.map( (point) => {
                        const relativity = {'class': point.category, 'relativity': Math.round(point.relativity*1000)/1000};
                        return relativity
                })
            }
        },

        async exportOneWayChart() {
            if (!this.selectedVariable) {
                this.notifyError("No variable selected to export.");
                return;
            }
            const store = useModelStore();
            if (!store.activeModel) {
                this.notifyError("No model selected to export.");
                return;
            }
            try {
                const response = await API.exportOneWay({id: store.activeModel.id, 
                                            name: store.activeModel.name, 
                                            variable: this.selectedVariable.variable, 
                                            trainTest: store.trainTest,
                                            rescale: this.rescale});
                this._triggerDownload(response.data, store.activeModel.name + '_' + this.selectedVariable.variable + '_' + (this.trainTest ? "test" : "train") + (this.rescale ? "_rescaled" : "") + '.csv');
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

        _applyRescaling(dataPoints: DataPoint[], baseValues: any[]): DataPoint[] {
            console.log('apply rescaling');
            console.log(this.selectedVariable)
            if (!this.selectedVariable) return dataPoints;

            console.log(baseValues)
            const baseCategory = baseValues.find(item => item.variable === this.selectedVariable!.variable);
            console.log(baseCategory)
            if (!baseCategory) return dataPoints;

            const baseDataPoint = dataPoints.find(item => item.Category === baseCategory.base_level);
            console.log(baseDataPoint)
            if (!baseDataPoint) return dataPoints;

            const { baseLevelPrediction, fittedAverage, observedAverage } = baseDataPoint;

            return dataPoints.map(item => ({
                ...item,
                baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
                fittedAverage: item.fittedAverage / fittedAverage,
                observedAverage: item.observedAverage / observedAverage,
            }));
        },

        notifyError(message: string) {
            useNotification("negative", message);
        },
    }
});
