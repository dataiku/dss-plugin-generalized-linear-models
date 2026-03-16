<template>
    <v-chart
      :option="chartOption"
      ref="chart"
      autoresize
      :init-options="{
          renderer: 'canvas',
      }"
      style="height: 400px; width: 100%;"
    />
  </template>
  
<script lang="ts">
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, LineChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

export default {
  name: 'BarChart',
  components: { VChart },
  props: {
    xaxisLabels: {
      type: Array,
      required: true
    },
    xaxisType: {
      type: String,
      required: true
    },
    barData: {
      type: Array,
      required: true
    },
    observedAverageLine: {
      type: Array,
      required: true
    },
    fittedAverageLine: {
      type: Array,
      required: true
    },
    baseLevelPredictionLine: {
      type: Array,
      required: true
    },
    fittedAverageLine2: {
      type: Array,
      required: false,
      default: null
    },
    baseLevelPredictionLine2: {
      type: Array,
      required: false,
      default: null
    },
    chartTitle:{
        type: String,
        required: true,
        default: ''
      },
    levelOrder:{
        type: String,
        required: true,
        default: 'Natural order'
      },
    chartDistribution:{
        type: String,
        required: true,
        default: 'Raw data'
      },
    nbBins:{
        type: Number,
        required: false,
        default: 20
      },
    chartRescaling:{
        type: String,
        required: true,
        default: 'None'
      },
    showBaseLevelPrediction: {
      type: Boolean,
      required: false,
      default: true
    },
    legendSelection: {
      type: Object,
      required: false,
      default: () => ({})
    }
  },
  emits: ['update:legendSelection'],
  data() {
    return {
      chartOption: undefined as undefined | any,
    }
  },
  methods: {
    onLegendSelectChanged(params: any) {
      if (params && params.selected && typeof params.selected === "object") {
        this.$emit('update:legendSelection', { ...params.selected });
      }
    },
    bindLegendListener() {
      const chartComp = this.$refs.chart as any;
      const chart = chartComp?.chart;
      if (!chart) {
        return;
      }
      chart.off('legendselectchanged', this.onLegendSelectChanged);
      chart.on('legendselectchanged', this.onLegendSelectChanged);
    },
    createChartData() {
      // 1. Combine all data points into a single array of objects to sort them together, with robust null/undefined checks.
      let combinedData = (this.xaxisLabels || []).map((label, index) => ({
        label: label,
        weight: Array.isArray(this.barData) ? this.barData[index] : null,
        observed: Array.isArray(this.observedAverageLine) ? this.observedAverageLine[index] : null,
        predicted: Array.isArray(this.fittedAverageLine) ? this.fittedAverageLine[index] : null,
        base: Array.isArray(this.baseLevelPredictionLine) ? this.baseLevelPredictionLine[index] : null,
        // Handle optional data series
        fitted2: Array.isArray(this.fittedAverageLine2) ? this.fittedAverageLine2[index] : null,
        base2: Array.isArray(this.baseLevelPredictionLine2) ? this.baseLevelPredictionLine2[index] : null,
      }));

      // 2. Sort the combined data array based on the levelOrder prop.
      const order = this.levelOrder;
      if (order !== 'Natural order') {
        combinedData.sort((a, b) => {
          // Defensive: treat null/undefined as NaN, sort NaN to end
          const obsA = typeof a.observed === 'number' ? a.observed : Number.NaN;
          const obsB = typeof b.observed === 'number' ? b.observed : Number.NaN;
          const predA = typeof a.predicted === 'number' ? a.predicted : Number.NaN;
          const predB = typeof b.predicted === 'number' ? b.predicted : Number.NaN;
          switch (order) {
            case 'Ascending observed':
              return (isNaN(obsA) ? 1 : isNaN(obsB) ? -1 : obsA - obsB);
            case 'Descending observed':
              return (isNaN(obsB) ? 1 : isNaN(obsA) ? -1 : obsB - obsA);
            case 'Ascending predicted':
              return (isNaN(predA) ? 1 : isNaN(predB) ? -1 : predA - predB);
            case 'Descending predicted':
              return (isNaN(predB) ? 1 : isNaN(predA) ? -1 : predB - predA);
            default:
              return 0; // No sorting for 'Natural order' or unknown values
          }
        });
      }

      // 3. "Unzip" the sorted data back into individual arrays for ECharts.
  const sortedXaxisLabels = combinedData.map(d => d.label);
  const sortedBarData = combinedData.map(d => d.weight);
  const sortedObservedAverageLine = combinedData.map(d => d.observed);
  const sortedFittedAverageLine = combinedData.map(d => d.predicted);
  const sortedBaseLevelPredictionLine = combinedData.map(d => d.base);
  const sortedFittedAverageLine2 = Array.isArray(this.fittedAverageLine2) ? combinedData.map(d => d.fitted2) : null;
  const sortedBaseLevelPredictionLine2 = Array.isArray(this.baseLevelPredictionLine2) ? combinedData.map(d => d.base2) : null;


      // 4. Build the chart series using the new sorted data arrays.
      const series: any[] = [
        {
          name: "Weights",
          type: "bar",
          yAxisIndex: 1,
          itemStyle: { color: "#D9D8D6", opacity: 0.7 },
          z: 1,
          data: sortedBarData // Use sorted data
        },
        {
          name: "Observed Average",
          type: "line",
          yAxisIndex: 0,
          itemStyle: { color: "#A77BCA", opacity: 0.7 },
          z: 3,
          data: sortedObservedAverageLine, // Use sorted data
        },
        {
            name: "Fitted Average",
            type: "line",
            yAxisIndex: 0,
            itemStyle: { color: "#008675", opacity: 0.7 },
            z: 3,
            data: sortedFittedAverageLine, // Use sorted data
        },
        {
            name: "Base Level Prediction",
            type: "line",
            yAxisIndex: 0,
            itemStyle: { color: "#26d07c", opacity: 0.7 },
            z: 3,
            data: sortedBaseLevelPredictionLine, // Use sorted data
        },
      ];

      if (!this.showBaseLevelPrediction) {
        const baseSeriesIdx = series.findIndex((s) => s.name === "Base Level Prediction");
        if (baseSeriesIdx >= 0) {
          series.splice(baseSeriesIdx, 1);
        }
      }

      // Only add model 2 lines if they have at least one non-null, non-undefined value
      const hasFitted2 = Array.isArray(sortedFittedAverageLine2) && sortedFittedAverageLine2.some(v => v !== null && v !== undefined);
      const hasBase2 = Array.isArray(sortedBaseLevelPredictionLine2) && sortedBaseLevelPredictionLine2.some(v => v !== null && v !== undefined);
      if (hasFitted2) {
        series.push({
          name: "Fitted Average 2",
          type: "line",
          yAxisIndex: 0,
          itemStyle: { color: "#008675", opacity: 0.7 },
          lineStyle: { type: 'dashed' },
          z: 3,
          data: sortedFittedAverageLine2, // Use sorted data
        });
      }
      if (hasBase2) {
        series.push({
          name: "Base Level Prediction 2",
          type: "line",
          yAxisIndex: 0,
          itemStyle: { color: "#26d07c", opacity: 0.7 },
          lineStyle: { type: 'dashed' },
          z: 3,
          data: sortedBaseLevelPredictionLine2, // Use sorted data
        });
      }
      if (!this.showBaseLevelPrediction) {
        const baseSeries2Idx = series.findIndex((s) => s.name === "Base Level Prediction 2");
        if (baseSeries2Idx >= 0) {
          series.splice(baseSeries2Idx, 1);
        }
      }

      // 5. Define the final chart option object, with legend only for present series.
      const availableLegendEntries = series.reduce((acc: Record<string, boolean>, s: any) => {
        acc[s.name] = true;
        return acc;
      }, {});
      const persistedSelection = Object.entries(this.legendSelection || {}).reduce((acc: Record<string, boolean>, [name, value]) => {
        if (Object.prototype.hasOwnProperty.call(availableLegendEntries, name)) {
          acc[name] = Boolean(value);
        }
        return acc;
      }, {});
      const selectedLegendState = { ...availableLegendEntries, ...persistedSelection };

      this.chartOption = {
      xAxis: [{
        type: "category",
        data: sortedXaxisLabels, // Use sorted labels
        axisLabel: {'interval': 0, 'rotate': 45 },
        axisLine: { onZero: false},
      }],
          yAxis: [
              {
                  type: "value",
                  position: "left",
                  name: "value",
                  axisLine: { onZero: false, show: true },
                  min: function(value: any) {
                    if (isNaN(value.min) || isNaN(value.max)) return 0;
                    if (value.min === value.max) return value.min - 1; // avoid flat line
                    return Math.floor((value.min - (value.max - value.min) * 0.1) * 100) / 100;
                  },
                  max: function(value: any) {
                    if (isNaN(value.min) || isNaN(value.max)) return 1;
                    if (value.min === value.max) return value.max + 1;
                    return Math.ceil((value.max + (value.max - value.min) * 0.1) * 100) / 100;
                  },
              },
              {
                  type: "value",
                  position: "right",
                  name: "weights",
                  max: function(value: any) {
                    return Math.round((value.max + (value.max-value.min)*0.1) * 100) / 100;
                  },
                  splitLine: {show: false} ,
              },
          ],
          grid: {
              top: 40,
              left: 0,
              right: 0,
              containLabel: true,
          },
          series: series,
          legend: {
            orient: 'horizontal',
            bottom: 0,
            data: series.map(s => s.name), // Only show legend for present series
            selected: selectedLegendState
          },
          title: {
            text: this.chartTitle,
            left: 'center'
          },
          tooltip: {
              trigger: 'axis',
              axisPointer: { type: 'cross' },
              formatter: function(params: any) {
                  var tooltip = params[0].axisValueLabel + '<br/>';
                  params.forEach(function(item: any) {
                      tooltip += item.seriesName + ': ' + (Math.round(item.data*1000.0)/1000.0) + '<br/>';
                  });
                  return tooltip;
              }
          }
      };
      this.$nextTick(() => {
        this.bindLegendListener();
      });
    },
  },
  mounted() {
      this.createChartData();
  },
  beforeUnmount() {
    const chartComp = this.$refs.chart as any;
    const chart = chartComp?.chart;
    if (chart) {
      chart.off('legendselectchanged', this.onLegendSelectChanged);
    }
  },
  watch: {
    xaxisLabels: {
        deep: true,
        handler() {
            this.createChartData();
        },
    },
    levelOrder: {
        handler() {
            this.createChartData();
        }
    },
    legendSelection: {
        deep: true,
        handler() {
            this.createChartData();
        }
    }
  },
}

</script>
