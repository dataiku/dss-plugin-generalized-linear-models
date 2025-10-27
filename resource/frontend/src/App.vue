<template>
    <BsLayoutDefault ref="layout" :left-panel-width="370" :class="{ 'no-analysis-selected': !analysisStore.selectedMlTask.mlTaskId }">
        <template v-for="tabInfo in tabs" :key="tabInfo.name">
            <BsTab :name="tabInfo.name" :docTitle="tabInfo.docTitle" :show-seperator="tabInfo.showSeperator">
                <BsTabIcon>
                    <img :src="tabInfo.icon" :alt="`${tabInfo.name} Icon`" />
                </BsTabIcon>
                    <BsHeader>
                            <template #documentation>
                                <div class="header-components">
                                    <BsLabel class="header-label" label="Analysis: " v-if="tabInfo.name !== 'Analysis Setup'" />
                                    <AnalysisSelector class="header-analysis-selector" v-if="tabInfo.name !== 'Analysis Setup'" />
                                    <BsLabel v-if="tabInfo.displayTitleInHeader" :label="tabInfo.name" className="tab-title"></BsLabel>
                                </div>
                            </template>
                    </BsHeader>
                <BsDrawer v-if="tabInfo.drawerComponent">
                    <component
                        :is="tabInfo.drawerComponent"
                        v-bind="tabInfo.drawerProps"
                        @navigate-tab="goToTab"
                    />
                </BsDrawer>
                <BsContent>
                    <template v-if="tabInfo.contentComponent && !tabInfo.showEmptyState">
                        <component
                            :is="tabInfo.contentComponent"
                            v-bind="tabInfo.contentProps"
                            @navigate-tab="goToTab"
                        />
                    </template>       
                    <template v-else>
                        <EmptyState
                            :title="tabInfo.emptyState.title"
                            :subtitle="tabInfo.emptyState.subtitle"
                        />
                    </template>
                </BsContent>
            </BsTab>
        </template>
    </BsLayoutDefault>
</template>

<script lang="ts">
import OneWayVariableTabDrawer from './components/OneWayVariableTabDrawer.vue';
import LiftChartTabDrawer from './components/LiftChartTabDrawer.vue';

import AnalysisSetup from './components/AnalysisSetup.vue';
import OneWayTabContent from './components/OneWayTabContent.vue';
import VariableLevelStatsTabContent from './components/VariableLevelStatsTabContent.vue';
import LiftChartTabContent from './components/LiftChartTabContent.vue';
import ModelManagement from './components/ModelManagement.vue'

import ModelTrainingTabContent from './components/ModelTrainingTabContent.vue'
import EmptyState from './components/EmptyState.vue';
import CustomDocumentation from './components/CustomDocumentation.vue';
import AnalysisSelector from './components/AnalysisSelector.vue';
import { BsLayoutDefault } from "quasar-ui-bs";
import { defineComponent } from "vue";
import { useModelStore } from "./stores/webapp";
import oneWayIcon from "./assets/images/one-way.svg";
import trainingIcon from "./assets/images/training.svg";
import globeIcon from "./assets/images/globe.svg";
import statsIcon from "./assets/images/variable-level-stats.svg";
import liftIcon from "./assets/images/lift-chart.svg";
import analysisIcon from "./assets/images/analysis.svg";
import { useOneWayChartStore } from "./stores/oneWayChartStore"
import { useLiftChartStore } from "./stores/liftChartStore"
import { useAnalysisStore } from "./stores/analysisStore"
import { useVariableLevelStatsStore } from "./stores/variableLevelStatsStore"

import { useLoader } from "./composables/use-loader";
import { useTrainingStore } from './stores/training';
import { WT1iser } from './utilities/utils';

export default defineComponent({
    components: {
      OneWayVariableTabDrawer,
      LiftChartTabDrawer,
      OneWayTabContent,
      VariableLevelStatsTabContent,
      LiftChartTabContent,
      ModelManagement,
      EmptyState,
      ModelTrainingTabContent,
      CustomDocumentation,
      AnalysisSetup,
      AnalysisSelector
    },
    data() {
    return {
        store: useModelStore(),
        analysisStore: useAnalysisStore(),
        trainingStore: useTrainingStore(),
        oneWayStore: useOneWayChartStore(),
        liftChartStore: useLiftChartStore(),
        variableStatsStore: useVariableLevelStatsStore(),
      }
    },
    computed: {
    tabs() {
            return [
                {
                    name: "Analysis Setup",
                    docTitle: "GLM Hub",
                    icon: analysisIcon,
                    contentComponent: "AnalysisSetup",
                    contentProps: {},
                    showEmptyState: false,
                    emptyState: {
                        title: "Analysis Setup",
                        subtitle:
                            "Select an existing analysis or create a new one",
                    },
                    showSeperator: false,
                    displayTitleInHeader: true,
                },
                {
                    name: "Model/Variable Configuration",
                    docTitle: "GLM Hub",
                    icon: trainingIcon,
                    contentComponent: "ModelTrainingTabContent",
                    contentProps: {},
                    showEmptyState: false,
                    emptyState: {
                        title: "Model Training",
                        subtitle:
                            "Configure a model and start training",
                    },
                    showSeperator: false,
                    displayTitleInHeader: true,
                },
                {
                    name: "Observed vs Predicted Chart",
                    docTitle: "GLM Hub",
                    icon: oneWayIcon,
                    drawerComponent: "OneWayVariableTabDrawer",
                    contentComponent: "OneWayTabContent",
                    contentProps: {
                        'chart-data': this.oneWayStore.primaryChartData,
                        'chart-data2': this.oneWayStore.comparisonChartData,
                        'selected-variable': this.oneWayStore.chartOptions.selectedVariable,
                        relativities: this.oneWayStore.relativities,
                        'level-order': this.oneWayStore.chartOptions.levelOrder,
                        'selected-model': this.store.activeModelName,
                        'metrics': this.store.modelMetrics1,
                        'compared-model': this.store.comparedModelName,
                        'compared-metrics': this.store.modelMetrics2,
                    },
                    drawerProps: {},
                    showEmptyState: !this.oneWayStore.primaryChartData,
                    emptyState: {
                        title: "One-Way Variable Analysis",
                        subtitle: "Select a model in the left menu to begin",
                    },
                    showSeperator: false,
                    displayTitleInHeader: false
                },
                {
                    name: "Variable-Level Statistics",
                    docTitle: "GLM Hub",
                    icon: statsIcon,
                    contentComponent: "VariableLevelStatsTabContent",
                    contentProps: {
                        'variable-level-stats-data': this.variableStatsStore.modelStats,
                        columns: this.variableStatsStore.columns
                    },
                    showSeperator: false,
                    displayTitleInHeader: true
                },
                {
                    name: "Lift Chart",
                    docTitle: "GLM Hub",
                    icon: liftIcon,
                    drawerComponent: "LiftChartTabDrawer",
                    contentComponent: "LiftChartTabContent",
                    contentProps: {
                        'chart-data': this.liftChartStore.liftChartData
                    },
                    drawerProps: {},
                    showEmptyState: !this.store.activeModelName,
                    emptyState: {
                        title: "Lift Chart Analysis",
                        subtitle: "Select a model in the left menu to generate a lift chart",
                    },
                    showSeperator: true,
                    displayTitleInHeader: false,
                },
                {
                    name: "GLM Model Management",
                    docTitle: "GLM Hub",
                    icon: globeIcon,
                    contentComponent: "ModelManagement",
                    contentProps: {
                    },
                    showEmptyState: !this.store.models,
                    emptyState: {
                        title: "Model Management",
                        subtitle: "Train a first GLM in the Training screen",
                    },
                    showSeperator: false,
                    displayTitleInHeader: true
                }
              ]
            },
        loading() {
            return this.store.isLoading || this.trainingStore.isLoading || this.oneWayStore.isLoading || this.liftChartStore.isLoading || this.variableStatsStore.isLoading;
        },
        updateModels() {
            return this.trainingStore.updateModels;
        }
    },
    watch: {
        loading(newVal) {
            console.log("App loading");
            if (newVal) {
                useLoader("Loading data..").show();
            } else {
                useLoader().hide();
            }
        },
        updateModels(newVal) {
            if (newVal) {
                console.log("App: Reload models")
                this.store.loadModels();
                this.trainingStore.updateModels = false;
            }
        }
    },
    methods: {
        goToTab(index: number) {
            WT1iser.tabChange({ tabIndex: index });
            const layout = this.$refs.layout as InstanceType<
                typeof BsLayoutDefault
            >;
            if (layout) {
                layout.tabIndex = index;
            }
        },
    }
})
</script>
<style>

.q-drawer--with-menu~.bs-drawer-container .bs-tab-title {
    padding-top: 10px;
    padding-bottom: 20px;
    color: #2B66FF !important;
    font-size: 16px;
    font-style: normal;
    font-weight: 600;
    line-height: 22px;
}
</style>

<style lang="scss" scoped>
/* General text color for the component */
body,
div {
    color: var(--text-and-icons-bs-color-text, #333e48);
}

/* This likely hides a button in the child BsLayoutDefault component */
:deep(.toggle-left-button) {
    display: none;
}

/* Basic styling for the <BsHeader> component's rendered <header> element */
header {
  line-height: 1.5;
}

/* Responsive styling for the header on larger screens */
@media (min-width: 1024px) {
  header {
    display: flex;
    /* The var() here might be from a global stylesheet */
    padding-right: calc(var(--section-gap) / 2);
  }
}

.documentation-btn {
    background-color: white;
    color: black;
    border: 1px solid #000000;

}

.tab-title {
    color: #2B66FF;
    font-size: 16px;
    font-style: normal;
    font-weight: 600;
    line-height: 22px;
    position: fixed;
    left: 62px;
}

.header-components {
    display: flex;
    align-items: center;
    gap: 16px;
    height: 36px;
}

.header-analysis-selector {
    padding-right: 16px;
}

.header-label {
    font-weight: 600;
    font-size: 16px;
    color: #333E48;
}
</style>