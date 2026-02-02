<template>
  <div class="risk-center-page">
    <div class="page-header">
      <h1><t-icon name="shield" /> 风控中心</h1>
      <p class="header-desc">实时监控和管理您的交易风险</p>
    </div>
    
    <!-- 风险概览 -->
    <div class="risk-overview">
      <div class="risk-score-card">
        <div class="score-circle" :class="riskLevel">
          <div class="score-value">{{ riskScore }}</div>
          <div class="score-label">风险评分</div>
        </div>
        <div class="risk-status">
          <t-tag :theme="riskLevel === 'safe' ? 'success' : riskLevel === 'warning' ? 'warning' : 'danger'" size="large">
            {{ riskLevelText }}
          </t-tag>
          <p>{{ riskDescription }}</p>
        </div>
      </div>
      
      <div class="risk-stats">
        <div class="stat-item" v-for="stat in riskStats" :key="stat.label">
          <div class="stat-header">
            <t-icon :name="stat.icon" />
            <span>{{ stat.label }}</span>
          </div>
          <div class="stat-value" :class="stat.class">{{ stat.value }}</div>
          <div class="stat-limit">限制: {{ stat.limit }}</div>
          <t-progress :percentage="stat.percent" :color="stat.color" size="small" />
        </div>
      </div>
    </div>
    
    <!-- 风控规则 -->
    <t-card title="风控规则设置" :bordered="false" class="rules-card">
      <template #actions>
        <t-button variant="outline" size="small" @click="showAddRule = true">
          <t-icon name="add" /> 添加规则
        </t-button>
      </template>
      
      <t-table :data="riskRules" :columns="ruleColumns" row-key="id" stripe>
        <template #status="{ row }">
          <t-switch v-model="row.enabled" size="small" />
        </template>
        <template #type="{ row }">
          <t-tag :theme="getRuleTheme(row.type)" variant="light">{{ row.type }}</t-tag>
        </template>
        <template #operation="{ row }">
          <t-button variant="text" size="small" @click="editRule(row)">编辑</t-button>
          <t-button variant="text" size="small" theme="danger" @click="deleteRule(row)">删除</t-button>
        </template>
      </t-table>
    </t-card>
    
    <!-- 风险警报 -->
    <t-card title="风险警报" :bordered="false" class="alerts-card">
      <template #actions>
        <t-button variant="text" size="small" @click="clearAlerts">清除全部</t-button>
      </template>
      
      <div class="alert-list">
        <div v-for="alert in alerts" :key="alert.id" class="alert-item" :class="alert.level">
          <div class="alert-icon">
            <t-icon :name="alert.level === 'danger' ? 'error-circle' : 'warning-circle'" />
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-desc">{{ alert.description }}</div>
            <div class="alert-time">{{ alert.time }}</div>
          </div>
          <div class="alert-actions">
            <t-button size="small" variant="outline" @click="handleAlert(alert)">处理</t-button>
            <t-button size="small" variant="text" @click="dismissAlert(alert)">忽略</t-button>
          </div>
        </div>
        <t-empty v-if="!alerts.length" description="暂无风险警报" />
      </div>
    </t-card>
    
    <!-- 风险报表 -->
    <div class="risk-charts">
      <t-card title="风险趋势" :bordered="false">
        <apexchart type="line" height="280" :options="trendChartOptions" :series="trendSeries" />
      </t-card>
      
      <t-card title="风险分布" :bordered="false">
        <apexchart type="donut" height="280" :options="distributionOptions" :series="distributionSeries" />
      </t-card>
    </div>
    
    <!-- 添加规则弹窗 -->
    <t-dialog v-model:visible="showAddRule" header="添加风控规则" width="500px" @confirm="saveRule">
      <t-form :data="ruleForm" layout="vertical">
        <t-form-item label="规则名称">
          <t-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </t-form-item>
        <t-form-item label="规则类型">
          <t-select v-model="ruleForm.type">
            <t-option value="止损" label="止损规则" />
            <t-option value="仓位" label="仓位限制" />
            <t-option value="频率" label="交易频率" />
            <t-option value="时间" label="时间限制" />
          </t-select>
        </t-form-item>
        <t-form-item label="触发条件">
          <t-input v-model="ruleForm.condition" placeholder="如: 单日亏损 > 5%" />
        </t-form-item>
        <t-form-item label="执行动作">
          <t-select v-model="ruleForm.action">
            <t-option value="alert" label="发送警报" />
            <t-option value="pause" label="暂停交易" />
            <t-option value="close" label="平仓" />
            <t-option value="stop" label="停止策略" />
          </t-select>
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const showAddRule = ref(false)

// 风险评分
const riskScore = ref(72)
const riskLevel = computed(() => {
  if (riskScore.value >= 80) return 'safe'
  if (riskScore.value >= 50) return 'warning'
  return 'danger'
})
const riskLevelText = computed(() => {
  if (riskScore.value >= 80) return '风险较低'
  if (riskScore.value >= 50) return '风险中等'
  return '风险较高'
})
const riskDescription = computed(() => {
  if (riskScore.value >= 80) return '当前账户风险控制良好，各项指标正常'
  if (riskScore.value >= 50) return '部分风控指标接近阈值，请关注'
  return '存在较大风险敞口，建议立即调整'
})

// 风险统计
const riskStats = ref([
  { icon: 'trending-down', label: '今日亏损', value: '-1.2%', limit: '5%', percent: 24, color: '#00A870', class: 'text-danger' },
  { icon: 'chart-line', label: '最大回撤', value: '-8.5%', limit: '20%', percent: 42.5, color: '#00A870', class: 'text-danger' },
  { icon: 'layers', label: '持仓占比', value: '35%', limit: '80%', percent: 43.75, color: '#0052D9' },
  { icon: 'time', label: '杠杆使用', value: '12x', limit: '20x', percent: 60, color: '#E37318' }
])

// 风控规则
const riskRules = ref([
  { id: 1, name: '单日最大亏损', type: '止损', condition: '日亏损 > 5%', action: '暂停交易', enabled: true },
  { id: 2, name: '最大回撤限制', type: '止损', condition: '回撤 > 20%', action: '停止策略', enabled: true },
  { id: 3, name: '单笔仓位限制', type: '仓位', condition: '单笔 > 20%', action: '禁止开仓', enabled: true },
  { id: 4, name: '高波动暂停', type: '时间', condition: 'VIX > 30', action: '暂停交易', enabled: false },
  { id: 5, name: '交易频率限制', type: '频率', condition: '每小时 > 10次', action: '发送警报', enabled: true }
])

const ruleColumns = [
  { colKey: 'status', title: '状态', width: 80 },
  { colKey: 'name', title: '规则名称', width: 150 },
  { colKey: 'type', title: '类型', width: 100 },
  { colKey: 'condition', title: '触发条件', width: 180 },
  { colKey: 'action', title: '执行动作', width: 120 },
  { colKey: 'operation', title: '操作', width: 120 }
]

// 风险警报
const alerts = ref([
  { id: 1, level: 'warning', title: '回撤接近阈值', description: '当前回撤8.5%，接近20%的阈值限制', time: '10分钟前' },
  { id: 2, level: 'warning', title: '持仓集中度过高', description: 'BTC持仓占总资金的35%，建议分散风险', time: '1小时前' },
  { id: 3, level: 'danger', title: '杠杆使用率偏高', description: '当前使用12x杠杆，风险较大', time: '2小时前' }
])

// 规则表单
const ruleForm = ref({ name: '', type: '止损', condition: '', action: 'alert' })

// 图表配置
const trendChartOptions = {
  chart: { type: 'line', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#0052D9', '#E34D59', '#00A870'],
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { categories: ['1日', '2日', '3日', '4日', '5日', '6日', '7日'], labels: { style: { colors: '#666' } } },
  yaxis: { labels: { style: { colors: '#666' } } },
  grid: { borderColor: '#21262d' },
  legend: { labels: { colors: '#999' } }
}

const trendSeries = ref([
  { name: '风险评分', data: [85, 82, 78, 75, 72, 74, 72] },
  { name: '回撤率', data: [3, 5, 6, 7, 8.5, 8, 8.5] },
  { name: '仓位占比', data: [20, 25, 30, 28, 35, 32, 35] }
])

const distributionOptions = {
  chart: { type: 'donut', background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#0052D9', '#00A870', '#E37318', '#E34D59'],
  labels: ['市场风险', '流动性风险', '操作风险', '信用风险'],
  legend: { labels: { colors: '#999' }, position: 'bottom' },
  plotOptions: { pie: { donut: { size: '65%' } } }
}

const distributionSeries = ref([45, 25, 20, 10])

// 方法
const getRuleTheme = (type) => {
  const themes = { '止损': 'danger', '仓位': 'primary', '频率': 'warning', '时间': 'default' }
  return themes[type] || 'default'
}

const editRule = (rule) => {
  ruleForm.value = { ...rule }
  showAddRule.value = true
}

const deleteRule = (rule) => {
  const index = riskRules.value.findIndex(r => r.id === rule.id)
  if (index > -1) {
    riskRules.value.splice(index, 1)
    MessagePlugin.success('规则已删除')
  }
}

const saveRule = () => {
  if (!ruleForm.value.name) {
    MessagePlugin.warning('请输入规则名称')
    return
  }
  if (ruleForm.value.id) {
    const index = riskRules.value.findIndex(r => r.id === ruleForm.value.id)
    if (index > -1) riskRules.value[index] = { ...ruleForm.value }
  } else {
    riskRules.value.push({ ...ruleForm.value, id: Date.now(), enabled: true })
  }
  showAddRule.value = false
  ruleForm.value = { name: '', type: '止损', condition: '', action: 'alert' }
  MessagePlugin.success('规则已保存')
}

const handleAlert = (alert) => MessagePlugin.info(`处理警报: ${alert.title}`)
const dismissAlert = (alert) => {
  const index = alerts.value.findIndex(a => a.id === alert.id)
  if (index > -1) alerts.value.splice(index, 1)
}
const clearAlerts = () => { alerts.value = []; MessagePlugin.success('已清除所有警报') }
</script>

<style lang="less" scoped>
.risk-center-page { padding: 24px; background: #0d1117; min-height: calc(100vh - 56px); }
.page-header { margin-bottom: 24px;
  h1 { margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 8px; }
  .header-desc { margin: 8px 0 0 32px; color: rgba(255,255,255,0.6); }
}

.risk-overview { display: grid; grid-template-columns: 300px 1fr; gap: 24px; margin-bottom: 24px; }

.risk-score-card { background: #161b22; border-radius: 12px; padding: 24px; text-align: center;
  .score-circle { width: 150px; height: 150px; border-radius: 50%; margin: 0 auto 16px; display: flex; flex-direction: column; align-items: center; justify-content: center;
    &.safe { background: linear-gradient(135deg, rgba(0,168,112,0.2), rgba(0,168,112,0.1)); border: 3px solid var(--green); }
    &.warning { background: linear-gradient(135deg, rgba(227,115,24,0.2), rgba(227,115,24,0.1)); border: 3px solid #E37318; }
    &.danger { background: linear-gradient(135deg, rgba(227,77,89,0.2), rgba(227,77,89,0.1)); border: 3px solid var(--red); }
    .score-value { font-size: 48px; font-weight: bold; color: #fff; }
    .score-label { font-size: 14px; color: rgba(255,255,255,0.6); }
  }
  .risk-status { p { margin: 12px 0 0; color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.6; } }
}

.risk-stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;
  .stat-item { background: #161b22; border-radius: 12px; padding: 20px;
    .stat-header { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.6); margin-bottom: 12px; }
    .stat-value { font-size: 28px; font-weight: bold; color: #fff; margin-bottom: 4px; }
    .stat-limit { font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
  }
}

.text-success { color: var(--green) !important; }
.text-danger { color: var(--red) !important; }

.rules-card, .alerts-card { margin-bottom: 24px;
  :deep(.t-card) { background: #161b22; border: none; }
}

.alert-list { .alert-item { display: flex; align-items: flex-start; gap: 16px; padding: 16px; background: #21262d; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid;
  &.warning { border-color: #E37318; .alert-icon { color: #E37318; } }
  &.danger { border-color: var(--red); .alert-icon { color: var(--red); } }
  .alert-icon { font-size: 24px; }
  .alert-content { flex: 1;
    .alert-title { font-weight: 500; color: #fff; margin-bottom: 4px; }
    .alert-desc { font-size: 13px; color: rgba(255,255,255,0.7); margin-bottom: 8px; }
    .alert-time { font-size: 12px; color: rgba(255,255,255,0.5); }
  }
  .alert-actions { display: flex; gap: 8px; }
} }

.risk-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
  :deep(.t-card) { background: #161b22; border: none; }
}
</style>
