<template>
  <div class="min-h-screen bg-dark-900 flex items-center justify-center px-4">
    <div class="text-center">
      <div class="text-8xl font-extrabold gradient-text mb-4">404</div>
      <h1 class="text-2xl font-bold text-white mb-3">页面未找到</h1>
      <p class="text-dark-100 mb-8 max-w-md mx-auto">抱歉，您访问的页面不存在或已被移除。</p>
      <div class="flex items-center justify-center gap-4">
        <router-link to="/" class="btn-primary !py-2.5 !px-6 text-sm rounded-xl">返回首页</router-link>
        <button @click="$router.back()" class="btn-outline !py-2.5 !px-6 text-sm rounded-xl">返回上页</button>
      </div>
    </div>
  </div>
</template>
