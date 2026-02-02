<template>
  <div class="my-strategy">
    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">我的策略</h1>
        <div class="header-actions">
          <t-button @click="$router.push('/backtest')">
            <t-icon name="add" /> 新建策略
          </t-button>
        </div>
      </div>
      
      <!-- 模式切换 -->
      <div class="mode-tabs">
        <t-radio-group v-model="strategyMode" variant="default-filled">
          <t-radio-button value="live">
            <t-icon name="play-circle" /> 实盘策略
          </t-radio-button>
          <t-radio-button value="paper">
            <t-icon name="file-paste" /> 模拟策略
          </t-radio-button>
        </t-radio-group>
      </div>
      
      <!-- 策略列表 -->
      <div class="strategy-list">
        <div
          v-for="strategy in currentStrategies"
          :key="strategy.id"
          class="strategy-item"
        >
          <div class="strategy-header">
            <div class="strategy-info">
              <t-icon name="app" size="24px" class="strategy-icon" />
              <div>
                <div class="strategy-name">{{ strategy.name }}</div>
                <div class="strategy-pair">{{ strategy.pair }}</div>
              </div>
            </div>
            <t-tag :theme="getStatusTheme(strategy.status)" variant="light">
              {{ getStatusText(strategy.status) }}
            </t-tag>
          </div>
          
          <div class="strategy-stats">
            <div class="stat">
              <div class="stat-label">累计收益</div>
              <div class="stat-value" :class="strategy.totalReturn >= 0 ? 'positive' : 'negative'">
                {{ strategy.totalReturn >= 0 ? '+' : '' }}{{ strategy.totalReturn }}%
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">今日收益</div>
              <div class="stat-value" :class="strategy.todayReturn >= 0 ? 'positive' : 'negative'">
                {{ strategy.todayReturn >= 0 ? '+' : '' }}{{ strategy.todayReturn }}%
              </div>
            </div>
            <div class="stat">
              <div class="stat-label">投入资金</div>
              <div class="stat-value">{{ formatMoney(strategy.capital) }} USDT</div>
            </div>
            <div class="stat">
              <div class="stat-label">运行时长</div>
              <div class="stat-value">{{ strategy.runtime }}</div>
            </div>
          </div>
          
          <div class="strategy-actions">
            <t-button variant="text" @click="viewDetail(strategy.id)">
              <t-icon name="chart-line" /> 详情
            </t-button>
            <t-button
              v-if="strategy.status === 'running'"
              variant="text"
              theme="warning"
              @click="pauseStrategy(strategy.id)"
            >
              <t-icon name="pause" /> 暂停
            </t-button>
            <t-button
              v-else-if="strategy.status === 'paused'"
              variant="text"
              theme="success"
              @click="resumeStrategy(strategy.id)"
            >
              <t-icon name="play" /> 恢复
            </t-button>
            <t-button variant="text" theme="danger" @click="stopStrategy(strategy.id)">
              <t-icon name="poweroff" /> 停止
            </t-button>
          </div>
        </div>
        
        <!-- 空状态 -->
        <t-empty v-if="currentStrategies.length === 0" description="暂无运行中的策略">
          <t-button @click="$router.push('/strategy')">去策略广场看看</t-button>
        </t-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'

const router = useRouter()

const strategyMode = ref('live')

// 实盘策略
const liveStrategies = ref([
  {
    id: 1,
    name: '双均线趋势跟踪',
    pair: 'BTC/USDT',
    status: 'running',
    totalReturn: 12.5,
    todayReturn: 0.85,
    capital: 10000,
    runtime: '5天12小时'
  },
  {
    id: 2,
    name: 'ETH网格交易',
    pair: 'ETH/USDT',
    status: 'paused',
    totalReturn: 8.2,
    todayReturn: 0,
    capital: 5000,
    runtime: '3天8小时'
  }
])

// 模拟策略
const paperStrategies = ref([
  {
    id: 101,
    name: 'MACD趋势策略（测试）',
    pair: 'BTC/USDT',
    status: 'running',
    totalReturn: 15.8,
    todayReturn: 1.2,
    capital: 10000,
    runtime: '7天'
  }
])

// 当前显示的策略
const currentStrategies = computed(() => {
  return strategyMode.value === 'live' ? liveStrategies.value : paperStrategies.value
})

// 状态相关
const getStatusTheme = (status) => {
  const themes = { running: 'success', paused: 'warning', stopped: 'default' }
  return themes[status] || 'default'
}

const getStatusText = (status) => {
  const texts = { running: '🟢 运行中', paused: '🟡 已暂停', stopped: '⚪ 已停止' }
  return texts[status] || ''
}

const formatMoney = (value) => {
  return value.toLocaleString('en-US')
}

// 操作方法
const viewDetail = (id) => {
  router.push('/live-monitor')
}

const pauseStrategy = (id) => {
  DialogPlugin.confirm({
    header: '暂停策略',
    body: '确定要暂停这个策略吗？',
    onConfirm: () => {
      const strategy = liveStrategies.value.find(s => s.id === id) || paperStrategies.value.find(s => s.id === id)
      if (strategy) strategy.status = 'paused'
      MessagePlugin.success('策略已暂停')
    }
  })
}

const resumeStrategy = (id) => {
  const strategy = liveStrategies.value.find(s => s.id === id) || paperStrategies.value.find(s => s.id === id)
  if (strategy) strategy.status = 'running'
  MessagePlugin.success('策略已恢复运行')
}

const stopStrategy = (id) => {
  DialogPlugin.confirm({
    header: '停止策略',
    body: '确定要停止这个策略吗？此操作不可撤销。',
    theme: 'danger',
    onConfirm: () => {
      const list = strategyMode.value === 'live' ? liveStrategies : paperStrategies
      const index = list.value.findIndex(s => s.id === id)
      if (index > -1) list.value.splice(index, 1)
      MessagePlugin.success('策略已停止')
    }
  })
}
</script>

<style lang="less" scoped>
.my-strategy {
  background: var(--bg);
  min-height: calc(100vh - 56px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.mode-tabs {
  margin-bottom: 24px;
}

.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strategy-item {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.strategy-info {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .strategy-icon {
    color: var(--brand);
  }
  
  .strategy-name {
    font-size: 16px;
    font-weight: 600;
  }
  
  .strategy-pair {
    font-size: 13px;
    color: var(--text2);
    margin-top: 4px;
  }
}

.strategy-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 16px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
  
  .stat {
    text-align: center;
    
    .stat-label {
      font-size: 13px;
      color: var(--text2);
      margin-bottom: 4px;
    }
    
    .stat-value {
      font-size: 16px;
      font-weight: 600;
      
      &.positive { color: var(--green); }
      &.negative { color: var(--red); }
    }
  }
}

.strategy-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
