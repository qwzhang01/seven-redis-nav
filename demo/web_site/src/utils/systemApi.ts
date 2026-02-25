/**
 * 系统管理 API服务
 * 对接量化交易系统的系统管理接口
 */

import { get, put } from './request'

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
  return get<SystemInfo>('/api/v1/m/system/info')
}

/**
 * 获取系统配置信息
 */
export function getSystemConfig(): Promise<SystemConfig> {
  return get<SystemConfig>('/api/v1/m/system/config')
}

/**
 * 系统组件健康检查
 */
export function getSystemHealth(): Promise<SystemHealth> {
  return get<SystemHealth>('/api/v1/m/system/health')
}

/**
 * 获取系统性能指标
 */
export function getSystemMetrics(): Promise<SystemMetrics> {
  return get<SystemMetrics>('/api/v1/m/system/metrics')
}

/**
 * 基础健康检查
 */
export function healthCheck(): Promise<HealthCheckResponse> {
  return get<HealthCheckResponse>('/api/v1/m/health/')
}

/**
 * 数据库健康检查
 */
export function healthCheckDatabase(): Promise<DatabaseHealthResponse> {
  return get<DatabaseHealthResponse>('/api/v1/m/health/db')
}

/**
 * 完整健康检查
 */
export function healthCheckFull(): Promise<FullHealthResponse> {
  return get<FullHealthResponse>('/api/v1/m/health/full')
}

/**
 * 就绪检查
 */
export function readyCheck(): Promise<ReadyCheckResponse> {
  return get<ReadyCheckResponse>('/api/v1/m/health/ready')
}

/**
 * 存活检查
 */
export function liveCheck(): Promise<LiveCheckResponse> {
  return get<LiveCheckResponse>('/api/v1/m/health/live')
}

/**
 * 系统资源指标
 */
export function getHealthMetrics(): Promise<MetricsResponse> {
  return get<MetricsResponse>('/api/v1/m/health/metrics')
}

// ==================== M端日志审计接口 ====================

/**
 * 日志查询基础参数
 */
export interface LogQueryParams {
  level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  username?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 日志条目
 */
export interface LogEntry {
  id: string
  category: string
  level: string
  username?: string
  action?: string
  message: string
  details?: Record<string, any>
  timestamp: string
}

/**
 * 日志列表响应
 */
export interface LogListResponse {
  items: LogEntry[]
  total: number
  page: number
  page_size: number
}

/**
 * 审计日志查询参数
 */
export interface AuditLogParams extends LogQueryParams {
  category?: 'system' | 'trading' | 'strategy' | 'user' | 'risk' | 'market'
  action?: string
}

/**
 * 风控日志查询参数
 */
export interface RiskLogParams {
  level?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

/**
 * 风控告警
 */
export interface RiskAlert {
  id: string
  severity: 'info' | 'warning' | 'critical'
  alert_type: 'drawdown' | 'position_limit' | 'loss_limit' | 'volatility'
  strategy_id?: string
  message: string
  details?: Record<string, any>
  is_resolved: boolean
  resolved_by?: string
  resolved_at?: string
  note?: string
  created_at: string
}

/**
 * 风控告警列表查询参数
 */
export interface RiskAlertParams {
  severity?: 'info' | 'warning' | 'critical'
  alert_type?: 'drawdown' | 'position_limit' | 'loss_limit' | 'volatility'
  is_resolved?: boolean
  strategy_id?: string
  page?: number
  page_size?: number
}

/**
 * 风控告警列表响应
 */
export interface RiskAlertListResponse {
  items: RiskAlert[]
  total: number
  page: number
  page_size: number
}

/**
 * 标记告警已处理请求
 */
export interface ResolveAlertRequest {
  resolved_by?: string
  note?: string
}

/**
 * 获取系统操作日志
 */
export function getSystemLogs(params?: LogQueryParams): Promise<LogListResponse> {
  return get<LogListResponse>('/api/v1/m/logs/system', params)
}

/**
 * 获取交易日志
 */
export function getTradingLogs(params?: LogQueryParams): Promise<LogListResponse> {
  return get<LogListResponse>('/api/v1/m/logs/trading', params)
}

/**
 * 获取风控日志
 */
export function getRiskLogs(params?: RiskLogParams): Promise<LogListResponse> {
  return get<LogListResponse>('/api/v1/m/logs/risk', params)
}

/**
 * 获取审计日志（全量）
 */
export function getAuditLogs(params?: AuditLogParams): Promise<LogListResponse> {
  return get<LogListResponse>('/api/v1/m/logs/audit', params)
}

/**
 * 获取风控告警列表
 */
export function getRiskAlerts(params?: RiskAlertParams): Promise<RiskAlertListResponse> {
  return get<RiskAlertListResponse>('/api/v1/m/logs/risk/alerts', params)
}

/**
 * 标记告警已处理
 */
export function resolveRiskAlert(alertId: string, data?: ResolveAlertRequest): Promise<{ success: boolean; message: string }> {
  return put<{ success: boolean; message: string }>(`/api/v1/m/logs/risk/alerts/${alertId}/resolve`, data)
}

// ==================== C端枚举查询接口 ====================

/**
 * 枚举项
 */
export interface EnumItem {
  value: string
  label: string
  description?: string
}

/**
 * 枚举信息响应
 */
export interface EnumInfoResponse {
  name: string
  items: EnumItem[]
}

/**
 * 枚举列表响应
 */
export interface EnumListResponse {
  enums: string[]
}

/**
 * 批量枚举响应
 */
export interface EnumBatchResponse {
  enums: Record<string, EnumItem[]>
}

/**
 * 获取所有可用枚举名称
 */
export function getEnumList(): Promise<EnumListResponse> {
  return get<EnumListResponse>('/api/v1/c/enum/list')
}

/**
 * 按名称获取枚举值
 */
export function getEnumByName(enumName: string): Promise<EnumInfoResponse> {
  return get<EnumInfoResponse>(`/api/v1/c/enum/${enumName}`)
}

/**
 * 批量获取枚举值
 */
export function getEnumBatch(enumNames: string[]): Promise<EnumBatchResponse> {
  return get<EnumBatchResponse>(`/api/v1/c/enum/batch/${enumNames.join(',')}`)
}

// 导出所有API
export default {
  // 系统管理
  getSystemInfo,
  getSystemConfig,
  getSystemHealth,
  getSystemMetrics,
  // 健康检查
  healthCheck,
  healthCheckDatabase,
  healthCheckFull,
  readyCheck,
  liveCheck,
  getHealthMetrics,
  // 日志审计
  getSystemLogs,
  getTradingLogs,
  getRiskLogs,
  getAuditLogs,
  getRiskAlerts,
  resolveRiskAlert,
  // C端枚举查询
  getEnumList,
  getEnumByName,
  getEnumBatch,
}
