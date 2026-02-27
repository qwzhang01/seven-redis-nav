/**
 * 用户API服务
 * 对接量化交易系统的用户管理接口
 */

import { get, post, put, del } from './request'
import type {
  RegisterRequest,
  LoginRequest,
  LoginResponse,
  UserResponse,
  UserProfile,
  UpdateProfileRequest,
  ChangePasswordRequest,
  ResetPasswordRequest,
  RefreshTokenRequest,
  RefreshTokenResponse,
  ExchangeInfo,
  CreateAPIKeyRequest,
  UpdateAPIKeyRequest,
  APIKeyResponse,
  APIKeyListResponse,
  SignalFollow,
  CreateFollowRequest,
  UpdateFollowConfigRequest,
  SignalFollowPosition,
  SignalFollowTrade,
  UserStatistics,
  UpdateUserRequest,
  UpdateUserStatusRequest,
  // 扩展类型
  GetSignalFollowsParams,
  GetSignalFollowsResponse,
  CreateSignalFollowApiResponse,
  GetSignalFollowDetailResponse,
  UpdateSignalFollowApiResponse,
  StopSignalFollowResponse,
  GetSignalFollowPositionsParams,
  GetSignalFollowPositionsResponse,
  GetSignalFollowTradesParams,
  GetSignalFollowTradesResponse,
  GetUsersParams,
  GetUsersResponse,
  GetUserDetailResponse,
  UpdateUserResponse,
  UpdateUserStatusResponse,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
  UserProfile,
  RegisterRequest,
  LoginRequest,
  UserResponse,
  GetSignalFollowsParams,
  GetSignalFollowsResponse,
  GetSignalFollowPositionsParams,
  GetSignalFollowPositionsResponse,
  GetSignalFollowTradesParams,
  GetSignalFollowTradesResponse,
  GetUsersParams,
  GetUsersResponse,
  GetUserDetailResponse,
  UpdateUserResponse,
  UpdateUserStatusResponse,
}
// 向后兼容别名
export type { CreateSignalFollowApiResponse as CreateSignalFollowResponse }
export type { UpdateSignalFollowApiResponse as UpdateSignalFollowConfigResponse }
export type { GetSignalFollowDetailResponse }
export type { StopSignalFollowResponse }

// ==================== API方法 ====================

/**
 * 用户注册
 */
export function register(data: RegisterRequest): Promise<UserResponse> {
  return post<UserResponse>('/api/v1/c/user/register', data, { skipAuth: true })
}

/**
 * 用户登录
 */
export function login(data: LoginRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/api/v1/c/user/login', data, { skipAuth: true })
}

/**
 * 更新用户信息
 */
export function updateProfile(data: UpdateProfileRequest): Promise<UserResponse> {
  return put<UserResponse>('/api/v1/c/user/profile', data)
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
  return post<{ message: string }>('/api/v1/c/user/password/change', data)
}

/**
 * 刷新Token
 * 使用 refresh_token 换取新的 access_token 和 refresh_token
 */
export function refreshToken(data: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  return post<RefreshTokenResponse>('/api/v1/c/user/token/refresh', data, { skipAuth: true, skipErrorHandler: true })
}

/**
 * 忘记密码重置
 */
export function resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
  return post<{ message: string }>('/api/v1/c/user/password/reset', data, { skipAuth: true })
}

/**
 * 获取交易所详情
 */
export function getExchangeById(exchangeId: string): Promise<ExchangeInfo> {
  return get<ExchangeInfo>(`/api/v1/c/user/exchanges/${exchangeId}`)
}

/**
 * 添加API密钥
 */
export function addApiKey(data: CreateAPIKeyRequest): Promise<APIKeyResponse> {
  return post<APIKeyResponse>('/api/v1/c/user/api-keys', data)
}

/**
 * 获取API密钥列表
 */
export function getApiKeys(status?: 'pending' | 'approved' | 'rejected' | 'disabled'): Promise<APIKeyListResponse> {
  const params = status ? { status } : undefined
  return get<APIKeyListResponse>('/api/v1/c/user/api-keys', params)
}

/**
 * 获取API密钥详情
 */
export function getApiKeyById(keyId: string): Promise<APIKeyResponse> {
  return get<APIKeyResponse>(`/api/v1/c/user/api-keys/${keyId}`)
}

/**
 * 更新API密钥
 */
export function updateApiKey(keyId: string, data: UpdateAPIKeyRequest): Promise<APIKeyResponse> {
  return put<APIKeyResponse>(`/api/v1/c/user/api-keys/${keyId}`, data)
}

/**
 * 删除API密钥
 */
export function deleteApiKey(keyId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/c/user/api-keys/${keyId}`)
}

// ==================== 信号跟单接口 ====================

/**
 * 获取我的跟单列表
 */
export function getSignalFollows(params?: GetSignalFollowsParams): Promise<GetSignalFollowsResponse> {
  return get<GetSignalFollowsResponse>('/api/v1/c/user/signal-follows', params)
}

export function createSignalFollow(data: CreateFollowRequest): Promise<CreateSignalFollowApiResponse> {
  return post<CreateSignalFollowApiResponse>('/api/v1/c/user/signal-follows', data)
}

/**
 * 获取跟单详情
 */
export function getSignalFollowDetail(followId: number): Promise<GetSignalFollowDetailResponse> {
  return get<GetSignalFollowDetailResponse>(`/api/v1/c/user/signal-follows/${followId}`)
}

export function updateSignalFollowConfig(followId: number, data: UpdateFollowConfigRequest): Promise<UpdateSignalFollowApiResponse> {
  return put<UpdateSignalFollowApiResponse>(`/api/v1/c/user/signal-follows/${followId}/config`, data)
}

/**
 * 停止跟单
 */
export function stopSignalFollow(followId: number): Promise<StopSignalFollowResponse> {
  return post<StopSignalFollowResponse>(`/api/v1/c/user/signal-follows/${followId}/stop`)
}

/**
 * 获取跟单持仓列表
 */
export function getSignalFollowPositions(followId: number, params?: GetSignalFollowPositionsParams): Promise<GetSignalFollowPositionsResponse> {
  return get<GetSignalFollowPositionsResponse>(`/api/v1/c/user/signal-follows/${followId}/positions`, params)
}

/**
 * 获取跟单交易记录
 */
export function getSignalFollowTrades(followId: number, params?: GetSignalFollowTradesParams): Promise<GetSignalFollowTradesResponse> {
  return get<GetSignalFollowTradesResponse>(`/api/v1/c/user/signal-follows/${followId}/trades`, params)
}

// ==================== Admin端用户管理接口 ====================

/**
 * 获取用户列表
 */
export function getUsers(params?: GetUsersParams): Promise<GetUsersResponse> {
  return get<GetUsersResponse>('/api/v1/m/users', params)
}

/**
 * 获取用户详情（Admin）
 */
export function getUserDetail(userId: number): Promise<GetUserDetailResponse> {
  return get<GetUserDetailResponse>(`/api/v1/m/users/${userId}`)
}

export function updateUser(userId: number, data: UpdateUserRequest): Promise<UpdateUserResponse> {
  return put<UpdateUserResponse>(`/api/v1/m/users/${userId}`, data)
}

export function updateUserStatus(userId: number, data: UpdateUserStatusRequest): Promise<UpdateUserStatusResponse> {
  return put<UpdateUserStatusResponse>(`/api/v1/m/users/${userId}/status`, data)
}

// 导出所有API
export default {
  // 用户认证
  register,
  login,
  refreshToken,
  updateProfile,
  changePassword,
  resetPassword,
  // 交易所和API密钥
  getExchangeById,
  addApiKey,
  getApiKeys,
  getApiKeyById,
  updateApiKey,
  deleteApiKey,
  // 信号跟单
  getSignalFollows,
  createSignalFollow,
  getSignalFollowDetail,
  updateSignalFollowConfig,
  stopSignalFollow,
  getSignalFollowPositions,
  getSignalFollowTrades,
  // Admin端用户管理
  getUsers,
  getUserDetail,
  updateUser,
  updateUserStatus,
}
