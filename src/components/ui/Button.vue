<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  icon?: string;
  block?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'medium',
  loading: false,
  disabled: false,
  block: false
});

const emit = defineEmits<{
  click: [e: MouseEvent]
}>();

const isDisabled = computed(() => props.disabled || props.loading);

function handleClick(e: MouseEvent) {
  if (!isDisabled.value) {
    emit('click', e);
  }
}
</script>

<template>
  <button
    type="button"
    :disabled="isDisabled"
    class="ui-button"
    :class="[
      `ui-button--${variant}`,
      `ui-button--${size}`,
      { 'ui-button--block': block },
      { 'ui-button--loading': loading }
    ]"
    @click="handleClick"
  >
    <template v-if="icon">
      <i :class="icon" class="ui-button__icon" />
    </template>
    <slot />
  </button>
</template>

<style scoped>
.ui-button {
  font-family: var(--srn-font-sans);
  font-weight: 500;
  transition: all var(--srn-motion-fast);
}

.ui-button--small {
  font-size: 12px;
  height: 24px;
  padding: 0 12px;
}

.ui-button--medium {
  font-size: 13px;
  height: 28px;
  padding: 0 16px;
}

.ui-button--large {
  font-size: 14px;
  height: 32px;
  padding: 0 20px;
}

.ui-button--block {
  width: 100%;
}

.ui-button__icon {
  margin-right: 4px;
  font-size: 14px;
}

.ui-button--small .ui-button__icon {
  font-size: 12px;
  margin-right: 3px;
}

.ui-button--large .ui-button__icon {
  font-size: 16px;
  margin-right: 6px;
}

/* 自定义主题样式 */
.ui-button--primary {
  background: var(--srn-color-primary);
  border-color: var(--srn-color-primary);
  color: white;
}

.ui-button--primary:hover {
  background: var(--srn-color-primary-hover);
  border-color: var(--srn-color-primary-hover);
}

.ui-button--secondary {
  background: var(--srn-color-surface-2);
  border-color: var(--srn-color-border);
  color: var(--srn-color-text-2);
}

.ui-button--secondary:hover {
  background: var(--srn-color-surface-3);
  border-color: var(--srn-color-border-hover);
}

.ui-button--outline {
  background: transparent;
  border-color: var(--srn-color-primary);
  color: var(--srn-color-primary);
}

.ui-button--outline:hover {
  background: var(--srn-color-primary);
  color: white;
}

.ui-button--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--srn-color-text-2);
}

.ui-button--ghost:hover {
  background: var(--srn-color-surface-2);
  color: var(--srn-color-text-1);
}

.ui-button--danger {
  background: var(--srn-color-error);
  border-color: var(--srn-color-error);
  color: white;
}

.ui-button--danger:hover {
  background: var(--srn-color-error-hover);
  border-color: var(--srn-color-error-hover);
}

/* 禁用状态 */
.ui-button:disabled,
.ui-button.ui-button--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载状态 */
.ui-button--loading {
  pointer-events: none;
}
</style>
