<script setup>
import { onMounted } from 'vue'
import { useDocumentsStore } from '@/stores/documents'
import { useResizable } from '@/composables/useResizable'
import AppSidebar from './AppSidebar.vue'

const documentsStore = useDocumentsStore()

const { size: sidebarWidth, isDragging, collapsed: sidebarCollapsed, startResize: startSidebarResize, toggleCollapse: toggleSidebar } = useResizable({
  defaultSize: 280,
  minSize: 200,
  maxSize: 500,
  collapseSize: 0,
})

onMounted(() => {
  documentsStore.fetchDocuments()
})
</script>

<template>
  <div class="app-layout">
    <aside
      class="app-layout__sidebar"
      :class="{ 'app-layout__sidebar--collapsed': sidebarCollapsed, 'app-layout__sidebar--dragging': isDragging }"
      :style="{ width: sidebarWidth + 'px' }"
    >
      <div v-show="!sidebarCollapsed" class="app-layout__sidebar-inner">
        <AppSidebar />
      </div>
    </aside>

    <div
      class="app-layout__resize-handle"
      :class="{ 'resize-handle--active': isDragging }"
      @mousedown="startSidebarResize"
    >
      <button
        class="app-layout__collapse-btn"
        :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @mousedown.stop
        @click="toggleSidebar"
      >
        {{ sidebarCollapsed ? '▶' : '◀' }}
      </button>
    </div>

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
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  overflow: hidden;
  transition: width 0.15s ease;
}

.app-layout__sidebar--dragging {
  transition: none;
}

.app-layout__sidebar--collapsed {
  border-right: none;
}

.app-layout__sidebar-inner {
  min-width: 200px;
  height: 100%;
}

.app-layout__resize-handle {
  position: relative;
  width: 6px;
  flex-shrink: 0;
  cursor: col-resize;
  background: transparent;
  transition: background 0.15s ease;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-layout__resize-handle:hover,
.resize-handle--active {
  background: var(--color-accent);
}

.app-layout__collapse-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 18px;
  height: 36px;
  border-radius: 4px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  cursor: pointer;
  font-size: 10px;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.app-layout__resize-handle:hover .app-layout__collapse-btn {
  opacity: 1;
}

.app-layout__main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>
