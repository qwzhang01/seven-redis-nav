<template>
  <div class="auth-page">
    <!-- Close button -->
    <router-link to="/" class="auth-close" title="返回首页">
      <X :size="20" />
    </router-link>

    <!-- Left visual panel -->
    <div class="auth-visual">
      <div class="auth-visual__bg" />
      <div class="auth-visual__content">
        <h2 class="auth-visual__title">
          Quantify,
          <em>Amplified</em>
        </h2>
      </div>
    </div>

    <!-- Right form panel -->
    <div class="auth-form-panel">
      <div class="auth-form-wrapper">
        <!-- Logo -->
        <router-link to="/" class="flex items-center justify-center gap-2.5 mb-6">
          <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-xs">QM</div>
          <span class="text-white font-bold text-xl tracking-tight">Quant<span class="gradient-text ml-1">Meta</span></span>
        </router-link>

        <h1 class="text-[22px] font-bold text-white text-center mb-7 leading-snug">
          创建您的 Quant Meta<br/>账户
        </h1>

        <!-- Google login button -->
        <button class="auth-social-btn" @click="handleGoogleRegister">
          <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span>Google</span>
        </button>

        <div class="auth-divider">
          <span>or</span>
        </div>

        <!-- Form -->
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
              v-model="form.nickname"
              type="text"
              placeholder="昵称"
              class="auth-input"
              :class="{ 'auth-input--error': errors.nickname }"
            />
            <p v-if="errors.nickname" class="auth-error">{{ errors.nickname }}</p>
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
              <Mail :size="16" />
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
              placeholder="Password"
              class="auth-input"
              :class="{ 'auth-input--error': errors.password }"
              autocomplete="new-password"
            />
            <button type="button" class="auth-input-icon" tabindex="-1" @click="togglePasswordVisibility">
              <component :is="passwordVisible ? Eye : EyeOff" :size="16" />
            </button>
            <p v-if="errors.password" class="auth-error">{{ errors.password }}</p>
          </div>

          <!-- Terms checkbox -->
          <label class="auth-checkbox pt-1">
            <input type="checkbox" v-model="form.agree" />
            <span class="auth-checkbox__box">
              <Check :size="12" />
            </span>
            <span class="leading-snug">
              我已阅读并同意
              <a href="javascript:void(0)" class="text-primary-500 hover:text-primary-400">服务条款</a>
              和
              <a href="javascript:void(0)" class="text-primary-500 hover:text-primary-400">隐私政策</a>
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

        <p class="text-center text-sm text-dark-200 mt-6">
          已有账户？
          <router-link to="/login" class="text-primary-500 hover:text-primary-400 font-medium transition-colors">
            立即登录
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { X, Mail, Eye, EyeOff, Check } from 'lucide-vue-next'
import { MessagePlugin } from 'tdesign-vue-next'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/utils/userApi'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const passwordVisible = ref(false)

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  password: '',
  agree: true,
})

const errors = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  password: '',
  agree: '',
})

function togglePasswordVisibility() {
  passwordVisible.value = !passwordVisible.value
}

function handleGoogleRegister() {
  MessagePlugin.info('Google 注册功能即将上线')
}

function validate(): boolean {
  errors.username = ''
  errors.nickname = ''
  errors.email = ''
  errors.phone = ''
  errors.password = ''
  errors.agree = ''
  
  let valid = true
  
  if (!form.username) {
    errors.username = '请输入用户名'
    valid = false
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
    valid = false
  }
  
  if (!form.nickname) {
    errors.nickname = '请输入昵称'
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
    // 构建注册数据
    const registerData: RegisterRequest = {
      username: form.username,
      nickname: form.nickname,
      email: form.email,
      password: form.password,
    }
    
    // 添加可选字段
    if (form.phone) {
      registerData.phone = form.phone
    }
    
    // 调用真实API注册
    await authStore.register(registerData)
    MessagePlugin.success('注册成功，正在跳转...')
    
    // 跳转到首页
    setTimeout(() => {
      router.push('/')
    }, 500)
  } catch (error: any) {
    console.error('注册失败:', error)
    MessagePlugin.error(error.message || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Auth page base */
.auth-page {
  @apply min-h-screen flex relative;
  background-color: #0c1021;
}

/* Close button */
.auth-close {
  @apply absolute top-5 right-5 z-30 w-9 h-9 flex items-center justify-center
         rounded-full text-dark-200 hover:text-white hover:bg-white/10 transition-all;
}

/* Left visual panel */
.auth-visual {
  @apply hidden lg:flex lg:w-[50%] relative items-end overflow-hidden;
}

.auth-visual__bg {
  @apply absolute inset-0;
  background: 
    radial-gradient(ellipse at 30% 50%, rgba(0, 212, 255, 0.35) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 30%, rgba(59, 130, 246, 0.25) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(0, 180, 220, 0.2) 0%, transparent 50%),
    linear-gradient(160deg, #0a1628 0%, #0d1a30 30%, #0e2040 60%, #0a1628 100%);
}

.auth-visual__bg::after {
  content: '';
  @apply absolute inset-0;
  background: 
    radial-gradient(ellipse at 40% 60%, rgba(0, 212, 255, 0.15) 0%, transparent 70%),
    radial-gradient(ellipse at 60% 40%, rgba(100, 180, 255, 0.1) 0%, transparent 60%);
  filter: blur(40px);
}

.auth-visual__content {
  @apply relative z-10 p-12 pb-20;
}

.auth-visual__title {
  @apply text-[44px] leading-[1.15] font-semibold tracking-tight;
  color: #e0f0ff;
}

.auth-visual__title em {
  @apply not-italic;
  background: linear-gradient(135deg, #00d4ff 0%, #3b82f6 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Right form panel */
.auth-form-panel {
  @apply flex-1 flex items-center justify-center px-6 py-10 relative;
  background-color: #0c1021;
}

.auth-form-wrapper {
  @apply w-full max-w-[380px];
}

/* Social button */
.auth-social-btn {
  @apply w-full flex items-center justify-center gap-2.5 h-11 rounded-lg
         border border-white/[0.12] bg-white/[0.04] text-sm text-white/90
         hover:bg-white/[0.08] hover:border-white/[0.2] transition-all;
}

/* Divider */
.auth-divider {
  @apply flex items-center gap-3 my-5;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  @apply flex-1 h-px bg-white/[0.08];
}

.auth-divider span {
  @apply text-xs text-dark-200;
}

/* Input */
.auth-field {
  @apply relative;
}

.auth-input {
  @apply w-full h-11 px-4 pr-10 rounded-lg text-sm text-white placeholder-dark-200
         bg-white/[0.04] border border-white/[0.12] outline-none
         transition-all duration-200;
}

.auth-input:focus {
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.08);
  background: rgba(255, 255, 255, 0.06);
}

.auth-input--error {
  border-color: rgba(239, 68, 68, 0.6) !important;
}

.auth-input-icon {
  @apply absolute right-3 top-1/2 -translate-y-1/2 text-dark-200 hover:text-white/70 transition-colors p-0.5;
}

.auth-field .auth-input-icon {
  top: 22px;
}

.auth-error {
  @apply text-xs text-red-400 mt-1.5 pl-1;
}

/* Checkbox */
.auth-checkbox {
  @apply flex items-start gap-2 cursor-pointer text-sm text-dark-200;
}

.auth-checkbox input {
  @apply hidden;
}

.auth-checkbox__box {
  @apply w-4 h-4 rounded flex items-center justify-center shrink-0 mt-0.5
         border border-white/[0.15] bg-white/[0.04] transition-all text-transparent;
}

.auth-checkbox input:checked ~ .auth-checkbox__box {
  @apply bg-primary-500 border-primary-500 text-white;
}

/* Submit */
.auth-submit {
  @apply w-full h-11 rounded-lg text-sm font-semibold text-white
         transition-all duration-300;
  background: linear-gradient(135deg, #1a9dd6 0%, #2a7de1 50%, #3b82f6 100%);
}

.auth-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #17a3e0 0%, #2680eb 50%, #4b8ff7 100%);
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.25);
}

.auth-submit:disabled {
  @apply opacity-60 cursor-not-allowed;
}

/* Mobile responsive */
@media (max-width: 1023px) {
  .auth-form-panel {
    background:
      radial-gradient(ellipse at 30% 20%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
      #0c1021;
  }
}
</style>
