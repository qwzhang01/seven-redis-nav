<template>
  <div class="backtest-config">
    <div class="config-page">
      <h1 class="page-title">📊 策略回测配置</h1>
      
      <!-- 时间范围 -->
      <div class="config-section">
        <div class="section-title">📅 时间范围</div>
        <t-form :data="formData" label-width="100px">
          <t-row :gutter="20">
            <t-col :span="4">
              <t-form-item label="开始日期">
                <t-date-picker v-model="formData.startDate" />
              </t-form-item>
            </t-col>
            <t-col :span="4">
              <t-form-item label="结束日期">
                <t-date-picker v-model="formData.endDate" />
              </t-form-item>
            </t-col>
            <t-col :span="4">
              <t-form-item label="快速选择">
                <t-space>
                  <t-button
                    v-for="period in quickPeriods"
                    :key="period.value"
                    :theme="selectedPeriod === period.value ? 'primary' : 'default'"
                    variant="outline"
                    size="small"
                    @click="setQuickPeriod(period.value)"
                  >
                    {{ period.label }}
                  </t-button>
                </t-space>
              </t-form-item>
            </t-col>
          </t-row>
        </t-form>
      </div>
      
      <!-- 交易配置 -->
      <div class="config-section">
        <div class="section-title">💱 交易配置</div>
        <t-form :data="formData" label-width="100px">
          <t-row :gutter="20">
            <t-col :span="4">
              <t-form-item label="交易对">
                <t-select v-model="formData.pair">
                  <t-option value="BTC/USDT" label="BTC/USDT" />
                  <t-option value="ETH/USDT" label="ETH/USDT" />
                  <t-option value="BNB/USDT" label="BNB/USDT" />
                  <t-option value="SOL/USDT" label="SOL/USDT" />
                </t-select>
              </t-form-item>
            </t-col>
            <t-col :span="4">
              <t-form-item label="K线周期">
                <t-select v-model="formData.timeframe">
                  <t-option value="1m" label="1分钟" />
                  <t-option value="5m" label="5分钟" />
                  <t-option value="15m" label="15分钟" />
                  <t-option value="1h" label="1小时" />
                  <t-option value="4h" label="4小时" />
                  <t-option value="1d" label="日线" />
                </t-select>
              </t-form-item>
            </t-col>
            <t-col :span="4">
              <t-form-item label="初始资金">
                <t-input-number
                  v-model="formData.capital"
                  :min="100"
                  :step="1000"
                  theme="normal"
                >
                  <template #suffix>USDT</template>
                </t-input-number>
              </t-form-item>
            </t-col>
          </t-row>
        </t-form>
      </div>
      
      <!-- 高级参数 -->
      <div class="config-section">
        <div class="section-title">⚙️ 高级参数</div>
        <t-form :data="formData" label-width="100px">
          <t-row :gutter="20">
            <t-col :span="4">
              <t-form-item label="手续费率">
                <t-input-number
                  v-model="formData.commission"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :decimal-places="2"
                  theme="normal"
                >
                  <template #suffix>%</template>
                </t-input-number>
              </t-form-item>
            </t-col>
            <t-col :span="4">
              <t-form-item label="滑点">
                <t-input-number
                  v-model="formData.slippage"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :decimal-places="2"
                  theme="normal"
                >
                  <template #suffix>%</template>
                </t-input-number>
              </t-form-item>
            </t-col>
          </t-row>
          
          <t-row :gutter="20">
            <t-col :span="6">
              <t-form-item label="启用杠杆">
                <t-switch v-model="formData.enableLeverage" />
              </t-form-item>
            </t-col>
            <t-col :span="6">
              <t-form-item label="允许做空">
                <t-switch v-model="formData.enableShort" />
              </t-form-item>
            </t-col>
          </t-row>
        </t-form>
      </div>
      
      <!-- 进度条 -->
      <div v-if="isRunning" class="progress-section">
        <t-progress
          :percentage="progress"
          :color="{ from: '#125FFF', to: '#00A870' }"
        />
        <div class="progress-info">
          <span>{{ progress }}%</span>
          <span>{{ progressText }}</span>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="btn-group">
        <t-button variant="outline" @click="$router.back()">取消</t-button>
        <t-button variant="outline" @click="$router.push('/strategy-dev')">
          <t-icon name="edit" /> 编辑策略
        </t-button>
        <t-button theme="primary" :loading="isRunning" @click="startBacktest">
          <t-icon name="play-circle" /> 开始回测
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import dayjs from 'dayjs'

const router = useRouter()

const isRunning = ref(false)
const progress = ref(0)
const progressText = ref('')
const selectedPeriod = ref('1y')

const formData = reactive({
  startDate: dayjs().subtract(1, 'year').format('YYYY-MM-DD'),
  endDate: dayjs().format('YYYY-MM-DD'),
  pair: 'BTC/USDT',
  timeframe: '1h',
  capital: 10000,
  commission: 0.1,
  slippage: 0.05,
  enableLeverage: false,
  enableShort: false
})

const quickPeriods = [
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近3月' },
  { value: '180d', label: '近半年' },
  { value: '1y', label: '近1年' }
]

const setQuickPeriod = (period) => {
  selectedPeriod.value = period
  const days = { '30d': 30, '90d': 90, '180d': 180, '1y': 365 }
  formData.startDate = dayjs().subtract(days[period], 'day').format('YYYY-MM-DD')
  formData.endDate = dayjs().format('YYYY-MM-DD')
  MessagePlugin.info(`已设置回测周期: ${quickPeriods.find(p => p.value === period).label}`)
}

const stages = [
  '加载历史数据...',
  '解析K线数据...',
  '初始化策略...',
  '执行回测计算...',
  '生成统计报告...',
  '完成！'
]

const startBacktest = () => {
  isRunning.value = true
  progress.value = 0
  
  const interval = setInterval(() => {
    progress.value += Math.random() * 8 + 2
    
    const stageIndex = Math.floor(progress.value / 20)
    progressText.value = stages[Math.min(stageIndex, stages.length - 1)]
    
    if (progress.value >= 100) {
      progress.value = 100
      clearInterval(interval)
      progressText.value = '回测完成！正在生成报告...'
      
      setTimeout(() => {
        isRunning.value = false
        MessagePlugin.success('回测完成！')
        router.push('/backtest-result')
      }, 500)
    }
  }, 300)
}
</script>

<style lang="less" scoped>
.backtest-config {
  background: var(--bg);
  min-height: calc(100vh - 56px);
}

.config-page {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.config-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.progress-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  
  .progress-info {
    display: flex;
    justify-content: space-between;
    margin-top: 12px;
    font-size: 14px;
    color: var(--text2);
  }
}

.btn-group {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
