# 信号详情 & 信号跟单 — 接口设计文档

> 文档版本：v1.1  
> 最后更新：2026-02-27  
> 对应页面：SignalDetail.vue、SignalFollowDetail.vue
>
> **v1.1 更新说明：**  
> - 信号详情接口从 `signal` 主表及 `signal_trade_record` 表查询
> - 新增 `GET /signals/{id}/return-curve` 独立收益曲线接口  
> - 统一 K线接口路径为 `/market/kline`  
> - 跟单配置更新接口统一为 `/follows/{id}/config`  
> - 补充鉴权说明和接口清单中的鉴权列  
> - 补充 `provider` 字段中的 `badges` 支持

---

## 目录

- [1. 接口总览](#1-接口总览)
- [2. 信号详情页接口](#2-信号详情页接口)
  - [2.1 获取信号详情](#21-获取信号详情)
  - [2.2 获取K线数据](#22-获取k线数据)
  - [2.3 获取信号历史记录](#23-获取信号历史记录)
  - [2.4 获取信号提供者信息](#24-获取信号提供者信息)
  - [2.5 获取月度收益分布](#25-获取月度收益分布)
  - [2.6 获取回撤分析数据](#26-获取回撤分析数据)
  - [2.7 获取用户评价列表](#27-获取用户评价列表)
  - [2.8 提交用户评价](#28-提交用户评价)
  - [2.9 评价点赞](#29-评价点赞)
  - [2.10 创建跟单](#210-创建跟单)
- [3. 信号跟单详情页接口](#3-信号跟单详情页接口)
  - [3.1 获取跟单详情](#31-获取跟单详情)
  - [3.2 获取跟单收益对比数据](#32-获取跟单收益对比数据)
  - [3.3 获取跟单交易记录](#33-获取跟单交易记录)
  - [3.4 获取事件日志](#34-获取事件日志)
  - [3.5 获取仓位分布](#35-获取仓位分布)
  - [3.6 更新跟单配置](#36-更新跟单配置)
  - [3.7 停止跟单](#37-停止跟单)
- [4. 公共数据结构](#4-公共数据结构)
- [5. 错误码定义](#5-错误码定义)

---

## 1. 接口总览

### 基础信息

| 项目 | 说明 |
|------|------|
| 基础URL | `{API_BASE}/api/v1` |
| 鉴权方式 | Bearer Token (JWT) |
| 内容类型 | `application/json` |
| 时间格式 | ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`) |

### 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

### 接口清单

| # | 方法 | 路径 | 说明 | 鉴权 |
|---|------|------|------|------|
| 2.1 | GET | `/signals/{id}` | 获取信号详情 | 可选 |
| 2.2 | GET | `/market/kline` | 获取K线数据 | 否 |
| 2.3 | GET | `/signals/{id}/history` | 获取信号历史记录 | 可选 |
| 2.4 | GET | `/signals/{id}/provider` | 获取信号提供者信息 | 否 |
| 2.5 | GET | `/signals/{id}/monthly-returns` | 获取月度收益分布 | 否 |
| 2.6 | GET | `/signals/{id}/drawdown` | 获取回撤分析数据 | 否 |
| 2.7 | GET | `/signals/{id}/return-curve` | 获取收益曲线数据 | 否 |
| 2.8 | GET | `/signals/{id}/reviews` | 获取用户评价列表 | 否 |
| 2.9 | POST | `/signals/{id}/reviews` | 提交用户评价 | 是 |
| 2.10 | POST | `/signals/{id}/reviews/{reviewId}/like` | 评价点赞 | 是 |
| 2.11 | POST | `/signals/{id}/follow` | 创建跟单 | 是 |
| 3.1 | GET | `/follows/{id}` | 获取跟单详情 | 是 |
| 3.2 | GET | `/follows/{id}/comparison` | 获取收益对比数据 | 是 |
| 3.3 | GET | `/follows/{id}/trades` | 获取跟单交易记录 | 是 |
| 3.4 | GET | `/follows/{id}/events` | 获取事件日志 | 是 |
| 3.5 | GET | `/follows/{id}/positions` | 获取仓位分布 | 是 |
| 3.6 | PUT | `/follows/{id}/config` | 更新跟单配置 | 是 |
| 3.7 | POST | `/follows/{id}/stop` | 停止跟单 | 是 |

---

## 2. 信号详情页接口

### 2.1 获取信号详情

获取信号的完整详情信息，包括基本信息、风险参数、绩效指标、持仓等。

**请求**

```
GET /api/v1/signals/{id}
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 信号唯一标识 |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "signal_001",
    "name": "Alpha Trend v2",
    "description": "基于多因子量化模型的趋势跟踪策略...",
    "platform": "Binance",
    "type": "live",
    "status": "running",
    "exchange": "Binance",
    "tradingPair": "BTC/USDT",
    "timeframe": "4H",
    "signalFrequency": "medium",
    "followers": 1234,
    "cumulativeReturn": 45.67,
    "maxDrawdown": 12.34,
    "runDays": 180,
    "returnCurve": [0.5, 1.2, 2.3, ...],
    "returnCurveLabels": ["2025-01-01", "2025-01-02", ...],
    "riskParameters": {
      "maxPositionSize": 30,
      "stopLossPercentage": 5,
      "takeProfitPercentage": 15,
      "riskRewardRatio": 3,
      "volatilityFilter": true
    },
    "performanceMetrics": {
      "sharpeRatio": 1.85,
      "winRate": 68.5,
      "profitFactor": 2.13,
      "averageHoldingPeriod": 3.5,
      "maxConsecutiveLosses": 4
    },
    "notificationSettings": {
      "emailAlerts": true,
      "pushNotifications": true,
      "telegramBot": false,
      "discordWebhook": false,
      "alertThreshold": 5
    },
    "positions": [
      {
        "symbol": "BTC/USDT",
        "side": "long",
        "amount": 0.05,
        "entryPrice": 89234.50,
        "currentPrice": 91234.56,
        "pnlPercent": 2.24
      }
    ],
    "provider": {
      "id": "provider_001",
      "name": "CryptoMaster",
      "avatar": "https://...",
      "verified": true,
      "bio": "8年加密货币交易经验...",
      "totalSignals": 12,
      "avgReturn": 23.5,
      "totalFollowers": 8420,
      "rating": 4.6,
      "joinDate": "2023-06-15",
      "experience": "8年",
      "badges": ["certified_trader", "top_performer"]
    },
    "createdAt": "2024-08-15T10:30:00Z",
    "updatedAt": "2025-02-26T00:00:00Z"
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 信号唯一标识 |
| name | string | 信号名称 |
| description | string | 信号描述 |
| platform | string | 所属平台 |
| type | enum | 信号类型：`live`(实盘) / `demo`(模拟) |
| status | enum | 状态：`running` / `paused` / `stopped` |
| exchange | string | 交易所名称 |
| tradingPair | string | 主要交易对 |
| timeframe | string | 时间周期 (15m/1H/4H/1D/1W) |
| signalFrequency | enum | 信号频率：`high` / `medium` / `low` |
| followers | number | 跟随人数 |
| cumulativeReturn | number | 累计收益率(%) |
| maxDrawdown | number | 最大回撤(%) |
| runDays | number | 运行天数 |
| returnCurve | number[] | 收益曲线数据点 |
| returnCurveLabels | string[] | 收益曲线X轴标签 (日期) |
| riskParameters | object | 风险参数配置 |
| performanceMetrics | object | 绩效指标 |
| notificationSettings | object | 通知设置 |
| positions | Position[] | 当前持仓列表 |

---

### 2.2 获取K线数据

获取指定交易对的K线历史数据，用于 TradingChart 组件渲染。

**请求**

```
GET /api/v1/market/kline
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| symbol | query | string | 是 | 交易对，如 `BTC/USDT` |
| interval | query | string | 是 | K线周期：`15m`/`1h`/`4h`/`1d`/`1w` |
| limit | query | number | 否 | 返回数量，默认 200，最大 1000 |
| startTime | query | number | 否 | 起始时间戳(秒) |
| endTime | query | number | 否 | 结束时间戳(秒) |

**响应**

```json
{
  "code": 0,
  "data": {
    "symbol": "BTC/USDT",
    "interval": "1h",
    "klines": [
      {
        "time": 1740000000,
        "open": 89234.50,
        "high": 89567.80,
        "low": 89100.20,
        "close": 89456.30,
        "volume": 234.56
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| time | number | Unix时间戳(秒) |
| open | number | 开盘价 |
| high | number | 最高价 |
| low | number | 最低价 |
| close | number | 收盘价 |
| volume | number | 成交量 |

---

### 2.3 获取信号历史记录

获取信号发出的交易信号历史列表。

**请求**

```
GET /api/v1/signals/{id}/history
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 信号ID |
| page | query | number | 否 | 页码，默认 1 |
| pageSize | query | number | 否 | 每页数量，默认 20 |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 156,
    "page": 1,
    "pageSize": 20,
    "records": [
      {
        "id": "sh_001",
        "action": "buy",
        "symbol": "BTC/USDT",
        "price": 89234.50,
        "amount": 0.055,
        "time": "2025-02-25T14:30:00Z",
        "strength": "strong",
        "pnl": null,
        "status": "open"
      },
      {
        "id": "sh_002",
        "action": "sell",
        "symbol": "ETH/USDT",
        "price": 3521.23,
        "amount": 1.42,
        "time": "2025-02-24T10:15:00Z",
        "strength": "medium",
        "pnl": 91.52,
        "status": "closed"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录唯一标识 |
| action | enum | 操作方向：`buy` / `sell` |
| symbol | string | 交易对 |
| price | number | 成交价格 |
| amount | number | 交易数量 |
| time | string | 信号发出时间 (ISO 8601) |
| strength | enum | 信号强度：`strong` / `medium` / `weak` |
| pnl | number\|null | 盈亏金额，未平仓为 null |
| status | enum | 状态：`open`(持仓中) / `closed`(已平仓) |

---

### 2.4 获取信号提供者信息

**请求**

```
GET /api/v1/signals/{id}/provider
```

**响应**

```json
{
  "code": 0,
  "data": {
    "id": "provider_001",
    "name": "CryptoMaster",
    "avatar": "https://...",
    "verified": true,
    "bio": "8年加密货币交易经验，擅长趋势跟踪和量化分析。",
    "totalSignals": 12,
    "avgReturn": 23.5,
    "totalFollowers": 8420,
    "rating": 4.6,
    "joinDate": "2023-06-15",
    "experience": "8年",
    "badges": ["certified_trader", "top_performer"]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 提供者ID |
| name | string | 昵称 |
| avatar | string | 头像URL |
| verified | boolean | 是否认证交易员 |
| bio | string | 个人简介 |
| totalSignals | number | 发布的信号总数 |
| avgReturn | number | 平均收益率(%) |
| totalFollowers | number | 总粉丝数 |
| rating | number | 评分(1-5) |
| joinDate | string | 入驻日期 |
| experience | string | 交易经验描述 |
| badges | string[] | 徽章列表 |

---

### 2.5 获取月度收益分布

**请求**

```
GET /api/v1/signals/{id}/monthly-returns
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 信号ID |
| months | query | number | 否 | 返回月份数，默认 12 |

**响应**

```json
{
  "code": 0,
  "data": {
    "months": [
      { "month": "2024-03", "return": 5.2 },
      { "month": "2024-04", "return": -1.8 },
      { "month": "2024-05", "return": 8.3 }
    ],
    "statistics": {
      "profitMonths": 9,
      "lossMonths": 3,
      "bestMonth": 12.6,
      "worstMonth": -4.5,
      "avgMonthlyReturn": 4.0
    }
  }
}
```

---

### 2.6 获取回撤分析数据

**请求**

```
GET /api/v1/signals/{id}/drawdown
```

**响应**

```json
{
  "code": 0,
  "data": {
    "drawdownCurve": [-0.5, -1.2, 0, -0.8, -2.3, ...],
    "labels": ["2025-01-01", "2025-01-02", ...],
    "statistics": {
      "currentDrawdown": -1.25,
      "maxDrawdown": -8.45,
      "avgDrawdown": -2.13,
      "maxDrawdownDate": "2024-11-15",
      "maxDrawdownDuration": 12
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| drawdownCurve | number[] | 回撤序列（≤0） |
| labels | string[] | X轴日期标签 |
| currentDrawdown | number | 当前回撤(%) |
| maxDrawdown | number | 最大回撤(%) |
| avgDrawdown | number | 平均回撤(%) |
| maxDrawdownDate | string | 最大回撤发生日期 |
| maxDrawdownDuration | number | 最大回撤持续天数 |

---

### 2.7 获取收益曲线数据

获取信号的累计收益率曲线和回撤曲线，支持时间范围筛选。

**请求**

```
GET /api/v1/signals/{id}/return-curve
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 信号ID |
| period | query | string | 否 | 时间范围：`7d`/`30d`/`90d`/`180d`/`all`，默认 `all` |

**响应**

```json
{
  "code": 0,
  "data": {
    "returnCurve": [0.5, 1.2, 2.3, 5.6, 8.1, ...],
    "drawdownCurve": [0, -0.3, -0.1, -1.2, -0.5, ...],
    "labels": ["2025-01-01", "2025-01-02", ...]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| returnCurve | number[] | 累计收益率序列(%) |
| drawdownCurve | number[] | 回撤序列(≤ 0 的负数)(%) |
| labels | string[] | X轴日期标签 |

---

### 2.8 获取用户评价列表

**请求**

```
GET /api/v1/signals/{id}/reviews
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 信号ID |
| page | query | number | 否 | 页码，默认 1 |
| pageSize | query | number | 否 | 每页数量，默认 10 |
| sort | query | string | 否 | 排序：`latest` / `highest` / `lowest` / `most_liked` |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 45,
    "averageRating": 4.6,
    "ratingDistribution": {
      "5": 45,
      "4": 30,
      "3": 15,
      "2": 7,
      "1": 3
    },
    "reviews": [
      {
        "id": "review_001",
        "user": "Trader_John",
        "userId": "user_123",
        "avatar": "https://...",
        "date": "2025-02-20",
        "rating": 5,
        "content": "信号质量很高，跟单两个月了收益很稳定。",
        "likes": 24,
        "isLiked": false
      }
    ]
  }
}
```

---

### 2.9 提交用户评价

**请求**

```
POST /api/v1/signals/{id}/reviews
Authorization: Bearer {token}
```

**请求体**

```json
{
  "rating": 5,
  "content": "信号质量很高，跟单两个月了收益很稳定。"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rating | number | 是 | 评分 1-5 |
| content | string | 是 | 评价内容，10-500字 |

**响应**

```json
{
  "code": 0,
  "message": "评价提交成功",
  "data": {
    "id": "review_046",
    "rating": 5,
    "content": "...",
    "date": "2025-02-26"
  }
}
```

---

### 2.10 评价点赞

**请求**

```
POST /api/v1/signals/{id}/reviews/{reviewId}/like
Authorization: Bearer {token}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "liked": true,
    "totalLikes": 25
  }
}
```

---

### 2.11 创建跟单

**请求**

```
POST /api/v1/signals/{id}/follow
Authorization: Bearer {token}
```

**请求体**

```json
{
  "amount": 5000,
  "ratio": 1.0,
  "stopLoss": 15
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| amount | number | 是 | 跟单资金 (USDT)，最小 100 |
| ratio | number | 是 | 跟单比例，0.25/0.5/1.0/2.0 |
| stopLoss | number | 是 | 总亏损止损百分比，1-50 |

**响应**

```json
{
  "code": 0,
  "message": "跟单创建成功",
  "data": {
    "followId": "follow_001",
    "signalId": "signal_001",
    "amount": 5000,
    "ratio": 1.0,
    "stopLoss": 15,
    "status": "following",
    "startTime": "2025-02-26T00:30:00Z"
  }
}
```

---

## 3. 信号跟单详情页接口

### 3.1 获取跟单详情

获取用户跟单的完整详情，包括配置、收益、持仓、绩效。

**请求**

```
GET /api/v1/follows/{id}
Authorization: Bearer {token}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "id": "follow_001",
    "signalId": "signal_001",
    "signalName": "Alpha Pro #1",
    "exchange": "Binance",
    "status": "following",
    "totalReturn": 15.23,
    "todayReturn": 1.23,
    "followAmount": 5000,
    "currentValue": 5761.50,
    "maxDrawdown": 8.45,
    "currentDrawdown": 3.21,
    "followDays": 45,
    "winRate": 68.5,
    "followRatio": 1.0,
    "stopLoss": 15,
    "startTime": "2025-01-06T10:30:00Z",
    "riskLevel": "medium",
    "currentPrice": 91234.56,
    "priceChange24h": 2.34,
    "volume24h": "12.5B",
    "totalTrades": 156,
    "winTrades": 107,
    "lossTrades": 49,
    "avgWin": 125.50,
    "avgLoss": 78.30,
    "profitFactor": 1.60,
    "returnCurve": [0.5, 1.2, 2.3, ...],
    "returnCurveLabels": ["2025-01-06", "2025-01-07", ...],
    "positions": [
      {
        "id": "pos_001",
        "symbol": "BTC/USDT",
        "side": "long",
        "amount": 0.055,
        "entryPrice": 89234.50,
        "currentPrice": 91234.56,
        "pnl": 110.00,
        "pnlPercent": 2.24
      }
    ],
    "tradingPoints": [
      {
        "id": "tp_001",
        "type": "buy",
        "symbol": "BTC/USDT",
        "price": 89234.50,
        "amount": 0.055,
        "time": "2025-02-20T14:30:00Z"
      }
    ]
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 跟单记录ID |
| signalId | string | 对应信号ID |
| signalName | string | 信号名称 |
| status | enum | `following`/`paused`/`stopped` |
| totalReturn | number | 总收益率(%) |
| todayReturn | number | 今日收益率(%) |
| followAmount | number | 初始跟单资金(USDT) |
| currentValue | number | 当前净值(USDT) |
| maxDrawdown | number | 最大回撤(%) |
| currentDrawdown | number | 当前回撤(%) |
| followDays | number | 跟单天数 |
| winRate | number | 胜率(%) |
| followRatio | number | 跟单比例 |
| stopLoss | number | 止损线(%) |
| riskLevel | enum | 风险等级：`low`/`medium`/`high` |
| positions | Position[] | 当前持仓 |
| tradingPoints | TradingPoint[] | 最近交易点位 |

---

### 3.2 获取跟单收益对比数据

获取跟单收益曲线与信号源收益曲线的对比数据。

**请求**

```
GET /api/v1/follows/{id}/comparison
Authorization: Bearer {token}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "labels": ["2025-01-06", "2025-01-07", ...],
    "followCurve": [0.5, 1.1, 2.0, ...],
    "signalCurve": [0.6, 1.3, 2.5, ...],
    "statistics": {
      "returnDiff": -1.85,
      "avgSlippage": 0.12,
      "copyRate": 98.7,
      "followFinalReturn": 15.23,
      "signalFinalReturn": 17.08
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| labels | string[] | X轴日期标签 |
| followCurve | number[] | 跟单收益曲线(%) |
| signalCurve | number[] | 信号源收益曲线(%) |
| returnDiff | number | 收益差异：follow - signal (%) |
| avgSlippage | number | 平均滑点(%) |
| copyRate | number | 跟单复制率(%) |

---

### 3.3 获取跟单交易记录

**请求**

```
GET /api/v1/follows/{id}/trades
Authorization: Bearer {token}
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 跟单记录ID |
| page | query | number | 否 | 页码，默认 1 |
| pageSize | query | number | 否 | 每页数量，默认 20 |
| side | query | string | 否 | 过滤方向：`buy`/`sell` |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 156,
    "page": 1,
    "records": [
      {
        "id": "trade_001",
        "side": "buy",
        "symbol": "BTC/USDT",
        "price": 89234.50,
        "amount": 0.055,
        "total": 4907.90,
        "pnl": null,
        "time": "2025-02-20T14:30:00Z",
        "signalTime": "2025-02-20T14:29:58Z",
        "slippage": 0.08
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 交易记录ID |
| side | enum | `buy`/`sell` |
| symbol | string | 交易对 |
| price | number | 成交价格 |
| amount | number | 交易数量 |
| total | number | 成交额(USDT) |
| pnl | number\|null | 盈亏金额(卖出时有值) |
| time | string | 实际成交时间 |
| signalTime | string | 信号源发出时间 |
| slippage | number | 滑点(%) |

---

### 3.4 获取事件日志

**请求**

```
GET /api/v1/follows/{id}/events
Authorization: Bearer {token}
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | path | string | 是 | 跟单记录ID |
| page | query | number | 否 | 页码 |
| pageSize | query | number | 否 | 每页数量，默认 20 |
| type | query | string | 否 | 过滤类型：`trade`/`risk`/`success`/`error`/`system` |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 89,
    "records": [
      {
        "id": "evt_001",
        "type": "trade",
        "typeLabel": "交易",
        "message": "跟单买入 BTC/USDT 0.055个，成交价 $89,234.50",
        "time": "2025-02-20T14:30:12Z",
        "metadata": {
          "symbol": "BTC/USDT",
          "side": "buy",
          "price": 89234.50,
          "amount": 0.055
        }
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 事件ID |
| type | enum | 事件类型：`trade`/`risk`/`success`/`error`/`system` |
| typeLabel | string | 类型中文标签 |
| message | string | 事件描述文本 |
| time | string | 事件发生时间 |
| metadata | object | 事件附加数据（按类型不同结构不同） |

**事件类型说明**

| type | 场景 | metadata 示例 |
|------|------|---------------|
| trade | 跟单执行交易 | `{symbol, side, price, amount}` |
| success | 交易成功确认 | `{tradeId, pnl}` |
| risk | 风控预警 | `{drawdown, threshold}` |
| error | 异常事件 | `{errorCode, delay, slippage}` |
| system | 系统通知 | `{action, config}` |

---

### 3.5 获取仓位分布

**请求**

```
GET /api/v1/follows/{id}/positions
Authorization: Bearer {token}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "totalValue": 5761.50,
    "usedValue": 9815.52,
    "freeValue": -4054.02,
    "capitalUsageRate": 85.3,
    "positions": [
      {
        "symbol": "BTC/USDT",
        "value": 4907.90,
        "percentage": 50.1
      },
      {
        "symbol": "ETH/USDT",
        "value": 4908.62,
        "percentage": 49.9
      }
    ],
    "distribution": [
      { "name": "BTC/USDT", "value": 4907.90 },
      { "name": "ETH/USDT", "value": 4908.62 },
      { "name": "可用资金", "value": 852.88 }
    ]
  }
}
```

---

### 3.6 更新跟单配置

**请求**

```
PUT /api/v1/follows/{id}/config
Authorization: Bearer {token}
```

**请求体**

```json
{
  "followRatio": 0.5,
  "stopLoss": 20,
  "followAmount": 3000
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| followRatio | number | 否 | 跟单比例 |
| stopLoss | number | 否 | 止损百分比 |
| followAmount | number | 否 | 跟单资金（需追加/减少时） |

**响应**

```json
{
  "code": 0,
  "message": "配置更新成功",
  "data": {
    "followRatio": 0.5,
    "stopLoss": 20,
    "followAmount": 3000,
    "updatedAt": "2025-02-26T00:30:00Z"
  }
}
```

---

### 3.7 停止跟单

**请求**

```
POST /api/v1/follows/{id}/stop
Authorization: Bearer {token}
```

**请求体**

```json
{
  "closePositions": true,
  "reason": "手动停止"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| closePositions | boolean | 否 | 是否同时平仓所有持仓，默认 true |
| reason | string | 否 | 停止原因 |

**响应**

```json
{
  "code": 0,
  "message": "跟单已停止",
  "data": {
    "followId": "follow_001",
    "status": "stopped",
    "finalReturn": 15.23,
    "closedPositions": 2,
    "stoppedAt": "2025-02-26T00:30:00Z"
  }
}
```

---

## 4. 公共数据结构

### Position（持仓）

```typescript
interface Position {
  id: string              // 持仓ID
  symbol: string          // 交易对
  side: 'long' | 'short'  // 方向
  amount: number          // 数量
  entryPrice: number      // 开仓价
  currentPrice: number    // 现价
  pnl: number             // 浮动盈亏(USDT)
  pnlPercent: number      // 浮动盈亏(%)
}
```

### TradingPoint（交易点位）

```typescript
interface TradingPoint {
  id: string              // 点位ID
  type: 'buy' | 'sell'    // 方向
  symbol: string          // 交易对
  price: number           // 价格
  amount: number          // 数量
  time: string            // 时间 (ISO 8601)
}
```

### KlineDataPoint（K线数据点）

```typescript
interface KlineDataPoint {
  time: number    // Unix时间戳(秒)
  open: number    // 开盘价
  high: number    // 最高价
  low: number     // 最低价
  close: number   // 收盘价
  volume: number  // 成交量
}
```

### PaginationParams（分页参数）

```typescript
interface PaginationParams {
  page: number      // 页码，从1开始
  pageSize: number  // 每页数量
}
```

### PaginationResponse（分页响应）

```typescript
interface PaginationResponse<T> {
  total: number     // 总记录数
  page: number      // 当前页码
  pageSize: number  // 每页数量
  records: T[]      // 数据列表
}
```

---

## 5. 错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 0 | 200 | 成功 |
| 1001 | 401 | 未登录或 Token 过期 |
| 1002 | 403 | 无权限访问 |
| 2001 | 404 | 信号不存在 |
| 2002 | 404 | 跟单记录不存在 |
| 2003 | 400 | 信号已停止，无法跟单 |
| 2004 | 400 | 余额不足 |
| 2005 | 400 | 已跟单该信号，不可重复跟单 |
| 2006 | 400 | 跟单资金低于最低限额 |
| 2007 | 400 | 止损比例超出范围 |
| 2008 | 400 | 跟单已停止，无法修改配置 |
| 3001 | 400 | 评价内容过短或过长 |
| 3002 | 400 | 已评价过该信号 |
| 5001 | 500 | 服务器内部错误 |
| 5002 | 503 | 交易所连接异常 |
