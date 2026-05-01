import { config } from '@vue/test-utils'

// 配置Vue测试工具
config.global.mocks = {
  // 模拟Tauri API
  invoke: () => Promise.resolve(),
  listen: () => Promise.resolve(() => {}),
  emit: () => Promise.resolve(),

  // 模拟路由
  $route: {
    path: '/',
    params: {},
    query: {}
  },

  // 模拟路由
  $router: {
    push: () => {},
    replace: () => {},
    go: () => {},
    back: () => {}
  }
}

// 模拟Tauri API
;(globalThis as any).__TAURI__ = {
  invoke: () => Promise.resolve(),
  listen: () => Promise.resolve(() => {}),
  emit: () => Promise.resolve()
}

// 模拟CSS模块
;(globalThis as any).CSS = {
  supports: () => true,
  escape: (ident: string) => ident
}

// 注入 CSS 变量到 document.documentElement，使 jsdom 能读取设计令牌
document.documentElement.style.setProperty('--srn-font-mono', 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, mono')
document.documentElement.style.setProperty('--srn-font-sans', '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif')
document.documentElement.style.setProperty('--srn-color-primary', '#e53e3e')
document.documentElement.style.setProperty('--srn-color-border', '#e2e8f0')
document.documentElement.style.setProperty('--srn-color-surface-1', '#ffffff')
document.documentElement.style.setProperty('--srn-color-surface-2', '#f7fafc')
document.documentElement.style.setProperty('--srn-color-text-1', '#1a202c')
document.documentElement.style.setProperty('--srn-color-text-2', '#4a5568')
document.documentElement.style.setProperty('--srn-color-text-3', '#718096')

// 模拟ResizeObserver
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// 模拟IntersectionObserver
;(globalThis as any).IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// 模拟MatchMedia
;(globalThis as any).matchMedia = () => ({
  matches: false,
  media: '',
  onchange: null,
  addListener: () => {},
  removeListener: () => {},
  addEventListener: () => {},
  removeEventListener: () => {},
  dispatchEvent: () => true
})

// 模拟Console方法
const originalConsole = { ...console }
const mockConsole = {
  log: () => {},
  warn: () => {},
  error: () => {},
  info: () => {},
  debug: () => {}
}

// 在测试期间模拟console
;(globalThis as any).beforeEach(() => {
  Object.assign(console, mockConsole)
})

;(globalThis as any).afterEach(() => {
  Object.assign(console, originalConsole)
})
