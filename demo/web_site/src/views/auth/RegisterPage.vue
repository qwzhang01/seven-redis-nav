<template>
  <AuthLayout title="创建您的 量元 Quanta<br/>账户"
              @google-click="handleGoogleRegister">
    <!-- 表单 -->
    <form @submit.prevent="handleRegister" class="space-y-3.5">
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
            v-model="form.email"
            type="email"
            placeholder="邮箱地址"
            class="auth-input"
            :class="{ 'auth-input--error': errors.email }"
            autocomplete="email"
        />
        <button type="button" class="auth-input-icon" tabindex="-1">
          <Mail :size="16"/>
        </button>
        <p v-if="errors.email" class="auth-error">{{ errors.email }}</p>
      </div>

      <div class="auth-field">
        <input
            v-model="form.phone"
            type="tel"
            placeholder="手机号（可选）"
            class="auth-input"
            :class="{ 'auth-input--error': errors.phone }"
        />
        <p v-if="errors.phone" class="auth-error">{{ errors.phone }}</p>
      </div>

      <div class="auth-field">
        <input
            v-model="form.password"
            :type="passwordVisible ? 'text' : 'password'"
            placeholder="密码"
            class="auth-input"
            :class="{ 'auth-input--error': errors.password }"
            autocomplete="new-password"
        />
        <button type="button" class="auth-input-icon" tabindex="-1"
                @click="passwordVisible = !passwordVisible">
          <component :is="passwordVisible ? Eye : EyeOff" :size="16"/>
        </button>
        <p v-if="errors.password" class="auth-error">{{ errors.password }}</p>
      </div>

      <div class="auth-field">
        <input
            v-model="form.invitation_code"
            type="text"
            placeholder="请联系QQ00000000获取邀请码"
            class="auth-input"
            :class="{ 'auth-input--error': errors.invitation_code }"
        />
        <p v-if="errors.invitation_code" class="auth-error">
          {{ errors.invitation_code }}</p>
      </div>

      <!-- 服务条款 -->
      <label class="auth-checkbox pt-1">
        <input type="checkbox" v-model="form.agree"/>
        <span class="auth-checkbox__box">
          <Check :size="12"/>
        </span>
        <span class="leading-snug">
          我已阅读并同意
          <a href="javascript:void(0)"
             class="text-primary-500 hover:text-primary-400">服务条款</a>
          和
          <a href="javascript:void(0)"
             class="text-primary-500 hover:text-primary-400">隐私政策</a>
        </span>
      </label>
      <p v-if="errors.agree" class="auth-error !mt-0.5">{{ errors.agree }}</p>

      <button
          type="submit"
          class="auth-submit"
          :disabled="loading"
      >
        {{ loading ? '注册中...' : 'Continue' }}
      </button>
    </form>

    <!-- 底部 -->
    <template #footer>
      <p class="text-center text-sm text-dark-200 mt-6">
        已有账户？
        <router-link to="/login"
                     class="text-primary-500 hover:text-primary-400 font-medium transition-colors">
          立即登录
        </router-link>
      </p>
    </template>
  </AuthLayout>
</template>

<script setup lang="ts">
import {ref, reactive} from 'vue'
import {useRouter} from 'vue-router'
import {Mail, Eye, EyeOff, Check} from 'lucide-vue-next'
import {MessagePlugin} from 'tdesign-vue-next'
import {useAuthStore} from '@/stores/auth'
import type {RegisterRequest} from '@/utils/userApi'
import AuthLayout from './components/AuthLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const passwordVisible = ref(false)

const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  invitation_code: '',
  agree: true,
})

const errors = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  invitation_code: '',
  agree: '',
})

function handleGoogleRegister() {
  MessagePlugin.info('Google 注册功能即将上线')
}

function validate(): boolean {
  errors.username = ''
  errors.email = ''
  errors.phone = ''
  errors.password = ''
  errors.invitation_code = ''
  errors.agree = ''

  let valid = true

  if (!form.username) {
    errors.username = '请输入用户名'
    valid = false
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
    valid = false
  }

  if (!form.email || !/\S+@\S+\.\S+/.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    valid = false
  }

  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    errors.phone = '请输入有效的手机号'
    valid = false
  }

  if (!form.password || form.password.length < 6) {
    errors.password = '密码至少6位'
    valid = false
  }

  if (!form.invitation_code) {
    errors.invitation_code = '请联系QQ00000000获取邀请码'
    valid = false
  }

  if (!form.agree) {
    errors.agree = '请同意服务条款和隐私政策'
    valid = false
  }

  return valid
}

async function handleRegister() {
  if (!validate()) return

  loading.value = true
  try {
    const registerData: RegisterRequest = {
      username: form.username,
      email: form.email,
      password: form.password,
      invitation_code: form.invitation_code,
    }

    if (form.phone) {
      registerData.phone = form.phone
    }

    const user = await authStore.register(registerData)
    if (user.id) {
      router.push('/')
    }
  } catch (error: any) {
    MessagePlugin.error(error.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 注册页特有样式 */
.auth-checkbox {
  @apply flex items-start gap-2 cursor-pointer text-sm text-dark-200;
}

.auth-checkbox__box {
  @apply mt-0.5;
}
</style>

<style>
@import '@/views/auth/styles/auth-form.css';
</style>