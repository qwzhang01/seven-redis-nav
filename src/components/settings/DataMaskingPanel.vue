<template>
  <div class="masking-panel">
    <div class="panel-header">
      <div class="panel-title">数据脱敏规则</div>
      <button class="btn-primary" @click="showAddDialog = true">
        <i class="ri-add-line" /> 添加规则
      </button>
    </div>

    <div class="panel-desc">
      配置 Glob 模式匹配规则，匹配的键值将在 Browser 中显示为掩码。规则按顺序匹配，第一个匹配的规则生效。
    </div>

    <div v-if="store.rules.length === 0" class="empty-tip">
      暂无脱敏规则，点击"添加规则"开始配置
    </div>

    <div v-else class="rules-list">
      <div v-for="rule in store.rules" :key="rule.id" class="rule-item">
        <div class="rule-drag-handle"><i class="ri-drag-move-line" /></div>
        <div class="rule-pattern">
          <code>{{ rule.pattern }}</code>
        </div>
        <div class="rule-mask">
          <span class="mask-preview">{{ rule.mask_char.repeat(6) }}</span>
        </div>
        <div class="rule-actions">
          <label class="toggle-label" :title="rule.enabled ? '已启用' : '已禁用'">
            <input
              type="checkbox"
              :checked="rule.enabled"
              @change="toggleRule(rule)"
            />
          </label>
          <button class="icon-btn danger" title="删除" @click="deleteRule(rule.id)">
            <i class="ri-delete-bin-line" />
          </button>
        </div>
      </div>
    </div>

    <!-- Add Rule Dialog -->
    <div v-if="showAddDialog" class="dialog-overlay" @click.self="showAddDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span>添加脱敏规则</span>
          <button class="close-btn" @click="showAddDialog = false"><i class="ri-close-line" /></button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <label>键名模式 (Glob)</label>
            <input v-model="newPattern" placeholder="例如：*token* 或 user:*:password" class="form-input" />
            <div class="form-hint">支持 * (任意字符) 和 ? (单个字符)</div>
          </div>
          <div class="form-row">
            <label>掩码字符</label>
            <div class="mask-char-options">
              <button
                v-for="c in maskChars"
                :key="c"
                :class="['mask-char-btn', { active: newMaskChar === c }]"
                @click="newMaskChar = c"
              >{{ c.repeat(4) }}</button>
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="showAddDialog = false">取消</button>
          <button class="btn-primary" :disabled="!newPattern.trim()" @click="addRule">添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMaskingStore } from '@/stores/masking'
import type { MaskingRule } from '@/ipc/phase4'
import { v4 as uuidv4 } from 'uuid'

const store = useMaskingStore()
onMounted(() => store.loadRules())

const showAddDialog = ref(false)
const newPattern = ref('')
const newMaskChar = ref('*')
const maskChars = ['*', '#', '●', '×', '-']

async function addRule() {
  if (!newPattern.value.trim()) return
  const rule: MaskingRule = {
    id: uuidv4(),
    pattern: newPattern.value.trim(),
    mask_char: newMaskChar.value,
    enabled: true,
    sort_order: store.rules.length,
  }
  await store.saveRule(rule)
  newPattern.value = ''
  showAddDialog.value = false
}

async function toggleRule(rule: MaskingRule) {
  await store.saveRule({ ...rule, enabled: !rule.enabled })
}

async function deleteRule(id: string) {
  await store.deleteRule(id)
}
</script>

<style scoped>
.masking-panel { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); flex-shrink: 0; }
.panel-title { font-size: 14px; font-weight: 600; }
.panel-desc { padding: 8px 16px; font-size: 12px; color: var(--text-secondary, #6b7280); background: var(--bg-secondary, #f9fafb); border-bottom: 1px solid var(--border-color, #e5e7eb); }
.btn-primary { padding: 5px 12px; background: var(--primary, #ef4444); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 4px; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.empty-tip { padding: 40px; text-align: center; color: var(--text-secondary, #9ca3af); font-size: 13px; }
.rules-list { flex: 1; overflow-y: auto; padding: 8px 16px; display: flex; flex-direction: column; gap: 6px; }
.rule-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 6px; background: #fff; }
.rule-drag-handle { color: var(--text-secondary, #9ca3af); cursor: grab; }
.rule-pattern { flex: 1; }
.rule-pattern code { font-size: 12px; font-family: monospace; background: var(--bg-secondary, #f3f4f6); padding: 2px 6px; border-radius: 3px; }
.rule-mask { width: 80px; }
.mask-preview { font-family: monospace; font-size: 13px; color: #f97316; letter-spacing: 2px; }
.rule-actions { display: flex; align-items: center; gap: 6px; }
.toggle-label { cursor: pointer; }
.icon-btn { background: none; border: none; cursor: pointer; padding: 3px; color: var(--text-secondary, #9ca3af); }
.icon-btn.danger:hover { color: #ef4444; }
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog { background: #fff; border-radius: 8px; width: 440px; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border-color, #e5e7eb); font-weight: 600; font-size: 14px; }
.close-btn { background: none; border: none; cursor: pointer; font-size: 16px; }
.dialog-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: 12px; font-weight: 600; color: var(--text-secondary, #6b7280); }
.form-input { padding: 6px 10px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; font-size: 13px; font-family: monospace; outline: none; }
.form-input:focus { border-color: var(--primary, #ef4444); }
.form-hint { font-size: 11px; color: var(--text-secondary, #9ca3af); }
.mask-char-options { display: flex; gap: 6px; }
.mask-char-btn { padding: 4px 10px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; background: none; cursor: pointer; font-family: monospace; font-size: 13px; }
.mask-char-btn.active { border-color: var(--primary, #ef4444); background: #fef2f2; color: var(--primary, #ef4444); }
.dialog-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border-color, #e5e7eb); }
.btn-cancel { padding: 5px 12px; background: none; border: 1px solid var(--border-color, #e5e7eb); border-radius: 4px; cursor: pointer; font-size: 13px; }
</style>
