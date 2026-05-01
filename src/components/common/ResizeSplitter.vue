<script setup lang="ts">
/**
 * ResizeSplitter - A vertical draggable splitter between panels.
 *
 * Emits:
 *   resize(delta: number) - fired on each pointermove with px offset from drag start
 *   resize-end()          - fired on pointerup
 *   reset()               - fired on dblclick
 */
import { ref } from 'vue';

const dragging = ref(false);
let startX = 0;

function onPointerDown(e: PointerEvent) {
  dragging.value = true;
  startX = e.clientX;
  (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);

  // Prevent text selection and force col-resize cursor globally
  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';

  emit('resize-start');
}

const emit = defineEmits<{
  'resize-start': [];
  resize: [delta: number];
  'resize-end': [];
  reset: [];
}>();

function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return;
  const delta = e.clientX - startX;
  emit('resize', delta);
}

function onPointerUp() {
  if (!dragging.value) return;
  dragging.value = false;

  // Restore global cursor and text selection
  document.body.style.cursor = '';
  document.body.style.userSelect = '';

  emit('resize-end');
}

function onDblClick() {
  emit('reset');
}
</script>

<template>
  <div
    class="resize-splitter"
    :class="{ active: dragging }"
    @pointerdown.prevent="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @dblclick="onDblClick"
  />
</template>

<style scoped>
.resize-splitter {
  width: 4px;
  cursor: col-resize;
  flex-shrink: 0;
  background: transparent;
  transition: background var(--srn-motion-fast);
  position: relative;
  z-index: 10;
}

.resize-splitter:hover {
  background: rgba(0, 0, 0, 0.08);
}

.resize-splitter.active {
  background: var(--srn-color-info);
}
</style>
