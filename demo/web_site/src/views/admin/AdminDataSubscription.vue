<template>
  <div class="space-y-6">
    <!-- 页面标题和操作按钮 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-white">实时数据订阅管理</h2>
        <p class="text-sm text-dark-100 mt-1">
          管理实时数据订阅状态、启动、暂停、恢复和手动同步</p>
      </div>
      <div class="flex items-center gap-3">
        <button @click="showHistorySyncDialog = true"
                class="btn-secondary !py-2 !px-4 text-sm flex items-center gap-1.5">
          <Database :size="14"/>
          历史数据同步
        </button>
        <button @click="showAddDialog = true"
                class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
          <Plus :size="14"/>
          新增订阅
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="glass-card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-dark-100">运行中</p>
            <p class="text-2xl font-bold text-emerald-400 mt-1">{{
                stats.running
              }}</p>
          </div>
          <div
              class="w-12 h-12 rounded-lg bg-emerald-500/10 flex items-center justify-center">
            <Play :size="24" class="text-emerald-400"/>
          </div>
        </div>
      </div>
      <div class="glass-card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-dark-100">已暂停</p>
            <p class="text-2xl font-bold text-amber-400 mt-1">{{
                stats.paused
              }}</p>
          </div>
          <div
              class="w-12 h-12 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <Pause :size="24" class="text-amber-400"/>
          </div>
        </div>
      </div>
      <div class="glass-card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-dark-100">已停止</p>
            <p class="text-2xl font-bold text-red-400 mt-1">{{
                stats.stopped
              }}</p>
          </div>
          <div
              class="w-12 h-12 rounded-lg bg-red-500/10 flex items-center justify-center">
            <Square :size="24" class="text-red-400"/>
          </div>
        </div>
      </div>
      <div class="glass-card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-dark-100">总记录数</p>
            <p class="text-2xl font-bold text-primary-500 mt-1">
              {{ formatNumber(stats.totalRecords) }}</p>
          </div>
          <div
              class="w-12 h-12 rounded-lg bg-primary-500/10 flex items-center justify-center">
            <Database :size="24" class="text-primary-500"/>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="glass-card p-4 flex flex-wrap items-center gap-4">
      <t-input v-model="search" placeholder="搜索订阅名称..." clearable
               size="medium" style="width: 240px">
        <template #prefix-icon>
          <Search :size="16" class="text-dark-100"/>
        </template>
      </t-input>
      <t-select v-model="filterStatus" placeholder="状态" clearable
                size="medium" style="width: 140px">
        <t-option label="运行中" value="running"/>
        <t-option label="已暂停" value="paused"/>
        <t-option label="已停止" value="stopped"/>
      </t-select>
      <t-select v-model="filterExchange" placeholder="交易所" clearable
                size="medium" style="width: 160px">
        <t-option label="Binance" value="Binance"/>
        <t-option label="OKX" value="OKX"/>
        <t-option label="Bybit" value="Bybit"/>
        <t-option label="Bitget" value="Bitget"/>
      </t-select>
      <t-select v-model="filterDataType" placeholder="数据类型" clearable
                size="medium" style="width: 140px">
        <t-option label="K线" value="kline"/>
        <t-option label="Ticker" value="ticker"/>
        <t-option label="深度" value="depth"/>
        <t-option label="成交" value="trade"/>
        <t-option label="订单簿" value="orderbook"/>
      </t-select>
    </div>

    <!-- 订阅列表 -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
          <tr class="border-b border-white/[0.06]">
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">
              订阅名称
            </th>
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易所
            </th>
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">
              数据类型
            </th>
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易对
            </th>
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">周期
            </th>
            <th class="text-right py-3.5 px-5 text-dark-100 font-medium">
              总记录数
            </th>
            <th class="text-right py-3.5 px-5 text-dark-100 font-medium">
              错误数
            </th>
            <th class="text-left py-3.5 px-5 text-dark-100 font-medium">
              最后同步
            </th>
            <th class="text-center py-3.5 px-5 text-dark-100 font-medium">状态
            </th>
            <th class="text-center py-3.5 px-5 text-dark-100 font-medium">操作
            </th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="sub in filteredList" :key="sub.id"
              class="border-b border-white/[0.04] hover:bg-white/[0.02]">
            <td class="py-3.5 px-5 text-white font-medium">{{ sub.name }}</td>
            <td class="py-3.5 px-5 text-dark-100">{{ sub.exchange }}</td>
            <td class="py-3.5 px-5">
                <span class="px-2 py-1 rounded text-xs font-medium"
                      :class="getDataTypeClass(sub.dataType)">
                  {{ getDataTypeLabel(sub.dataType) }}
                </span>
            </td>
            <td class="py-3.5 px-5 text-dark-100">
              <div class="flex flex-wrap gap-1">
                  <span v-for="symbol in sub.symbols.slice(0, 2)" :key="symbol"
                        class="text-xs bg-white/[0.04] px-2 py-0.5 rounded">
                    {{ symbol }}
                  </span>
                <span v-if="sub.symbols.length > 2"
                      class="text-xs text-dark-100">+{{
                    sub.symbols.length - 2
                  }}</span>
              </div>
            </td>
            <td class="py-3.5 px-5 text-dark-100">{{ sub.interval || '-' }}</td>
            <td class="py-3.5 px-5 text-right text-white font-medium">
              {{ formatNumber(sub.totalRecords) }}
            </td>
            <td class="py-3.5 px-5 text-right"
                :class="sub.errorCount > 0 ? 'text-red-400' : 'text-dark-100'">
              {{ sub.errorCount }}
            </td>
            <td class="py-3.5 px-5 text-dark-100 text-xs">
              {{ formatTime(sub.lastSyncTime) }}
            </td>
            <td class="py-3.5 px-5 text-center">
                <span class="px-2 py-1 rounded text-xs font-medium"
                      :class="getStatusClass(sub.status)">
                  {{ getStatusLabel(sub.status) }}
                </span>
            </td>
            <td class="py-3.5 px-5">
              <div class="flex items-center justify-center gap-1">
                <button
                    v-if="sub.status === 'stopped' || sub.status === 'paused'"
                    @click="startSubscription(sub.id)"
                    class="p-1.5 rounded text-dark-100 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                    title="启动"
                >
                  <Play :size="14"/>
                </button>
                <button
                    v-if="sub.status === 'running'"
                    @click="pauseSubscription(sub.id)"
                    class="p-1.5 rounded text-dark-100 hover:text-amber-400 hover:bg-amber-500/10 transition-all"
                    title="暂停"
                >
                  <Pause :size="14"/>
                </button>
                <button
                    v-if="sub.status === 'running' || sub.status === 'paused'"
                    @click="stopSubscription(sub.id)"
                    class="p-1.5 rounded text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all"
                    title="停止"
                >
                  <Square :size="14"/>
                </button>
                <button
                    @click="openSyncDialog(sub)"
                    class="p-1.5 rounded text-dark-100 hover:text-primary-500 hover:bg-primary-500/10 transition-all"
                    title="手动同步"
                >
                  <RefreshCw :size="14"/>
                </button>
                <button
                    @click="editSubscription(sub)"
                    class="p-1.5 rounded text-dark-100 hover:text-primary-500 hover:bg-primary-500/10 transition-all"
                    title="编辑"
                >
                  <Pencil :size="14"/>
                </button>
                <button
                    @click="deleteSubscription(sub.id)"
                    class="p-1.5 rounded text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all"
                    title="删除"
                >
                  <Trash2 :size="14"/>
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 同步任务列表 -->
    <div class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-white">同步任务</h3>
        <button @click="refreshTasks"
                class="text-sm text-primary-500 hover:text-primary-400 flex items-center gap-1">
          <RefreshCw :size="14"/>
          刷新
        </button>
      </div>
      <div class="space-y-3">
        <div v-for="task in syncTasks" :key="task.id"
             class="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06]">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-3">
              <span class="text-white font-medium">{{
                  task.subscriptionName
                }}</span>
              <span class="px-2 py-0.5 rounded text-xs font-medium"
                    :class="getTaskStatusClass(task.status)">
                {{ getTaskStatusLabel(task.status) }}
              </span>
            </div>
            <span class="text-xs text-dark-100">{{
                formatTime(task.createdAt)
              }}</span>
          </div>
          <div class="grid grid-cols-4 gap-4 text-sm mb-2">
            <div>
              <span class="text-dark-100">交易所：</span>
              <span class="text-white">{{ task.exchange }}</span>
            </div>
            <div>
              <span class="text-dark-100">数据类型：</span>
              <span class="text-white">{{ task.dataType }}</span>
            </div>
            <div>
              <span class="text-dark-100">时间范围：</span>
              <span class="text-white">{{
                  formatTime(task.startTime)
                }} ~ {{ formatTime(task.endTime) }}</span>
            </div>
            <div>
              <span class="text-dark-100">进度：</span>
              <span class="text-white">{{
                  task.syncedRecords
                }} / {{ task.totalRecords }}</span>
            </div>
          </div>
          <div v-if="task.status === 'running'"
               class="w-full bg-white/[0.06] rounded-full h-2">
            <div class="bg-primary-500 h-2 rounded-full transition-all"
                 :style="{ width: task.progress + '%' }"></div>
          </div>
          <div v-if="task.errorMessage" class="mt-2 text-xs text-red-400">
            错误：{{ task.errorMessage }}
          </div>
        </div>
        <div v-if="syncTasks.length === 0"
             class="text-center py-8 text-dark-100">
          暂无同步任务
        </div>
      </div>
    </div>

    <!-- 新增/编辑订阅对话框 -->
    <t-dialog
        v-model:visible="showAddDialog"
        :header="currentEditId ? '编辑订阅' : '新增订阅'"
        :dialogStyle="{'background-color': 'rgb(8 10 15)'}"
        width="600px"
        :footer="false"
        @close="resetAddDialog"
    >
      <div class="space-y-4 py-4">
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">订阅名称</label>
          <t-input v-model="formData.name" placeholder="请输入订阅名称"/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">交易所</label>
          <t-select v-model="formData.exchange" placeholder="选择交易所"
                    style="width: 100%">
            <t-option label="Binance" value="Binance"/>
            <t-option label="OKX" value="OKX"/>
            <t-option label="Bybit" value="Bybit"/>
            <t-option label="Bitget" value="Bitget"/>
          </t-select>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">数据类型</label>
          <t-select v-model="formData.dataType" placeholder="选择数据类型"
                    style="width: 100%">
            <t-option label="K线" value="kline"/>
            <t-option label="Ticker" value="ticker"/>
            <t-option label="深度" value="depth"/>
            <t-option label="成交" value="trade"/>
            <t-option label="订单簿" value="orderbook"/>
          </t-select>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">交易对（多个用逗号分隔）</label>
          <t-input v-model="formData.symbols"
                   placeholder="例如：BTC/USDT,ETH/USDT"/>
        </div>
        <div v-if="formData.dataType === 'kline'">
          <label
              class="block text-sm font-medium text-white mb-2">K线周期</label>
          <t-select v-model="formData.interval" placeholder="选择周期"
                    style="width: 100%">
            <t-option label="1分钟" value="1m"/>
            <t-option label="5分钟" value="5m"/>
            <t-option label="15分钟" value="15m"/>
            <t-option label="1小时" value="1h"/>
            <t-option label="4小时" value="4h"/>
            <t-option label="日线" value="1d"/>
          </t-select>
        </div>
        <div class="flex items-center gap-2">
          <t-checkbox v-model="formData.autoRestart">自动重启</t-checkbox>
        </div>
        <div class="flex justify-end gap-2 pt-4">
          <button @click="showAddDialog = false"
                  class="px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
            取消
          </button>
          <button @click="saveSubscription"
                  class="btn-primary !py-2 !px-4 text-sm">
            保存
          </button>
        </div>
      </div>
    </t-dialog>

    <!-- 手动同步对话框 -->
    <t-dialog
        v-model:visible="showSyncDialog"
        header="手动同步数据"
        width="500px"
        :dialogStyle="{'background-color': 'rgb(8 10 15)'}"
        :footer="false"
    >
      <div class="space-y-4 py-4">
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">订阅名称</label>
          <t-input v-model="syncFormData.subscriptionName" disabled/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">开始时间</label>
          <t-date-picker v-model="syncFormData.startTime" enable-time-picker
                         style="width: 100%"/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">结束时间</label>
          <t-date-picker v-model="syncFormData.endTime" enable-time-picker
                         style="width: 100%"/>
        </div>
        <div class="flex justify-end gap-2 pt-4">
          <button @click="showSyncDialog = false"
                  class="px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
            取消
          </button>
          <button @click="startManualSync"
                  class="btn-primary !py-2 !px-4 text-sm">
            开始同步
          </button>
        </div>
      </div>
    </t-dialog>

    <!-- 历史数据同步对话框 -->
    <t-dialog
        v-model:visible="showHistorySyncDialog"
        header="历史数据同步"
        width="600px"
        :dialogStyle="{'background-color': 'rgb(8 10 15)'}"
        :footer="false"
    >
      <div class="space-y-4 py-4">
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">同步名称</label>
          <t-input v-model="historySyncFormData.name"
                   placeholder="请输入同步任务名称"/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">交易所</label>
          <t-select v-model="historySyncFormData.exchange"
                    placeholder="选择交易所" style="width: 100%">
            <t-option label="Binance" value="Binance"/>
            <t-option label="OKX" value="OKX"/>
            <t-option label="Bybit" value="Bybit"/>
            <t-option label="Bitget" value="Bitget"/>
          </t-select>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">数据类型</label>
          <t-select v-model="historySyncFormData.dataType"
                    placeholder="选择数据类型" style="width: 100%">
            <t-option label="K线" value="kline"/>
            <t-option label="Ticker" value="ticker"/>
            <t-option label="深度" value="depth"/>
            <t-option label="成交" value="trade"/>
            <t-option label="订单簿" value="orderbook"/>
          </t-select>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">交易对（多个用逗号分隔）</label>
          <t-input v-model="historySyncFormData.symbols"
                   placeholder="例如：BTC/USDT,ETH/USDT"/>
        </div>
        <div v-if="historySyncFormData.dataType === 'kline'">
          <label
              class="block text-sm font-medium text-white mb-2">K线周期</label>
          <t-select v-model="historySyncFormData.interval"
                    placeholder="选择周期" style="width: 100%">
            <t-option label="1分钟" value="1m"/>
            <t-option label="5分钟" value="5m"/>
            <t-option label="15分钟" value="15m"/>
            <t-option label="1小时" value="1h"/>
            <t-option label="4小时" value="4h"/>
            <t-option label="日线" value="1d"/>
          </t-select>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">开始时间</label>
          <t-date-picker v-model="historySyncFormData.startTime"
                         enable-time-picker style="width: 100%"/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">结束时间</label>
          <t-date-picker v-model="historySyncFormData.endTime"
                         enable-time-picker style="width: 100%"/>
        </div>
        <div>
          <label
              class="block text-sm font-medium text-white mb-2">批次大小</label>
          <t-input v-model.number="historySyncFormData.batchSize" type="number"
                   placeholder="每次请求的数据量，默认1000"/>
        </div>
        <div class="flex justify-end gap-2 pt-4">
          <button @click="showHistorySyncDialog = false"
                  class="px-4 py-2 rounded-lg text-sm text-dark-100 hover:text-white hover:bg-white/[0.04] transition-all">
            取消
          </button>
          <button @click="startHistorySync"
                  class="btn-primary !py-2 !px-4 text-sm">
            开始同步
          </button>
        </div>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, watch} from 'vue'
import {
  Plus,
  Search,
  Play,
  Pause,
  Square,
  RefreshCw,
  Pencil,
  Trash2,
  Database
} from 'lucide-vue-next'
import type {DataSubscription, SyncTask} from '@/types'
import {MessagePlugin, DialogPlugin} from 'tdesign-vue-next'
import * as marketApi from '@/utils/marketApi'

// 数据状态
const subscriptions = ref<DataSubscription[]>([])
const syncTasks = ref<any[]>([])
const loading = ref(false)
const currentEditId = ref<string | null>(null)

const search = ref('')
const filterStatus = ref('')
const filterExchange = ref('')
const filterDataType = ref('')
const showAddDialog = ref(false)
const showSyncDialog = ref(false)
const showHistorySyncDialog = ref(false)

const formData = ref({
  name: '',
  exchange: '',
  dataType: '',
  symbols: '',
  interval: '',
  autoRestart: true
})

const syncFormData = ref({
  subscriptionId: '',
  subscriptionName: '',
  startTime: '',
  endTime: ''
})

const historySyncFormData = ref({
  name: '',
  exchange: '',
  dataType: '',
  symbols: '',
  interval: '',
  startTime: '',
  endTime: '',
  batchSize: 1000
})

// 统计数据
const statisticsData = ref<any>(null)
const stats = computed(() => {
  if (statisticsData.value) {
    return {
      running: statisticsData.value.running_subscriptions || 0,
      paused: statisticsData.value.paused_subscriptions || 0,
      stopped: statisticsData.value.stopped_subscriptions || 0,
      totalRecords: statisticsData.value.total_records || 0
    }
  }
  return {
    running: subscriptions.value.filter(s => s.status === 'running').length,
    paused: subscriptions.value.filter(s => s.status === 'paused').length,
    stopped: subscriptions.value.filter(s => s.status === 'stopped').length,
    totalRecords: subscriptions.value.reduce((sum, s) => sum + s.totalRecords, 0)
  }
})

// 过滤列表
const filteredList = computed(() => {
  return subscriptions.value.filter((s) => {
    if (search.value && !s.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterStatus.value && s.status !== filterStatus.value) return false
    if (filterExchange.value && s.exchange !== filterExchange.value) return false
    if (filterDataType.value && s.dataType !== filterDataType.value) return false
    return true
  })
})

// 工具函数
function formatNumber(num: number): string {
  return num.toLocaleString()
}

function formatTime(time?: string): string {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

function getDataTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    kline: 'K线',
    ticker: 'Ticker',
    depth: '深度',
    trade: '成交',
    orderbook: '订单簿'
  }
  return labels[type] || type
}

function getDataTypeClass(type: string): string {
  const classes: Record<string, string> = {
    kline: 'bg-blue-500/10 text-blue-400',
    ticker: 'bg-green-500/10 text-green-400',
    depth: 'bg-purple-500/10 text-purple-400',
    trade: 'bg-orange-500/10 text-orange-400',
    orderbook: 'bg-pink-500/10 text-pink-400'
  }
  return classes[type] || 'bg-gray-500/10 text-gray-400'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止'
  }
  return labels[status] || status
}

function getStatusClass(status: string): string {
  const classes: Record<string, string> = {
    running: 'bg-emerald-500/10 text-emerald-400',
    paused: 'bg-amber-500/10 text-amber-400',
    stopped: 'bg-red-500/10 text-red-400'
  }
  return classes[status] || 'bg-gray-500/10 text-gray-400'
}

function getTaskStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '同步中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

function getTaskStatusClass(status: string): string {
  const classes: Record<string, string> = {
    pending: 'bg-gray-500/10 text-gray-400',
    running: 'bg-blue-500/10 text-blue-400',
    completed: 'bg-emerald-500/10 text-emerald-400',
    failed: 'bg-red-500/10 text-red-400'
  }
  return classes[status] || 'bg-gray-500/10 text-gray-400'
}

// 初始化数据
onMounted(() => {
  loadSubscriptions()
  loadStatistics()
  loadSyncTasks()
})

// 监听筛选条件变化
watch([search, filterStatus, filterExchange, filterDataType], () => {
  loadSubscriptions()
}, {deep: true})

// 加载订阅列表
async function loadSubscriptions() {
  try {
    loading.value = true
    const params: marketApi.GetSubscriptionsParams = {
      page: 1,
      page_size: 100
    }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterExchange.value) params.exchange = filterExchange.value
    if (filterDataType.value) params.data_type = filterDataType.value
    if (search.value) params.search = search.value

    const response = await marketApi.getSubscriptions(params)
    if (response.success && response.data) {
      // 转换API数据格式到前端数据格式
      subscriptions.value = response.data.items.map(item => ({
        id: item.id,
        name: item.name,
        exchange: item.exchange,
        dataType: item.data_type,
        symbols: item.symbols,
        interval: item.interval,
        status: item.status,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        lastSyncTime: item.last_sync_time,
        totalRecords: item.total_records,
        errorCount: item.error_count,
        lastError: item.last_error,
        config: item.config
      }))
    }
  } catch (error: any) {
    console.error('加载订阅列表失败:', error)
    MessagePlugin.error(error.message || '加载订阅列表失败')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
async function loadStatistics() {
  try {
    const response = await marketApi.getSubscriptionStatistics()
    if (response.success && response.data) {
      statisticsData.value = response.data
    }
  } catch (error: any) {
    console.error('加载统计信息失败:', error)
  }
}

// 加载同步任务列表
async function loadSyncTasks() {
  try {
    const response = await marketApi.getSyncTasks({page: 1, page_size: 20})
    if (response.success && response.data) {
      syncTasks.value = response.data.items
    }
  } catch (error: any) {
    console.error('加载同步任务失败:', error)
  }
}

// 操作函数
async function startSubscription(id: string) {
  try {
    const response = await marketApi.startSubscription(id)
    if (response.success) {
      MessagePlugin.success(response.message || '订阅已启动')
      await loadSubscriptions()
      await loadStatistics()
    }
  } catch (error: any) {
    console.error('启动订阅失败:', error)
    MessagePlugin.error(error.message || '启动订阅失败')
  }
}

async function pauseSubscription(id: string) {
  try {
    const response = await marketApi.pauseSubscription(id)
    if (response.success) {
      MessagePlugin.success(response.message || '订阅已暂停')
      await loadSubscriptions()
      await loadStatistics()
    }
  } catch (error: any) {
    console.error('暂停订阅失败:', error)
    MessagePlugin.error(error.message || '暂停订阅失败')
  }
}

async function stopSubscription(id: string) {
  try {
    const response = await marketApi.stopSubscription(id)
    if (response.success) {
      MessagePlugin.success(response.message || '订阅已停止')
      await loadSubscriptions()
      await loadStatistics()
    }
  } catch (error: any) {
    console.error('停止订阅失败:', error)
    MessagePlugin.error(error.message || '停止订阅失败')
  }
}

function openSyncDialog(sub: DataSubscription) {
  syncFormData.value = {
    subscriptionId: sub.id,
    subscriptionName: sub.name,
    startTime: '',
    endTime: ''
  }
  showSyncDialog.value = true
}

async function startManualSync() {
  if (!syncFormData.value.startTime || !syncFormData.value.endTime) {
    MessagePlugin.warning('请选择时间范围')
    return
  }

  try {
    const response = await marketApi.createSyncTask({
      subscription_id: syncFormData.value.subscriptionId,
      start_time: syncFormData.value.startTime,
      end_time: syncFormData.value.endTime
    })

    if (response.success) {
      MessagePlugin.success(response.message || '同步任务已创建')
      showSyncDialog.value = false
      await loadSyncTasks()
    }
  } catch (error: any) {
    console.error('创建同步任务失败:', error)
    MessagePlugin.error(error.message || '创建同步任务失败')
  }
}

function editSubscription(sub: DataSubscription) {
  currentEditId.value = sub.id
  formData.value = {
    name: sub.name,
    exchange: sub.exchange,
    dataType: sub.dataType,
    symbols: sub.symbols.join(','),
    interval: sub.interval || '',
    autoRestart: sub.config.autoRestart
  }
  showAddDialog.value = true
}

async function deleteSubscription(id: string) {
  const confirmDialog = await DialogPlugin.confirm({
    header: '确认删除',
    body: '确定要删除这个订阅吗？删除后将无法恢复。',
    confirmBtn: '确定',
    cancelBtn: '取消'
  })

  confirmDialog.then(async () => {
    try {
      const response = await marketApi.deleteSubscription(id)
      if (response.success) {
        MessagePlugin.success(response.message || '订阅已删除')
        await loadSubscriptions()
        await loadStatistics()
      }
    } catch (error: any) {
      console.error('删除订阅失败:', error)
      MessagePlugin.error(error.message || '删除订阅失败')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

async function saveSubscription() {
  if (!formData.value.name || !formData.value.exchange || !formData.value.dataType || !formData.value.symbols) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  if (formData.value.dataType === 'kline' && !formData.value.interval) {
    MessagePlugin.warning('K线数据类型需要选择周期')
    return
  }

  try {
    const symbols = formData.value.symbols.split(',').map(s => s.trim())

    if (currentEditId.value) {
      // 更新订阅
      const response = await marketApi.updateSubscription(currentEditId.value, {
        name: formData.value.name,
        symbols: symbols,
        interval: formData.value.interval || undefined,
        config: {
          auto_restart: formData.value.autoRestart,
          max_retries: 3,
          batch_size: 1000,
          sync_interval: 60
        }
      })

      if (response.success) {
        MessagePlugin.success(response.message || '订阅已更新')
        showAddDialog.value = false
        currentEditId.value = null
        await loadSubscriptions()
      }
    } else {
      // 创建订阅
      const response = await marketApi.createSubscription({
        name: formData.value.name,
        exchange: formData.value.exchange,
        data_type: formData.value.dataType,
        symbols: symbols,
        interval: formData.value.interval || undefined,
        config: {
          auto_restart: formData.value.autoRestart,
          max_retries: 3,
          batch_size: 1000,
          sync_interval: 60
        }
      })

      if (response.success) {
        MessagePlugin.success(response.message || '订阅已创建')
        showAddDialog.value = false
        await loadSubscriptions()
        await loadStatistics()
      }
    }

    // 重置表单
    formData.value = {
      name: '',
      exchange: '',
      dataType: '',
      symbols: '',
      interval: '',
      autoRestart: true
    }
  } catch (error: any) {
    console.error('保存订阅失败:', error)
    MessagePlugin.error(error.message || '保存订阅失败')
  }
}

async function refreshTasks() {
  await loadSyncTasks()
  MessagePlugin.success('任务列表已刷新')
}

function resetAddDialog() {
  currentEditId.value = null
  formData.value = {
    name: '',
    exchange: '',
    dataType: '',
    symbols: '',
    interval: '',
    autoRestart: true
  }
}

async function startHistorySync() {
  if (!historySyncFormData.value.name || !historySyncFormData.value.exchange ||
      !historySyncFormData.value.dataType || !historySyncFormData.value.symbols ||
      !historySyncFormData.value.startTime || !historySyncFormData.value.endTime) {
    MessagePlugin.warning('请填写完整信息')
    return
  }

  if (historySyncFormData.value.dataType === 'kline' && !historySyncFormData.value.interval) {
    MessagePlugin.warning('K线数据类型需要选择周期')
    return
  }

  try {
    const symbols = historySyncFormData.value.symbols.split(',').map(s => s.trim())

    const response = await marketApi.createHistoricalSync({
      name: historySyncFormData.value.name,
      exchange: historySyncFormData.value.exchange,
      data_type: historySyncFormData.value.dataType,
      symbols: symbols,
      interval: historySyncFormData.value.interval || undefined,
      start_time: historySyncFormData.value.startTime,
      end_time: historySyncFormData.value.endTime,
      batch_size: historySyncFormData.value.batchSize || 1000
    })

    if (response.success) {
      MessagePlugin.success(response.message || '历史数据同步任务已创建')
      showHistorySyncDialog.value = false
      await loadSyncTasks()
    }

    // 重置表单
    historySyncFormData.value = {
      name: '',
      exchange: '',
      dataType: '',
      symbols: '',
      interval: '',
      startTime: '',
      endTime: '',
      batchSize: 1000
    }
  } catch (error: any) {
    console.error('创建历史同步任务失败:', error)
    MessagePlugin.error(error.message || '创建历史同步任务失败')
  }
}
</script>

<style scoped>
/* TDesign组件样式覆盖 */
:deep(.t-select .t-select__single-input),
:deep(.t-select .t-select__placeholder),
:deep(.t-input__inner) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option.t-is-selected) {
  color: #000000 !important;
}


:deep(.t-checkbox) {
  color: rgb(255 255 255);
}
</style>
