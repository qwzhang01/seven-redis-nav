<template>
  <div class="backtest-result">
    <!-- 头部 -->
    <div class="result-header">
      <h1 class="page-title">回测报告 - 双均线趋势跟踪</h1>
      <div class="result-actions">
        <t-button variant="outline" @click="exportPDF">
          <t-icon name="file-pdf" /> 导出PDF
        </t-button>
        <t-button variant="outline" @click="exportExcel">
          <t-icon name="file-excel" /> 导出数据
        </t-button>
        <t-button theme="primary" @click="$router.push('/live-config')">
          <t-icon name="play-circle" /> 转入实盘
        </t-button>
      </div>
    </div>
    
    <!-- 回测参数 -->
    <div class="backtest-params">
      <t-tag>回测周期: 2024-01-01 ~ 2024-12-31</t-tag>
      <t-tag>交易对: BTC/USDT</t-tag>
      <t-tag>初始资金: 10,000 USDT</t-tag>
      <t-tag>手续费: 0.1%</t-tag>
    </div>
    
    <!-- 核心指标 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-value good">+45.6%</div>
        <div class="metric-label">累计收益</div>
      </div>
      <div class="metric-card">
        <div class="metric-value good">+36.2%</div>
        <div class="metric-label">年化收益</div>
      </div>
      <div class="metric-card">
        <div class="metric-value warn">-8.5%</div>
        <div class="metric-label">最大回撤</div>
      </div>
      <div class="metric-card">
        <div class="metric-value good">1.92</div>
        <div class="metric-label">夏普比率</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">65.8%</div>
        <div class="metric-label">胜率</div>
      </div>
      <div class="metric-card">
        <div class="metric-value">156</div>
        <div class="metric-label">交易次数</div>
      </div>
    </div>
    
    <!-- 图表 -->
    <div class="charts-row">
      <div class="chart-card">
        <div class="card-title">
          资金曲线
          <span class="legend">
            <span class="leg-item"><span class="dot blue"></span>策略</span>
            <span class="leg-item"><span class="dot gray"></span>持有BTC</span>
          </span>
        </div>
        <apexchart
          type="line"
          height="300"
          :options="equityChartOptions"
          :series="equityChartSeries"
        />
      </div>
      <div class="chart-card">
        <div class="card-title">回撤曲线</div>
        <apexchart
          type="area"
          height="300"
          :options="drawdownChartOptions"
          :series="drawdownChartSeries"
        />
      </div>
    </div>
    
    <div class="charts-row">
      <div class="chart-card">
        <div class="card-title">月度收益</div>
        <apexchart
          type="bar"
          height="250"
          :options="monthlyChartOptions"
          :series="monthlyChartSeries"
        />
      </div>
      <div class="chart-card">
        <div class="card-title">交易明细</div>
        <t-table
          :data="tradeDetails"
          :columns="tradeColumns"
          row-key="id"
          hover
          stripe
          size="small"
          max-height="250"
        >
          <template #side="{ row }">
            <span :class="row.side">{{ row.side === 'buy' ? '买入' : '卖出' }}</span>
          </template>
          <template #pnl="{ row }">
            <span :class="row.pnl >= 0 ? 'positive' : 'negative'">
              {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl }}
            </span>
          </template>
        </t-table>
        <div class="view-all">
          <t-link theme="primary" @click="showAllTrades">查看全部 156 条交易记录 →</t-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

// 图表配置
const equityChartOptions = {
  chart: { toolbar: { show: false }, zoom: { enabled: false } },
  colors: ['#125FFF', '#999'],
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { type: 'datetime', labels: { style: { colors: '#666' } } },
  yaxis: { labels: { style: { colors: '#666' }, formatter: (val) => val.toFixed(0) } },
  grid: { borderColor: '#e7e7e7' },
  legend: { show: false },
  tooltip: { x: { format: 'yyyy-MM-dd' } }
}

const equityChartSeries = ref([
  { name: '策略', data: generateEquityData(1.5) },
  { name: '持有BTC', data: generateEquityData(1.2) }
])

const drawdownChartOptions = {
  chart: { toolbar: { show: false }, zoom: { enabled: false } },
  colors: ['#E34D59'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] } },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { type: 'datetime', labels: { style: { colors: '#666' } } },
  yaxis: { labels: { style: { colors: '#666' }, formatter: (val) => val.toFixed(1) + '%' } },
  grid: { borderColor: '#e7e7e7' }
}

const drawdownChartSeries = ref([{
  name: '回撤',
  data: generateDrawdownData()
}])

const monthlyChartOptions = {
  chart: { toolbar: { show: false } },
  colors: ['#00A870'],
  plotOptions: {
    bar: {
      borderRadius: 4,
      colors: {
        ranges: [{ from: -100, to: 0, color: '#E34D59' }]
      }
    }
  },
  xaxis: { categories: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'] },
  yaxis: { labels: { formatter: (val) => val + '%' } },
  grid: { borderColor: '#e7e7e7' }
}

const monthlyChartSeries = ref([{
  name: '月收益',
  data: [4.5, -2.1, 6.8, 3.2, 8.5, -1.5, 5.2, 9.8, 4.1, -3.2, 7.2, 5.1]
}])

// 交易明细
const tradeDetails = ref([
  { id: 1, time: '12-28 14:00', side: 'buy', price: 42500, amount: 0.12, pnl: 180 },
  { id: 2, time: '12-25 09:00', side: 'sell', price: 43200, amount: 0.10, pnl: 85 },
  { id: 3, time: '12-22 16:00', side: 'buy', price: 41800, amount: 0.15, pnl: -45 },
  { id: 4, time: '12-18 11:00', side: 'sell', price: 42100, amount: 0.08, pnl: 120 },
  { id: 5, time: '12-15 08:00', side: 'buy', price: 40500, amount: 0.20, pnl: 320 }
])

const tradeColumns = [
  { colKey: 'time', title: '时间', width: 100 },
  { colKey: 'side', title: '方向', width: 60, cell: 'side' },
  { colKey: 'price', title: '价格', width: 80 },
  { colKey: 'amount', title: '数量', width: 60 },
  { colKey: 'pnl', title: '盈亏', width: 80, cell: 'pnl' }
]

// 生成数据
function generateEquityData(growth = 1) {
  const data = []
  let value = 10000
  const now = Date.now()
  for (let i = 365; i >= 0; i--) {
    const time = now - i * 86400000
    value = value * (1 + (Math.random() - 0.48) * 0.02 * growth)
    data.push([time, value])
  }
  return data
}

function generateDrawdownData() {
  const equityData = generateEquityData()
  let peak = equityData[0][1]
  return equityData.map(([time, value]) => {
    if (value > peak) peak = value
    return [time, ((value - peak) / peak) * 100]
  })
}

// 操作方法
const exportPDF = () => MessagePlugin.success('PDF报告导出成功')
const exportExcel = () => MessagePlugin.success('Excel数据导出成功')
const showAllTrades = () => MessagePlugin.info('查看全部156条交易记录')
</script>

<style lang="less" scoped>
.backtest-result {
  background: var(--bg);
  min-height: calc(100vh - 56px);
  padding: 24px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.result-actions {
  display: flex;
  gap: 12px;
}

.backtest-params {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  
  .metric-value {
    font-size: 24px;
    font-weight: bold;
    
    &.good { color: var(--green); }
    &.warn { color: var(--warning); }
    &.bad { color: var(--red); }
  }
  
  .metric-label {
    font-size: 13px;
    color: var(--text2);
    margin-top: 8px;
  }
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .legend {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: var(--text2);
    
    .leg-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      
      &.blue { background: #125FFF; }
      &.gray { background: #999; }
    }
  }
}

.view-all {
  margin-top: 12px;
  text-align: center;
}

:deep(.t-table) {
  .buy { color: var(--green); }
  .sell { color: var(--red); }
  .positive { color: var(--green); }
  .negative { color: var(--red); }
}
</style>
