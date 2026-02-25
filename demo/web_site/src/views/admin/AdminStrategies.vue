<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold text-white">策略管理</h2>
      <button @click="openCreateDialog" class="btn-primary !py-2 !px-4 text-sm flex items-center gap-1.5">
        <Plus :size="14" /> 新增策略
      </button>
    </div>

    <!-- Filters -->
    <div class="glass-card p-4 flex flex-wrap items-center gap-4">
      <t-input v-model="search" placeholder="搜索策略..." clearable size="medium" style="width: 240px">
        <template #prefix-icon><Search :size="16" class="text-dark-100" /></template>
      </t-input>
      <t-select v-model="filterStatus" placeholder="状态" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </t-select>
      <t-select v-model="filterRisk" placeholder="风险等级" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option v-for="item in riskLevelOptions" :key="item.value" :label="item.label" :value="item.value" />
      </t-select>
      <t-select v-model="filterExchange" placeholder="交易所" clearable size="medium" style="width: 160px; color: white !important;" class="text-white">
        <t-option v-for="item in exchangeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </t-select>
      <t-select v-model="filterTimeframe" placeholder="时间周期" clearable size="medium" style="width: 140px; color: white !important;" class="text-white">
        <t-option v-for="item in timeframeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </t-select>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/[0.06]">
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">策略名称</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易所</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">交易对</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">时间周期</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">类型</th>
              <th class="text-left py-3.5 px-5 text-dark-100 font-medium">风险</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">收益率</th>
              <th class="text-right py-3.5 px-5 text-dark-100 font-medium">最大回撤</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">状态</th>
              <th class="text-center py-3.5 px-5 text-dark-100 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredList" :key="s.id" class="border-b border-white/[0.04] hover:bg-white/[0.02]">
              <td class="py-3.5 px-5 text-white font-medium">{{ s.name }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.exchange }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.tradingPair }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.timeframe }}</td>
              <td class="py-3.5 px-5 text-dark-100">{{ s.type }}</td>
              <td class="py-3.5 px-5"><RiskBadge :level="s.riskLevel" /></td>
              <td class="py-3.5 px-5 text-right font-medium" :class="s.returnRate >= 0 ? 'text-emerald-400' : 'text-red-400'">
                {{ s.returnRate >= 0 ? '+' : '' }}{{ s.returnRate }}%
              </td>
              <td class="py-3.5 px-5 text-right text-amber-400">{{ s.maxDrawdown }}%</td>
              <td class="py-3.5 px-5 text-center"><StatusDot :status="s.status" /></td>
              <td class="py-3.5 px-5 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button class="p-1.5 rounded text-dark-100 hover:text-primary-500 hover:bg-primary-500/10 transition-all"><Pencil :size="14" /></button>
                  <button @click.stop="handleDelete(s.id, s.name)" class="p-1.5 rounded text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-all"><Trash2 :size="14" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 新增策略弹窗 -->
    <t-dialog
      v-model:visible="createDialogVisible"
      header="新增策略"
      :footer="false"
      :dialogStyle="{'background-color': 'rgb(8 10 15)'}"
      width="640px"
      placement="center"
      destroy-on-close
    >
      <form @submit.prevent="handleCreateStrategy" class="space-y-5 py-2">
        <!-- 策略名称 -->
        <div class="space-y-1.5">
          <label class="text-sm text-dark-100">策略名称 <span class="text-red-400">*</span></label>
          <t-input v-model="createForm.name" placeholder="请输入策略名称" clearable />
        </div>

        <!-- 策略描述 -->
        <div class="space-y-1.5">
          <label class="text-sm text-dark-100">策略描述</label>
          <t-textarea v-model="createForm.description" placeholder="请输入策略描述" :maxlength="500" :autosize="{ minRows: 2, maxRows: 4 }" />
        </div>

        <!-- 策略类型 & 市场类型 -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="text-sm text-dark-100">策略类型 <span class="text-red-400">*</span></label>
            <t-select v-model="createForm.strategy_type" placeholder="请选择策略类型" clearable>
              <t-option v-for="st in strategyTypes" :key="st.value" :label="st.label" :value="st.value" />
            </t-select>
          </div>
          <div class="space-y-1.5">
            <label class="text-sm text-dark-100">市场类型</label>
            <t-select v-model="createForm.market_type" placeholder="请选择市场类型" clearable>
              <t-option v-for="item in marketTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </t-select>
          </div>
        </div>

        <!-- 交易所 & 风险等级 -->
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="text-sm text-dark-100">交易所</label>
            <t-select v-model="createForm.exchange" placeholder="请选择交易所" clearable>
              <t-option v-for="item in exchangeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </t-select>
          </div>
          <div class="space-y-1.5">
            <label class="text-sm text-dark-100">风险等级</label>
            <t-select v-model="createForm.risk_level" placeholder="请选择风险等级" clearable>
              <t-option v-for="item in riskLevelOptions" :key="item.value" :label="item.label" :value="item.value" />
            </t-select>
          </div>
        </div>

        <!-- 交易对 -->
        <div class="space-y-1.5">
          <label class="text-sm text-dark-100">交易对</label>
          <t-input v-model="createForm.symbols" placeholder="请输入交易对，多个用逗号分隔，如 BTCUSDT,ETHUSDT" clearable />
        </div>

        <!-- 时间周期 -->
        <div class="space-y-1.5">
          <label class="text-sm text-dark-100">时间周期</label>
          <t-select v-model="createForm.timeframes" placeholder="请选择时间周期" multiple clearable>
            <t-option v-for="item in timeframeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </t-select>
        </div>

        <!-- 按钮 -->
        <div class="flex justify-end gap-3 pt-2">
          <t-button theme="default" variant="outline" @click="createDialogVisible = false">取消</t-button>
          <t-button theme="primary" type="submit" :loading="createLoading">确认创建</t-button>
        </div>
      </form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Search, Pencil, Trash2 } from 'lucide-vue-next'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import RiskBadge from '@/components/common/RiskBadge.vue'
import StatusDot from '@/components/common/StatusDot.vue'
import strategyApi from '@/utils/strategyApi'
import systemApi, { type EnumItem } from '@/utils/systemApi'

const search = ref('')
const filterStatus = ref('')
const filterRisk = ref('')
const filterExchange = ref('')
const filterTimeframe = ref('')
const loading = ref(false)
const strategies = ref<any[]>([])

// ========== 枚举选项数据 ==========
const statusOptions = ref<EnumItem[]>([])
const riskLevelOptions = ref<EnumItem[]>([])
const exchangeOptions = ref<EnumItem[]>([])
const timeframeOptions = ref<EnumItem[]>([])
const marketTypeOptions = ref<EnumItem[]>([])
const strategyTypeOptions = ref<EnumItem[]>([])

// ========== 新增策略相关 ==========
const createDialogVisible = ref(false)
const createLoading = ref(false)
const strategyTypes = ref<{ label: string; value: string }[]>([])

const defaultCreateForm = () => ({
  name: '',
  description: '',
  strategy_type: '',
  market_type: 'spot',
  risk_level: 'medium',
  exchange: 'binance',
  symbols: '',
  timeframes: [] as string[],
})
const createForm = ref(defaultCreateForm())

// 打开新增弹窗
function openCreateDialog() {
  createForm.value = defaultCreateForm()
  createDialogVisible.value = true
  loadStrategyTypes()
}

// 批量加载枚举数据
async function loadEnums() {
  try {
    const response = await systemApi.getEnumBatch([
      'StrategyStatus', 'RiskLevel', 'ExchangeEnum', 'KlineInterval', 'MarketType', 'StrategyType'
    ])
    if (response?.enums) {
      const enums = response.enums
      if (enums['StrategyStatus']) statusOptions.value = enums['StrategyStatus']
      if (enums['RiskLevel']) riskLevelOptions.value = enums['RiskLevel']
      if (enums['ExchangeEnum']) exchangeOptions.value = enums['ExchangeEnum']
      if (enums['KlineInterval']) timeframeOptions.value = enums['KlineInterval']
      if (enums['MarketType']) marketTypeOptions.value = enums['MarketType']
      if (enums['StrategyType']) {
        strategyTypeOptions.value = enums['StrategyType']
        strategyTypes.value = enums['StrategyType'].map((t: EnumItem) => ({
          label: t.label,
          value: t.value,
        }))
      }
    }
  } catch (error) {
    console.error('批量加载枚举失败:', error)
  }
}

// 加载策略类型（作为备用，当枚举未加载时在打开弹窗时调用）
async function loadStrategyTypes() {
  if (strategyTypes.value.length > 0) return
  try {
    const res = await systemApi.getEnumByName('StrategyType')
    if (res?.items) {
      strategyTypes.value = res.items.map((t: EnumItem) => ({
        label: t.label,
        value: t.value,
      }))
    }
  } catch (e: any) {
    console.error('加载策略类型失败:', e)
  }
}

// 提交创建策略
async function handleCreateStrategy() {
  if (!createForm.value.name.trim()) {
    MessagePlugin.warning('请输入策略名称')
    return
  }
  if (!createForm.value.strategy_type) {
    MessagePlugin.warning('请选择策略类型')
    return
  }

  createLoading.value = true
  try {
    const symbolsArr = createForm.value.symbols
      ? createForm.value.symbols.split(',').map((s: string) => s.trim()).filter(Boolean)
      : []

    await strategyApi.createStrategy({
      name: createForm.value.name.trim(),
      description: createForm.value.description || undefined,
      strategy_type: createForm.value.strategy_type,
      market_type: createForm.value.market_type || undefined,
      risk_level: createForm.value.risk_level || undefined,
      exchange: createForm.value.exchange || undefined,
      symbols: symbolsArr.length > 0 ? symbolsArr : undefined,
      timeframes: createForm.value.timeframes.length > 0 ? createForm.value.timeframes : undefined,
    } as any)

    MessagePlugin.success('策略创建成功')
    createDialogVisible.value = false
    loadStrategies()
  } catch (error: any) {
    MessagePlugin.error(error.message || '创建策略失败')
  } finally {
    createLoading.value = false
  }
}

// 加载策略列表
async function loadStrategies() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: 1,
      page_size: 100,
    }
    if (search.value) params.keyword = search.value
    if (filterStatus.value) params.state = filterStatus.value
    if (filterRisk.value) params.risk_level = filterRisk.value
    if (filterExchange.value) params.exchange = filterExchange.value
    if (filterTimeframe.value) params.timeframe = filterTimeframe.value

    const response = await strategyApi.getStrategies(params)
    strategies.value = (response.strategies || []).map((s: any) => ({
      id: s.id || s.strategy_id,
      name: s.name || '',
      exchange: s.exchange || '',
      tradingPair: s.symbols?.[0] || s.tradingPair || s.symbol || '',
      timeframe: s.timeframe || '',
      type: s.strategy_type || s.type || '',
      riskLevel: s.risk_level || s.riskLevel || 'medium',
      returnRate: s.total_return ?? s.returnRate ?? 0,
      maxDrawdown: s.max_drawdown ?? s.maxDrawdown ?? 0,
      status: s.state || s.status || 'active',
    }))
  } catch (error: any) {
    console.error('加载策略列表失败:', error)
    MessagePlugin.error(error.message || '加载策略列表失败')
  } finally {
    loading.value = false
  }
}

const filteredList = computed(() => {
  return strategies.value.filter((s) => {
    if (search.value && !s.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterStatus.value && s.status !== filterStatus.value) return false
    if (filterRisk.value && s.riskLevel !== filterRisk.value) return false
    if (filterExchange.value && s.exchange !== filterExchange.value) return false
    if (filterTimeframe.value && s.timeframe !== filterTimeframe.value) return false
    return true
  })
})

async function handleDelete(id: string, name: string) {
  const dlg = DialogPlugin.confirm({
    header: '确认删除策略',
    body: `确定要删除策略「${name}」吗？此操作不可撤销。`,
    theme: 'danger',
    confirmBtn: '确认删除',
    cancelBtn: '取消',
    onConfirm: async () => {
      dlg.hide()
      try {
        await strategyApi.deleteStrategy(id)
        MessagePlugin.success('策略已删除')
        loadStrategies()
      } catch (error: any) {
        MessagePlugin.error(error.message || '删除策略失败')
      }
    },
    onCancel: () => dlg.hide(),
  })
}

onMounted(() => {
  loadEnums()
  loadStrategies()
})
</script>

<style scoped>
/* 确保下拉框占位符文本颜色为白色 */
:deep(.t-select .t-select__single-input),
:deep(.t-select .t-select__placeholder),
:deep(.t-select.t-is-empty .t-select__single-input),
:deep(.t-select.t-is-empty .t-select__placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::placeholder),
:deep(.t-select .t-select__placeholder::placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::-webkit-input-placeholder),
:deep(.t-select .t-select__placeholder::-webkit-input-placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input::-moz-placeholder),
:deep(.t-select .t-select__placeholder::-moz-placeholder) {
  color: #ffffff !important;
}

:deep(.t-select .t-select__single-input:-ms-input-placeholder),
:deep(.t-select .t-select__placeholder:-ms-input-placeholder) {
  color: #ffffff !important;
}

/* 针对实际DOM结构的下拉选项样式 */
:deep(.t-popup__content .t-select-option),
:deep(.t-select__dropdown-inner .t-select-option),
:deep(.t-select__list .t-select-option),
:deep(.t-select-option) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option:hover),
:deep(.t-select__dropdown-inner .t-select-option:hover),
:deep(.t-select__list .t-select-option:hover),
:deep(.t-select-option:hover) {
  color: #ffffff !important;
}

/* 选中状态下的文本颜色改为黑色 */
:deep(.t-popup__content .t-select-option.t-is-selected),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected),
:deep(.t-select__list .t-select-option.t-is-selected),
:deep(.t-select-option.t-is-selected) {
  color: #000000 !important;
}

/* 确保下拉选项内的span元素也应用颜色 */
:deep(.t-select-option span),
:deep(.t-select-option.t-is-selected span) {
  color: inherit !important;
}

/* 针对下拉列表中的所有文本 */
:deep(.t-popup__content),
:deep(.t-popup__content *),
:deep(.t-select__dropdown-inner),
:deep(.t-select__dropdown-inner *),
:deep(.t-select__list),
:deep(.t-select__list *) {
  color: #ffffff !important;
}

:deep(.t-popup__content .t-select-option.t-is-selected),
:deep(.t-popup__content .t-select-option.t-is-selected *),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected),
:deep(.t-select__dropdown-inner .t-select-option.t-is-selected *),
:deep(.t-select__list .t-select-option.t-is-selected),
:deep(.t-select__list .t-select-option.t-is-selected *) {
  color: #000000 !important;
}
</style>