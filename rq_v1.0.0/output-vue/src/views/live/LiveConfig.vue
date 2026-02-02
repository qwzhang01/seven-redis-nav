<template>
  <div class="live-config-page">
    <div class="page-header">
      <div class="header-title">
        <t-icon name="dashboard" class="header-icon" />
        <h1>实盘配置</h1>
      </div>
      <p class="header-desc">配置并启动您的自动化交易策略</p>
    </div>
    
    <!-- 配置步骤 -->
    <div class="config-steps">
      <t-steps :current="currentStep" theme="dot">
        <t-step-item title="选择策略" content="选择要运行的交易策略" />
        <t-step-item title="选择交易所" content="配置交易所API" />
        <t-step-item title="资金配置" content="设置交易资金和风控" />
        <t-step-item title="确认启动" content="检查配置并启动" />
      </t-steps>
    </div>
    
    <!-- 配置内容 -->
    <div class="config-content">
      <!-- 步骤1: 选择策略 -->
      <div v-show="currentStep === 0" class="step-panel">
        <t-card title="选择交易策略" :bordered="false">
          <div class="strategy-selector">
            <t-radio-group v-model="selectedStrategy" variant="primary-filled">
              <div class="strategy-options">
                <div 
                  v-for="strategy in availableStrategies" 
                  :key="strategy.id"
                  class="strategy-option"
                  :class="{ selected: selectedStrategy === strategy.id }"
                  @click="selectedStrategy = strategy.id"
                >
                  <t-radio :value="strategy.id" />
                  <div class="strategy-info">
                    <div class="strategy-name">
                      {{ strategy.name }}
                      <t-tag v-if="strategy.isOwned" theme="primary" size="small">已购买</t-tag>
                      <t-tag v-if="strategy.isCustom" theme="success" size="small">自定义</t-tag>
                    </div>
                    <div class="strategy-desc">{{ strategy.description }}</div>
                    <div class="strategy-stats">
                      <span class="stat">
                        <t-icon name="chart-line" />
                        收益率: <b class="text-success">+{{ strategy.returns }}%</b>
                      </span>
                      <span class="stat">
                        <t-icon name="trending-down" />
                        最大回撤: <b class="text-danger">-{{ strategy.drawdown }}%</b>
                      </span>
                      <span class="stat">
                        <t-icon name="time" />
                        运行: {{ strategy.runningDays }}天
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </t-radio-group>
          </div>
        </t-card>
      </div>
      
      <!-- 步骤2: 选择交易所 -->
      <div v-show="currentStep === 1" class="step-panel">
        <t-card title="配置交易所" :bordered="false">
          <div class="exchange-list">
            <div 
              v-for="exchange in exchanges" 
              :key="exchange.id"
              class="exchange-item"
              :class="{ selected: selectedExchange === exchange.id, connected: exchange.connected }"
              @click="selectExchange(exchange)"
            >
              <div class="exchange-logo">
                <img :src="exchange.logo" :alt="exchange.name" />
              </div>
              <div class="exchange-info">
                <div class="exchange-name">{{ exchange.name }}</div>
                <div class="exchange-status">
                  <t-tag v-if="exchange.connected" theme="success" size="small">
                    <t-icon name="check-circle" /> 已连接
                  </t-tag>
                  <t-tag v-else theme="default" size="small">未连接</t-tag>
                </div>
              </div>
              <t-radio :checked="selectedExchange === exchange.id" />
            </div>
          </div>
          
          <!-- API配置 -->
          <div v-if="selectedExchange && !getExchange(selectedExchange)?.connected" class="api-config">
            <t-divider>配置API密钥</t-divider>
            <t-form :data="apiForm" layout="vertical">
              <t-form-item label="API Key">
                <t-input v-model="apiForm.apiKey" placeholder="请输入API Key" />
              </t-form-item>
              <t-form-item label="API Secret">
                <t-input v-model="apiForm.apiSecret" type="password" placeholder="请输入API Secret" />
              </t-form-item>
              <t-form-item label="Passphrase（如有）">
                <t-input v-model="apiForm.passphrase" type="password" placeholder="请输入Passphrase" />
              </t-form-item>
              <t-form-item>
                <t-button theme="primary" @click="testConnection">测试连接</t-button>
              </t-form-item>
            </t-form>
          </div>
          
          <!-- 已连接的账户信息 -->
          <div v-if="selectedExchange && getExchange(selectedExchange)?.connected" class="account-info">
            <t-divider>账户信息</t-divider>
            <t-descriptions :column="2">
              <t-descriptions-item label="账户ID">{{ accountInfo.id }}</t-descriptions-item>
              <t-descriptions-item label="总资产">{{ accountInfo.totalBalance }} USDT</t-descriptions-item>
              <t-descriptions-item label="可用余额">{{ accountInfo.availableBalance }} USDT</t-descriptions-item>
              <t-descriptions-item label="冻结金额">{{ accountInfo.frozenBalance }} USDT</t-descriptions-item>
            </t-descriptions>
          </div>
        </t-card>
      </div>
      
      <!-- 步骤3: 资金配置 -->
      <div v-show="currentStep === 2" class="step-panel">
        <t-card title="资金与风控配置" :bordered="false">
          <t-form :data="fundConfig" layout="vertical">
            <t-row :gutter="24">
              <t-col :span="12">
                <t-form-item label="投入资金 (USDT)">
                  <t-input-number 
                    v-model="fundConfig.investAmount" 
                    :min="100" 
                    :max="accountInfo.availableBalance"
                    :step="100"
                    theme="column"
                  />
                  <div class="form-tips">
                    可用余额: {{ accountInfo.availableBalance }} USDT
                  </div>
                </t-form-item>
              </t-col>
              <t-col :span="12">
                <t-form-item label="单笔最大仓位 (%)">
                  <t-slider v-model="fundConfig.maxPositionPercent" :min="1" :max="100" />
                </t-form-item>
              </t-col>
            </t-row>
            
            <t-divider>风控设置</t-divider>
            
            <t-row :gutter="24">
              <t-col :span="8">
                <t-form-item label="单日最大亏损 (%)">
                  <t-input-number v-model="fundConfig.maxDailyLoss" :min="1" :max="50" theme="column" />
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="总最大回撤 (%)">
                  <t-input-number v-model="fundConfig.maxDrawdown" :min="5" :max="80" theme="column" />
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="同时持仓数量">
                  <t-input-number v-model="fundConfig.maxPositions" :min="1" :max="20" theme="column" />
                </t-form-item>
              </t-col>
            </t-row>
            
            <t-row :gutter="24">
              <t-col :span="8">
                <t-form-item label="默认止损 (%)">
                  <t-input-number v-model="fundConfig.defaultStopLoss" :min="0.5" :max="20" :step="0.5" theme="column" />
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="默认止盈 (%)">
                  <t-input-number v-model="fundConfig.defaultTakeProfit" :min="1" :max="100" :step="1" theme="column" />
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="移动止损">
                  <t-switch v-model="fundConfig.trailingStop" />
                </t-form-item>
              </t-col>
            </t-row>
            
            <t-divider>通知设置</t-divider>
            
            <t-row :gutter="24">
              <t-col :span="8">
                <t-form-item label="交易通知">
                  <t-checkbox-group v-model="fundConfig.notifications">
                    <t-checkbox value="email">邮件</t-checkbox>
                    <t-checkbox value="sms">短信</t-checkbox>
                    <t-checkbox value="push">推送</t-checkbox>
                  </t-checkbox-group>
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="异常报警">
                  <t-switch v-model="fundConfig.alertOnError" />
                </t-form-item>
              </t-col>
              <t-col :span="8">
                <t-form-item label="日报推送">
                  <t-switch v-model="fundConfig.dailyReport" />
                </t-form-item>
              </t-col>
            </t-row>
          </t-form>
        </t-card>
      </div>
      
      <!-- 步骤4: 确认启动 -->
      <div v-show="currentStep === 3" class="step-panel">
        <t-card title="配置确认" :bordered="false">
          <div class="config-summary">
            <t-descriptions :column="1" layout="horizontal" bordered>
              <t-descriptions-item label="交易策略">
                {{ getStrategy(selectedStrategy)?.name }}
              </t-descriptions-item>
              <t-descriptions-item label="交易所">
                {{ getExchange(selectedExchange)?.name }}
              </t-descriptions-item>
              <t-descriptions-item label="投入资金">
                {{ fundConfig.investAmount }} USDT
              </t-descriptions-item>
              <t-descriptions-item label="单笔最大仓位">
                {{ fundConfig.maxPositionPercent }}%
              </t-descriptions-item>
              <t-descriptions-item label="单日最大亏损">
                {{ fundConfig.maxDailyLoss }}%
              </t-descriptions-item>
              <t-descriptions-item label="总最大回撤">
                {{ fundConfig.maxDrawdown }}%
              </t-descriptions-item>
              <t-descriptions-item label="默认止损/止盈">
                {{ fundConfig.defaultStopLoss }}% / {{ fundConfig.defaultTakeProfit }}%
              </t-descriptions-item>
              <t-descriptions-item label="移动止损">
                {{ fundConfig.trailingStop ? '开启' : '关闭' }}
              </t-descriptions-item>
            </t-descriptions>
            
            <t-alert theme="warning" class="config-warning">
              <template #message>
                <p><strong>重要提示：</strong></p>
                <ul>
                  <li>实盘交易存在亏损风险，请确保您已充分了解策略特性</li>
                  <li>建议先使用模拟交易测试策略效果</li>
                  <li>请确保您的API权限设置正确，不要给予提币权限</li>
                  <li>建议设置合理的风控参数，避免过度亏损</li>
                </ul>
              </template>
            </t-alert>
            
            <t-checkbox v-model="agreeRisk" class="risk-checkbox">
              我已阅读并理解上述风险提示，确认开始实盘交易
            </t-checkbox>
          </div>
        </t-card>
      </div>
    </div>
    
    <!-- 底部操作按钮 -->
    <div class="config-footer">
      <t-button v-if="currentStep > 0" variant="outline" @click="prevStep">
        <t-icon name="chevron-left" /> 上一步
      </t-button>
      <div class="footer-right">
        <t-button variant="outline" @click="saveDraft">保存草稿</t-button>
        <t-button 
          v-if="currentStep < 3" 
          theme="primary" 
          @click="nextStep"
          :disabled="!canProceed"
        >
          下一步 <t-icon name="chevron-right" />
        </t-button>
        <t-button 
          v-else 
          theme="primary" 
          @click="startLive"
          :disabled="!agreeRisk"
          :loading="starting"
        >
          <t-icon name="play-circle" /> 启动实盘
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)
const starting = ref(false)
const agreeRisk = ref(false)

// 可用策略
const availableStrategies = ref([
  {
    id: 'grid-btc',
    name: 'BTC网格交易策略',
    description: '适合震荡行情的网格交易策略，自动在设定区间内低买高卖',
    returns: 45.6,
    drawdown: 12.3,
    runningDays: 180,
    isOwned: true,
    isCustom: false
  },
  {
    id: 'trend-following',
    name: '趋势跟踪策略',
    description: '基于均线和动量指标的趋势跟踪策略，适合单边行情',
    returns: 78.2,
    drawdown: 18.5,
    runningDays: 365,
    isOwned: true,
    isCustom: false
  },
  {
    id: 'my-custom-1',
    name: '我的自定义策略',
    description: '基于MACD和RSI的组合策略',
    returns: 32.1,
    drawdown: 8.7,
    runningDays: 45,
    isOwned: true,
    isCustom: true
  }
])

const selectedStrategy = ref('grid-btc')

// 交易所列表
const exchanges = ref([
  {
    id: 'binance',
    name: 'Binance',
    logo: 'https://cryptologos.cc/logos/binance-coin-bnb-logo.png',
    connected: true
  },
  {
    id: 'okx',
    name: 'OKX',
    logo: 'https://cryptologos.cc/logos/okb-okb-logo.png',
    connected: false
  },
  {
    id: 'huobi',
    name: 'Huobi',
    logo: 'https://cryptologos.cc/logos/huobi-token-ht-logo.png',
    connected: false
  },
  {
    id: 'bybit',
    name: 'Bybit',
    logo: 'https://cryptologos.cc/logos/bybit-bit-logo.png',
    connected: false
  }
])

const selectedExchange = ref('binance')

// API表单
const apiForm = ref({
  apiKey: '',
  apiSecret: '',
  passphrase: ''
})

// 账户信息
const accountInfo = ref({
  id: 'xxx...xxx123',
  totalBalance: 50000,
  availableBalance: 45000,
  frozenBalance: 5000
})

// 资金配置
const fundConfig = ref({
  investAmount: 10000,
  maxPositionPercent: 20,
  maxDailyLoss: 5,
  maxDrawdown: 20,
  maxPositions: 5,
  defaultStopLoss: 2,
  defaultTakeProfit: 5,
  trailingStop: true,
  notifications: ['email', 'push'],
  alertOnError: true,
  dailyReport: true
})

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return !!selectedStrategy.value
    case 1:
      return selectedExchange.value && getExchange(selectedExchange.value)?.connected
    case 2:
      return fundConfig.value.investAmount >= 100
    default:
      return true
  }
})

// 方法
const getStrategy = (id) => {
  return availableStrategies.value.find(s => s.id === id)
}

const getExchange = (id) => {
  return exchanges.value.find(e => e.id === id)
}

const selectExchange = (exchange) => {
  selectedExchange.value = exchange.id
}

const testConnection = () => {
  MessagePlugin.loading('正在测试连接...')
  setTimeout(() => {
    const exchange = exchanges.value.find(e => e.id === selectedExchange.value)
    if (exchange) {
      exchange.connected = true
    }
    MessagePlugin.success('连接成功！')
  }, 2000)
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = () => {
  if (currentStep.value < 3 && canProceed.value) {
    currentStep.value++
  }
}

const saveDraft = () => {
  MessagePlugin.success('配置草稿已保存')
}

const startLive = () => {
  if (!agreeRisk.value) {
    MessagePlugin.warning('请先确认风险提示')
    return
  }
  
  starting.value = true
  setTimeout(() => {
    starting.value = false
    MessagePlugin.success('实盘策略启动成功！')
    router.push('/live-monitor')
  }, 2000)
}
</script>

<style lang="less" scoped>
.live-config-page {
  padding: 24px;
  background: #0d1117;
  min-height: calc(100vh - 56px);
}

.page-header {
  margin-bottom: 32px;
  
  .header-title {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .header-icon {
      font-size: 32px;
      color: var(--primary);
    }
    
    h1 {
      margin: 0;
      font-size: 28px;
      color: #fff;
    }
  }
  
  .header-desc {
    margin: 8px 0 0 44px;
    color: rgba(255, 255, 255, 0.6);
  }
}

.config-steps {
  margin-bottom: 32px;
  padding: 24px;
  background: #161b22;
  border-radius: 12px;
}

.config-content {
  margin-bottom: 24px;
}

.step-panel {
  :deep(.t-card) {
    background: #161b22;
    border: none;
    
    .t-card__title {
      color: #fff;
    }
  }
}

.strategy-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strategy-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #21262d;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #30363d;
  }
  
  &.selected {
    border-color: var(--primary);
    background: rgba(0, 82, 217, 0.1);
  }
  
  .strategy-info {
    flex: 1;
    
    .strategy-name {
      font-size: 16px;
      font-weight: 500;
      color: #fff;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .strategy-desc {
      color: rgba(255, 255, 255, 0.6);
      font-size: 13px;
      margin-bottom: 12px;
    }
    
    .strategy-stats {
      display: flex;
      gap: 24px;
      
      .stat {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        color: rgba(255, 255, 255, 0.6);
        
        b {
          font-weight: 600;
        }
      }
    }
  }
}

.text-success { color: var(--green); }
.text-danger { color: var(--red); }

.exchange-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.exchange-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #21262d;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #30363d;
  }
  
  &.selected {
    border-color: var(--primary);
  }
  
  .exchange-logo {
    width: 40px;
    height: 40px;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }
  
  .exchange-info {
    flex: 1;
    
    .exchange-name {
      font-size: 16px;
      font-weight: 500;
      color: #fff;
      margin-bottom: 4px;
    }
  }
}

.api-config, .account-info {
  padding: 16px;
  background: #21262d;
  border-radius: 8px;
}

.form-tips {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.config-summary {
  .config-warning {
    margin-top: 24px;
    
    ul {
      margin: 8px 0 0 20px;
      padding: 0;
      
      li {
        margin-bottom: 4px;
      }
    }
  }
  
  .risk-checkbox {
    margin-top: 24px;
    padding: 16px;
    background: #21262d;
    border-radius: 8px;
  }
}

.config-footer {
  display: flex;
  justify-content: space-between;
  padding: 24px;
  background: #161b22;
  border-radius: 12px;
  
  .footer-right {
    display: flex;
    gap: 12px;
  }
}
</style>
