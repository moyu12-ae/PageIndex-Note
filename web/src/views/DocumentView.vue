<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import TreeViewer from '@/components/tree/TreeViewer.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'

const route = useRoute()
const store = useDocumentsStore()

const documentId = computed(() => route.params.id)
const loading = ref(true)
const error = ref('')
const processingStatus = ref('')
const processingMessage = ref('')

async function loadDocument() {
  loading.value = true
  error.value = ''

  try {
    // Check if document is still processing
    const docMeta = store.documents.find(d => d.document_id === documentId.value)

    if (docMeta?.status === 'processing') {
      processingStatus.value = 'processing'
      // Connect to SSE for progress
      pollProgress()
      return
    }

    // Fetch tree
    await store.fetchTree(documentId.value)
    processingStatus.value = 'completed'
  } catch (e) {
    error.value = e.message || 'Failed to load document'
  } finally {
    loading.value = false
  }
}

async function pollProgress() {
  try {
    const response = await fetch(`/api/documents/${documentId.value}/progress`)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop()

      for (const part of parts) {
        if (!part.trim()) continue
        const dataLine = part.split('\n').find(l => l.startsWith('data: '))
        if (!dataLine) continue

        try {
          const data = JSON.parse(dataLine.slice(6))
          processingMessage.value = data.message || data.stage || ''

          if (data.status === 'completed') {
            processingStatus.value = 'completed'
            store.updateDocumentStatus(documentId.value, 'completed')
            store.fetchDocuments()
            await store.fetchTree(documentId.value)
            loading.value = false
            return
          }
          if (data.status === 'failed') {
            error.value = data.message || 'Processing failed'
            processingStatus.value = 'failed'
            loading.value = false
            return
          }
        } catch {}
      }
    }
  } catch (e) {
    // If SSE fails, try fetching tree directly (maybe already done)
    try {
      await store.fetchTree(documentId.value)
      processingStatus.value = 'completed'
      loading.value = false
    } catch {
      error.value = 'Failed to connect to processing stream'
      loading.value = false
    }
  }
}

onMounted(loadDocument)
watch(documentId, loadDocument)
</script>

<template>
  <div class="doc-view">
    <!-- Loading / Processing -->
    <div v-if="loading || processingStatus === 'processing'" class="doc-view__loading">
      <div class="doc-view__spinner"></div>
      <h3>Processing Document...</h3>
      <p>{{ processingMessage || 'Analyzing document structure with AI...' }}</p>
      <p class="doc-view__hint">This may take 1-3 minutes depending on document size.</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="doc-view__error">
      <p>❌ {{ error }}</p>
      <button @click="loadDocument">Retry</button>
    </div>

    <!-- Document loaded -->
    <div v-else-if="store.activeTree" class="doc-view__content">
      <div class="doc-view__tree">
        <TreeViewer :tree="store.activeTree" :document-id="documentId" />
      </div>
      <div class="doc-view__chat">
        <ChatPanel :document-id="documentId" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.doc-view__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-md);
  color: var(--color-text-secondary);
}

.doc-view__spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.doc-view__loading h3 {
  font-size: var(--text-lg);
  color: var(--color-text-primary);
}

.doc-view__hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.doc-view__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-md);
}

.doc-view__error p {
  color: var(--color-error);
  font-size: var(--text-base);
}

.doc-view__error button {
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-accent);
  color: white;
  border-radius: var(--border-radius);
  font-size: var(--text-sm);
}

.doc-view__content {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.doc-view__tree {
  flex: 1;
  overflow: hidden;
}

.doc-view__chat {
  width: 420px;
  flex-shrink: 0;
}

@media (max-width: 1024px) {
  .doc-view__content {
    flex-direction: column;
  }
  .doc-view__chat {
    width: 100%;
    height: 50%;
    border-left: none;
    border-top: 1px solid var(--color-border);
  }
}
</style>
