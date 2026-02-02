<template>
  <div class="virtual-account-page">
    <div class="page-header">
      <div class="header-left">
        <h1><t-icon name="currency-exchange" /> 虚拟账户</h1>
        <t-tag theme="primary" size="large">模拟交易专用</t-tag>
      </div>
      <t-button theme="primary" @click="showRecharge = true">
        <t-icon name="add" /> 充值虚拟资金
      </t-button>
    </div>
    
    <!-- 账户概览 -->
    <div class="account-overview">
      <div class="balance-card">
        <div class="balance-main">
          <div class="balance-label">账户总资产</div>
          <div class="balance-value">{{ formatPrice(accountInfo.totalBalance) }} <span>USDT</span></div>
          <div class="balance-change" :class="accountInfo.todayPnl >= 0 ? 'positive' : 'negative'">
            今日盈亏: {{ accountInfo.todayPnl >= 0 ? '+' : '' }}{{ formatPrice(accountInfo.todayPnl) }} USDT
            ({{ accountInfo.todayPnlPercent >= 0 ? '+' : '' }}{{ accountInfo.todayPnlPercent.toFixed(2) }}%)
          </div>
        </div>
        <div class="balance-chart">
          <apexchart type="area" height="100" :options="miniChartOptions" :series="miniChartSeries" />
        </div>
      </div>
      
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon"><t-icon name="wallet" /></div>
          <div class="stat-info">
            <div class="stat-label">可用余额</div>
            <div class="stat-value">{{ formatPrice(accountInfo.availableBalance) }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><t-icon name="lock-on" /></div>
          <div class="stat-info">
            <div class="stat-label">冻结资金</div>
            <div class="stat-value">{{ formatPrice(accountInfo.frozenBalance) }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><t-icon name="chart-line" /></div>
          <div class="stat-info">
            <div class="stat-label">累计收益</div>
            <div class="stat-value" :class="accountInfo.totalPnl >= 0 ? 'text-success' : 'text-danger'">
              {{ accountInfo.totalPnl >= 0 ? '+' : '' }}{{ formatPrice(accountInfo.totalPnl) }}
            </div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><t-icon name="swap" /></div>
          <div class="stat-info">
            <div class="stat-label">交易次数</div>
            <div class="stat-value">{{ accountInfo.tradeCount }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 持仓资产 -->
    <t-card title="持仓资产" :bordered="false" class="holdings-card">
      <t-table :data="holdings" :columns="holdingColumns" row-key="symbol" stripe hover>
        <template #symbol="{ row }">
          <div class="symbol-cell">
            <img :src="row.icon" class="coin-icon" />
            <div class="symbol-info">
              <span class="symbol-name">{{ row.symbol }}</span>
              <span class="symbol-fullname">{{ row.name }}</span>
            </div>
          </div>
        </template>
        <template #pnl="{ row }">
          <span :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
            {{ row.pnl >= 0 ? '+' : '' }}{{ formatPrice(row.pnl) }}
            ({{ row.pnlPercent >= 0 ? '+' : '' }}{{ row.pnlPercent.toFixed(2) }}%)
          </span>
        </template>
      </t-table>
    </t-card>
    
    <!-- 交易记录 -->
    <t-card title="交易记录" :bordered="false" class="history-card">
      <template #actions>
        <t-select v-model="historyType" size="small" style="width: 120px">
          <t-option value="all" label="全部" />
          <t-option value="buy" label="买入" />
          <t-option value="sell" label="卖出" />
        </t-select>
      </template>
      <t-table :data="filteredHistory" :columns="historyColumns" row-key="id" stripe>
        <template #type="{ row }">
          <t-tag :theme="row.type === 'buy' ? 'success' : 'danger'" size="small">
            {{ row.type === 'buy' ? '买入' : '卖出' }}
          </t-tag>
        </template>
        <template #pnl="{ row }">
          <span v-if="row.pnl !== null" :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
            {{ row.pnl >= 0 ? '+' : '' }}{{ formatPrice(row.pnl) }}
          </span>
          <span v-else>-</span>
        </template>
      </t-table>
    </t-card>
    
    <!-- 充值弹窗 -->
    <t-dialog v-model:visible="showRecharge" header="充值虚拟资金" @confirm="recharge">
      <t-form :data="rechargeForm" layout="vertical">
        <t-form-item label="充值金额">
          <t-input-number v-model="rechargeForm.amount" :min="1000" :max="1000000" :step="1000" theme="column" />
        </t-form-item>
        <div class="quick-amounts">
          <t-button v-for="a in [10000, 50000, 100000, 500000]" :key="a" variant="outline" size="small" @click="rechargeForm.amount = a">
            {{ a.toLocaleString() }}
          </t-button>
        </div>
        <t-alert theme="info">
          <p>虚拟资金仅用于模拟交易，不涉及真实资金。</p>
        </t-alert>
      </t-form>
    </t-dialog>
    
    <!-- 重置确认 -->
    <div class="page-footer">
      <t-button variant="outline" theme="danger" @click="showResetConfirm = true">
        <t-icon name="refresh" /> 重置账户
      </t-button>
    </div>
    
    <t-dialog v-model:visible="showResetConfirm" header="重置账户" theme="danger" @confirm="resetAccount">
      <p>确定要重置虚拟账户吗？此操作将清空所有持仓和交易记录，账户余额将重置为初始值。</p>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const showRecharge = ref(false)
const showResetConfirm = ref(false)
const historyType = ref('all')

// 账户信息
const accountInfo = ref({
  totalBalance: 156780.50,
  availableBalance: 98500.00,
  frozenBalance: 12500.00,
  totalPnl: 56780.50,
  todayPnl: 1280.30,
  todayPnlPercent: 0.82,
  tradeCount: 156
})

// 持仓数据
const holdings = ref([
  { symbol: 'BTC', name: 'Bitcoin', icon: 'https://cryptologos.cc/logos/bitcoin-btc-logo.png', amount: 1.25, avgPrice: 42500, currentPrice: 45230, value: 56537.5, pnl: 3412.5, pnlPercent: 6.43 },
  { symbol: 'ETH', name: 'Ethereum', icon: 'https://cryptologos.cc/logos/ethereum-eth-logo.png', amount: 15.5, avgPrice: 2350, currentPrice: 2480, value: 38440, pnl: 2015, pnlPercent: 5.53 },
  { symbol: 'SOL', name: 'Solana', icon: 'https://cryptologos.cc/logos/solana-sol-logo.png', amount: 100, avgPrice: 95, currentPrice: 98.5, value: 9850, pnl: 350, pnlPercent: 3.68 }
])

const holdingColumns = [
  { colKey: 'symbol', title: '币种', width: 180 },
  { colKey: 'amount', title: '持有数量', width: 120 },
  { colKey: 'avgPrice', title: '平均成本', width: 120, cell: (h, { row }) => `$${row.avgPrice.toLocaleString()}` },
  { colKey: 'currentPrice', title: '当前价格', width: 120, cell: (h, { row }) => `$${row.currentPrice.toLocaleString()}` },
  { colKey: 'value', title: '市值', width: 140, cell: (h, { row }) => `$${row.value.toLocaleString()}` },
  { colKey: 'pnl', title: '盈亏', width: 180 }
]

// 交易记录
const tradeHistory = ref([
  { id: 1, time: '2024-01-15 14:30:25', symbol: 'BTC/USDT', type: 'buy', price: 44850, amount: 0.5, total: 22425, pnl: null },
  { id: 2, time: '2024-01-15 10:15:32', symbol: 'ETH/USDT', type: 'sell', price: 2510, amount: 5, total: 12550, pnl: 250 },
  { id: 3, time: '2024-01-14 16:45:18', symbol: 'BTC/USDT', type: 'sell', price: 45100, amount: 0.3, total: 13530, pnl: 180 },
  { id: 4, time: '2024-01-14 09:22:45', symbol: 'SOL/USDT', type: 'buy', price: 95, amount: 50, total: 4750, pnl: null },
  { id: 5, time: '2024-01-13 20:10:33', symbol: 'ETH/USDT', type: 'buy', price: 2400, amount: 5, total: 12000, pnl: null }
])

const historyColumns = [
  { colKey: 'time', title: '时间', width: 180 },
  { colKey: 'symbol', title: '交易对', width: 120 },
  { colKey: 'type', title: '类型', width: 80 },
  { colKey: 'price', title: '价格', width: 120, cell: (h, { row }) => `$${row.price.toLocaleString()}` },
  { colKey: 'amount', title: '数量', width: 100 },
  { colKey: 'total', title: '总额', width: 140, cell: (h, { row }) => `$${row.total.toLocaleString()}` },
  { colKey: 'pnl', title: '盈亏', width: 120 }
]

const filteredHistory = computed(() => {
  if (historyType.value === 'all') return tradeHistory.value
  return tradeHistory.value.filter(t => t.type === historyType.value)
})

// 迷你图表
const miniChartOptions = {
  chart: { type: 'area', sparkline: { enabled: true }, background: 'transparent' },
  stroke: { curve: 'smooth', width: 2 },
  fill: { type: 'gradient', gradient: { opacityFrom: 0.5, opacityTo: 0 } },
  colors: ['#00A870']
}

const miniChartSeries = ref([{
  data: [100000, 102000, 105000, 103000, 108000, 112000, 115000, 118000, 120000, 125000, 130000, 135000, 140000, 145000, 150000, 156780]
}])

// 充值表单
const rechargeForm = ref({ amount: 50000 })

// 方法
const formatPrice = (p) => p?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'

const recharge = () => {
  accountInfo.value.totalBalance += rechargeForm.value.amount
  accountInfo.value.availableBalance += rechargeForm.value.amount
  showRecharge.value = false
  MessagePlugin.success(`成功充值 ${rechargeForm.value.amount.toLocaleString()} USDT`)
}

const resetAccount = () => {
  accountInfo.value = { totalBalance: 100000, availableBalance: 100000, frozenBalance: 0, totalPnl: 0, todayPnl: 0, todayPnlPercent: 0, tradeCount: 0 }
  holdings.value = []
  tradeHistory.value = []
  showResetConfirm.value = false
  MessagePlugin.success('账户已重置')
}
</script>

<style lang="less" scoped>
.virtual-account-page { padding: 24px; background: #0d1117; min-height: calc(100vh - 56px); }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
  .header-left { display: flex; align-items: center; gap: 16px;
    h1 { margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 8px; }
  }
}

.account-overview { margin-bottom: 24px; }

.balance-card { display: flex; justify-content: space-between; align-items: center; padding: 24px; background: linear-gradient(135deg, #161b22, #21262d); border-radius: 12px; margin-bottom: 16px;
  .balance-main {
    .balance-label { font-size: 14px; color: rgba(255,255,255,0.6); margin-bottom: 8px; }
    .balance-value { font-size: 36px; font-weight: bold; color: #fff; span { font-size: 18px; color: rgba(255,255,255,0.6); } }
    .balance-change { font-size: 14px; margin-top: 8px; &.positive { color: var(--green); } &.negative { color: var(--red); } }
  }
  .balance-chart { width: 200px; }
}

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  .stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: #161b22; border-radius: 12px;
    .stat-icon { width: 48px; height: 48px; background: rgba(0,82,217,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--primary); }
    .stat-info { .stat-label { font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 4px; } .stat-value { font-size: 18px; font-weight: 600; color: #fff; } }
  }
}

.text-success { color: var(--green) !important; }
.text-danger { color: var(--red) !important; }

.holdings-card, .history-card { margin-bottom: 24px;
  :deep(.t-card) { background: #161b22; border: none; }
}

.symbol-cell { display: flex; align-items: center; gap: 12px;
  .coin-icon { width: 32px; height: 32px; border-radius: 50%; }
  .symbol-info { display: flex; flex-direction: column;
    .symbol-name { font-weight: 500; color: #fff; }
    .symbol-fullname { font-size: 12px; color: rgba(255,255,255,0.5); }
  }
}

.quick-amounts { display: flex; gap: 8px; margin: 16px 0; }

.page-footer { padding: 24px; background: #161b22; border-radius: 12px; text-align: center; }
</style>
