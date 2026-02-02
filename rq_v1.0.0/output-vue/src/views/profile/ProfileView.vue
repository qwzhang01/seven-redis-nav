<template>
  <div class="profile-page">
    <div class="profile-header">
      <div class="user-info">
        <t-avatar size="80px" image="https://tdesign.gtimg.com/site/avatar.jpg" />
        <div class="user-details">
          <h2>{{ userInfo.nickname }}</h2>
          <p class="user-email">{{ userInfo.email }}</p>
          <div class="user-tags">
            <t-tag theme="primary">{{ userInfo.level }}</t-tag>
            <t-tag v-if="userInfo.isVip" theme="warning">VIP会员</t-tag>
          </div>
        </div>
      </div>
      <t-button variant="outline" @click="showEditProfile = true">
        <t-icon name="edit" /> 编辑资料
      </t-button>
    </div>
    
    <!-- 账户概览 -->
    <div class="account-overview">
      <div class="stat-card" v-for="stat in accountStats" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.bg }">
          <t-icon :name="stat.icon" />
        </div>
        <div class="stat-info">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value" :class="stat.class">{{ stat.value }}</div>
        </div>
      </div>
    </div>
    
    <!-- 功能菜单 -->
    <div class="profile-sections">
      <t-card title="账户安全" :bordered="false">
        <div class="menu-list">
          <div class="menu-item" @click="showChangePassword = true">
            <t-icon name="lock-on" />
            <span class="menu-label">修改密码</span>
            <span class="menu-value">定期更换密码更安全</span>
            <t-icon name="chevron-right" />
          </div>
          <div class="menu-item" @click="showBindPhone = true">
            <t-icon name="mobile" />
            <span class="menu-label">手机绑定</span>
            <span class="menu-value">{{ userInfo.phone || '未绑定' }}</span>
            <t-icon name="chevron-right" />
          </div>
          <div class="menu-item">
            <t-icon name="verify" />
            <span class="menu-label">两步验证</span>
            <span class="menu-value">
              <t-switch v-model="security.twoFactor" size="small" />
            </span>
          </div>
          <div class="menu-item">
            <t-icon name="finger" />
            <span class="menu-label">生物识别</span>
            <span class="menu-value">
              <t-switch v-model="security.biometric" size="small" />
            </span>
          </div>
        </div>
      </t-card>
      
      <t-card title="API管理" :bordered="false">
        <template #actions>
          <t-button size="small" @click="showAddApi = true"><t-icon name="add" /> 添加</t-button>
        </template>
        <div class="api-list">
          <div v-for="api in apiKeys" :key="api.id" class="api-item">
            <div class="api-info">
              <div class="api-name">{{ api.exchange }}</div>
              <div class="api-key">{{ api.apiKey }}</div>
              <div class="api-meta">
                <t-tag size="small" :theme="api.status === 'active' ? 'success' : 'default'">
                  {{ api.status === 'active' ? '正常' : '已禁用' }}
                </t-tag>
                <span>创建于 {{ api.createdAt }}</span>
              </div>
            </div>
            <div class="api-actions">
              <t-button variant="text" size="small" @click="testApi(api)">测试</t-button>
              <t-button variant="text" size="small" theme="danger" @click="deleteApi(api)">删除</t-button>
            </div>
          </div>
          <t-empty v-if="!apiKeys.length" description="暂无API密钥" />
        </div>
      </t-card>
      
      <t-card title="通知设置" :bordered="false">
        <div class="notification-settings">
          <div class="setting-item" v-for="setting in notificationSettings" :key="setting.key">
            <div class="setting-info">
              <div class="setting-label">{{ setting.label }}</div>
              <div class="setting-desc">{{ setting.description }}</div>
            </div>
            <t-switch v-model="setting.enabled" size="small" />
          </div>
        </div>
      </t-card>
      
      <t-card title="订阅与会员" :bordered="false">
        <div class="subscription-info">
          <div class="current-plan">
            <div class="plan-name">{{ subscription.plan }}</div>
            <div class="plan-expire">到期时间: {{ subscription.expireDate }}</div>
          </div>
          <t-button theme="warning">升级会员</t-button>
        </div>
        <t-divider />
        <div class="subscription-benefits">
          <h4>会员权益</h4>
          <div class="benefits-list">
            <div class="benefit-item" v-for="b in subscription.benefits" :key="b">
              <t-icon name="check-circle" class="text-success" /> {{ b }}
            </div>
          </div>
        </div>
      </t-card>
    </div>
    
    <!-- 修改密码弹窗 -->
    <t-dialog v-model:visible="showChangePassword" header="修改密码" @confirm="changePassword">
      <t-form :data="passwordForm" layout="vertical">
        <t-form-item label="当前密码">
          <t-input v-model="passwordForm.oldPassword" type="password" />
        </t-form-item>
        <t-form-item label="新密码">
          <t-input v-model="passwordForm.newPassword" type="password" />
        </t-form-item>
        <t-form-item label="确认新密码">
          <t-input v-model="passwordForm.confirmPassword" type="password" />
        </t-form-item>
      </t-form>
    </t-dialog>
    
    <!-- 编辑资料弹窗 -->
    <t-dialog v-model:visible="showEditProfile" header="编辑资料" @confirm="saveProfile">
      <t-form :data="profileForm" layout="vertical">
        <t-form-item label="昵称">
          <t-input v-model="profileForm.nickname" />
        </t-form-item>
        <t-form-item label="个性签名">
          <t-textarea v-model="profileForm.bio" :maxlength="100" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const showChangePassword = ref(false)
const showEditProfile = ref(false)
const showBindPhone = ref(false)
const showAddApi = ref(false)

// 用户信息
const userInfo = ref({
  nickname: 'CryptoTrader',
  email: 'trader@example.com',
  phone: '138****8888',
  level: 'Pro会员',
  isVip: true
})

// 账户统计
const accountStats = ref([
  { icon: 'wallet', label: '总资产', value: '125,680.50 USDT', bg: 'rgba(0,82,217,0.2)' },
  { icon: 'chart-line', label: '累计收益', value: '+25,680.50 USDT', bg: 'rgba(0,168,112,0.2)', class: 'text-success' },
  { icon: 'time', label: '交易天数', value: '365 天', bg: 'rgba(227,115,24,0.2)' },
  { icon: 'layers', label: '策略数量', value: '8 个', bg: 'rgba(134,96,217,0.2)' }
])

// 安全设置
const security = ref({
  twoFactor: true,
  biometric: false
})

// API密钥
const apiKeys = ref([
  { id: 1, exchange: 'Binance', apiKey: 'xxx...xxx123', status: 'active', createdAt: '2024-01-01' },
  { id: 2, exchange: 'OKX', apiKey: 'xxx...xxx456', status: 'active', createdAt: '2024-02-15' }
])

// 通知设置
const notificationSettings = ref([
  { key: 'trade', label: '交易通知', description: '订单成交、持仓变动等', enabled: true },
  { key: 'risk', label: '风险警报', description: '触发风控规则时通知', enabled: true },
  { key: 'system', label: '系统消息', description: '平台公告、维护通知等', enabled: true },
  { key: 'market', label: '行情提醒', description: '价格波动、异动预警', enabled: false }
])

// 订阅信息
const subscription = ref({
  plan: 'Pro会员',
  expireDate: '2025-12-31',
  benefits: ['无限策略数量', '实时行情数据', 'API调用无限制', '专属客服支持', '高级风控功能']
})

// 表单
const passwordForm = ref({ oldPassword: '', newPassword: '', confirmPassword: '' })
const profileForm = ref({ nickname: 'CryptoTrader', bio: '' })

// 方法
const changePassword = () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    MessagePlugin.error('两次密码不一致')
    return
  }
  showChangePassword.value = false
  MessagePlugin.success('密码修改成功')
}

const saveProfile = () => {
  userInfo.value.nickname = profileForm.value.nickname
  showEditProfile.value = false
  MessagePlugin.success('资料已更新')
}

const testApi = (api) => MessagePlugin.success(`${api.exchange} API连接正常`)
const deleteApi = (api) => {
  const index = apiKeys.value.findIndex(a => a.id === api.id)
  if (index > -1) { apiKeys.value.splice(index, 1); MessagePlugin.success('API已删除') }
}
</script>

<style lang="less" scoped>
.profile-page { padding: 24px; background: #0d1117; min-height: calc(100vh - 56px); }

.profile-header { display: flex; justify-content: space-between; align-items: center; padding: 24px; background: #161b22; border-radius: 12px; margin-bottom: 24px;
  .user-info { display: flex; align-items: center; gap: 20px;
    .user-details { h2 { margin: 0 0 8px; color: #fff; } .user-email { color: rgba(255,255,255,0.6); margin-bottom: 8px; } .user-tags { display: flex; gap: 8px; } }
  }
}

.account-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
  .stat-card { display: flex; align-items: center; gap: 16px; padding: 20px; background: #161b22; border-radius: 12px;
    .stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: var(--primary); }
    .stat-info { .stat-label { font-size: 13px; color: rgba(255,255,255,0.6); margin-bottom: 4px; } .stat-value { font-size: 18px; font-weight: 600; color: #fff; } }
  }
}

.text-success { color: var(--green) !important; }

.profile-sections { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;
  :deep(.t-card) { background: #161b22; border: none; }
}

.menu-list { .menu-item { display: flex; align-items: center; gap: 12px; padding: 16px 0; border-bottom: 1px solid #30363d; cursor: pointer;
  &:last-child { border-bottom: none; }
  &:hover { background: rgba(255,255,255,0.02); }
  .menu-label { flex: 1; color: #fff; }
  .menu-value { color: rgba(255,255,255,0.5); font-size: 13px; }
} }

.api-list { .api-item { display: flex; justify-content: space-between; align-items: center; padding: 16px; background: #21262d; border-radius: 8px; margin-bottom: 12px;
  .api-info { .api-name { font-weight: 500; color: #fff; margin-bottom: 4px; } .api-key { font-family: monospace; color: rgba(255,255,255,0.6); font-size: 13px; margin-bottom: 8px; } .api-meta { display: flex; align-items: center; gap: 12px; font-size: 12px; color: rgba(255,255,255,0.5); } }
} }

.notification-settings { .setting-item { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; border-bottom: 1px solid #30363d;
  &:last-child { border-bottom: none; }
  .setting-info { .setting-label { color: #fff; margin-bottom: 4px; } .setting-desc { font-size: 13px; color: rgba(255,255,255,0.5); } }
} }

.subscription-info { display: flex; justify-content: space-between; align-items: center;
  .current-plan { .plan-name { font-size: 20px; font-weight: 600; color: #fff; margin-bottom: 4px; } .plan-expire { color: rgba(255,255,255,0.6); font-size: 13px; } }
}

.subscription-benefits { h4 { color: #fff; margin-bottom: 16px; }
  .benefits-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
    .benefit-item { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.8); font-size: 14px; }
  }
}
</style>
