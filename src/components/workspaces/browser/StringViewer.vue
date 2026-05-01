<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { KeyDetail } from '@/types/data';
import JsonEditor from './JsonEditor.vue';
import BinaryViewToggle from './BinaryViewToggle.vue';
import { useDataMasking } from '@/composables/useDataMasking';

const props = defineProps<{ detail: KeyDetail; keyName?: string }>();

const { maskValue, isMasked } = useDataMasking();
const masked = computed(() => props.keyName ? isMasked(props.keyName) : false);

// 懒加载状态
const isVisible = ref(false);
const observer = ref<IntersectionObserver | null>(null);
const containerRef = ref<HTMLElement | null>(null);

// 判断是否需要懒加载（大于10KB的数据）
const needsLazyLoad = ref(false);

// View mode: 'auto' | 'json' | 'binary'
const viewMode = ref<'auto' | 'json' | 'binary'>('auto');

// JSON detection
const isJson = computed(() => {
  if (viewMode.value !== 'auto') return false;
  const str = extractStringValue(props.detail.value);
  if (str.length > 1024 * 1024) return false; // > 1MB skip auto-detect
  try {
    const parsed = JSON.parse(str);
    return typeof parsed === 'object' && parsed !== null;
  } catch {
    return false;
  }
});

// Binary detection (contains null bytes or >30% non-printable)
const isBinary = computed(() => {
  if (viewMode.value !== 'auto') return false;
  const str = extractStringValue(props.detail.value);
  if (str.length === 0) return false;
  let nonPrintable = 0;
  for (let i = 0; i < Math.min(str.length, 512); i++) {
    const code = str.charCodeAt(i);
    if (code === 0 || (code < 32 && code !== 9 && code !== 10 && code !== 13)) {
      nonPrintable++;
    }
  }
  return nonPrintable / Math.min(str.length, 512) > 0.3;
});

// Effective view mode
const effectiveMode = computed(() => {
  if (viewMode.value !== 'auto') return viewMode.value;
  if (isJson.value) return 'json';
  if (isBinary.value) return 'binary';
  return 'auto';
});

// Encode string to base64 for BinaryViewToggle
const valueBase64 = computed(() => {
  const str = extractStringValue(props.detail.value);
  // Encode to UTF-8 then base64
  const bytes = new TextEncoder().encode(str);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
});

// 提取实际字符串值（兼容 { value: string } 包装格式和纯字符串格式）
function extractStringValue(raw: any): string {
  if (typeof raw === 'string') return raw;
  if (raw && typeof raw === 'object' && typeof raw.value === 'string') return raw.value;
  return JSON.stringify(raw, null, 2);
}

// 在 setup 阶段同步计算是否需要懒加载，并初始化 isVisible
{
  const strValue = extractStringValue(props.detail.value);
  needsLazyLoad.value = strValue.length > 10240;
  if (!needsLazyLoad.value) {
    isVisible.value = true;
  }
}

onMounted(() => {
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
    // 小数据直接显示（兜底，正常情况下 setup 阶段已设置）
    isVisible.value = true;
  }
});

onUnmounted(() => {
  if (observer.value) {
    observer.value.disconnect();
  }
});

// 计算数据大小
const dataSize = computed(() => {
  return extractStringValue(props.detail.value).length;
});

// 格式化数据大小显示
const formattedSize = computed(() => {
  const bytes = dataSize.value;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
});

// 截断显示的数据（避免DOM渲染过大的文本）
const truncatedValue = computed(() => {
  if (!isVisible.value) return '';

  const strValue = extractStringValue(props.detail.value);

  // Apply masking if rule matches
  if (masked.value && props.keyName) {
    return maskValue(props.keyName, strValue);
  }

  // 如果数据太大，只显示前100KB
  if (strValue.length > 102400) {
    return strValue.substring(0, 102400) + '\n\n... (数据过大，已截断显示)';
  }

  return strValue;
});
</script>

<template>
  <div class="string-viewer" ref="containerRef">
    <div class="sv-header">
      <div class="sv-label">
        值
        <span v-if="masked" class="mask-badge">🔒 已脱敏</span>
      </div>
      <div class="sv-mode-toggle">
        <button
          v-for="m in (['auto', 'json', 'binary'] as const)"
          :key="m"
          class="sv-mode-btn"
          :class="{ active: viewMode === m }"
          @click="viewMode = m"
        >
          {{ m === 'auto' ? '自动' : m === 'json' ? 'JSON' : '二进制' }}
        </button>
      </div>
      <div v-if="needsLazyLoad" class="sv-size-info">
        <span class="size-badge">{{ formattedSize }}</span>
        <span v-if="!isVisible" class="lazy-loading">
          <i class="ri-loader-4-line spin" /> 加载中...
        </span>
      </div>
    </div>

    <div v-if="!isVisible && needsLazyLoad" class="sv-placeholder">
      <div class="placeholder-content">
        <i class="ri-download-line" />
        <p>大型数据内容 ({{ formattedSize }})</p>
        <p class="placeholder-hint">滚动到可视区域自动加载</p>
      </div>
    </div>

    <!-- JSON mode -->
    <JsonEditor
      v-else-if="effectiveMode === 'json'"
      :value="extractStringValue(props.detail.value)"
      :size="dataSize"
    />

    <!-- Binary mode -->
    <BinaryViewToggle
      v-else-if="effectiveMode === 'binary'"
      :raw-data="valueBase64"
      :detected-binary="true"
    />

    <!-- Auto/Plain text mode -->
    <textarea
      v-else
      class="sv-textarea"
      :value="truncatedValue"
      readonly
    />
  </div>
</template>

<style scoped>
.string-viewer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.sv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sv-mode-toggle {
  display: flex;
  gap: 2px;
  background: var(--srn-color-surface-2);
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 1px;
}
.sv-mode-btn {
  padding: 2px 8px;
  border: none;
  background: transparent;
  color: var(--srn-color-text-3);
  font-size: 10px;
  cursor: pointer;
  border-radius: 3px;
  transition: all var(--srn-motion-fast);
}
.sv-mode-btn:hover { color: var(--srn-color-text-1); }
.sv-mode-btn.active { background: var(--srn-color-primary); color: #fff; }

.sv-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--srn-color-text-3);
  text-transform: uppercase;
}

.sv-size-info {
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

.sv-placeholder {
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
}

.placeholder-content i {
  font-size: 24px;
  margin-bottom: 8px;
  color: var(--srn-color-info);
}

.placeholder-hint {
  font-size: 9px;
  margin-top: 4px;
  opacity: 0.7;
}

.sv-textarea {
  flex: 1;
  border: 1px solid var(--srn-color-border);
  border-radius: var(--srn-radius-sm);
  padding: 10px;
  font-size: 13px;
  font-family: var(--srn-font-mono);
  background: var(--srn-color-surface-1);
  color: var(--srn-color-text-1);
  resize: none;
  outline: none;
  line-height: 1.6;
}

.mask-badge { font-size: 10px; color: #f97316; background: #fff7ed; padding: 1px 5px; border-radius: 8px; margin-left: 4px; }
.spin { animation: spin 1s linear infinite; }

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
