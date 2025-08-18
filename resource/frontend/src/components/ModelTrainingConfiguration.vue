<template>
    <div>
        <q-card flat bordered>
            <q-card-section>
                <BsLabel
                    label="Model Configuration"
                    className="section-title">
                </BsLabel>
                <BsLabel
                    className="explanation"
                    label="* Fields marked with an asterisk are mandatory"
                    :isSubLabel="true">
                </BsLabel>
            </q-card-section>
            <q-separator />
            <q-card-section>
                <BsLabel
                    label="Name *"
                    :isSubLabel="true">
                </BsLabel>
                <input
                        v-model="trainingStore.modelName"
                        type="text"
                        id="modelNameInput"
                        placeholder="Enter model name"
                        class="model-name-input"
                />
            </q-card-section>
            <q-card-section>
                <BsLabel
                    label="Parameters"
                    className="section-title">
                </BsLabel>

                <BsLabel
                    label="Load a previous model"
                    :isSubLabel="true">
                </BsLabel>
                <BsSelect
                    :all-options="store.modelOptions"
                    @update:modelValue="value => trainingStore.getDatasetColumns(value)"
                    style="min-width: 250px">
                </BsSelect>
                <BsLabel
                        label="Select a Distribution Function *"
                        :isSubLabel="true"
                        info-text="Distribution function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="trainingStore.selectedDistributionFunctionString"
                    :all-options="trainingStore.distributionOptions"
                    @update:modelValue="value => trainingStore.updateModelProperty('selectedDistributionFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
                <BsLabel
                        label="Select a Link Function *"
                        :isSubLabel="true"
                        info-text="Link function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="trainingStore.selectedLinkFunctionString"
                    :all-options="trainingStore.linkOptions"
                    @update:modelValue="value => trainingStore.updateModelProperty('selectedLinkFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
        </q-card-section>
        <q-card-section>
            <BsLabel
                label="Regularization"
                className="section-title"
            ></BsLabel>
            <BsLabel
                    label="Set the Elastic Net Penalty"
                    :isSubLabel="true"
                    info-text="The overall level of regularization"
            ></BsLabel>
            <input className="model-name-input" type="number" v-model.number="trainingStore.selectedElasticNetPenalty"/>
            <BsLabel
                    label="Set the L1 Ratio"
                    :isSubLabel="true"
                    info-text="l1_ratio = 0 means Ridge (only L2), l1_ratio = 1 means LASSO (only L1)"
            ></BsLabel>
            <BsSlider
                v-model="trainingStore.selectedL1Ratio"
                :min="0"
                :max="1"
                :step="0.01"
                class="slider-input">
            </BsSlider>
        </q-card-section>
        </q-card>
        <q-footer 
            bordered 
            class="bg-white text-primary q-pa-sm"
            >
            <div class="row items-center justify-end">
                <BsButton
                unelevated
                no-caps
                color="primary"
                label="Train Model" 
                @click="submitVariables"
                :disable="!trainingStore.isModelNameValid.valid"
                />
            </div>
            </q-footer>
        </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import EmptyState from './EmptyState.vue';
    import { BsTab, BsTabIcon, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip, BsSlider, BsCard } from "quasar-ui-bs";
    import { QRadio, QCard, QSeparator, QCardSection } from 'quasar';
    import VariableInteractions from './VariableInteractions.vue'
    import { useTrainingStore } from "../stores/training";
    import { useModelStore } from "../stores/webapp";
    
    export default defineComponent({
    components: {
        EmptyState,
        VariableInteractions,
        BsTab,
        BsTabIcon,
        BsHeader,
        BsButton,
        BsDrawer,
        BsContent,
        BsTooltip,
        QRadio,
        BsSlider,
        BsCard,
        QCard, 
        QSeparator, 
        QCardSection
    
    },
    props: [],
    data() {
        return {
            trainingStore: useTrainingStore(),
            store: useModelStore(),
        };
    },
    watch: {
        updateModels(newValue) {
            this.$emit("update:models", newValue);
        }
    },
    methods: {
        async submitVariables() {
            this.trainingStore.trainModel();
        },
    },
    computed: {
        updateModels() {
            return this.trainingStore.updateModels;
        }
    },
    async mounted() {
        await this.store.loadModels();
        await this.trainingStore.getDatasetColumns();
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
    .form-group {
    display: flex;
    flex-direction: column; /* Stack the label and select vertically */
    margin-bottom: 15px; /* Spacing between each form group */
    }
    
    .form-group label {
    margin-bottom: 5px; /* Space between label and select */
    }
    
    /* If you want the label and dropdown to be on the same line, switch .form-group to row */
    .form-group.row {
    flex-direction: row;
    align-items: center; /* Align items vertically */
    }
    
    .form-group.row label {
    margin-right: 10px; /* Space between label and select, when inline */
    margin-bottom: 0; /* Remove bottom margin when inline */
    }
    
    .form-group.row select {
    flex-grow: 1; /* Let the select take up available space */
    }
    .outline-box {
    border: 2px solid #000; /* Solid black border, adjust as needed */
    padding: 20px; /* Optional: Adds some spacing inside the box */
    margin: 20px 0; /* Optional: Adds some spacing outside the box */
    background-color: #f5f5f5; 
    }
    .h5-spacing {
    margin-bottom: 10px;
    margin-top: 5px;
    }
    .model-name-input-container {
      padding: 20px
    }
    
    .model-name-input {
      width: 100%;
      padding: 15px;
      border: 1px solid #ccc;
      border-radius: 4px;
      height: 40px;
    }
    .error-message {
      color: red;
      margin-top: 10px;
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

    .section-title {
        font-weight: 600;
        font-size: 16px;
        color: #333E48;
        margin-bottom: 6px;
    }

    .explanation {
        font-size: 12px;
    }

    .slider-input :deep(.q-slider) {
        width: 100% !important;
        max-width: 100% !important;
    }
    </style>