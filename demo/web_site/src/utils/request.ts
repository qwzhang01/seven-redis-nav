/**
 * API请求工具
 * 基于fetch封装，支持请求拦截、响应拦截、错误处理
 */

import { MessagePlugin } from 'tdesign-vue-next'

// API基础配置
// 如果环境变量未定义，使用默认值；如果定义为空字符串，则使用空字符串（相对路径）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined 
  ? import.meta.env.VITE_API_BASE_URL 
  : 'http://127.0.0.1:8000'

// 响应接口
interface ApiResponse<T = any> {
  code?: number
  message?: string
  data?: T
  [key: string]: any
}

// 请求配置接口
interface RequestConfig extends RequestInit {
  skipAuth?: boolean // 是否跳过认证
  skipErrorHandler?: boolean // 是否跳过错误处理
}

/**
 * 获取认证token
 */
function getToken(): string | null {
  return localStorage.getItem('qm_token')
}

/**
 * 设置认证token
 */
export function setToken(token: string) {
  localStorage.setItem('qm_token', token)
}

/**
 * 清除认证token
 */
export function clearToken() {
  localStorage.removeItem('qm_token')
  localStorage.removeItem('qm_user')
}

/**
 * 请求拦截器
 */
function requestInterceptor(url: string, config: RequestConfig): [string, RequestInit] {
  // 设置默认headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(config.headers as Record<string, string> || {}),
  }

  // 添加认证token
  if (!config.skipAuth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  // 处理完整URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`

  return [
    fullUrl,
    {
      ...config,
      headers,
    },
  ]
}

/**
 * 响应拦截器
 */
async function responseInterceptor<T>(response: Response, config: RequestConfig): Promise<T> {
  // 处理HTTP错误状态
  if (!response.ok) {
    if (response.status === 401) {
      // 未授权，清除token并跳转登录
      clearToken()
      if (!config.skipErrorHandler) {
        MessagePlugin.error('登录已过期，请重新登录')
        // 延迟跳转，避免在某些场景下立即跳转
        setTimeout(() => {
          window.location.href = '/login'
        }, 1000)
      }
      throw new Error('未授权')
    }

    if (response.status === 403) {
      if (!config.skipErrorHandler) {
        MessagePlugin.error('没有权限访问')
      }
      throw new Error('没有权限')
    }

    if (response.status === 404) {
      if (!config.skipErrorHandler) {
        MessagePlugin.error('请求的资源不存在')
      }
      throw new Error('资源不存在')
    }

    if (response.status >= 500) {
      if (!config.skipErrorHandler) {
        MessagePlugin.error('服务器错误，请稍后重试')
      }
      throw new Error('服务器错误')
    }
  }

  // 解析响应数据
  const contentType = response.headers.get('content-type')
  let data: any

  if (contentType?.includes('application/json')) {
    data = await response.json()
  } else {
    data = await response.text()
  }

  // 处理业务错误
  if (data && typeof data === 'object') {
    // 如果返回的数据包含code字段，检查业务状态码
    if ('code' in data && data.code !== 0 && data.code !== 200) {
      if (!config.skipErrorHandler) {
        MessagePlugin.error(data.message || '请求失败')
      }
      throw new Error(data.message || '请求失败')
    }

    // 返回data字段或整个响应
    return (data.data !== undefined ? data.data : data) as T
  }

  return data as T
}

/**
 * 通用请求方法
 */
async function request<T = any>(url: string, config: RequestConfig = {}): Promise<T> {
  try {
    const [fullUrl, requestConfig] = requestInterceptor(url, config)
    const response = await fetch(fullUrl, requestConfig)
    return await responseInterceptor<T>(response, config)
  } catch (error) {
    // 网络错误或其他异常
    if (error instanceof TypeError && error.message.includes('fetch')) {
      if (!config.skipErrorHandler) {
        MessagePlugin.error('网络连接失败，请检查网络')
      }
      throw new Error('网络连接失败')
    }
    throw error
  }
}

/**
 * GET请求
 */
export function get<T = any>(url: string, params?: Record<string, any>, config?: RequestConfig): Promise<T> {
  // 构建查询参数
  if (params) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
    ).toString()
    url = queryString ? `${url}?${queryString}` : url
  }

  return request<T>(url, {
    ...config,
    method: 'GET',
  })
}

/**
 * POST请求
 */
export function post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>(url, {
    ...config,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT请求
 */
export function put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>(url, {
    ...config,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE请求
 */
export function del<T = any>(url: string, config?: RequestConfig): Promise<T> {
  return request<T>(url, {
    ...config,
    method: 'DELETE',
  })
}

/**
 * PATCH请求
 */
export function patch<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
  return request<T>(url, {
    ...config,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
}

export default {
  get,
  post,
  put,
  delete: del,
  patch,
  setToken,
  clearToken,
}
