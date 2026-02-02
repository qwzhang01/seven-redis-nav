<template>
  <div class="strategy-detail">
    <!-- 面包屑 -->
    <div class="breadcrumb">
      <t-breadcrumb>
        <t-breadcrumb-item to="/strategy">策略广场</t-breadcrumb-item>
        <t-breadcrumb-item>{{ strategy.name }}</t-breadcrumb-item>
      </t-breadcrumb>
    </div>
    
    <!-- 策略头部 -->
    <div class="detail-header">
      <div class="detail-info">
        <div class="detail-icon">
          <t-icon name="app" size="40px" />
        </div>
        <div>
          <h1>{{ strategy.name }}</h1>
          <div class="detail-meta">
            {{ strategy.type }} |
            <t-tag :theme="getRiskTheme(strategy.risk)" variant="light" size="small">
              {{ getRiskText(strategy.risk) }}
            </t-tag>
            | 订阅: {{ formatNumber(strategy.subscribers) }}
          </div>
        </div>
      </div>
      <div class="detail-actions">
        <t-button variant="outline" @click="toggleFavorite">
          <t-icon :name="isFavorite ? 'star-filled' : 'star'" />
          {{ isFavorite ? '已收藏' : '收藏' }}
        </t-button>
        <t-button variant="outline" @click="$router.push('/backtest')">
          <t-icon name="chart-bar" /> 回测
        </t-button>
        <t-button theme="primary" @click="$router.push('/live-config')">
          <t-icon name="play-circle" /> 实盘
        </t-button>
      </div>
    </div>
    
    <!-- Tab切换 -->
    <t-tabs v-model="activeTab" class="detail-tabs">
      <t-tab-panel value="intro" label="策略说明" />
      <t-tab-panel value="performance" label="绩效分析" />
      <t-tab-panel value="backtest" label="回测报告" />
      <t-tab-panel value="reviews" label="用户评价" />
    </t-tabs>
    
    <!-- Tab内容 -->
    <div class="tab-content">
      <!-- 策略说明 -->
      <div v-if="activeTab === 'intro'" class="intro-content">
        <!-- 核心指标 -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-value positive">+125.6%</div>
            <div class="stat-label">累计收益</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">1.85</div>
            <div class="stat-label">夏普比率</div>
          </div>
          <div class="stat-card">
            <div class="stat-value negative">-12.3%</div>
            <div class="stat-label">最大回撤</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">68.5%</div>
            <div class="stat-label">胜率</div>
          </div>
        </div>
        
        <div class="intro-grid">
          <!-- 收益曲线 -->
          <div class="chart-card">
            <div class="card-title">收益曲线</div>
            <apexchart
              type="area"
              height="250"
              :options="equityChartOptions"
              :series="equityChartSeries"
            />
          </div>
          
          <!-- 策略简介 -->
          <div class="chart-card">
            <div class="card-title">策略简介</div>
            <div class="strategy-intro">
              <p><strong>策略原理：</strong>基于双均线交叉信号进行趋势跟踪交易。当短期均线（MA5）上穿长期均线（MA20）时产生买入信号，下穿时产生卖出信号。</p>
              <p><strong>适用市场：</strong>BTC/USDT、ETH/USDT等主流交易对</p>
              <p><strong>建议资金：</strong>≥ 1,000 USDT</p>
              <p><strong>策略特点：</strong></p>
              <ul>
                <li>✅ 趋势行情表现优异</li>
                <li>✅ 回撤控制相对稳定</li>
                <li>⚠️ 震荡行情可能产生假信号</li>
              </ul>
            </div>
          </div>
        </div>
        
        <!-- 历史交易记录 -->
        <div class="chart-card">
          <div class="card-title">历史交易记录</div>
          <t-table
            :data="tradeHistory"
            :columns="tradeColumns"
            row-key="id"
            hover
            stripe
          >
            <template #side="{ row }">
              <span :class="row.side">{{ row.side === 'buy' ? '买入' : '卖出' }}</span>
            </template>
            <template #pnl="{ row }">
              <span :class="row.pnl >= 0 ? 'positive' : 'negative'">
                {{ row.pnl >= 0 ? '+' : '' }}{{ row.pnl }} USDT
              </span>
            </template>
            <template #returnRate="{ row }">
              <span :class="row.returnRate >= 0 ? 'positive' : 'negative'">
                {{ row.returnRate >= 0 ? '+' : '' }}{{ row.returnRate }}%
              </span>
            </template>
          </t-table>
        </div>
      </div>
      
      <!-- 绩效分析 -->
      <div v-if="activeTab === 'performance'" class="performance-content">
        <!-- 周期选择 -->
        <div class="period-selector">
          <t-radio-group v-model="performancePeriod" variant="default-filled">
            <t-radio-button value="7d">近7天</t-radio-button>
            <t-radio-button value="30d">近30天</t-radio-button>
            <t-radio-button value="90d">近90天</t-radio-button>
            <t-radio-button value="1y">近1年</t-radio-button>
            <t-radio-button value="all">全部</t-radio-button>
          </t-radio-group>
        </div>
        
        <!-- 指标网格 -->
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-value good">+125.6%</div>
            <div class="metric-label">累计收益</div>
          </div>
          <div class="metric-card">
            <div class="metric-value good">+89.3%</div>
            <div class="metric-label">年化收益</div>
          </div>
          <div class="metric-card">
            <div class="metric-value warn">-12.3%</div>
            <div class="metric-label">最大回撤</div>
          </div>
          <div class="metric-card">
            <div class="metric-value good">1.85</div>
            <div class="metric-label">夏普比率</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">68.5%</div>
            <div class="metric-label">胜率</div>
          </div>
          <div class="metric-card">
            <div class="metric-value good">2.15</div>
            <div class="metric-label">盈亏比</div>
          </div>
        </div>
        
        <!-- 图表 -->
        <div class="charts-row">
          <div class="chart-card">
            <div class="card-title">累计收益曲线</div>
            <apexchart
              type="area"
              height="250"
              :options="equityChartOptions"
              :series="equityChartSeries"
            />
          </div>
          <div class="chart-card">
            <div class="card-title">回撤曲线</div>
            <apexchart
              type="area"
              height="250"
              :options="drawdownChartOptions"
              :series="drawdownChartSeries"
            />
          </div>
        </div>
        
        <!-- 月度收益 -->
        <div class="charts-row">
          <div class="chart-card">
            <div class="card-title">月度收益分布</div>
            <apexchart
              type="bar"
              height="250"
              :options="monthlyChartOptions"
              :series="monthlyChartSeries"
            />
          </div>
          <div class="chart-card">
            <div class="card-title">详细指标</div>
            <div class="metrics-detail">
              <div class="metric-row">
                <span class="label">总交易次数</span>
                <span class="value">256 次</span>
              </div>
              <div class="metric-row">
                <span class="label">盈利次数</span>
                <span class="value positive">175 次</span>
              </div>
              <div class="metric-row">
                <span class="label">亏损次数</span>
                <span class="value negative">81 次</span>
              </div>
              <div class="metric-row">
                <span class="label">平均持仓时间</span>
                <span class="value">4.2 小时</span>
              </div>
              <div class="metric-row">
                <span class="label">平均盈利</span>
                <span class="value positive">+2.35%</span>
              </div>
              <div class="metric-row">
                <span class="label">平均亏损</span>
                <span class="value negative">-1.12%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 用户评价 -->
      <div v-if="activeTab === 'reviews'" class="reviews-content">
        <!-- 评分概览 -->
        <div class="review-summary">
          <div class="rating-overview">
            <div class="big-rating">4.6<span class="max">/5</span></div>
            <t-rate :value="4.6" :count="5" allow-half disabled />
            <div class="total-reviews">共 328 条评价</div>
          </div>
          <div class="rating-bars">
            <div class="rating-row" v-for="n in 5" :key="n">
              <span class="star">{{ 6 - n }}星</span>
              <t-progress
                :percentage="[65, 22, 8, 3, 2][n - 1]"
                :color="{ from: '#00A870', to: '#00A870' }"
              />
              <span class="pct">{{ [65, 22, 8, 3, 2][n - 1] }}%</span>
            </div>
          </div>
        </div>
        
        <!-- 评价列表 -->
        <div class="review-list">
          <div class="review-item" v-for="review in reviews" :key="review.id">
            <div class="review-header">
              <div class="reviewer">
                <t-avatar size="36px">{{ review.user.charAt(0) }}</t-avatar>
                <div>
                  <span class="reviewer-name">{{ review.user }}</span>
                  <t-tag v-if="review.vip" size="small" theme="warning">VIP用户</t-tag>
                </div>
              </div>
              <div class="review-meta">
                <t-rate :value="review.rating" :count="5" allow-half disabled size="small" />
                <span class="date">{{ review.date }}</span>
              </div>
            </div>
            <div class="review-content">{{ review.content }}</div>
            <div class="review-stats">
              <span>使用时长: {{ review.duration }}天</span>
              <span>实盘收益: <span :class="review.profit >= 0 ? 'positive' : 'negative'">
                {{ review.profit >= 0 ? '+' : '' }}{{ review.profit }}%
              </span></span>
            </div>
            <div class="review-footer">
              <t-button variant="text" size="small">
                <t-icon name="thumb-up" /> 有用 ({{ review.helpful }})
              </t-button>
              <t-button variant="text" size="small">
                <t-icon name="chat" /> 回复 ({{ review.replies }})
              </t-button>
            </div>
          </div>
        </div>
        
        <!-- 发表评价 -->
        <div class="write-review">
          <h3>📝 撰写评价</h3>
          <div class="rating-select">
            <span>评分：</span>
            <t-rate v-model="newReview.rating" :count="5" />
          </div>
          <t-textarea
            v-model="newReview.content"
            placeholder="分享您的使用体验...（至少20字）"
            :maxlength="500"
          />
          <t-button theme="primary" @click="submitReview">提交评价</t-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'

const route = useRoute()
const router = useRouter()

const activeTab = ref('intro')
const isFavorite = ref(false)
const performancePeriod = ref('30d')

// 策略数据
const strategy = ref({
  id: 1,
  name: '双均线趋势跟踪',
  type: '趋势跟踪',
  risk: 'medium',
  subscribers: 1234
})

// 交易历史
const tradeHistory = ref([
  { id: 1, time: '2025-01-15 14:30', pair: 'BTC/USDT', side: 'buy', openPrice: 45000, closePrice: 45680, amount: 0.1, pnl: 68, returnRate: 1.51 },
  { id: 2, time: '2025-01-14 09:15', pair: 'BTC/USDT', side: 'sell', openPrice: 44800, closePrice: 44500, amount: 0.08, pnl: 24, returnRate: 0.67 },
  { id: 3, time: '2025-01-13 16:45', pair: 'BTC/USDT', side: 'buy', openPrice: 44200, closePrice: 44100, amount: 0.12, pnl: -12, returnRate: -0.23 }
])

const tradeColumns = [
  { colKey: 'time', title: '时间', width: 150 },
  { colKey: 'pair', title: '交易对', width: 100 },
  { colKey: 'side', title: '方向', width: 80, cell: 'side' },
  { colKey: 'openPrice', title: '开仓价', width: 100 },
  { colKey: 'closePrice', title: '平仓价', width: 100 },
  { colKey: 'amount', title: '数量', width: 80 },
  { colKey: 'pnl', title: '盈亏', width: 100, cell: 'pnl' },
  { colKey: 'returnRate', title: '收益率', width: 100, cell: 'returnRate' }
]

// 用户评价
const reviews = ref([
  { id: 1, user: '李*明', vip: true, rating: 5, date: '2025-01-12', content: '策略非常稳定，使用3个月了，累计收益18%，回撤控制得很好。趋势行情下表现优异，推荐！', duration: 92, profit: 18.5, helpful: 56, replies: 3 },
  { id: 2, user: '王*华', vip: false, rating: 5, date: '2025-01-10', content: '双均线策略经典有效，这个实现版本参数优化得不错，比我自己写的效果好很多。', duration: 45, profit: 12.3, helpful: 42, replies: 1 }
])

// 新评价
const newReview = reactive({
  rating: 5,
  content: ''
})

// 图表配置
const equityChartOptions = {
  chart: { 
    toolbar: { show: false }, 
    zoom: { enabled: false },
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  colors: ['#00A870'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] } },
  stroke: { curve: 'smooth', width: 2 },
  dataLabels: { enabled: false },
  xaxis: { 
    type: 'datetime', 
    labels: { 
      style: { colors: '#666' },
      datetimeFormatter: { year: 'yyyy', month: "MMM 'yy", day: 'dd MMM' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: { 
    labels: { 
      style: { colors: '#666' }, 
      formatter: (val) => '$' + (val / 1000).toFixed(1) + 'k'
    }
  },
  grid: { borderColor: '#e7e7e7', strokeDashArray: 4 },
  tooltip: { 
    x: { format: 'yyyy-MM-dd' },
    y: { formatter: (val) => '$' + val.toFixed(2) }
  },
  markers: { size: 0, hover: { size: 5 } }
}

const equityChartSeries = ref([{
  name: '收益',
  data: generateEquityData()
}])

const drawdownChartOptions = {
  chart: { 
    toolbar: { show: false }, 
    zoom: { enabled: false },
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  colors: ['#E34D59'],
  fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] } },
  stroke: { curve: 'smooth', width: 2 },
  dataLabels: { enabled: false },
  xaxis: { 
    type: 'datetime', 
    labels: { 
      style: { colors: '#666' },
      datetimeFormatter: { year: 'yyyy', month: "MMM 'yy", day: 'dd MMM' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: { 
    labels: { 
      style: { colors: '#666' }, 
      formatter: (val) => val.toFixed(1) + '%'
    }
  },
  grid: { borderColor: '#e7e7e7', strokeDashArray: 4 },
  tooltip: { 
    x: { format: 'yyyy-MM-dd' },
    y: { formatter: (val) => val.toFixed(2) + '%' }
  },
  markers: { size: 0, hover: { size: 5 } }
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
      colors: {
        ranges: [{ from: -100, to: 0, color: '#E34D59' }]
      }
    }
  },
  xaxis: { categories: ['1月', '2月', '3月', '4月', '5月', '6月'] },
  yaxis: { labels: { formatter: (val) => val + '%' } }
}

const monthlyChartSeries = ref([{
  name: '月收益',
  data: [8.5, -2.1, 6.8, 3.2, 8.5, -1.5]
}])

// 生成收益数据
function generateEquityData() {
  const data = []
  let value = 10000
  const now = Date.now()
  for (let i = 180; i >= 0; i--) {
    const time = now - i * 86400000
    value = value * (1 + (Math.random() - 0.48) * 0.02)
    data.push([time, value])
  }
  return data
}

// 生成回撤数据
function generateDrawdownData() {
  const equityData = generateEquityData()
  let peak = equityData[0][1]
  return equityData.map(([time, value]) => {
    if (value > peak) peak = value
    return [time, ((value - peak) / peak) * 100]
  })
}

// 工具函数
const getRiskTheme = (risk) => {
  const themes = { low: 'success', medium: 'warning', high: 'danger' }
  return themes[risk] || 'default'
}

const getRiskText = (risk) => {
  const texts = { low: '🟢 低风险', medium: '🟡 中风险', high: '🔴 高风险' }
  return texts[risk] || ''
}

const formatNumber = (num) => num.toLocaleString('en-US')

const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  MessagePlugin.success(isFavorite.value ? '已收藏' : '已取消收藏')
}

const submitReview = () => {
  if (newReview.content.length < 20) {
    MessagePlugin.warning('评价内容至少20字')
    return
  }
  MessagePlugin.success('评价提交成功！')
  newReview.content = ''
}
</script>

<style lang="less" scoped>
.strategy-detail {
  background: var(--bg);
  min-height: calc(100vh - 56px);
}

.breadcrumb {
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.detail-header {
  padding: 24px;
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-info {
  display: flex;
  gap: 20px;
  align-items: center;
  
  h1 {
    font-size: 24px;
    margin-bottom: 8px;
  }
}

.detail-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--brand), #5d9efe);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.detail-meta {
  font-size: 14px;
  color: var(--text2);
}

.detail-actions {
  display: flex;
  gap: 12px;
}

.detail-tabs {
  background: #fff;
  padding: 0 24px;
  border-bottom: 1px solid var(--border);
}

.tab-content {
  padding: 24px;
}

// 统计卡片
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  
  .stat-value {
    font-size: 28px;
    font-weight: bold;
    
    &.positive { color: var(--green); }
    &.negative { color: var(--red); }
  }
  
  .stat-label {
    font-size: 14px;
    color: var(--text2);
    margin-top: 8px;
  }
}

// 指标网格
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

// 图表卡片
.chart-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  
  .card-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }
}

.intro-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.strategy-intro {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text);
  
  p {
    margin-bottom: 12px;
  }
  
  ul {
    padding-left: 20px;
  }
}

.period-selector {
  margin-bottom: 24px;
}

.metrics-detail {
  .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      color: var(--text2);
    }
    
    .positive { color: var(--green); }
    .negative { color: var(--red); }
  }
}

// 评价样式
.review-summary {
  display: flex;
  gap: 40px;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.rating-overview {
  text-align: center;
  
  .big-rating {
    font-size: 48px;
    font-weight: bold;
    
    .max {
      font-size: 24px;
      color: var(--text2);
    }
  }
  
  .total-reviews {
    margin-top: 8px;
    color: var(--text2);
  }
}

.rating-bars {
  flex: 1;
  
  .rating-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    
    .star {
      width: 40px;
    }
    
    .t-progress {
      flex: 1;
    }
    
    .pct {
      width: 40px;
      text-align: right;
    }
  }
}

.review-list {
  margin-bottom: 24px;
}

.review-item {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  
  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .reviewer {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .reviewer-name {
    font-weight: 500;
    margin-right: 8px;
  }
  
  .review-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .date {
      color: var(--text2);
      font-size: 13px;
    }
  }
  
  .review-content {
    margin-bottom: 12px;
    line-height: 1.6;
  }
  
  .review-stats {
    display: flex;
    gap: 24px;
    font-size: 13px;
    color: var(--text2);
    margin-bottom: 12px;
    
    .positive { color: var(--green); }
    .negative { color: var(--red); }
  }
  
  .review-footer {
    display: flex;
    gap: 16px;
  }
}

.write-review {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  
  h3 {
    margin-bottom: 16px;
  }
  
  .rating-select {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }
  
  .t-textarea {
    margin-bottom: 16px;
  }
}

// 表格样式
:deep(.t-table) {
  .buy { color: var(--green); }
  .sell { color: var(--red); }
  .positive { color: var(--green); }
  .negative { color: var(--red); }
}
</style>
