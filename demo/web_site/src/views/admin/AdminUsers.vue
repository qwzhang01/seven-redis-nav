<template>
  <div class="pt-8 pb-16">
    <div class="page-container">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-extrabold text-white mb-2">用户管理</h1>
        <p class="text-dark-100">管理系统用户信息和状态</p>
      </div>

      <!-- Search and Filter -->
      <div class="glass-card p-6 mb-6">
        <div class="flex flex-col md:flex-row gap-4">
          <!-- Search Input -->
          <div class="flex-1">
            <div class="relative">
              <Search :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-dark-300" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="搜索用户名、邮箱或昵称..."
                class="w-full bg-dark-600 border border-dark-500 rounded-lg pl-10 pr-4 py-2.5 text-white text-sm placeholder-dark-300 focus:border-primary-500 focus:outline-none"
              />
            </div>
          </div>
          
          <!-- Status Filter -->
          <div class="flex gap-2">
            <select
              v-model="statusFilter"
              class="bg-dark-600 border border-dark-500 rounded-lg px-4 py-2.5 text-white text-sm focus:border-primary-500 focus:outline-none"
            >
              <option value="">全部状态</option>
              <option value="active">活跃</option>
              <option value="inactive">未激活</option>
              <option value="locked">已锁定</option>
            </select>

            <select
              v-model="userTypeFilter"
              class="bg-dark-600 border border-dark-500 rounded-lg px-4 py-2.5 text-white text-sm focus:border-primary-500 focus:outline-none"
            >
              <option value="">全部类型</option>
              <option value="customer">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-dark-100 text-sm">总用户数</span>
            <Users :size="18" class="text-primary-400" />
          </div>
          <div class="text-2xl font-bold text-white">{{ statistics.total }}</div>
        </div>
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-dark-100 text-sm">活跃用户</span>
            <UserCheck :size="18" class="text-emerald-400" />
          </div>
          <div class="text-2xl font-bold text-white">{{ statistics.active }}</div>
        </div>
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-dark-100 text-sm">今日新增</span>
            <UserPlus :size="18" class="text-accent-blue" />
          </div>
          <div class="text-2xl font-bold text-white">{{ statistics.newToday }}</div>
        </div>
        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-dark-100 text-sm">已锁定</span>
            <UserX :size="18" class="text-red-400" />
          </div>
          <div class="text-2xl font-bold text-white">{{ statistics.locked }}</div>
        </div>
      </div>

      <!-- Users Table -->
      <div class="glass-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-white/[0.06]">
                <th class="text-left px-6 py-4 text-sm font-semibold text-dark-100">用户信息</th>
                <th class="text-left px-6 py-4 text-sm font-semibold text-dark-100">用户类型</th>
                <th class="text-left px-6 py-4 text-sm font-semibold text-dark-100">状态</th>
                <th class="text-left px-6 py-4 text-sm font-semibold text-dark-100">注册时间</th>
                <th class="text-left px-6 py-4 text-sm font-semibold text-dark-100">最后登录</th>
                <th class="text-right px-6 py-4 text-sm font-semibold text-dark-100">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                class="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
              >
                <!-- User Info -->
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-blue/20 flex items-center justify-center shrink-0">
                      <User :size="18" class="text-primary-400" />
                    </div>
                    <div>
                      <div class="text-white font-medium">{{ user.nickname || user.username }}</div>
                      <div class="text-sm text-dark-100">{{ user.email }}</div>
                      <div class="text-xs text-dark-200 mt-0.5">ID: {{ user.id.substring(0, 8) }}...</div>
                    </div>
                  </div>
                </td>

                <!-- User Type -->
                <td class="px-6 py-4">
                  <span
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                    :class="user.user_type === 'admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'"
                  >
                    <Shield v-if="user.user_type === 'admin'" :size="12" />
                    <User v-else :size="12" />
                    {{ user.user_type === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>

                <!-- Status -->
                <td class="px-6 py-4">
                  <span
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                    :class="getStatusClass(user.status)"
                  >
                    <div class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(user.status)"></div>
                    {{ getStatusText(user.status) }}
                  </span>
                </td>

                <!-- Registration Time -->
                <td class="px-6 py-4">
                  <div class="text-sm text-white">{{ formatDate(user.registration_time) }}</div>
                </td>

                <!-- Last Login -->
                <td class="px-6 py-4">
                  <div class="text-sm text-dark-100">{{ formatDate(user.last_login_time) || '从未登录' }}</div>
                </td>

                <!-- Actions -->
                <td class="px-6 py-4">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      @click="showUserDetail(user)"
                      class="p-2 rounded-lg text-dark-100 hover:text-white hover:bg-white/[0.06] transition-colors"
                      title="查看详情"
                    >
                      <Eye :size="16" />
                    </button>
                    <button
                      @click="editUser(user)"
                      class="p-2 rounded-lg text-dark-100 hover:text-white hover:bg-white/[0.06] transition-colors"
                      title="编辑"
                    >
                      <Edit :size="16" />
                    </button>
                    <button
                      v-if="user.status === 'active'"
                      @click="toggleUserStatus(user, 'locked')"
                      class="p-2 rounded-lg text-dark-100 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      title="锁定用户"
                    >
                      <Lock :size="16" />
                    </button>
                    <button
                      v-else-if="user.status === 'locked'"
                      @click="toggleUserStatus(user, 'active')"
                      class="p-2 rounded-lg text-dark-100 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                      title="解锁用户"
                    >
                      <Unlock :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty State -->
        <div v-if="filteredUsers.length === 0" class="text-center py-12 text-dark-100">
          <Users :size="48" class="mx-auto mb-4 text-dark-300" />
          <p>暂无用户数据</p>
        </div>
      </div>
    </div>

    <!-- User Detail Modal -->
    <div v-if="detailModal.show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-dark-800/95 backdrop-blur-xl border-b border-white/[0.06] px-6 py-4 flex items-center justify-between">
          <h3 class="text-white font-bold text-lg">用户详情</h3>
          <button @click="closeDetailModal" class="text-dark-100 hover:text-white transition-colors">
            <X :size="20" />
          </button>
        </div>
        
        <div v-if="detailModal.user" class="p-6 space-y-6">
          <!-- Basic Info -->
          <div>
            <h4 class="text-white font-semibold mb-4 flex items-center gap-2">
              <User :size="18" />
              基本信息
            </h4>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-dark-100">用户ID:</span>
                <div class="text-white mt-1 font-mono">{{ detailModal.user.id }}</div>
              </div>
              <div>
                <span class="text-dark-100">用户名:</span>
                <div class="text-white mt-1">{{ detailModal.user.username }}</div>
              </div>
              <div>
                <span class="text-dark-100">昵称:</span>
                <div class="text-white mt-1">{{ detailModal.user.nickname || '-' }}</div>
              </div>
              <div>
                <span class="text-dark-100">邮箱:</span>
                <div class="text-white mt-1">{{ detailModal.user.email }}</div>
              </div>
              <div>
                <span class="text-dark-100">手机号:</span>
                <div class="text-white mt-1">{{ detailModal.user.phone || '-' }}</div>
              </div>
              <div>
                <span class="text-dark-100">用户类型:</span>
                <div class="text-white mt-1">{{ detailModal.user.user_type === 'admin' ? '管理员' : '普通用户' }}</div>
              </div>
            </div>
          </div>

          <!-- Status Info -->
          <div>
            <h4 class="text-white font-semibold mb-4 flex items-center gap-2">
              <Activity :size="18" />
              状态信息
            </h4>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-dark-100">账户状态:</span>
                <div class="mt-1">
                  <span
                    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                    :class="getStatusClass(detailModal.user.status)"
                  >
                    <div class="w-1.5 h-1.5 rounded-full" :class="getStatusDotClass(detailModal.user.status)"></div>
                    {{ getStatusText(detailModal.user.status) }}
                  </span>
                </div>
              </div>
              <div>
                <span class="text-dark-100">邮箱验证:</span>
                <div class="text-white mt-1">{{ detailModal.user.email_verified ? '已验证' : '未验证' }}</div>
              </div>
              <div>
                <span class="text-dark-100">手机验证:</span>
                <div class="text-white mt-1">{{ detailModal.user.phone_verified ? '已验证' : '未验证' }}</div>
              </div>
              <div>
                <span class="text-dark-100">注册时间:</span>
                <div class="text-white mt-1">{{ formatDate(detailModal.user.registration_time) }}</div>
              </div>
              <div>
                <span class="text-dark-100">最后登录:</span>
                <div class="text-white mt-1">{{ formatDate(detailModal.user.last_login_time) || '从未登录' }}</div>
              </div>
              <div>
                <span class="text-dark-100">创建时间:</span>
                <div class="text-white mt-1">{{ formatDate(detailModal.user.create_time) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Users, User, UserCheck, UserPlus, UserX, Search, Eye, Edit, 
  Lock, Unlock, Shield, X, Activity 
} from 'lucide-vue-next'
import type { UserProfile } from '@/utils/userApi'

const searchQuery = ref('')
const statusFilter = ref('')
const userTypeFilter = ref('')

const detailModal = ref({
  show: false,
  user: null as UserProfile | null,
})

// Mock data - 实际应该从API获取
const users = ref<UserProfile[]>([
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    username: 'zhangsan',
    nickname: '张三',
    email: 'zhangsan@example.com',
    email_verified: true,
    phone: '13800138000',
    phone_verified: true,
    avatar_url: '',
    user_type: 'customer',
    registration_time: '2025-01-15T10:30:00Z',
    last_login_time: '2025-02-20T15:20:00Z',
    status: 'active',
    create_time: '2025-01-15T10:30:00Z',
    update_time: '2025-02-20T15:20:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    username: 'lisi',
    nickname: '李四',
    email: 'lisi@example.com',
    email_verified: true,
    phone: '13900139000',
    phone_verified: false,
    avatar_url: '',
    user_type: 'admin',
    registration_time: '2025-01-10T09:00:00Z',
    last_login_time: '2025-02-21T08:30:00Z',
    status: 'active',
    create_time: '2025-01-10T09:00:00Z',
    update_time: '2025-02-21T08:30:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440003',
    username: 'wangwu',
    nickname: '王五',
    email: 'wangwu@example.com',
    email_verified: false,
    phone: '',
    phone_verified: false,
    avatar_url: '',
    user_type: 'customer',
    registration_time: '2025-02-01T14:20:00Z',
    last_login_time: '2025-02-10T11:15:00Z',
    status: 'inactive',
    create_time: '2025-02-01T14:20:00Z',
    update_time: '2025-02-10T11:15:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440004',
    username: 'zhaoliu',
    nickname: '赵六',
    email: 'zhaoliu@example.com',
    email_verified: true,
    phone: '13700137000',
    phone_verified: true,
    avatar_url: '',
    user_type: 'customer',
    registration_time: '2025-02-18T16:45:00Z',
    last_login_time: '2025-02-19T10:00:00Z',
    status: 'locked',
    create_time: '2025-02-18T16:45:00Z',
    update_time: '2025-02-19T10:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440005',
    username: 'sunqi',
    nickname: '孙七',
    email: 'sunqi@example.com',
    email_verified: true,
    phone: '13600136000',
    phone_verified: true,
    avatar_url: '',
    user_type: 'customer',
    registration_time: '2025-02-21T09:30:00Z',
    status: 'active',
    create_time: '2025-02-21T09:30:00Z',
  },
])

// Statistics
const statistics = computed(() => {
  const total = users.value.length
  const active = users.value.filter(u => u.status === 'active').length
  const locked = users.value.filter(u => u.status === 'locked').length
  
  // Calculate new users today
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const newToday = users.value.filter(u => {
    const regDate = new Date(u.registration_time)
    regDate.setHours(0, 0, 0, 0)
    return regDate.getTime() === today.getTime()
  }).length

  return { total, active, locked, newToday }
})

// Filtered users
const filteredUsers = computed(() => {
  return users.value.filter(user => {
    // Search filter
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      const matchesSearch = 
        user.username.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query) ||
        (user.nickname && user.nickname.toLowerCase().includes(query))
      if (!matchesSearch) return false
    }

    // Status filter
    if (statusFilter.value && user.status !== statusFilter.value) {
      return false
    }

    // User type filter
    if (userTypeFilter.value && user.user_type !== userTypeFilter.value) {
      return false
    }

    return true
  })
})

const getStatusClass = (status: string) => {
  switch (status) {
    case 'active': return 'bg-emerald-500/20 text-emerald-400'
    case 'inactive': return 'bg-amber-500/20 text-amber-400'
    case 'locked': return 'bg-red-500/20 text-red-400'
    default: return 'bg-dark-600 text-dark-100'
  }
}

const getStatusDotClass = (status: string) => {
  switch (status) {
    case 'active': return 'bg-emerald-400'
    case 'inactive': return 'bg-amber-400'
    case 'locked': return 'bg-red-400'
    default: return 'bg-dark-300'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'inactive': return '未激活'
    case 'locked': return '已锁定'
    default: return status
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const showUserDetail = (user: UserProfile) => {
  detailModal.value = {
    show: true,
    user,
  }
}

const closeDetailModal = () => {
  detailModal.value.show = false
}

const editUser = (user: UserProfile) => {
  // TODO: 实现编辑用户功能
  console.log('编辑用户:', user)
}

const toggleUserStatus = (user: UserProfile, newStatus: 'active' | 'locked') => {
  // TODO: 调用API更新用户状态
  const index = users.value.findIndex(u => u.id === user.id)
  if (index !== -1) {
    users.value[index].status = newStatus
  }
  console.log('切换用户状态:', user.username, newStatus)
}
</script>
