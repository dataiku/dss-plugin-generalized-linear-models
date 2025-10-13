<template>
    <BsDocumentation>
        <template #title>
            <img :src="docLogo" style="margin-right: 12px;"/>
            Visual GLM
        </template>

        <template #content>
            <div class="bs-font-medium-3-normal">
                <p>
                    Visual GLM lets you design your Generalized Linear Model visually 
                    and explore Model performance and interpretation. <br />
                    Create a first model by selecting the variables that you want to include,
                    the distribution and the link function. <br />
                    Then visualize the results in the second tab, including
                    One-Way Variable Analysis, Variable Level Stats and Lift Charts. 
                </p>
                <p>
                    When you are satisfied with a model, you can export it in a standard format
                    with the relativities of each of your modalities.
                </p>
            </div>
        </template>
    </BsDocumentation>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import docLogo from "../assets/images/doc-logo-example.svg";

export default defineComponent({
    data() {
        return {
            docLogo,
        }
    }
})
</script>
