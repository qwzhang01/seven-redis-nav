<template>
  <div>
    <!-- Hero Section -->
    <section class="relative min-h-[90vh] flex items-center overflow-hidden">
      <!-- Background Effects -->
      <div class="absolute inset-0 bg-hero-glow" />
      <div
        class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary-500/5 rounded-full blur-[120px]" />
      <div class="absolute top-1/3 right-0 w-[400px] h-[400px] bg-accent-blue/5 rounded-full blur-[100px]" />
      <!-- Grid Pattern -->
      <div class="absolute inset-0 opacity-[0.03]"
        style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 60px 60px;" />

      <div class="page-container relative z-10 pt-24">
        <div class="max-w-4xl mx-auto text-center">
          <!-- Badge -->
          <div
            class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20 mb-8 animate-fade-in-up">
            <span class="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
            <span class="text-sm text-primary-400 font-medium">专为专业交易者设计</span>
          </div>

          <h1 class="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold leading-[1.1] mb-6 animate-fade-in-up"
            style="animation-delay: 0.1s">
            更明智地交易
            <span class="block gradient-text mt-2">用数据驱动每一次决策</span>
          </h1>

          <p class="text-lg md:text-xl text-dark-100 max-w-2xl mx-auto mb-10 animate-fade-in-up"
            style="animation-delay: 0.2s">
            Quant Meta 的交易指标享誉全球并屡获殊荣是有原因的。融合先进的趋势逻辑、结构分析、流动性模型和成交量智能，为您提供反映真实市场行为而非猜测的信号。
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 animate-fade-in-up"
            style="animation-delay: 0.3s">
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
          <h2 class="section-title">核心功能</h2>
          <p class="section-subtitle">从策略选择到信号跟单，一站式量化交易解决方案</p>
        </div>

        <!-- Grid Layout with Picture 2 Style -->
        <div class="space-y-16">
          <!-- Main Signal & Alert Section -->
          <div class="glass-card p-8 rounded-2xl border border-white/10">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <!-- Left: Content -->
              <div class="space-y-6">
                <!-- Badge -->
                <div
                  class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-500/10 border border-primary-500/20">
                  <span class="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
                  <span class="text-sm text-primary-400 font-medium">专为专业交易者设计的指标</span>
                </div>

                <h3 class="text-2xl font-bold text-white">信号与警报</h3>

                <p class="text-dark-100 text-lg leading-relaxed">
                  Quant Meta 的交易指标融合了先进的趋势逻辑、结构分析、流动性模型和成交量智能，为您提供反映真实市场行为而非猜测的信号。无论是趋势信号、BOS/CHOCH
                  警报、智能带量测还是流动性抢占，每个警报都经过精心设计，旨在提供清晰的提示、精准的时机和可靠的判断。
                </p>

                <!-- Features Grid -->
                <div class="grid grid-cols-2 gap-4">
                  <div v-for="feature in ['趋势逻辑', '结构分析', '流动性模型', '成交量智能']" :key="feature"
                    class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full bg-primary-500" />
                    <span class="text-dark-100 text-sm">{{ feature }}</span>
                  </div>
                </div>

                <!-- Action Button -->
                <div class="pt-4">
                  <a href="/system/signals" target="_blank"
                    class="btn-primary inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base">
                    <span>获取指标</span>
                    <ArrowRight :size="16" />
                  </a>
                </div>
              </div>

              <!-- Right: Chart Visualization -->
              <div class="relative group">
                <div
                  class="bg-gradient-to-br from-primary-500/5 to-accent-blue/5 rounded-xl border border-white/10 p-6 h-64 flex items-center justify-center">
                  <!-- Chart Background Grid -->
                  <div class="absolute inset-0 opacity-10"
                    style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 20px 20px;" />

                  <!-- Main Chart Line -->
                  <div class="absolute bottom-0 left-0 right-0 h-32">
                    <svg class="w-full h-full" viewBox="0 0 400 160">
                      <path d="M20,100 Q60,80 100,120 Q140,60 180,100 Q220,140 260,80 Q300,120 340,100" fill="none"
                        stroke="#3b82f6" stroke-width="2" class="animate-draw-line" style="animation-delay: 0.3s" />
                    </svg>
                  </div>

                  <!-- Chart Points -->
                  <div
                    class="absolute top-1/4 left-1/4 w-3 h-3 rounded-full bg-primary-500/80 shadow-lg shadow-primary-500/30 animate-pulse" />
                  <div
                    class="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-accent-blue/80 shadow-lg shadow-blue-500/30 animate-pulse" />
                  <div
                    class="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-emerald-500/80 shadow-lg shadow-emerald-500/30 animate-pulse" />
                </div>

                <!-- Performance Stats -->
                <div class="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div class="text-lg font-bold text-white">98.7%</div>
                    <div class="text-xs text-dark-100">信号准确率</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">23.5%</div>
                    <div class="text-xs text-dark-100">平均收益</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">1.8秒</div>
                    <div class="text-xs text-dark-100">响应速度</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- System Strategy Module -->
          <div class="glass-card p-8 rounded-2xl border border-white/10">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <!-- Left: Chart Visualization -->
              <div class="relative group">
                <div
                  class="bg-gradient-to-br from-accent-blue/5 to-primary-500/5 rounded-xl border border-white/10 p-6 h-64 flex items-center justify-center">
                  <!-- Chart Background Grid -->
                  <div class="absolute inset-0 opacity-10"
                    style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 20px 20px;" />

                  <!-- Strategy Performance Chart -->
                  <div class="absolute bottom-0 left-0 right-0 h-32">
                    <svg class="w-full h-full" viewBox="0 0 400 160">
                      <path d="M20,140 Q60,100 100,120 Q140,80 180,100 Q220,60 260,80 Q300,100 340,60" fill="none"
                        stroke="#0ea5e9" stroke-width="2" class="animate-draw-line" style="animation-delay: 0.3s" />
                    </svg>
                  </div>

                  <!-- Chart Points -->
                  <div
                    class="absolute top-1/3 left-1/4 w-3 h-3 rounded-full bg-accent-blue/80 shadow-lg shadow-blue-500/30 animate-pulse" />
                  <div
                    class="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-primary-500/80 shadow-lg shadow-primary-500/30 animate-pulse" />
                  <div
                    class="absolute bottom-1/3 right-1/4 w-3 h-3 rounded-full bg-emerald-500/80 shadow-lg shadow-emerald-500/30 animate-pulse" />
                </div>

                <!-- Performance Stats -->
                <div class="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div class="text-lg font-bold text-white">85.2%</div>
                    <div class="text-xs text-dark-100">策略胜率</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">18.7%</div>
                    <div class="text-xs text-dark-100">年化收益</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">0.95</div>
                    <div class="text-xs text-dark-100">夏普比率</div>
                  </div>
                </div>
              </div>

              <!-- Right: Content -->
              <div class="space-y-6">
                <!-- Badge -->
                <div
                  class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-blue/10 border border-accent-blue/20">
                  <span class="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
                  <span class="text-sm text-accent-blue font-medium">智能量化策略系统</span>
                </div>

                <h3 class="text-2xl font-bold text-white">系统策略</h3>

                <p class="text-dark-100 text-lg leading-relaxed">
                  基于深度学习和强化学习的量化策略系统，支持多因子模型、风险平价、动量策略等高级算法，为专业交易者提供机构级别的策略执行能力。从策略回测到实盘运行，全程自动化管理。
                </p>

                <!-- Features Grid -->
                <div class="grid grid-cols-2 gap-4">
                  <div v-for="feature in ['多因子模型策略', '实时风险监控', '自动参数优化', '回测验证系统']" :key="feature"
                    class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full bg-accent-blue" />
                    <span class="text-dark-100 text-sm">{{ feature }}</span>
                  </div>
                </div>

                <!-- Action Button -->
                <div class="pt-4">
                  <a href="/system/strategies" target="_blank"
                    class="btn-primary inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base">
                    <span>探索策略</span>
                    <ArrowRight :size="16" />
                  </a>
                </div>
              </div>
            </div>
          </div>

          <!-- Market Depth Analysis Module -->
          <div class="glass-card p-8 rounded-2xl border border-white/10">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <!-- Left: Content -->
              <div class="space-y-6">
                <!-- Badge -->
                <div
                  class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20">
                  <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span class="text-sm text-amber-400 font-medium">专业市场微观分析</span>
                </div>

                <h3 class="text-2xl font-bold text-white">市场深度分析</h3>

                <p class="text-dark-100 text-lg leading-relaxed">
                  实时监控订单簿深度、流动性分布、大单动向等关键指标，提供专业的市场微观结构分析，帮助您把握最佳入场时机。深度洞察市场情绪和资金流向。
                </p>

                <!-- Features Grid -->
                <div class="grid grid-cols-2 gap-4">
                  <div v-for="feature in ['订单簿深度监控', '流动性热力图', '大单追踪系统', '市场情绪分析']" :key="feature"
                    class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full bg-amber-500" />
                    <span class="text-dark-100 text-sm">{{ feature }}</span>
                  </div>
                </div>

                <!-- Action Button -->
                <div class="pt-4">
                  <button
                    class="btn-outline inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base cursor-not-allowed opacity-50">
                    <span>深度分析</span>
                    <ArrowRight :size="16" />
                  </button>
                </div>
              </div>

              <!-- Right: Chart Visualization -->
              <div class="relative group">
                <div
                  class="bg-gradient-to-br from-amber-500/5 to-primary-500/5 rounded-xl border border-white/10 p-6 h-64 flex items-center justify-center">
                  <!-- Chart Background Grid -->
                  <div class="absolute inset-0 opacity-10"
                    style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 20px 20px;" />

                  <!-- Depth Analysis Chart -->
                  <div class="absolute bottom-0 left-0 right-0 h-32">
                    <svg class="w-full h-full" viewBox="0 0 400 160">
                      <path d="M20,80 Q60,120 100,100 Q140,140 180,120 Q220,100 260,140 Q300,120 340,100" fill="none"
                        stroke="#f59e0b" stroke-width="2" class="animate-draw-line" style="animation-delay: 0.3s" />
                    </svg>
                  </div>

                  <!-- Chart Points -->
                  <div
                    class="absolute top-1/4 left-1/4 w-3 h-3 rounded-full bg-amber-500/80 shadow-lg shadow-amber-500/30 animate-pulse" />
                  <div
                    class="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-primary-500/80 shadow-lg shadow-primary-500/30 animate-pulse" />
                  <div
                    class="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-red-500/80 shadow-lg shadow-red-500/30 animate-pulse" />
                </div>

                <!-- Performance Stats -->
                <div class="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div class="text-lg font-bold text-white">92.3%</div>
                    <div class="text-xs text-dark-100">分析准确率</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">15.8%</div>
                    <div class="text-xs text-dark-100">入场时机优化</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">2.1秒</div>
                    <div class="text-xs text-dark-100">数据更新频率</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Risk Management Module -->
          <div class="glass-card p-8 rounded-2xl border border-white/10">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <!-- Left: Chart Visualization -->
              <div class="relative group">
                <div
                  class="bg-gradient-to-br from-purple-500/5 to-primary-500/5 rounded-xl border border-white/10 p-6 h-64 flex items-center justify-center">
                  <!-- Chart Background Grid -->
                  <div class="absolute inset-0 opacity-10"
                    style="background-image: linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 20px 20px;" />

                  <!-- Risk Management Chart -->
                  <div class="absolute bottom-0 left-0 right-0 h-32">
                    <svg class="w-full h-full" viewBox="0 0 400 160">
                      <path d="M20,100 Q60,80 100,100 Q140,120 180,100 Q220,80 260,100 Q300,120 340,100" fill="none"
                        stroke="#a855f7" stroke-width="2" class="animate-draw-line" style="animation-delay: 0.3s" />
                    </svg>
                  </div>

                  <!-- Chart Points -->
                  <div
                    class="absolute top-1/4 left-1/4 w-3 h-3 rounded-full bg-purple-500/80 shadow-lg shadow-purple-500/30 animate-pulse" />
                  <div
                    class="absolute top-1/2 left-1/2 w-3 h-3 rounded-full bg-primary-500/80 shadow-lg shadow-primary-500/30 animate-pulse" />
                  <div
                    class="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-green-500/80 shadow-lg shadow-green-500/30 animate-pulse" />
                </div>

                <!-- Performance Stats -->
                <div class="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div class="text-lg font-bold text-white">99.5%</div>
                    <div class="text-xs text-dark-100">风控成功率</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">45.2%</div>
                    <div class="text-xs text-dark-100">风险降低</div>
                  </div>
                  <div>
                    <div class="text-lg font-bold text-white">0.3秒</div>
                    <div class="text-xs text-dark-100">响应时间</div>
                  </div>
                </div>
              </div>

              <!-- Right: Content -->
              <div class="space-y-6">
                <!-- Badge -->
                <div
                  class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20">
                  <span class="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                  <span class="text-sm text-purple-400 font-medium">全面风控保障</span>
                </div>

                <h3 class="text-2xl font-bold text-white">风险管理系统</h3>

                <p class="text-dark-100 text-lg leading-relaxed">
                  全面的风险管理框架，包含仓位控制、止损止盈、波动率监控等多维度风控措施，确保交易安全稳定运行。智能风控系统实时保护您的资产安全。
                </p>

                <!-- Features Grid -->
                <div class="grid grid-cols-2 gap-4">
                  <div v-for="feature in ['智能止损止盈', '仓位动态调整', '波动率预警', '压力测试系统']" :key="feature"
                    class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full bg-purple-500" />
                    <span class="text-dark-100 text-sm">{{ feature }}</span>
                  </div>
                </div>

                <!-- Action Button -->
                <div class="pt-4">
                  <button
                    class="btn-outline inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base cursor-not-allowed opacity-50">
                    <span>风险管理</span>
                    <ArrowRight :size="16" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Preferred Strategies - Modern Polling Display -->
    <section class="py-20 relative">
      <div class="absolute inset-0 bg-gradient-to-b from-transparent via-accent-blue/[0.02] to-transparent"></div>
      <div class="page-container relative z-10">
        <div class="flex items-end justify-between mb-12">
          <div>
            <h2 class="section-title text-left">优选策略</h2>
            <p class="text-dark-100 text-lg">基于AI算法精选的高胜率量化策略，持续优化，自动轮换</p>
          </div>
          <a href="/system/strategies" target="_blank"
            class="btn-outline !py-2 !px-5 text-sm hidden md:inline-flex items-center gap-2">
            查看全部
            <ArrowRight :size="14" />
          </a>
        </div>

        <!-- Modern Polling Container -->
        <div class="relative">
          <!-- Active Strategy Display with Transition -->
          <div
            class="glass-card strategy-card rounded-2xl border border-white/10 overflow-hidden transition-all duration-500 ease-in-out"
            :key="currentStrategyIndex">
            <div class="grid grid-cols-1 lg:grid-cols-[1fr_1.5fr_1fr] gap-6 p-8">
              <!-- Left Column: Strategy Text and Statistics -->
              <div class="space-y-4">
                <!-- Strategy Badge -->
                <div
                  class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full color-transition badge-glow strategy-fade-in"
                  :class="strategies[currentStrategyIndex].colorClass">
                  <span class="w-2 h-2 rounded-full badge-glow"
                    :class="strategies[currentStrategyIndex].dotColor"></span>
                  <span class="text-sm font-medium color-transition"
                    :class="strategies[currentStrategyIndex].textColor">
                    {{ strategies[currentStrategyIndex].badge }}
                  </span>
                </div>

                <!-- Strategy Title -->
                <h3 class="text-xl font-bold text-white color-transition strategy-fade-in">{{ strategies[currentStrategyIndex].title }}</h3>

                <!-- Strategy Description -->
                <p class="text-dark-100 text-base leading-relaxed color-transition strategy-fade-in">
                  {{ strategies[currentStrategyIndex].description }}
                </p>

                <!-- Statistics -->
                <div class="grid grid-cols-2 gap-3">
                  <div v-for="(stat, index) in strategies[currentStrategyIndex].stats" :key="index"
                    class="float-animation strategy-fade-in" :style="{ animationDelay: `${index * 0.2}s` }">
                    <div class="text-base font-bold text-white color-transition">{{ stat.value }}</div>
                    <div class="text-xs text-dark-100">{{ stat.label }}</div>
                  </div>
                </div>
              </div>

              <!-- Middle Column: Strategy Chart (Larger) -->
              <div class="relative flex items-center justify-center strategy-fade-in">
                <div
                  class="bg-gradient-to-br from-primary-500/5 to-accent-blue/5 rounded-xl border border-white/10 p-8 h-80 w-full">
                  <!-- Animated Chart -->
                  <div class="absolute inset-0 flex items-center justify-center">
                    <svg class="w-full h-40" viewBox="0 0 400 200">
                      <path :d="strategies[currentStrategyIndex].chartPath" fill="none"
                        :stroke="strategies[currentStrategyIndex].chartColor" stroke-width="3"
                        class="animate-draw-line color-transition" style="animation-delay: 0.2s" />
                    </svg>
                  </div>
                  
                  <!-- Performance Ring -->
                  <div class="absolute top-6 right-6 w-20 h-20 float-animation">
                    <svg class="w-full h-full" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="40" stroke="rgba(255,255,255,0.1)" stroke-width="8" fill="none" />
                      <circle cx="50" cy="50" r="40" :stroke="strategies[currentStrategyIndex].chartColor"
                        stroke-width="8" fill="none" stroke-dasharray="251.2"
                        :stroke-dashoffset="251.2 - (strategies[currentStrategyIndex].performance * 251.2 / 100)"
                        class="performance-ring color-transition" />
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center">
                      <span class="text-sm font-bold text-white">{{ strategies[currentStrategyIndex].performance }}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Right Column: Strategy Features + Follow Button (Compact) -->
              <div class="space-y-4">
                <!-- Strategy Features -->
                <div class="space-y-4 strategy-fade-in">
                  <h4 class="text-base font-semibold text-white color-transition">策略特性</h4>
                  <div class="space-y-2">
                    <div v-for="(feature, index) in strategies[currentStrategyIndex].features" :key="index"
                      class="flex items-center gap-2 p-2 rounded-lg bg-white/5 color-transition hover:bg-white/10 float-animation strategy-fade-in"
                      :style="{ animationDelay: `${index * 0.1}s` }">
                      <div class="w-1.5 h-1.5 rounded-full badge-glow" :class="strategies[currentStrategyIndex].dotColor">
                      </div>
                      <span class="text-dark-100 text-xs">{{ feature }}</span>
                    </div>
                  </div>

                  <!-- Strategy Tags -->
                  <div class="flex flex-wrap gap-1 pt-2">
                    <span v-for="(tag, index) in strategies[currentStrategyIndex].tags" :key="index"
                      class="px-2 py-0.5 rounded-full text-xs border color-transition float-animation strategy-fade-in"
                      :class="strategies[currentStrategyIndex].tagClass"
                      :style="{ animationDelay: `${index * 0.15}s` }">
                      {{ tag }}
                    </span>
                  </div>
                </div>

                <!-- Follow Button -->
                <button
                  class="btn-primary inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm color-transition hover:scale-105 float-animation strategy-fade-in">
                  <span>立即跟随</span>
                </button>
              </div>
            </div>

            <!-- Strategy Indicator -->
            <div class="flex justify-center mt-8 space-x-2">
              <div v-for="(strategy, index) in strategies" :key="index" @click="currentStrategyIndex = index"
                class="cursor-pointer color-transition"
                :class="currentStrategyIndex === index ? 'scale-110' : 'opacity-50 hover:opacity-75'">
                <div class="w-12 h-2 rounded-full color-transition badge-glow"
                  :class="currentStrategyIndex === index ? strategy.indicatorActiveClass : strategy.indicatorInactiveClass" />
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
          <a href="/system/signals" target="_blank"
            class="btn-outline !py-2 !px-5 text-sm hidden md:inline-flex items-center gap-2">
            查看全部
            <ArrowRight :size="14" />
          </a>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <a v-for="signal in hotSignals" :key="signal.id" :href="`/system/signals/${signal.id}`" target="_blank"
            class="glass-card-hover p-6 group cursor-pointer">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-3">
                <div
                  class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
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
                <div class="text-lg font-bold"
                  :class="signal.cumulativeReturn >= 0 ? 'text-emerald-400' : 'text-red-400'">
                  {{ signal.cumulativeReturn >= 0 ? '+' : '' }}{{ signal.cumulativeReturn.toFixed(2) }}%
                </div>
              </div>
              <div>
                <div class="text-xs text-dark-100 mb-1">最大回撤</div>
                <div class="text-lg font-bold text-amber-400">{{ signal.maxDrawdown.toFixed(2) }}%</div>
              </div>
            </div>

            <ReturnCurveChart v-if="signal.returnCurve?.length" :data="signal.returnCurve" :labels="signal.returnCurveLabels" :height="100"
              :color="signal.cumulativeReturn >= 0 ? '#10b981' : '#ef4444'" />

            <div class="flex items-center justify-between mt-4 pt-4 border-t border-white/[0.06]">
              <span class="text-xs text-dark-100">{{ signal.followers }} 人跟随</span>
              <span class="text-xs text-dark-100">运行 {{ signal.runDays }} 天</span>
            </div>
          </a>
        </div>
        <a href="/system/signals" target="_blank"
          class="btn-outline w-full mt-8 text-sm !py-3 md:hidden flex items-center justify-center gap-2">
          查看全部信号
          <ArrowRight :size="14" />
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
            <div
              class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center mx-auto mb-6 border border-primary-500/20">
              <span class="text-2xl font-bold gradient-text">{{ i + 1 }}</span>
            </div>
            <h3 class="text-lg font-bold text-white mb-3">{{ step.title }}</h3>
            <p class="text-dark-100 text-sm leading-relaxed">{{ step.desc }}</p>
            <!-- Connector -->
            <div v-if="i < steps.length - 1"
              class="hidden md:block absolute top-8 left-[60%] w-[80%] border-t border-dashed border-dark-300" />
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Zap, Radio, Trophy, User, ArrowRight, ArrowLeft, AlertTriangle } from 'lucide-vue-next'
import StatusDot from '@/components/common/StatusDot.vue'
import ReturnCurveChart from '@/components/charts/ReturnCurveChart.vue'
import { signals } from '@/utils/mockData'

// Modern Polling Logic for Preferred Strategies
const currentStrategyIndex = ref(0)
let pollingInterval: NodeJS.Timeout | null = null

// Strategy Data
const strategies = [
  {
    badge: "AI精选策略",
    title: "趋势动量策略",
    description: "基于多时间框架趋势分析，结合成交量确认，捕捉强势突破行情。策略胜率高达87.5%，最大回撤控制在15%以内。",
    stats: [
      { value: "87.5%", label: "策略胜率" },
      { value: "15%", label: "最大回撤" },
      { value: "23.8%", label: "年化收益" },
      { value: "1.25", label: "夏普比率" }
    ],
    features: ["多时间框架分析", "成交量确认", "趋势跟踪", "动量捕捉"],
    tags: ["高胜率", "趋势跟踪", "突破策略"],
    chartPath: "M20,100 Q60,80 100,120 Q140,60 180,100 Q220,140 260,80 Q300,120 340,100",
    chartColor: "#10b981",
    performance: 87.5,
    colorClass: "bg-emerald-500/10 border border-emerald-500/20",
    dotColor: "bg-emerald-500",
    textColor: "text-emerald-400",
    tagClass: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    indicatorActiveClass: "bg-emerald-500 w-16",
    indicatorInactiveClass: "bg-white/30 w-8"
  },
  {
    badge: "均值回归策略",
    title: "震荡突破策略",
    description: "基于布林带和RSI指标，识别超买超卖区域，结合成交量突破确认，捕捉震荡行情中的突破机会。",
    stats: [
      { value: "82.3%", label: "策略胜率" },
      { value: "12%", label: "最大回撤" },
      { value: "18.5%", label: "年化收益" },
      { value: "1.08", label: "夏普比率" }
    ],
    features: ["布林带分析", "RSI指标", "超买超卖识别", "突破确认"],
    tags: ["震荡策略", "均值回归", "风险控制"],
    chartPath: "M20,100 Q60,120 100,80 Q140,100 180,120 Q220,80 260,100 Q300,80 340,100",
    chartColor: "#3b82f6",
    performance: 82.3,
    colorClass: "bg-blue-500/10 border border-blue-500/20",
    dotColor: "bg-blue-500",
    textColor: "text-blue-400",
    tagClass: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    indicatorActiveClass: "bg-blue-500 w-16",
    indicatorInactiveClass: "bg-white/30 w-8"
  },
  {
    badge: "套利策略",
    title: "跨期套利策略",
    description: "利用期货合约间的价差波动，结合统计套利模型，实现低风险稳定收益。策略年化波动率仅8.2%。",
    stats: [
      { value: "76.8%", label: "策略胜率" },
      { value: "8.2%", label: "年化波动" },
      { value: "15.3%", label: "年化收益" },
      { value: "1.86", label: "夏普比率" }
    ],
    features: ["价差分析", "统计套利", "低风险", "稳定收益"],
    tags: ["套利策略", "低波动", "稳定收益"],
    chartPath: "M20,100 Q60,90 100,110 Q140,95 180,105 Q220,100 260,95 Q300,105 340,100",
    chartColor: "#8b5cf6",
    performance: 76.8,
    colorClass: "bg-purple-500/10 border border-purple-500/20",
    dotColor: "bg-purple-500",
    textColor: "text-purple-400",
    tagClass: "bg-purple-500/10 border-purple-500/20 text-purple-400",
    indicatorActiveClass: "bg-purple-500 w-16",
    indicatorInactiveClass: "bg-white/30 w-8"
  }
]

const nextStrategy = () => {
  // Reset animation state before switching
  const container = document.querySelector('.strategy-card') as HTMLElement
  if (container) {
    container.style.opacity = '0'
    container.style.transform = 'translateY(20px)'
  }

  // Switch to next strategy
  currentStrategyIndex.value = (currentStrategyIndex.value + 1) % strategies.length

  // Restore animation after a brief delay
  setTimeout(() => {
    if (container) {
      container.style.opacity = '1'
      container.style.transform = 'translateY(0)'
    }
  }, 50)
}

const startPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
  pollingInterval = setInterval(() => {
    nextStrategy()
  }, 5000) // Change strategy every 5 seconds
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

const heroStats = [
  { value: '98.7%', label: '信号准确率' },
  { value: '25,000+', label: '专业交易者' },
  { value: '$850M+', label: '日均交易量' },
  { value: '99.99%', label: '系统稳定性' },
]

const coreModules = [
  {
    title: '量化策略引擎',
    description: '基于深度学习和强化学习的量化策略系统，支持多因子模型、风险平价、动量策略等高级算法，为专业交易者提供机构级别的策略执行能力。',
    icon: Radio,
    iconBg: 'bg-accent-blue/10',
    iconColor: 'text-blue-400',
    to: '/system/strategies',
    buttonText: '探索策略',
    features: [
      '多因子模型策略',
      '实时风险监控',
      '自动参数优化',
      '回测验证系统'
    ]
  },
  {
    title: '市场深度分析',
    description: '实时监控订单簿深度、流动性分布、大单动向等关键指标，提供专业的市场微观结构分析，帮助您把握最佳入场时机。',
    icon: Trophy,
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    to: '/system/analysis',
    buttonText: '深度分析',
    features: [
      '订单簿深度监控',
      '流动性热力图',
      '大单追踪系统',
      '市场情绪分析'
    ]
  },
  {
    title: '风险管理系统',
    description: '全面的风险管理框架，包含仓位控制、止损止盈、波动率监控等多维度风控措施，确保交易安全稳定运行。',
    icon: User,
    iconBg: 'bg-accent-purple/10',
    iconColor: 'text-purple-400',
    to: '/system/risk',
    buttonText: '风险管理',
    features: [
      '智能止损止盈',
      '仓位动态调整',
      '波动率预警',
      '压力测试系统'
    ]
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

<style scoped>
/* Modern Polling Animations */
.strategy-transition-enter-active {
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.strategy-transition-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.strategy-transition-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.strategy-transition-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(1.05);
}

/* Strategy Card Hover Effects */
.strategy-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Performance Ring Animation */
@keyframes ring-fill {
  0% {
    stroke-dashoffset: 251.2;
  }

  100% {
    stroke-dashoffset: 0;
  }
}

.performance-ring {
  animation: ring-fill 2s ease-out forwards;
}

/* Indicator Pulse Animation */
@keyframes indicator-pulse {

  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }

  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

.indicator-pulse {
  animation: indicator-pulse 2s infinite;
}

/* Chart Draw Animation */
.animate-draw-line {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: draw 3s ease-in-out forwards;
}

@keyframes draw {
  to {
    stroke-dashoffset: 0;
  }
}

/* Strategy Badge Glow Effect */
@keyframes badge-glow {

  0%,
  100% {
    box-shadow: 0 0 5px currentColor;
  }

  50% {
    box-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
  }
}

.badge-glow {
  animation: badge-glow 3s ease-in-out infinite;
}

/* Smooth Color Transitions */
.color-transition {
  transition: all 0.5s ease-in-out;
}

/* Floating Animation */
@keyframes float {

  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-10px);
  }
}

.float-animation {
  animation: float 6s ease-in-out infinite;
}

/* Strategy Card Hover Effects */
.strategy-card {
  transition: all 0.3s ease-in-out;
}

.strategy-card:hover {
  transform: scale(1.02);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

/* Performance Ring Animation */
.performance-ring {
  transition: all 1s ease-out;
}

/* Strategy Transition Animations */
.strategy-transition-enter-active {
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.strategy-transition-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.strategy-transition-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.strategy-transition-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Strategy Content Fade Animation */
@keyframes strategy-fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.strategy-fade-in {
  animation: strategy-fade-in 0.6s ease-out forwards;
}
</style>