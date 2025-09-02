import packageInfo from '../../package.json';
const version = packageInfo.version;

export enum WT1EventActions {
    CREATE_ANALYSIS = 'create-analysis',
    SELECT_ANALYSIS = 'select-analysis',
    TRAIN_MODEL = 'train-model',
    LOAD_PREVIOUS_MODEL = 'load-previous-model',
    SELECT_MODEL = 'select-model',
    DEPLOY_MODEL = 'deploy-model',
    CREATE_ONE_WAY_CHART = 'create-one-way-chart',
    SELECT_SECOND_MODEL = 'select-second-model',
    CREATE_STATS_TABLE = 'create-stats-table',
    DOWNLOAD_STATS_TABLE = 'download-stats-table',
    CREATE_LIFT_CHART = 'create-lift-chart',
    DOWNLOAD_LIFT_CHART = 'download-lift-chart',
    DELETE_MODEL = 'delete-model',
    DOWNLOAD_MODEL = 'download-model',
}
enum WT1Event {
    OPEN = 'sol-webapp-open',
    ACTION = 'sol-webapp-action'
}
export class WT1iser {
  
  private static pluginVersion = version
  private static pluginID = 'generalized-linear-models'


  private static prepareEventParams(tab: string) {
    return {
      tab: tab,
      pluginVersion: this.pluginVersion,
      pluginID: this.pluginID
    }
  }
  public static open(tab: string): void {
    const params = this.prepareEventParams(tab)
    console.debug(WT1Event.OPEN, params)
    if ((window.parent as any).WT1SVC) {
      ;(window.parent as any).WT1SVC.event(WT1Event.OPEN, params)
    }
  }
  public static action(
    actionsName: string,
    tab: string,
    extraParams?: Record<string, any>
  ): void {
    const params = {
      ...this.prepareEventParams(tab),
      action: actionsName,
      ...extraParams
    }
    console.debug(WT1Event.ACTION, params)
    if ((window.parent as any).WT1SVC) {
      ;(window.parent as any).WT1SVC.event(WT1Event.ACTION, params)
    }
  }

}