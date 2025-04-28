<template>
    <BsLayoutDefault ref="layout" :left-panel-width="350">
      <ModelTrainingTab
        @update-models="updateModels">
      </ModelTrainingTab>
      <OneWayTab
      :reload-models="reloadModels">
      </OneWayTab>
      <VariableLevelStatsTab
      :reload-models="reloadModels">
      </VariableLevelStatsTab>
      <LiftChartTab
      :reload-models="reloadModels">
      </LiftChartTab>
      <ModelComparisonTab
      :reload-models="reloadModels">
      </ModelComparisonTab>

    </BsLayoutDefault>
</template>

<script lang="ts">
import LiftChartTab from './components/LiftChartTab.vue';
import ModelTrainingTab from './components/ModelTrainingTab.vue';
import ModelComparisonTab from './components/ModelComparisonTab.vue';
import OneWayTab from './components/OneWayTab.vue';
import VariableLevelStatsTab from './components/VariableLevelStatsTab.vue';
import { BsLayoutDefault } from "quasar-ui-bs";
import { defineComponent } from "vue";
import { API } from './Api';
export default defineComponent({
    components: {
        ModelTrainingTab,
        ModelComparisonTab,
        OneWayTab,
        VariableLevelStatsTab,
        LiftChartTab,
    },
    data() {
    return {
        reloadModels: false as boolean,
      }
    },
    methods: {
      updateModels(){
        console.log("App: update models");
        this.reloadModels = !this.reloadModels;
      },
    },
    async mounted() {
      const iframes = window.parent.document.getElementsByTagName('iframe');
      const url = iframes[0].src;
      const urlParams = new URLSearchParams(new URL(url).search);
      const webAppId = urlParams.get('webAppId');
      if (webAppId === null) {
        throw new Error('WebAppId not found in URL');
      }
      await API.sendWebappId({"webAppId": webAppId});
    }
})
</script>

<style lang="scss" scoped>

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

.close-side-drawer-btn {
    color: var(--interactions-bs-color-interaction-primary, #2b66ff);
    position: absolute;
    top: 7px;
    right: 10px;
    z-index: 1000;
}
.open-side-drawer-btn {
    color: var(--interactions-bs-color-interaction-primary, #2b66ff);
    position: relative;
    top: 4px;
}
</style>
