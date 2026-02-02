<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">
        <h1>
          <t-icon name="chart-bubble" size="32px" />
          CryptoQuant
        </h1>
        <p>专业的加密货币量化交易平台</p>
      </div>
      
      <t-form
        ref="formRef"
        :data="formData"
        :rules="rules"
        label-width="0"
        @submit="handleSubmit"
      >
        <t-form-item name="account">
          <t-input
            v-model="formData.account"
            placeholder="请输入邮箱或手机号"
            size="large"
            clearable
          >
            <template #prefix-icon>
              <t-icon name="user" />
            </template>
          </t-input>
        </t-form-item>
        
        <t-form-item name="password">
          <t-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            clearable
          >
            <template #prefix-icon>
              <t-icon name="lock-on" />
            </template>
          </t-input>
        </t-form-item>
        
        <!-- 验证码（多次失败后显示） -->
        <t-form-item v-if="showCaptcha" name="captcha">
          <div class="captcha-row">
            <t-input
              v-model="formData.captcha"
              placeholder="请输入验证码"
              size="large"
            />
            <div class="captcha-img" @click="refreshCaptcha">{{ captchaText }}</div>
          </div>
        </t-form-item>
        
        <div class="form-options">
          <t-checkbox v-model="formData.remember">记住登录</t-checkbox>
          <t-link theme="primary" @click="$router.push('/forgot-password')">忘记密码？</t-link>
        </div>
        
        <t-form-item>
          <t-button
            theme="primary"
            type="submit"
            size="large"
            block
            :loading="loading"
          >
            登 录
          </t-button>
        </t-form-item>
      </t-form>
      
      <div class="auth-footer">
        还没有账号？
        <t-link theme="primary" @click="$router.push('/register')">立即注册</t-link>
      </div>
      
      <t-divider>其他登录方式</t-divider>
      
      <div class="social-login">
        <t-button variant="outline" shape="circle">
          <template #icon><t-icon name="logo-wechat" /></template>
        </t-button>
        <t-button variant="outline" shape="circle">
          <template #icon><t-icon name="logo-google" /></template>
        </t-button>
        <t-button variant="outline" shape="circle">
          <template #icon><t-icon name="logo-github" /></template>
        </t-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const loginAttempts = ref(0)
const showCaptcha = ref(false)
const captchaText = ref('A7X9')

const formData = reactive({
  account: '',
  password: '',
  captcha: '',
  remember: false
})

const rules = {
  account: [
    { required: true, message: '请输入邮箱或手机号' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 6, message: '密码至少6位' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

const handleSubmit = async ({ validateResult }) => {
  if (validateResult !== true) return
  
  loading.value = true
  
  try {
    // 模拟登录请求
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (formData.password === 'Password123' || formData.password.length >= 6) {
      userStore.login({
        id: 1,
        name: '张三',
        email: formData.account
      })
      MessagePlugin.success('登录成功！')
      router.push('/trading')
    } else {
      loginAttempts.value++
      if (loginAttempts.value >= 3) {
        showCaptcha.value = true
        MessagePlugin.warning('请输入验证码')
      } else {
        MessagePlugin.error('密码错误')
      }
    }
  } finally {
    loading.value = false
  }
}

const refreshCaptcha = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  captchaText.value = Array(4).fill(0).map(() => chars[Math.floor(Math.random() * chars.length)]).join('')
}
</script>

<style lang="less" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
}

.auth-container {
  width: 420px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.auth-logo {
  text-align: center;
  margin-bottom: 40px;
  
  h1 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 28px;
    color: var(--brand);
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text2);
    font-size: 14px;
  }
}

.captcha-row {
  display: flex;
  gap: 12px;
  width: 100%;
  
  .t-input {
    flex: 1;
  }
  
  .captcha-img {
    width: 100px;
    height: 40px;
    background: linear-gradient(45deg, #e0e0e0, #f5f5f5);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    letter-spacing: 3px;
    font-weight: bold;
    cursor: pointer;
    user-select: none;
    
    &:hover {
      opacity: 0.8;
    }
  }
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--text2);
}

.social-login {
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>
