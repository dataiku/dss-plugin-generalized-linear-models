import { defineStore } from "pinia";
import { API } from "../Api";
import { useNotification } from "../composables/use-notification";
import type { ModelPoint, VariableLevelStatsPoint } from '../models';
import type { QTableColumn } from 'quasar';
import { useModelStore } from "./webapp";
import { WT1iser, WT1EventActions } from '../utilities/utils';

const VARIABLE_STATS_COLUMNS: QTableColumn[] = [
    { name: 'variable', align: 'left', label: 'Variable', field: 'variable', sortable: true },
    { name: 'value', align: 'left', label: 'Value', field: 'value', sortable: true },
    { name: 'relativity', align: 'right', label: 'Relativity', field: 'relativity', sortable: true },
    { name: 'coefficient', align: 'right', label: 'Coefficient', field: 'coefficient', sortable: true },
    { name: 'p_value', align: 'right', label: 'P-value', field: 'p_value', sortable: true },
    { name: 'standard_error', align: 'right', label: 'Standard Error', field: 'standard_error', sortable: true },
    { name: 'standard_error_pct', align: 'right', label: 'Standard Error %', field: 'standard_error_pct', sortable: true, format: (val) => `${val}%`},
    { name: 'weight', align: 'right', label: 'Weight', field: 'weight', sortable: true },
    { name: 'weight_pct', align: 'right', label: 'Weight %', field: 'weight_pct', sortable: true, format: (val) => `${val}%`},
];

export const useVariableLevelStatsStore = defineStore("variableLevelStats", {
    state: () => ({
        modelStats: [] as VariableLevelStatsPoint[],
        columns: VARIABLE_STATS_COLUMNS,
        isLoading: false,
    }),

    actions: {
        
        handleError(error: any) {
            const errorMessage = error.message || "An unknown error occurred in the Variable Stats feature.";
            console.error("VariableLevelStatsStore Error:", error);
            useNotification("negative", errorMessage);
        },

        async fetchStatsForModel(modelName: string) {
            if (!modelName) {
                this.modelStats = [];
                return;
            }

            this.isLoading = true;
            try {
                const store = useModelStore();
                const model = store.models.filter( (v: ModelPoint) => v.name==modelName)[0];
                store.activeModel = model;
                const response = await API.getVariableLevelStats(model);

                this.modelStats = response.data.map((point: any) => ({
                    ...point,
                    coefficient: this._round(point.coefficient),
                    p_value: this._round(point.p_value),
                    standard_error: this._round(point.standard_error),
                    standard_error_pct: this._round(point.standard_error_pct),
                    weight: this._round(point.weight),
                    weight_pct: this._round(point.weight_pct),
                    relativity: this._round(point.relativity),
                }));
                WT1iser.action(WT1EventActions.CREATE_STATS_TABLE, 'Stats');
            } catch (err) {
                this.handleError(err);
                this.modelStats = [];
            } finally {
                this.isLoading = false;
            }
        },

        async exportVariableLevelStats() {
            const store = useModelStore();
            if (!store.activeModel) {
                this.notifyError("No variable selected to export.");
                return;
            }
            try {
                const response = await API.exportVariableLevelStats(store.activeModel);
                this._triggerDownload(response.data, `variable_level_stats_${store.activeModel.name}.csv`);
                WT1iser.action(WT1EventActions.DOWNLOAD_STATS_TABLE, 'Stats');
            } catch (error) {
                this.handleError(error);
            }
        },

        _triggerDownload(data: any, filename: string) {
            const url = window.URL.createObjectURL(new Blob([data], { type: 'text/csv' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        },

        _round(value: number): number {
            return Math.round(value * 1000) / 1000;
        },

        notifyError(message: string) {
            useNotification("negative", message);
        },
    }
});
