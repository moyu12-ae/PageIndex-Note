<script setup>
import LLMConfigForm from '@/components/settings/LLMConfigForm.vue'
</script>

<template>
  <div class="settings-view">
    <div class="settings-view__container">
      <h2 class="settings-view__title">⚙️ Settings</h2>
      <LLMConfigForm />
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  padding: var(--space-xl);
  overflow-y: auto;
  height: 100%;
}

.settings-view__container {
  max-width: 600px;
  margin: 0 auto;
}

.settings-view__title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: var(--space-xl);
}
</style>
