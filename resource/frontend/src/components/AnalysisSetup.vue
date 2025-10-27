<template>
    <div class="layout">
    <q-card flat bordered>
        <q-card-section>
            <BsLabel label="Select an Existing Analysis" className="section-title" />
            <AnalysisSelector/>
            <div class="create-switch-container">
                <BsButton 
                    v-if="mode === 'select'"
                    flat
                    no-caps
                    color="primary"
                    label="Or create a new analysis..."
                    @click="switchToCreateMode"
                />
            </div>
        </q-card-section>

        <template v-if="mode === 'create'">
            <q-separator />
            <q-card-section>
                <BsLabel label="Create a New Analysis" className="section-title" />

                <BsLabel label="Analysis Name *" :isSubLabel="true" />
                <input v-model="form.analysisName" type="text" placeholder="Enter analysis name" class="model-name-input" />

                <BsLabel label="Train Dataset *" :isSubLabel="true" />
                <BsSelect
                    v-model="form.trainSet"
                    :all-options="store.datasets"
                    @update:modelValue="handleDatasetChange"
                />

                <BsLabel label="Split Policy *" :isSubLabel="true" />
                <BsSelect
                    v-model="form.splitPolicy"
                    :all-options="store.splitPolicies"
                    :disable="!form.trainSet"
                />

                <BsLabel v-if="form.splitPolicy === 'Explicit'" label="Test Dataset *" :isSubLabel="true" />
                <BsSelect v-if="form.splitPolicy === 'Explicit'"
                    v-model="form.testSet"
                    :all-options="store.datasets"
                />

                <BsLabel label="Target Variable *" :isSubLabel="true" />
                <BsSelect
                    v-model="form.targetColumn"
                    :all-options="store.variables.filter(v => v !== form.exposureColumn)"
                    :disable="!form.trainSet"
                />

                <BsLabel label="Exposure Variable *" :isSubLabel="true" />
                <BsSelect
                    v-model="form.exposureColumn"
                    :all-options="store.variables.filter(v => v !== form.targetColumn)"
                    :disable="!form.trainSet"
                />
            </q-card-section>

            <q-card-actions align="right" class="q-pa-md">
                <BsButton flat no-caps label="Cancel" @click="switchToSelectMode" />
                <BsButton
                    unelevated
                    no-caps
                    color="primary"
                    label="Create Analysis"
                    @click="handleCreateAnalysis"
                    :disable="!isFormValid"
                    :loading="store.isLoading"
                />
            </q-card-actions>
        </template>
    </q-card>
    </div>
</template>


<script lang="ts">
import { BsButton, BsLabel, BsSelect } from 'quasar-ui-bs';
import AnalysisSelector from './AnalysisSelector.vue';
import { defineComponent } from 'vue';
import { useAnalysisStore } from '../stores/analysisStore';
import { useNotification } from '../composables/use-notification';
import type { MlTask } from '../models';

export default defineComponent({
    components: {
    BsSelect,
    AnalysisSelector,
        BsLabel,
        BsButton
    },
    name: 'AnalysisSetup',
    data() {
        return {
            store: useAnalysisStore(),
            mode: 'select' as 'select' | 'create',
            form: {
                analysisName: '',
                trainSet: '',
                testSet: '',
                splitPolicy: '',
                targetColumn: '',
                exposureColumn: '',
            }
        };
    },
    computed: {
        isFormValid(): boolean {
            return !!(this.form.analysisName && this.form.trainSet && (this.form.testSet || this.form.splitPolicy=="Random") && this.form.splitPolicy && this.form.targetColumn && this.form.exposureColumn);
        }
    },
    methods: {
        switchToCreateMode() {
            this.mode = 'create';
            this.store.selectMlTask({} as MlTask);
        },
        switchToSelectMode() {
            this.mode = 'select';
            this.form = {
                analysisName: '',
                trainSet: '',
                testSet: '',
                splitPolicy: '',
                targetColumn: '',
                exposureColumn: '',
            };
        },
        handleDatasetChange(newDataset: string) {
            this.form.targetColumn = '';
            this.form.exposureColumn = '';
            this.store.fetchVariablesForDataset(newDataset);
        },
        async handleCreateAnalysis() {
            if (!this.isFormValid) return;
            try {
                await this.store.createNewMlTask(this.form);
                this.switchToSelectMode();
            } catch (error: any) {
                useNotification("negative", error?.message || "Component failed to create analysis.");
            }
        },
        isTaskValid(mlTask: MlTask): boolean {
            return mlTask.isValid; 
    },
    },
    async mounted() {
        await this.store.fetchInitialData();
    }
});
</script>

<style scoped>
.section-title {
    font-weight: 600;
    font-size: 16px;
    display: block;
    margin-bottom: 12px;
}
.create-switch-container {
    margin-top: 8px;
}
.model-name-input {
    width: 100%;
    padding: 10px 15px;
    border: 1px solid #ccc;
    border-radius: 4px;
    height: 40px;
    margin-bottom: 10px;
}

.layout {
    padding: 32px;
}
</style>