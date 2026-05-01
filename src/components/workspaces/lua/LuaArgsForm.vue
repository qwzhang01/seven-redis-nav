<template>
  <div class="args-form">
    <div class="args-section">
      <div class="args-label">KEYS</div>
      <div class="args-rows">
        <div v-for="(key, i) in keys" :key="i" class="args-row">
          <span class="arg-index">{{ i + 1 }}</span>
          <input
            :value="key"
            :placeholder="`KEYS[${i + 1}]`"
            class="arg-input"
            @input="$emit('update-key', i, ($event.target as HTMLInputElement).value)"
          />
          <button class="remove-btn" @click="$emit('remove-key', i)"><i class="ri-subtract-line" /></button>
        </div>
        <button class="add-btn" @click="$emit('add-key')"><i class="ri-add-line" /> 添加 KEY</button>
      </div>
    </div>
    <div class="args-section">
      <div class="args-label">ARGV</div>
      <div class="args-rows">
        <div v-for="(arg, i) in argv" :key="i" class="args-row">
          <span class="arg-index">{{ i + 1 }}</span>
          <input
            :value="arg"
            :placeholder="`ARGV[${i + 1}]`"
            class="arg-input"
            @input="$emit('update-argv', i, ($event.target as HTMLInputElement).value)"
          />
          <button class="remove-btn" @click="$emit('remove-argv', i)"><i class="ri-subtract-line" /></button>
        </div>
        <button class="add-btn" @click="$emit('add-argv')"><i class="ri-add-line" /> 添加 ARGV</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ keys: string[]; argv: string[] }>()
defineEmits<{
  'add-key': []
  'remove-key': [i: number]
  'add-argv': []
  'remove-argv': [i: number]
  'update-key': [i: number, v: string]
  'update-argv': [i: number, v: string]
}>()
</script>

<style scoped>
.args-form { display: flex; gap: 0; border-bottom: 1px solid var(--border-color, #e5e7eb); max-height: 120px; overflow-y: auto; }
.args-section { flex: 1; padding: 6px 12px; border-right: 1px solid var(--border-color, #e5e7eb); }
.args-section:last-child { border-right: none; }
.args-label { font-size: 11px; font-weight: 600; color: var(--text-secondary, #6b7280); margin-bottom: 4px; }
.args-rows { display: flex; flex-direction: column; gap: 3px; }
.args-row { display: flex; align-items: center; gap: 4px; }
.arg-index { font-size: 11px; color: var(--text-secondary, #9ca3af); width: 14px; text-align: right; }
.arg-input { flex: 1; font-size: 12px; padding: 2px 6px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 3px; font-family: monospace; }
.remove-btn, .add-btn { background: none; border: none; cursor: pointer; font-size: 11px; color: var(--text-secondary, #9ca3af); padding: 1px 3px; }
.remove-btn:hover { color: var(--danger, #ef4444); }
.add-btn { display: flex; align-items: center; gap: 2px; color: var(--primary, #ef4444); font-size: 11px; margin-top: 2px; }
</style>
