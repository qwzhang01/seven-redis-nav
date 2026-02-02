<template>
  <div class="notification-page">
    <div class="page-header">
      <h1><t-icon name="notification" /> 消息中心</h1>
      <div class="header-actions">
        <t-button variant="outline" size="small" @click="markAllRead">
          <t-icon name="check-double" /> 全部已读
        </t-button>
        <t-button variant="outline" size="small" @click="clearAll">
          <t-icon name="delete" /> 清空
        </t-button>
      </div>
    </div>
    
    <!-- 消息分类 -->
    <div class="notification-tabs">
      <t-tabs v-model="activeTab">
        <t-tab-panel value="all" :label="`全部 (${allCount})`" />
        <t-tab-panel value="trade" :label="`交易 (${tradeCount})`" />
        <t-tab-panel value="system" :label="`系统 (${systemCount})`" />
        <t-tab-panel value="risk" :label="`风控 (${riskCount})`" />
      </t-tabs>
    </div>
    
    <!-- 消息列表 -->
    <div class="notification-list">
      <div 
        v-for="notification in filteredNotifications" 
        :key="notification.id" 
        class="notification-item"
        :class="{ unread: !notification.read }"
        @click="readNotification(notification)"
      >
        <div class="notification-icon" :class="notification.type">
          <t-icon :name="getIcon(notification.type)" />
        </div>
        <div class="notification-content">
          <div class="notification-title">
            {{ notification.title }}
            <t-tag v-if="!notification.read" theme="danger" size="small">未读</t-tag>
          </div>
          <div class="notification-desc">{{ notification.description }}</div>
          <div class="notification-time">{{ notification.time }}</div>
        </div>
        <div class="notification-actions">
          <t-button variant="text" size="small" @click.stop="deleteNotification(notification)">
            <t-icon name="delete" />
          </t-button>
        </div>
      </div>
      
      <t-empty v-if="!filteredNotifications.length" description="暂无消息" />
    </div>
    
    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="filteredNotifications.length > 0">
      <t-pagination
        v-model:current="currentPage"
        :total="filteredNotifications.length"
        :page-size="pageSize"
        show-jumper
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const activeTab = ref('all')
const currentPage = ref(1)
const pageSize = ref(10)

// 通知数据
const notifications = ref([
  { id: 1, type: 'trade', title: '订单成交通知', description: '您的 BTC/USDT 买入订单已成交，成交数量 0.5 BTC，成交价格 $45,180', time: '5分钟前', read: false },
  { id: 2, type: 'risk', title: '风控警报', description: '当前回撤已达 8.5%，接近 20% 的阈值限制，请关注风险', time: '30分钟前', read: false },
  { id: 3, type: 'trade', title: '止盈触发', description: 'ETH/USDT 多单已触发止盈，盈利 $125.50', time: '1小时前', read: true },
  { id: 4, type: 'system', title: '系统维护通知', description: '平台将于今晚 22:00-23:00 进行系统维护，届时部分功能可能暂时不可用', time: '2小时前', read: true },
  { id: 5, type: 'trade', title: '订单失败', description: 'SOL/USDT 买入订单因余额不足被拒绝', time: '3小时前', read: true },
  { id: 6, type: 'system', title: '新功能上线', description: '合约交易功能已上线，支持最高 125 倍杠杆', time: '1天前', read: true },
  { id: 7, type: 'risk', title: '杠杆提醒', description: '当前杠杆使用率达到 60%，请注意风险控制', time: '1天前', read: true },
  { id: 8, type: 'trade', title: '策略启动', description: '网格交易策略已成功启动，正在监控市场', time: '2天前', read: true }
])

// 计数
const allCount = computed(() => notifications.value.filter(n => !n.read).length)
const tradeCount = computed(() => notifications.value.filter(n => n.type === 'trade' && !n.read).length)
const systemCount = computed(() => notifications.value.filter(n => n.type === 'system' && !n.read).length)
const riskCount = computed(() => notifications.value.filter(n => n.type === 'risk' && !n.read).length)

// 过滤
const filteredNotifications = computed(() => {
  if (activeTab.value === 'all') return notifications.value
  return notifications.value.filter(n => n.type === activeTab.value)
})

// 方法
const getIcon = (type) => {
  const icons = { trade: 'swap', system: 'info-circle', risk: 'error-circle' }
  return icons[type] || 'notification'
}

const readNotification = (notification) => {
  notification.read = true
}

const deleteNotification = (notification) => {
  const index = notifications.value.findIndex(n => n.id === notification.id)
  if (index > -1) {
    notifications.value.splice(index, 1)
    MessagePlugin.success('消息已删除')
  }
}

const markAllRead = () => {
  notifications.value.forEach(n => n.read = true)
  MessagePlugin.success('已全部标为已读')
}

const clearAll = () => {
  notifications.value = []
  MessagePlugin.success('已清空所有消息')
}
</script>

<style lang="less" scoped>
.notification-page { padding: 24px; background: #0d1117; min-height: calc(100vh - 56px); }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
  h1 { margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 8px; }
  .header-actions { display: flex; gap: 12px; }
}

.notification-tabs { margin-bottom: 24px; }

.notification-list {
  .notification-item { display: flex; align-items: flex-start; gap: 16px; padding: 20px; background: #161b22; border-radius: 12px; margin-bottom: 12px; cursor: pointer; transition: all 0.2s;
    &:hover { background: #21262d; }
    &.unread { border-left: 4px solid var(--primary); }
    
    .notification-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px;
      &.trade { background: rgba(0,168,112,0.2); color: var(--green); }
      &.system { background: rgba(0,82,217,0.2); color: var(--primary); }
      &.risk { background: rgba(227,77,89,0.2); color: var(--red); }
    }
    
    .notification-content { flex: 1;
      .notification-title { font-weight: 500; color: #fff; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
      .notification-desc { color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.6; margin-bottom: 8px; }
      .notification-time { font-size: 12px; color: rgba(255,255,255,0.5); }
    }
  }
}

.pagination-wrapper { display: flex; justify-content: center; margin-top: 24px; }
</style>
