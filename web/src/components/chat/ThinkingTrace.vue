<script setup>
import { ref } from 'vue'

const props = defineProps({
  thinking: { type: String, required: true },
})

const expanded = ref(false)
</script>

<template>
  <div class="thinking-trace">
    <button class="thinking-trace__toggle" @click="expanded = !expanded">
      <span class="thinking-trace__icon">{{ expanded ? '▼' : '▶' }}</span>
      <span class="thinking-trace__label">{{ expanded ? 'Hide reasoning' : 'Show reasoning' }}</span>
    </button>
    <div v-show="expanded" class="thinking-trace__content">
      {{ thinking }}
    </div>
  </div>
</template>

<style scoped>
.thinking-trace {
  margin-bottom: var(--space-sm);
  border-radius: var(--border-radius);
  background: rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.thinking-trace__toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  width: 100%;
  text-align: left;
}

.thinking-trace__toggle:hover {
  color: var(--color-text-secondary);
}

.thinking-trace__icon {
  font-size: 8px;
}

.thinking-trace__label {
  font-style: italic;
}

.thinking-trace__content {
  padding: 0 10px 10px;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
