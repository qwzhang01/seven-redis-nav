/**
 * 用户相关API类型定义
 * 根据 api.json 的 schema 定义
 */

// ==================== 用户认证相关 ====================

/**
 * 用户注册请求
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  invitation_code: string
  phone?: string
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
  refresh_token: string
  token_type: string
  remark: string
  expires_in: number
  user: UserResponse
}

/**
 * 用户信息响应（根据API定义）
 */
export interface UserResponse {
  id: string  // 服务端返回integer，前端用string接收避免长整型溢出
  username: string
  nickname: string
  email: string
  phone?: string | null
  user_type: 'customer' | 'admin'
  registration_time: string
  // 扩展字段（用于前端展示）
  avatar_url?: string
  status?: 'active' | 'inactive' | 'locked'
  email_verified?: boolean
  phone_verified?: boolean
  last_login_time?: string
  create_time?: string
  update_time?: string
}

/**
 * 更新用户信息请求
 */
export interface UpdateProfileRequest {
  nickname?: string
  email?: string
  phone?: string
}

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 重置密码请求（根据API定义）
 */
export interface ResetPasswordRequest {
  username: string  // API定义是username，不是email
  new_password: string
}

/**
 * 刷新Token请求
 */
export interface RefreshTokenRequest {
  refresh_token: string
}

/**
 * 刷新Token响应
 */
export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// ==================== 交易所相关 ====================

/**
 * 交易所信息（根据API定义）
 */
export interface ExchangeInfo {
  id: string  // 服务端返回integer，前端用string接收
  code: string
  name: string
  region?: string | null
  status: string
}

// ==================== API密钥相关 ====================

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
 * 创建API密钥请求
 */
export interface CreateAPIKeyRequest {
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
export interface UpdateAPIKeyRequest {
  label?: string
  permissions?: ApiKeyPermissions
}

/**
 * API密钥响应（根据API定义）
 */
export interface APIKeyResponse {
  id: string  // 服务端返回integer，前端用string接收
  user_id: string
  exchange_id: string
  label: string
  api_key: string
  secret_key_masked: string
  status: 'pending' | 'approved' | 'rejected' | 'disabled'
  review_reason?: string | null
  approved_by?: string | null
  approved_time?: string | null
  last_used_time?: string | null
  permissions?: ApiKeyPermissions | null
  created_at: string
  updated_at?: string | null
}

/**
 * API密钥列表响应
 */
export interface APIKeyListResponse {
  total: number
  items: APIKeyResponse[]
}

// ==================== 信号跟单相关 ====================

/**
 * 跟单记录
 */
export interface SignalFollow {
  id: string  // 服务端返回integer，前端用string接收
  user_id: string
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
  created_at: string
  updated_at: string
}

/**
 * 创建跟单请求
 */
export interface CreateFollowRequest {
  strategy_id: string
  signal_name: string
  exchange?: string
  follow_amount: number
  follow_ratio?: number
  stop_loss?: number
}

/**
 * 更新跟单配置请求
 */
export interface UpdateFollowConfigRequest {
  follow_amount?: number
  follow_ratio?: number
  stop_loss?: number
}

/**
 * 跟单持仓
 */
export interface SignalFollowPosition {
  id: string
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
 * 跟单交易记录
 */
export interface SignalFollowTrade {
  id: string
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

// ==================== Admin端API密钥审核 ====================

/**
 * Admin端查询API密钥列表参数
 */
export interface GetAdminApiKeysParams {
  review_status?: 'pending' | 'approved' | 'rejected'
  page?: number
  page_size?: number
}

/**
 * Admin端API密钥详情（含用户信息）
 */
export interface AdminAPIKeyResponse {
  id: string  // 服务端返回integer，前端用string接收避免长整型溢出
  user_id: string
  user_name: string
  exchange_id: string
  exchange_name: string
  label: string
  api_key: string
  secret_key_masked: string
  status: 'pending' | 'approved' | 'rejected'  // 与 review_status 使用同一字段
  review_status: 'pending' | 'approved' | 'rejected'
  review_reason?: string | null
  reviewed_by?: string | null
  reviewed_at?: string | null
  permissions?: {
    spot_trading?: boolean
    margin_trading?: boolean
    futures_trading?: boolean
    withdraw?: boolean
  } | null
  created_at: string
  updated_at?: string | null
}

/**
 * Admin端API密钥列表统计
 */
export interface AdminApiKeysStatistics {
  pending_count: number
  approved_count: number
  rejected_count: number
}

/**
 * Admin端API密钥列表响应
 */
export interface GetAdminApiKeysResponse {
  total: number
  page: number
  page_size: number
  items: AdminAPIKeyResponse[]
  statistics?: AdminApiKeysStatistics
}

/**
 * 审核API密钥请求
 */
export interface ReviewAPIKeyRequest {
  result: 'approved' | 'rejected'
  reason?: string
}

/**
 * 审核API密钥响应
 */
export interface ReviewAPIKeyResponse {
  success: boolean
  data: AdminAPIKeyResponse
  message: string
}

// ==================== Admin端用户管理 ====================

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
 * 更新用户请求（Admin）
 */
export interface UpdateUserRequest {
  nickname?: string
  email?: string
  phone?: string
  user_type?: 'customer' | 'admin'
}

/**
 * 更新用户状态请求（Admin）
 */
export interface UpdateUserStatusRequest {
  status: 'active' | 'inactive' | 'locked'
}

// ==================== 用户API扩展类型 ====================

/**
 * UserProfile 类型别名（向后兼容）
 */
export type UserProfile = UserResponse

/**
 * 获取我的跟单列表参数
 */
export interface GetSignalFollowsParams {
  status?: 'following' | 'stopped' | 'paused'
  page?: number
  page_size?: number
}

/**
 * 获取我的跟单列表响应
 */
export interface GetSignalFollowsResponse {
  success: boolean
  data: {
    items: SignalFollow[]
    total: number
    page: number
    pages: number
  }
}

/**
 * 创建跟单响应（用户端）
 */
export interface CreateSignalFollowApiResponse {
  success: boolean
  data: SignalFollow
  message: string
}

/**
 * 获取跟单详情响应
 */
export interface GetSignalFollowDetailResponse {
  success: boolean
  data: SignalFollow
}

/**
 * 更新跟单配置响应（用户端）
 */
export interface UpdateSignalFollowApiResponse {
  success: boolean
  data: SignalFollow
  message: string
}

/**
 * 停止跟单响应（用户端）
 */
export interface StopSignalFollowResponse {
  success: boolean
  data: SignalFollow
  message: string
}

/**
 * 获取跟单持仓列表参数
 */
export interface GetSignalFollowPositionsParams {
  status?: 'open' | 'closed'
  page?: number
  page_size?: number
}

/**
 * 获取跟单持仓列表响应
 */
export interface GetSignalFollowPositionsResponse {
  success: boolean
  data: {
    items: SignalFollowPosition[]
    total: number
    page: number
    pages: number
  }
}

/**
 * 获取跟单交易记录参数
 */
export interface GetSignalFollowTradesParams {
  symbol?: string
  side?: 'buy' | 'sell'
  page?: number
  page_size?: number
}

/**
 * 获取跟单交易记录响应
 */
export interface GetSignalFollowTradesResponse {
  success: boolean
  data: {
    items: SignalFollowTrade[]
    total: number
    page: number
    pages: number
  }
}

/**
 * 获取用户列表参数（Admin）
 */
export interface GetUsersParams {
  search?: string
  status?: 'active' | 'inactive' | 'locked'
  user_type?: 'customer' | 'admin'
  page?: number
  page_size?: number
}

/**
 * 获取用户列表响应（Admin）
 */
export interface GetUsersResponse {
  success: boolean
  data: {
    total: number
    page: number
    page_size: number
    items: UserResponse[]
    statistics: UserStatistics
  }
}

/**
 * 获取用户详情响应（Admin）
 */
export interface GetUserDetailResponse {
  success: boolean
  data: UserResponse
}

/**
 * 更新用户响应（Admin）
 */
export interface UpdateUserResponse {
  success: boolean
  data: UserResponse
  message: string
}

/**
 * 更新用户状态响应（Admin）
 */
export interface UpdateUserStatusResponse {
  success: boolean
  data: UserResponse
  message: string
}

// ==================== 邀请系统相关 ====================

/**
 * 邀请用户信息
 */
export interface InvitedUser {
  id: string
  username: string
  email: string
  phone?: string
  invited_at: string
  level: number
  reward?: number
  status: 'active' | 'inactive' | 'locked'
}

/**
 * 获取邀请用户列表参数
 */
export interface GetInvitedUsersParams {
  page?: number
  page_size?: number
  status?: 'active' | 'inactive' | 'locked'
}

/**
 * 获取邀请用户列表响应
 */
export interface GetInvitedUsersResponse {
    items: InvitedUser[]
    total: number
    page: number
    page_size: number
}

/**
 * 用户邀请统计信息
 */
export interface UserInvitationStats {
  invitation_code: string
  total_invited: number
  total_reward: number
  active_invited: number
  pending_reward: number
}

/**
 * 获取用户邀请统计响应
 */
export interface GetUserInvitationStatsResponse {
  success: boolean
  data: UserInvitationStats
}

/**
 * 邀请人信息
 */
export interface InviterInfo {
  id: string
  username: string
  email: string
  phone?: string
  level?: string
  invitedAt: string
  reward?: number
}

/**
 * 获取邀请人信息响应
 */
export interface GetInviterInfoResponse {
  success: boolean
  data: InviterInfo | null
}

/**
 * 合并邀请统计信息（包含邀请码、统计数据和邀请人信息）
 */
export interface CombinedInvitationStats {
  invitation_code: string
  total_invited_users: number
  active_invited_users: number
  total_reward: number
  inviter_info?: InviterInfo | null
}

/**
 * 获取合并邀请统计信息响应
 */
export interface GetCombinedInvitationStatsResponse {
  success: boolean
  data: CombinedInvitationStats
}