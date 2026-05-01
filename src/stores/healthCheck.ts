import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { HealthReport } from '@/ipc/phase4'
import * as ipc from '@/ipc/phase4'

export const useHealthCheckStore = defineStore('healthCheck', () => {
  const currentReport = ref<HealthReport | null>(null)
  const historyList = ref<HealthReport[]>([])
  const isGenerating = ref(false)
  const isLoadingHistory = ref(false)

  async function generate(connId: string) {
    isGenerating.value = true
    try {
      currentReport.value = await ipc.healthCheckGenerate(connId)
    } finally {
      isGenerating.value = false
    }
  }

  async function loadHistory() {
    isLoadingHistory.value = true
    try {
      historyList.value = await ipc.healthCheckHistoryList()
    } finally {
      isLoadingHistory.value = false
    }
  }

  async function loadHistoryItem(id: string) {
    currentReport.value = await ipc.healthCheckHistoryGet(id)
  }

  async function exportMarkdown(connId: string): Promise<string> {
    if (!currentReport.value) throw new Error('No report to export')
    return ipc.healthCheckExportMarkdown(connId, currentReport.value)
  }

  return {
    currentReport, historyList, isGenerating, isLoadingHistory,
    generate, loadHistory, loadHistoryItem, exportMarkdown,
  }
})
