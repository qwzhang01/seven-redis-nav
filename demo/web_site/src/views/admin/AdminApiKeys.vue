<template>
  <div class="pt-8 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-extrabold text-white mb-2">API密钥审核</h1>
        <p class="text-dark-100">审核用户提交的API密钥申请</p>
      </div>

      <!-- Filter Tabs -->
      <div class="glass-card p-1.5 mb-6 inline-flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
          :class="activeTab === tab.value ? 'bg-primary-500/15 text-primary-400' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- API Keys List -->
      <div class="space-y-4">
        <div
          v-for="apiKey in filteredApiKeys"
          :key="apiKey.id"
          class="glass-card-hover p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
                <Key :size="20" class="text-primary-400" />
              </div>
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <h3 class="text-white font-semibold">{{ apiKey.label }}</h3>
                  <span class="text-xs px-2 py-0.5 rounded bg-dark-600 text-dark-100">{{ apiKey.exchange }}</span>
                  <span
                    class="text-xs px-2 py-0.5 rounded font-medium"
                    :class="getStatusClass(apiKey.reviewStatus)"
                  >
                    {{ getStatusText(apiKey.reviewStatus) }}
                  </span>
                </div>
                <div class="text-sm text-dark-100">
                  <span>用户: {{ apiKey.userName }}</span>
                  <span class="mx-2">•</span>
                  <span>提交时间: {{ formatDate(apiKey.createdAt) }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="apiKey.reviewStatus === 'pending'"
                @click="showReviewDialog(apiKey)"
                class="btn-primary !py-2 !px-4 text-sm"
              >
                审核
              </button>
              <button
                @click="showDetail(apiKey)"
                class="btn-secondary !py-2 !px-4 text-sm"
              >
                详情
              </button>
            </div>
          </div>

          <!-- API Key Info (masked) -->
          <div class="bg-dark-800/50 rounded-lg p-4 mb-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-dark-100">API Key:</span>
                <div class="font-mono text-white mt-1">{{ maskApiKey(apiKey.apiKey) }}</div>
              </div>
              <div>
                <span class="text-dark-100">状态:</span>
                <div class="mt-1">
                  <StatusDot :status="apiKey.status" />
                  <span class="ml-2 text-white">{{ apiKey.status === 'active' ? '已激活' : '已禁用' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Review Info -->
          <div v-if="apiKey.reviewStatus !== 'pending'" class="bg-dark-800/30 rounded-lg p-4">
            <div class="text-sm">
              <div class="flex items-center gap-4">
                <span class="text-dark-100">审核结果:</span>
                <span :class="getStatusColor(apiKey.reviewStatus)" class="font-medium">
                  {{ getStatusText(apiKey.reviewStatus) }}
                </span>
                <span class="text-dark-100">审核人: {{ apiKey.reviewedBy || '系统' }}</span>
                <span class="text-dark-100">审核时间: {{ formatDate(apiKey.reviewedAt) }}</span>
              </div>
              <div v-if="apiKey.reviewReason" class="mt-2">
                <span class="text-dark-100">审核原因:</span>
                <p class="text-white mt-1">{{ apiKey.reviewReason }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="filteredApiKeys.length === 0" class="text-center py-12 text-dark-100">
          <Key :size="48" class="mx-auto mb-4 text-dark-300" />
          <p>暂无API密钥申请</p>
        </div>
      </div>
    </div>

    <!-- Review Dialog -->
    <div v-if="reviewDialog.show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="glass-card max-w-md w-full mx-4 p-6">
        <h3 class="text-white font-bold mb-4">审核API密钥</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-dark-100 mb-2">审核结果</label>
            <div class="flex gap-2">
              <button
                @click="reviewDialog.result = 'approved'"
                class="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all"
                :class="reviewDialog.result === 'approved' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-dark-600 text-dark-100 hover:text-white'"
              >
                通过
              </button>
              <button
                @click="reviewDialog.result = 'rejected'"
                class="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all"
                :class="reviewDialog.result === 'rejected' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-dark-600 text-dark-100 hover:text-white'"
              >
                拒绝
              </button>
            </div>
          </div>
          <div>
            <label class="block text-sm text-dark-100 mb-2">审核原因</label>
            <textarea
              v-model="reviewDialog.reason"
              placeholder="请输入审核原因（可选）"
              class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
              rows="3"
            ></textarea>
          </div>
          <div class="flex gap-3 pt-2">
            <button @click="closeReviewDialog" class="btn-secondary flex-1">取消</button>
            <button @click="submitReview" class="btn-primary flex-1">提交审核</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Key } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import type { ApiKey } from '@/types'

const activeTab = ref('pending')

const tabs = [
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' },
]

// Mock data for API keys
const apiKeys: ApiKey[] = [
  {
    id: '1',
    exchange: 'Binance',
    label: '主交易账户',
    apiKey: 'aBc123dEf456gHi789jKl012mNo345pQr678',
    createdAt: '2025-02-10T10:30:00Z',
    status: 'active',
    reviewStatus: 'pending',
    userId: 'user1',
    userName: '张三',
  },
  {
    id: '2',
    exchange: 'OKX',
    label: '跟单账户',
    apiKey: 'xYz987uVw654tSr321qPo098nMl765kIj432',
    createdAt: '2025-02-11T14:20:00Z',
    status: 'active',
    reviewStatus: 'approved',
    reviewReason: '密钥格式正确，权限设置合理',
    reviewedBy: '管理员A',
    reviewedAt: '2025-02-11T15:00:00Z',
    userId: 'user2',
    userName: '李四',
  },
  {
    id: '3',
    exchange: 'Binance',
    label: '测试账户',
    apiKey: 'mNo345pQr678sTu901vWx234yZa567bCd890',
    createdAt: '2025-02-12T09:15:00Z',
    status: 'disabled',
    reviewStatus: 'rejected',
    reviewReason: '密钥权限过大，存在安全风险',
    reviewedBy: '管理员B',
    reviewedAt: '2025-02-12T10:30:00Z',
    userId: 'user3',
    userName: '王五',
  },
]

const reviewDialog = ref({
  show: false,
  apiKey: null as ApiKey | null,
  result: 'approved' as 'approved' | 'rejected',
  reason: '',
})

const filteredApiKeys = computed(() => {
  return apiKeys.filter(key => key.reviewStatus === activeTab.value)
})

const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-amber-500/20 text-amber-400'
    case 'approved': return 'bg-emerald-500/20 text-emerald-400'
    case 'rejected': return 'bg-red-500/20 text-red-400'
    default: return 'bg-dark-600 text-dark-100'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '待审核'
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return status
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending': return 'text-amber-400'
    case 'approved': return 'text-emerald-400'
    case 'rejected': return 'text-red-400'
    default: return 'text-white'
  }
}

const maskApiKey = (key: string) => {
  if (key.length <= 8) return key
  return key.substring(0, 6) + '*'.repeat(key.length - 10) + key.substring(key.length - 4)
}

const formatDate = (dateString?: string) => {
  if (!dateString) return '--'
  return new Date(dateString).toLocaleString('zh-CN')
}

const showReviewDialog = (apiKey: ApiKey) => {
  reviewDialog.value = {
    show: true,
    apiKey,
    result: 'approved',
    reason: '',
  }
}

const closeReviewDialog = () => {
  reviewDialog.value.show = false
}

const submitReview = () => {
  if (!reviewDialog.value.apiKey) return

  const apiKeyIndex = apiKeys.findIndex(k => k.id === reviewDialog.value.apiKey!.id)
  if (apiKeyIndex !== -1) {
    apiKeys[apiKeyIndex] = {
      ...apiKeys[apiKeyIndex],
      reviewStatus: reviewDialog.value.result,
      reviewReason: reviewDialog.value.reason,
      reviewedBy: '当前管理员',
      reviewedAt: new Date().toISOString(),
    }
  }

  closeReviewDialog()
}

const showDetail = (apiKey: ApiKey) => {
  // 显示详细信息的逻辑
  console.log('查看详情:', apiKey)
}
</script>