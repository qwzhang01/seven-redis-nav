import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    // 测试环境
    environment: 'jsdom',
    globals: true,

    // 测试文件匹配
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['**/node_modules/**', '**/dist/**', 'src-tauri/**'],

    // 测试覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'coverage/**',
        'dist/**',
        '**/[.]**',
        'packages/*/test?(s)/**',
        '**/*.d.ts',
        '**/virtual:*',
        '**/__x00__*',
        '**/\u0000*',
        '**/*.+(cjs|config.*|mjs)',
        '**/main.*',
        'src-tauri/**'
      ],
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        }
      }
    },

    // 别名配置
    alias: {
      '@': '/src'
    },

    // 设置
    setupFiles: ['./src/test/setup.ts'],

    // 超时设置
    testTimeout: 10000,
    hookTimeout: 10000,

    // 报告器
    reporters: ['verbose'],

    // 输出
    outputFile: './test-results.json',

    // 序列化
    sequence: {
      shuffle: false
    }
  },

  // 解析配置
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})
