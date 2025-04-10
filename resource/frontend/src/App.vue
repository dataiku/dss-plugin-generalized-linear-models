<template>
    <BsLayoutDefault ref="layout" :left-panel-width="350">
      <template v-for="tabInfo in tabs" :key="tabInfo.name">
      <BsTab :name="tabInfo.name" :docTitle="tabInfo.docTitle">
                <BsTabIcon>
                    <img :src="tabInfo.icon" :alt="`${tabInfo.name} Icon`" />
                </BsTabIcon>
                <BsHeader>
                    <!-- <template #content>
                        <Header
                            :target="tabInfo.headerInfo.target"
                            :target-date="tabInfo.headerInfo.targetDate"
                            :target-type="tabInfo.headerInfo.targetType"
                        ></Header>
                    </template> -->
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
import ModelVisualizationTabContent from './components/ModelVisualizationTabContent.vue';
import ModelVisualizationTabDrawer from './components/ModelVisualizationTabDrawer.vue';
import ModelTrainingTabDrawer from './components/ModelTrainingTabDrawer.vue'
import ModelTrainingTabContent from './components/ModelTrainingTabContent.vue'
import EmptyState from './components/EmptyState.vue';
import CustomDocumentation from './components/CustomDocumentation.vue';
import { BsLayoutDefault } from "quasar-ui-bs";
import { defineComponent } from "vue";
import { useModelStore } from "./stores/webapp";
import oneWayIcon from "./assets/images/one-way.svg";
import trainingIcon from "./assets/images/training.svg";
import { useLoader } from "./composables/use-loader";

export default defineComponent({
    components: {
      ModelVisualizationTabContent,
      ModelVisualizationTabDrawer,
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
                    name: "Model Visualization",
                    docTitle: "GLM Hub",
                    icon: oneWayIcon,
                    drawerComponent: "ModelVisualizationTabDrawer",
                    contentComponent: "ModelVisualizationTabContent",
                    contentProps: {},
                    drawerProps: {},
                    showEmptyState: !this.store.chartData,
                    emptyState: {
                        title: "Model Visualization",
                        subtitle:
                            "Select a model and variable in the left menu",
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
