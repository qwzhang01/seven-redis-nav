# 信号 API 文档

## 概述

信号模块提供策略信号的查询、订阅、跟单和管理功能，包括信号广场浏览、信号详情页（收益曲线、历史记录、提供者信息、月度收益、回撤分析、用户评价）、信号跟单（创建跟单、跟单详情、收益对比、交易记录、事件日志）、信号订阅通知，以及管理员的信号审核和手动创建功能。

## 基础信息

- **C端信号基础URL**: `/api/v1/c/signal`
- **C端跟单基础URL**: `/api/v1/c/follows`
- **Admin端基础URL**: `/api/v1/m/signal`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### C 端接口 — 信号广场（/api/v1/c/signal）

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/c/signal/list` | 获取公开信号列表（信号广场） | 否 |
| GET | `/api/v1/c/signal/platforms` | 获取平台列表（筛选项） | 否 |
| GET | `/api/v1/c/signal/subscriptions` | 获取我的信号订阅列表 | 是 |
| GET | `/api/v1/c/signal/strategy/{strategy_id}/history` | 获取策略历史信号 | 否 |
| GET | `/api/v1/c/signal/{signal_id}` | 获取信号详情 | 可选 |
| GET | `/api/v1/c/signal/{signal_id}/return-curve` | 获取信号收益曲线 | 否 |
| GET | `/api/v1/c/signal/{signal_id}/history` | 获取信号历史记录 | 否 |
| GET | `/api/v1/c/signal/{signal_id}/provider` | 获取信号提供者信息 | 否 |
| GET | `/api/v1/c/signal/{signal_id}/monthly-returns` | 获取月度收益分布 | 否 |
| GET | `/api/v1/c/signal/{signal_id}/drawdown` | 获取回撤分析数据 | 否 |
| GET | `/api/v1/c/signal/{signal_id}/reviews` | 获取用户评价列表 | 可选 |
| POST | `/api/v1/c/signal/{signal_id}/reviews` | 提交用户评价 | 是 |
| POST | `/api/v1/c/signal/{signal_id}/reviews/{review_id}/like` | 评价点赞/取消点赞 | 是 |
| POST | `/api/v1/c/signal/subscribe` | 订阅信号通知 | 是 |
| DELETE | `/api/v1/c/signal/subscriptions/{subscription_id}` | 取消信号订阅 | 是 |

### C 端接口 — 跟单管理（/api/v1/c/follows）

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/c/follows/list` | 获取用户所有跟单记录 | 是 |
| POST | `/api/v1/c/follows/` | 创建跟单 | 是 |
| GET | `/api/v1/c/follows/{follow_id}` | 获取跟单详情 | 是 |
| GET | `/api/v1/c/follows/{follow_id}/comparison` | 获取跟单收益对比数据 | 是 |
| GET | `/api/v1/c/follows/{follow_id}/trades` | 获取跟单交易记录 | 是 |
| GET | `/api/v1/c/follows/{follow_id}/events` | 获取事件日志 | 是 |
| GET | `/api/v1/c/follows/{follow_id}/positions` | 获取仓位分布 | 是 |
| PUT | `/api/v1/c/follows/{follow_id}/config` | 更新跟单配置 | 是 |
| POST | `/api/v1/c/follows/{follow_id}/stop` | 停止跟单 | 是 |

### Admin 端接口（/api/v1/m/signal）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/signal/pending` | 获取待审核信号列表 |
| PUT | `/api/v1/m/signal/{signal_id}/approve` | 审核信号（设置是否公开） |
| POST | `/api/v1/m/signal/` | 手动创建信号记录 |

---

## C 端接口详情 — 信号广场

### 1. 获取公开信号列表（信号广场）

**GET** `/api/v1/c/signal/list`

获取信号列表，支持按平台、类型、运行天数筛选，支持关键词搜索和多种排序方式。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| platform | string | 否 | - | 来源平台筛选 |
| type | string | 否 | - | 信号类型: live / simulated |
| min_days | integer | 否 | - | 最小运行天数（≥0） |
| search | string | 否 | - | 关键词搜索（模糊匹配信号名称） |
| sort_by | string | 否 | `"return_desc"` | 排序方式: return_desc / return_asc / drawdown_asc / followers |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `9` | 每页数量（1-100） |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 50,
    "page": 1,
    "pages": 6
  }
}
```

---

### 2. 获取平台列表（筛选项）

**GET** `/api/v1/c/signal/platforms`

返回当前系统中所有信号源的平台名称列表，用于信号广场筛选项。

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": ["Binance", "OKX", "Bybit"]
}
```

---

### 3. 获取我的信号订阅列表

**GET** `/api/v1/c/signal/subscriptions`

查询当前用户订阅的所有策略信号。**需要认证**。

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 987654321,
        "strategy_id": "strategy_001",
        "notify_type": "realtime",
        "is_active": true,
        "created_at": "2025-01-10T08:00:00"
      }
    ],
    "total": 1
  }
}
```

---

### 4. 获取策略历史信号

**GET** `/api/v1/c/signal/strategy/{strategy_id}/history`

查询指定策略产生的所有历史信号记录。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| strategy_id | string | 策略ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "strategy_id": "strategy_001",
    "items": [
      {
        "id": 123456789,
        "strategy_id": "strategy_001",
        "strategy_name": "MA Cross",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "signal_type": "buy",
        "price": 65000.0,
        "quantity": 0.1,
        "confidence": 0.85,
        "timeframe": "1h",
        "reason": "均线金叉",
        "indicators": {"ma5": 64500, "ma20": 64000},
        "status": "executed",
        "executed_order_id": null,
        "executed_price": null,
        "executed_at": null,
        "is_public": true,
        "subscriber_count": 15,
        "created_at": "2025-01-15T10:30:00",
        "updated_at": "2025-01-15T10:35:00"
      }
    ],
    "total": 120,
    "page": 1,
    "pages": 3
  }
}
```

---

### 5. 获取信号详情

**GET** `/api/v1/c/signal/{signal_id}`

获取信号的完整详情信息，包括基本信息、风险参数、绩效指标、持仓等。支持可选认证（登录用户可获取个性化数据）。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 123456789,
    "strategy_id": "strategy_001",
    "strategy_name": "MA Cross",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "signal_type": "buy",
    "price": 65000.0,
    "quantity": 0.1,
    "confidence": 0.85,
    "timeframe": "1h",
    "reason": "均线金叉",
    "indicators": {"ma5": 64500, "ma20": 64000},
    "status": "pending",
    "executed_order_id": null,
    "executed_price": null,
    "executed_at": null,
    "is_public": true,
    "subscriber_count": 15,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 6. 获取信号收益曲线

**GET** `/api/v1/c/signal/{signal_id}/return-curve`

返回信号的每日累计收益率和回撤曲线数据，支持时间范围筛选。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"all"` | 时间范围: 7d / 30d / 90d / 180d / all |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "signal_id": 123456789,
    "period": "30d",
    "curve": [
      {"date": "2025-01-01", "cumulative_return": 0.05, "drawdown": -0.02},
      {"date": "2025-01-02", "cumulative_return": 0.08, "drawdown": 0.0}
    ]
  }
}
```

---

### 7. 获取信号历史记录

**GET** `/api/v1/c/signal/{signal_id}/history`

获取信号发出的交易信号历史列表，支持分页。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 80,
    "page": 1,
    "pages": 4
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 8. 获取信号提供者信息

**GET** `/api/v1/c/signal/{signal_id}/provider`

获取信号创建者/提供者的详细资料。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "provider_id": "user_001",
    "name": "量化大师",
    "avatar": "https://example.com/avatar.png",
    "bio": "专注加密货币量化交易",
    "signal_count": 15,
    "follower_count": 200,
    "total_return": 0.35
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 9. 获取月度收益分布

**GET** `/api/v1/c/signal/{signal_id}/monthly-returns`

按月汇总信号的收益分布数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| months | integer | 否 | `12` | 返回月份数（1-60） |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "signal_id": 123456789,
    "monthly_returns": [
      {"month": "2025-01", "return_rate": 0.12, "trade_count": 25},
      {"month": "2024-12", "return_rate": -0.03, "trade_count": 18}
    ]
  }
}
```

---

### 10. 获取回撤分析数据

**GET** `/api/v1/c/signal/{signal_id}/drawdown`

获取信号的回撤曲线和统计信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "signal_id": 123456789,
    "max_drawdown": -0.15,
    "current_drawdown": -0.05,
    "avg_drawdown": -0.08,
    "drawdown_curve": [
      {"date": "2025-01-01", "drawdown": -0.02},
      {"date": "2025-01-02", "drawdown": -0.05}
    ]
  }
}
```

---

### 11. 获取用户评价列表

**GET** `/api/v1/c/signal/{signal_id}/reviews`

获取信号的用户评价，包括评分分布和评价详情。支持可选认证。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `10` | 每页数量（1-50） |
| sort | string | 否 | `"latest"` | 排序方式: latest / highest / lowest / most_liked |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 111,
        "user_id": "user_002",
        "username": "trader_bob",
        "rating": 5,
        "content": "信号非常准确，收益稳定！",
        "likes": 12,
        "is_liked": false,
        "created_at": "2025-01-14T16:00:00"
      }
    ],
    "total": 30,
    "page": 1,
    "pages": 3,
    "rating_distribution": {
      "5": 15, "4": 8, "3": 4, "2": 2, "1": 1
    },
    "average_rating": 4.2
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 12. 提交用户评价

**POST** `/api/v1/c/signal/{signal_id}/reviews`

为信号提交评价和评分，每个用户只能评价一次。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| rating | integer | 是 | 评分 1-5 |
| content | string | 是 | 评价内容（10-500字） |

#### 响应示例

```json
{
  "code": 0,
  "message": "评价提交成功",
  "data": {
    "id": 222,
    "signal_id": 123456789,
    "rating": 5,
    "content": "信号质量很高",
    "created_at": "2025-01-16T10:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 错误码 | 描述 |
|-------------|--------|------|
| 400 | 3002 | 已评价过该信号 |
| 404 | - | 信号不存在 |

---

### 13. 评价点赞/取消点赞

**POST** `/api/v1/c/signal/{signal_id}/reviews/{review_id}/like`

对评价进行点赞，重复点赞则取消。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |
| review_id | integer | 评价ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "liked": true,
    "total_likes": 13
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 评价不存在 |

---

### 14. 获取用户所有跟单记录

**GET** `/api/v1/c/follows/list`

查询当前用户的全部跟单记录列表，支持分页和状态过滤。**需要认证**。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| pageSize | integer | 否 | `20` | 每页数量（1-100） |
| status | string | 否 | - | 状态过滤: following / stopped / paused |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "333",
        "signalId": "strategy_001",
        "signalName": "MA Cross Signal",
        "exchange": "binance",
        "status": "following",
        "followAmount": 1000.0,
        "currentValue": 1120.0,
        "totalReturn": 0.12,
        "todayReturn": 0.02,
        "maxDrawdown": 0.05,
        "winRate": 0.65,
        "followRatio": 1.0,
        "stopLoss": 0.1,
        "riskLevel": "low",
        "totalTrades": 25,
        "followDays": 30,
        "startTime": "2025-01-10T08:00:00",
        "stopTime": null,
        "createTime": "2025-01-10T08:00:00"
      }
    ],
    "total": 5,
    "page": 1,
    "pages": 1
  }
}
```

---

### 15. 创建跟单

**POST** `/api/v1/c/follows/`

为当前用户创建一条新的信号跟单记录。**需要认证**。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategyId | string | 是 | - | 要跟单的策略ID |
| signalName | string | 是 | - | 信号/策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| followAmount | float | 是 | - | 跟单资金(USDT)，须大于0 |
| followRatio | float | 否 | `1.0` | 跟单比例（0~1） |
| stopLoss | float | 否 | - | 止损比例（0~1） |

#### 响应示例

```json
{
  "code": 0,
  "message": "跟单创建成功",
  "data": {
    "id": "333",
    "signalId": "strategy_001",
    "signalName": "MA Cross Signal",
    "exchange": "binance",
    "status": "following",
    "followAmount": 1000.0,
    "currentValue": 1000.0,
    "totalReturn": 0,
    "todayReturn": 0,
    "maxDrawdown": 0,
    "winRate": 0,
    "followRatio": 1.0,
    "stopLoss": 0.1,
    "riskLevel": "low",
    "totalTrades": 0,
    "followDays": 0,
    "startTime": "2025-01-10T08:00:00",
    "stopTime": null,
    "createTime": "2025-01-10T08:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 跟单资金必须大于0 |
| 400 | 跟单比例必须在 0~1 之间 |
| 400 | 止损比例必须在 0~1 之间 |
| 400 | 已存在该策略的活跃跟单，请先停止后再创建 |

---

### 16. 订阅策略信号通知

**POST** `/api/v1/c/signal/subscribe`

订阅指定策略的信号推送。**需要认证**。若已订阅但处于非活跃状态，将自动重新激活。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要订阅的策略ID |
| notify_type | string | 否 | `"realtime"` | 通知方式（realtime/daily/weekly） |

#### 响应示例

```json
{
  "code": 0,
  "message": "订阅成功",
  "data": {
    "id": 987654321,
    "strategy_id": "strategy_001",
    "notify_type": "realtime",
    "is_active": true
  }
}
```

---

### 17. 取消信号订阅

**DELETE** `/api/v1/c/signal/subscriptions/{subscription_id}`

取消对指定策略信号的订阅。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | integer | 订阅ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "已取消订阅",
  "data": {
    "success": true
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权操作此订阅 |
| 404 | 订阅不存在 |

---

## C 端接口详情 — 跟单管理

### 18. 获取跟单详情

**GET** `/api/v1/c/follows/{follow_id}`

获取跟单的完整详情，包括配置、收益、持仓、绩效统计。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "follow_id": 333,
    "signal_id": 123456789,
    "signal_name": "MA Cross Signal",
    "status": "active",
    "config": {
      "follow_ratio": 1.0,
      "stop_loss": 10.0,
      "follow_amount": 1000.0
    },
    "performance": {
      "total_return": 0.12,
      "total_pnl": 120.0,
      "win_rate": 0.65,
      "trade_count": 25
    },
    "created_at": "2025-01-10T08:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 19. 获取跟单收益对比数据

**GET** `/api/v1/c/follows/{follow_id}/comparison`

获取跟单收益曲线与信号源收益曲线的对比数据，包含收益差异、平均滑点、跟单复制率等统计指标。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "follow_id": 333,
    "follow_curve": [...],
    "signal_curve": [...],
    "stats": {
      "return_diff": 0.02,
      "avg_slippage": 0.001,
      "copy_rate": 0.95
    }
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 20. 获取跟单交易记录

**GET** `/api/v1/c/follows/{follow_id}/trades`

查询跟单的历史成交记录，支持按方向过滤和分页。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |
| side | string | 否 | - | 过滤方向: buy / sell |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 444,
        "symbol": "BTCUSDT",
        "side": "buy",
        "price": 65000.0,
        "quantity": 0.1,
        "pnl": 50.0,
        "executed_at": "2025-01-15T10:35:00"
      }
    ],
    "total": 25,
    "page": 1,
    "pages": 2
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 21. 获取事件日志

**GET** `/api/v1/c/follows/{follow_id}/events`

查询跟单操作的完整事件日志，包括交易、风控、异常、系统事件。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |
| type | string | 否 | - | 过滤类型: trade / risk / success / error / system |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 555,
        "type": "trade",
        "message": "买入 BTCUSDT 0.1 @ 65000",
        "created_at": "2025-01-15T10:35:00"
      }
    ],
    "total": 50,
    "page": 1,
    "pages": 3
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 22. 获取仓位分布

**GET** `/api/v1/c/follows/{follow_id}/positions`

获取跟单的当前持仓分布，包括各交易对占比、资金使用率等。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "follow_id": 333,
    "positions": [
      {
        "symbol": "BTCUSDT",
        "side": "long",
        "quantity": 0.1,
        "entry_price": 65000.0,
        "current_price": 66000.0,
        "unrealized_pnl": 100.0,
        "ratio": 0.65
      }
    ],
    "total_value": 1120.0,
    "usage_rate": 0.65
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 23. 更新跟单配置

**PUT** `/api/v1/c/follows/{follow_id}/config`

修改跟单的比例、止损和资金设置。仅允许修改进行中的跟单。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| followRatio | float | 否 | 跟单比例 |
| stopLoss | float | 否 | 止损百分比（1-50） |
| followAmount | float | 否 | 跟单资金(USDT)，须大于0 |

#### 响应示例

```json
{
  "code": 0,
  "message": "配置更新成功",
  "data": {
    "follow_id": 333,
    "follow_ratio": 1.5,
    "stop_loss": 15.0,
    "follow_amount": 2000.0
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 跟单已停止，无法修改 |
| 403 | 无权操作此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 24. 停止跟单

**POST** `/api/v1/c/follows/{follow_id}/stop`

将跟单设为停止状态，可选择是否同时平仓。**需要认证**。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| follow_id | integer | 跟单ID |

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| closePositions | boolean | 否 | `true` | 是否同时平仓所有持仓 |
| reason | string | 否 | - | 停止原因（最多200字） |

#### 响应示例

```json
{
  "code": 0,
  "message": "跟单已停止",
  "data": {
    "follow_id": 333,
    "status": "stopped",
    "closed_positions": true
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 跟单已停止 |
| 403 | 无权操作此跟单记录 |
| 404 | 跟单记录不存在 |

---

## Admin 端接口详情

### 25. 获取待审核信号列表

**GET** `/api/v1/m/signal/pending`

查询所有尚未设置公开状态的信号记录，供管理员审核。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 123456789,
      "strategy_id": "strategy_001",
      "strategy_name": "MA Cross",
      "symbol": "BTCUSDT",
      "exchange": "binance",
      "signal_type": "buy",
      "price": 65000.0,
      "is_public": false,
      "created_at": "2025-01-15T10:30:00"
    }
  ],
  "total": 5,
  "page": 1,
  "pages": 1
}
```

---

### 26. 审核信号

**PUT** `/api/v1/m/signal/{signal_id}/approve`

设置信号是否在信号广场公开展示。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| is_public | boolean | 是 | - | 是否公开 |
| reason | string | 否 | - | 审核原因 |

#### 响应示例

```json
{
  "success": true,
  "signal": {
    "id": 123456789,
    "strategy_id": "strategy_001",
    "is_public": true,
    "updated_at": "2025-01-15T12:00:00"
  },
  "message": "审核完成"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 27. 手动创建信号记录

**POST** `/api/v1/m/signal/`

手动向系统写入一条信号记录，用于测试或手动操作。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 策略ID |
| strategy_name | string | 否 | - | 策略名称 |
| symbol | string | 是 | - | 交易对（自动转大写） |
| exchange | string | 否 | `"binance"` | 交易所 |
| signal_type | string | 是 | - | 信号类型（buy/sell/close） |
| price | float | 是 | - | 信号价格 |
| quantity | float | 否 | - | 数量 |
| confidence | float | 否 | - | 信号置信度 |
| timeframe | string | 否 | - | 时间周期 |
| reason | string | 否 | - | 信号原因 |
| indicators | object | 否 | - | 指标数据 |
| is_public | boolean | 否 | `false` | 是否公开 |

#### 响应示例

```json
{
  "success": true,
  "signal": {
    "id": 123456789,
    "strategy_id": "strategy_001",
    "symbol": "BTCUSDT",
    "signal_type": "buy",
    "price": 65000.0,
    "status": "pending",
    "is_public": false,
    "created_at": "2025-01-15T10:30:00"
  },
  "message": "信号创建成功"
}
```

---

## 信号数据字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 信号唯一ID（雪花算法生成） |
| strategy_id | string | 关联的策略ID |
| strategy_name | string | 策略名称 |
| symbol | string | 交易对（如 BTCUSDT） |
| exchange | string | 交易所（如 binance） |
| signal_type | string | 信号类型：buy（买入）、sell（卖出）、close（平仓） |
| price | float | 信号价格 |
| quantity | float | 数量 |
| confidence | float | 信号置信度（0-1） |
| timeframe | string | 时间周期 |
| reason | string | 信号原因/备注 |
| indicators | object | 技术指标数据 |
| status | string | 信号状态（pending/executed/cancelled） |
| executed_order_id | string | 已执行的订单ID |
| executed_price | float | 实际执行价格 |
| executed_at | string | 执行时间（ISO格式） |
| is_public | boolean | 是否公开展示 |
| subscriber_count | integer | 订阅人数 |
| created_at | string | 创建时间（ISO格式） |
| updated_at | string | 更新时间（ISO格式） |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 / 业务逻辑错误 |
| 401 | 未认证或用户不存在/已被禁用 |
| 403 | 无权操作 |
| 404 | 信号/订阅/跟单/评价不存在 |
| 500 | 服务器内部错误 |
