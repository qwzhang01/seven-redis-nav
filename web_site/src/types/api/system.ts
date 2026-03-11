/**
 * 系统管理相关API类型定义
 */

// ==================== 系统信息 ====================

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

// ==================== 健康检查 ====================

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

// ==================== 日志审计 ====================

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

// ==================== 交易所 ====================

/**
 * 交易所信息
 */
export interface ExchangeDict {
  id: number
  exchange_code: string
  exchange_name: string
  exchange_type: string
  base_url: string
  api_doc_url: string
  status: string
  supported_pairs: string[]
  rate_limits: Record<string, any>
  create_time: string
  update_time: string
}

// ==================== 枚举查询 ====================

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
