import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { KeyMemoryStat, TtlDistribution, ScanProgress } from '@/ipc/phase4'
import * as ipc from '@/ipc/phase4'

export const useKeyAnalyzerStore = defineStore('keyAnalyzer', () => {
  const isScanning = ref(false)
  const taskId = ref<string | null>(null)
  const progress = ref<ScanProgress | null>(null)
  const topKeys = ref<KeyMemoryStat[]>([])
  const scanAborted = ref(false)

  const ttlDistribution = ref<TtlDistribution | null>(null)
  const isAnalyzingTtl = ref(false)

  async function startScan(connId: string, lowImpact: boolean): Promise<string | null> {
    isScanning.value = true
    scanAborted.value = false
    topKeys.value = []
    progress.value = null

    try {
      taskId.value = await ipc.keyScanMemoryStart(connId, lowImpact)
      return taskId.value
    } catch (e) {
      isScanning.value = false
      throw e
    }
  }

  async function stopScan() {
    if (taskId.value) {
      await ipc.keyScanMemoryStop(taskId.value)
      scanAborted.value = true
    }
    isScanning.value = false
  }

  function onProgress(data: ScanProgress) {
    progress.value = data
    if (data.top_keys) topKeys.value = data.top_keys
    if (data.is_done) isScanning.value = false
  }

  async function analyzeTtl(connId: string) {
    isAnalyzingTtl.value = true
    try {
      ttlDistribution.value = await ipc.keyTtlDistribution(connId)
    } finally {
      isAnalyzingTtl.value = false
    }
  }

  return {
    isScanning, taskId, progress, topKeys, scanAborted,
    ttlDistribution, isAnalyzingTtl,
    startScan, stopScan, onProgress, analyzeTtl,
  }
})
