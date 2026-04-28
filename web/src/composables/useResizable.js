import { ref, onUnmounted } from 'vue'

/**
 * Composable for drag-based panel resizing.
 *
 * @param {Object} options
 * @param {number} options.defaultSize   - initial size in px
 * @param {number} options.minSize       - minimum size in px (default 180)
 * @param {number} options.maxSize       - maximum size in px (default 900)
 * @param {boolean} options.reverse      - reverse delta (for right-side panels)
 * @param {number} options.collapseSize  - size to collapse to when toggled (default 0)
 */
export function useResizable(options = {}) {
  const {
    defaultSize = 320,
    minSize = 180,
    maxSize = 900,
    reverse = false,
    collapseSize = 0,
  } = options

  const size = ref(defaultSize)
  const isDragging = ref(false)
  const collapsed = ref(false)
  const preCollapseSize = ref(defaultSize)

  function startResize(e) {
    e.preventDefault()
    isDragging.value = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    const startPos = e.clientX
    const startSize = size.value

    function onMouseMove(ev) {
      const delta = reverse
        ? startPos - ev.clientX
        : ev.clientX - startPos
      let newSize = startSize + delta
      newSize = Math.max(minSize, Math.min(maxSize, newSize))
      size.value = newSize
    }

    function onMouseUp() {
      isDragging.value = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }

    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }

  function toggleCollapse() {
    if (collapsed.value) {
      // Expand back to pre-collapse size
      collapsed.value = false
      size.value = preCollapseSize.value
    } else {
      // Collapse
      collapsed.value = true
      preCollapseSize.value = size.value
      size.value = collapseSize
    }
  }

  onUnmounted(() => {
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  })

  return {
    size,
    isDragging,
    collapsed,
    startResize,
    toggleCollapse,
  }
}
