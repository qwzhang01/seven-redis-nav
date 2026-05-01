<script setup lang="ts">
import { ref, watch, onUnmounted, shallowRef, nextTick } from 'vue';

const props = defineProps<{
  value: string;
  size?: number;
}>();

const emit = defineEmits<{
  (e: 'save', value: string): void;
}>();

const isJson = ref(false);
const showEditor = ref(false);
const jsonError = ref<string | null>(null);
const editValue = ref('');
const prettyValue = ref('');
const compactValue = ref('');

// CodeMirror integration
const cmContainer = ref<HTMLElement | null>(null);
const cmView = shallowRef<any | null>(null);
const cmInitialized = ref(false);
const cmLoading = ref(false);

async function initCodeMirror() {
  if (!cmContainer.value || cmInitialized.value) return;
  cmLoading.value = true;

  try {
    // Dynamic imports for CodeMirror 6 — reduces initial bundle by ~150KB
    const [
      { EditorState },
      { EditorView, keymap, lineNumbers, highlightActiveLine },
      { json, jsonParseLinter },
      { defaultKeymap, indentWithTab, history, historyKeymap },
      { searchKeymap, highlightSelectionMatches },
      { linter },
    ] = await Promise.all([
      import('@codemirror/state'),
      import('@codemirror/view'),
      import('@codemirror/lang-json'),
      import('@codemirror/commands'),
      import('@codemirror/search'),
      import('@codemirror/lint'),
    ]);

    cmInitialized.value = true;

    const startState = EditorState.create({
      doc: prettyValue.value || props.value,
      extensions: [
        lineNumbers(),
        highlightActiveLine(),
        history(),
        highlightSelectionMatches(),
        json(),
        linter(jsonParseLinter()),
        keymap.of([
          ...defaultKeymap,
          ...historyKeymap,
          ...searchKeymap,
          indentWithTab,
          {
            key: 'Mod-Enter',
            run: () => {
              validateAndSave();
              return true;
            },
          },
        ]),
        EditorView.theme({
          '&': { fontSize: '12px', height: '100%' },
          '.cm-content': { fontFamily: 'var(--srn-font-mono)', padding: '8px 0' },
          '.cm-gutters': { backgroundColor: 'var(--srn-color-surface-2)', border: 'none', paddingRight: '4px' },
          '.cm-activeLineGutter': { backgroundColor: 'rgba(0,0,0,0.04)' },
        }),
        EditorView.updateListener.of((update: any) => {
          if (update.docChanged) {
            editValue.value = update.state.doc.toString();
            // Clear error on change
            jsonError.value = null;
          }
        }),
      ],
    });

    cmView.value = new EditorView({
      state: startState,
      parent: cmContainer.value,
    });
  } catch (e: any) {
    console.error('CodeMirror init failed:', e);
  } finally {
    cmLoading.value = false;
  }
}

function destroyCodeMirror() {
  if (cmView.value) {
    cmView.value.destroy();
    cmView.value = null;
    cmInitialized.value = false;
  }
}

// Detect JSON
function detectJson(val: string) {
  if (!val || val.length === 0) {
    isJson.value = false;
    return;
  }
  if (val.length <= 1024 * 1024) {
    try {
      JSON.parse(val);
      isJson.value = true;
      prettyValue.value = JSON.stringify(JSON.parse(val), null, 2);
      compactValue.value = JSON.stringify(JSON.parse(val));
      return;
    } catch {
      isJson.value = false;
    }
  } else {
    isJson.value = false;
  }
}

function toggleJson() {
  isJson.value = !isJson.value;
  if (isJson.value) {
    try {
      prettyValue.value = JSON.stringify(JSON.parse(props.value), null, 2);
      compactValue.value = JSON.stringify(JSON.parse(props.value));
    } catch {
      // Keep current value
    }
  }
}

function formatPretty() {
  try {
    const raw = cmView.value ? cmView.value.state.doc.toString() : (editValue.value || props.value);
    const parsed = JSON.parse(raw);
    const formatted = JSON.stringify(parsed, null, 2);
    if (cmView.value) {
      cmView.value.dispatch({
        changes: { from: 0, to: cmView.value.state.doc.length, insert: formatted },
      });
    }
    editValue.value = formatted;
    prettyValue.value = formatted;
    jsonError.value = null;
  } catch (e: any) {
    jsonError.value = `格式化失败：${e.message}`;
  }
}

function formatCompact() {
  try {
    const raw = cmView.value ? cmView.value.state.doc.toString() : (editValue.value || props.value);
    const parsed = JSON.parse(raw);
    const compacted = JSON.stringify(parsed);
    if (cmView.value) {
      cmView.value.dispatch({
        changes: { from: 0, to: cmView.value.state.doc.length, insert: compacted },
      });
    }
    editValue.value = compacted;
    compactValue.value = compacted;
    jsonError.value = null;
  } catch (e: any) {
    jsonError.value = `压缩失败：${e.message}`;
  }
}

function startEdit() {
  showEditor.value = true;
  editValue.value = isJson.value ? prettyValue.value : props.value;
  jsonError.value = null;
  nextTick(() => {
    initCodeMirror();
  });
}

function cancelEdit() {
  showEditor.value = false;
  jsonError.value = null;
  destroyCodeMirror();
}

function validateAndSave() {
  const val = cmView.value ? cmView.value.state.doc.toString() : editValue.value;
  if (isJson.value) {
    try {
      JSON.parse(val);
      jsonError.value = null;
    } catch (e: any) {
      jsonError.value = `JSON 语法错误：${e.message}`;
      return;
    }
  }
  emit('save', val);
  showEditor.value = false;
  destroyCodeMirror();
}

watch(() => props.value, (newVal) => {
  detectJson(newVal);
}, { immediate: true });

onUnmounted(() => {
  destroyCodeMirror();
});
</script>

<template>
  <div class="json-editor-wrapper">
    <!-- JSON mode indicator -->
    <div v-if="isJson && !showEditor" class="je-toolbar">
      <span class="je-badge">JSON</span>
      <button class="je-btn" @click="formatPretty" title="美化"><i class="ri-code-line" /> 美化</button>
      <button class="je-btn" @click="formatCompact" title="压缩"><i class="ri-code-s-slash-line" /> 压缩</button>
      <button class="je-btn primary" @click="startEdit" title="编辑"><i class="ri-edit-line" /> 编辑</button>
    </div>

    <!-- Non-JSON: toggle button -->
    <div v-if="!isJson && !showEditor" class="je-toolbar">
      <button class="je-btn" @click="toggleJson" title="尝试 JSON 模式">
        <i class="ri-braces-line" /> JSON 模式
      </button>
      <button class="je-btn primary" @click="startEdit" title="编辑"><i class="ri-edit-line" /> 编辑</button>
    </div>

    <!-- View mode -->
    <div v-if="!showEditor" class="je-content">
      <pre v-if="isJson" class="je-pretty">{{ prettyValue }}</pre>
      <pre v-else class="je-plain">{{ value }}</pre>
    </div>

    <!-- Edit mode with CodeMirror -->
    <div v-else class="je-edit-area">
      <div v-if="cmLoading" class="je-loading">
        <i class="ri-loader-4-line ri-spin" /> 加载编辑器…
      </div>
      <div v-if="jsonError" class="je-error">
        <i class="ri-error-warning-line" /> {{ jsonError }}
      </div>
      <div ref="cmContainer" class="je-cm-container" />
      <div class="je-edit-actions">
        <span class="je-hint">⌘+Enter 保存</span>
        <button class="je-btn" @click="cancelEdit">取消</button>
        <button class="je-btn primary" :disabled="!!jsonError" @click="validateAndSave">保存</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.json-editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.je-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.je-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--srn-type-hash-bg);
  color: var(--srn-type-hash-text);
}
.je-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: var(--srn-radius-xs);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all var(--srn-motion-fast);
}
.je-btn:hover { background: rgba(0,0,0,0.05); }
.je-btn.primary { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }
.je-btn.primary:hover { opacity: 0.9; }

.je-content { flex: 1; overflow: auto; }
.je-pretty {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--srn-color-text-1);
}
.je-plain {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--srn-color-text-1);
}

.je-edit-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.je-loading {
  padding: 8px 12px;
  font-size: 12px;
  color: var(--srn-color-text-3);
  display: flex;
  align-items: center;
  gap: 6px;
}
.je-error {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--srn-color-primary);
  background: rgba(220, 38, 38, 0.06);
  border-bottom: 1px solid rgba(220, 38, 38, 0.2);
  display: flex;
  align-items: center;
  gap: 6px;
}
.je-cm-container {
  flex: 1;
  overflow: hidden;
}
.je-cm-container :deep(.cm-editor) {
  height: 100%;
}
.je-cm-container :deep(.cm-scroller) {
  overflow: auto;
  font-family: var(--srn-font-mono);
}

.je-edit-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}
.je-hint { font-size: 11px; color: var(--srn-color-text-3); margin-right: auto; }
</style>
