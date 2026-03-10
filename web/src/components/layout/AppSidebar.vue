<script setup>
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import DocumentList from '@/components/document/DocumentList.vue'

const router = useRouter()
const documentsStore = useDocumentsStore()
</script>

<template>
  <div class="sidebar">
    <div class="sidebar__header">
      <h1 class="sidebar__title">📄 PageIndex</h1>
      <p class="sidebar__subtitle">Document Intelligence</p>
    </div>

    <button class="sidebar__new-btn" @click="router.push('/')">
      <span class="sidebar__new-icon">＋</span>
      Upload Document
    </button>

    <div class="sidebar__documents">
      <DocumentList />
    </div>

    <div class="sidebar__footer">
      <button class="sidebar__settings-btn" @click="router.push('/settings')">
        ⚙️ Settings
      </button>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
}

.sidebar__header {
  margin-bottom: var(--space-lg);
}

.sidebar__title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

.sidebar__subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.sidebar__new-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: 10px var(--space-md);
  background: var(--color-accent);
  color: white;
  border-radius: var(--border-radius);
  font-weight: 500;
  font-size: var(--text-sm);
  transition: background var(--transition-fast);
  margin-bottom: var(--space-md);
}

.sidebar__new-btn:hover {
  background: var(--color-accent-hover);
}

.sidebar__new-icon {
  font-size: var(--text-lg);
}

.sidebar__documents {
  flex: 1;
  overflow-y: auto;
  margin: 0 calc(var(--space-md) * -1);
  padding: 0 var(--space-md);
}

.sidebar__footer {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.sidebar__settings-btn {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  border-radius: var(--border-radius);
  transition: background var(--transition-fast);
}

.sidebar__settings-btn:hover {
  background: var(--color-bg-tertiary);
}
</style>
