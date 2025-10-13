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
  import VChart from "vue-echarts";
  import { CanvasRenderer } from "echarts/renderers";
  import { use } from "echarts/core";

  use(CanvasRenderer);
  
  export default {
  name: 'LiftChart',
  components: { VChart },
  props: {
    xaxisLabels: {
      type: Array,
      required: true
    },
    barData: {
      type: Array,
      required: true
    },
    observedData: {
      type: Array,
      required: true
    },
    predictedData: {
      type: Array,
      required: true
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
      this.chartOption = {
          xAxis: [{
              type: "category",
              data: this.xaxisLabels,
              axisLabel: {'interval': 0,
                          'rotate': 45
              }
          }],
          yAxis: [
                    {
                        type: "value",
                        position: "left",
                        name: "value",
                        axisLine: { onZero: false, show: true },
                    },
                    {
                        type: "value",
                        position: "right",
                        name: "weights",
                        splitLine: {show: false} ,
                    },
                ],
                grid: {
                    top: 40,
                    left: 0,
                    right: 0,
                    containLabel: true,
                },
                series: [
                    {
                        name: "Weights",
                        type: "bar",
                        yAxisIndex: 1, // Assign to the right Y-axis
                        itemStyle: {
                            color: "#D9D8D6",
                            // color: "gray",
                            opacity: 0.7, // Semi-transparent or different color
                        },
                        z: 1, // Lower z-index for background
                        data: this.barData
                    },
                    {
                        name: "Observed Data",
                        type: "line",
                        yAxisIndex: 0, // Assign to the left Y-axis
                        itemStyle: {
                            color: "#A77BCA",

                            opacity: 0.7,
                        },
                        z: 3, // Higher z-index for main bars
                        data: this.observedData,
                    },
                    {
                        name: "Predicted Data",
                        type: "line",
                        yAxisIndex: 0, // Assign to the left Y-axis
                        itemStyle: {
                            color: "#008675",
                            opacity: 0.7,
                        },
                        z: 3, // Higher z-index for main bars
                        data: this.predictedData,
                    },
                ],
                legend: {
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
                            tooltip += item.seriesName + ': ' + item.data + '<br/>'; // Series name and value
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