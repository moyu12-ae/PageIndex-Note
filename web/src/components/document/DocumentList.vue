<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'

const router = useRouter()
const route = useRoute()
const store = useDocumentsStore()

const activeDocId = computed(() => route.params.id)

function selectDoc(docId) {
  router.push(`/doc/${docId}`)
}

async function deleteDoc(docId) {
  if (confirm('Delete this document and its tree?')) {
    await store.removeDocument(docId)
    if (activeDocId.value === docId) {
      router.push('/')
    }
  }
}

function getStatusDot(status) {
  const colors = { completed: '#10b981', processing: '#f59e0b', failed: '#ef4444' }
  return colors[status] || '#9ca3af'
}

function getFileIcon(type) {
  const icons = {
    pdf: '📕',
    markdown: '📝',
    text: '📄',
    json: '📋',
    csv: '📊',
    word: '📘',
  }
  return icons[type] || '📄'
}
</script>

<template>
  <div class="doc-list">
    <div class="doc-list__label">Documents</div>

    <div v-if="store.documents.length === 0" class="doc-list__empty">
      No documents yet.<br>Upload one to get started.
    </div>

    <div
      v-for="doc in store.documents"
      :key="doc.document_id"
      class="doc-item"
      :class="{ 'doc-item--active': doc.document_id === activeDocId }"
      @click="selectDoc(doc.document_id)"
    >
      <span class="doc-item__icon">{{ getFileIcon(doc.file_type) }}</span>
      <div class="doc-item__info">
        <div class="doc-item__name" :title="doc.filename">{{ doc.filename }}</div>
        <div class="doc-item__meta">
          <span class="doc-item__status-dot" :style="{ background: getStatusDot(doc.status) }"></span>
          {{ doc.status }}
        </div>
      </div>
      <button class="doc-item__delete" @click.stop="deleteDoc(doc.document_id)" title="Delete">✕</button>
    </div>
  </div>
</template>

<style scoped>
.doc-list__label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
}

.doc-list__empty {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-lg) 0;
  line-height: 1.6;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-sm);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background var(--transition-fast);
  position: relative;
}

.doc-item:hover {
  background: var(--color-bg-tertiary);
}

.doc-item--active {
  background: var(--color-accent-light);
}

.doc-item__icon {
  font-size: var(--text-lg);
  flex-shrink: 0;
}

.doc-item__info {
  flex: 1;
  min-width: 0;
}

.doc-item__name {
  font-size: var(--text-sm);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-item__meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}

.doc-item__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.doc-item__delete {
  opacity: 0;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding: 4px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.doc-item:hover .doc-item__delete {
  opacity: 1;
}

.doc-item__delete:hover {
  color: var(--color-error);
  background: rgba(239, 68, 68, 0.1);
}
</style>
