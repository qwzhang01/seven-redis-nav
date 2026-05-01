import { mount, shallowMount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { vi, expect } from 'vitest'
import type { Component } from 'vue'

/**
 * 测试工具函数集合
 */

// 创建Pinia实例
export function createTestPinia() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return pinia
}

// 模拟Tauri API调用
export function mockTauriApi() {
  return {
    invoke: vi.fn().mockResolvedValue({}),
    listen: vi.fn().mockResolvedValue(() => {}),
    emit: vi.fn().mockResolvedValue({})
  }
}

// 模拟Redis数据
export function mockRedisData() {
  return {
    // 模拟键数据
    key: {
      key: 'test:key',
      key_type: 'string',
      value: 'test value',
      ttl: -1,
      size: 10,
      encoding: 'raw',
      length: 1,
      db: 0
    },

    // 模拟哈希数据
    hash: {
      key: 'test:hash',
      key_type: 'hash',
      value: { field1: 'value1', field2: 'value2' },
      ttl: 3600,
      size: 20,
      encoding: 'hashtable',
      length: 2,
      db: 0
    },

    // 模拟列表数据
    list: {
      key: 'test:list',
      key_type: 'list',
      value: ['item1', 'item2', 'item3'],
      ttl: 1800,
      size: 15,
      encoding: 'linkedlist',
      length: 3,
      db: 0
    }
  }
}

// 模拟连接配置
export function mockConnectionConfig() {
  return {
    id: 'test-connection',
    name: 'Test Connection',
    host: 'localhost',
    port: 6379,
    password: '',
    db: 0,
    timeout: 5000,
    ssl: false
  }
}

// 组件挂载工具
export function mountComponent(
  component: Component,
  options: any = {}
): VueWrapper {
  return mount(component, {
    global: {
      plugins: [createTestPinia()],
      mocks: {
        ...mockTauriApi()
      }
    },
    ...options
  })
}

export function shallowMountComponent(
  component: Component,
  options: any = {}
): VueWrapper {
  return shallowMount(component, {
    global: {
      plugins: [createTestPinia()],
      mocks: {
        ...mockTauriApi()
      }
    },
    ...options
  })
}

// 异步工具函数
export async function waitFor(callback: () => void, timeout = 1000) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    try {
      callback()
      return
    } catch {
      await new Promise(resolve => setTimeout(resolve, 10))
    }
  }
  throw new Error('Timeout waiting for callback')
}

export async function waitForNextTick() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

// 事件模拟
export function mockEvent() {
  return {
    preventDefault: vi.fn(),
    stopPropagation: vi.fn(),
    target: {
      value: ''
    }
  }
}

// 断言工具
export function expectElement(wrapper: VueWrapper, selector: string) {
  const element = wrapper.find(selector)
  expect(element.exists()).toBe(true)
  return element
}

export function expectNoElement(wrapper: VueWrapper, selector: string) {
  const element = wrapper.find(selector)
  expect(element.exists()).toBe(false)
}

export function expectText(wrapper: VueWrapper, selector: string, text: string) {
  const element = wrapper.find(selector)
  expect(element.text()).toBe(text)
}

export function expectClass(wrapper: VueWrapper, selector: string, className: string) {
  const element = wrapper.find(selector)
  expect(element.classes()).toContain(className)
}

// 模拟用户输入
export async function simulateInput(wrapper: VueWrapper, selector: string, value: string) {
  const input = wrapper.find(selector)
  await input.setValue(value)
}

export async function simulateClick(wrapper: VueWrapper, selector: string) {
  const button = wrapper.find(selector)
  await button.trigger('click')
}

// 模拟键盘事件
export async function simulateKey(wrapper: VueWrapper, selector: string, key: string) {
  const element = wrapper.find(selector)
  await element.trigger('keydown', { key })
}

// 模拟路由
export function mockRouter() {
  return {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn()
  }
}

// 模拟Store状态
export function mockStoreState() {
  return {
    connections: [mockConnectionConfig()],
    currentConnection: mockConnectionConfig(),
    currentKey: mockRedisData().key,
    keys: ['test:key', 'test:hash', 'test:list'],
    loading: false,
    error: null
  }
}

// 性能测试工具
export function measurePerformance(callback: () => void) {
  const start = performance.now()
  callback()
  const end = performance.now()
  return end - start
}

// 内存使用监控
export function getMemoryUsage() {
  const perf = globalThis.performance as any
  if (perf && perf.memory) {
    return {
      used: perf.memory.usedJSHeapSize,
      total: perf.memory.totalJSHeapSize,
      limit: perf.memory.jsHeapSizeLimit
    }
  }
  return null
}

// 测试数据生成器
export function generateTestData(count: number, prefix = 'test') {
  return Array.from({ length: count }, (_, i) => ({
    key: `${prefix}:${i}`,
    key_type: i % 5 === 0 ? 'string' : i % 5 === 1 ? 'hash' : i % 5 === 2 ? 'list' : i % 5 === 3 ? 'set' : 'zset',
    value: `value-${i}`,
    ttl: i % 10 === 0 ? -1 : 3600,
    size: Math.floor(Math.random() * 100) + 10,
    encoding: 'raw',
    length: Math.floor(Math.random() * 10) + 1,
    db: 0
  }))
}
