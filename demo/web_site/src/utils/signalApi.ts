/**
 * 信号管理 API服务
 * 对接量化交易系统的信号管理接口
 *
 * C端信号基础URL: /api/v1/c/signal
 * C端跟单基础URL: /api/v1/c/follows
 * Admin端基础URL: /api/v1/m/signal
 */

import {get, post, put, del} from './request'
import type {
    SignalType,
    SignalStatus,
    NotifyType,
    Signal,
    SignalSubscription,
    SubscribeSignalRequest,
    CreateSignalRequest,
    ApproveSignalRequest,
    // 信号广场
    SignalListParams,
    SignalListResponse,
    // 信号详情
    SignalDetailResponse,
    SignalReturnCurveResponse,
    SignalHistoryResponse,
    SignalProvider,
    SignalMonthlyReturnsResponse,
    SignalDrawdownResponse,
    SignalReviewsResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    ToggleLikeResponse,
    CreateSignalFollowRequest,
    CreateSignalFollowResponse,
    // 跟单列表
    FollowListItem,
    FollowListResponse,
    // 跟单详情
    FollowDetailResponse,
    FollowComparisonResponse,
    FollowTradesResponse,
    FollowEventsResponse,
    FollowPositionsResponse,
    UpdateSignalFollowConfigRequest,
    UpdateSignalFollowConfigResponse,
    StopFollowRequest,
    StopFollowResponse,
    // 策略历史
    StrategySignalHistoryResponse,
    SignalSubscribeResponse,
    SubscriptionListResponse,
    ApproveSignalResponse,
    CreateSignalResponse,
    // K线
    KlineDataPoint,
    SignalKlineParams,
    SignalKlineResponse,
} from '../types'

// 重新导出类型，保持向后兼容
export type {
    SignalListParams,
    SignalListResponse,
    SignalDetailResponse,
    SignalReturnCurveResponse,
    SignalHistoryResponse,
    SignalProvider,
    SignalMonthlyReturnsResponse,
    SignalDrawdownResponse,
    SignalReviewsResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    ToggleLikeResponse,
    FollowListItem,
    FollowListResponse,
    FollowDetailResponse,
    FollowComparisonResponse,
    FollowTradesResponse,
    FollowEventsResponse,
    FollowPositionsResponse,
    StopFollowRequest,
    StopFollowResponse,
    StrategySignalHistoryResponse,
    SubscriptionListResponse,
    ApproveSignalResponse,
    CreateSignalResponse,
    KlineDataPoint,
}

// 向后兼容的类型别名
export type {CreateSignalFollowRequest as CreateFollowRequest}
export type {CreateSignalFollowResponse as CreateFollowResponse}
export type {UpdateSignalFollowConfigRequest as UpdateFollowConfigRequest}
export type {UpdateSignalFollowConfigResponse as UpdateFollowConfigResponse}
export type {SignalSubscribeResponse as SubscribeResponse}
export type {SignalKlineParams as KlineParams}
export type {SignalKlineResponse as KlineResponse}

// 重新导出子类型，保持向后兼容
export type {
    RiskParameters,
    PerformanceMetrics,
    NotificationSettings,
    SignalPosition,
    ReturnCurvePoint,
    SignalHistoryRecord,
    MonthlyReturnItem,
    DrawdownPoint,
    SignalReview,
    FollowPosition,
    TradingPoint,
    ComparisonStats,
    FollowTradeRecord,
    FollowEvent,
    PositionDistributionItem,
    PositionDetail,
} from '../types'

// ==================== C端API — 信号广场 ====================

/**
 * 获取公开信号列表（信号广场）
 */
export function getSignalList(params?: SignalListParams): Promise<SignalListResponse> {
    return get<SignalListResponse>('/api/v1/c/signal/list', params)
}

/**
 * 获取平台列表（筛选项）
 */
export function getSignalPlatforms(): Promise<string[]> {
    return get<string[]>('/api/v1/c/signal/platforms')
}

/**
 * 获取我的信号订阅列表
 */
export function getMySubscriptions(): Promise<SubscriptionListResponse> {
    return get<SubscriptionListResponse>('/api/v1/c/signal/subscriptions')
}

/**
 * 获取策略历史信号
 */
export function getStrategySignalHistory(
    strategyId: string,
    params?: { page?: number; page_size?: number }
): Promise<StrategySignalHistoryResponse> {
    return get<StrategySignalHistoryResponse>(`/api/v1/c/signal/strategy/${strategyId}/history`, params)
}

// ==================== C端API — 信号详情页 ====================

/**
 * 获取信号详情
 */
export function getSignalDetail(signalId: string): Promise<SignalDetailResponse> {
    return get<SignalDetailResponse>(`/api/v1/c/signal/${signalId}`)
}

/**
 * 获取信号收益曲线
 */
export function getSignalReturnCurve(
    signalId: string,
    params?: { period?: '7d' | '30d' | '90d' | '180d' | 'all' }
): Promise<SignalReturnCurveResponse> {
    return get<SignalReturnCurveResponse>(`/api/v1/c/signal/${signalId}/return-curve`, params)
}

/**
 * 获取信号历史记录
 */
export function getSignalHistory(
    signalId: string,
    params?: { page?: number; pageSize?: number }
): Promise<SignalHistoryResponse> {
    return get<SignalHistoryResponse>(`/api/v1/c/signal/${signalId}/history`, params)
}

/**
 * 获取信号提供者信息
 */
export function getSignalProvider(signalId: string): Promise<SignalProvider> {
    return get<SignalProvider>(`/api/v1/c/signal/${signalId}/provider`)
}

/**
 * 获取月度收益分布
 */
export function getSignalMonthlyReturns(
    signalId: string,
    params?: { months?: number }
): Promise<SignalMonthlyReturnsResponse> {
    return get<SignalMonthlyReturnsResponse>(`/api/v1/c/signal/${signalId}/monthly-returns`, params)
}

/**
 * 获取回撤分析数据
 */
export function getSignalDrawdown(signalId: string): Promise<SignalDrawdownResponse> {
    return get<SignalDrawdownResponse>(`/api/v1/c/signal/${signalId}/drawdown`)
}

/**
 * 获取用户评价列表
 */
export function getSignalReviews(
    signalId: string,
    params?: {
        page?: number;
        page_size?: number;
        sort?: 'latest' | 'highest' | 'lowest' | 'most_liked'
    }
): Promise<SignalReviewsResponse> {
    return get<SignalReviewsResponse>(`/api/v1/c/signal/${signalId}/reviews`, params)
}

/**
 * 提交用户评价
 */
export function submitSignalReview(
    signalId: string,
    data: SubmitReviewRequest
): Promise<SubmitReviewResponse> {
    return post<SubmitReviewResponse>(`/api/v1/c/signal/${signalId}/reviews`, data)
}

/**
 * 评价点赞/取消点赞
 */
export function toggleReviewLike(
    signalId: string,
    reviewId: string
): Promise<ToggleLikeResponse> {
    return post<ToggleLikeResponse>(`/api/v1/c/signal/${signalId}/reviews/${reviewId}/like`)
}

/**
 * 创建跟单
 * 对接接口: POST /api/v1/c/follows/
 */
export function createFollow(
    signalId: string,
    data: CreateSignalFollowRequest
): Promise<CreateSignalFollowResponse> {
    return post<CreateSignalFollowResponse>('/api/v1/c/follows/', data)
}

/**
 * 订阅策略信号通知
 */
export function subscribeSignal(data: SubscribeSignalRequest): Promise<SignalSubscribeResponse> {
    return post<SignalSubscribeResponse>('/api/v1/c/signal/subscribe', data)
}

/**
 * 取消信号订阅
 */
export function unsubscribeSignal(subscriptionId: string): Promise<{
    success: boolean;
    message: string
}> {
    return del<{
        success: boolean;
        message: string
    }>(`/api/v1/c/signal/subscriptions/${subscriptionId}`)
}

// ==================== C端API — 跟单管理 ====================

/**
 * 获取用户所有跟单记录
 * 对接接口: GET /api/v1/c/follows/list
 */
export function getFollowList(params?: {
    page?: number
    pageSize?: number
    status?: 'following' | 'stopped' | 'paused'
}): Promise<FollowListResponse> {
    return get<FollowListResponse>('/api/v1/c/follows/list', params)
}

/**
 * 获取跟单详情
 */
export function getFollowDetail(followId: string): Promise<FollowDetailResponse> {
    return get<FollowDetailResponse>(`/api/v1/c/follows/${followId}`)
}

/**
 * 获取跟单收益对比数据
 */
export function getFollowComparison(followId: string): Promise<FollowComparisonResponse> {
    return get<FollowComparisonResponse>(`/api/v1/c/follows/${followId}/comparison`)
}

/**
 * 获取跟单交易记录
 */
export function getFollowTrades(
    followId: string,
    params?: { page?: number; page_size?: number; side?: 'buy' | 'sell' }
): Promise<FollowTradesResponse> {
    return get<FollowTradesResponse>(`/api/v1/c/follows/${followId}/trades`, params)
}

/**
 * 获取跟单事件日志
 */
export function getFollowEvents(
    followId: string,
    params?: {
        page?: number;
        page_size?: number;
        type?: 'trade' | 'risk' | 'success' | 'error' | 'system'
    }
): Promise<FollowEventsResponse> {
    return get<FollowEventsResponse>(`/api/v1/c/follows/${followId}/events`, params)
}

/**
 * 获取跟单仓位分布
 */
export function getFollowPositions(followId: string): Promise<FollowPositionsResponse> {
    return get<FollowPositionsResponse>(`/api/v1/c/follows/${followId}/positions`)
}

/**
 * 更新跟单配置
 */
export function updateFollowConfig(
    followId: string,
    data: UpdateSignalFollowConfigRequest
): Promise<UpdateSignalFollowConfigResponse> {
    return put<UpdateSignalFollowConfigResponse>(`/api/v1/c/follows/${followId}/config`, data)
}

/**
 * 停止跟单
 */
export function stopFollow(
    followId: string,
    data?: StopFollowRequest
): Promise<StopFollowResponse> {
    return post<StopFollowResponse>(`/api/v1/c/follows/${followId}/stop`, data)
}

// ==================== Admin端API ====================

/**
 * 获取待审核信号列表
 */
export function getPendingSignals(params?: {
    page?: number;
    page_size?: number
}): Promise<SignalListResponse> {
    return get<SignalListResponse>('/api/v1/m/signal/pending', params)
}

/**
 * 审核信号（设置是否公开）
 */
export function approveSignal(signalId: string, data: ApproveSignalRequest): Promise<ApproveSignalResponse> {
    return put<ApproveSignalResponse>(`/api/v1/m/signal/${signalId}/approve`, data)
}

/**
 * 手动创建信号记录
 */
export function createSignal(data: CreateSignalRequest): Promise<CreateSignalResponse> {
    return post<CreateSignalResponse>('/api/v1/m/signal/', data)
}

// ==================== K线数据（公共） ====================

/**
 * 获取K线数据
 */
export function getKlineData(params: SignalKlineParams): Promise<SignalKlineResponse[]> {
    let {symbol, interval, limit} = params
    symbol = symbol.replace('/', '-')
    return get<SignalKlineResponse[]>(`/api/v1/c/market/kline/${encodeURIComponent(symbol)}`, {
        timeframe: interval,
        limit
    })
}


// ==================== 默认导出 ====================

export default {
    // C端 — 信号广场
    getSignalList,
    getSignalPlatforms,
    getMySubscriptions,
    getStrategySignalHistory,
    // C端 — 信号详情
    getSignalDetail,
    getSignalReturnCurve,
    getSignalHistory,
    getSignalProvider,
    getSignalMonthlyReturns,
    getSignalDrawdown,
    getSignalReviews,
    submitSignalReview,
    toggleReviewLike,
    createFollow,
    subscribeSignal,
    unsubscribeSignal,
    // C端 — 跟单管理
    getFollowList,
    getFollowDetail,
    getFollowComparison,
    getFollowTrades,
    getFollowEvents,
    getFollowPositions,
    updateFollowConfig,
    stopFollow,
    // K线
    getKlineData,
    // Admin端
    getPendingSignals,
    approveSignal,
    createSignal,
}
