<template>
  <AuthLayout title="登录您的账户" @google-click="handleGoogleLogin">
    <!-- 表单 -->
    <form @submit.prevent="handleLogin" class="space-y-4">
      <div class="auth-field">
        <input
          v-model="form.username"
          type="text"
          placeholder="用户名"
          class="auth-input"
          :class="{ 'auth-input--error': errors.username }"
          autocomplete="username"
        />
        <p v-if="errors.username" class="auth-error">{{ errors.username }}</p>
      </div>

      <div class="auth-field">
        <input
          v-model="form.password"
          :type="passwordVisible ? 'text' : 'password'"
          placeholder="密码"
          class="auth-input"
          :class="{ 'auth-input--error': errors.password }"
          autocomplete="current-password"
        />
        <button type="button" class="auth-input-icon" tabindex="-1" @click="passwordVisible = !passwordVisible">
          <component :is="passwordVisible ? Eye : EyeOff" :size="16" />
        </button>
        <p v-if="errors.password" class="auth-error">{{ errors.password }}</p>
      </div>

      <div class="flex items-center justify-between pt-1">
        <label class="auth-checkbox">
          <input type="checkbox" v-model="form.remember" />
          <span class="auth-checkbox__box">
            <Check :size="12" />
          </span>
          <span>记住我</span>
        </label>
        <a href="javascript:void(0)" class="text-sm text-primary-500 hover:text-primary-400 transition-colors">忘记密码？</a>
      </div>

      <button
        type="submit"
        class="auth-submit"
        :disabled="loading"
      >
        {{ loading ? '登录中...' : 'Continue' }}
      </button>
    </form>

    <!-- 底部 -->
    <template #footer>
      <p class="text-center text-sm text-dark-200 mt-6">
        还没有账户？
        <router-link to="/register" class="text-primary-500 hover:text-primary-400 font-medium transition-colors">
          立即注册
        </router-link>
      </p>

      <!-- API提示 -->
      <div class="mt-6 py-2.5 px-3 rounded-lg bg-white/[0.03] border border-white/[0.05]">
        <p class="text-[11px] text-dark-200 text-center leading-relaxed">
          使用后端API登录：输入注册的用户名和密码
        </p>
      </div>
    </template>
  </AuthLayout>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Eye, EyeOff, Check } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'
import AuthLayout from './components/AuthLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const passwordVisible = ref(false)

const form = reactive({
  username: '',
  password: '',
  remember: false,
})

const errors = reactive({
  username: '',
  password: '',
})

function handleGoogleLogin() {
  MessagePlugin.info('Google 登录功能即将上线')
}

function validate(): boolean {
  errors.username = ''
  errors.password = ''
  
  if (!form.username) {
    errors.username = '请输入用户名'
    return false
  }
  
  if (!form.password) {
    errors.password = '请输入密码'
    return false
  }
  
  if (form.password.length < 6) {
    errors.password = '密码至少6位'
    return false
  }
  
  return true
}

async function handleLogin() {
  if (!validate()) return
  
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    MessagePlugin.success('登录成功')
    
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (error: any) {
    console.error('登录失败:', error)
    MessagePlugin.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 登录页特有样式 —— 公共样式通过 auth-form.css 引入 */
</style>

<style>
@import '@/views/auth/styles/auth-form.css';
</style>