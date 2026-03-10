<template>
  <div class="auth-page">
    <!-- 关闭按钮 -->
    <router-link to="/" class="auth-close" title="返回首页">
      <X :size="20" />
    </router-link>

    <!-- 左侧视觉面板 -->
    <div class="auth-visual">
      <div class="auth-visual__bg" />
      <!-- 光束效果 -->
      <div class="light-beam">
        <div class="light-beam__ray light-beam__ray--main"></div>
        <div class="light-beam__ray light-beam__ray--secondary"></div>
        <div class="light-beam__ray light-beam__ray--tertiary"></div>
        <div class="light-beam__glow"></div>
        <div class="light-beam__particles">
          <span v-for="n in 12" :key="n" class="light-beam__particle" :style="particleStyle(n)"></span>
        </div>
      </div>

      <!-- 欢迎文字 -->
      <div class="auth-visual__welcome">
        <span class="welcome-sub">WELCOME TO</span>
        <span class="welcome-main">Quanta</span>
      </div>
    </div>

    <!-- 右侧表单面板 -->
    <div class="auth-form-panel">
      <div class="auth-form-wrapper">
        <!-- Logo -->
        <router-link to="/" class="flex items-center justify-center gap-2.5 mb-6">
          <div
              class="w-9 h-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-blue flex items-center justify-center text-dark-900 font-extrabold text-xs">QA</div>
          <span class="text-white font-bold text-xl tracking-tight">量元<span
              class="gradient-text ml-1">Quanta</span></span>
        </router-link>

        <!-- 标题 -->
        <h1 class="text-[22px] font-bold text-white text-center mb-7 leading-snug" v-html="title" />

        <!-- Google 社交登录 -->
        <button class="auth-social-btn" @click="$emit('google-click')">
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

        <!-- 表单内容插槽 -->
        <slot />

        <!-- 底部链接插槽 -->
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { X } from 'lucide-vue-next'
import logoImg from '@/assets/logo.jpeg'

defineProps<{
  title: string
}>()

defineEmits<{
  'google-click': []
}>()

// 光束粒子随机样式
function particleStyle(n: number) {
  const left = 30 + Math.sin(n * 1.3) * 25
  const delay = (n * 0.7) % 4
  const duration = 3 + (n % 3) * 1.5
  const size = 1.5 + (n % 4) * 0.8
  return {
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    width: `${size}px`,
    height: `${size}px`,
  }
}
</script>

<style scoped>
/* ====== 页面基础布局 ====== */
.auth-page {
  @apply min-h-screen flex relative;
  background-color: #0c1021;
}

/* 关闭按钮 */
.auth-close {
  @apply absolute top-5 right-5 z-30 w-9 h-9 flex items-center justify-center
         rounded-full text-dark-200 hover:text-white hover:bg-white/10 transition-all;
}

/* ====== 左侧视觉面板 ====== */
.auth-visual {
  @apply hidden lg:flex lg:w-[50%] relative items-end overflow-hidden;
  background-image: v-bind('`url(${logoImg})`');
  background-size: cover;
  background-position: center;
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

/* ====== 光束效果 ====== */
.light-beam {
  @apply absolute inset-0 overflow-hidden;
  z-index: 3;
  pointer-events: none;
}

.light-beam__ray--main {
  position: absolute;
  top: -10%;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 120%;
  background: linear-gradient(
    180deg,
    rgba(180, 220, 255, 0.55) 0%,
    rgba(100, 200, 255, 0.30) 15%,
    rgba(60, 170, 240, 0.16) 40%,
    rgba(30, 140, 220, 0.06) 70%,
    transparent 100%
  );
  clip-path: polygon(30% 0%, 70% 0%, 95% 100%, 5% 100%);
  animation: beamPulse 6s ease-in-out infinite;
}

.light-beam__ray--secondary {
  position: absolute;
  top: -5%;
  left: 42%;
  transform: translateX(-50%);
  width: 200px;
  height: 110%;
  background: linear-gradient(
    180deg,
    rgba(150, 210, 255, 0.35) 0%,
    rgba(80, 180, 240, 0.18) 20%,
    rgba(40, 150, 220, 0.08) 50%,
    transparent 100%
  );
  clip-path: polygon(25% 0%, 75% 0%, 90% 100%, 10% 100%);
  animation: beamPulse 8s ease-in-out 1s infinite;
}

.light-beam__ray--tertiary {
  position: absolute;
  top: -8%;
  left: 60%;
  transform: translateX(-50%);
  width: 180px;
  height: 105%;
  background: linear-gradient(
    180deg,
    rgba(200, 230, 255, 0.28) 0%,
    rgba(120, 200, 255, 0.14) 25%,
    rgba(60, 160, 230, 0.06) 55%,
    transparent 100%
  );
  clip-path: polygon(20% 0%, 80% 0%, 92% 100%, 8% 100%);
  animation: beamPulse 7s ease-in-out 2s infinite;
}

.light-beam__glow {
  position: absolute;
  top: -15%;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(160, 220, 255, 0.50) 0%,
    rgba(100, 190, 255, 0.25) 30%,
    rgba(60, 150, 230, 0.10) 60%,
    transparent 100%
  );
  filter: blur(35px);
  animation: glowPulse 5s ease-in-out infinite;
}

.light-beam__particles {
  @apply absolute inset-0;
}

.light-beam__particle {
  position: absolute;
  top: -5%;
  border-radius: 50%;
  background: rgba(180, 225, 255, 0.7);
  box-shadow: 0 0 6px 2px rgba(140, 210, 255, 0.4);
  animation: particleFall linear infinite;
  opacity: 0;
}

@keyframes beamPulse {
  0%, 100% {
    opacity: 0.85;
    transform: translateX(-50%) scaleX(1);
  }
  50% {
    opacity: 1;
    transform: translateX(-50%) scaleX(1.2);
  }
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0.75;
    transform: translateX(-50%) scale(1);
  }
  50% {
    opacity: 1;
    transform: translateX(-50%) scale(1.15);
  }
}

@keyframes particleFall {
  0% {
    opacity: 0;
    transform: translateY(0) scale(0.5);
  }
  10% {
    opacity: 0.8;
  }
  80% {
    opacity: 0.3;
  }
  100% {
    opacity: 0;
    transform: translateY(calc(100vh + 20px)) scale(0.2);
  }
}



/* ====== 欢迎文字 ====== */
.auth-visual__welcome {
  @apply absolute w-full flex flex-col items-center z-10;
  bottom: 12%;
  pointer-events: none;
}

.welcome-sub {
  @apply text-sm font-medium tracking-[0.35em] uppercase;
  color: rgba(160, 215, 255, 0.6);
  text-shadow: 0 0 20px rgba(100, 200, 255, 0.3);
  letter-spacing: 0.35em;
  margin-bottom: 8px;
}

.welcome-main {
  @apply text-4xl font-bold tracking-wide;
  background: linear-gradient(
    135deg,
    rgba(220, 240, 255, 1) 0%,
    rgba(140, 210, 255, 1) 40%,
    rgba(80, 180, 255, 0.9) 70%,
    rgba(60, 160, 240, 0.8) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
  filter: drop-shadow(0 0 20px rgba(100, 200, 255, 0.3));
}

/* ====== 右侧表单面板 ====== */
.auth-form-panel {
  @apply flex-1 flex items-center justify-center px-6 py-10 relative;
  background-color: #0c1021;
}

.auth-form-wrapper {
  @apply w-full max-w-[380px];
}

/* 社交按钮 */
.auth-social-btn {
  @apply w-full flex items-center justify-center gap-2.5 h-11 rounded-lg
         border border-white/[0.12] bg-white/[0.04] text-sm text-white/90
         hover:bg-white/[0.08] hover:border-white/[0.2] transition-all;
}

/* 分割线 */
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

/* 移动端适配 */
@media (max-width: 1023px) {
  .auth-form-panel {
    background:
      radial-gradient(ellipse at 30% 20%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
      #0c1021;
  }
}
</style>
