<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import AppSidebar from './AppSidebar.vue'

const documentsStore = useDocumentsStore()

onMounted(() => {
  documentsStore.fetchDocuments()
})
</script>

<template>
  <div class="app-layout">
    <AppSidebar class="app-layout__sidebar" />
    <main class="app-layout__main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-layout__sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.app-layout__main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
