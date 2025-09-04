import packageInfo from '../../package.json';
const version = packageInfo.version;

export enum EventName {
    CREATE_ANALYSIS = 'visual-glm-create-analysis',
    SELECT_ANALYSIS = 'visual-glm-select-analysis',
    TAB_CHANGE = 'visual-glm-tab-change',
    TRAIN_MODEL = 'visual-glm-train-model',
    LOAD_PREVIOUS_MODEL = 'visual-glm-load-previous-model',
    SELECT_MODEL = 'visual-glm-select-model',
    DEPLOY_MODEL = 'visual-glm-deploy-model',
    CREATE_ONE_WAY_CHART = 'visual-glm-create-one-way-chart',
    SELECT_SECOND_MODEL = 'visual-glm-select-second-model',
    CREATE_STATS_TABLE = 'visual-glm-create-stats-table',
    DOWNLOAD_STATS_TABLE = 'visual-glm-download-stats-table',
    CREATE_LIFT_CHART = 'visual-glm-create-lift-chart',
    DOWNLOAD_LIFT_CHART = 'visual-glm-download-lift-chart',
    DELETE_MODEL = 'visual-glm-delete-model',
    DOWNLOAD_MODEL = 'visual-glm-download-model',
}

export class WT1iser {
  
  private static pluginVersion = version

  static createAnalysis(props: any) {
    this.sendEvent(EventName.CREATE_ANALYSIS, props);
  }

  static selectAnalysis() {
    this.sendEvent(EventName.SELECT_ANALYSIS, {});
  }

  static tabChange(props: any) {
    this.sendEvent(EventName.TAB_CHANGE, props);
  }

  static trainModel(props: any) {
    this.sendEvent(EventName.TRAIN_MODEL, props);
  }

  static loadPreviousModel() {
    this.sendEvent(EventName.LOAD_PREVIOUS_MODEL, {});
  }

  static selectModel() {
    this.sendEvent(EventName.SELECT_MODEL, {});
  }

  static deployModel() {
    this.sendEvent(EventName.DEPLOY_MODEL, {});
  }

  static createOneWayChart(props: any) {
    this.sendEvent(EventName.CREATE_ONE_WAY_CHART, props);
  }

  static selectSecondModel() {
    this.sendEvent(EventName.SELECT_SECOND_MODEL, {});
  }

  static createStatsTable() {
    this.sendEvent(EventName.CREATE_STATS_TABLE, {});
  }

  static downloadStatsTable() {
    this.sendEvent(EventName.DOWNLOAD_STATS_TABLE, {});
  }

  static createLiftChart(props: any) {
    this.sendEvent(EventName.CREATE_LIFT_CHART, props);
  }

  static downloadLiftChart() {
    this.sendEvent(EventName.DOWNLOAD_LIFT_CHART, {});
  }

  static deleteModel() {
    this.sendEvent(EventName.DELETE_MODEL, {});
  }

  static downloadModel() {
    this.sendEvent(EventName.DOWNLOAD_MODEL, {});
  }

  static init() {
    console.log('** visual glm version **', version)
    try {
      if (!(window.parent as any).WT1SVC && (window as any).dkuUsageReportingUtils) {
        console.debug('bootstrap standalone reporting mode')
        ;(window as any).dkuUsageReportingUtils.standaloneModeBootstrap()
      }
    } catch (error) {
      console.error('Error in WT1iser.init', error)
    }
  }

  private static prepareEventParams(props: any) {
    return {
      ...props,
      pluginVersion: this.pluginVersion
    }
  }

  private static sendEvent(event: EventName, props: any) {
    try {
      const params = this.prepareEventParams(props)
      if ((window.parent as any).WT1SVC) {
        ;(window.parent as any).WT1SVC.event(event, params)
      } else if ((window as any).dkuUsageReportingUtils) {
        ;(window as any).dkuUsageReportingUtils.standaloneModeTrackEvent(event, params)
      }
    } catch (error) {
      console.error('Error in WT1iser.sendEvent', error)
    }
  }

}