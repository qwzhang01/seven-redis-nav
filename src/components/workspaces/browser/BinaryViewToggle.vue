<script setup lang="ts">
import { ref, computed, watch } from 'vue';

type ViewMode = 'hex' | 'base64' | 'text';

const props = defineProps<{
  rawData: string;       // base64 encoded raw bytes
  detectedBinary: boolean;
}>();

const emit = defineEmits<{
  (e: 'save', data: string, encoding: 'hex' | 'base64' | 'text'): void;
}>();

const mode = ref<ViewMode>(props.detectedBinary ? 'hex' : 'text');

// Decode base64 to Uint8Array
function decodeBase64(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

// Encode Uint8Array to base64
function encodeBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

const hexView = computed(() => {
  if (!props.rawData) return [];
  const bytes = decodeBase64(props.rawData);
  const lines: { offset: string; hex: string; ascii: string }[] = [];
  for (let i = 0; i < bytes.length; i += 16) {
    const slice = bytes.slice(i, Math.min(i + 16, bytes.length));
    const hex = Array.from(slice).map(b => b.toString(16).padStart(2, '0')).join(' ');
    const ascii = Array.from(slice).map(b => (b >= 32 && b <= 126) ? String.fromCharCode(b) : '.').join('');
    lines.push({
      offset: i.toString(16).padStart(8, '0'),
      hex: hex.padEnd(47, ' '),
      ascii,
    });
  }
  return lines;
});

const base64View = computed(() => {
  return props.rawData || '';
});

const textView = computed(() => {
  if (!props.rawData) return '';
  try {
    const bytes = decodeBase64(props.rawData);
    // Replace non-printable chars with replacement char
    let text = '';
    for (let i = 0; i < bytes.length; i++) {
      if (bytes[i] === 0) {
        text += '\uFFFD';
      } else if (bytes[i] >= 32 && bytes[i] <= 126) {
        text += String.fromCharCode(bytes[i]);
      } else {
        text += String.fromCharCode(bytes[i]);
      }
    }
    return text;
  } catch {
    return '';
  }
});

// Editable hex text
const editableHex = ref('');
const editableBase64 = ref('');
const editableText = ref('');
const isEditing = ref(false);

function startEdit() {
  isEditing.value = true;
  if (mode.value === 'hex') {
    editableHex.value = hexView.value.map(l => `${l.offset}  ${l.hex}  |${l.ascii}|`).join('\n');
  } else if (mode.value === 'base64') {
    editableBase64.value = base64View.value;
  } else {
    editableText.value = textView.value;
  }
}

function cancelEdit() {
  isEditing.value = false;
}

function saveEdit() {
  if (mode.value === 'hex') {
    // Parse hex editor content: extract hex bytes
    const hexBytes: number[] = [];
    for (const line of editableHex.value.split('\n')) {
      // Match hex bytes between offset and ASCII
      const match = line.match(/^\s*[0-9a-fA-F]+\s+(.+?)\s*\|/);
      if (match) {
        const hexStr = match[1].trim();
        for (const byte of hexStr.split(/\s+/)) {
          const val = parseInt(byte, 16);
          if (!isNaN(val) && val >= 0 && val <= 255) {
            hexBytes.push(val);
          }
        }
      }
    }
    const bytes = new Uint8Array(hexBytes);
    emit('save', encodeBase64(bytes), 'hex');
  } else if (mode.value === 'base64') {
    // Try to decode the edited base64
    try {
      atob(editableBase64.value); // validate
      emit('save', editableBase64.value, 'base64');
    } catch {
      // Invalid base64, still send
      emit('save', editableBase64.value, 'base64');
    }
  } else {
    // Text mode: encode to base64
    const bytes = new TextEncoder().encode(editableText.value);
    emit('save', encodeBase64(bytes), 'text');
  }
  isEditing.value = false;
}

watch(() => props.rawData, () => {
  isEditing.value = false;
});
</script>

<template>
  <div class="binary-view">
    <!-- Mode tabs -->
    <div class="bv-tabs">
      <button class="bv-tab" :class="{ active: mode === 'hex' }" @click="mode = 'hex'; isEditing = false">Hex</button>
      <button class="bv-tab" :class="{ active: mode === 'base64' }" @click="mode = 'base64'; isEditing = false">Base64</button>
      <button class="bv-tab" :class="{ active: mode === 'text' }" @click="mode = 'text'; isEditing = false">文本</button>
      <div class="bv-tab-actions">
        <button v-if="!isEditing" class="bv-action-btn" title="编辑" @click="startEdit">
          <i class="ri-edit-line" />
        </button>
        <template v-else>
          <button class="bv-action-btn" title="取消" @click="cancelEdit">
            <i class="ri-close-line" />
          </button>
          <button class="bv-action-btn primary" title="保存" @click="saveEdit">
            <i class="ri-check-line" />
          </button>
        </template>
      </div>
    </div>

    <!-- Content -->
    <div class="bv-content">
      <!-- Hex view -->
      <template v-if="mode === 'hex' && !isEditing">
        <pre class="bv-hex-view"><code v-for="(line, i) in hexView" :key="i"><span class="bv-offset">{{ line.offset }}</span>  <span class="bv-hex">{{ line.hex }}</span>  <span class="bv-ascii">|{{ line.ascii }}|</span></code></pre>
      </template>

      <!-- Base64 view -->
      <template v-else-if="mode === 'base64' && !isEditing">
        <pre class="bv-plain-view">{{ base64View }}</pre>
      </template>

      <!-- Text view -->
      <template v-else-if="mode === 'text' && !isEditing">
        <pre class="bv-plain-view">{{ textView }}</pre>
      </template>

      <!-- Edit mode -->
      <template v-else-if="isEditing">
        <textarea
          v-if="mode === 'hex'"
          v-model="editableHex"
          class="bv-editor"
          spellcheck="false"
        />
        <textarea
          v-else-if="mode === 'base64'"
          v-model="editableBase64"
          class="bv-editor"
          spellcheck="false"
        />
        <textarea
          v-else
          v-model="editableText"
          class="bv-editor"
          spellcheck="false"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.binary-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.bv-tabs {
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  padding: 0 8px;
}
.bv-tab {
  padding: 6px 14px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--srn-color-text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--srn-motion-fast);
}
.bv-tab:hover { color: var(--srn-color-text-1); }
.bv-tab.active { color: var(--srn-color-primary); border-bottom-color: var(--srn-color-primary); }
.bv-tab-actions { margin-left: auto; display: flex; gap: 4px; }
.bv-action-btn {
  border: 1px solid var(--srn-color-border);
  background: transparent;
  color: var(--srn-color-text-2);
  cursor: pointer;
  font-size: 13px;
  padding: 3px 7px;
  border-radius: var(--srn-radius-xs);
  transition: all var(--srn-motion-fast);
}
.bv-action-btn:hover { background: rgba(0,0,0,0.05); }
.bv-action-btn.primary { background: var(--srn-color-primary); color: #fff; border-color: var(--srn-color-primary); }

.bv-content { flex: 1; overflow: auto; padding: 8px 12px; }

.bv-hex-view {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  white-space: pre;
}
.bv-offset { color: var(--srn-color-text-3); }
.bv-hex { color: var(--srn-color-text-1); }
.bv-ascii { color: var(--srn-color-info); }

.bv-plain-view {
  font-family: var(--srn-font-mono);
  font-size: 12px;
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--srn-color-text-1);
}

.bv-editor {
  width: 100%;
  height: 100%;
  border: 1px solid var(--srn-color-info);
  border-radius: var(--srn-radius-sm);
  padding: 8px;
  font-family: var(--srn-font-mono);
  font-size: 12px;
  line-height: 1.5;
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  resize: none;
  outline: none;
  box-sizing: border-box;
}
</style>
