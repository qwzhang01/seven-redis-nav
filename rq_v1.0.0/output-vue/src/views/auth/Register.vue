<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">
        <h1>
          <t-icon name="chart-bubble" size="32px" />
          CryptoQuant
        </h1>
        <p>开启您的量化交易之旅</p>
      </div>
      
      <!-- 注册方式切换 -->
      <t-tabs v-model="registerType" class="auth-tabs">
        <t-tab-panel value="email" label="邮箱注册" />
        <t-tab-panel value="phone" label="手机号注册" />
      </t-tabs>
      
      <t-form
        ref="formRef"
        :data="formData"
        :rules="rules"
        label-width="0"
        @submit="handleSubmit"
      >
        <!-- 邮箱 -->
        <t-form-item v-if="registerType === 'email'" name="email">
          <t-input
            v-model="formData.email"
            placeholder="请输入邮箱"
            size="large"
            clearable
          >
            <template #prefix-icon>
              <t-icon name="mail" />
            </template>
          </t-input>
        </t-form-item>
        
        <!-- 手机号 -->
        <t-form-item v-else name="phone">
          <t-input
            v-model="formData.phone"
            placeholder="请输入手机号"
            size="large"
            clearable
          >
            <template #prefix-icon>
              <t-icon name="mobile" />
            </template>
          </t-input>
        </t-form-item>
        
        <!-- 验证码 -->
        <t-form-item name="code">
          <div class="code-row">
            <t-input
              v-model="formData.code"
              placeholder="6位验证码"
              size="large"
              maxlength="6"
            />
            <t-button
              variant="outline"
              size="large"
              :disabled="countdown > 0"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </t-button>
          </div>
        </t-form-item>
        
        <!-- 密码 -->
        <t-form-item name="password">
          <t-input
            v-model="formData.password"
            type="password"
            placeholder="8-128位密码"
            size="large"
            @input="checkStrength"
          >
            <template #prefix-icon>
              <t-icon name="lock-on" />
            </template>
          </t-input>
          <!-- 密码强度 -->
          <div class="password-strength">
            <div class="strength-bar" :class="strengthClass" :style="{ width: strengthWidth }"></div>
          </div>
          <div class="strength-text" :class="strengthClass">{{ strengthText }}</div>
        </t-form-item>
        
        <!-- 确认密码 -->
        <t-form-item name="confirmPassword">
          <t-input
            v-model="formData.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            size="large"
          >
            <template #prefix-icon>
              <t-icon name="lock-on" />
            </template>
          </t-input>
        </t-form-item>
        
        <!-- 协议 -->
        <t-form-item name="agree">
          <t-checkbox v-model="formData.agree">
            我已阅读并同意
            <t-link theme="primary" @click.stop="showTerms">《服务条款》</t-link>
            和
            <t-link theme="primary" @click.stop="showPrivacy">《隐私政策》</t-link>
          </t-checkbox>
        </t-form-item>
        
        <t-form-item>
          <t-button
            theme="primary"
            type="submit"
            size="large"
            block
            :loading="loading"
          >
            注 册
          </t-button>
        </t-form-item>
      </t-form>
      
      <div class="auth-footer">
        已有账号？
        <t-link theme="primary" @click="$router.push('/login')">立即登录</t-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const registerType = ref('email')
const countdown = ref(0)
const passwordStrength = ref(0)

const formData = reactive({
  email: '',
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
  agree: false
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱' },
    { email: true, message: '请输入正确的邮箱格式' }
  ],
  phone: [
    { required: true, message: '请输入手机号' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
  ],
  code: [
    { required: true, message: '请输入验证码' },
    { len: 6, message: '验证码为6位' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 8, message: '密码至少8位' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码' },
    {
      validator: (val) => val === formData.password,
      message: '两次密码不一致'
    }
  ],
  agree: [
    { validator: (val) => val === true, message: '请同意服务条款' }
  ]
}

// 密码强度
const strengthClass = computed(() => {
  if (passwordStrength.value <= 1) return 'weak'
  if (passwordStrength.value <= 2) return 'medium'
  return 'strong'
})

const strengthWidth = computed(() => {
  return `${(passwordStrength.value / 4) * 100}%`
})

const strengthText = computed(() => {
  if (!formData.password) return ''
  if (passwordStrength.value <= 1) return '弱'
  if (passwordStrength.value <= 2) return '中'
  return '强'
})

const checkStrength = () => {
  const pwd = formData.password
  let strength = 0
  if (pwd.length >= 8) strength++
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++
  if (/\d/.test(pwd)) strength++
  if (/[!@#$%^&*]/.test(pwd)) strength++
  passwordStrength.value = strength
}

// 发送验证码
const sendCode = () => {
  const account = registerType.value === 'email' ? formData.email : formData.phone
  if (!account) {
    MessagePlugin.warning(`请先输入${registerType.value === 'email' ? '邮箱' : '手机号'}`)
    return
  }
  
  MessagePlugin.success('验证码已发送')
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

// 提交注册
const handleSubmit = async ({ validateResult }) => {
  if (validateResult !== true) return
  
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    MessagePlugin.success('注册成功！')
    router.push('/login')
  } finally {
    loading.value = false
  }
}

// 显示条款
const showTerms = () => {
  DialogPlugin.alert({
    header: '服务条款',
    body: '使用本平台即表示您同意遵守平台规则，包括但不限于交易规则、风险提示等...',
    confirmBtn: '我已了解'
  })
}

const showPrivacy = () => {
  DialogPlugin.alert({
    header: '隐私政策',
    body: '我们重视您的隐私，会严格保护您的个人信息安全...',
    confirmBtn: '我已了解'
  })
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
  margin-bottom: 32px;
  
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

.auth-tabs {
  margin-bottom: 24px;
}

.code-row {
  display: flex;
  gap: 12px;
  width: 100%;
  
  .t-input {
    flex: 1;
  }
}

.password-strength {
  height: 4px;
  background: #e7e7e7;
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
  
  .strength-bar {
    height: 100%;
    transition: all 0.3s;
    
    &.weak { background: var(--error); }
    &.medium { background: var(--warning); }
    &.strong { background: var(--success); }
  }
}

.strength-text {
  font-size: 12px;
  margin-top: 4px;
  text-align: right;
  
  &.weak { color: var(--error); }
  &.medium { color: var(--warning); }
  &.strong { color: var(--success); }
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--text2);
}
</style>
