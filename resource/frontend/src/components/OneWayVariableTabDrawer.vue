<template>
    <div class="variable-select-container">
        <BsLabel label="Select a model" info-text="Charts will be generated with respect to this model" />
        <BsSelect
            :modelValue="store.selectedModelString"
            :all-options="store.modelsString.filter(option => option !== store.selectedModelString2)"
            @update:modelValue="updateModelString"
        />
        <div v-if="store.selectedModelString" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClick">Export Full Model</BsButton>
        </div>
        <BsCheckbox v-if="store.selectedModelString" v-model="store.includeSuspectVariables" label="Include Suspect Variables" />
        
        <BsLabel v-if="store.selectedModelString" label="Select a Variable" info-text="Charts will be generated with respect to this variable" />
        <BsSelect
              v-if="store.selectedModelString"
                  v-model="store.selectedVariable"
                  :all-options="store.variablePoints"
                  @update:modelValue="updateVariable">
                  <template v-slot:selected-item="scope">
                    <q-item v-if="scope.opt">
                      {{ store.selectedVariable.variable }}
                    </q-item>
                </template>
                      <template #option="props">
                          <q-item v-if="props.opt.isInModel || store.includeSuspectVariables" v-bind="props.itemProps" clickable>
                              <q-item-section side>
                                <div v-if="props.opt.isInModel">selected</div>
                                <div v-else>unselected</div>
                              </q-item-section>
                            <q-item-section class="bs-font-medium-2-normal">
                                {{ props.opt.variable }}
                            </q-item-section>
                          </q-item>
                    </template>
              </BsSelect>

        <!-- <BsSelect
            v-if="store.selectedModelString"
            v-model="selectedVariable"
            :all-options="store.variablePoints"
            @update:modelValue="updateVariable">
            </BsSelect> -->
        
        <BsCheckbox v-if="store.selectedModelString" v-model="store.rescale" @update:modelValue="updateRescale" label="Rescale?" />
        
        <BsLabel v-if="store.selectedModelString" label="Run Analysis on" />
        <BsToggle v-if="store.selectedModelString" v-model="store.trainTest" @update:modelValue="updateTrainTest" labelRight="Test" labelLeft="Train" />
        
        <div v-if="store.selectedVariable.variable" class="button-container">
            <BsButton class="bs-primary-button" unelevated dense no-caps padding="4" @click="onClickOneWay">Export One-Way Data</BsButton>
        </div>
    
        <BsLabel v-if="store.selectedModelString" label="Compare with model" info-text="Second model to compare with the first one" />
        <BsSelect
            v-if="store.selectedModelString"
            :modelValue="store.selectedModelString2"
            :all-options="store.modelsString.filter(option => option !== store.selectedModelString)"
            @update:modelValue="updateModelString2"
        />
    </div>
    </template>
    
    <script lang="ts">
    import { defineComponent } from "vue";
    import { useModelStore } from "../stores/webapp";
    import type { VariablePoint } from '../models';
    import { useLoader } from "../composables/use-loader";
    import { useNotification } from "../composables/use-notification";
    
    export default defineComponent({
        emits: ["update:loading"],
        data() {
            return {
                store: useModelStore(),
                loading: false as boolean
            };
        },
        watch: {
          loading(newVal: any) { this.$emit("update:loading", newVal); },
          // selectedVariable(newValue: VariablePoint) {
          //   this.loading = true;
          //   this.store.selectedVariable = newValue;
          //   this.store.updateChartData();
          //   this.loading = false;
          // },
        },
        methods: {
            async updateVariable(value: VariablePoint) {
              this.loading = true;
              this.store.selectedVariable = value;
              await this.store.updateChartData();
              this.loading = false;
            },
            async updateTrainTest(value: boolean) {
              this.loading = true;
              await this.store.updateTrainTest(value);
              this.loading = false;
            },
            async updateRescale(value: boolean) {
                this.loading = true;
              this.store.rescale = value;
              await this.store.updateChartData();
              this.loading = false;
            },
            async updateModelString(value: string) {
                this.loading = true;
                await this.store.updateModelString(value);
              this.loading = false;
            },
            async updateModelString2(value: string) {
                this.loading = true;
                await this.store.updateModelString2(value);
              this.loading = false;
            },
            async onClick() {
                this.loading = true;
                await this.store.exportModel();
              this.loading = false;
            },
            async onClickOneWay() {
                this.loading = true;
                await this.store.exportOneWay();
              this.loading = false;
            },
            notifyError(msg: string) {
                useNotification("negative", msg);
            },
            handleError(msg: any) {
                this.loading = false;
                this.notifyError(msg);
            },
        },
        mounted() {
            this.loading = true;
            this.store.loadModels();
            this.loading = false;
        }
    })
    </script>
    
    <style lang="scss" scoped>
        /* Copy styles from ModelVisualizationDrawer.vue */
        .variable-select-container { padding: 20px; }
        .button-container { margin-top: 12px; }
    </style>