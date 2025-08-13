<template>
    <div>
        <q-card flat bordered>
            <q-card-section>
                <BsLabel
                    label="Model Configuration">
                </BsLabel>
            </q-card-section>
            <q-separator />
            <q-card-section>
                <BsLabel
                    label="Name"
                    isSubLabel="true">
                </BsLabel>
                <input
                        v-model="store.modelName"
                        type="text"
                        id="modelNameInput"
                        placeholder="Enter model name"
                        class="model-name-input"
                />
            </q-card-section>
            <q-card-section>
                <BsLabel
                    label="Parameters">
                </BsLabel>

                <BsLabel
                    label="Load a previous model"
                    isSubLabel="true">
                </BsLabel>
                <BsSelect
                    :modelValue="store.selectedModelString"
                    :all-options="store.modelsString"
                    @update:modelValue="value => store.getDatasetColumns(value)"
                    style="min-width: 250px">
                </BsSelect>
                <BsLabel
                        label="Select a Distribution Function"
                        isSubLabel="true"
                        info-text="Distribution function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="store.selectedDistributionFunctionString"
                    :all-options="store.distributionOptions"
                    @update:modelValue="value => store.updateModelProperty('selectedDistributionFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
                <BsLabel
                        label="Select a Link Function"
                        isSubLabel="true"
                        info-text="Link function for GLM"
                ></BsLabel>
                <BsSelect
                    :modelValue="store.selectedLinkFunctionString"
                    :all-options="store.linkOptions"
                    @update:modelValue="value => store.updateModelProperty('selectedLinkFunctionString', value)"
                    style="min-width: 150px">
                </BsSelect>
        </q-card-section>
        <q-card-section>
            <BsLabel
                label="Regularization"
            ></BsLabel>
            <div class="variable-select-container">
            <BsLabel
                    label="Set the Elastic Net Penalty"
                    isSubLabel="true"
                    info-text="The overall level of regularization"
            ></BsLabel>
            <BsSlider
                v-model="store.selectedElasticNetPenalty"
                :min="0"
                :step="0.01"
                :max="1000"
                style="min-width: 150px">
            </BsSlider>
            <BsLabel
                    label="Set the L1 Ratio"
                    isSubLabel="true"
                    info-text="l1_ratio = 0 means Ridge (only L2), l1_ratio = 1 means LASSO (only L1)"
            ></BsLabel>
            <BsSlider
                v-model="store.selectedL1Ratio"
                :min="0"
                :max="1"
                :step="0.01"
                style="min-width: 150px">
            </BsSlider>
    
            </div>
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
                :disable="!store.isModelNameValid.valid"
                />
            </div>
            </q-footer>
        </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import type { ErrorPoint, AccType } from '../models';
    import EmptyState from './EmptyState.vue';
    import { BsTab, BsTabIcon, BsLayoutDefault, BsHeader, BsButton, BsDrawer, BsContent, BsTooltip, BsSlider, BsCard } from "quasar-ui-bs";
    import docLogo from "../assets/images/doc-logo-example.svg";
    import trainingIcon from "../assets/images/training.svg";
    import { API } from '../Api';
    import { QRadio, QCard, QSeparator, QCardSection } from 'quasar';
    import type { AxiosError } from 'axios';
    import { isAxiosError } from 'axios';
    import VariableInteractions from './VariableInteractions.vue'
    import { useTrainingStore } from "../stores/training";
    
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
            store: useTrainingStore(),
            layoutRef: undefined as undefined | InstanceType<typeof BsLayoutDefault>,
            trainingIcon,
            docLogo,
            errorMessage: "" as string,
        };
    },
    emits: ['update:modelValue', 'update-models', "update:loading"],
    watch: {
        isLoading(newValue) {
            console.log('watch is loading')
            this.$emit("update:loading", newValue);
        },
        updateModels(newValue) {
            this.$emit("update-models", newValue);
        }
    },
    methods: {
        async submitVariables() {
            this.store.trainModel();
        },
    },
    computed: {
        isLoading() { 
            console.log('computed is loading')
            return this.store.isLoading;
        },
        updateModels() {
            return this.store.updateModels;
        }
    },
    async mounted() {
        API.getModels().then((data: any) => {
            this.store.models = data.data;
            this.store.modelsString = this.store.models.map(item => item.name);
          });
        this.layoutRef = this.$refs.layout as InstanceType<typeof BsLayoutDefault>;
        const savedDistributionFunction = localStorage.getItem('DistributionFunction');
        const savedLinkFunction = localStorage.getItem('linkFunction');
        await this.store.getDatasetColumns();
    
        
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
    .variable-select-container {
        padding: 20px;
    }
    .model-name-input-container {
      padding: 20px
    }
    
    .model-name-input {
      width: 87%;
      padding: 15px;
      border: 1px solid #ccc;
      border-radius: 4px;
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
    </style>