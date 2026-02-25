# 信号 API 文档

## 概述

信号模块提供策略信号的查询、订阅和管理功能，包括信号广场浏览、信号订阅通知、策略历史信号查询，以及管理员的信号审核和手动创建功能。

## 基础信息

- **C端基础URL**: `/api/v1/c/signal`
- **Admin端基础URL**: `/api/v1/m/signal`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### C 端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/signal/list` | 获取公开信号列表（信号广场） |
| GET | `/api/v1/c/signal/subscriptions` | 获取我的信号订阅列表 |
| GET | `/api/v1/c/signal/strategy/{strategy_id}/history` | 获取策略历史信号 |
| GET | `/api/v1/c/signal/{signal_id}` | 获取信号详情 |
| POST | `/api/v1/c/signal/subscribe` | 订阅策略信号通知 |
| DELETE | `/api/v1/c/signal/subscriptions/{subscription_id}` | 取消信号订阅 |

### Admin 端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/signal/pending` | 获取待审核信号列表 |
| PUT | `/api/v1/m/signal/{signal_id}/approve` | 审核信号（设置是否公开） |
| POST | `/api/v1/m/signal/` | 手动创建信号记录 |

---

## C 端接口详情

### 1. 获取公开信号列表（信号广场）

**GET** `/api/v1/c/signal/list`

查询所有公开展示的策略信号，支持按交易对、信号类型、策略过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbol | string | 否 | - | 交易对过滤 |
| signal_type | string | 否 | - | 信号类型过滤（buy/sell/close） |
| strategy_id | string | 否 | - | 策略ID过滤 |
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
  ],
  "total": 50,
  "page": 1,
  "pages": 3
}
```

---

### 2. 获取我的信号订阅列表

**GET** `/api/v1/c/signal/subscriptions`

查询当前用户订阅的所有策略信号。需要认证。

#### 响应示例

```json
{
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
```

---

### 3. 获取策略历史信号

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
  "strategy_id": "strategy_001",
  "items": [
    {
      "id": 123456789,
      "strategy_id": "strategy_001",
      "strategy_name": "MA Cross",
      "symbol": "BTCUSDT",
      "signal_type": "buy",
      "price": 65000.0,
      "confidence": 0.85,
      "status": "executed",
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:35:00"
    }
  ],
  "total": 120,
  "page": 1,
  "pages": 3
}
```

---

### 4. 获取信号详情

**GET** `/api/v1/c/signal/{signal_id}`

根据信号ID查询详细信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| signal_id | integer | 信号ID |

#### 响应示例

```json
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
  "status": "pending",
  "executed_order_id": null,
  "executed_price": null,
  "executed_at": null,
  "is_public": true,
  "subscriber_count": 15,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 5. 订阅策略信号通知

**POST** `/api/v1/c/signal/subscribe`

订阅指定策略的信号推送，支持实时/每日/每周通知。需要认证。若已订阅但处于非活跃状态，将自动重新激活。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要订阅的策略ID |
| notify_type | string | 否 | `"realtime"` | 通知方式（realtime/daily/weekly） |

#### 响应示例

```json
{
  "id": 987654321,
  "strategy_id": "strategy_001",
  "notify_type": "realtime",
  "is_active": true,
  "message": "订阅成功"
}
```

---

### 6. 取消信号订阅

**DELETE** `/api/v1/c/signal/subscriptions/{subscription_id}`

取消对指定策略信号的订阅。需要认证。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | integer | 订阅ID |

#### 响应示例

```json
{
  "success": true,
  "message": "已取消订阅"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权操作此订阅 |
| 404 | 订阅不存在 |

---

## Admin 端接口详情

### 7. 获取待审核信号列表

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

### 8. 审核信号

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

### 9. 手动创建信号记录

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
| 401 | 未认证或用户不存在/已被禁用 |
| 403 | 无权操作 |
| 404 | 信号/订阅不存在 |
| 500 | 服务器内部错误 |
