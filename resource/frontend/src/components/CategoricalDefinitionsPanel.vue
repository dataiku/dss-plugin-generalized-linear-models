<template>
    <div class="categorical-container">
        <div class="categorical-header">
            <div class="categorical-header-meta">
                <span class="categorical-label">No. groups</span>
                <q-icon name="info" size="14px" class="categorical-info-icon" />
                <span class="group-count-value">{{ row.categoricalGroups.length }}</span>
                <q-icon v-if="hasIncompleteGroups" name="warning" size="16px" class="categorical-warning-icon" />
            </div>
            <BsButton
                class="create-group-btn"
                flat
                no-caps
                :ripple="false"
                :disabled="row.categoricalGroups.length >= 5"
                @click="$emit('add-group')"
            >
                + Create group
            </BsButton>
        </div>

        <table class="groups-table">
            <thead>
                <tr>
                    <th class="group-col">Group</th>
                    <th class="merged-col">Merged levels</th>
                    <th class="delete-col">
                        <div class="delete-header-label">Delete group</div>
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr
                    v-for="(group, groupIdx) in row.categoricalGroups"
                    :key="`${row.name}-group-${groupIdx}`"
                >
                    <td class="group-name">
                        <div class="group-name-label">Group {{ groupIdx + 1 }}</div>
                    </td>
                    <td class="merged-cell">
                        <q-select
                            dense
                            outlined
                            use-chips
                            multiple
                            :model-value="group"
                            :options="groupOptions(groupIdx)"
                            options-dense
                            popup-content-class="categorical-options-popup"
                            :placeholder="group.length === 0 ? 'Select two or more levels to form a group' : ''"
                            @update:model-value="value => $emit('update-group-modalities', { groupIdx, modalities: value })"
                        >
                            <template #option="props">
                                <q-item
                                    v-bind="props.itemProps"
                                    class="categorical-option"
                                    :class="{ 'categorical-option--selected': props.selected }"
                                >
                                    <q-item-section>{{ props.opt }}</q-item-section>
                                    <q-item-section side>
                                        <q-icon v-if="props.selected" name="check" size="16px" />
                                    </q-item-section>
                                </q-item>
                            </template>
                        </q-select>
                    </td>
                    <td class="delete-cell">
                        <div class="delete-cell-content">
                            <BsButton
                                class="delete-group-btn"
                                flat
                                no-caps
                                :ripple="false"
                                @click="$emit('remove-group', groupIdx)"
                            >
                                <q-icon name="delete" size="18px" />
                            </BsButton>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { BsButton } from "quasar-ui-bs";
import { QIcon, QItem, QItemSection, QSelect } from "quasar";

export default defineComponent({
    name: "CategoricalDefinitionsPanel",
    components: {
        BsButton,
        QIcon,
        QItem,
        QItemSection,
        QSelect,
    },
    props: {
        row: {
            type: Object,
            required: true,
        },
    },
    emits: ["add-group", "remove-group", "update-group-modalities"],
    computed: {
        hasIncompleteGroups() {
            const groups = Array.isArray(this.row.categoricalGroups) ? this.row.categoricalGroups : [];
            return groups.some((group: string[]) => !Array.isArray(group) || group.length < 2);
        },
    },
    methods: {
        groupOptions(groupIdx: number) {
            const allOptions = Array.isArray(this.row.options) ? this.row.options.map((option: any) => String(option)) : [];
            const selectedInOtherGroups = new Set(
                (this.row.categoricalGroups || [])
                    .flatMap((group: string[], idx: number) => idx === groupIdx ? [] : group)
                    .map((value: any) => String(value))
            );
            return allOptions.filter((value: string) => !selectedInOtherGroups.has(value) || (this.row.categoricalGroups[groupIdx] || []).includes(value));
        },
    },
});
</script>

<style scoped>
.categorical-container {
    width: 100%;
    padding: 12px 14px 18px;
    box-sizing: border-box;
    background: #ffffff;
}

.categorical-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.categorical-header-meta {
    display: flex;
    align-items: center;
    gap: 8px;
}

.categorical-label {
    font-size: 12px;
    font-weight: 500;
}

.group-count-value {
    min-width: 32px;
    height: 24px;
    border: 1px solid #8f98a8;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    background: #fff;
}

.categorical-warning-icon {
    color: #a64d06;
}

.create-group-btn {
    border: 1px solid #3a67f7;
    color: #3a67f7;
    border-radius: 4px;
    min-height: 34px;
    padding: 0 12px;
    font-size: 12px;
    font-weight: 600;
}

.groups-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border: 1px solid #a9acb4;
    background: #fff;
}

.groups-table th,
.groups-table td {
    border-bottom: 1px solid #a9acb4;
    padding: 12px 12px;
    font-size: 12px;
    text-align: left;
    vertical-align: middle;
    background: #ffffff !important;
}

.groups-table tr:last-child td {
    border-bottom: 0;
}

.groups-table th {
    font-weight: 700;
}

.group-col {
    width: 120px;
    text-align: center;
}

.delete-col {
    width: 140px;
    text-align: center;
}

.delete-header-label {
    width: 100%;
    display: flex;
    justify-content: center;
}

.delete-cell {
    text-align: center;
}

.group-name {
    text-align: left;
    padding-left: 12px !important;
}

.group-name-label,
.delete-cell-content {
    width: 100%;
    display: flex;
    align-items: center;
}

.merged-cell :deep(.q-field) {
    margin-top: 4px;
    margin-bottom: 4px;
}

.group-name-label {
    justify-content: flex-start;
}

.delete-cell-content {
    justify-content: center;
}

.delete-group-btn {
    color: #2f62ff;
    margin: 0 auto;
}

.groups-table :deep(.q-field__control) {
    min-height: 32px;
    height: 32px;
    background: #ffffff !important;
    border-radius: 0;
    border: 1px solid #a9acb4 !important;
    box-shadow: none !important;
}

.groups-table :deep(.q-field--outlined .q-field__control:before),
.groups-table :deep(.q-field--outlined .q-field__control:after) {
    display: none !important;
    border: 0 !important;
}

.groups-table :deep(.q-field__native),
.groups-table :deep(.q-chip) {
    background: #ffffff;
}

.groups-table :deep(.q-field__append) {
    height: 32px;
    min-height: 32px;
}

.groups-table :deep(.q-field__control-container) {
    padding-top: 0;
}

.groups-table :deep(.q-chip) {
    border: 1px solid #3a67f7;
    color: #1f2a44;
    border-radius: 999px;
    font-size: 11px;
    min-height: 20px;
    padding: 0 6px;
}

.groups-table :deep(.q-chip__icon) {
    color: #1f2a44;
    font-size: 14px;
}

.groups-table :deep(.q-field__native span) {
    display: inline-flex;
    align-items: center;
}

:global(.categorical-options-popup .categorical-option) {
    min-height: 30px;
}

:global(.categorical-options-popup .categorical-option--selected) {
    background: #d6e1fe;
    color: #214ab5;
}
</style>
