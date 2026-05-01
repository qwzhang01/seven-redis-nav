<script setup lang="ts">
import { computed } from 'vue';
import type { KeyDetail } from '@/types/data';

interface Props {
  data: KeyDetail;
  editable?: boolean;
  compact?: boolean;
  maxHeight?: string;
}

const props = withDefaults(defineProps<Props>(), {
  editable: false,
  compact: false,
  maxHeight: '400px'
});

const emit = defineEmits<{
  edit: [field: string, value: string]
  delete: [field: string]
}>();

// 格式化显示的数据
const formattedData = computed(() => {
  const value = props.data.value;

  switch (value.type) {
    case 'string':
      return formatString(value.value);

    case 'hash':
      return formatHash(value);

    case 'list':
      return formatList(value);

    case 'set':
      return formatSet(value);

    case 'zset':
      return formatZSet(value);

    default:
      return JSON.stringify(value, null, 2);
  }
});

// 格式化字符串数据
function formatString(value: string) {
  // 检查是否是JSON格式
  try {
    const parsed = JSON.parse(value);
    return JSON.stringify(parsed, null, 2);
  } catch {
    // 不是JSON，直接返回原字符串
    return value;
  }
}

// 格式化哈希数据
function formatHash(value: any) {
  const fields = value.fields || [];
  return fields.map(([field, val]: [string, string]) => {
    return `${field}: ${val}`;
  }).join('\n');
}

// 格式化列表数据
function formatList(value: any) {
  const items = value.items || [];
  return items.map((item: string, index: number) => {
    return `${index}: ${item}`;
  }).join('\n');
}

// 格式化集合数据
function formatSet(value: any) {
  const members = value.members || [];
  return members.map((member: string) => {
    return `• ${member}`;
  }).join('\n');
}

// 格式化有序集合数据
function formatZSet(value: any) {
  const members = value.members || [];
  return members.map(([score, member]: [number, string]) => {
    return `${score}: ${member}`;
  }).join('\n');
}

// 获取数据类型图标
const typeIcon = computed(() => {
  const typeMap: Record<string, string> = {
    string: 'ri-text',
    hash: 'ri-table-2',
    list: 'ri-list-unordered',
    set: 'ri-list-check',
    zset: 'ri-list-ordered',
    stream: 'ri-flow-chart'
  };
  return typeMap[props.data.value.type] || 'ri-question-line';
});

// 获取数据类型颜色
const typeColor = computed(() => {
  const colorMap: Record<string, string> = {
    string: 'var(--srn-color-info)',
    hash: 'var(--srn-color-success)',
    list: 'var(--srn-color-warning)',
    set: 'var(--srn-color-primary)',
    zset: 'var(--srn-color-purple)',
    stream: 'var(--srn-color-cyan)'
  };
  return colorMap[props.data.value.type] || 'var(--srn-color-text-3)';
});

// 数据大小统计
const dataSize = computed(() => {
  const value = props.data.value;
  return JSON.stringify(value).length;
});

const formattedSize = computed(() => {
  const bytes = dataSize.value;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
});


</script>

<template>
  <div class="data-display" :class="{ 'data-display--compact': compact }">
    <div class="data-display__header">
      <div class="data-display__type">
        <i :class="typeIcon" :style="{ color: typeColor }" />
        <span class="type-label">{{ data.value.type.toUpperCase() }}</span>
      </div>
      <div class="data-display__meta">
        <span class="size-badge">{{ formattedSize }}</span>
        <span class="key-name">{{ data.key }}</span>
      </div>
    </div>

    <div class="data-display__content" :style="{ maxHeight: maxHeight }">
      <pre class="data-display__preview">{{ formattedData }}</pre>
    </div>

    <div v-if="editable" class="data-display__actions">
      <button class="action-btn edit" @click="emit('edit', data.key, formattedData)">
        <i class="ri-edit-line" /> 编辑
      </button>
      <button class="action-btn delete" @click="emit('delete', data.key)">
        <i class="ri-delete-bin-line" /> 删除
      </button>
    </div>
  </div>
</template>

<style scoped>
.data-display {
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-md);
  background: var(--srn-color-surface-1);
  overflow: hidden;
}

.data-display--compact {
  font-size: 12px;
}

.data-display__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--srn-color-surface-2);
  border-bottom: 1px solid var(--srn-color-border);
}

.data-display__type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--srn-color-text-2);
}

.type-label {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-display__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--srn-color-text-3);
}

.size-badge {
  background: var(--srn-color-surface-3);
  color: var(--srn-color-text-2);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: var(--srn-font-mono);
}

.key-name {
  font-family: var(--srn-font-mono);
  color: var(--srn-color-text-1);
  font-weight: 500;
}

.data-display__content {
  overflow: auto;
  padding: 12px;
}

.data-display__preview {
  margin: 0;
  font-family: var(--srn-font-mono);
  font-size: 13px;
  line-height: 1.5;
  color: var(--srn-color-text-1);
  white-space: pre-wrap;
  word-break: break-all;
}

.data-display--compact .data-display__preview {
  font-size: 11px;
  line-height: 1.4;
}

.data-display__actions {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--srn-color-border);
  background: var(--srn-color-surface-2);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-2);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--srn-motion-fast);
}

.action-btn:hover {
  background: var(--srn-color-surface-3);
  border-color: var(--srn-color-border-hover);
}

.action-btn.edit:hover {
  color: var(--srn-color-primary);
  border-color: var(--srn-color-primary);
}

.action-btn.delete:hover {
  color: var(--srn-color-error);
  border-color: var(--srn-color-error);
}

/* 滚动条样式 */
.data-display__content::-webkit-scrollbar {
  width: 6px;
}

.data-display__content::-webkit-scrollbar-track {
  background: var(--srn-color-surface-2);
}

.data-display__content::-webkit-scrollbar-thumb {
  background: var(--srn-color-border);
  border-radius: 3px;
}

.data-display__content::-webkit-scrollbar-thumb:hover {
  background: var(--srn-color-border-hover);
}
</style>
