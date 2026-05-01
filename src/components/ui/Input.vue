<script setup lang="ts">

interface Props {
  modelValue?: string;
  placeholder?: string;
  size?: 'small' | 'medium' | 'large';
  type?: 'text' | 'password' | 'number' | 'email' | 'search';
  disabled?: boolean;
  readonly?: boolean;
  clearable?: boolean;
  prefixIcon?: string;
  suffixIcon?: string;
  status?: 'default' | 'success' | 'warning' | 'error';
  message?: string;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  type: 'text',
  disabled: false,
  readonly: false,
  clearable: false,
  status: 'default'
});

const emit = defineEmits<{
  'update:modelValue': [value: string]
  change: [value: string]
  focus: [e: FocusEvent]
  blur: [e: FocusEvent]
}>();



function handleUpdate(value: string) {
  if (!props.disabled && !props.readonly) {
    emit('update:modelValue', value);
    emit('change', value);
  }
}

function handleFocus(e: FocusEvent) {
  emit('focus', e);
}

function handleBlur(e: FocusEvent) {
  emit('blur', e);
}
</script>

<template>
  <div class="ui-input-wrapper">
    <input
      :value="modelValue"
      :placeholder="placeholder"
      :type="type"
      :disabled="disabled"
      :readonly="readonly"
      class="ui-input"
      :class="[
        `ui-input--${size}`,
        `ui-input--${status}`
      ]"
      @input="handleUpdate(($event.target as HTMLInputElement).value)"
      @focus="handleFocus"
      @blur="handleBlur"
    />

    <div v-if="message" class="ui-input__message" :class="`ui-input__message--${status}`">
      {{ message }}
    </div>
  </div>
</template>

<style scoped>
.ui-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ui-input {
  font-family: var(--srn-font-sans);
  transition: all var(--srn-motion-fast);
}

.ui-input--small {
  font-size: 12px;
}

.ui-input--medium {
  font-size: 13px;
}

.ui-input--large {
  font-size: 14px;
}

/* 自定义状态样式 */
.ui-input--success {
  border-color: var(--srn-color-success);
}

.ui-input--success:focus {
  border-color: var(--srn-color-success);
  box-shadow: 0 0 0 2px rgba(var(--srn-color-success-rgb), 0.1);
}

.ui-input--warning {
  border-color: var(--srn-color-warning);
}

.ui-input--warning:focus {
  border-color: var(--srn-color-warning);
  box-shadow: 0 0 0 2px rgba(var(--srn-color-warning-rgb), 0.1);
}

.ui-input--error {
  border-color: var(--srn-color-error);
}

.ui-input--error:focus {
  border-color: var(--srn-color-error);
  box-shadow: 0 0 0 2px rgba(var(--srn-color-error-rgb), 0.1);
}

.ui-input__message {
  font-size: 11px;
  line-height: 1.4;
  padding: 0 4px;
}

.ui-input__message--success {
  color: var(--srn-color-success);
}

.ui-input__message--warning {
  color: var(--srn-color-warning);
}

.ui-input__message--error {
  color: var(--srn-color-error);
}

/* 禁用状态 */
.ui-input:disabled {
  background-color: var(--srn-color-surface-2);
  color: var(--srn-color-text-3);
  cursor: not-allowed;
}

/* 只读状态 */
.ui-input:readonly {
  background-color: var(--srn-color-surface-1);
  border-color: var(--srn-color-border);
}

/* 聚焦状态 */
.ui-input:focus {
  border-color: var(--srn-color-primary);
  box-shadow: 0 0 0 2px rgba(var(--srn-color-primary-rgb), 0.1);
  outline: none;
}

/* 悬停状态 */
.ui-input:hover:not(:disabled):not(:readonly) {
  border-color: var(--srn-color-primary-hover);
}
</style>
