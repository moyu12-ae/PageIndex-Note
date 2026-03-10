<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentsStore } from '@/stores/documents'
import { uploadDocument } from '@/api/documents'

const router = useRouter()
const store = useDocumentsStore()

const isDragging = ref(false)
const uploading = ref(false)
const uploadError = ref('')

function onDragOver(e) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

function onFileSelect(e) {
  const file = e.target?.files?.[0]
  if (file) handleFile(file)
}

async function handleFile(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'md', 'markdown', 'txt', 'json', 'csv', 'docx', 'doc'].includes(ext)) {
    uploadError.value = 'Unsupported format. Supports: PDF, Markdown, TXT, JSON, CSV, Word'
    return
  }

  if (file.size > 50 * 1024 * 1024) {
    uploadError.value = 'File too large (max 50MB)'
    return
  }

  uploading.value = true
  uploadError.value = ''

  try {
    const result = await uploadDocument(file)
    store.addDocument(result)
    router.push(`/doc/${result.document_id}`)
  } catch (e) {
    uploadError.value = e.message || 'Upload failed'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="upload">
    <div
      class="upload__dropzone"
      :class="{ 'upload__dropzone--active': isDragging, 'upload__dropzone--uploading': uploading }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div v-if="uploading" class="upload__loading">
        <div class="upload__spinner"></div>
        <p>Uploading & Processing...</p>
      </div>
      <div v-else class="upload__content">
        <div class="upload__icon">📁</div>
        <h3 class="upload__title">Upload Document</h3>
        <p class="upload__desc">Drag and drop a file here</p>
        <label class="upload__btn">
          Browse Files
          <input type="file" accept=".pdf,.md,.markdown,.txt,.json,.csv,.docx,.doc" hidden @change="onFileSelect" />
        </label>
        <p class="upload__hint">Supports PDF, Markdown, TXT, JSON, CSV, Word • Max 50MB</p>
      </div>
    </div>

    <p v-if="uploadError" class="upload__error">{{ uploadError }}</p>
  </div>
</template>

<style scoped>
.upload {
  width: 100%;
  max-width: 500px;
}

.upload__dropzone {
  border: 2px dashed var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--space-xl) var(--space-lg);
  text-align: center;
  transition: all var(--transition-normal);
  background: var(--color-bg-primary);
}

.upload__dropzone--active {
  border-color: var(--color-accent);
  background: var(--color-accent-light);
}

.upload__dropzone--uploading {
  border-color: var(--color-accent);
}

.upload__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.upload__icon {
  font-size: 48px;
  margin-bottom: var(--space-sm);
}

.upload__title {
  font-size: var(--text-lg);
  font-weight: 600;
}

.upload__desc {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.upload__btn {
  display: inline-block;
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-accent);
  color: white;
  border-radius: var(--border-radius);
  font-weight: 500;
  font-size: var(--text-sm);
  cursor: pointer;
  margin-top: var(--space-sm);
  transition: background var(--transition-fast);
}

.upload__btn:hover {
  background: var(--color-accent-hover);
}

.upload__hint {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-xs);
}

.upload__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
}

.upload__spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.upload__loading p {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

.upload__error {
  color: var(--color-error);
  font-size: var(--text-sm);
  text-align: center;
  margin-top: var(--space-sm);
}
</style>
