<template>
  <div ref="editorEl" class="lua-editor" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { StreamLanguage } from '@codemirror/language'
import { lua } from '@codemirror/legacy-modes/mode/lua'
import { EditorState } from '@codemirror/state'
import { keymap } from '@codemirror/view'
import { defaultKeymap } from '@codemirror/commands'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const editorEl = ref<HTMLElement | null>(null)
let view: EditorView | null = null

onMounted(() => {
  if (!editorEl.value) return
  view = new EditorView({
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [
        basicSetup,
        StreamLanguage.define(lua),
        keymap.of(defaultKeymap),
        EditorView.updateListener.of(update => {
          if (update.docChanged) {
            emit('update:modelValue', update.state.doc.toString())
          }
        }),
        EditorView.theme({
          '&': { height: '100%', fontSize: '13px' },
          '.cm-scroller': { overflow: 'auto', fontFamily: 'monospace' },
        }),
      ],
    }),
    parent: editorEl.value,
  })
})

watch(() => props.modelValue, (val) => {
  if (!view) return
  const current = view.state.doc.toString()
  if (current !== val) {
    view.dispatch({ changes: { from: 0, to: current.length, insert: val } })
  }
})

onBeforeUnmount(() => view?.destroy())
</script>

<style scoped>
.lua-editor {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}
.lua-editor :deep(.cm-editor) {
  height: 100%;
}
</style>
