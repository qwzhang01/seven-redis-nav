# API 接口对接分析报告

生成时间：2026-02-21

## 一、概述

本报告对量化交易系统的前端页面代码与后端API接口文档进行了全面对比分析，识别出已对接、未对接、缺失以及错误对接的接口。

### 接口分类说明

- **C端接口**：`/api/v1/c/` 开头，面向普通用户（customer）
- **M端接口**：`/api/v1/m/` 开头，面向管理员（admin/manager）

---

## 二、已对接接口清单

### 2.1 用户管理接口（C端）✅

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/user/register` | POST | `register()` | ✅ 已对接 |
| `/api/v1/c/user/login` | POST | `login()` | ✅ 已对接 |
| `/api/v1/c/user/profile` | PUT | `updateProfile()` | ✅ 已对接 |
| `/api/v1/c/user/password/change` | POST | `changePassword()` | ✅ 已对接 |
| `/api/v1/c/user/password/reset` | POST | `resetPassword()` | ✅ 已对接 |
| `/api/v1/c/user/exchanges/{exchange_id}` | GET | `getExchangeById()` | ✅ 已对接 |
| `/api/v1/c/user/api-keys` | POST | `addApiKey()` | ✅ 已对接 |
| `/api/v1/c/user/api-keys` | GET | `getApiKeys()` | ✅ 已对接 |
| `/api/v1/c/user/api-keys/{api_key_id}` | GET | `getApiKeyById()` | ✅ 已对接 |
| `/api/v1/c/user/api-keys/{api_key_id}` | PUT | `updateApiKey()` | ✅ 已对接 |
| `/api/v1/c/user/api-keys/{api_key_id}` | DELETE | `deleteApiKey()` | ✅ 已对接 |

**对接率：11/11 (100%)**

### 2.2 策略管理接口（M端）⚠️

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/m/strategy/list` | GET | `getStrategies()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/types` | GET | `getStrategyTypes()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/create` | POST | `createStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}` | GET | `getStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}` | PUT | `updateStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}` | DELETE | `deleteStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}/start` | POST | `startStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}/stop` | POST | `stopStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}/pause` | POST | `pauseStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}/resume` | POST | `resumeStrategy()` | ⚠️ **错误对接** |
| `/api/v1/m/strategy/{strategy_id}/signals` | GET | `getStrategySignals()` | ⚠️ **错误对接** |

**对接率：11/11 (100%)，但全部为错误对接（应使用C端接口）**

### 2.3 信号管理接口（C端+M端）✅

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/signal/list` | GET | `getSignalList()` | ✅ 已对接 |
| `/api/v1/c/signal/{signal_id}` | GET | `getSignalDetail()` | ✅ 已对接 |
| `/api/v1/c/signal/strategy/{strategy_id}/history` | GET | `getStrategySignalHistory()` | ✅ 已对接 |
| `/api/v1/c/signal/subscribe` | POST | `subscribeSignal()` | ✅ 已对接 |
| `/api/v1/c/signal/subscriptions` | GET | `getMySubscriptions()` | ✅ 已对接 |
| `/api/v1/c/signal/subscriptions/{subscription_id}` | DELETE | `unsubscribeSignal()` | ✅ 已对接 |
| `/api/v1/m/signal/pending` | GET | `getPendingSignals()` | ✅ 已对接 |
| `/api/v1/m/signal/{signal_id}/approve` | PUT | `approveSignal()` | ✅ 已对接 |
| `/api/v1/m/signal/` | POST | `createSignal()` | ✅ 已对接 |

**对接率：9/9 (100%)**

### 2.4 交易管理接口（C端）❌

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/trading/order` | POST | `placeOrder()` | ❌ **参数不匹配** |
| `/api/v1/c/trading/order/{order_id}` | DELETE | `cancelOrder()` | ✅ 已对接 |
| `/api/v1/c/trading/order/cancel-all` | POST | `cancelAllOrders()` | ✅ 已对接 |
| `/api/v1/c/trading/orders` | GET | `getOrders()` | ✅ 已对接 |
| `/api/v1/c/trading/order/{order_id}` | GET | `getOrderById()` | ✅ 已对接 |
| `/api/v1/c/trading/trades` | GET | `getTrades()` | ✅ 已对接 |
| `/api/v1/c/trading/positions` | GET | `getPositions()` | ✅ 已对接 |
| `/api/v1/c/trading/position/{symbol}` | GET | `getPositionBySymbol()` | ✅ 已对接 |
| `/api/v1/c/trading/account` | GET | `getAccount()` | ✅ 已对接 |
| `/api/v1/c/trading/risk` | GET | `getRisk()` | ✅ 已对接 |

**对接率：9/10 (90%)，1个参数不匹配**

### 2.5 回测管理接口（C端）❌

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/backtest/run` | POST | `runBacktest()` | ❌ **参数不匹配** |
| `/api/v1/c/backtest/list` | GET | `getBacktestList()` | ✅ 已对接 |
| `/api/v1/c/backtest/{backtest_id}` | GET | `getBacktestResult()` | ✅ 已对接 |
| `/api/v1/c/backtest/{backtest_id}/equity` | GET | `getEquityCurve()` | ✅ 已对接 |
| `/api/v1/c/backtest/{backtest_id}/trades` | GET | `getBacktestTrades()` | ✅ 已对接 |
| `/api/v1/c/backtest/{backtest_id}` | DELETE | `deleteBacktest()` | ✅ 已对接 |

**对接率：5/6 (83%)，1个参数不匹配**

### 2.6 排行榜接口（C端+M端）✅

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/leaderboard` | GET | `getLeaderboardOverview()` | ✅ 已对接 |
| `/api/v1/c/leaderboard/strategy` | GET | `getStrategyLeaderboard()` | ✅ 已对接 |
| `/api/v1/c/leaderboard/signal` | GET | `getSignalLeaderboard()` | ✅ 已对接 |
| `/api/v1/m/leaderboard/refresh` | POST | `refreshLeaderboard()` | ✅ 已对接 |

**对接率：4/4 (100%)**

### 2.7 市场数据接口（C端）❌

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/c/market/klines` | GET | `getKlines()` | ❌ **接口路径错误** |
| `/api/v1/c/market/ticker` | GET | `getTicker()` | ❌ **接口路径错误** |
| `/api/v1/c/market/tickers` | GET | `getTickers()` | ❌ **接口路径错误** |
| `/api/v1/c/market/depth` | GET | `getDepth()` | ❌ **接口路径错误** |
| `/api/v1/c/market/trades` | GET | `getTrades()` | ❌ **接口路径错误** |
| `/api/v1/c/market/symbols` | GET | `getSymbols()` | ❌ **接口路径错误** |
| `/api/v1/c/market/exchanges` | GET | `getExchanges()` | ❌ **接口路径错误** |

**对接率：0/7 (0%)，全部路径错误**

### 2.8 统计分析接口（M端）✅

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/m/stats/overview` | GET | `getSystemOverview()` | ✅ 已对接 |
| `/api/v1/m/stats/users` | GET | `getUserStats()` | ✅ 已对接 |
| `/api/v1/m/stats/strategies` | GET | `getStrategyStats()` | ✅ 已对接 |
| `/api/v1/m/stats/trading` | GET | `getTradingStats()` | ✅ 已对接 |
| `/api/v1/m/stats/market` | GET | `getMarketStats()` | ✅ 已对接 |

**对接率：5/5 (100%)**

### 2.9 系统管理接口（M端）✅

| 接口路径 | 方法 | 前端函数 | 状态 |
|---------|------|---------|------|
| `/api/v1/m/system/info` | GET | `getSystemInfo()` | ✅ 已对接 |
| `/api/v1/m/system/config` | GET | `getSystemConfig()` | ✅ 已对接 |
| `/api/v1/m/system/health` | GET | `getSystemHealth()` | ✅ 已对接 |
| `/api/v1/m/system/metrics` | GET | `getSystemMetrics()` | ✅ 已对接 |
| `/api/v1/m/health/` | GET | `healthCheck()` | ✅ 已对接 |
| `/api/v1/m/health/db` | GET | `healthCheckDatabase()` | ✅ 已对接 |
| `/api/v1/m/health/full` | GET | `healthCheckFull()` | ✅ 已对接 |
| `/api/v1/m/health/ready` | GET | `readyCheck()` | ✅ 已对接 |
| `/api/v1/m/health/live` | GET | `liveCheck()` | ✅ 已对接 |
| `/api/v1/m/health/metrics` | GET | `getHealthMetrics()` | ✅ 已对接 |

**对接率：10/10 (100%)**

---

## 三、未对接接口清单

### 3.1 市场数据接口（C端）- 7个接口未对接

根据API文档，以下接口已定义但前端未对接：

| 接口路径 | 方法 | 描述 | 优先级 |
|---------|------|------|--------|
| `/api/v1/c/market/subscribe` | POST | 订阅行情数据 | 🔴 高 |
| `/api/v1/c/market/unsubscribe` | POST | 取消行情订阅 | 🔴 高 |
| `/api/v1/c/market/kline/{symbol}` | GET | 获取K线数据 | 🔴 高 |
| `/api/v1/c/market/tick/{symbol}` | GET | 获取最新Tick数据 | 🔴 高 |
| `/api/v1/c/market/depth/{symbol}` | GET | 获取市场深度数据 | 🟡 中 |
| `/api/v1/c/market/symbols` | GET | 获取已订阅的交易对列表 | 🟡 中 |
| `/api/v1/c/market/stats` | GET | 获取行情服务统计信息 | 🟢 低 |

### 3.2 市场数据管理接口（M端）- 13个接口未对接

| 接口路径 | 方法 | 描述 | 优先级 |
|---------|------|------|--------|
| `/api/v1/m/market/subscriptions` | POST | 创建订阅配置 | 🟡 中 |
| `/api/v1/m/market/subscriptions` | GET | 获取订阅列表 | 🟡 中 |
| `/api/v1/m/market/subscriptions/statistics` | GET | 获取订阅统计信息 | 🟢 低 |
| `/api/v1/m/market/subscriptions/{id}` | GET | 获取订阅详情 | 🟡 中 |
| `/api/v1/m/market/subscriptions/{id}` | PUT | 更新订阅配置 | 🟡 中 |
| `/api/v1/m/market/subscriptions/{id}` | DELETE | 删除订阅 | 🟡 中 |
| `/api/v1/m/market/subscriptions/{id}/start` | POST | 启动订阅 | 🟡 中 |
| `/api/v1/m/market/subscriptions/{id}/pause` | POST | 暂停订阅 | 🟡 中 |
| `/api/v1/m/market/subscriptions/{id}/stop` | POST | 停止订阅 | 🟡 中 |
| `/api/v1/m/market/sync-tasks` | POST | 创建同步任务 | 🟢 低 |
| `/api/v1/m/market/sync-tasks` | GET | 获取同步任务列表 | 🟢 低 |
| `/api/v1/m/market/sync-tasks/{id}` | GET | 获取同步任务详情 | 🟢 低 |
| `/api/v1/m/market/sync-tasks/{id}/cancel` | POST | 取消同步任务 | 🟢 低 |

**未对接接口总计：20个**

---

## 四、错误对接分析

### 4.1 策略管理接口 - C端/M端混淆 ⚠️

**问题描述**：
前端代码中策略管理相关接口全部使用了 **M端（管理员）接口** `/api/v1/m/strategy/*`，但根据业务逻辑，普通用户也需要管理自己的策略，应该使用 **C端接口**。

**影响范围**：
- `strategyApi.ts` 中的所有11个接口

**错误示例**：
```typescript
// ❌ 错误：使用了M端接口
export function getStrategies(params?: StrategyListParams): Promise<StrategyListResponse> {
  return get<StrategyListResponse>('/api/v1/m/strategy/list', params)
}

// ✅ 应该：根据用户角色使用对应接口
// 普通用户应使用 /api/v1/c/strategy/list
// 管理员使用 /api/v1/m/strategy/list
```

**修复建议**：
1. 后端需要补充C端策略管理接口（如果尚未实现）
2. 前端需要根据用户角色（customer/admin）动态选择接口路径
3. 或者将策略管理统一为C端接口，M端通过权限控制访问所有策略

### 4.2 市场数据接口 - 路径错误 ❌

**问题描述**：
前端代码中市场数据接口路径与API文档不匹配。

**错误对比**：

| 前端代码路径 | API文档路径 | 状态 |
|------------|-----------|------|
| `/api/v1/c/market/klines` | `/api/v1/c/market/kline/{symbol}` | ❌ 路径错误 |
| `/api/v1/c/market/ticker` | `/api/v1/c/market/tick/{symbol}` | ❌ 路径错误 |
| `/api/v1/c/market/tickers` | 文档中无此接口 | ❌ 接口不存在 |
| `/api/v1/c/market/depth` | `/api/v1/c/market/depth/{symbol}` | ❌ 缺少路径参数 |
| `/api/v1/c/market/trades` | 文档中无此接口 | ❌ 接口不存在 |
| `/api/v1/c/market/symbols` | `/api/v1/c/market/symbols` | ⚠️ 参数不匹配 |
| `/api/v1/c/market/exchanges` | 文档中无此接口 | ❌ 接口不存在 |

**修复建议**：
需要修改 `marketApi.ts` 中的所有接口路径，使其与API文档一致。

### 4.3 交易接口 - 参数不匹配 ❌

**问题描述**：
`placeOrder()` 函数的请求参数与API文档不匹配。

**前端参数**：
```typescript
export interface PlaceOrderRequest {
  exchange_id: string      // ❌ 文档中无此参数
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stop_price?: number
  time_in_force?: 'GTC' | 'IOC' | 'FOK'
  client_order_id?: string
  strategy_id?: string
}
```

**API文档参数**：
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "order_type": "limit",    // ⚠️ 字段名不同
  "quantity": 0.01,
  "price": 50000.0,
  "strategy_id": ""
}
```

**差异**：
1. 前端多了 `exchange_id` 参数（文档中无）
2. 字段名不一致：`type` vs `order_type`
3. 前端多了 `stop_price`、`time_in_force`、`client_order_id` 参数

### 4.4 回测接口 - 参数不匹配 ❌

**问题描述**：
`runBacktest()` 函数的请求参数与API文档不匹配。

**前端参数**：
```typescript
export interface RunBacktestRequest {
  strategy_id: string       // ❌ 文档中无此参数
  exchange_id: string       // ❌ 文档中无此参数
  symbol: string
  start_time: string
  end_time: string
  initial_capital: number
  parameters?: Record<string, any>
  commission_rate?: number
  slippage_rate?: number
}
```

**API文档参数**：
```json
{
  "strategy_type": "ma_cross",  // ⚠️ 前端缺少此参数
  "symbol": "BTCUSDT",
  "timeframe": "1h",            // ⚠️ 前端缺少此参数
  "start_time": "2025-01-01T00:00:00Z",
  "end_time": "2026-01-01T00:00:00Z",
  "initial_capital": 1000000.0,
  "commission_rate": 0.0004,
  "slippage_rate": 0.0001,
  "params": {}                  // ⚠️ 字段名不同
}
```

**差异**：
1. 前端使用 `strategy_id`，文档使用 `strategy_type`
2. 前端多了 `exchange_id` 参数
3. 前端缺少 `timeframe` 参数
4. 参数名不一致：`parameters` vs `params`

---

## 五、缺失接口分析

### 5.1 后端已定义但前端未实现的接口

根据API文档，以下接口后端已实现但前端未对接：

#### 市场数据模块（20个接口）
- C端：7个接口（订阅、K线、Tick、深度等）
- M端：13个接口（订阅配置管理、同步任务管理）

**业务影响**：
- 无法实时订阅行情数据
- 无法查看K线图表
- 无法查看市场深度
- 管理员无法管理数据订阅

### 5.2 前端实现但后端可能缺失的接口

根据前端代码，以下接口前端已实现但API文档中未找到：

| 前端接口 | 描述 | 状态 |
|---------|------|------|
| `/api/v1/c/market/tickers` | 获取所有交易对行情 | ❓ 文档中无 |
| `/api/v1/c/market/trades` | 获取最近成交 | ❓ 文档中无 |
| `/api/v1/c/market/exchanges` | 获取交易所列表 | ❓ 文档中无 |

**说明**：这些接口可能是：
1. 后端已实现但文档未更新
2. 前端预留接口但后端未实现
3. 接口路径或命名发生了变更

---

## 六、修复方案

### 6.1 高优先级修复（影响核心功能）

#### 1. 修复策略管理接口的C/M端混淆

**方案A：后端补充C端接口（推荐）**
```
后端需要实现：
- POST /api/v1/c/strategy/create
- GET /api/v1/c/strategy/list
- GET /api/v1/c/strategy/{strategy_id}
- PUT /api/v1/c/strategy/{strategy_id}
- DELETE /api/v1/c/strategy/{strategy_id}
- POST /api/v1/c/strategy/{strategy_id}/start
- POST /api/v1/c/strategy/{strategy_id}/stop
- POST /api/v1/c/strategy/{strategy_id}/pause
- POST /api/v1/c/strategy/{strategy_id}/resume
- GET /api/v1/c/strategy/{strategy_id}/signals
- GET /api/v1/c/strategy/types
```

**方案B：前端根据角色动态选择接口**
```typescript
// 在 strategyApi.ts 中添加角色判断
import { useAuthStore } from '@/stores/auth'

function getApiPrefix(): string {
  const authStore = useAuthStore()
  return authStore.user?.user_type === 'admin' ? '/api/v1/m' : '/api/v1/c'
}

export function getStrategies(params?: StrategyListParams): Promise<StrategyListResponse> {
  return get<StrategyListResponse>(`${getApiPrefix()}/strategy/list`, params)
}
```

#### 2. 修复市场数据接口路径

需要修改 `marketApi.ts` 文件：

```typescript
// ❌ 错误
export function getKlines(params: KlineParams): Promise<KlineResponse> {
  return get<KlineResponse>('/api/v1/c/market/klines', params)
}

// ✅ 正确
export function getKlines(symbol: string, params: Omit<KlineParams, 'symbol'>): Promise<KlineResponse> {
  return get<KlineResponse>(`/api/v1/c/market/kline/${symbol}`, params)
}
```

#### 3. 修复交易下单接口参数

需要修改 `tradingApi.ts` 文件：

```typescript
// 修改请求接口
export interface PlaceOrderRequest {
  symbol: string
  side: OrderSide
  order_type: OrderType  // 改名
  quantity: number
  price?: number
  strategy_id?: string
  // 移除 exchange_id, stop_price, time_in_force, client_order_id
}
```

#### 4. 修复回测接口参数

需要修改 `backtestApi.ts` 文件：

```typescript
// 修改请求接口
export interface RunBacktestRequest {
  strategy_type: string  // 改名
  symbol: string
  timeframe?: string     // 新增
  start_time: string
  end_time: string
  initial_capital: number
  params?: Record<string, any>  // 改名
  commission_rate?: number
  slippage_rate?: number
  // 移除 strategy_id, exchange_id
}
```

### 6.2 中优先级修复（完善功能）

#### 5. 补充市场数据C端接口

在 `marketApi.ts` 中添加：

```typescript
/**
 * 订阅行情数据
 */
export function subscribeMarket(data: {
  symbols: string[]
  exchange?: string
  market_type?: string
}): Promise<{ success: boolean; message: string; symbols: string[] }> {
  return post('/api/v1/c/market/subscribe', data)
}

/**
 * 取消行情订阅
 */
export function unsubscribeMarket(data: {
  symbols: string[]
  exchange?: string
  market_type?: string
}): Promise<{ success: boolean; message: string; symbols: string[] }> {
  return post('/api/v1/c/market/unsubscribe', data)
}

/**
 * 获取已订阅的交易对列表
 */
export function getSubscribedSymbols(params?: {
  exchange?: string
  market_type?: string
}): Promise<{ exchange: string; market_type: string; symbols: string[] }> {
  return get('/api/v1/c/market/symbols', params)
}

/**
 * 获取行情服务统计信息
 */
export function getMarketStats(): Promise<Record<string, any>> {
  return get('/api/v1/c/market/stats')
}
```

### 6.3 低优先级修复（管理功能）

#### 6. 补充市场数据M端管理接口

创建新文件 `src/utils/marketAdminApi.ts`：

```typescript
/**
 * 市场数据管理 API服务（管理员端）
 */

import { get, post, put, del } from './request'

// 订阅配置管理
export function createSubscription(data: any): Promise<any> {
  return post('/api/v1/m/market/subscriptions', data)
}

export function getSubscriptions(params?: any): Promise<any> {
  return get('/api/v1/m/market/subscriptions', params)
}

export function getSubscriptionStats(): Promise<any> {
  return get('/api/v1/m/market/subscriptions/statistics')
}

export function getSubscriptionById(id: string): Promise<any> {
  return get(`/api/v1/m/market/subscriptions/${id}`)
}

export function updateSubscription(id: string, data: any): Promise<any> {
  return put(`/api/v1/m/market/subscriptions/${id}`, data)
}

export function deleteSubscription(id: string): Promise<any> {
  return del(`/api/v1/m/market/subscriptions/${id}`)
}

export function startSubscription(id: string): Promise<any> {
  return post(`/api/v1/m/market/subscriptions/${id}/start`)
}

export function pauseSubscription(id: string): Promise<any> {
  return post(`/api/v1/m/market/subscriptions/${id}/pause`)
}

export function stopSubscription(id: string): Promise<any> {
  return post(`/api/v1/m/market/subscriptions/${id}/stop`)
}

// 同步任务管理
export function createSyncTask(data: any): Promise<any> {
  return post('/api/v1/m/market/sync-tasks', data)
}

export function getSyncTasks(params?: any): Promise<any> {
  return get('/api/v1/m/market/sync-tasks', params)
}

export function getSyncTaskById(id: string): Promise<any> {
  return get(`/api/v1/m/market/sync-tasks/${id}`)
}

export function cancelSyncTask(id: string): Promise<any> {
  return post(`/api/v1/m/market/sync-tasks/${id}/cancel`)
}
```

---

## 七、总结

### 7.1 整体对接情况

| 模块 | 已对接 | 未对接 | 错误对接 | 对接率 |
|------|--------|--------|----------|--------|
| 用户管理（C端） | 11 | 0 | 0 | 100% |
| 策略管理（M端） | 11 | 0 | 11 | 0%（全部错误） |
| 信号管理（C+M端） | 9 | 0 | 0 | 100% |
| 交易管理（C端） | 9 | 0 | 1 | 90% |
| 回测管理（C端） | 5 | 0 | 1 | 83% |
| 排行榜（C+M端） | 4 | 0 | 0 | 100% |
| 市场数据（C端） | 0 | 7 | 7 | 0% |
| 市场数据（M端） | 0 | 13 | 0 | 0% |
| 统计分析（M端） | 5 | 0 | 0 | 100% |
| 系统管理（M端） | 10 | 0 | 0 | 100% |
| **总计** | **64** | **20** | **20** | **76%** |

### 7.2 关键问题

1. **策略管理接口全部错误对接**：使用了M端接口，应使用C端接口或根据角色动态选择
2. **市场数据接口完全未对接**：7个C端接口和13个M端接口均未正确对接
3. **交易和回测接口参数不匹配**：需要调整参数结构以匹配API文档

### 7.3 修复优先级

#### 🔴 高优先级（影响核心功能）
1. 修复策略管理接口的C/M端混淆
2. 修复市场数据C端接口（K线、Tick、深度）
3. 修复交易下单接口参数
4. 修复回测接口参数

#### 🟡 中优先级（完善功能）
5. 补充市场数据订阅接口
6. 补充市场数据管理接口（M端）

#### 🟢 低优先级（优化体验）
7. 完善错误处理和类型定义
8. 添加接口文档注释

### 7.4 后续建议

1. **建立接口对接规范**：
   - 明确C端和M端接口的使用场景
   - 统一接口命名和参数格式
   - 建立接口变更通知机制

2. **完善API文档**：
   - 补充缺失的接口文档
   - 更新过时的接口说明
   - 添加接口使用示例

3. **加强测试**：
   - 编写接口集成测试
   - 添加参数校验测试
   - 建立自动化测试流程

4. **代码审查**：
   - 在代码审查中检查接口对接正确性
   - 确保新增接口及时更新文档
   - 定期进行接口对接审计

---

**报告生成时间**：2026-02-21  
**分析范围**：前端代码 `src/utils/*Api.ts` + API文档 `doc/api/*.md`  
**分析工具**：人工对比分析
