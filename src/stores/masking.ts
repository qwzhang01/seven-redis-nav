import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MaskingRule } from '@/ipc/phase4'
import * as ipc from '@/ipc/phase4'

export const useMaskingStore = defineStore('masking', () => {
  const rules = ref<MaskingRule[]>([])
  const isLoaded = ref(false)

  async function loadRules() {
    rules.value = await ipc.maskingRuleList()
    isLoaded.value = true
  }

  async function saveRule(rule: MaskingRule) {
    await ipc.maskingRuleSave(rule)
    await loadRules()
  }

  async function deleteRule(id: string) {
    await ipc.maskingRuleDelete(id)
    rules.value = rules.value.filter(r => r.id !== id)
  }

  async function reorderRules(ids: string[]) {
    await ipc.maskingRuleReorder(ids)
    await loadRules()
  }

  /** Check if a key matches any enabled masking rule. Returns the mask char or null. */
  function getMask(key: string): string | null {
    if (!isLoaded.value) return null
    for (const rule of rules.value) {
      if (!rule.enabled) continue
      if (matchGlob(rule.pattern, key)) return rule.mask_char
    }
    return null
  }

  function isMasked(key: string): boolean {
    return getMask(key) !== null
  }

  return { rules, isLoaded, loadRules, saveRule, deleteRule, reorderRules, getMask, isMasked }
})

/** Simple glob matching: * matches any sequence, ? matches single char */
function matchGlob(pattern: string, str: string): boolean {
  const regexStr = pattern
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*/g, '.*')
    .replace(/\?/g, '.')
  return new RegExp(`^${regexStr}$`).test(str)
}
