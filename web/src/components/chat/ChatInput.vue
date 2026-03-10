<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['send'])

const text = ref('')
const textarea = ref(null)

function handleSend() {
  const q = text.value.trim()
  if (!q || props.disabled) return
  emit('send', q)
  text.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input">
    <div class="chat-input__wrapper">
      <textarea
        ref="textarea"
        v-model="text"
        class="chat-input__textarea"
        :placeholder="disabled ? 'Processing...' : 'Ask a question about this document...'"
        :disabled="disabled"
        rows="1"
        @keydown="handleKeydown"
      ></textarea>
      <button
        class="chat-input__send"
        :disabled="!text.trim() || disabled"
        @click="handleSend"
      >
        ➤
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input {
  padding: var(--space-sm) var(--space-md);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-primary);
}

.chat-input__wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--space-sm);
  transition: border-color var(--transition-fast);
  background: var(--color-bg-primary);
}

.chat-input__wrapper:focus-within {
  border-color: var(--color-accent);
}

.chat-input__textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: var(--text-sm);
  line-height: 1.5;
  max-height: 100px;
  min-height: 24px;
  padding: 2px 4px;
  background: transparent;
}

.chat-input__textarea:disabled {
  opacity: 0.5;
}

.chat-input__send {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  color: white;
  border-radius: 50%;
  font-size: var(--text-sm);
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.chat-input__send:disabled {
  background: var(--color-border);
  cursor: not-allowed;
}

.chat-input__send:not(:disabled):hover {
  background: var(--color-accent-hover);
}
</style>
