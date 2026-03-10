<script setup>
import DocumentUpload from '@/components/document/DocumentUpload.vue'
</script>

<template>
  <div class="home-view">
    <div class="home-view__hero">
      <h2 class="home-view__title">Welcome to PageIndex</h2>
      <p class="home-view__desc">
        Upload a PDF or Markdown document to generate a hierarchical tree index,
        then ask questions using AI-powered reasoning retrieval.
      </p>
      <DocumentUpload />
    </div>
  </div>
</template>

<style scoped>
.home-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--space-xl);
}

.home-view__hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-md);
}

.home-view__title {
  font-size: 28px;
  font-weight: 700;
}

.home-view__desc {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  max-width: 480px;
  line-height: 1.6;
  margin-bottom: var(--space-md);
}
</style>
