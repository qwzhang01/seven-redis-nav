<template>
  <div class="order-list-wrapper">
    <!-- 订单类型切换 -->
    <div class="orders-header">
      <div class="orders-tabs">
        <span
          :class="{ active: activeTab === 'current' }"
          @click="activeTab = 'current'"
        >
          当前委托
          <t-tag v-if="tradingStore.pendingOrderCount > 0" size="small" theme="primary">
            {{ tradingStore.pendingOrderCount }}
          </t-tag>
        </span>
        <span
          :class="{ active: activeTab === 'history' }"
          @click="activeTab = 'history'"
        >
          历史订单
        </span>
      </div>
      
      <!-- 筛选 -->
      <div class="orders-filter">
        <t-input
          v-model="searchKeyword"
          placeholder="搜索订单..."
          clearable
          size="small"
        >
          <template #prefix-icon>
            <t-icon name="search" />
          </template>
        </t-input>
        
        <t-select v-model="filterPair" placeholder="全部交易对" clearable size="small">
          <t-option value="BTC/USDT" label="BTC/USDT" />
          <t-option value="ETH/USDT" label="ETH/USDT" />
        </t-select>
        
        <t-select v-model="filterSide" placeholder="全部方向" clearable size="small">
          <t-option value="buy" label="买入" />
          <t-option value="sell" label="卖出" />
        </t-select>
      </div>
      
      <t-button
        v-if="activeTab === 'current'"
        variant="outline"
        size="small"
        theme="danger"
        @click="cancelAllOrders"
      >
        一键撤单
      </t-button>
    </div>
    
    <!-- 当前委托表格 -->
    <t-table
      v-if="activeTab === 'current'"
      :data="filteredOrders"
      :columns="currentColumns"
      row-key="id"
      hover
      stripe
      size="small"
      :loading="loading"
    >
      <template #side="{ row }">
        <span :class="row.side">{{ row.side === 'buy' ? '买入' : '卖出' }}</span>
      </template>
      <template #status="{ row }">
        <t-tag size="small" :theme="getStatusTheme(row.status)">
          {{ getStatusText(row.status) }}
        </t-tag>
      </template>
      <template #operation="{ row }">
        <t-button
          variant="text"
          size="small"
          theme="danger"
          @click="cancelOrder(row.id)"
        >
          撤单
        </t-button>
      </template>
    </t-table>
    
    <!-- 历史订单表格 -->
    <t-table
      v-else
      :data="filteredHistoryOrders"
      :columns="historyColumns"
      row-key="id"
      hover
      stripe
      size="small"
    >
      <template #side="{ row }">
        <span :class="row.side">{{ row.side === 'buy' ? '买入' : '卖出' }}</span>
      </template>
      <template #status="{ row }">
        <t-tag size="small" :theme="getStatusTheme(row.status)">
          {{ getStatusText(row.status) }}
        </t-tag>
      </template>
      <template #pnl="{ row }">
        <span v-if="row.pnl" :class="row.pnl >= 0 ? 'positive' : 'negative'">
          {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl.toFixed(2) }}
        </span>
        <span v-else>-</span>
      </template>
    </t-table>
    
    <!-- 分页 -->
    <div class="orders-pagination">
      <span class="page-info">共 {{ totalCount }} 条记录</span>
      <t-pagination
        v-model:current="currentPage"
        :total="totalCount"
        :page-size="10"
        size="small"
        show-jumper
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import { useTradingStore } from '@/stores/trading'

const tradingStore = useTradingStore()

const activeTab = ref('current')
const loading = ref(false)
const searchKeyword = ref('')
const filterPair = ref('')
const filterSide = ref('')
const currentPage = ref(1)

// 当前委托列定义
const currentColumns = [
  { colKey: 'time', title: '时间', width: 100 },
  { colKey: 'pair', title: '交易对', width: 100 },
  { colKey: 'side', title: '方向', width: 80, cell: 'side' },
  { colKey: 'type', title: '类型', width: 80 },
  { colKey: 'price', title: '价格', width: 100 },
  { colKey: 'amount', title: '数量', width: 80 },
  { colKey: 'filled', title: '已成交', width: 80 },
  { colKey: 'status', title: '状态', width: 80, cell: 'status' },
  { colKey: 'operation', title: '操作', width: 80, cell: 'operation' }
]

// 历史订单列定义
const historyColumns = [
  { colKey: 'time', title: '时间', width: 100 },
  { colKey: 'pair', title: '交易对', width: 100 },
  { colKey: 'side', title: '方向', width: 80, cell: 'side' },
  { colKey: 'type', title: '类型', width: 80 },
  { colKey: 'price', title: '价格', width: 100 },
  { colKey: 'amount', title: '数量', width: 80 },
  { colKey: 'fillPrice', title: '成交价', width: 100 },
  { colKey: 'status', title: '状态', width: 80, cell: 'status' },
  { colKey: 'pnl', title: '盈亏', width: 100, cell: 'pnl' }
]

// 筛选后的订单
const filteredOrders = computed(() => {
  let orders = tradingStore.orders
  
  if (searchKeyword.value) {
    orders = orders.filter(o => o.pair.includes(searchKeyword.value))
  }
  if (filterPair.value) {
    orders = orders.filter(o => o.pair === filterPair.value)
  }
  if (filterSide.value) {
    orders = orders.filter(o => o.side === filterSide.value)
  }
  
  return orders
})

// 筛选后的历史订单
const filteredHistoryOrders = computed(() => {
  let orders = tradingStore.historyOrders
  
  if (searchKeyword.value) {
    orders = orders.filter(o => o.pair.includes(searchKeyword.value))
  }
  if (filterPair.value) {
    orders = orders.filter(o => o.pair === filterPair.value)
  }
  if (filterSide.value) {
    orders = orders.filter(o => o.side === filterSide.value)
  }
  
  return orders
})

// 总数
const totalCount = computed(() => {
  return activeTab.value === 'current' ? filteredOrders.value.length : filteredHistoryOrders.value.length
})

// 获取状态主题
const getStatusTheme = (status) => {
  const themes = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'default',
    partial: 'primary'
  }
  return themes[status] || 'default'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    partial: '部分成交'
  }
  return texts[status] || status
}

// 撤销订单
const cancelOrder = (orderId) => {
  DialogPlugin.confirm({
    header: '撤销确认',
    body: '确定要撤销这个订单吗？',
    confirmBtn: '确定',
    cancelBtn: '取消',
    onConfirm: () => {
      tradingStore.cancelOrder(orderId)
      MessagePlugin.success('订单已撤销')
    }
  })
}

// 一键撤单
const cancelAllOrders = () => {
  DialogPlugin.confirm({
    header: '撤销确认',
    body: '确定要撤销所有当前委托吗？',
    confirmBtn: '确定',
    cancelBtn: '取消',
    onConfirm: () => {
      tradingStore.orders.forEach(o => tradingStore.cancelOrder(o.id))
      MessagePlugin.success('已撤销所有订单')
    }
  })
}
</script>

<style lang="less" scoped>
.order-list-wrapper {
  color: #fff;
}

.orders-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.orders-tabs {
  display: flex;
  gap: 24px;
  
  span {
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    padding-bottom: 8px;
    border-bottom: 2px solid transparent;
    display: flex;
    align-items: center;
    gap: 4px;
    
    &.active {
      color: #fff;
      border-bottom-color: var(--brand);
    }
  }
}

.orders-filter {
  display: flex;
  gap: 12px;
  margin-left: auto;
  
  :deep(.t-input),
  :deep(.t-select) {
    width: 140px;
    
    .t-input {
      background: #21262d;
      border-color: #30363d;
      color: #fff;
    }
  }
}

:deep(.t-table) {
  background: transparent;
  
  .t-table__header th {
    background: #21262d;
    color: rgba(255, 255, 255, 0.6);
    border-color: #30363d;
  }
  
  .t-table__body td {
    color: #fff;
    border-color: #21262d;
    background: transparent;
  }
  
  .t-table__body tr:hover td {
    background: #21262d;
  }
  
  .buy {
    color: var(--green);
  }
  
  .sell {
    color: var(--red);
  }
  
  .positive {
    color: var(--green);
  }
  
  .negative {
    color: var(--red);
  }
}

.orders-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  
  .page-info {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
  }
}
</style>
