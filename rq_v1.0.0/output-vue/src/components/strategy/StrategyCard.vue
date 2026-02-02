<template>
  <div class="strategy-card" @click="$emit('click')">
    <div class="card-header">
      <div class="strategy-icon">
        <t-icon name="app" size="24px" />
      </div>
      <div class="strategy-info">
        <div class="strategy-name">{{ strategy.name }}</div>
        <div class="strategy-type">{{ strategy.type }}</div>
      </div>
    </div>
    
    <div class="card-stats">
      <div class="stat">
        <div class="stat-value" :class="strategy.return30d >= 0 ? 'positive' : 'negative'">
          {{ strategy.return30d >= 0 ? '+' : '' }}{{ strategy.return30d }}%
        </div>
        <div class="stat-label">近30天收益</div>
      </div>
      <div class="stat">
        <div class="stat-value negative">{{ strategy.maxDrawdown }}%</div>
        <div class="stat-label">最大回撤</div>
      </div>
    </div>
    
    <div class="card-footer">
      <t-tag :theme="getRiskTheme(strategy.risk)" variant="light" size="small">
        {{ getRiskIcon(strategy.risk) }} {{ getRiskText(strategy.risk) }}
      </t-tag>
      <span class="subscribers">{{ formatNumber(strategy.subscribers) }} 人订阅</span>
    </div>
    
    <div class="card-actions" @click.stop>
      <t-button
        variant="outline"
        :theme="strategy.favorite ? 'warning' : 'default'"
        @click="$emit('toggle-favorite', strategy.id)"
      >
        <t-icon :name="strategy.favorite ? 'star-filled' : 'star'" />
        {{ strategy.favorite ? '已收藏' : '收藏' }}
      </t-button>
      <t-button
        :theme="strategy.subscribed ? 'success' : 'primary'"
        @click="$emit('toggle-subscribe', strategy.id)"
      >
        <t-icon :name="strategy.subscribed ? 'check' : 'add'" />
        {{ strategy.subscribed ? '已订阅' : '订阅策略' }}
      </t-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  strategy: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'toggle-favorite', 'toggle-subscribe'])

const getRiskTheme = (risk) => {
  const themes = { low: 'success', medium: 'warning', high: 'danger' }
  return themes[risk] || 'default'
}

const getRiskIcon = (risk) => {
  const icons = { low: '🟢', medium: '🟡', high: '🔴' }
  return icons[risk] || ''
}

const getRiskText = (risk) => {
  const texts = { low: '低风险', medium: '中风险', high: '高风险' }
  return texts[risk] || ''
}

const formatNumber = (num) => {
  return num.toLocaleString('en-US')
}
</script>

<style lang="less" scoped>
.strategy-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.strategy-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--brand), #5d9efe);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
}

.strategy-type {
  font-size: 12px;
  color: var(--text2);
  margin-top: 4px;
}

.card-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  
  .stat {
    text-align: center;
  }
  
  .stat-value {
    font-size: 18px;
    font-weight: 600;
    
    &.positive {
      color: var(--green);
    }
    
    &.negative {
      color: var(--red);
    }
  }
  
  .stat-label {
    font-size: 12px;
    color: var(--text2);
    margin-top: 4px;
  }
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .subscribers {
    font-size: 13px;
    color: var(--text2);
  }
}

.card-actions {
  display: flex;
  gap: 12px;
  
  .t-button {
    flex: 1;
  }
}
</style>
