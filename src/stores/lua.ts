import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LuaScript, LuaEvalResult } from '@/ipc/phase4'
import * as ipc from '@/ipc/phase4'

export const useLuaStore = defineStore('lua', () => {
  // Editor state
  const scriptContent = ref<string>(`local key = KEYS[1]\nlocal val = redis.call('GET', key)\nreturn val`)
  const keys = ref<string[]>([''])
  const argv = ref<string[]>([])
  const currentSha = ref<string | null>(null)
  const evalMode = ref<'eval' | 'evalsha'>('eval')

  // Execution state
  const isExecuting = ref(false)
  const lastResult = ref<LuaEvalResult | null>(null)

  // History
  const history = ref<LuaScript[]>([])
  const isLoadingHistory = ref(false)

  // Computed
  const canExecute = computed(() => scriptContent.value.trim().length > 0)

  // Actions
  async function loadHistory() {
    isLoadingHistory.value = true
    try {
      history.value = await ipc.luaHistoryList()
    } finally {
      isLoadingHistory.value = false
    }
  }

  async function execute(connId: string) {
    if (!canExecute.value) return
    isExecuting.value = true
    try {
      const filteredKeys = keys.value.filter(k => k.trim())
      const filteredArgv = argv.value.filter(a => a.trim())

      if (evalMode.value === 'eval') {
        lastResult.value = await ipc.luaEval(connId, scriptContent.value, filteredKeys, filteredArgv)
      } else if (currentSha.value) {
        lastResult.value = await ipc.luaEvalsha(connId, currentSha.value, filteredKeys, filteredArgv)
      }

      // Auto-save to history on success
      if (lastResult.value && !lastResult.value.is_error) {
        await ipc.luaHistorySave(scriptContent.value, '未命名脚本')
        await loadHistory()
      }
    } finally {
      isExecuting.value = false
    }
  }

  async function loadScript(script: LuaScript) {
    scriptContent.value = script.script
    keys.value = ['']
    argv.value = []
    currentSha.value = null
    lastResult.value = null
  }

  async function loadScriptToSha(connId: string) {
    const sha = await ipc.luaScriptLoad(connId, scriptContent.value)
    currentSha.value = sha
    return sha
  }

  async function deleteScript(id: string) {
    await ipc.luaHistoryDelete(id)
    history.value = history.value.filter(s => s.id !== id)
  }

  async function renameScript(id: string, name: string) {
    await ipc.luaHistoryRename(id, name)
    const idx = history.value.findIndex(s => s.id === id)
    if (idx !== -1) history.value[idx].name = name
  }

  function addKey() { keys.value.push('') }
  function removeKey(i: number) { keys.value.splice(i, 1) }
  function addArgv() { argv.value.push('') }
  function removeArgv(i: number) { argv.value.splice(i, 1) }

  return {
    scriptContent, keys, argv, currentSha, evalMode,
    isExecuting, lastResult, history, isLoadingHistory, canExecute,
    loadHistory, execute, loadScript, loadScriptToSha,
    deleteScript, renameScript, addKey, removeKey, addArgv, removeArgv,
  }
})
