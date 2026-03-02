import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  base: '/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  css: {
    preprocessorOptions: {},
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // 禁用 gzip 大小报告以加速构建
    reportCompressedSize: false,
    // 提高 chunk 大小警告阈值
    chunkSizeWarningLimit: 1000,
    // 启用 CSS 代码分割
    cssCodeSplit: true,
    // 生产环境禁用 source map 以加速构建
    sourcemap: false,
    // 压缩选项
    minify: 'esbuild',
    // 目标浏览器
    target: 'es2015',
    rollupOptions: {
      output: {
        // 优化代码分割策略 - 使用函数形式更灵活
        manualChunks(id) {
          // node_modules 中的包
          if (id.includes('node_modules')) {
            // Vue 核心
            if (id.includes('vue') || id.includes('vue-router')) {
              return 'vue-vendor';
            }
            // UI 组件库
            if (id.includes('tdesign')) {
              return 'ui-vendor';
            }
            // 其他第三方库统一打包
            return 'vendor';
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        // target: 'http://localhost:8000',
        target: 'http://34.96.254.48:80',
        changeOrigin: true,
        secure: false,
        ws: true, // 同时代理 WebSocket 请求
      },
    },
  },
})
