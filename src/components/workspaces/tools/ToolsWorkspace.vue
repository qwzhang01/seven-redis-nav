<template>
  <div class="tools-workspace">
    <!-- Sub-tab navigation -->
    <div class="tools-tabs">
      <button
        v-for="tab in subTabs"
        :key="tab.id"
        :class="['tools-tab', { active: activeSubTab === tab.id }]"
        @click="activeSubTab = tab.id"
      >
        <i :class="tab.icon" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Sub-tab content -->
    <div class="tools-content">
      <KeyScanPanel v-if="activeSubTab === 'key-scan'" />
      <TtlDistributionPanel v-else-if="activeSubTab === 'ttl'" />
      <HealthCheckPanel v-else-if="activeSubTab === 'health'" />
      <ImportExportPanel v-else-if="activeSubTab === 'import-export'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import KeyScanPanel from './KeyScanPanel.vue'
import TtlDistributionPanel from './TtlDistributionPanel.vue'
import HealthCheckPanel from './HealthCheckPanel.vue'
import ImportExportPanel from './ImportExportPanel.vue'

const activeSubTab = ref('key-scan')

const subTabs = [
  { id: 'key-scan', label: '大 Key 扫描', icon: 'ri-search-eye-line' },
  { id: 'ttl', label: 'TTL 分析', icon: 'ri-time-line' },
  { id: 'health', label: '健康检查', icon: 'ri-heart-pulse-line' },
  { id: 'import-export', label: '导入导出', icon: 'ri-exchange-line' },
]
</script>

<style scoped>
.tools-workspace { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.tools-tabs { display: flex; border-bottom: 1px solid var(--border-color, #e5e7eb); padding: 0 12px; gap: 0; flex-shrink: 0; }
.tools-tab { display: flex; align-items: center; gap: 5px; padding: 8px 14px; font-size: 13px; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; color: var(--text-secondary, #6b7280); white-space: nowrap; }
.tools-tab.active { color: var(--primary, #ef4444); border-bottom-color: var(--primary, #ef4444); }
.tools-tab:hover:not(.active) { color: var(--text-primary, #111827); }
.tools-content { flex: 1; overflow: hidden; }
</style>
