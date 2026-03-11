/**
 * 系统管理 API服务
 * 对接量化交易系统的系统管理接口
 */

import { get, put } from './request'
import {
  SystemInfo,
  SystemConfig,
  ComponentHealth,
  SystemHealth,
  SystemMetrics,
  HealthCheckResponse,
  DatabaseHealthResponse,
  FullHealthResponse,
  ReadyCheckResponse,
  LiveCheckResponse,
  MetricsResponse,
  LogQueryParams,
  LogEntry,
  LogListResponse,
  AuditLogParams,
  RiskLogParams,
  RiskAlert,
  RiskAlertParams,
  RiskAlertListResponse,
  ResolveAlertRequest,
  EnumItem,
  EnumInfoResponse,
  EnumListResponse,
  EnumBatchResponse, ExchangeInfo, ExchangeDict,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  SystemInfo,
  SystemConfig,
  ComponentHealth,
  SystemHealth,
  SystemMetrics,
  HealthCheckResponse,
  DatabaseHealthResponse,
  FullHealthResponse,
  ReadyCheckResponse,
  LiveCheckResponse,
  MetricsResponse,
  LogQueryParams,
  LogEntry,
  LogListResponse,
  AuditLogParams,
  RiskLogParams,
  RiskAlert,
  RiskAlertParams,
  RiskAlertListResponse,
  ResolveAlertRequest,
  EnumItem,
  EnumInfoResponse,
  EnumListResponse,
  EnumBatchResponse,
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

export function getExchanges(): Promise<ExchangeDict[]> {
  return get<ExchangeDict[]>(`/api/v1/c/enum/exchanges`)
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
  getExchanges
}
