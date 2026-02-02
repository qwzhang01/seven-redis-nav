<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">
        <h1>
          <t-icon name="lock-on" size="32px" />
          找回密码
        </h1>
        <p>请输入您的注册邮箱/手机号</p>
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
            placeholder="请输入注册时使用的邮箱或手机号"
            size="large"
            clearable
          >
            <template #prefix-icon>
              <t-icon name="user" />
            </template>
          </t-input>
        </t-form-item>
        
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
        
        <!-- 第二步：设置新密码 -->
        <template v-if="step === 2">
          <t-form-item name="newPassword">
            <t-input
              v-model="formData.newPassword"
              type="password"
              placeholder="8-128位，含大小写和数字"
              size="large"
            >
              <template #prefix-icon>
                <t-icon name="lock-on" />
              </template>
            </t-input>
          </t-form-item>
          
          <t-form-item name="confirmPassword">
            <t-input
              v-model="formData.confirmPassword"
              type="password"
              placeholder="再次输入新密码"
              size="large"
            >
              <template #prefix-icon>
                <t-icon name="lock-on" />
              </template>
            </t-input>
          </t-form-item>
        </template>
        
        <t-form-item>
          <t-button
            theme="primary"
            type="submit"
            size="large"
            block
            :loading="loading"
          >
            {{ step === 1 ? '下一步' : '重置密码' }}
          </t-button>
        </t-form-item>
      </t-form>
      
      <div class="auth-footer">
        <t-link theme="primary" @click="$router.push('/login')">
          <t-icon name="chevron-left" /> 返回登录
        </t-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const step = ref(1)
const countdown = ref(0)

const formData = reactive({
  account: '',
  code: '',
  newPassword: '',
  confirmPassword: ''
})

const rules = {
  account: [{ required: true, message: '请输入邮箱或手机号' }],
  code: [
    { required: true, message: '请输入验证码' },
    { len: 6, message: '验证码为6位' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码' },
    { min: 8, message: '密码至少8位' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码' },
    {
      validator: (val) => val === formData.newPassword,
      message: '两次密码不一致'
    }
  ]
}

const sendCode = () => {
  if (!formData.account) {
    MessagePlugin.warning('请先输入邮箱或手机号')
    return
  }
  
  MessagePlugin.success('验证码已发送')
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

const handleSubmit = async ({ validateResult }) => {
  if (validateResult !== true) return
  
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (step.value === 1) {
      step.value = 2
      MessagePlugin.success('验证成功，请设置新密码')
    } else {
      MessagePlugin.success('密码重置成功！')
      router.push('/login')
    }
  } finally {
    loading.value = false
  }
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

.code-row {
  display: flex;
  gap: 12px;
  width: 100%;
  
  .t-input {
    flex: 1;
  }
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
}
</style>
