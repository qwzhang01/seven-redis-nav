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
  return post<UserProfile>('/api/v1/c/user/register', data, { skipAuth: true })
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
export function updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
  return put<UserProfile>('/api/v1/c/user/profile', data)
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
  return post<{ message: string }>('/api/v1/c/user/password/change', data)
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
export function addApiKey(data: AddApiKeyRequest): Promise<ApiKeyInfo> {
  return post<ApiKeyInfo>('/api/v1/c/user/api-keys', data)
}

/**
 * 获取API密钥列表
 */
export function getApiKeys(status?: 'pending' | 'approved' | 'rejected' | 'disabled'): Promise<ApiKeyListResponse> {
  const params = status ? { status } : undefined
  return get<ApiKeyListResponse>('/api/v1/c/user/api-keys', params)
}

/**
 * 获取API密钥详情
 */
export function getApiKeyById(keyId: string): Promise<ApiKeyInfo> {
  return get<ApiKeyInfo>(`/api/v1/c/user/api-keys/${keyId}`)
}

/**
 * 更新API密钥
 */
export function updateApiKey(keyId: string, data: UpdateApiKeyRequest): Promise<ApiKeyInfo> {
  return put<ApiKeyInfo>(`/api/v1/c/user/api-keys/${keyId}`, data)
}

/**
 * 删除API密钥
 */
export function deleteApiKey(keyId: string): Promise<{ message: string }> {
  return del<{ message: string }>(`/api/v1/c/user/api-keys/${keyId}`)
}

// ==================== 信号跟单接口 ====================

/**
 * 跟单记录
 */
export interface SignalFollow {
  id: number
  user_id: number
  strategy_id: string
  signal_name: string
  exchange: string
  follow_amount: number
  current_value: number
  follow_ratio: number
  stop_loss: number | null
  total_return: number
  max_drawdown: number
  current_drawdown: number
  today_return: number
  win_rate: number
  total_trades: number
  win_trades: number
  loss_trades: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  risk_level: string
  status: 'following' | 'stopped' | 'paused'
  follow_days: number
  start_time: string | null
  stop_time: string | null
  return_curve: number[]
  return_curve_labels: string[]
  create_time: string
  update_time: string
}

/**
 * 获取我的跟单列表
 */
export interface GetSignalFollowsParams {
  status?: 'following' | 'stopped' | 'paused'
  page?: number
  page_size?: number
}

export interface GetSignalFollowsResponse {
  success: boolean
  data: {
    items: SignalFollow[]
    total: number
    page: number
    pages: number
  }
}

export function getSignalFollows(params?: GetSignalFollowsParams): Promise<GetSignalFollowsResponse> {
  return get<GetSignalFollowsResponse>('/api/v1/c/user/signal-follows', params)
}

/**
 * 创建跟单
 */
export interface CreateSignalFollowRequest {
  strategy_id: string
  signal_name: string
  exchange?: string
  follow_amount: number
  follow_ratio?: number
  stop_loss?: number
}

export interface CreateSignalFollowResponse {
  success: boolean
  data: SignalFollow
  message: string
}

export function createSignalFollow(data: CreateSignalFollowRequest): Promise<CreateSignalFollowResponse> {
  return post<CreateSignalFollowResponse>('/api/v1/c/user/signal-follows', data)
}

/**
 * 获取跟单详情
 */
export interface GetSignalFollowDetailResponse {
  success: boolean
  data: SignalFollow
}

export function getSignalFollowDetail(followId: number): Promise<GetSignalFollowDetailResponse> {
  return get<GetSignalFollowDetailResponse>(`/api/v1/c/user/signal-follows/${followId}`)
}

/**
 * 更新跟单配置
 */
export interface UpdateSignalFollowConfigRequest {
  follow_amount?: number
  follow_ratio?: number
  stop_loss?: number
}

export interface UpdateSignalFollowConfigResponse {
  success: boolean
  data: SignalFollow
  message: string
}

export function updateSignalFollowConfig(followId: number, data: UpdateSignalFollowConfigRequest): Promise<UpdateSignalFollowConfigResponse> {
  return put<UpdateSignalFollowConfigResponse>(`/api/v1/c/user/signal-follows/${followId}/config`, data)
}

/**
 * 停止跟单
 */
export interface StopSignalFollowResponse {
  success: boolean
  data: SignalFollow
  message: string
}

export function stopSignalFollow(followId: number): Promise<StopSignalFollowResponse> {
  return post<StopSignalFollowResponse>(`/api/v1/c/user/signal-follows/${followId}/stop`)
}

/**
 * 跟单持仓
 */
export interface SignalFollowPosition {
  id: number
  follow_order_id: string
  symbol: string
  side: 'buy' | 'sell'
  amount: number
  entry_price: number
  current_price: number
  pnl: number
  pnl_percent: number
  status: 'open' | 'closed'
  open_time: string
  close_time: string | null
}

/**
 * 获取跟单持仓列表
 */
export interface GetSignalFollowPositionsParams {
  status?: 'open' | 'closed'
  page?: number
  page_size?: number
}

export interface GetSignalFollowPositionsResponse {
  success: boolean
  data: {
    items: SignalFollowPosition[]
    total: number
    page: number
    pages: number
  }
}

export function getSignalFollowPositions(followId: number, params?: GetSignalFollowPositionsParams): Promise<GetSignalFollowPositionsResponse> {
  return get<GetSignalFollowPositionsResponse>(`/api/v1/c/user/signal-follows/${followId}/positions`, params)
}

/**
 * 跟单交易记录
 */
export interface SignalFollowTrade {
  id: number
  follow_order_id: string
  position_id: string | null
  symbol: string
  side: 'buy' | 'sell'
  price: number
  amount: number
  total: number
  pnl: number | null
  fee: number
  signal_record_id: string | null
  trade_time: string
}

/**
 * 获取跟单交易记录
 */
export interface GetSignalFollowTradesParams {
  symbol?: string
  side?: 'buy' | 'sell'
  page?: number
  page_size?: number
}

export interface GetSignalFollowTradesResponse {
  success: boolean
  data: {
    items: SignalFollowTrade[]
    total: number
    page: number
    pages: number
  }
}

export function getSignalFollowTrades(followId: number, params?: GetSignalFollowTradesParams): Promise<GetSignalFollowTradesResponse> {
  return get<GetSignalFollowTradesResponse>(`/api/v1/c/user/signal-follows/${followId}/trades`, params)
}

// ==================== Admin端用户管理接口 ====================

/**
 * 用户统计信息
 */
export interface UserStatistics {
  total_users: number
  active_users: number
  today_new: number
  locked_users: number
}

/**
 * 获取用户列表
 */
export interface GetUsersParams {
  search?: string
  status?: 'active' | 'inactive' | 'locked'
  user_type?: 'customer' | 'admin'
  page?: number
  page_size?: number
}

export interface GetUsersResponse {
  success: boolean
  data: {
    total: number
    page: number
    page_size: number
    items: UserProfile[]
    statistics: UserStatistics
  }
}

export function getUsers(params?: GetUsersParams): Promise<GetUsersResponse> {
  return get<GetUsersResponse>('/api/v1/m/users', params)
}

/**
 * 获取用户详情（Admin）
 */
export interface GetUserDetailResponse {
  success: boolean
  data: UserProfile
}

export function getUserDetail(userId: number): Promise<GetUserDetailResponse> {
  return get<GetUserDetailResponse>(`/api/v1/m/users/${userId}`)
}

/**
 * 更新用户信息（Admin）
 */
export interface UpdateUserRequest {
  nickname?: string
  email?: string
  phone?: string
  user_type?: 'customer' | 'admin'
}

export interface UpdateUserResponse {
  success: boolean
  data: UserProfile
  message: string
}

export function updateUser(userId: number, data: UpdateUserRequest): Promise<UpdateUserResponse> {
  return put<UpdateUserResponse>(`/api/v1/m/users/${userId}`, data)
}

/**
 * 更新用户状态（Admin）
 */
export interface UpdateUserStatusRequest {
  status: 'active' | 'inactive' | 'locked'
}

export interface UpdateUserStatusResponse {
  success: boolean
  data: UserProfile
  message: string
}

export function updateUserStatus(userId: number, data: UpdateUserStatusRequest): Promise<UpdateUserStatusResponse> {
  return put<UpdateUserStatusResponse>(`/api/v1/m/users/${userId}/status`, data)
}

// 导出所有API
export default {
  // 用户认证
  register,
  login,
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
