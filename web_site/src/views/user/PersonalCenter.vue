<template>
  <div class="pt-24 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-10">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
            <UserIcon :size="32" class="text-primary-400" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-extrabold text-white">个人中心</h1>
            <p class="text-dark-100">管理您的个人信息与邀请关系</p>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="glass-card p-1.5 mb-8 inline-flex gap-1">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          class="px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
          :class="activeTab === tab.value ? 'bg-primary-500/15 text-primary-400' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Profile Management -->
      <div v-if="activeTab === 'profile'" class="space-y-6">
        <!-- Basic Info -->
        <div class="glass-card p-6">
          <h3 class="text-white font-bold mb-6">基本信息</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm text-dark-100 mb-2">用户名</label>
              <input 
                v-model="userProfile.username"
                type="text" 
                class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
                placeholder="请输入用户名"
              />
            </div>
            <div>
              <label class="block text-sm text-dark-100 mb-2">邮箱</label>
              <input 
                v-model="userProfile.email"
                type="email" 
                class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
                placeholder="请输入邮箱"
                disabled
              />
            </div>
            <div>
              <label class="block text-sm text-dark-100 mb-2">手机号</label>
              <input 
                v-model="userProfile.phone"
                type="tel" 
                class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
                placeholder="请输入手机号"
              />
            </div>
            <div>
              <label class="block text-sm text-dark-100 mb-2">注册时间</label>
              <input 
                :value="formatDate(userProfile.createdAt)"
                type="text" 
                class="w-full bg-dark-600 border border-dark-500 rounded-lg px-3 py-2 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
                disabled
              />
            </div>
          </div>
          <!-- Save Button at the bottom -->
          <div class="flex justify-end mt-6 pt-4 border-t border-dark-500">
            <button @click="updateProfile" class="btn-primary !py-2 !px-6 text-sm">保存</button>
          </div>
        </div>
      </div>

      <!-- Invitation Management -->
      <div v-if="activeTab === 'invitation'" class="space-y-6">
        <!-- Invitation Code -->
        <div class="glass-card p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-white font-bold">邀请码</h3>
            <div class="flex items-center gap-2 text-sm text-dark-100">
              <span>已邀请 {{ combinedInvitationStats?.total_invited_users || 0 }} 人</span>
              <span class="text-emerald-400">+{{ combinedInvitationStats?.total_reward || 0 }} USDT</span>
            </div>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex-1 bg-dark-600 border border-dark-500 rounded-lg px-4 py-3">
              <div class="text-sm text-dark-100 mb-1">您的专属邀请码</div>
              <div class="text-lg font-mono font-bold text-primary-400">{{ combinedInvitationStats?.invitation_code || '加载中...' }}</div>
            </div>
            <button 
              @click="copyInvitationCode" 
              class="btn-primary !py-3 !px-6 text-sm flex items-center gap-2"
            >
              <Copy :size="14" />
              复制邀请码
            </button>
          </div>
          <div class="mt-4 text-xs text-dark-100">
            分享此邀请码给好友注册，您将获得邀请奖励
          </div>
        </div>

        <!-- Inviter Info -->
        <div v-if="combinedInvitationStats?.inviter_info" class="glass-card p-6">
          <h3 class="text-white font-bold mb-6">我的邀请人</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- 基本信息卡片 -->
            <div class="p-4 rounded-lg bg-dark-600/50 border border-dark-500">
              <div class="flex items-center gap-4 mb-4">
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <User :size="20" class="text-primary-400" />
                </div>
                <div>
                  <div class="text-white font-medium">{{ combinedInvitationStats.inviter_info.username }}</div>
                  <div class="text-xs text-dark-100">ID: {{ combinedInvitationStats.inviter_info.id }}</div>
                </div>
              </div>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-dark-100">级别:</span>
                  <span class="text-white">{{ combinedInvitationStats.inviter_info.level || '普通用户' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-dark-100">邀请时间:</span>
                  <span class="text-white">{{ formatDate(combinedInvitationStats.inviter_info.invitedAt) }}</span>
                </div>
                <div v-if="combinedInvitationStats.inviter_info.reward" class="flex justify-between">
                  <span class="text-dark-100">邀请奖励:</span>
                  <span class="text-emerald-400">+{{ combinedInvitationStats.inviter_info.reward }} USDT</span>
                </div>
              </div>
            </div>
            
            <!-- 联系信息卡片 -->
            <div class="p-4 rounded-lg bg-dark-600/50 border border-dark-500">
              <h4 class="text-white font-medium mb-3">联系信息</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-dark-100">邮箱:</span>
                  <span class="text-white">{{ combinedInvitationStats.inviter_info.email }}</span>
                </div>
                <div v-if="combinedInvitationStats.inviter_info.phone" class="flex justify-between">
                  <span class="text-dark-100">手机号:</span>
                  <span class="text-white">{{ combinedInvitationStats.inviter_info.phone }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-dark-100">状态:</span>
                  <span class="text-emerald-400">已邀请</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Invited Users List -->
        <div class="glass-card p-6">
          <h3 class="text-white font-bold mb-6">我邀请的用户</h3>
          <div class="space-y-4">
            <!-- Loading State -->
            <div v-if="invitedUsers.loading" class="text-center py-12">
              <Loader2 :size="24" class="text-primary-400 animate-spin mx-auto mb-2" />
              <span class="text-dark-100 text-sm">加载中...</span>
            </div>
            
            <!-- User List -->
            <div 
              v-else-if="invitedUsers.list.length > 0"
              v-for="user in invitedUsers.list" 
              :key="user.id"
              class="flex items-center justify-between p-4 rounded-lg bg-dark-600/50 border border-dark-500"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center">
                  <User :size="16" class="text-primary-400" />
                </div>
                <div>
                  <div class="text-white font-medium text-sm">{{ user.username }}</div>
                  <div class="text-xs text-dark-100">{{ formatDate(user.createdAt) }} 注册</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm font-medium text-emerald-400">+{{ user.reward || 0 }} USDT</div>
                <div class="text-xs text-dark-100">邀请奖励</div>
              </div>
            </div>
            
            <!-- Pagination -->
            <div v-if="!invitedUsers.loading && invitedUsers.total > 0" class="flex items-center justify-between pt-4 border-t border-dark-500">
              <div class="text-sm text-dark-100">
                共 {{ invitedUsers.total }} 条记录
              </div>
              <div class="flex items-center gap-2">
                <button 
                  @click="prevPage" 
                  :disabled="invitedUsers.page === 1 || invitedUsers.loading"
                  class="px-3 py-1.5 rounded text-sm transition-all"
                  :class="invitedUsers.page === 1 || invitedUsers.loading ? 'text-dark-300 cursor-not-allowed' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
                >
                  上一页
                </button>
                <span class="text-sm text-dark-100 px-2">
                  {{ invitedUsers.page }} / {{ invitedUsers.totalPages }}
                </span>
                <button 
                  @click="nextPage" 
                  :disabled="invitedUsers.page === invitedUsers.totalPages || invitedUsers.loading"
                  class="px-3 py-1.5 rounded text-sm transition-all"
                  :class="invitedUsers.page === invitedUsers.totalPages || invitedUsers.loading ? 'text-dark-300 cursor-not-allowed' : 'text-dark-100 hover:text-white hover:bg-white/[0.04]'"
                >
                  下一页
                </button>
              </div>
            </div>
            
            <!-- Empty State -->
            <div v-else-if="!invitedUsers.loading" class="text-center py-8 text-dark-100">
              <UserX :size="32" class="mx-auto mb-2 text-dark-200" />
              <div>暂无邀请用户</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { User as UserIcon, Copy, Loader2, User, UserX } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'
import {
  getInvitedUsers,
  getCombinedInvitationStats,
  InviterInfo
} from '@/utils/userApi'
import type { InvitedUser, CombinedInvitationStats } from '@/utils/userApi'

const authStore = useAuthStore()
const route = useRoute()
const activeTab = ref('profile')

// 根据URL参数设置默认标签页
if (route.query.tab === 'invitation') {
  activeTab.value = 'invitation'
}

const tabs = [
  { label: '个人信息', value: 'profile' },
  { label: '邀请管理', value: 'invitation' },
]

// User Profile Data
const userProfile = ref({
  username: authStore.user?.username || '用户昵称',
  email: authStore.user?.email || 'user@example.com',
  phone: '',
  invitationCode: 'QM2024INVITE',
  createdAt: new Date(authStore.user?.createdAt || '2024-01-01'),
})

// Inviter Info
const inviterInfo = ref<InviterInfo | null>(null)

// Invited Users Data
const invitedUsers = ref({
  list: [] as InvitedUser[],
  page: 1,
  pageSize: 10,
  total: 0,
  totalReward: 0,
  totalPages: 1,
  loading: false
})

// Combined Invitation Stats
const combinedInvitationStats = ref<CombinedInvitationStats | null>(null)

// Profile Management Functions
async function updateProfile() {
  try {
    await authStore.updateProfile({
      nickname: userProfile.value.username,
      phone: userProfile.value.phone
    })
    MessagePlugin.success('个人信息更新成功')
  } catch (error) {
    MessagePlugin.error('更新失败，请重试')
  }
}

function copyInvitationCode() {
  const invitationCode = combinedInvitationStats.value?.invitation_code || userProfile.value.invitationCode
  navigator.clipboard.writeText(invitationCode)
  MessagePlugin.success('邀请码已复制到剪贴板')
}

function formatDate(date: Date | string) {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  if(dateObj){
  return dateObj.toLocaleDateString('zh-CN')
  }
  return '';
}

async function fetchCombinedInvitationStats() {
  try {
    const response = await getCombinedInvitationStats()
    if (response) {
      combinedInvitationStats.value = response
      userProfile.value.invitationCode = response.invitation_code
      invitedUsers.value.totalReward = response.total_reward
      inviterInfo.value = response.inviter_info || null
    }
  } catch (error) {
    console.error('获取合并邀请统计信息失败', error)
  }
}

async function fetchInvitedUsers() {
  invitedUsers.value.loading = true
  try {
    const response = await getInvitedUsers({
      page: invitedUsers.value.page,
      page_size: invitedUsers.value.pageSize
    })
    
      invitedUsers.value.list = response.items
      invitedUsers.value.total = response.total
      invitedUsers.value.totalReward = 0
      invitedUsers.value.totalPages = response.page
  } catch (error) {
    console.error('获取邀请用户列表失败', error)
    MessagePlugin.error('获取邀请用户列表失败')
  } finally {
    invitedUsers.value.loading = false
  }
}

async function prevPage() {
  if (invitedUsers.value.page > 1) {
    invitedUsers.value.page--
    await fetchInvitedUsers()
  }
}

async function nextPage() {
  if (invitedUsers.value.page < invitedUsers.value.totalPages) {
    invitedUsers.value.page++
    await fetchInvitedUsers()
  }
}

// Computed properties
const invitedUsersTotalPages = computed(() => {
  return Math.ceil(invitedUsers.value.total / invitedUsers.value.pageSize)
})

// Initialize data
onMounted(async () => {
  // 从auth store获取用户信息
  if (authStore.user) {
    userProfile.value.username = authStore.user.username
    userProfile.value.email = authStore.user.email
    userProfile.value.createdAt = new Date(authStore.user.createdAt)
  }
  
  // 获取合并邀请统计信息和用户列表
  await Promise.all([
    fetchCombinedInvitationStats(),
    fetchInvitedUsers()
  ])
  
  // 设置总页数
  invitedUsers.value.totalPages = invitedUsersTotalPages.value
})

// 监听页码变化
watch(() => invitedUsers.value.page, () => {
  fetchInvitedUsers()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #2563eb, #1e40af);
  transform: translateY(-1px);
}
</style>