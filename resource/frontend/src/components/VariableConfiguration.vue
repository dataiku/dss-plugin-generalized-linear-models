<template>
        <BsTable
            flat
            title="Variable Configuration"
            :rows="filteredColumns"
            :columns="columns"
            row-key="name"
            :pagination="{ rowsPerPage: 0 }"
            hide-bottom
            class="feature-table">

            <template #body-cell-include="props">
                <q-td :props="props">
                    <BsCheckbox v-model="props.row.isIncluded" />
                </q-td>
            </template>

            <template #body-cell-type="props">
                
                <q-td :props="props" class="type-cell">

                    <BsToggle
                    :model-value="getToggleValue(props.row)"
                    @update:model-value="newValue => setToggleValue(props.row, newValue)"
                    label-left="Numerical"
                    label-right="Categorical"/>
                </q-td>
            </template>

            <template #body-cell-baseLevel="props">
                <q-td :props="props">
                    <BsSelect
                        dense
                        borderless
                        :modelValue="props.row.baseLevel"
                        :all-options="props.row.options"
                        @update:modelValue="value => props.row.baseLevel = value"
                        style="min-width: 150px;"
                    />
                </q-td>
            </template>
        </BsTable>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import { BsTable, BsToggle, BsCheckbox } from "quasar-ui-bs";
    import docLogo from "../assets/images/doc-logo-example.svg";
    import trainingIcon from "../assets/images/training.svg";
    import { QRadio, QTableColumn } from 'quasar';
    import { useTrainingStore } from "../stores/training";
    
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
        field: 'baseLevel'
    }
];

    export default defineComponent({
    components: {
        QRadio,
        BsTable,
        BsToggle, 
        BsCheckbox
    },
    props: [],
    data() {
        return {
            store: useTrainingStore(),
            columns: featureHandlingColumns,
        };
    },
    computed:{
        filteredColumns() {
                return this.store.datasetColumns.filter(column =>
                    column.role !== 'Target' &&
                    column.role !== 'Exposure')
            },
    },
    methods: {
        getToggleValue(row: any) {
            return row.type === 'categorical';
        },
        setToggleValue(row: any, newValue: boolean) {
            row.type = newValue ? 'categorical' : 'numerical';
        },
    },
    watch: {
        "store.datasetColumns": {
            handler(newVal) {
                this.store.updateDatasetColumnsPreprocessing();
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
</style>