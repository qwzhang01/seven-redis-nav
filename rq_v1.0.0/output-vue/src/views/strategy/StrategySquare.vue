<template>
  <div class="strategy-square">
    <div class="page-content">
      <h1 class="page-title">策略广场</h1>
      
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-group">
          <t-button
            v-for="cat in categories"
            :key="cat.value"
            :theme="activeCategory === cat.value ? 'primary' : 'default'"
            variant="outline"
            @click="activeCategory = cat.value"
          >
            {{ cat.label }}
          </t-button>
        </div>
        
        <t-input
          v-model="searchKeyword"
          placeholder="搜索策略..."
          clearable
          class="search-input"
        >
          <template #prefix-icon>
            <t-icon name="search" />
          </template>
        </t-input>
      </div>
      
      <!-- 策略卡片网格 -->
      <div class="strategy-grid">
        <StrategyCard
          v-for="strategy in filteredStrategies"
          :key="strategy.id"
          :strategy="strategy"
          @click="viewStrategy(strategy.id)"
          @toggle-favorite="toggleFavorite"
          @toggle-subscribe="toggleSubscribe"
        />
      </div>
      
      <!-- 加载更多 -->
      <div class="load-more">
        <t-button variant="outline" :loading="loading" @click="loadMore">
          加载更多
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import StrategyCard from '@/components/strategy/StrategyCard.vue'

const router = useRouter()

const loading = ref(false)
const searchKeyword = ref('')
const activeCategory = ref('all')

// 分类
const categories = [
  { value: 'all', label: '全部' },
  { value: 'trend', label: '趋势跟踪' },
  { value: 'grid', label: '网格交易' },
  { value: 'arbitrage', label: '套利' }
]

// 策略列表
const strategies = ref([
  {
    id: 1,
    name: '双均线趋势跟踪',
    type: '趋势跟踪',
    category: 'trend',
    return30d: 25.6,
    maxDrawdown: -8.2,
    risk: 'medium',
    subscribers: 1234,
    subscribed: false,
    favorite: false
  },
  {
    id: 2,
    name: 'BTC网格交易',
    type: '网格交易',
    category: 'grid',
    return30d: 12.3,
    maxDrawdown: -3.5,
    risk: 'low',
    subscribers: 3456,
    subscribed: true,
    favorite: true
  },
  {
    id: 3,
    name: 'ETH突破策略',
    type: '趋势跟踪',
    category: 'trend',
    return30d: 18.9,
    maxDrawdown: -12.1,
    risk: 'high',
    subscribers: 892,
    subscribed: false,
    favorite: false
  },
  {
    id: 4,
    name: '稳定币套利',
    type: '套利',
    category: 'arbitrage',
    return30d: 8.5,
    maxDrawdown: -1.2,
    risk: 'low',
    subscribers: 5678,
    subscribed: false,
    favorite: false
  },
  {
    id: 5,
    name: '波动率做多',
    type: '趋势跟踪',
    category: 'trend',
    return30d: -5.3,
    maxDrawdown: -15.8,
    risk: 'high',
    subscribers: 234,
    subscribed: false,
    favorite: false
  },
  {
    id: 6,
    name: '震荡区间策略',
    type: '网格交易',
    category: 'grid',
    return30d: 15.2,
    maxDrawdown: -6.5,
    risk: 'medium',
    subscribers: 1567,
    subscribed: false,
    favorite: true
  }
])

// 筛选后的策略
const filteredStrategies = computed(() => {
  let result = strategies.value
  
  if (activeCategory.value !== 'all') {
    result = result.filter(s => s.category === activeCategory.value)
  }
  
  if (searchKeyword.value) {
    result = result.filter(s => s.name.includes(searchKeyword.value))
  }
  
  return result
})

// 查看策略详情
const viewStrategy = (id) => {
  router.push(`/strategy/${id}`)
}

// 切换收藏
const toggleFavorite = (id) => {
  const strategy = strategies.value.find(s => s.id === id)
  if (strategy) {
    strategy.favorite = !strategy.favorite
    MessagePlugin.success(strategy.favorite ? '已收藏' : '已取消收藏')
  }
}

// 切换订阅
const toggleSubscribe = (id) => {
  const strategy = strategies.value.find(s => s.id === id)
  if (strategy) {
    strategy.subscribed = !strategy.subscribed
    MessagePlugin.success(strategy.subscribed ? '订阅成功' : '已取消订阅')
  }
}

// 加载更多
const loadMore = async () => {
  loading.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))
  loading.value = false
  MessagePlugin.info('没有更多数据了')
}
</script>

<style lang="less" scoped>
.strategy-square {
  background: var(--bg);
  min-height: calc(100vh - 56px);
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: center;
  
  .filter-group {
    display: flex;
    gap: 8px;
  }
  
  .search-input {
    margin-left: auto;
    width: 250px;
  }
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
