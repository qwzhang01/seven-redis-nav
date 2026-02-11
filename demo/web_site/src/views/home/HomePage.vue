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
            <span class="text-sm text-primary-400 font-medium">专业量化交易平台</span>
          </div>

          <h1 class="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.1] mb-6 animate-fade-in-up" style="animation-delay: 0.1s">
            用数据驱动
            <span class="block gradient-text mt-2">每一次交易决策</span>
          </h1>

          <p class="text-lg md:text-xl text-dark-100 max-w-2xl mx-auto mb-10 animate-fade-in-up" style="animation-delay: 0.2s">
            Quant Meta 汇聚顶级量化策略与实盘信号，提供一站式策略订阅、信号跟单、收益排行，助力您在加密市场中获取持续稳定收益。
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up" style="animation-delay: 0.3s">
            <router-link to="/strategies" class="btn-primary text-base px-8 py-3.5 rounded-xl">
              探索策略
            </router-link>
            <router-link to="/signals" class="btn-outline text-base px-8 py-3.5 rounded-xl">
              浏览信号
            </router-link>
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

    <!-- Core Modules -->
    <section class="py-24">
      <div class="page-container">
        <div class="text-center mb-16">
          <h2 class="section-title">核心功能</h2>
          <p class="section-subtitle">从策略选择到信号跟单，一站式量化交易解决方案</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <router-link
            v-for="module in coreModules"
            :key="module.title"
            :to="module.to"
            class="glass-card-hover p-8 group"
          >
            <div class="flex items-start gap-5">
              <div class="w-14 h-14 rounded-xl flex items-center justify-center shrink-0 transition-all duration-300"
                   :class="module.iconBg">
                <component :is="module.icon" :size="26" :class="module.iconColor" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-xl font-bold text-white mb-2 group-hover:text-primary-400 transition-colors">
                  {{ module.title }}
                </h3>
                <p class="text-dark-100 text-sm leading-relaxed">{{ module.description }}</p>
                <div class="mt-4 flex items-center gap-2 text-primary-500 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>了解更多</span>
                  <ArrowRight :size="14" />
                </div>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- Hot Signals -->
    <section class="py-24 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-primary-500/[0.02] to-transparent" />
      <div class="page-container relative z-10">
        <div class="flex items-end justify-between mb-12">
          <div>
            <h2 class="section-title text-left">热门信号</h2>
            <p class="text-dark-100 text-lg">实时追踪高收益交易信号</p>
          </div>
          <router-link to="/signals" class="btn-outline !py-2 !px-5 text-sm hidden md:inline-flex items-center gap-2">
            查看全部 <ArrowRight :size="14" />
          </router-link>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="signal in hotSignals"
            :key="signal.id"
            class="glass-card-hover p-6 group cursor-pointer"
            @click="$router.push(`/signals/${signal.id}`)"
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
          </div>
        </div>
        <router-link to="/signals" class="btn-outline w-full mt-8 text-sm !py-3 md:hidden flex items-center justify-center gap-2">
          查看全部信号 <ArrowRight :size="14" />
        </router-link>
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
  { value: '200+', label: '量化策略' },
  { value: '5,000+', label: '活跃用户' },
  { value: '$12M+', label: '管理资产' },
  { value: '99.9%', label: '系统稳定性' },
]

const coreModules = [
  {
    title: '系统预设策略',
    description: '精选多种量化策略，涵盖网格交易、趋势跟踪、套利等类型，支持一键启动与自定义参数配置。',
    icon: Zap,
    iconBg: 'bg-primary-500/10',
    iconColor: 'text-primary-400',
    to: '/strategies',
  },
  {
    title: '信号广场',
    description: '汇聚全网优质交易信号，支持模拟盘与实盘筛选，一键跟单，实时同步交易动作。',
    icon: Radio,
    iconBg: 'bg-accent-blue/10',
    iconColor: 'text-blue-400',
    to: '/signals',
  },
  {
    title: '收益排行榜',
    description: '透明公开的信号收益排行，按累计收益、回撤等维度排序，助您发现顶级交易者。',
    icon: Trophy,
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    to: '/leaderboard',
  },
  {
    title: '个人中心',
    description: '管理您的策略订阅、信号跟单、API 密钥和账户设置，一站式追踪收益表现。',
    icon: User,
    iconBg: 'bg-accent-purple/10',
    iconColor: 'text-purple-400',
    to: '/user',
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
