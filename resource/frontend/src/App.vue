<template>
    <BsLayoutDefault ref="layout" :left-panel-width="350">
      <template v-for="tabInfo in tabs" :key="tabInfo.name">
      <BsTab :name="tabInfo.name" :docTitle="tabInfo.docTitle">
                <BsTabIcon>
                    <img :src="tabInfo.icon" :alt="`${tabInfo.name} Icon`" />
                </BsTabIcon>
                <BsHeader>
                    <template #documentation>
                        <CustomDocumentation></CustomDocumentation>
                    </template>
                </BsHeader>
                <BsDrawer>
                    <component
                        :is="tabInfo.drawerComponent"
                        v-bind="tabInfo.drawerProps"
                        @update:loading="updateLoading"
                        @navigate-tab="goToTab"
                    />
                </BsDrawer>
                <BsContent>
                    <template
                        v-if="
                            tabInfo.contentComponent && !tabInfo.showEmptyState
                        "
                    >
                        <component
                            :is="tabInfo.contentComponent"
                            v-bind="tabInfo.contentProps"
                            @update:loading="updateLoading"
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
// --- DELETED ---
// import ModelVisualizationTabContent from './components/ModelVisualizationTabContent.vue';
// import ModelVisualizationTabDrawer from './components/ModelVisualizationTabDrawer.vue';
// --- DELETED ---

// --- ADDED ---
// Import the new drawer components you will create in Step 2
import OneWayVariableTabDrawer from './components/OneWayVariableTabDrawer.vue';
import VariableLevelStatsTabDrawer from './components/VariableLevelStatsTabDrawer.vue';
import LiftChartTabDrawer from './components/LiftChartTabDrawer.vue';

// Import the content components that were previously sub-tabs
import OneWayTabContent from './components/OneWayTabContent.vue';
import VariableLevelStatsTabContent from './components/VariableLevelStatsTabContent.vue';
import LiftChartTabContent from './components/LiftChartTabContent.vue';
// --- ADDED ---

import ModelTrainingTabDrawer from './components/ModelTrainingTabDrawer.vue'
import ModelTrainingTabContent from './components/ModelTrainingTabContent.vue'
import EmptyState from './components/EmptyState.vue';
import CustomDocumentation from './components/CustomDocumentation.vue';
import { BsLayoutDefault } from "quasar-ui-bs";
import { defineComponent } from "vue";
import { useModelStore } from "./stores/webapp";
import oneWayIcon from "./assets/images/one-way.svg";
import trainingIcon from "./assets/images/training.svg";
// NOTE: You may want to add new icons for the other tabs
import statsIcon from "./assets/images/variable-level-stats.svg"; // Example: create this icon
import liftIcon from "./assets/images/lift-chart.svg";   // Example: create this icon

import { useLoader } from "./composables/use-loader";

export default defineComponent({
    components: {
      // --- REMOVED ---
      // ModelVisualizationTabContent,
      // ModelVisualizationTabDrawer,
      // --- REMOVED ---
      
      // --- ADDED ---
      OneWayVariableTabDrawer,
      VariableLevelStatsTabDrawer,
      LiftChartTabDrawer,
      OneWayTabContent,
      VariableLevelStatsTabContent,
      LiftChartTabContent,
      // --- ADDED ---

      EmptyState,
      ModelTrainingTabDrawer,
      ModelTrainingTabContent,
      CustomDocumentation
    },
    data() {
    return {
        reloadModels: false as boolean,
        store: useModelStore(),
        loading: false as boolean
      }
    },
    computed: {
    tabs() {
            // Updated tabs array with 4 main tabs
            return [
                {
                    name: "Model Training",
                    docTitle: "GLM Hub",
                    icon: trainingIcon,
                    drawerComponent: "ModelTrainingTabDrawer",
                    contentComponent: "ModelTrainingTabContent",
                    contentProps: {},
                    drawerProps: {},
                    showEmptyState: false,
                    emptyState: {
                        title: "Model Training",
                        subtitle:
                            "Configure a model and start training",
                    }
                },
                {
                    name: "One-Way Variable",
                    docTitle: "GLM Hub",
                    icon: oneWayIcon,
                    drawerComponent: "OneWayVariableTabDrawer", // New Drawer
                    contentComponent: "OneWayTabContent",     // Existing Content
                    contentProps: { // Pass all necessary props to the content component
                        'chart-data': this.store.chartData,
                        'chart-data2': this.store.chartData2,
                        'selected-variable': this.store.selectedVariable,
                        relativities: this.store.relativities,
                        'relativities-columns': this.store.relativitiesColumns
                    },
                    drawerProps: {},
                    showEmptyState: !this.store.selectedModelString,
                    emptyState: {
                        title: "One-Way Variable Analysis",
                        subtitle: "Select a model in the left menu to begin",
                    }
                },
                {
                    name: "Variable-Level Stats",
                    docTitle: "GLM Hub",
                    icon: statsIcon, // Use a new or existing icon
                    drawerComponent: "VariableLevelStatsTabDrawer", // New Drawer
                    contentComponent: "VariableLevelStatsTabContent", // Existing Content
                    contentProps: {
                        'variable-level-stats-data': this.store.variableLevelStatsData,
                        columns: this.store.variableLevelStatsColumns
                    },
                    drawerProps: {},
                    showEmptyState: !this.store.selectedModelString,
                    emptyState: {
                        title: "Variable-Level Statistics",
                        subtitle: "Select a model in the left menu to view its stats",
                    }
                },
                {
                    name: "Lift Chart",
                    docTitle: "GLM Hub",
                    icon: liftIcon, // Use a new or existing icon
                    drawerComponent: "LiftChartTabDrawer", // New Drawer
                    contentComponent: "LiftChartTabContent", // Existing Content
                    contentProps: {
                        'chart-data': this.store.liftChartData
                    },
                    drawerProps: {},
                    showEmptyState: !this.store.selectedModelString,
                    emptyState: {
                        title: "Lift Chart Analysis",
                        subtitle: "Select a model in the left menu to generate a lift chart",
                    }
                }
              ]
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
    },
    methods: {
      updateModels(){
        console.log("App: update models");
        this.reloadModels = !this.reloadModels;
      },
      updateLoading(newVal: boolean) {
            this.loading = newVal;
        },
        goToTab(index: number) {
            const layout = this.$refs.layout as InstanceType<
                typeof BsLayoutDefault
            >;
            if (layout) {
                layout.tabIndex = index;
            }
        },
    },
    mounted() {
        this.store.sendWebappId();
    }
})
</script>

<style lang="scss" scoped>
/* Your existing styles remain unchanged */
body,
div {
    color: var(--text-and-icons-bs-color-text, #333e48);
}
:deep(.toggle-left-button) {
    display: none;
}
header {
  line-height: 1.5;
}
.tab-content {
  padding-left: 0px;
  padding-right: 0px;
  padding-top: 20px;
  display: flex;
  align-items: center;
  gap: var(--bs-spacing-13, 52px);
  min-height: 350px;
}
.logo {
  display: block;
  margin: 0 auto 2rem;
}
@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }
  .logo {
    margin: 0 2rem 0 0;
  }
  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>