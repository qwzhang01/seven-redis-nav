<template>
  <div>
    <!-- Hero Section -->
    <section class="relative min-h-[90vh] flex items-center overflow-hidden">
      <!-- Background Effects -->
      <div class="absolute inset-0 bg-hero-glow" />
      <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary-500/5 rounded-full blur-[120px]" />
      <div class="absolute top-1/3 right-0 w-[400px] h-[400px] bg-accent-blue/5 rounded-full blur-[100px]" />
      <!-- Grid Pattern -->
      <div class="absolute inset-0 opacity-[0.03]" style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 60px 60px;" />

      <div class="page-container relative z-10 pt-24">
        <div class="max-w-4xl mx-auto text-center">
          <!-- Badge -->
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 mb-8 animate-fade-in-up">
            <span class="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            <span class="text-sm text-primary-400 font-medium">专为专业交易者设计</span>
          </div>

          <h1 class="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.1] mb-6 animate-fade-in-up" style="animation-delay: 0.1s">
            更明智地交易
            <span class="block gradient-text mt-2">用数据驱动每一次决策</span>
          </h1>

          <p class="text-lg md:text-xl text-dark-100 max-w-2xl mx-auto mb-10 animate-fade-in-up" style="animation-delay: 0.2s">
            Quant Meta 的交易指标享誉全球并屡获殊荣是有原因的。融合先进的趋势逻辑、结构分析、流动性模型和成交量智能，为您提供反映真实市场行为而非猜测的信号。
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up" style="animation-delay: 0.3s">
            <a href="/system/signals" target="_blank" class="btn-primary text-base px-8 py-3.5 rounded-xl">
              获取指标
            </a>
            <a href="/system/strategies" target="_blank" class="btn-outline text-base px-8 py-3.5 rounded-xl">
              探索策略
            </a>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6 animate-fade-in-up" style="animation-delay: 0.4s">
            <div v-for="stat in heroStats" :key="stat.label" class="glass-card p-5 text-center">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Core Modules - Redesigned with Picture 2 Style -->
    <section class="py-24 bg-gradient-to-b from-dark-900/30 to-transparent">
      <div class="page-container">
        <div class="text-center mb-16">
          <h2 class="section-title">信号与警报</h2>
          <p class="section-subtitle">Quant Meta指标融合了先进的趋势逻辑、结构分析、流动性模型和成交量智能</p>
        </div>
        
        <!-- Grid Layout with Picture 2 Style -->
        <div class="space-y-12">
          <div 
            v-for="(module, index) in coreModules" 
            :key="module.title"
            class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center"
            :class="{ 'lg:grid-flow-col-dense': index % 2 === 1 }"
          >
            <!-- Chart/Visual Area (Left) -->
            <div class="relative group">
              <div class="glass-card p-6 rounded-2xl overflow-hidden">
                <!-- Chart Container -->
                <div class="h-64 bg-gradient-to-br from-primary-500/5 to-accent-blue/5 rounded-xl border border-white/10 p-4 flex items-center justify-center">
                  <!-- Chart Background Grid -->
                  <div class="absolute inset-0 opacity-10" style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 20px 20px;" />
                  
                  <!-- Chart Line -->
                  <div class="absolute bottom-0 left-0 right-0 h-32">
                    <svg class="w-full h-full" viewBox="0 0 400 160">
                      <path 
                        :d="module.chartData" 
                        fill="none" 
                        :stroke="module.chartColor" 
                        stroke-width="2" 
                        class="animate-draw-line"
                        style="animation-delay: 0.3s"
                      />
                    </svg>
                  </div>
                  
                  <!-- Chart Points -->
                  <div class="absolute top-1/4 left-1/4 w-3 h-3 rounded-full bg-primary-500/80 shadow-lg shadow-primary-500/30 animate-pulse" />
                  <div class="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-accent-blue/80 shadow-lg shadow-blue-500/30 animate-pulse" />
                  <div class="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-emerald-500/80 shadow-lg shadow-emerald-500/30 animate-pulse" />
                </div>
                
                <!-- Chart Stats -->
                <div class="mt-4 grid grid-cols-3 gap-2 text-center">
                  <div v-for="stat in module.stats" :key="stat.label" class="text-xs">
                    <div class="font-semibold text-white">{{ stat.value }}</div>
                    <div class="text-dark-100">{{ stat.label }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Content Area (Right) -->
            <div class="space-y-6">
              <!-- Icon and Title -->
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="module.iconBg">
                  <component :is="module.icon" :size="24" :class="module.iconColor" />
                </div>
                <h3 class="text-2xl font-bold text-white">{{ module.title }}</h3>
              </div>

              <!-- Description -->
              <p class="text-dark-100 text-lg leading-relaxed">{{ module.description }}</p>

              <!-- Features -->
              <div class="space-y-2">
                <div v-for="feature in module.features" :key="feature" class="flex items-center gap-3 text-sm">
                  <div class="w-2 h-2 rounded-full bg-primary-500" />
                  <span class="text-dark-100">{{ feature }}</span>
                </div>
              </div>

              <!-- Action Button -->
              <div class="pt-4">
                <a :href="module.to" target="_blank" class="btn-primary inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base">
                  <span>{{ module.buttonText }}</span>
                  <ArrowRight :size="16" />
                </a>
              </div>

              <!-- User Info (Bottom) -->
              <div class="flex items-center gap-3 pt-4 border-t border-white/10">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <User :size="14" class="text-primary-400" />
                </div>
                <div class="text-xs text-dark-100">
                  <div>{{ module.userInfo.activeUsers }}</div>
                  <div>{{ module.userInfo.description }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Hot Signals -->
    <section class="py-24 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary-500/[0.02] to-transparent" />
      <div class="page-container relative z-10">
        <div class="flex items-end justify-between mb-12">
          <div>
            <h2 class="section-title text-left">实时交易信号</h2>
            <p class="text-dark-100 text-lg">每个警报都经过精心设计，旨在提供清晰的提示、精准的时机和可靠的判断</p>
          </div>
          <a href="/system/signals" target="_blank" class="btn-outline !py-2 !px-5 text-sm hidden md:inline-flex items-center gap-2">
            查看全部 <ArrowRight :size="14" />
          </a>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <a
            v-for="signal in hotSignals"
            :key="signal.id"
            :href="`/system/signals/${signal.id}`"
            target="_blank"
            class="glass-card-hover p-6 group cursor-pointer"
          >
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <Radio :size="18" class="text-primary-400" />
                </div>
                <div>
                  <h4 class="text-white font-semibold text-sm">{{ signal.name }}</h4>
                  <span class="text-xs text-dark-100">{{ signal.platform }}</span>
                </div>
              </div>
              <StatusDot :status="signal.status" />
            </div>

            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div class="text-xs text-dark-100 mb-1">累计收益率</div>
                <div class="text-lg font-bold" :class="signal.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ signal.cumulativeReturn >= 0 ? '+' : '' }}{{ signal.cumulativeReturn.toFixed(2) }}%
                </div>
              </div>
              <div>
                <div class="text-xs text-dark-100 mb-1">最大回撤</div>
                <div class="text-lg font-bold text-amber-400">{{ signal.maxDrawdown.toFixed(2) }}%</div>
              </div>
            </div>

            <ReturnCurveChart
              v-if="signal.returnCurve?.length"
              :data="signal.returnCurve"
              :height="100"
              :color="signal.cumulativeReturn >= 0 ? '#10b981' : '#ef4444'"
            />

            <div class="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
              <span class="text-xs text-dark-100">{{ signal.followers }} 人跟随</span>
              <span class="text-xs text-dark-100">运行 {{ signal.runDays }} 天</span>
            </div>
          </a>
        </div>
        <a href="/system/signals" target="_blank" class="btn-outline w-full mt-8 text-sm !py-3 md:hidden flex items-center justify-center gap-2">
          查看全部信号 <ArrowRight :size="14" />
        </a>
      </div>
    </section>

    <!-- How It Works -->
    <section class="py-24">
      <div class="page-container">
        <div class="text-center mb-16">
          <h2 class="section-title">如何开始</h2>
          <p class="section-subtitle">三步开启您的量化交易之旅</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div v-for="(step, i) in steps" :key="i" class="relative text-center">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center mx-auto mb-6 border border-primary-500/20">
              <span class="text-2xl font-bold gradient-text">{{ i + 1 }}</span>
            </div>
            <h3 class="text-lg font-bold text-white mb-3">{{ step.title }}</h3>
            <p class="text-dark-100 text-sm leading-relaxed">{{ step.desc }}</p>
            <!-- Connector -->
            <div v-if="i < steps.length - 1" class="hidden md:block absolute top-8 left-[60%] w-[80%] border-t border-dashed border-dark-300" />
          </div>
        </div>
      </div>
    </section>

    <!-- Risk Disclaimer -->
    <section class="py-16">
      <div class="page-container">
        <div class="glass-card p-8 border-amber-500/20">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
              <AlertTriangle :size="20" class="text-amber-400" />
            </div>
            <div>
              <h4 class="text-white font-semibold mb-2">风险提示</h4>
              <p class="text-dark-100 text-sm leading-relaxed">
                加密货币交易存在较高的市场风险。历史表现不代表未来收益。量化策略和交易信号仅供参考，不构成投资建议。请根据自身风险承受能力，合理配置资产，谨慎投资。平台不对因使用本平台策略或信号造成的任何损失承担责任。
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Zap, Radio, Trophy, User, ArrowRight, AlertTriangle } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import { signals } from '@/utils/mockData'

const heroStats = [
  { value: '98.7%', label: '信号准确率' },
  { value: '25,000+', label: '专业交易者' },
  { value: '$850M+', label: '日均交易量' },
  { value: '99.99%', label: '系统稳定性' },
]

const coreModules = [
  {
    title: '智能交易信号',
    description: '融合先进的趋势逻辑、结构分析、流动性模型和成交量智能，为您提供反映真实市场行为而非猜测的信号。每个警报都经过精心设计，旨在提供清晰的提示、精准的时机和可靠的判断。',
    icon: Zap,
    iconBg: 'bg-primary-500/10',
    iconColor: 'text-primary-400',
    to: '/system/signals',
    buttonText: '获取指标',
    chartData: 'M20,100 Q60,80 100,120 Q140,60 180,100 Q220,140 260,80 Q300,120 340,100',
    chartColor: '#3b82f6',
    stats: [
      { value: '98.7%', label: '信号准确率' },
      { value: '23.5%', label: '平均收益' },
      { value: '1.8秒', label: '响应速度' }
    ],
    features: [
      '趋势信号识别',
      'BOS/CHOCH警报',
      '智能带量测',
      '流动性抢占提示'
    ],
    userInfo: {
      activeUsers: '15,000+ 专业交易者',
      description: '正在使用智能信号'
    }
  },
  {
    title: '量化策略引擎',
    description: '基于深度学习和强化学习的量化策略系统，支持多因子模型、风险平价、动量策略等高级算法，为专业交易者提供机构级别的策略执行能力。',
    icon: Radio,
    iconBg: 'bg-accent-blue/10',
    iconColor: 'text-blue-400',
    to: '/system/strategies',
    buttonText: '探索策略',
    chartData: 'M20,80 Q80,120 140,60 Q200,100 260,80 Q320,120 380,100',
    chartColor: '#10b981',
    stats: [
      { value: '45.2%', label: '最高年化' },
      { value: '8.3%', label: '最大回撤' },
      { value: '2.1', label: '夏普比率' }
    ],
    features: [
      '多因子模型策略',
      '实时风险监控',
      '自动参数优化',
      '回测验证系统'
    ],
    userInfo: {
      activeUsers: '8,500+ 策略用户',
      description: '正在运行量化策略'
    }
  },
  {
    title: '市场深度分析',
    description: '实时监控订单簿深度、流动性分布、大单动向等关键指标，提供专业的市场微观结构分析，帮助您把握最佳入场时机。',
    icon: Trophy,
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    to: '/system/analysis',
    buttonText: '深度分析',
    chartData: 'M20,120 Q100,60 180,140 Q260,80 340,120',
    chartColor: '#f59e0b',
    stats: [
      { value: '99.9%', label: '数据准确率' },
      { value: '500ms', label: '实时延迟' },
      { value: '50+', label: '监控指标' }
    ],
    features: [
      '订单簿深度监控',
      '流动性热力图',
      '大单追踪系统',
      '市场情绪分析'
    ],
    userInfo: {
      activeUsers: '12,000+ 分析用户',
      description: '正在使用深度分析'
    }
  },
  {
    title: '风险管理系统',
    description: '全面的风险管理框架，包含仓位控制、止损止盈、波动率监控等多维度风控措施，确保交易安全稳定运行。',
    icon: User,
    iconBg: 'bg-accent-purple/10',
    iconColor: 'text-purple-400',
    to: '/system/risk',
    buttonText: '风险管理',
    chartData: 'M20,100 Q60,140 100,80 Q140,120 180,60 Q220,100 260,140 Q300,80 340,100',
    chartColor: '#8b5cf6',
    stats: [
      { value: '0事故', label: '安全记录' },
      { value: '99.99%', label: '系统稳定' },
      { value: '24/7', label: '实时监控' }
    ],
    features: [
      '智能止损止盈',
      '仓位动态调整',
      '波动率预警',
      '压力测试系统'
    ],
    userInfo: {
      activeUsers: '20,000+ 风控用户',
      description: '正在使用风控系统'
    }
  },
]

const hotSignals = computed(() =>
  [...signals]
    .filter((s) => s.status === 'running')
    .sort((a, b) => b.cumulativeReturn - a.cumulativeReturn)
    .slice(0, 6)
)

const steps = [
  { title: '选择策略或信号', desc: '浏览系统策略库或信号广场，根据市场类型、风险等级、收益表现筛选适合您的方案。' },
  { title: '配置参数并启动', desc: '设置投入资金、杠杆倍数、止损比例等参数，确认后一键启动策略或跟随信号。' },
  { title: '实时监控收益', desc: '通过个人中心追踪策略运行状态、收益曲线、持仓情况，随时调整或停止。' },
]
</script>
