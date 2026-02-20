/**
 * 系统管理 API服务
 * 对接量化交易系统的系统管理接口
 */

import { get } from './request'

// ==================== 类型定义 ====================

/**
 * 系统基本信息
 */
export interface SystemInfo {
  name: string
  version: string
  environment: 'development' | 'staging' | 'production'
  start_time: string
  uptime: number
  server_time: string
  timezone: string
  api_version: string
  features: string[]
}

/**
 * 系统配置信息
 */
export interface SystemConfig {
  max_strategies_per_user: number
  max_api_keys_per_user: number
  default_commission_rate: number
  default_slippage_rate: number
  supported_exchanges: string[]
  supported_intervals: string[]
  rate_limits: {
    requests_per_minute: number
    orders_per_minute: number
  }
  maintenance_mode: boolean
  maintenance_message?: string
}

/**
 * 组件健康状态
 */
export interface ComponentHealth {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  message?: string
  last_check_time: string
  response_time?: number
}

/**
 * 系统健康检查响应
 */
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  components: ComponentHealth[]
  check_time: string
}

/**
 * 系统性能指标
 */
export interface SystemMetrics {
  cpu: {
    usage_percent: number
    cores: number
  }
  memory: {
    total: number
    used: number
    free: number
    usage_percent: number
  }
  disk: {
    total: number
    used: number
    free: number
    usage_percent: number
  }
  network: {
    bytes_sent: number
    bytes_recv: number
    packets_sent: number
    packets_recv: number
  }
  process: {
    threads: number
    open_files: number
    connections: number
  }
  application: {
    active_users: number
    active_strategies: number
    active_orders: number
    requests_per_second: number
    avg_response_time: number
  }
  timestamp: string
}

/**
 * 健康检查响应
 */
export interface HealthCheckResponse {
  status: 'ok' | 'error'
  timestamp: string
  uptime: number
}

/**
 * 数据库健康检查响应
 */
export interface DatabaseHealthResponse {
  status: 'ok' | 'error'
  database: string
  connection_pool: {
    size: number
    active: number
    idle: number
  }
  response_time: number
  timestamp: string
}

/**
 * 完整健康检查响应
 */
export interface FullHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  checks: {
    api: HealthCheckResponse
    database: DatabaseHealthResponse
    redis?: {
      status: 'ok' | 'error'
      response_time: number
    }
    message_queue?: {
      status: 'ok' | 'error'
      pending_messages: number
    }
  }
  timestamp: string
}

/**
 * 就绪检查响应
 */
export interface ReadyCheckResponse {
  ready: boolean
  message?: string
  timestamp: string
}

/**
 * 存活检查响应
 */
export interface LiveCheckResponse {
  alive: boolean
  timestamp: string
}

/**
 * 系统资源指标响应
 */
export interface MetricsResponse {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  requests_total: number
  requests_per_second: number
  errors_total: number
  avg_response_time: number
  timestamp: string
}

// ==================== API方法 ====================

/**
 * 获取系统基本信息
 */
export function getSystemInfo(): Promise<SystemInfo> {
  return get<SystemInfo>('/system/info')
}

/**
 * 获取系统配置信息
 */
export function getSystemConfig(): Promise<SystemConfig> {
  return get<SystemConfig>('/system/config')
}

/**
 * 系统组件健康检查
 */
export function getSystemHealth(): Promise<SystemHealth> {
  return get<SystemHealth>('/system/health')
}

/**
 * 获取系统性能指标
 */
export function getSystemMetrics(): Promise<SystemMetrics> {
  return get<SystemMetrics>('/system/metrics')
}

/**
 * 基础健康检查
 */
export function healthCheck(): Promise<HealthCheckResponse> {
  return get<HealthCheckResponse>('/health/')
}

/**
 * 数据库健康检查
 */
export function healthCheckDatabase(): Promise<DatabaseHealthResponse> {
  return get<DatabaseHealthResponse>('/health/db')
}

/**
 * 完整健康检查
 */
export function healthCheckFull(): Promise<FullHealthResponse> {
  return get<FullHealthResponse>('/health/full')
}

/**
 * 就绪检查
 */
export function readyCheck(): Promise<ReadyCheckResponse> {
  return get<ReadyCheckResponse>('/health/ready')
}

/**
 * 存活检查
 */
export function liveCheck(): Promise<LiveCheckResponse> {
  return get<LiveCheckResponse>('/health/live')
}

/**
 * 系统资源指标
 */
export function getHealthMetrics(): Promise<MetricsResponse> {
  return get<MetricsResponse>('/health/metrics')
}

// 导出所有API
export default {
  getSystemInfo,
  getSystemConfig,
  getSystemHealth,
  getSystemMetrics,
  healthCheck,
  healthCheckDatabase,
  healthCheckFull,
  readyCheck,
  liveCheck,
  getHealthMetrics,
}
