import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import { isErrorPoint } from '../models';
import type { 
  DataPoint, ModelPoint, RelativityPoint, VariablePoint, VariableLevelStatsPoint, LiftDataPoint, 
  ModelMetricsDataPoint, BaseValue 
} from '../models';
import type { QTableColumn } from "quasar";

function roundDecimals(x: number): number {
    return Math.round(x * 1000) / 1000;
  }

const rows = [
    {
        class: 'January',
        relativity: 1.0,
    },
    {
        class: 'February',
        relativity: 1.087,
    },
    {
        class: 'March',
        relativity: 0.98,
    },
    {
        class: 'April',
        relativity: 1.12,
    }
  ]

  const columns: QTableColumn[] = [
    { name: 'class', align: 'center', label: 'Class', field: 'class',sortable: true},
    { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
  ]

  const variableLevelStatsColumns: QTableColumn[] = [
    { name: 'variable', align: 'center', label: 'Variable', field: 'variable',sortable: true},
    { name: 'value', align: 'center', label: 'Value', field: 'value',sortable: true},
    { name: 'coefficient', align: 'center', label: 'Coefficient', field: 'coefficient',sortable: true},
    { name: 'standard_error', align: 'center', label: 'Standard Error', field: 'standard_error',sortable: true},
    { name: 'standard_error_pct', align: 'center', label: 'Standard Error PCT', field: 'standard_error_pct',sortable: true},
    { name: 'weight', align: 'center', label: 'Weight', field: 'weight',sortable: true},
    { name: 'weight_pct', align: 'center', label: 'Weight PCT', field: 'weight_pct',sortable: true},
    { name: 'relativity', align: 'center', label: 'Relativity', field: 'relativity', sortable: true},
  ]

export const useModelStore = defineStore("GLMStore", {
    state: () => ({
      models: [] as ModelPoint[],
      activeModel: {} as ModelPoint,
      comparedModel: {} as ModelPoint,
      modelsString: [] as string[],
      selectedModelString: "",
      selectedModelString2: "",
      chartData: [] as DataPoint[],
      chartData2: [] as DataPoint[],
      liftChartData: [] as LiftDataPoint[],
      allData: [] as DataPoint[],
      allData2: [] as DataPoint[],
      relativitiesData: [] as RelativityPoint[],
      relativitiesData2: [] as RelativityPoint[],
      relativitiesTable: [] as RelativityPoint[],
      relativities: rows,
      relativitiesColumns: columns,
      variablePoints: [] as VariablePoint[],
      allVariables: [] as String[],
      variables: [] as VariablePoint[],
      selectedVariable: {} as VariablePoint,
      variableLevelStatsColumns: variableLevelStatsColumns,
      variableLevelStatsData: [] as VariableLevelStatsPoint[],
      variableLevelStatsData2: [] as VariableLevelStatsPoint[],
      modelMetrics1: {} as ModelMetricsDataPoint,
      modelMetrics2: {} as ModelMetricsDataPoint,
      baseValues1: [] as BaseValue[],
      baseValues2: [] as BaseValue[],
      nbBins: 8,
      trainTest: false,
      rescale: false,
      includeSuspectVariables: true,
      tab: "one-way-variable",
      comparisonChartTitle: "Model Metrics",
    }),
    actions: {
      async sendWebappId() {
        const iframes = window.parent.document.getElementsByTagName('iframe');
        const url = iframes[0].src;
        const urlParams = new URLSearchParams(new URL(url).search);
        const webAppId = urlParams.get('webAppId');
        if (webAppId === null) {
          throw new Error('WebAppId not found in URL');
        }
        await API.sendWebappId(webAppId);
      },
      async loadModels() {
        try {
          const response = await API.getModels();
          this.models = response.data;
          this.modelsString = this.models.map(item => item.name);
        } catch (error) {
          this.handleError(error);
        }
      },
      async updateTrainTest(value: boolean) {
        this.trainTest = value;
        const modelTrainPoint = {id: this.activeModel.id, name: this.activeModel.name, trainTest: this.trainTest};
        const dataResponse = await API.getData(modelTrainPoint);
        this.allData = dataResponse?.data;
        const modelLiftPoint = { nbBins: this.nbBins, id: modelTrainPoint.id, name: modelTrainPoint.name, trainTest: this.trainTest};
        const liftDataResponse = await API.getLiftData(modelLiftPoint);
        this.liftChartData = liftDataResponse?.data;
        this.updateChartData();
      },
      async updateModelString(value: string) {
              try {
                this.selectedVariable = {} as VariablePoint;
                const model = this.models.filter( (v: ModelPoint) => v.name==value)[0];
                this.activeModel = model
                const variableResponse = await API.getVariables(model)
                if (isErrorPoint(variableResponse?.data)) {
                  this.handleError(variableResponse?.data.error);
                } else {
                  this.variablePoints = variableResponse?.data;
                  this.allVariables = this.variablePoints.map(item => item.variable);
                  const modelTrainPoint = {id: model.id, name: model.name, trainTest: this.trainTest};
                  const dataResponse = await API.getData(modelTrainPoint);
                  this.allData = dataResponse?.data;
                  const relativityResponse = await API.getRelativities(model);
                  this.relativitiesData = relativityResponse?.data;
                  this.selectedModelString = value;
                }
                const baseResponse = await API.getBaseValues(model);
                this.baseValues1 = baseResponse?.data;
                const variableLevelStatsResponse = await API.getVariableLevelStats(model);
                this.variableLevelStatsData = variableLevelStatsResponse?.data.map( (point) => {
                    const variableLevelStats = {'variable': point.variable, 'value': point.value, 
                                                'coefficient': roundDecimals(point.coefficient),
                                                'standard_error': roundDecimals(point.standard_error), 
                                                'standard_error_pct': roundDecimals(point.standard_error_pct),
                                                'weight': roundDecimals(point.weight), 
                                                'weight_pct': roundDecimals(point.weight_pct), 
                                                'relativity': roundDecimals(point.relativity)};
                    return variableLevelStats
                });
                const modelNbBins = { nbBins: this.nbBins, id: model.id, name: model.name, trainTest: this.trainTest};
                const dataResponse = await API.getLiftData(modelNbBins);
                this.liftChartData = dataResponse?.data;
                const ModelMetricsResponse = await API.getModelMetrics(model);
                this.modelMetrics1 = ModelMetricsResponse?.data as ModelMetricsDataPoint;
            } catch (err) {
                this.handleError(err);
            }
      },
      async updateModelString2(value: string) {
              try {
                this.selectedVariable = {} as VariablePoint;
                const model = this.models.filter( (v: ModelPoint) => v.name==value)[0];
                this.comparedModel = model;
                const modelTrainPoint = {id: model.id, name: model.name, trainTest: this.trainTest};
                const dataResponse = await API.getData(modelTrainPoint);
                this.allData2 = dataResponse?.data;
                const relativityResponse = await API.getRelativities(model);
                this.relativitiesData2 = relativityResponse?.data;
                this.selectedModelString2 = value;
                const baseResponse = await API.getBaseValues(model);
                this.baseValues2 = baseResponse?.data;
                const variableLevelStatsResponse = await API.getVariableLevelStats(model);
                this.variableLevelStatsData2 = variableLevelStatsResponse?.data.map( (point) => {
                    const variableLevelStats = {'variable': point.variable, 'value': point.value, 
                                                'coefficient': roundDecimals(point.coefficient),
                                                'standard_error': roundDecimals(point.standard_error), 
                                                'standard_error_pct': roundDecimals(point.standard_error_pct),
                                                'weight': roundDecimals(point.weight), 
                                                'weight_pct': roundDecimals(point.weight_pct), 
                                                'relativity': roundDecimals(point.relativity)};
                    return variableLevelStats
                });
                const ModelMetricsResponse = await API.getModelMetrics(model);
                this.modelMetrics2 = ModelMetricsResponse?.data as ModelMetricsDataPoint;
              } catch (err) {
                  this.handleError(err);
              }
      },
      async updateChartData() {
        this.relativitiesTable = this.relativitiesData.filter(item => item.variable === this.selectedVariable.variable);
        this.relativities = this.relativitiesTable.map( (point) => {
        const relativity = {'class': point.category, 'relativity': Math.round(point.relativity*1000)/1000};
        return relativity
      })
      if (this.rescale) {
          const baseCategory = this.baseValues1.find(item => item.variable === this.selectedVariable.variable);
          if (baseCategory) {
            const baseData = this.allData.find(item => item.Category === baseCategory.base_level && item.definingVariable === this.selectedVariable.variable);
            if (baseData) {
              const baseLevelPrediction = baseData.baseLevelPrediction;
              const fittedAverage = baseData.fittedAverage;
              const observedAverage = baseData.observedAverage;
          this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable).map(item => ({
              ...item,
              baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
              fittedAverage: item.fittedAverage / fittedAverage,
              observedAverage: item.observedAverage / observedAverage
              }));
            } else {
          this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
          }
          } else {
            this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
          }
          if (this.selectedModelString2) {
            const baseCategory2 = this.baseValues2.find(item => item.variable === this.selectedVariable.variable);
            if (baseCategory2) {
            const baseData2 = this.allData2.find(item => item.Category === baseCategory2.base_level && item.definingVariable === this.selectedVariable.variable);
            if (baseData2) {
              const baseLevelPrediction = baseData2.baseLevelPrediction;
              const fittedAverage = baseData2.fittedAverage;
              const observedAverage = baseData2.observedAverage;
          this.chartData2 = this.allData2.filter(item => item.definingVariable === this.selectedVariable.variable).map(item => ({
              ...item,
              baseLevelPrediction: item.baseLevelPrediction / baseLevelPrediction,
              fittedAverage: item.fittedAverage / fittedAverage,
              observedAverage: item.observedAverage / observedAverage
              }));
            } else {
            this.chartData2 = this.allData2.filter(item => item.definingVariable === this.selectedVariable.variable);
            }
          } else {
            this.chartData2 = this.allData2.filter(item => item.definingVariable === this.selectedVariable.variable);
            }
        }
      } else {
          this.chartData = this.allData.filter(item => item.definingVariable === this.selectedVariable.variable);
          if (this.selectedModelString2) {
            this.chartData2 = this.allData2.filter(item => item.definingVariable === this.selectedVariable.variable);
          }
    }
      },
     async updateNbBins(value: number) {
        this.nbBins = value;
        const model = this.models.filter( (v: ModelPoint) => v.name==this.selectedModelString)[0];
        const modelNbBins = { nbBins: this.nbBins, id: model.id, name: model.name, trainTest: this.trainTest};
        const dataResponse = await API.getLiftData(modelNbBins);
        this.liftChartData = dataResponse?.data;
    },
    async exportModel() {
        API.exportModel(this.activeModel).then(response => {
            const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', this.selectedModelString + '.csv'); // Set the filename for the download
            document.body.appendChild(link);
            link.click();
            window.URL.revokeObjectURL(url); // Clean up
        }).catch(error => {
            console.error('Error exporting model:', error);
        });
    },
    async exportOneWay() {
        API.exportOneWay({id: this.activeModel.id, 
            name: this.activeModel.name, 
            variable: this.selectedVariable.variable, 
            trainTest: this.trainTest,
            rescale: this.rescale}).then(response => {
              const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
              const link = document.createElement('a');
              link.href = url;
              link.setAttribute('download', this.selectedModelString + '_' + this.selectedVariable.variable + '_' + (this.trainTest ? "test" : "train") + (this.rescale ? "_rescaled" : "") + '.csv'); // Set the filename for the download
              document.body.appendChild(link);
              link.click();
              window.URL.revokeObjectURL(url); // Clean up
          }).catch(error => {
              console.error('Error exporting model:', error);
          });
    },
    async exportStats() {
        API.exportVariableLevelStats(this.activeModel).then(response => {
            const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'variable_level_stats.csv'); // Set the filename for the download
            document.body.appendChild(link);
            link.click();
            window.URL.revokeObjectURL(url); // Clean up
        }).catch(error => {
            console.error('Error exporting model:', error);
        });
    },
    handleError(msg: any) {
      console.error(msg);
      this.notifyError(msg);
  },
      notifyError(msg: string) {
        useNotification("negative", msg);
    },
    },
  });