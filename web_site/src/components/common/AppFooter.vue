<template>
  <footer class="bg-dark-800 border-t border-white/[0.06] mt-auto">
    <div class="page-container py-16">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
        <!-- Brand -->
        <div class="lg:col-span-1">
          <router-link to="/" class="flex items-center gap-3 mb-5">
            <div
                class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-sm">QA</div>
            <span class="text-white font-bold text-xl">Quanta<span
                class="gradient-text ml-1">量元</span></span>
          </router-link>
          <p class="text-dark-100 text-sm leading-relaxed mb-5">
            专业的量化交易策略与信号跟单平台，助力您的数字资产投资决策。
          </p>
          <div class="flex items-center gap-3">
            <a href="#" class="w-9 h-9 rounded-lg bg-dark-600 flex items-center justify-center text-dark-100 hover:text-primary-500 hover:bg-dark-500 transition-all">
              <Twitter :size="16" />
            </a>
            <a href="#" class="w-9 h-9 rounded-lg bg-dark-600 flex items-center justify-center text-dark-100 hover:text-primary-500 hover:bg-dark-500 transition-all">
              <Github :size="16" />
            </a>
            <a href="#" class="w-9 h-9 rounded-lg bg-dark-600 flex items-center justify-center text-dark-100 hover:text-primary-500 hover:bg-dark-500 transition-all">
              <MessageCircle :size="16" />
            </a>
          </div>
        </div>

        <!-- Links -->
        <div v-for="group in footerLinks" :key="group.title">
          <h4 class="text-white font-semibold mb-4">{{ group.title }}</h4>
          <ul class="space-y-2.5">
            <li v-for="link in group.links" :key="link.label">
              <router-link :to="link.to" class="text-sm text-dark-100 hover:text-primary-500 transition-colors">
                {{ link.label }}
              </router-link>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom -->
      <div class="mt-12 pt-8 border-t border-white/[0.06] flex flex-col md:flex-row items-center justify-between gap-4">
        <p class="text-sm text-dark-200">© {{ new Date().getFullYear() }}
          Quanta. All rights reserved.</p>
        <div class="flex items-center gap-6">
          <a href="#" class="text-sm text-dark-200 hover:text-primary-500 transition-colors">隐私政策</a>
          <a href="#" class="text-sm text-dark-200 hover:text-primary-500 transition-colors">服务条款</a>
          <a href="#" class="text-sm text-dark-200 hover:text-primary-500 transition-colors">风险提示</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { Twitter, Github, MessageCircle } from 'lucide-vue-next'

const footerLinks = [
  {
    title: '产品',
    links: [
      { label: '系统策略', to: '/system/strategies' },
      { label: '信号广场', to: '/system/signals' },
      { label: '收益排行榜', to: '/system/leaderboard' },
      { label: 'API 文档', to: '#' },
    ],
  },
  {
    title: '支持',
    links: [
      { label: '帮助中心', to: '#' },
      { label: '新手指南', to: '#' },
      { label: '常见问题', to: '#' },
      { label: '联系我们', to: '#' },
    ],
  },
  {
    title: '关于',
    links: [
      { label: '关于我们', to: '#' },
      { label: '加入我们', to: '#' },
      { label: '合作伙伴', to: '#' },
      { label: '媒体报道', to: '#' },
    ],
  },
]
</script>
