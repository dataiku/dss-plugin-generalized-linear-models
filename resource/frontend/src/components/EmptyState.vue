<template>
  <div class="bs-empty-state">
    <img src="../assets/images/empty-state.svg" alt="Empty State Image" class="image">
    <h1 class="bs-header">{{ title }}</h1>
    <p class="bs-text">{{ subtitle }}</p>
  </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  props:{
    title: {
      type: String,
      required: true
    },
    subtitle: {
      type: String,
      required: true
    },
  }
})
</script>
<style>
.bs-empty-state {
  padding-top: 10%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.bs-header {
  color: #666;
  font-size: 24px;
  font-style: normal;
  font-weight: 600;
  line-height: 40px;
}

.bs-text {
  color: #666;
  font-size: 20px;
  font-style: normal;
  font-weight: 400;
  line-height: 32px;
}
</style>
