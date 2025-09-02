import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import { useModelStore } from "./webapp";
import type { DataPoint, VariablePoint, ModelPoint } from '../models';
import { WT1iser, WT1EventActions } from '../utilities/utils';

interface RelativityRow {
  class: string;
  relativity: number;
  compared_relativity?: number;
}

/**
 * Manages the state and logic exclusively for the "One-Way Variable" analysis tab.
 */
export const useOneWayChartStore = defineStore("oneWayChart", {
    state: () => ({
        availableVariables: [] as VariablePoint[],
        
        primaryModelRawData: [] as DataPoint[],
        comparisonModelRawData: [] as DataPoint[],

        primaryChartData: [] as DataPoint[],
        comparisonChartData: [] as DataPoint[],

        relativities: {},

        includeSuspectVariables: true,
        isLoading: false,

        formOptions: {
            selectedVariable: null as VariablePoint | null,
            levelOrder: "Natural order",
            chartDistribution: "Raw data",
            nbBins: 20,
            chartRescaling: "None",
            trainTest: true,
            comparisonModel: "",
        },

        chartOptions: {
            selectedVariable: null as VariablePoint | null,
            levelOrder: "Natural order",
            chartDistribution: "Raw data",
            nbBins: 20,
            chartRescaling: "None",
            trainTest: true,
            comparisonModel: "",
        }
        
    }),

    getters: {
        variableOptions: (state) => {
            return state.availableVariables
        },
        hasChartData(): boolean {
            return this.primaryChartData.length > 0;
        },
        selectedVariableName: (state): string => {
            return state.formOptions.selectedVariable?.variable || "";
        }
    },

    actions: {
        resetState() {
            this.$reset();
        },

        handleError(error: any) {
            const errorMessage = error.message || "An unknown error occurred in the One-Way Chart feature.";
            console.error("OneWayChartStore Error:", error);
            useNotification("negative", errorMessage);
        },

        applyForm() {
            this.chartOptions.selectedVariable = this.formOptions.selectedVariable;
            this.chartOptions.levelOrder = this.formOptions.levelOrder;
            this.chartOptions.chartDistribution = this.formOptions.chartDistribution;
            this.chartOptions.nbBins = this.formOptions.nbBins;
            this.chartOptions.chartRescaling = this.formOptions.chartRescaling;
            this.chartOptions.trainTest = this.formOptions.trainTest;
            this.chartOptions.comparisonModel = this.formOptions.comparisonModel;
        },

        async createChart() {
            this.isLoading = true;
            if (this.chartOptions.trainTest != this.formOptions.trainTest) {
                if (this.formOptions.selectedVariable) {
                    await this.selectVariable(this.formOptions.selectedVariable);
                }
            }
            this.applyForm();
            this.processAndFilterData();
            WT1iser.action(WT1EventActions.TRAIN_MODEL, 'Training', {
                chartDistribution: this.chartOptions.chartDistribution,
                chartRescaling: this.chartOptions.chartRescaling,
                nbBins: this.chartOptions.nbBins,
                trainTest: this.chartOptions.trainTest
            });
            this.isLoading = false;
        },

        setRescale(rescaling: string) {
            this.formOptions.chartRescaling = rescaling;
        },

        setTrainTest(trainTest: boolean) {
            this.formOptions.trainTest = trainTest;
        },

        setChartDistribution(chartDistribution: string) {
            this.formOptions.chartDistribution = chartDistribution;
        },

        setNbBins(nbBins: number) {
            this.formOptions.nbBins = nbBins;
        },

        setLevelOrder(levelOrder: string) {
            this.formOptions.levelOrder = levelOrder;
        },

        setComparisonModel(comparisonModel: string | null) {
            if (!comparisonModel) {
                this.formOptions.comparisonModel = "";
                // this.createChart();
                this.processAndFilterData();
            } else {
                this.formOptions.comparisonModel = comparisonModel;
            }
        },
        
        async fetchVariablesForModel(modelName: string) {
            if (!modelName) {
                this.availableVariables = [];
                this.formOptions.selectedVariable = null;
                return;
            }
            this.isLoading = true;
            try {
                const store = useModelStore();
                const model = store.models.filter( (v: ModelPoint) => v.name==modelName)[0];
                const response = await API.getVariables(model);
                this.availableVariables = response.data;
            } catch (err) {
                this.handleError(err);
                this.availableVariables = [];
            } finally {
                this.isLoading = false;
            }
        },

        async selectVariable(variableName: VariablePoint) {
            const store = useModelStore();
            let foundVariable = this.availableVariables.find(v => v === variableName);
            if (foundVariable) {
                this.formOptions.selectedVariable = foundVariable
            }
            if (!this.formOptions.selectedVariable || !store.activeModel?.id) {
                this.primaryChartData = [];
                this.comparisonChartData = [];
                return;
            }

            try {
                const modelTrainPoint = {id: store.activeModel.id, name: store.activeModel.name, trainTest: store.trainTest, variable: this.formOptions.selectedVariable.variable, chartRescaling: this.chartOptions.chartRescaling};
                const promises = [
                    API.getPredictedBase(modelTrainPoint)
                ];
                if (store.comparedModel?.id) {
                    const comparedModelTrainPoint = {id: store.comparedModel.id, name: store.comparedModel.name, trainTest: store.trainTest, variable: this.formOptions.selectedVariable.variable, chartRescaling: this.chartOptions.chartRescaling};
                    promises.push(API.getPredictedBase(comparedModelTrainPoint));
                } else {
                    this.comparisonChartData = [];
                }

                const responses = await Promise.all(promises);
                
                this.primaryModelRawData = responses[0].data;

                if (responses.length > 1) {
                    this.comparisonModelRawData = responses[1].data;
                } else {
                    this.comparisonModelRawData = [];
                }

            } catch (err) {
                this.handleError(err);
            } finally {
            }
        },
        
        processAndFilterData() {
            console.log('process and filter data')
            const store = useModelStore();
            let filteredPrimary = this.primaryModelRawData;
            if (this.chartOptions.chartRescaling == "Base level") {
                filteredPrimary = this._applyRescaling(this.primaryModelRawData, store.baseValues1);
            } else if (this.chartOptions.chartRescaling == "Ratio") {
                filteredPrimary = this._applyRescalingRatio(this.primaryModelRawData);
            }
            if (this.chartOptions.chartDistribution == "Binning") {
                filteredPrimary = this._binData(filteredPrimary, this.chartOptions.nbBins);
            }
            this.primaryChartData = filteredPrimary;

            if (this.comparisonModelRawData.length > 0) {
                let filteredComparison = this.comparisonModelRawData;
                if (this.chartOptions.chartRescaling == "Base level") {
                    filteredComparison = this._applyRescaling(filteredComparison, store.baseValues2);
                } else if (this.chartOptions.chartRescaling == "Ratio") {
                    filteredComparison = this._applyRescalingRatio(filteredComparison);
                }
                if (this.chartOptions.chartDistribution == "Binning") {
                filteredComparison = this._binData(filteredComparison, this.chartOptions.nbBins);
            }
                this.comparisonChartData = filteredComparison;
            } else {
                this.comparisonChartData = [];
            }

            if (this.chartOptions.selectedVariable?.isInModel) {
                const relativitiesTable = store.relativitiesData.filter(item => item.variable === this.chartOptions.selectedVariable?.variable);
                const relativitiesMap2 = new Map();
                if (store.relativitiesData2.length > 0) {
                    const relativitiesTable2 = store.relativitiesData2.filter(item => item.variable === this.chartOptions.selectedVariable?.variable);
                    relativitiesTable2.forEach(item => {
                        relativitiesMap2.set(item.category, item.relativity);
                    });
                }

                this.relativities = relativitiesTable.map((point) => {
                    const relativity: RelativityRow = {
                        'class': point.category,
                        'relativity': Math.round(point.relativity * 1000) / 1000
                    };

                    if (relativitiesMap2.has(point.category)) {
                        relativity.compared_relativity = Math.round(relativitiesMap2.get(point.category) * 1000) / 1000;
                    }

                    return relativity;
                });
            }
            console.log('process and filter data done')
        },

        async exportOneWayChart() {
            if (!this.chartOptions.selectedVariable) {
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
                                            variable: this.chartOptions.selectedVariable.variable, 
                                            trainTest: store.trainTest,
                                            chartRescaling: this.chartOptions.chartRescaling});
                this._triggerDownload(response.data, store.activeModel.name + '_' + this.chartOptions.selectedVariable.variable + '_' + (this.chartOptions.trainTest ? "test" : "train") + this.chartOptions.chartRescaling + '.csv');
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
            if (!this.chartOptions.selectedVariable) return dataPoints;

            const baseCategory = baseValues.find(item => item.variable === this.chartOptions.selectedVariable!.variable);
            if (!baseCategory) return dataPoints;

            const baseDataPoint = dataPoints.find(item => item.Category === baseCategory.base_level);
            if (!baseDataPoint) return dataPoints;

            const { baseLevelPrediction, fittedAverage, observedAverage } = baseDataPoint;

            return dataPoints.map(item => ({
                ...item,
                baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
                fittedAverage: item.fittedAverage / fittedAverage,
                observedAverage: item.observedAverage / observedAverage,
            }));
        },

        _applyRescalingRatio(dataPoints: DataPoint[]): DataPoint[] {
            if (!this.chartOptions.selectedVariable) return dataPoints;

            return dataPoints.map(item => ({
                ...item,
                baseLevelPrediction: item.baseLevelPrediction / item.observedAverage,
                fittedAverage: item.fittedAverage / item.observedAverage,
                observedAverage: item.observedAverage / item.observedAverage,
            }));
        },

        _isNumerical(data: DataPoint[]): boolean {
            return data.every(d => isFinite(Number(d.Category)));
        },

        _binNumericalData(data: DataPoint[], binCount: number): DataPoint[] {
            if (binCount < 1) return [];

            const definingVariable = data[0]?.definingVariable || 'Unknown';
            const numericData = data.map(d => ({...d, Category: parseFloat(d.Category as string)}));
            const categories = numericData.map(d => d.Category);
            const min = Math.min(...categories);
            const max = Math.max(...categories);
            
            if (min === max) {
                const totalWeight = numericData.reduce((sum, d) => sum + d.Value, 0);
                if (totalWeight === 0) {
                    return [{ definingVariable, Category: `${min}`, Value: 0, observedAverage: 0, fittedAverage: 0, baseLevelPrediction: 0 }];
                }
                const weightedObserved = numericData.reduce((sum, d) => sum + d.observedAverage * d.Value, 0) / totalWeight;
                const weightedFitted = numericData.reduce((sum, d) => sum + d.fittedAverage * d.Value, 0) / totalWeight;
                const weightedBase = numericData.reduce((sum, d) => sum + d.baseLevelPrediction * d.Value, 0) / totalWeight;
                return [{
                    definingVariable,
                    Category: `${min}`,
                    Value: totalWeight,
                    observedAverage: weightedObserved,
                    fittedAverage: weightedFitted,
                    baseLevelPrediction: weightedBase,
                }];
            }

            const binWidth = (max - min) / binCount;
            const bins: DataPoint[][] = Array.from({ length: binCount }, () => []);

            for (const point of numericData) {
                let binIndex = Math.floor((point.Category - min) / binWidth);
                if (binIndex === binCount) {
                    binIndex--;
                }
                bins[binIndex].push(point);
            }
            
            const finalBinnedData: DataPoint[] = [];

            for (let i = 0; i < binCount; i++) {
                const binContent = bins[i];
                const binStart = min + i * binWidth;
                const binEnd = binStart + binWidth;
                const categoryLabel = `${binStart.toFixed(2)} - ${binEnd.toFixed(2)}`;

                if (binContent.length === 0) {
                    finalBinnedData.push({ definingVariable, Category: categoryLabel, Value: 0, observedAverage: 0, fittedAverage: 0, baseLevelPrediction: 0 });
                    continue;
                }

                const totalWeight = binContent.reduce((sum, d) => sum + d.Value, 0);
                if (totalWeight === 0) {
                    finalBinnedData.push({ definingVariable, Category: categoryLabel, Value: 0, observedAverage: 0, fittedAverage: 0, baseLevelPrediction: 0 });
                    continue;
                }
                const weightedObserved = binContent.reduce((sum, d) => sum + d.observedAverage * d.Value, 0) / totalWeight;
                const weightedFitted = binContent.reduce((sum, d) => sum + d.fittedAverage * d.Value, 0) / totalWeight;
                const weightedBase = binContent.reduce((sum, d) => sum + d.baseLevelPrediction * d.Value, 0) / totalWeight;

                finalBinnedData.push({
                    definingVariable,
                    Category: categoryLabel,
                    Value: totalWeight,
                    observedAverage: weightedObserved,
                    fittedAverage: weightedFitted,
                    baseLevelPrediction: weightedBase,
                });
            }

            return finalBinnedData;
        },

        _binCategoricalData(data: DataPoint[], binCount: number): DataPoint[] {
            if (binCount < 1) return [];

            const definingVariable = data[0]?.definingVariable || 'Unknown';
            const categoryWeights = new Map<string | number, number>();
            for (const point of data) {
                const currentWeight = categoryWeights.get(point.Category) || 0;
                categoryWeights.set(point.Category, currentWeight + point.Value);
            }

            const sortedCategories = [...categoryWeights.entries()].sort((a, b) => b[1] - a[1]);

            const topCategoryNames = sortedCategories.slice(0, binCount - 1).map(c => c[0]);
            const otherCategories = new Set(sortedCategories.slice(binCount - 1).map(c => c[0]));
            
            const finalCategories = [...topCategoryNames];
            if (otherCategories.size > 0) {
                finalCategories.push("Others");
            }

            const finalBinnedData: DataPoint[] = [];

            for (const catName of finalCategories) {
                let pointsInGroup: DataPoint[];
                if (catName === "Others") {
                    pointsInGroup = data.filter(d => otherCategories.has(d.Category));
                } else {
                    pointsInGroup = data.filter(d => d.Category === catName);
                }

                if (pointsInGroup.length === 0) {
                    finalBinnedData.push({ definingVariable, Category: String(catName), Value: 0, observedAverage: 0, fittedAverage: 0, baseLevelPrediction: 0 });
                    continue;
                }

                const totalWeight = pointsInGroup.reduce((sum, d) => sum + d.Value, 0);
                if (totalWeight === 0) {
                    finalBinnedData.push({ definingVariable, Category: String(catName), Value: 0, observedAverage: 0, fittedAverage: 0, baseLevelPrediction: 0 });
                    continue;
                }
                const weightedObserved = pointsInGroup.reduce((sum, d) => sum + d.observedAverage * d.Value, 0) / totalWeight;
                const weightedFitted = pointsInGroup.reduce((sum, d) => sum + d.fittedAverage * d.Value, 0) / totalWeight;
                const weightedBase = pointsInGroup.reduce((sum, d) => sum + d.baseLevelPrediction * d.Value, 0) / totalWeight;
                
                finalBinnedData.push({
                    definingVariable,
                    Category: String(catName),
                    Value: totalWeight,
                    observedAverage: weightedObserved,
                    fittedAverage: weightedFitted,
                    baseLevelPrediction: weightedBase,
                });
            }

            return finalBinnedData;
        },

        _binData(data: DataPoint[], binCount: number): DataPoint[] {
            if (!data || data.length === 0 || !binCount || binCount <= 0) {
                return [];
            }

            if (this._isNumerical(data)) {
                return this._binNumericalData(data, binCount);
            } else {
                return this._binCategoricalData(data, binCount);
            }
        },

        notifyError(message: string) {
            useNotification("negative", message);
        },
    }
});
