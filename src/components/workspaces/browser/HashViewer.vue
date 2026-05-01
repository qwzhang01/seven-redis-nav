<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import type { KeyDetail } from '@/types/data';
import { useDataStore } from '@/stores/data';
import { useDataMasking } from '@/composables/useDataMasking';

const props = defineProps<{ detail: KeyDetail; keyName?: string }>();
const { maskValue, isMasked } = useDataMasking();
const masked = computed(() => props.keyName ? isMasked(props.keyName) : false);
const dataStore = useDataStore();

// 懒加载状态
const isVisible = ref(false);
const observer = ref<IntersectionObserver | null>(null);
const containerRef = ref<HTMLElement | null>(null);

// 判断是否需要懒加载（大于100个字段的哈希）
const needsLazyLoad = ref(false);

onMounted(() => {
  // 检查哈希大小，决定是否需要懒加载
  const value = props.detail.value as any;
  const fieldCount = value?.fields?.length || 0;
  needsLazyLoad.value = fieldCount > 100;

  if (needsLazyLoad.value && containerRef.value) {
    // 设置Intersection Observer
    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            isVisible.value = true;
            observer.value?.disconnect(); // 加载后停止观察
          }
        });
      },
      {
        rootMargin: '200px', // 提前200px开始加载
        threshold: 0.1
      }
    );

    observer.value.observe(containerRef.value);
  } else {
    // 小数据直接显示
    isVisible.value = true;
  }
});

onUnmounted(() => {
  if (observer.value) {
    observer.value.disconnect();
  }
});

// 编辑状态
const editingField = ref<string | null>(null);
const editValue = ref('');

// 计算数据大小
const dataSize = computed(() => {
  const value = props.detail.value as any;
  return JSON.stringify(value).length;
});

// 格式化数据大小显示
const formattedSize = computed(() => {
  const bytes = dataSize.value;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
});

// 字段数量
const fieldCount = computed(() => {
  const value = props.detail.value as any;
  return value?.fields?.length || 0;
});

// 分页显示（懒加载时只显示部分数据）
const displayedFields = computed(() => {
  const value = props.detail.value as any;
  const fields = value?.fields || [];

  if (!isVisible.value) {
    // 懒加载时只显示前10个字段作为预览
    return fields.slice(0, 10);
  }

  return fields;
});

function startEdit(field: string, value: string) {
  editingField.value = field;
  editValue.value = value;
}

async function saveEdit(field: string) {
  const fields = (props.detail.value as any).fields as [string, string][];
  const updated: Record<string, string> = {};
  for (const [f, v] of fields) {
    updated[f] = f === field ? editValue.value : v;
  }
  await dataStore.updateKey(props.detail.key, updated, 'hash');
  editingField.value = null;
}

function cancelEdit() {
  editingField.value = null;
}
</script>

<template>
  <div class="hash-viewer" ref="containerRef">
    <div class="hv-header">
      <div class="hv-label">哈希字段</div>
      <div v-if="needsLazyLoad" class="hv-size-info">
        <span class="size-badge">{{ fieldCount }} 个字段 · {{ formattedSize }}</span>
        <span v-if="!isVisible" class="lazy-loading">
          <i class="ri-loader-4-line spin" /> 加载中...
        </span>
      </div>
    </div>

    <div v-if="!isVisible && needsLazyLoad" class="hv-placeholder">
      <div class="placeholder-content">
        <i class="ri-download-line" />
        <p>大型哈希数据 ({{ fieldCount }} 个字段)</p>
        <p class="placeholder-hint">滚动到可视区域自动加载</p>
        <div class="preview-table">
          <table>
            <thead>
              <tr>
                <th>字段</th>
                <th>值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="[field, value] in displayedFields" :key="field">
                <td class="field-cell">{{ field }}</td>
                <td class="value-cell">{{ masked && keyName ? maskValue(keyName, String(value)) : value }}</td>
              </tr>
            </tbody>
          </table>
          <div class="preview-note">预览前10个字段</div>
        </div>
      </div>
    </div>

    <div v-else class="hv-table-container">
      <table class="hv-table">
        <thead>
          <tr>
            <th>字段</th>
            <th>值</th>
            <th style="width: 60px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="[field, value] in displayedFields"
            :key="field"
          >
            <td class="field-cell">{{ field }}</td>
            <td class="value-cell">
              <template v-if="editingField === field">
                <input
                  v-model="editValue"
                  class="inline-input"
                  @keydown.enter="saveEdit(field)"
                  @keydown.escape="cancelEdit"
                />
              </template>
              <template v-else>
                <span @dblclick="startEdit(field, value)">{{ masked && keyName ? maskValue(keyName, String(value)) : value }}</span>
              </template>
            </td>
            <td class="action-cell">
              <template v-if="editingField === field">
                <button type="button" class="act-btn save" @click="saveEdit(field)">✓</button>
                <button type="button" class="act-btn cancel" @click="cancelEdit">✗</button>
              </template>
              <template v-else>
                <button type="button" class="act-btn edit" @click="startEdit(field, value)">
                  <i class="ri-edit-line" />
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!isVisible" class="lazy-loading-footer">
        <i class="ri-loader-4-line spin" />
        <span>正在加载剩余 {{ fieldCount - displayedFields.length }} 个字段...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hash-viewer {
  overflow: auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.hv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  position: sticky;
  top: 0;
  z-index: 10;
}

.hv-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
}

.hv-size-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--srn-color-text-3);
}

.size-badge {
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-2);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--srn-font-mono);
  font-size: 9px;
}

.lazy-loading {
  color: var(--srn-color-info);
  font-size: 10px;
}

.hv-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-3);
}

.placeholder-content {
  text-align: center;
  padding: 20px;
  max-width: 400px;
}

.placeholder-content i {
  font-size: 24px;
  margin-bottom: 8px;
  color: var(--srn-color-info);
}

.preview-table {
  margin-top: 16px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  overflow: hidden;
}

.preview-table table {
  width: 100%;
  font-size: 10px;
}

.preview-table th {
  background: var(--srn-color-surface-2);
  padding: 4px 8px;
  font-weight: 600;
}

.preview-table td {
  padding: 4px 8px;
  border-top: 1px solid var(--srn-color-border);
}

.preview-note {
  font-size: 9px;
  padding: 4px;
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-3);
  text-align: center;
}

.hv-table-container {
  flex: 1;
  overflow: auto;
}

.hv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.hv-table th {
  padding: 6px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
  border-bottom: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
  position: sticky;
  top: 0;
}

.hv-table td {
  padding: 7px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  vertical-align: middle;
}

.hv-table tr:hover td {
  background: rgba(0,0,0,0.02);
}

.field-cell {
  font-family: var(--srn-font-mono);
  color: var(--srn-color-text-2);
  font-weight: 500;
}

.value-cell {
  font-family: var(--srn-font-mono);
  color: var(--srn-color-text-1);
}

.action-cell {
  text-align: center;
}

.inline-input {
  width: 100%;
  border: 1px solid var(--srn-color-info);
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  font-family: var(--srn-font-mono);
  outline: none;
}

.act-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 3px;
  color: var(--srn-color-text-3);
}

.act-btn:hover {
  background: rgba(0,0,0,0.06);
}

.act-btn.save {
  color: var(--srn-color-success);
}

.act-btn.cancel {
  color: var(--srn-color-primary);
}

.lazy-loading-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: var(--srn-color-info);
  font-size: 11px;
  border-top: 1px solid var(--srn-color-border);
}

.spin {
  animation: spin 1s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
