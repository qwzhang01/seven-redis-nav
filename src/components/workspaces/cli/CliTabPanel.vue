<template>
  <div class="cli-panel" @click="focusInput">
    <!-- Output area -->
    <div ref="outputRef" class="cli-output">
      <div v-if="tab.outputLines.length === 0" class="cli-welcome">
        <i class="ri-terminal-line" />
        <p>Redis CLI — 输入命令开始</p>
        <p class="cli-hint">↑↓ 历史导航 · ⌘L 清屏 · ⌘T 新建 Tab · ⌘W 关闭 Tab</p>
      </div>

      <div v-for="line in tab.outputLines" :key="line.id" class="cli-line">
        <div class="cli-prompt-line">
          <span class="cli-prompt">{{ line.prompt }}</span>
          <span class="cli-cmd">{{ line.command }}</span>
        </div>
        <div class="cli-result" :class="getOutputClass(line)">
          <pre>{{ line.output }}</pre>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="cli-input-area">
      <span class="cli-prompt-inline">
        {{ connStore.activeConnection?.host ?? '127.0.0.1' }}:{{ connStore.activeConnection?.port ?? 6379 }}[{{ tab.db }}]&gt;
      </span>
      <input
        ref="inputRef"
        v-model="inputValue"
        type="text"
        class="cli-input"
        placeholder="输入 Redis 命令..."
        :disabled="!connStore.isConnected || tab.loading"
        @keydown="handleKeydown"
        @keydown.enter="handleSubmit"
        @click.stop
      />
      <span v-if="tab.loading" class="cli-loading">
        <i class="ri-loader-4-line spin" />
      </span>
    </div>

    <!-- Dangerous command dialog -->
    <Transition name="modal">
      <div v-if="showDangerDialog" class="modal-overlay" @click.self="cancelDanger">
        <div class="modal-card">
          <div class="modal-header">
            <h3><i class="ri-alert-line" style="color: var(--srn-color-warning);" /> 危险命令确认</h3>
          </div>
          <div class="modal-body">
            <p>命令 <code class="danger-cmd">{{ dangerCommand }}</code> 可能导致数据丢失，请输入命令名确认执行：</p>
            <input
              v-model="dangerConfirmInput"
              type="text"
              class="confirm-input"
              :placeholder="`输入 ${dangerCommand} 确认`"
              @keydown.enter="confirmDanger"
            />
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="cancelDanger">取消</button>
            <button
              class="btn-danger"
              :disabled="dangerConfirmInput.toUpperCase() !== dangerCommand.toUpperCase()"
              @click="confirmDanger"
            >确认执行</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useTerminalStore, type CliTabState } from '@/stores/terminal'
import { useConnectionStore } from '@/stores/connection'
import type { IpcError } from '@/types/ipc'

const props = defineProps<{ tab: CliTabState }>()

const termStore = useTerminalStore()
const connStore = useConnectionStore()

const inputRef = ref<HTMLInputElement | null>(null)
const outputRef = ref<HTMLDivElement | null>(null)
const inputValue = ref('')
const historyIndex = ref(-1)

// Dangerous command confirm dialog
const showDangerDialog = ref(false)
const dangerCommand = ref('')
const dangerToken = ref('')
const dangerConfirmInput = ref('')

// Auto-scroll on new output
watch(() => props.tab.outputLines.length, async () => {
  await nextTick()
  if (outputRef.value) outputRef.value.scrollTop = outputRef.value.scrollHeight
})

function focusInput() {
  nextTick(() => inputRef.value?.focus())
}

async function handleSubmit() {
  const cmd = inputValue.value.trim()
  if (!cmd) return
  inputValue.value = ''
  historyIndex.value = -1

  try {
    await termStore.executeInTab(props.tab.tabId, cmd)
  } catch (e) {
    const err = e as IpcError
    if (err.kind === 'dangerous_command') {
      dangerCommand.value = err.command ?? cmd
      dangerToken.value = err.confirm_token ?? ''
      showDangerDialog.value = true
    }
  }
}

async function confirmDanger() {
  if (dangerConfirmInput.value.toUpperCase() !== dangerCommand.value.toUpperCase()) return
  const pendingCmd = dangerCommand.value
  const pendingToken = dangerToken.value
  showDangerDialog.value = false
  dangerConfirmInput.value = ''
  dangerCommand.value = ''
  dangerToken.value = ''
  try {
    await termStore.executeInTab(props.tab.tabId, pendingCmd, pendingToken)
  } catch (e) { console.error(e) }
}

function cancelDanger() {
  showDangerDialog.value = false
  dangerConfirmInput.value = ''
  dangerCommand.value = ''
  dangerToken.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    const h = props.tab.history
    historyIndex.value = Math.min(historyIndex.value + 1, h.length - 1)
    inputValue.value = h[historyIndex.value]?.command ?? ''
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    historyIndex.value = Math.max(historyIndex.value - 1, -1)
    inputValue.value = historyIndex.value === -1 ? '' : (props.tab.history[historyIndex.value]?.command ?? '')
  } else if (e.key === 'l' && (e.metaKey || e.ctrlKey)) {
    e.preventDefault()
    props.tab.outputLines.splice(0)
  }
}

function getOutputClass(line: { isError: boolean; output: string }) {
  if (line.isError) return 'resp-error'
  if (line.output.startsWith('(integer)')) return 'resp-integer'
  if (line.output === 'OK' || line.output === 'PONG') return 'resp-ok'
  return 'resp-string'
}

defineExpose({ focusInput })
</script>

<style scoped>
.cli-panel { display: flex; flex-direction: column; height: 100%; background: #1a1a2e; color: #e0e0e0; font-family: var(--srn-font-mono); cursor: text; }
.cli-output { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.cli-welcome { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--srn-color-text-3); gap: 8px; }
.cli-welcome i { font-size: 48px; }
.cli-welcome p { font-size: 13px; }
.cli-hint { font-size: 11px; color: var(--srn-color-text-3); opacity: 0.7; }
.cli-line { display: flex; flex-direction: column; gap: 4px; }
.cli-prompt-line { display: flex; align-items: center; gap: 8px; }
.cli-prompt { color: #4ade80; font-size: 12px; flex-shrink: 0; }
.cli-cmd { color: #e0e0e0; font-size: 13px; }
.cli-result pre { margin: 0; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; padding-left: 16px; }
.resp-string pre { color: #93c5fd; }
.resp-integer pre { color: #fb923c; }
.resp-error pre { color: #f87171; }
.resp-ok pre { color: #4ade80; }
.cli-input-area { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-top: 1px solid #2a2a4a; background: #16162a; }
.cli-prompt-inline { color: #4ade80; font-size: 12px; flex-shrink: 0; white-space: nowrap; }
.cli-input { flex: 1; background: transparent; border: none; outline: none; color: #e0e0e0; font-size: 13px; font-family: var(--srn-font-mono); caret-color: #4ade80; }
.cli-input::placeholder { color: #444; }
.cli-input:disabled { opacity: 0.5; cursor: not-allowed; }
.cli-loading { color: #666; font-size: 14px; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { width: 400px; background: var(--srn-color-surface-2); border-radius: var(--srn-radius-lg); box-shadow: 0 8px 32px rgba(0,0,0,0.3); border: 1px solid var(--srn-color-border); overflow: hidden; }
.modal-header { padding: 14px 20px; border-bottom: 1px solid var(--srn-color-border); }
.modal-header h3 { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; color: var(--srn-color-text-1); }
.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 10px; font-size: 13px; color: var(--srn-color-text-2); font-family: inherit; }
.danger-cmd { font-family: var(--srn-font-mono); font-size: 13px; color: var(--srn-color-primary); background: rgba(220,56,45,0.08); padding: 2px 6px; border-radius: 3px; }
.confirm-input { width: 100%; height: 32px; border: 1px solid var(--srn-color-border); border-radius: var(--srn-radius-sm); padding: 0 10px; font-size: 13px; font-family: var(--srn-font-mono); background: var(--srn-color-surface-1); color: var(--srn-color-text-1); outline: none; box-sizing: border-box; }
.confirm-input:focus { border-color: var(--srn-color-info); }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid var(--srn-color-border); background: var(--srn-color-surface-1); }
.btn-cancel, .btn-danger { height: 30px; padding: 0 14px; border-radius: var(--srn-radius-sm); font-size: 13px; cursor: pointer; }
.btn-cancel { border: 1px solid var(--srn-color-border); background: transparent; color: var(--srn-color-text-2); }
.btn-danger { border: none; background: var(--srn-color-primary); color: #fff; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.modal-enter-active, .modal-leave-active { transition: all 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
