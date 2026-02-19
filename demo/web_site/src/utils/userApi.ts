/**
 * 用户API服务
 * 对接量化交易系统的用户管理接口
 */

import { get, post, put, del } from './request'

// ==================== 类型定义 ====================

/**
 * 用户注册请求
 */
export interface RegisterRequest {
  username: string
  nickname: string
  email: string
  password: string
  phone?: string
  avatar_url?: string
}

/**
 * 用户登录请求
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * 用户登录响应
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserProfile
}

/**
 * 用户信息
 */
export interface UserProfile {
  id: string
  username: string
  nickname: string
  email: string
  email_verified: boolean
  phone?: string
  phone_verified: boolean
  avatar_url?: string
  user_type: 'customer' | 'admin'
  registration_time: string
  last_login_time?: string
  status: 'active' | 'inactive' | 'locked'
  create_time: string
  update_time?: string
}

/**
 * 更新用户信息请求
 */
export interface UpdateProfileRequest {
  nickname?: string
  email?: string
  phone?: string
  avatar_url?: string
}

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 忘记密码重置请求
 */
export interface ResetPasswordRequest {
  email: string
  verification_code: string
  new_password: string
}

/**
 * 交易所信息
 */
export interface ExchangeInfo {
  id: string
  exchange_code: string
  exchange_name: string
  exchange_type: 'spot' | 'futures' | 'margin'
  base_url: string
  api_doc_url?: string
  status: 'active' | 'inactive'
  supported_pairs?: string[]
  rate_limits?: Record<string, any>
  create_time: string
  update_time?: string
}

/**
 * API密钥权限
 */
export interface ApiKeyPermissions {
  spot_trading?: boolean
  margin_trading?: boolean
  futures_trading?: boolean
  withdraw?: boolean
}

/**
 * 添加API密钥请求
 */
export interface AddApiKeyRequest {
  exchange_id: string
  label: string
  api_key: string
  secret_key: string
  passphrase?: string
  permissions?: ApiKeyPermissions
}

/**
 * 更新API密钥请求
 */
export interface UpdateApiKeyRequest {
  label?: string
  permissions?: ApiKeyPermissions
  status?: 'pending' | 'approved' | 'rejected' | 'disabled'
}

/**
 * API密钥信息
 */
export interface ApiKeyInfo {
  id: string
  user_id: string
  exchange_id: string
  exchange_name?: string
  exchange_code?: string
  label: string
  api_key: string
  secret_key_masked?: string
  status: 'pending' | 'approved' | 'rejected' | 'disabled'
  review_reason?: string
  approved_by?: string
  approved_time?: string
  last_used_time?: string
  permissions?: ApiKeyPermissions
  create_time: string
  update_time?: string
}

/**
 * API密钥列表响应
 */
export interface ApiKeyListResponse {
  total: number
  items: ApiKeyInfo[]
}

// ==================== API方法 ====================

/**
 * 用户注册
 */
export function register(data: RegisterRequest): Promise<UserProfile> {
  return post<UserProfile>('/register', data, { skipAuth: true })
}

/**
 * 用户登录
 */
export function login(data: LoginRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/login', data, { skipAuth: true })
}

/**
 * 更新用户信息
 */
export function updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
  return put<UserProfile>('/profile', data)
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
  return post<{ message: string }>('/password/change', data)
}

/**
 * 忘记密码重置
 */
export function resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
  return post<{ message: string }>('/password/reset', data, { skipAuth: true })
}

/**
 * 获取交易所详情
 */
export function getExchangeById(exchangeId: string): Promise<ExchangeInfo> {
  return get<ExchangeInfo>(`/exchanges/${exchangeId}`)
}

/**
 * 添加API密钥
 */
export function addApiKey(data: AddApiKeyRequest): Promise<ApiKeyInfo> {
  return post<ApiKeyInfo>('/api-keys', data)
}

/**
 * 获取API密钥列表
 */
export function getApiKeys(status?: 'pending' | 'approved' | 'rejected' | 'disabled'): Promise<ApiKeyListResponse> {
  const params = status ? { status } : undefined
  return get<ApiKeyListResponse>('/api-keys', params)
}

/**
 * 获取API密钥详情
 */
export function getApiKeyById(keyId: string): Promise<ApiKeyInfo> {
  return get<ApiKeyInfo>(`/api-keys/${keyId}`)
}

/**
 * 更新API密钥
 */
export function updateApiKey(keyId: string, data: UpdateApiKeyRequest): Promise<ApiKeyInfo> {
  return put<ApiKeyInfo>(`/api-keys/${keyId}`, data)
}

/**
 * 删除API密钥
 */
export function deleteApiKey(keyId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api-keys/${keyId}`)
}

// 导出所有API
export default {
  register,
  login,
  updateProfile,
  changePassword,
  resetPassword,
  getExchangeById,
  addApiKey,
  getApiKeys,
  getApiKeyById,
  updateApiKey,
  deleteApiKey,
}
