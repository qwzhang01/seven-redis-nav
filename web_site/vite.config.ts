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
          if (id.includes('node_modules')) {
            // 从路径中提取包名，精确匹配避免循环依赖
            const getPackageName = (id: string) => {
              const parts = id.split('node_modules/');
              const name = parts[parts.length - 1];
              // 处理 @scope/package 格式
              if (name.startsWith('@')) {
                return name.split('/').slice(0, 2).join('/');
              }
              return name.split('/')[0];
            };

            const pkg = getPackageName(id);

            // Vue 核心 - 精确匹配包名
            if (['vue', '@vue', 'vue-router', 'pinia', '@vuepic'].some(
              name => pkg === name || pkg.startsWith(name + '/')
            )) {
              return 'vue-vendor';
            }
            // UI 组件库
            if (pkg.startsWith('tdesign')) {
              return 'ui-vendor';
            }
            // 其他第三方库不再统一打包到一个大 chunk，
            // 让 Rollup 自动分割，避免生成过大的 chunk 导致内存不足
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
        target: 'http://localhost:8000',
        // target: 'http://34.96.254.48:80',
        changeOrigin: true,
        secure: false,
        ws: true, // 同时代理 WebSocket 请求
      },
    },
  },
})
