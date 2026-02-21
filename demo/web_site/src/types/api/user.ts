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
  nickname: string
  email: string
  password: string
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
  token_type: string
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
