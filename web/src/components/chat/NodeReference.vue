<script setup>
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  nodeId: { type: String, required: true },
})

const chatStore = useChatStore()

function handleClick() {
  chatStore.highlightedNodes = new Set([props.nodeId])
  // Scroll to the node in the tree viewer
  setTimeout(() => {
    const el = document.querySelector(`[data-node-id="${props.nodeId}"]`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 100)
}
</script>

<template>
  <button class="node-ref" @click="handleClick" :title="`Node ${nodeId}`">
    📎 {{ nodeId }}
  </button>
</template>

<style scoped>
.node-ref {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  font-size: 11px;
  font-family: var(--font-mono);
  background: var(--color-accent-light);
  color: var(--color-accent);
  border: 1px solid var(--color-accent);
  border-radius: var(--border-radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.node-ref:hover {
  background: var(--color-accent);
  color: white;
}
</style>
