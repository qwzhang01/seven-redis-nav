# API接口文档与页面实现对比分析

> 生成时间：2026-02-20  
> 项目：Seven Quant 量化交易系统 Web 前端

---

## 📋 执行摘要

本文档对比分析了 `doc/api/` 目录下的接口文档与前端页面实际实现情况，识别出已实现、待实现和缺失的功能模块。

### 关键发现

- ✅ **接口文档完整性**：6个核心模块的API文档齐全
- ⚠️ **实现进度**：仅用户模块完成API对接，其他模块均使用Mock数据
- 🔧 **待补充工作**：需创建5个API封装文件，对接约60+个接口

---

## 📚 接口文档清单

### 1. 用户管理 API (user_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 18.14 KB  
**接口数量**: 11个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/c/user/register` | POST | 用户注册 | ✅ 已实现 |
| `/api/v1/c/user/login` | POST | 用户登录 | ✅ 已实现 |
| `/api/v1/c/user/profile` | GET | 获取用户信息 | ✅ 已实现 |
| `/api/v1/c/user/profile` | PUT | 更新用户信息 | ✅ 已实现 |
| `/api/v1/c/user/password/change` | POST | 修改密码 | ✅ 已实现 |
| `/api/v1/c/user/password/reset` | POST | 重置密码 | ✅ 已实现 |
| `/api/v1/c/user/exchanges/{id}` | GET | 获取交易所详情 | ✅ 已实现 |
| `/api/v1/c/user/api-keys` | POST | 添加API密钥 | ✅ 已实现 |
| `/api/v1/c/user/api-keys` | GET | 获取API密钥列表 | ✅ 已实现 |
| `/api/v1/c/user/api-keys/{id}` | GET | 获取API密钥详情 | ✅ 已实现 |
| `/api/v1/c/user/api-keys/{id}` | PUT | 更新API密钥 | ✅ 已实现 |
| `/api/v1/c/user/api-keys/{id}` | DELETE | 删除API密钥 | ✅ 已实现 |

**实现文件**: `src/utils/userApi.ts`

---

### 2. 市场数据 API (market_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 23.40 KB  
**接口数量**: 10个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/c/market/klines` | GET | 获取K线数据 | ❌ 未实现 |
| `/api/v1/c/market/ticker` | GET | 获取最新行情 | ❌ 未实现 |
| `/api/v1/c/market/tickers` | GET | 获取所有交易对行情 | ❌ 未实现 |
| `/api/v1/c/market/depth` | GET | 获取市场深度 | ❌ 未实现 |
| `/api/v1/c/market/trades` | GET | 获取最近成交 | ❌ 未实现 |
| `/api/v1/c/market/symbols` | GET | 获取交易对列表 | ❌ 未实现 |
| `/api/v1/c/market/exchanges` | GET | 获取交易所列表 | ❌ 未实现 |
| `/api/v1/c/market/ws/kline` | WebSocket | K线数据推送 | ❌ 未实现 |
| `/api/v1/c/market/ws/ticker` | WebSocket | 行情推送 | ❌ 未实现 |
| `/api/v1/c/market/ws/depth` | WebSocket | 深度推送 | ❌ 未实现 |

**需要创建**: `src/utils/marketApi.ts`  
**相关页面**: 
- `TradingPage.vue` - 交易盘面（需要实时行情、K线、深度数据）
- `HomePage.vue` - 首页（需要行情数据）

---

### 3. 回测 API (backtest_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 11.57 KB  
**接口数量**: 6个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/c/backtest/run` | POST | 运行策略回测 | ❌ 未实现 |
| `/api/v1/c/backtest/list` | GET | 获取回测历史列表 | ❌ 未实现 |
| `/api/v1/c/backtest/{id}` | GET | 获取回测结果 | ❌ 未实现 |
| `/api/v1/c/backtest/{id}/equity` | GET | 获取回测权益曲线 | ❌ 未实现 |
| `/api/v1/c/backtest/{id}/trades` | GET | 获取回测交易记录 | ❌ 未实现 |
| `/api/v1/c/backtest/{id}` | DELETE | 删除回测记录 | ❌ 未实现 |

**需要创建**: `src/utils/backtestApi.ts`  
**相关页面**: 
- `StrategyDetail.vue` - 策略详情（需要回测功能）
- `AdminStrategies.vue` - 策略管理（需要查看回测历史）

---

### 4. 策略管理 API (strategy_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 10.36 KB  
**接口数量**: 11个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/m/strategy/list` | GET | 获取策略列表 | ❌ 未实现 |
| `/api/v1/m/strategy/types` | GET | 获取可用策略类型 | ❌ 未实现 |
| `/api/v1/m/strategy/create` | POST | 创建策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}` | GET | 获取策略详情 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}` | PUT | 更新策略参数 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}` | DELETE | 删除策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}/start` | POST | 启动策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}/stop` | POST | 停止策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}/pause` | POST | 暂停策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}/resume` | POST | 恢复策略 | ❌ 未实现 |
| `/api/v1/m/strategy/{id}/signals` | GET | 获取策略信号历史 | ❌ 未实现 |

**需要创建**: `src/utils/strategyApi.ts`  
**相关页面**: 
- `StrategyList.vue` - 策略列表
- `StrategyDetail.vue` - 策略详情
- `RunningStrategiesPage.vue` - 策略实盘监控
- `RunningStrategyDetail.vue` - 策略运行详情
- `AdminStrategies.vue` - 策略管理

---

### 5. 交易管理 API (trading_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 12.35 KB  
**接口数量**: 10个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/c/trading/order` | POST | 下单 | ❌ 未实现 |
| `/api/v1/c/trading/order/{id}` | DELETE | 取消订单 | ❌ 未实现 |
| `/api/v1/c/trading/order/cancel-all` | POST | 取消所有订单 | ❌ 未实现 |
| `/api/v1/c/trading/orders` | GET | 获取订单列表 | ❌ 未实现 |
| `/api/v1/c/trading/order/{id}` | GET | 获取订单详情 | ❌ 未实现 |
| `/api/v1/c/trading/trades` | GET | 获取成交记录 | ❌ 未实现 |
| `/api/v1/c/trading/positions` | GET | 获取持仓列表 | ❌ 未实现 |
| `/api/v1/c/trading/position/{symbol}` | GET | 获取单个持仓详情 | ❌ 未实现 |
| `/api/v1/c/trading/account` | GET | 获取账户信息 | ❌ 未实现 |
| `/api/v1/c/trading/risk` | GET | 获取风险信息 | ❌ 未实现 |

**需要创建**: `src/utils/tradingApi.ts`  
**相关页面**: 
- `TradingPage.vue` - 交易盘面（需要下单、订单、持仓、账户信息）
- `RunningStrategiesPage.vue` - 策略实盘监控（需要持仓、订单信息）
- `RunningStrategyDetail.vue` - 策略运行详情（需要交易记录）
- `UserCenter.vue` - 用户中心（需要账户信息）

---

### 6. 系统管理 API (system_api.md)
**文档状态**: ✅ 完整  
**文件大小**: 11.82 KB  
**接口数量**: 10个

| 接口路径 | 方法 | 功能描述 | 实现状态 |
|---------|------|---------|---------| 
| `/api/v1/m/system/info` | GET | 获取系统基本信息 | ❌ 未实现 |
| `/api/v1/m/system/config` | GET | 获取系统配置信息 | ❌ 未实现 |
| `/api/v1/m/system/health` | GET | 系统组件健康检查 | ❌ 未实现 |
| `/api/v1/m/system/metrics` | GET | 获取系统性能指标 | ❌ 未实现 |
| `/api/v1/m/health/` | GET | 基础健康检查 | ❌ 未实现 |
| `/api/v1/m/health/db` | GET | 数据库健康检查 | ❌ 未实现 |
| `/api/v1/m/health/full` | GET | 完整健康检查 | ❌ 未实现 |
| `/api/v1/m/health/ready` | GET | 就绪检查 | ❌ 未实现 |
| `/api/v1/m/health/live` | GET | 存活检查 | ❌ 未实现 |
| `/api/v1/m/health/metrics` | GET | 系统资源指标 | ❌ 未实现 |

**需要创建**: `src/utils/systemApi.ts`  
**相关页面**: 
- `AdminDashboard.vue` - 管理概览（需要系统信息、健康状态）
- `AdminLogs.vue` - 风控与日志（需要系统指标）

---

## 🎯 页面功能与API需求对比

### 前台页面

#### 1. 首页 (HomePage.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ✅ 用户信息 - `userApi.getUserProfile()`
- ❌ 市场行情 - `marketApi.getTickers()`
- ❌ 热门策略 - `strategyApi.getStrategies({ sort: 'popular' })`
- ❌ 热门信号 - 需要信号API（文档中未找到）

#### 2. 交易盘面 (TradingPage.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ K线数据 - `marketApi.getKlines()`
- ❌ 实时行情 - `marketApi.getTicker()` / WebSocket
- ❌ 市场深度 - `marketApi.getDepth()` / WebSocket
- ❌ 最近成交 - `marketApi.getTrades()`
- ❌ 下单 - `tradingApi.placeOrder()`
- ❌ 订单列表 - `tradingApi.getOrders()`
- ❌ 持仓信息 - `tradingApi.getPositions()`
- ❌ 账户信息 - `tradingApi.getAccount()`

#### 3. 策略列表 (StrategyList.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 策略列表 - `strategyApi.getStrategies()`
- ❌ 策略类型 - `strategyApi.getStrategyTypes()`

#### 4. 策略详情 (StrategyDetail.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 策略详情 - `strategyApi.getStrategy(id)`
- ❌ 运行回测 - `backtestApi.runBacktest()`
- ❌ 回测结果 - `backtestApi.getBacktestResult(id)`
- ❌ 权益曲线 - `backtestApi.getEquityCurve(id)`
- ❌ 创建策略实例 - `strategyApi.createStrategy()`

#### 5. 策略实盘监控 (RunningStrategiesPage.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 运行中策略列表 - `strategyApi.getStrategies({ status: 'running' })`
- ❌ 持仓信息 - `tradingApi.getPositions()`
- ❌ 订单信息 - `tradingApi.getOrders()`
- ❌ 策略控制 - `strategyApi.start/stop/pause/resume()`

#### 6. 策略运行详情 (RunningStrategyDetail.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 策略详情 - `strategyApi.getStrategy(id)`
- ❌ 策略信号历史 - `strategyApi.getSignals(id)`
- ❌ 交易记录 - `tradingApi.getTrades({ strategy_id: id })`
- ❌ 持仓信息 - `tradingApi.getPositions()`
- ❌ 策略控制 - `strategyApi.start/stop/pause/resume()`

#### 7. 信号广场 (SignalList.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 信号列表 - **缺少信号API文档**

#### 8. 信号详情 (SignalDetail.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 信号详情 - **缺少信号API文档**
- ❌ 信号历史 - **缺少信号API文档**

#### 9. 收益排行榜 (LeaderboardPage.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 排行榜数据 - **缺少排行榜API文档**

#### 10. 用户中心 (UserCenter.vue)
**当前状态**: 部分使用真实API  
**需要的API**:
- ✅ 用户信息 - `userApi.getUserProfile()`
- ✅ 更新信息 - `userApi.updateProfile()`
- ✅ 修改密码 - `userApi.changePassword()`
- ✅ API密钥管理 - `userApi.getApiKeys/addApiKey/updateApiKey/deleteApiKey()`
- ❌ 账户资产 - `tradingApi.getAccount()`
- ❌ 我的策略 - `strategyApi.getStrategies({ user_id: 'me' })`

### 后台管理页面

#### 11. 管理概览 (AdminDashboard.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 系统信息 - `systemApi.getSystemInfo()`
- ❌ 系统健康 - `systemApi.getHealth()`
- ❌ 系统指标 - `systemApi.getMetrics()`
- ❌ 用户统计 - **缺少统计API文档**
- ❌ 策略统计 - **缺少统计API文档**

#### 12. 策略管理 (AdminStrategies.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 所有策略列表 - `strategyApi.getStrategies()`
- ❌ 策略审核 - **缺少审核API文档**
- ❌ 策略上下架 - **缺少管理API文档**

#### 13. 信号接入 (AdminSignals.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 信号列表 - **缺少信号API文档**
- ❌ 信号审核 - **缺少审核API文档**

#### 14. API密钥审核 (AdminApiKeys.vue)
**当前状态**: 部分使用真实API  
**需要的API**:
- ✅ 密钥列表 - `userApi.getApiKeys()`
- ✅ 审核密钥 - `userApi.updateApiKey()`
- ❌ 所有用户密钥 - **需要管理员版本的API**

#### 15. 风控与日志 (AdminLogs.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 系统日志 - **缺少日志API文档**
- ❌ 风控记录 - **缺少风控API文档**
- ❌ 告警信息 - **缺少告警API文档**

#### 16. 实时数据订阅 (AdminDataSubscription.vue)
**当前状态**: 使用Mock数据  
**需要的API**:
- ❌ 订阅管理 - **缺少订阅API文档**
- ❌ 数据源配置 - **缺少配置API文档**

---

## 🔍 接口文档缺失分析

### 已识别但缺少文档的功能模块

#### 1. 信号管理 API
**优先级**: 🔴 高  
**影响页面**: 
- SignalList.vue
- SignalDetail.vue
- AdminSignals.vue
- HomePage.vue

**建议接口**:
```
GET  /api/v1/c/signal/list          - 获取信号列表
GET  /api/v1/c/signal/{id}          - 获取信号详情
POST /api/v1/c/signal/subscribe     - 订阅信号
GET  /api/v1/c/signal/{id}/history  - 获取信号历史
GET  /api/v1/m/signal/pending       - 获取待审核信号（管理员）
PUT  /api/v1/m/signal/{id}/approve  - 审核信号（管理员）
```

#### 2. 排行榜 API
**优先级**: 🟡 中  
**影响页面**: 
- LeaderboardPage.vue
- AdminLeaderboard.vue

**建议接口**:
```
GET  /api/v1/c/leaderboard          - 获取排行榜
GET  /api/v1/c/leaderboard/strategy - 策略排行
GET  /api/v1/c/leaderboard/signal   - 信号排行
PUT  /api/v1/m/leaderboard/config   - 配置排行榜规则（管理员）
```

#### 3. 统计分析 API
**优先级**: 🟡 中  
**影响页面**: 
- AdminDashboard.vue

**建议接口**:
```
GET  /api/v1/m/stats/overview       - 系统概览统计
GET  /api/v1/m/stats/users          - 用户统计
GET  /api/v1/m/stats/strategies     - 策略统计
GET  /api/v1/m/stats/trading        - 交易统计
```

#### 4. 日志与审计 API
**优先级**: 🟡 中  
**影响页面**: 
- AdminLogs.vue

**建议接口**:
```
GET  /api/v1/m/logs/system          - 系统日志
GET  /api/v1/m/logs/trading         - 交易日志
GET  /api/v1/m/logs/risk            - 风控日志
GET  /api/v1/m/logs/audit           - 审计日志
```

#### 5. 数据订阅管理 API
**优先级**: 🟢 低  
**影响页面**: 
- AdminDataSubscription.vue

**建议接口**:
```
GET  /api/v1/m/subscription/list    - 订阅列表
POST /api/v1/m/subscription/create  - 创建订阅
PUT  /api/v1/m/subscription/{id}    - 更新订阅
DELETE /api/v1/m/subscription/{id}  - 删除订阅
```

---

## 📊 实现进度统计

### 接口实现进度

| 模块 | 文档接口数 | 已实现 | 未实现 | 完成率 |
|------|-----------|--------|--------|--------|
| 用户管理 | 11 | 11 | 0 | 100% |
| 市场数据 | 10 | 0 | 10 | 0% |
| 回测管理 | 6 | 0 | 6 | 0% |
| 策略管理 | 11 | 0 | 11 | 0% |
| 交易管理 | 10 | 0 | 10 | 0% |
| 系统管理 | 10 | 0 | 10 | 0% |
| **总计** | **58** | **11** | **47** | **19%** |

### 页面实现进度

| 页面类型 | 总数 | 完全Mock | 部分实现 | 完全实现 |
|---------|------|---------|---------|---------| 
| 前台页面 | 10 | 8 | 1 | 1 |
| 后台页面 | 6 | 5 | 1 | 0 |
| **总计** | **16** | **13** | **2** | **1** |

---

## 🚀 实施建议

### 第一阶段：核心交易功能（优先级：🔴 高）

**目标**: 实现基本的交易和策略功能

1. **创建 `src/utils/tradingApi.ts`**
   - 实现下单、撤单、查询订单
   - 实现持仓查询、账户信息
   - 对接 `TradingPage.vue`

2. **创建 `src/utils/strategyApi.ts`**
   - 实现策略列表、详情查询
   - 实现策略创建、启动、停止
   - 对接 `StrategyList.vue`、`StrategyDetail.vue`、`RunningStrategiesPage.vue`

3. **创建 `src/utils/marketApi.ts`**
   - 实现K线、行情、深度数据查询
   - 实现WebSocket连接（实时数据推送）
   - 对接 `TradingPage.vue`

**预计工时**: 5-7个工作日

### 第二阶段：回测与分析功能（优先级：🟡 中）

**目标**: 完善策略回测和数据分析

1. **创建 `src/utils/backtestApi.ts`**
   - 实现回测运行、结果查询
   - 实现权益曲线、交易记录查询
   - 对接 `StrategyDetail.vue`

2. **补充信号管理API文档**
   - 编写 `doc/api/signal_api.md`
   - 创建 `src/utils/signalApi.ts`
   - 对接 `SignalList.vue`、`SignalDetail.vue`

**预计工时**: 3-4个工作日

### 第三阶段：系统管理功能（优先级：🟡 中）

**目标**: 完善后台管理功能

1. **创建 `src/utils/systemApi.ts`**
   - 实现系统信息、健康检查
   - 实现性能指标查询
   - 对接 `AdminDashboard.vue`

2. **补充统计分析API文档**
   - 编写 `doc/api/stats_api.md`
   - 创建 `src/utils/statsApi.ts`
   - 对接 `AdminDashboard.vue`

3. **补充日志审计API文档**
   - 编写 `doc/api/log_api.md`
   - 创建 `src/utils/logApi.ts`
   - 对接 `AdminLogs.vue`

**预计工时**: 4-5个工作日

### 第四阶段：增强功能（优先级：🟢 低）

**目标**: 完善辅助功能

1. **补充排行榜API文档**
   - 编写 `doc/api/leaderboard_api.md`
   - 创建 `src/utils/leaderboardApi.ts`
   - 对接 `LeaderboardPage.vue`

2. **补充数据订阅API文档**
   - 编写 `doc/api/subscription_api.md`
   - 创建 `src/utils/subscriptionApi.ts`
   - 对接 `AdminDataSubscription.vue`

**预计工时**: 2-3个工作日

---

## 📝 代码规范建议

### API封装文件结构

参考 `userApi.ts` 的良好实践：

```typescript
/**
 * [模块名称] API服务
 * 对接量化交易系统的[模块]接口
 */

import { get, post, put, del } from './request'

// ==================== 类型定义 ====================

export interface [RequestType] {
  // 请求参数定义
}

export interface [ResponseType] {
  // 响应数据定义
}

// ==================== API方法 ====================

/**
 * [功能描述]
 */
export function [methodName](params: [RequestType]): Promise<[ResponseType]> {
  return get<[ResponseType]>('/path', params)
}

// 导出所有API
export default {
  [methodName],
  // ...
}
```

### 页面改造步骤

1. **移除Mock数据导入**
   ```typescript
   // 删除
   import { strategies } from '@/utils/mockData'
   
   // 添加
   import strategyApi from '@/utils/strategyApi'
   ```

2. **使用API获取数据**
   ```typescript
   // 原来
   const strategies = ref(mockStrategies)
   
   // 改为
   const strategies = ref([])
   const loading = ref(false)
   
   async function loadStrategies() {
     loading.value = true
     try {
       const data = await strategyApi.getStrategies()
       strategies.value = data.strategies
     } catch (error) {
       console.error('加载策略失败:', error)
     } finally {
       loading.value = false
     }
   }
   
   onMounted(() => {
     loadStrategies()
   })
   ```

3. **添加错误处理和加载状态**
   - 使用 `loading` 状态显示加载动画
   - 使用 `try-catch` 捕获错误
   - 使用 Toast/Message 组件提示用户

---

## 🔧 技术债务清单

### 需要补充的API文档

1. ❌ `signal_api.md` - 信号管理API
2. ❌ `leaderboard_api.md` - 排行榜API
3. ❌ `stats_api.md` - 统计分析API
4. ❌ `log_api.md` - 日志审计API
5. ❌ `subscription_api.md` - 数据订阅API

### 需要创建的API封装文件

1. ❌ `src/utils/marketApi.ts` - 市场数据API
2. ❌ `src/utils/backtestApi.ts` - 回测API
3. ❌ `src/utils/strategyApi.ts` - 策略管理API
4. ❌ `src/utils/tradingApi.ts` - 交易管理API
5. ❌ `src/utils/systemApi.ts` - 系统管理API
6. ❌ `src/utils/signalApi.ts` - 信号管理API（待文档）
7. ❌ `src/utils/leaderboardApi.ts` - 排行榜API（待文档）
8. ❌ `src/utils/statsApi.ts` - 统计分析API（待文档）
9. ❌ `src/utils/logApi.ts` - 日志审计API（待文档）
10. ❌ `src/utils/subscriptionApi.ts` - 数据订阅API（待文档）

### 需要改造的页面文件

**前台页面（9个）**:
1. `HomePage.vue`
2. `TradingPage.vue`
3. `StrategyList.vue`
4. `StrategyDetail.vue`
5. `RunningStrategiesPage.vue`
6. `RunningStrategyDetail.vue`
7. `SignalList.vue`
8. `SignalDetail.vue`
9. `LeaderboardPage.vue`

**后台页面（5个）**:
1. `AdminDashboard.vue`
2. `AdminStrategies.vue`
3. `AdminSignals.vue`
4. `AdminLogs.vue`
5. `AdminDataSubscription.vue`

---

## 📈 项目进度跟踪

### 里程碑

- [ ] **M1**: 核心交易功能上线（第一阶段完成）
- [ ] **M2**: 回测与分析功能上线（第二阶段完成）
- [ ] **M3**: 系统管理功能上线（第三阶段完成）
- [ ] **M4**: 全功能上线（第四阶段完成）

### 关键指标

| 指标 | 当前值 | 目标值 | 进度 |
|------|--------|--------|------|
| API文档完整度 | 6/11 | 11/11 | 55% |
| API实现率 | 11/58 | 58/58 | 19% |
| 页面真实数据率 | 1/16 | 16/16 | 6% |

---

## 📞 联系与反馈

如有疑问或建议，请联系：
- 技术负责人：[待补充]
- 文档维护：[待补充]

---

**文档版本**: v1.0  
**最后更新**: 2026-02-20  
**下次审查**: 2026-03-20
