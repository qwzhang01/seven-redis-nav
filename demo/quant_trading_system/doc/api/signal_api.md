# 信号管理 API 文档

## 概述

信号管理模块提供策略信号的查询、订阅和管理功能，支持信号广场浏览、信号详情查询、策略历史信号查询、信号订阅管理等功能。管理员端提供信号审核和手动创建信号的功能。

## 基础信息

- **C端基础URL**: `/api/v1/c/signal`
- **Admin端基础URL**: `/api/v1/m/signal`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：部分接口需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 认证 | 描述 |
|------|------|------|------|
| GET | `/api/v1/c/signal/list` | 否 | 获取公开信号列表（信号广场） |
| GET | `/api/v1/c/signal/{signal_id}` | 否 | 获取信号详情 |
| GET | `/api/v1/c/signal/strategy/{strategy_id}/history` | 否 | 获取策略历史信号 |
| POST | `/api/v1/c/signal/subscribe` | 是 | 订阅策略信号通知 |
| GET | `/api/v1/c/signal/subscriptions` | 是 | 获取我的信号订阅列表 |
| DELETE | `/api/v1/c/signal/subscriptions/{subscription_id}` | 是 | 取消信号订阅 |

### Admin端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/signal/pending` | 获取待审核信号列表 |
| PUT | `/api/v1/m/signal/{signal_id}/approve` | 审核信号（设置是否公开） |
| POST | `/api/v1/m/signal/` | 手动创建信号记录 |

---

## 信号数据结构

信号记录的完整字段说明：

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 信号ID（UUID） |
| strategy_id | string | 所属策略ID |
| strategy_name | string\|null | 策略名称 |
| symbol | string | 交易对（大写，如 BTCUSDT） |
| exchange | string | 交易所名称 |
| signal_type | string | 信号类型：buy/sell/close |
| price | float\|null | 信号价格 |
| quantity | float\|null | 建议数量 |
| confidence | float\|null | 置信度（0-1） |
| timeframe | string\|null | 时间周期 |
| reason | string\|null | 信号原因描述 |
| indicators | object\|null | 技术指标数据 |
| status | string | 信号状态：pending/executed/cancelled |
| executed_order_id | string\|null | 执行的订单ID |
| executed_price | float\|null | 实际执行价格 |
| executed_at | string\|null | 执行时间 |
| is_public | boolean | 是否公开展示 |
| subscriber_count | integer | 订阅人数 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

---

## C端接口详情

### 1. 获取公开信号列表（信号广场）

**GET** `/api/v1/c/signal/list`

查询所有公开展示的策略信号，支持按交易对、信号类型、策略过滤。无需认证。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbol | string | 否 | - | 交易对过滤（如 BTCUSDT） |
| signal_type | string | 否 | - | 信号类型过滤：buy/sell/close |
| strategy_id | string | 否 | - | 策略ID过滤 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 请求示例

```
GET /api/v1/c/signal/list?symbol=BTCUSDT&signal_type=buy&page=1&page_size=20
```

#### 响应示例

```json
{
  "items": [
    {
      "id": "signal_uuid",
      "strategy_id": "strategy_uuid",
      "strategy_name": "BTC均线策略",
      "symbol": "BTCUSDT",
      "exchange": "binance",
      "signal_type": "buy",
      "price": 50000.0,
      "quantity": 0.01,
      "confidence": 0.85,
      "timeframe": "1h",
      "reason": "快速均线上穿慢速均线",
      "indicators": {
        "ma_fast": 49800.0,
        "ma_slow": 49500.0
      },
      "status": "executed",
      "executed_order_id": "order_uuid",
      "executed_price": 49998.5,
      "executed_at": "2026-02-21T10:05:00",
      "is_public": true,
      "subscriber_count": 15,
      "created_at": "2026-02-21T10:00:00",
      "updated_at": "2026-02-21T10:05:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array[object] | 信号列表 |
| total | integer | 总信号数量 |
| page | integer | 当前页码 |
| pages | integer | 总页数 |

---

### 2. 获取信号详情

**GET** `/api/v1/c/signal/{signal_id}`

根据信号ID查询详细信息。无需认证。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| signal_id | string | 是 | 信号ID（UUID） |

#### 请求示例

```
GET /api/v1/c/signal/signal_uuid
```

#### 响应示例

```json
{
  "id": "signal_uuid",
  "strategy_id": "strategy_uuid",
  "strategy_name": "BTC均线策略",
  "symbol": "BTCUSDT",
  "exchange": "binance",
  "signal_type": "buy",
  "price": 50000.0,
  "quantity": 0.01,
  "confidence": 0.85,
  "timeframe": "1h",
  "reason": "快速均线上穿慢速均线",
  "indicators": {
    "ma_fast": 49800.0,
    "ma_slow": 49500.0
  },
  "status": "executed",
  "executed_order_id": "order_uuid",
  "executed_price": 49998.5,
  "executed_at": "2026-02-21T10:05:00",
  "is_public": true,
  "subscriber_count": 15,
  "created_at": "2026-02-21T10:00:00",
  "updated_at": "2026-02-21T10:05:00"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 3. 获取策略历史信号

**GET** `/api/v1/c/signal/strategy/{strategy_id}/history`

查询指定策略产生的所有历史信号记录，按创建时间倒序排列。无需认证。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `50` | 每页数量（最大200） |

#### 请求示例

```
GET /api/v1/c/signal/strategy/strategy_uuid/history?page=1&page_size=50
```

#### 响应示例

```json
{
  "strategy_id": "strategy_uuid",
  "items": [
    {
      "id": "signal_uuid",
      "strategy_id": "strategy_uuid",
      "strategy_name": "BTC均线策略",
      "symbol": "BTCUSDT",
      "exchange": "binance",
      "signal_type": "buy",
      "price": 50000.0,
      "quantity": 0.01,
      "confidence": 0.85,
      "timeframe": "1h",
      "reason": "快速均线上穿慢速均线",
      "indicators": null,
      "status": "executed",
      "executed_order_id": "order_uuid",
      "executed_price": 49998.5,
      "executed_at": "2026-02-21T10:05:00",
      "is_public": true,
      "subscriber_count": 15,
      "created_at": "2026-02-21T10:00:00",
      "updated_at": "2026-02-21T10:05:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategy_id | string | 策略ID |
| items | array[object] | 信号列表 |
| total | integer | 总信号数量 |
| page | integer | 当前页码 |
| pages | integer | 总页数 |

---

### 4. 订阅策略信号通知

**POST** `/api/v1/c/signal/subscribe`

订阅指定策略的信号推送，支持实时/每日/每周通知方式。**需要认证**。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要订阅的策略ID |
| notify_type | string | 否 | `"realtime"` | 通知方式：realtime/daily/weekly |

**notify_type 枚举值：**

| 值 | 描述 |
|----|------|
| `realtime` | 实时通知（信号产生时立即推送） |
| `daily` | 每日汇总通知 |
| `weekly` | 每周汇总通知 |

```json
{
  "strategy_id": "strategy_uuid",
  "notify_type": "realtime"
}
```

#### 响应示例（新订阅）

```json
{
  "id": "subscription_uuid",
  "strategy_id": "strategy_uuid",
  "notify_type": "realtime",
  "is_active": true,
  "message": "订阅成功"
}
```

#### 响应示例（更新已有订阅）

```json
{
  "id": "subscription_uuid",
  "strategy_id": "strategy_uuid",
  "notify_type": "daily",
  "is_active": true,
  "message": "已更新订阅"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 订阅记录ID |
| strategy_id | string | 订阅的策略ID |
| notify_type | string | 通知方式 |
| is_active | boolean | 订阅是否激活 |
| message | string | 操作结果描述 |

> **说明**：若已订阅该策略但处于非激活状态，重新订阅会激活并更新通知方式。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |

---

### 5. 获取我的信号订阅列表

**GET** `/api/v1/c/signal/subscriptions`

查询当前用户订阅的所有策略信号。**需要认证**。

#### 响应示例

```json
{
  "items": [
    {
      "id": "subscription_uuid",
      "strategy_id": "strategy_uuid",
      "notify_type": "realtime",
      "is_active": true,
      "created_at": "2026-02-21T10:00:00"
    }
  ],
  "total": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array[object] | 订阅列表 |
| items[].id | string | 订阅记录ID |
| items[].strategy_id | string | 订阅的策略ID |
| items[].notify_type | string | 通知方式 |
| items[].is_active | boolean | 订阅是否激活 |
| items[].created_at | string\|null | 订阅创建时间 |
| total | integer | 总订阅数量 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |

---

### 6. 取消信号订阅

**DELETE** `/api/v1/c/signal/subscriptions/{subscription_id}`

取消对指定策略信号的订阅（软删除，将订阅状态设为非激活）。**需要认证**。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅记录ID（UUID） |

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
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 403 | 无权操作此订阅（非本人订阅） |
| 404 | 订阅不存在 |

---

## Admin端接口详情

### 1. 获取待审核信号列表

**GET** `/api/v1/m/signal/pending`

查询所有尚未设置公开状态（`is_public = false`）的信号记录，供管理员审核。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 请求示例

```
GET /api/v1/m/signal/pending?page=1&page_size=20
```

#### 响应示例

```json
{
  "items": [
    {
      "id": "signal_uuid",
      "strategy_id": "strategy_uuid",
      "strategy_name": "BTC均线策略",
      "symbol": "BTCUSDT",
      "exchange": "binance",
      "signal_type": "buy",
      "price": 50000.0,
      "quantity": 0.01,
      "confidence": 0.85,
      "timeframe": "1h",
      "reason": "快速均线上穿慢速均线",
      "indicators": null,
      "status": "pending",
      "executed_order_id": null,
      "executed_price": null,
      "executed_at": null,
      "is_public": false,
      "subscriber_count": 0,
      "created_at": "2026-02-21T10:00:00",
      "updated_at": "2026-02-21T10:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "pages": 1
}
```

---

### 2. 审核信号

**PUT** `/api/v1/m/signal/{signal_id}/approve`

设置信号是否在信号广场公开展示。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| signal_id | string | 是 | 信号ID（UUID） |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_public | boolean | 是 | 是否公开展示 |
| reason | string | 否 | 审核原因（可选备注） |

```json
{
  "is_public": true,
  "reason": "信号质量良好，允许公开"
}
```

#### 响应示例

```json
{
  "success": true,
  "signal": {
    "id": "signal_uuid",
    "strategy_id": "strategy_uuid",
    "strategy_name": "BTC均线策略",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "signal_type": "buy",
    "price": 50000.0,
    "quantity": 0.01,
    "confidence": 0.85,
    "timeframe": "1h",
    "reason": "信号质量良好，允许公开",
    "indicators": null,
    "status": "pending",
    "executed_order_id": null,
    "executed_price": null,
    "executed_at": null,
    "is_public": true,
    "subscriber_count": 0,
    "created_at": "2026-02-21T10:00:00",
    "updated_at": "2026-02-21T10:10:00"
  },
  "message": "审核完成"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| signal | object | 更新后的信号完整信息 |
| message | string | 操作结果描述 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 3. 手动创建信号记录

**POST** `/api/v1/m/signal/`

手动向系统写入一条信号记录，用于测试或手动操作。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 所属策略ID |
| strategy_name | string | 否 | null | 策略名称 |
| symbol | string | 是 | - | 交易对（自动转为大写） |
| exchange | string | 否 | `"binance"` | 交易所名称 |
| signal_type | string | 是 | - | 信号类型：buy/sell/close（自动转为小写） |
| price | float | 是 | - | 信号价格 |
| quantity | float | 否 | null | 建议数量 |
| confidence | float | 否 | null | 置信度（0-1） |
| timeframe | string | 否 | null | 时间周期 |
| reason | string | 否 | null | 信号原因描述 |
| indicators | object | 否 | null | 技术指标数据 |
| is_public | boolean | 否 | `false` | 是否公开展示 |

```json
{
  "strategy_id": "strategy_uuid",
  "strategy_name": "BTC均线策略",
  "symbol": "BTCUSDT",
  "exchange": "binance",
  "signal_type": "buy",
  "price": 50000.0,
  "quantity": 0.01,
  "confidence": 0.85,
  "timeframe": "1h",
  "reason": "手动测试信号",
  "indicators": {
    "ma_fast": 49800.0,
    "ma_slow": 49500.0
  },
  "is_public": false
}
```

#### 响应示例

```json
{
  "success": true,
  "signal": {
    "id": "signal_uuid",
    "strategy_id": "strategy_uuid",
    "strategy_name": "BTC均线策略",
    "symbol": "BTCUSDT",
    "exchange": "binance",
    "signal_type": "buy",
    "price": 50000.0,
    "quantity": 0.01,
    "confidence": 0.85,
    "timeframe": "1h",
    "reason": "手动测试信号",
    "indicators": {
      "ma_fast": 49800.0,
      "ma_slow": 49500.0
    },
    "status": "pending",
    "executed_order_id": null,
    "executed_price": null,
    "executed_at": null,
    "is_public": false,
    "subscriber_count": 0,
    "created_at": "2026-02-21T10:00:00",
    "updated_at": "2026-02-21T10:00:00"
  },
  "message": "信号创建成功"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| signal | object | 创建的信号完整信息 |
| message | string | 操作结果描述 |

> **说明**：手动创建的信号初始状态为 `pending`，订阅人数为 `0`。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 403 | 权限不足（如操作他人订阅） |
| 404 | 资源不存在（信号、订阅不存在） |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |

## 信号状态说明

| 状态 | 描述 |
|------|------|
| pending | 信号已生成，等待执行 |
| executed | 信号已执行（已下单） |
| cancelled | 信号已取消 |

## 信号类型说明

| 类型 | 描述 |
|------|------|
| buy | 买入信号 |
| sell | 卖出信号 |
| close | 平仓信号 |
