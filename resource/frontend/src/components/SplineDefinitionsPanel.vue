<template>
    <div class="spline-container">
        <div class="spline-header">
            <div class="spline-header-meta">
                <span class="spline-label">No. features</span>
                <q-icon name="info" size="14px" class="spline-info-icon" />
                <span class="feature-count-value">{{ row.splineFeatures.length }}</span>
            </div>
            <div class="spline-actions">
                <BsButton
                    class="create-feature-btn"
                    @click="$emit('add-feature')"
                    :disabled="row.splineFeatures.length >= 3"
                    flat
                    no-caps
                    :ripple="false"
                >
                    + Create feature
                </BsButton>
            </div>
        </div>

        <div class="feature-grid">
            <div
                v-for="(feature, featureIdx) in row.splineFeatures"
                :key="`${row.name}-feature-${featureIdx}`"
                class="feature-card"
            >
                <div class="feature-card-header">
                    <div class="feature-header-main">
                        <span>Feature {{ featureIdx + 1 }}</span>
                        <span class="degree-label">Degree</span>
                        <BsSelect
                            dense
                            borderless
                            class="degree-select degree-select--feature"
                            :modelValue="featureMasterDegree(feature)"
                            :all-options="degreeOptions"
                            input-style="display: none;"
                            @update:modelValue="value => $emit('update-feature-degree', { featureIdx, degree: Number(value) })"
                        />
                    </div>
                    <BsButton class="close-btn" flat no-caps :ripple="false" @click="$emit('remove-feature', featureIdx)">
                        <q-icon name="close" size="16px" />
                    </BsButton>
                </div>
                <div class="knot-editor">
                    <input
                        class="knot-input"
                        type="number"
                        placeholder="Enter knot value"
                        :value="knotInputs[featureIdx] ?? ''"
                        @input="setKnotInput(featureIdx, ($event.target as HTMLInputElement).value)"
                    />
                    <BsButton
                        class="add-knot-btn"
                        flat
                        no-caps
                        :ripple="false"
                        @click="emitAddKnot(featureIdx)"
                    >
                        + Add knot
                    </BsButton>
                </div>
                <div class="knot-chips">
                    <span
                        v-for="knot in featureKnots(feature)"
                        :key="`${featureIdx}-${knot}`"
                        class="knot-chip"
                    >
                        {{ knot }}
                        <BsButton class="knot-remove-btn" flat no-caps :ripple="false" @click="$emit('remove-knot', { featureIdx, knot })">
                            <q-icon name="close" size="12px" />
                        </BsButton>
                    </span>
                </div>
                <table class="segment-table">
                    <thead>
                        <tr>
                            <th>Segment</th>
                            <th>Degree</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="(segment, segmentIdx) in feature"
                            :key="`${row.name}-${featureIdx}-${segmentIdx}`"
                        >
                            <td>{{ segment.min_value }} - {{ segment.max_value }}</td>
                            <td>
                                <BsSelect
                                    dense
                                    borderless
                                    class="degree-select degree-select--segment"
                                    :modelValue="segment.degree"
                                    :all-options="degreeOptions"
                                    input-style="display: none;"
                                    @update:modelValue="value => $emit('update-segment-degree', { featureIdx, segmentIdx, degree: Number(value) })"
                                />
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { BsButton, BsSelect } from "quasar-ui-bs";
import { QIcon } from "quasar";

export default defineComponent({
    name: "SplineDefinitionsPanel",
    components: {
        BsButton,
        BsSelect,
        QIcon,
    },
    props: {
        row: {
            type: Object,
            required: true,
        },
    },
    emits: [
        "add-feature",
        "remove-feature",
        "add-knot",
        "remove-knot",
        "update-feature-degree",
        "update-segment-degree",
    ],
    data() {
        return {
            knotInputs: {} as Record<number, string>,
            degreeOptions: [0, 1, 2, 3],
        };
    },
    methods: {
        featureMasterDegree(feature: any[]) {
            return Array.isArray(feature) && feature.length > 0 ? Number(feature[0].degree ?? 1) : 1;
        },
        featureKnots(feature: any[]) {
            if (!Array.isArray(feature) || feature.length <= 1) {
                return [];
            }
            return feature.slice(0, -1).map((segment: any) => segment.max_value);
        },
        setKnotInput(featureIdx: number, value: string) {
            this.knotInputs[featureIdx] = value ?? "";
        },
        emitAddKnot(featureIdx: number) {
            const raw = this.knotInputs[featureIdx];
            const knot = Number(raw);
            if (!Number.isFinite(knot)) {
                return;
            }
            this.$emit("add-knot", { featureIdx, knot });
            this.knotInputs[featureIdx] = "";
        },
    },
});
</script>

<style scoped>
.spline-container {
    --spline-card-bg: #F7F9FF;
    --spline-card-border: #e3e9ff;
    --spline-chip-border: #bcc8e8;
    --spline-cell-border: #d6d9e0;
    --spline-control-border: #b8bcc9;
    --spline-primary: #3a67f7;
    margin: 0;
    width: 100%;
    box-sizing: border-box;
    padding: 10px 14px 18px;
    background: #ffffff;
}

.spline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    margin-bottom: 12px;
    width: 100%;
    flex-wrap: nowrap;
}

.spline-header-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

.spline-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 0 0 auto;
    margin-left: auto;
}

.spline-label {
    font-size: 14px;
    font-weight: 400;
    line-height: 1.1;
    color: #212121;
}

.spline-info-icon {
    color: #121212;
}

.feature-count-value {
    min-width: 32px;
    height: 24px;
    border: 1px solid #8f98a8;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 8px;
    font-size: 13px;
    font-weight: 500;
    line-height: 1.1;
    color: #101010;
    background: #fff;
}

.create-feature-btn {
    border: 1px solid var(--spline-primary);
    color: var(--spline-primary);
    background-color: #FFFFFF;
    border-radius: 5px;
    min-height: 34px;
    padding: 0 14px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
    letter-spacing: 0;
    font-size: 16px;
    font-weight: 400;
}

.create-feature-btn:disabled,
.create-feature-btn.disabled,
.create-feature-btn[disabled],
.create-feature-btn[aria-disabled="true"] {
    opacity: 0.35;
    border: 1px solid #b8bcc9 !important;
    color: #b8bcc9 !important;
    background-color: #ffffff !important;
}

.feature-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-start;
}

.feature-card {
    flex: 0 0 calc((100% - 32px) / 3);
    max-width: calc((100% - 32px) / 3);
    min-width: 0;
    border: 1px solid var(--spline-card-border);
    border-radius: 0;
    padding: 12px;
    background: var(--spline-card-bg);
    box-sizing: border-box;
    overflow: hidden;
}

.feature-card:nth-child(2) {
    background: #EBF0FF;
}

.feature-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 10px;
    font-weight: 600;
}

.feature-header-main {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex: 0 1 auto;
    color: #171717;
}

.feature-header-main > span:first-child {
    font-size: 16px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 0 1 auto;
}

.degree-label {
    font-weight: 400;
    font-size: 16px;
}

.degree-select {
    min-width: 72px;
    width: 72px;
    max-width: 72px;
}

.knot-editor {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}

.knot-input {
    min-width: 0;
    width: 126px;
    height: 33px;
    border: 1px solid var(--spline-control-border);
    border-radius: 2px;
    background: #ffffff;
    font-size: 12px;
    padding: 0 10px;
    box-sizing: border-box;
}

.knot-input:focus {
    outline: none;
    border-color: #8ea6ff;
}

.add-knot-btn {
    border: 1px solid var(--spline-primary);
    color: var(--spline-primary);
    background-color: #FFFFFF;
    border-radius: 5px;
    min-height: 33px;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
}

.knot-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 12px;
    min-height: 34px;
}

.knot-chip {
    display: inline-flex;
    align-items: center;
    border: 1px solid #3445CB;
    border-radius: 9999px;
    height: 24px;
    padding: 0 8px;
    gap: 4px;
    background: #ffffff;
    font-size: 10px;
    line-height: 1;
    color: #262626;
}

.knot-remove-btn {
    min-width: 12px;
    height: 12px;
    padding: 0;
    font-size: 10px;
    font-weight: 100;
    line-height: 1;
    color: #202020;
}

.close-btn {
    min-width: 18px;
    height: 18px;
    padding: 0;
    flex: 0 0 auto;
    font-size: 14px;
    line-height: 1;
    font-weight: 500;
    color: #1f1f1f;
}

.segment-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid var(--spline-cell-border);
    background: #ffffff !important;
    margin-bottom: 0;
}

.segment-table th,
.segment-table td {
    border-right: 0;
    border-bottom: 1px solid var(--spline-cell-border);
    padding: 8px 10px !important;
    font-size: 14px;
    font-weight: 400;
    color: #252525;
}

.segment-table tr:last-child td {
    border-bottom: 0;
}

.segment-table th {
    background: #ffffff !important;
    font-size: 14px;
    font-weight: 600;
}

.segment-table th:first-child {
    text-align: left;
    width: calc(100% - 88px);
}

.segment-table th:last-child {
    text-align: left;
    width: 88px;
}

.segment-table td {
    background: #ffffff !important;
}

.segment-table td:first-child {
    width: calc(100% - 88px);
}

.segment-table td:last-child {
    text-align: left;
    vertical-align: middle;
    width: 88px;
}

.degree-select--segment {
    min-width: 68px;
    width: 68px;
    max-width: 68px;
    margin: 0;
}

.degree-select :deep(.q-field__control) {
    border-radius: 0 !important;
    min-height: 28px;
    background: #ffffff !important;
    overflow: hidden;
}

.degree-select--feature :deep(.q-field__control) {
    height: 33px !important;
    min-height: 33px !important;
}

.degree-select--feature :deep(.q-field__native),
.degree-select--feature :deep(.q-field__marginal),
.degree-select--feature :deep(.q-field__append),
.degree-select--feature :deep(.q-field__prepend) {
    height: 33px !important;
    min-height: 33px !important;
    display: flex;
    align-items: center;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.degree-select--feature :deep(.bs-font-medium-2-normal) {
    line-height: 33px !important;
}

.degree-select--segment :deep(.q-field__control) {
    height: 28px !important;
    min-height: 28px !important;
}

.degree-select--segment :deep(.q-field__native),
.degree-select--segment :deep(.q-field__marginal),
.degree-select--segment :deep(.q-field__append),
.degree-select--segment :deep(.q-field__prepend) {
    height: 28px !important;
    min-height: 28px !important;
    display: flex;
    align-items: center;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.degree-select--segment :deep(.bs-font-medium-2-normal) {
    line-height: 28px !important;
}

.create-feature-btn :deep(.q-focus-helper),
.add-knot-btn :deep(.q-focus-helper),
.knot-remove-btn :deep(.q-focus-helper),
.close-btn :deep(.q-focus-helper) {
    opacity: 0 !important;
    background: transparent !important;
}
</style>
