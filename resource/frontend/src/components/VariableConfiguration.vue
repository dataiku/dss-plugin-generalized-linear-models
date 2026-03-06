<template>
    <div>
        <BsTable
            class="variable-config-table"
            flat
            title="Variable Configuration"
            :rows="filteredColumns"
            :columns="columns"
            row-key="name"
            :pagination="{ rowsPerPage: 0 }"
            :virtual-scroll="false"
        >
            <template #body="props">
                <q-tr :props="props">
                    <q-td key="name" :props="props">
                        <div class="variable-name-cell">
                            <span>{{ props.row.name }}</span>
                            <span
                                v-if="getNumericFeatureCount(props.row) > 0"
                                class="numeric-feature-count"
                            >
                                ({{ getNumericFeatureCount(props.row) }})
                            </span>
                            <span
                                v-if="hasMergedLevels(props.row)"
                                class="merged-levels-dot"
                            />
                        </div>
                    </q-td>
                    <q-td key="include" :props="props" class="center-cell">
                        <BsCheckbox v-model="props.row.isIncluded" />
                    </q-td>
                    <q-td key="type" :props="props">
                        <GLMToggle
                            :model-value="getToggleValue(props.row)"
                            @update:model-value="newValue => setToggleValue(props.row, newValue)"
                            option1="Numerical"
                            option2="Categorical"
                        />
                    </q-td>
                    <q-td key="baseLevel" :props="props">
                        <div class="base-level-cell">
                            <BsSelect
                                dense
                                borderless
                                :modelValue="props.row.baseLevel"
                                :all-options="props.row.options"
                                @update:modelValue="value => props.row.baseLevel = value"
                                style="width: 100%;"
                            />
                            <BsButton
                                v-if="canShowAdvancedArrow(props.row)"
                                class="arrow-btn"
                                @click="toggleAdvancedRow(props.row)"
                                flat
                                no-caps
                                :ripple="false"
                            >
                                <q-icon :name="isExpanded(props.row) ? 'keyboard_arrow_up' : 'keyboard_arrow_down'" size="18px" />
                            </BsButton>
                        </div>
                    </q-td>
                    <q-td key="clearAllCol" :props="props" />
                </q-tr>
                <q-tr v-if="canExpandSpline(props.row) && isExpanded(props.row)" class="spline-detail-row">
                    <q-td :colspan="props.cols.length">
                        <SplineDefinitionsPanel
                            :row="props.row"
                            @add-feature="addSplineFeature(props.row)"
                            @remove-feature="featureIdx => removeSplineFeature(props.row, featureIdx)"
                            @add-knot="payload => addKnot(props.row, payload.featureIdx, payload.knot)"
                            @remove-knot="payload => removeKnot(props.row, payload.featureIdx, payload.knot)"
                            @update-feature-degree="payload => updateFeatureDegree(props.row, payload.featureIdx, payload.degree)"
                            @update-segment-degree="payload => updateSegmentDegree(props.row, payload.featureIdx, payload.segmentIdx, payload.degree)"
                        />
                    </q-td>
                </q-tr>
                <q-tr v-if="canExpandCategorical(props.row) && isExpanded(props.row)" class="spline-detail-row">
                    <q-td :colspan="props.cols.length">
                        <CategoricalDefinitionsPanel
                            :row="props.row"
                            @add-group="addCategoricalGroup(props.row)"
                            @remove-group="groupIdx => removeCategoricalGroup(props.row, groupIdx)"
                            @update-group-modalities="payload => updateCategoricalGroup(props.row, payload.groupIdx, payload.modalities)"
                        />
                    </q-td>
                </q-tr>
            </template>
        </BsTable>
    </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import { BsTable, BsToggle, BsCheckbox, BsButton } from "quasar-ui-bs";
    import { QIcon, QRadio, QTableColumn } from 'quasar';
    import { useTrainingStore } from "../stores/training";
    import GLMToggle from "./GLMToggle.vue";
    import SplineDefinitionsPanel from "./SplineDefinitionsPanel.vue";
    import CategoricalDefinitionsPanel from "./CategoricalDefinitionsPanel.vue";

    const featureHandlingColumns: QTableColumn[] = [
    {
        name: 'name',
        required: true,
        label: 'Variable Name',
        align: 'left',
        field: 'name',
        sortable: true
    },
    {
        name: 'include',
        align: 'center',
        label: 'Include?',
        field: 'isIncluded'
    },
    {
        name: 'type',
        align: 'left',
        label: 'Type',
        field: 'type'
    },
    {
        name: 'baseLevel',
        align: 'left',
        label: 'Base Level',
        field: 'baseLevel',
        style: 'width: 40%; min-width: 40%; max-width: 40%;',
        headerStyle: 'width: 40%; min-width: 40%; max-width: 40%;'
    },
];

    export default defineComponent({
    components: {
        QRadio,
        QIcon,
        BsTable,
        BsToggle,
        BsCheckbox,
        BsButton,
        GLMToggle,
        SplineDefinitionsPanel,
        CategoricalDefinitionsPanel,
    },
    props: [],
    data() {
        return {
            store: useTrainingStore(),
            columns: featureHandlingColumns,
            expandedSplineRows: {} as Record<string, boolean>,
            expandedCategoricalRows: {} as Record<string, boolean>,
        };
    },
    computed:{
        filteredColumns() {
                return this.store.datasetColumns.filter(column =>
                    column.role !== 'Target' &&
                    column.role !== 'Exposure' &&
                    column.role !== 'SampleWeight' &&
                    column.role !== 'Offset')
            },
    },
    methods: {
        canShowAdvancedArrow(row: any) {
            return row.type === "numerical" || row.type === "categorical";
        },
        canExpandSpline(row: any) {
            return row.type === "numerical";
        },
        canExpandCategorical(row: any) {
            return row.type === "categorical";
        },
        hasMergedLevels(row: any) {
            if (row.type !== "categorical" || !Array.isArray(row.categoricalGroups)) {
                return false;
            }
            return row.categoricalGroups.some((group: any[]) => Array.isArray(group) && group.length >= 2);
        },
        getNumericFeatureCount(row: any) {
            if (row.type !== "numerical" || !Array.isArray(row.splineFeatures)) {
                return 0;
            }
            return row.splineFeatures.length;
        },
        isExpanded(row: any) {
            if (row.type === "categorical") {
                return !!this.expandedCategoricalRows[row.name];
            }
            return !!this.expandedSplineRows[row.name];
        },
        toggleAdvancedRow(row: any) {
            const rowName = row.name;
            const selectedRow = this.store.datasetColumns.find((item: any) => item.name === rowName);
            if (!selectedRow) {
                return;
            }
            if (selectedRow.type === "numerical") {
                this.ensureSplineFeatures(selectedRow);
                if (!this.expandedSplineRows[rowName] && selectedRow.splineFeatures.length === 0) {
                    selectedRow.splineFeatures.push([this.defaultSegment(selectedRow)]);
                }
                this.expandedSplineRows[rowName] = !this.expandedSplineRows[rowName];
                delete this.expandedCategoricalRows[rowName];
                return;
            }
            if (selectedRow.type === "categorical") {
                this.ensureCategoricalGroups(selectedRow);
                if (!this.expandedCategoricalRows[rowName] && selectedRow.categoricalGroups.length === 0) {
                    selectedRow.categoricalGroups.push([]);
                }
                this.expandedCategoricalRows[rowName] = !this.expandedCategoricalRows[rowName];
                delete this.expandedSplineRows[rowName];
            }
        },
        getToggleValue(row: any) {
            return (row.type === 'categorical' ? 'Categorical' : 'Numerical');
        },
        setToggleValue(row: any, newValue: string) {
            row.type = (newValue === 'Categorical' ? 'categorical' : 'numerical');
            this.store.updateDatasetColumnsPreprocessing();
        },
        defaultSegment(row: any) {
            const { minValue, maxValue } = this.getFeatureBounds(row);
            return {
                min_value: minValue,
                max_value: maxValue,
                degree: 1,
            };
        },
        getFeatureBounds(row: any, feature: any[] | null = null) {
            const segmentMin = feature && feature.length > 0 ? Number(feature[0]?.min_value) : NaN;
            const segmentMax = feature && feature.length > 0 ? Number(feature[feature.length - 1]?.max_value) : NaN;
            if (Number.isFinite(segmentMin) && Number.isFinite(segmentMax) && segmentMin < segmentMax) {
                return { minValue: segmentMin, maxValue: segmentMax };
            }
            const rowMin = Number(row.minValue);
            const rowMax = Number(row.maxValue);
            if (Number.isFinite(rowMin) && Number.isFinite(rowMax) && rowMin < rowMax) {
                return { minValue: rowMin, maxValue: rowMax };
            }
            if (Number.isFinite(rowMin)) {
                return { minValue: rowMin, maxValue: rowMin + 1 };
            }
            return { minValue: 0, maxValue: 1 };
        },
        ensureSplineFeatures(row: any) {
            if (!Array.isArray(row.splineFeatures)) {
                row.splineFeatures = [];
            }
        },
        ensureCategoricalGroups(row: any) {
            if (!Array.isArray(row.categoricalGroups)) {
                row.categoricalGroups = [];
            }
        },
        getFeatureMasterDegree(feature: any[]) {
            return Array.isArray(feature) && feature.length > 0 ? Number(feature[0].degree ?? 1) : 1;
        },
        getFeatureKnots(feature: any[]) {
            if (!Array.isArray(feature) || feature.length <= 1) {
                return [];
            }
            return Array.from(
                new Set(
                    feature
                        .slice(0, -1)
                        .map((segment: any) => Number(segment.max_value))
                        .filter((value: number) => Number.isFinite(value))
                )
            ).sort((a, b) => a - b);
        },
        rebuildFeatureSegments(row: any, featureIdx: number, knots: number[], masterDegree: number) {
            this.ensureSplineFeatures(row);
            const currentFeature = row.splineFeatures[featureIdx] || [];
            const { minValue, maxValue } = this.getFeatureBounds(row, currentFeature);
            const validKnots = Array.from(
                new Set(
                    knots
                        .map((value) => Number(value))
                        .filter((value) => Number.isFinite(value) && value > minValue && value < maxValue)
                )
            ).sort((a, b) => a - b);
            const oldDegreeByRange = new Map(
                currentFeature.map((segment: any) => [`${Number(segment.min_value)}:${Number(segment.max_value)}`, Number(segment.degree)])
            );
            const boundaries = [minValue, ...validKnots, maxValue];
            const normalizedMasterDegree = Number.isFinite(masterDegree) ? Number(masterDegree) : 1;
            const rebuiltSegments = [];
            for (let i = 0; i < boundaries.length - 1; i += 1) {
                const segmentMin = boundaries[i];
                const segmentMax = boundaries[i + 1];
                const oldDegree = oldDegreeByRange.get(`${segmentMin}:${segmentMax}`);
                rebuiltSegments.push({
                    min_value: segmentMin,
                    max_value: segmentMax,
                    degree: Number.isFinite(oldDegree) ? Number(oldDegree) : normalizedMasterDegree,
                });
            }
            row.splineFeatures[featureIdx] = rebuiltSegments;
        },
        addSplineFeature(row: any) {
            this.ensureSplineFeatures(row);
            if (row.splineFeatures.length >= 3) {
                return;
            }
            row.splineFeatures.push([this.defaultSegment(row)]);
        },
        removeSplineFeature(row: any, featureIdx: number) {
            this.ensureSplineFeatures(row);
            row.splineFeatures.splice(featureIdx, 1);
        },
        addKnot(row: any, featureIdx: number, knot: number) {
            this.ensureSplineFeatures(row);
            if (!row.splineFeatures[featureIdx]) {
                row.splineFeatures[featureIdx] = [this.defaultSegment(row)];
            }
            const feature = row.splineFeatures[featureIdx];
            const knots = this.getFeatureKnots(feature);
            knots.push(Number(knot));
            this.rebuildFeatureSegments(row, featureIdx, knots, this.getFeatureMasterDegree(feature));
        },
        removeKnot(row: any, featureIdx: number, knot: number) {
            this.ensureSplineFeatures(row);
            const feature = row.splineFeatures[featureIdx];
            if (!feature) {
                return;
            }
            const knots = this.getFeatureKnots(feature).filter((value) => value !== Number(knot));
            this.rebuildFeatureSegments(row, featureIdx, knots, this.getFeatureMasterDegree(feature));
        },
        updateFeatureDegree(row: any, featureIdx: number, degree: number) {
            this.ensureSplineFeatures(row);
            const feature = row.splineFeatures[featureIdx];
            if (!feature) {
                return;
            }
            const normalizedDegree = Number.isFinite(degree) ? Number(degree) : 1;
            row.splineFeatures[featureIdx] = feature.map((segment: any) => ({
                ...segment,
                degree: normalizedDegree,
            }));
        },
        updateSegmentDegree(row: any, featureIdx: number, segmentIdx: number, degree: number) {
            this.ensureSplineFeatures(row);
            if (!row.splineFeatures[featureIdx] || !row.splineFeatures[featureIdx][segmentIdx]) {
                return;
            }
            row.splineFeatures[featureIdx][segmentIdx].degree = Number.isFinite(degree) ? Number(degree) : 1;
        },
        addCategoricalGroup(row: any) {
            this.ensureCategoricalGroups(row);
            if (row.categoricalGroups.length >= 5) {
                return;
            }
            row.categoricalGroups.push([]);
        },
        removeCategoricalGroup(row: any, groupIdx: number) {
            this.ensureCategoricalGroups(row);
            row.categoricalGroups.splice(groupIdx, 1);
        },
        normalizeCategoricalGroupValues(values: any[]) {
            const normalized = (values || []).map((value: any) => String(value));
            return Array.from(new Set(normalized));
        },
        areSameStringArrays(first: string[] = [], second: string[] = []) {
            if (first.length !== second.length) {
                return false;
            }
            return first.every((value, index) => value === second[index]);
        },
        updateCategoricalGroup(row: any, groupIdx: number, modalities: string[]) {
            this.ensureCategoricalGroups(row);
            if (groupIdx < 0 || groupIdx >= row.categoricalGroups.length) {
                return;
            }
            const normalizedModalities = this.normalizeCategoricalGroupValues(modalities || []);
            const currentGroup = this.normalizeCategoricalGroupValues(row.categoricalGroups[groupIdx] || []);
            if (!this.areSameStringArrays(currentGroup, normalizedModalities)) {
                row.categoricalGroups[groupIdx] = normalizedModalities;
            }

            const currentSet = new Set(normalizedModalities);
            row.categoricalGroups.forEach((group: string[], idx: number) => {
                if (idx === groupIdx) {
                    return;
                }
                const normalizedGroup = this.normalizeCategoricalGroupValues(group || []);
                const filteredGroup = normalizedGroup.filter((modality) => !currentSet.has(modality));
                if (!this.areSameStringArrays(normalizedGroup, filteredGroup)) {
                    row.categoricalGroups[idx] = filteredGroup;
                }
            });
        },
    },
    watch: {
        "store.datasetColumns": {
            handler() {
                const validNumericalNames = new Set(
                    this.store.datasetColumns
                        .filter((row: any) => row.type === "numerical")
                        .map((row: any) => row.name)
                );
                Object.keys(this.expandedSplineRows).forEach((name) => {
                    if (!validNumericalNames.has(name)) {
                        delete this.expandedSplineRows[name];
                    }
                });
                const validCategoricalNames = new Set(
                    this.store.datasetColumns
                        .filter((row: any) => row.type === "categorical")
                        .map((row: any) => row.name)
                );
                Object.keys(this.expandedCategoricalRows).forEach((name) => {
                    if (!validCategoricalNames.has(name)) {
                        delete this.expandedCategoricalRows[name];
                    }
                });
            },
            deep: true
        }
    }
})
</script>

<style scoped>
.row-spacing {
margin-bottom: 20px; /* Adjust this value as needed */
}
.column-management {
    display: flex;
    flex-direction: row;
    align-items: center; /* Align items vertically */
    gap: 10px; /* Spacing between each item */
    justify-content: space-between;
}
.custom-label-spacing {
    margin-right: 10px; /* Adjust the margin as needed */
    margin-left: 10px;
    padding: 5px;       /* Adjust padding for better alignment and spacing */
}
.radio-group-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: center;
    flex: 1;
}

.checkbox-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: left;
}
.column-name-container {
    margin-left: auto; /* Pushes the container to the right */
    display: flex;
    align-items: left;
    min-width: 150px;
}

.center-cell {
    text-align: center;
}

.spline-detail-row :deep(td) {
    padding: 0;
    background: #fafbff;
}

.base-level-cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    width: 100%;
    min-width: 0;
}

.base-level-cell > *:first-child {
    min-width: 0;
    flex: 1;
}

.arrow-btn {
    border: none;
    background: transparent;
    min-width: 24px;
    width: 24px;
    height: 24px;
    padding: 0;
    line-height: 1;
    cursor: pointer;
    color: #5c6478;
}

.arrow-btn:hover,
.arrow-btn:focus,
.arrow-btn:active {
    background: transparent !important;
    box-shadow: none !important;
}

.arrow-btn :deep(.q-focus-helper) {
    opacity: 0 !important;
    background: transparent !important;
}

.variable-config-table :deep(table) {
    width: 100%;
    table-layout: fixed;
}

.variable-config-table :deep(.q-table__container),
.variable-config-table :deep(.q-table),
.variable-config-table :deep(.q-table__middle) {
    width: 100%;
}

.variable-name-cell {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.merged-levels-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: #2f62ff;
    display: inline-block;
}

.numeric-feature-count {
    color: #2f62ff;
    font-weight: 600;
}
</style>
