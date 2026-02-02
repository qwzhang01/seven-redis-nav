<template>
  <div class="order-panel-wrapper">
    <!-- 买卖切换 -->
    <div class="order-tabs">
      <div
        class="order-tab buy"
        :class="{ active: side === 'buy' }"
        @click="side = 'buy'"
      >
        买入
      </div>
      <div
        class="order-tab sell"
        :class="{ active: side === 'sell' }"
        @click="side = 'sell'"
      >
        卖出
      </div>
    </div>
    
    <!-- 订单类型 -->
    <t-select v-model="orderType" class="order-type-select">
      <t-option value="limit" label="限价单" />
      <t-option value="market" label="市价单" />
      <t-option value="stop" label="止盈止损" />
    </t-select>
    
    <!-- 价格输入 -->
    <div class="input-group">
      <label>价格</label>
      <t-input-number
        v-model="price"
        :disabled="orderType === 'market'"
        :placeholder="orderType === 'market' ? '市价' : '价格'"
        theme="normal"
        align="right"
        :decimal-places="2"
      >
        <template #suffix>USDT</template>
      </t-input-number>
    </div>
    
    <!-- 数量输入 -->
    <div class="input-group">
      <label>数量</label>
      <t-input-number
        v-model="amount"
        placeholder="0.00"
        theme="normal"
        align="right"
        :decimal-places="6"
        :min="0"
      >
        <template #suffix>BTC</template>
      </t-input-number>
      
      <!-- 百分比按钮 -->
      <div class="percent-btns">
        <t-button size="small" variant="outline" @click="setPercent(25)">25%</t-button>
        <t-button size="small" variant="outline" @click="setPercent(50)">50%</t-button>
        <t-button size="small" variant="outline" @click="setPercent(75)">75%</t-button>
        <t-button size="small" variant="outline" @click="setPercent(100)">MAX</t-button>
      </div>
    </div>
    
    <!-- 订单信息 -->
    <div class="order-info">
      <div class="info-row">
        <span>可用</span>
        <span>{{ formatMoney(available) }} USDT</span>
      </div>
      <div class="info-row">
        <span>预估金额</span>
        <span>{{ formatMoney(estimatedTotal) }} USDT</span>
      </div>
    </div>
    
    <!-- 下单按钮 -->
    <t-button
      :theme="side === 'buy' ? 'success' : 'danger'"
      size="large"
      block
      :loading="loading"
      @click="submitOrder"
    >
      {{ side === 'buy' ? '买入' : '卖出' }} BTC
    </t-button>
    
    <!-- 快捷功能 -->
    <div class="quick-actions">
      <t-button variant="text" size="small">
        <t-icon name="time" /> 计划委托
      </t-button>
      <t-button variant="text" size="small">
        <t-icon name="chart-line" /> 条件单
      </t-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { useTradingStore } from '@/stores/trading'
import { useUserStore } from '@/stores/user'

const tradingStore = useTradingStore()
const userStore = useUserStore()

const side = ref('buy')
const orderType = ref('limit')
const price = ref(45230.50)
const amount = ref(0)
const loading = ref(false)

// 可用余额
const available = computed(() => {
  return userStore.isPaperTrading
    ? userStore.virtualAccount.balance
    : 10000
})

// 预估金额
const estimatedTotal = computed(() => {
  const p = orderType.value === 'market' ? tradingStore.currentPair.price : price.value
  return (p || 0) * (amount.value || 0)
})

// 设置百分比
const setPercent = (percent) => {
  const p = orderType.value === 'market' ? tradingStore.currentPair.price : price.value
  if (p > 0) {
    amount.value = parseFloat(((available.value * percent / 100) / p).toFixed(6))
  }
}

// 格式化金额
const formatMoney = (value) => {
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 提交订单
const submitOrder = async () => {
  if (!amount.value || amount.value <= 0) {
    MessagePlugin.warning('请输入数量')
    return
  }
  
  loading.value = true
  
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    tradingStore.placeOrder({
      pair: tradingStore.currentPair.symbol,
      side: side.value,
      type: orderType.value === 'limit' ? '限价' : '市价',
      price: orderType.value === 'market' ? null : price.value,
      amount: amount.value
    })
    
    MessagePlugin.success('订单提交成功！')
    amount.value = 0
  } finally {
    loading.value = false
  }
}
</script>

<style lang="less" scoped>
.order-panel-wrapper {
  padding: 20px;
  color: #fff;
}

.order-tabs {
  display: flex;
  margin-bottom: 20px;
  
  .order-tab {
    flex: 1;
    padding: 12px;
    text-align: center;
    cursor: pointer;
    font-weight: 500;
    border-radius: 6px 6px 0 0;
    color: rgba(255, 255, 255, 0.6);
    background: #21262d;
    transition: all 0.3s;
    
    &.buy.active {
      background: var(--green);
      color: #fff;
    }
    
    &.sell.active {
      background: var(--red);
      color: #fff;
    }
  }
}

.order-type-select {
  margin-bottom: 16px;
  
  :deep(.t-input) {
    background: #21262d;
    border-color: #30363d;
    color: #fff;
  }
}

.input-group {
  margin-bottom: 16px;
  
  label {
    display: block;
    color: rgba(255, 255, 255, 0.6);
    font-size: 13px;
    margin-bottom: 8px;
  }
  
  :deep(.t-input-number) {
    width: 100%;
    
    .t-input {
      background: #21262d;
      border-color: #30363d;
      color: #fff;
    }
    
    .t-input__suffix {
      color: rgba(255, 255, 255, 0.6);
    }
  }
}

.percent-btns {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  
  :deep(.t-button) {
    flex: 1;
    color: rgba(255, 255, 255, 0.8) !important;
    border-color: #30363d !important;
    background: transparent !important;
    
    &:hover {
      color: #fff !important;
      border-color: var(--brand) !important;
      background: rgba(18, 95, 255, 0.1) !important;
    }
  }
}

.order-info {
  padding: 16px 0;
  border-top: 1px solid #30363d;
  margin: 16px 0;
  
  .info-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    
    span:last-child {
      color: #fff;
    }
  }
}

.quick-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  
  .t-button {
    color: rgba(255, 255, 255, 0.6);
  }
}
</style>
