<template>
    <v-chart
      :option="chartOption"
      ref="chart"
      autoresize
      :init-options="{
          renderer: 'canvas',
      }"
      style="height: 400px; width: 100%; min-width: 500px"
    />
  </template>
  
  <script lang="ts">
  import { defineComponent, computed, PropType } from "vue";
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
      }
  },
  data() {
    return {
      chartOption: undefined as undefined | any,
    }
  },
  methods: {
    createChartData() {

      const series: any[] = [
        {
          name: "Weights",
          type: "bar",
          yAxisIndex: 1, // Assign to the right Y-axis
          itemStyle: {
            color: "#D9D8D6",
            opacity: 0.7, // Semi-transparent or different color
          },
          z: 1, // Lower z-index for background
          data: this.barData
        },
        {
          name: "Observed Average",
          type: "line",
          yAxisIndex: 0, // Assign to the left Y-axis
          itemStyle: {
            color: "#A77BCA",
            opacity: 0.7,
          },
          z: 3, // Higher z-index for main bars
          data: this.observedAverageLine,
        },
        {
            name: "Fitted Average",
            type: "line",
            yAxisIndex: 0, // Assign to the left Y-axis
            itemStyle: {
                color: "#008675",
                opacity: 0.7,
            },
            z: 3, // Higher z-index for main bars
            data: this.fittedAverageLine,
        },
        {
            name: "Base Level Prediction",
            type: "line",
            yAxisIndex: 0, // Assign to the left Y-axis
            itemStyle: {
                color: "#26d07c",
                opacity: 0.7,
            },
            z: 3, // Higher z-index for main bars
            data: this.baseLevelPredictionLine,
        },
      ];

      if (this.fittedAverageLine2) {
        series.push({
          name: "Fitted Average 2",
          type: "line",
          yAxisIndex: 0, // Assign to the left Y-axis
          itemStyle: {
            color: "#008675",
            opacity: 0.7
          },
          lineStyle: {
            type: 'dashed' // Make the line dashed
          },
          z: 3, // Higher z-index for main bars
          data: this.fittedAverageLine2,
        });
      }

      if (this.baseLevelPredictionLine2) {
        series.push({
          name: "Base Level Prediction 2",
          type: "line",
          yAxisIndex: 0, // Assign to the left Y-axis
          itemStyle: {
            color: "#26d07c",
            opacity: 0.7,
          },
          lineStyle: {
            type: 'dashed' // Make the line dashed
          },
          z: 3, // Higher z-index for main bars
          data: this.baseLevelPredictionLine2,
        });
      }

      this.chartOption = {
          xAxis: [{
              type: this.xaxisType==="categorical" ? "category" : null,
              data: this.xaxisLabels,
              axisLabel: {'interval': 0,
                          'rotate': 45,
                          },
              axisLine: { onZero: false},
          }],
          yAxis: [
                    {
                        type: "value",
                        position: "left",
                        name: "value",
                        axisLine: { onZero: false, show: true },
                        //axisLine: { onZero: false, show:false},
                        //min: 'dataMin',
                        max: function(value: any) {
                          return Math.round((value.max + (value.max-value.min)*0.1) * 100) / 100; // Adjust 'someMargin' as needed
                        },
                        min: function(value: any) {
                          return Math.round((value.min - (value.max-value.min)*0.1) * 100) / 100; // Adjust 'someMargin' as needed
                        },
                    },
                    {
                        type: "value",
                        position: "right",
                        name: "weights",
                        max: function(value: any) {
                          return Math.round((value.max + (value.max-value.min)*0.1) * 100) / 100; // Adjust 'someMargin' as needed
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
                  // Try 'horizontal'
                  // orient: 'vertical',
                  // right: '0%',
                  // top: 'center'
                  orient: 'horizontal',
                  bottom: 0
                },
                title: {
                  text: this.chartTitle,
                  left: 'center'
                },
                tooltip: {
                    trigger: 'axis', // Show tooltip for each data point
                    axisPointer: {
                        type: 'cross' // Show crosshair pointer
                    },
                    formatter: function(params: any) {
                        // Custom tooltip formatter
                        var tooltip = params[0].axisValueLabel + '<br/>'; // X-axis label
                        params.forEach(function(item: any) {
                            tooltip += item.seriesName + ': ' + (Math.round(item.data*1000.0)/1000.0) + '<br/>'; // Series name and value
                        });
                        return tooltip;
                    }
                }
            };
    },
  },
  mounted() {
      this.createChartData();
  },
  watch: {
    xaxisLabels: {
            deep: true,
            handler() {
                this.createChartData();
            },
        },
  },
}
</script>