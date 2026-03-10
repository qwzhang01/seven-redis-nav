/**
 * 通用API类型定义
 */

// ==================== 通用响应类型 ====================

/**
 * 标准API响应
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

/**
 * 分页参数
 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/**
 * 分页响应
 */
export interface PaginationResponse<T = any> {
  items: T[]
  total: number
  page: number
  page_size?: number
  pages?: number
}

/**
 * 列表查询参数
 */
export interface ListParams extends PaginationParams {
  search?: string
  sort?: string
  order?: 'asc' | 'desc'
}

// ==================== 时间范围 ====================

/**
 * 时间范围参数
 */
export interface TimeRangeParams {
  start_time?: string | number
  end_time?: string | number
}

// ==================== 状态相关 ====================

/**
 * 通用状态
 */
export type CommonStatus = 'active' | 'inactive' | 'pending' | 'disabled'

// ==================== 错误处理 ====================

/**
 * API错误响应
 */
export interface ApiError {
  code: string
  message: string
  details?: any
}

/**
 * 验证错误
 */
export interface ValidationError {
  field: string
  message: string
}
