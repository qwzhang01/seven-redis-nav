# 信号管理 API 文档

## 概述

信号模块提供策略信号的查询、订阅和管理功能。C端用户可浏览公开信号广场、订阅信号通知、查看历史信号；M端管理员可审核信号和手动创建信号记录。

## 基础信息

- **C端基础URL**: `/api/v1/c/signal`
- **M端基础URL**: `/api/v1/m/signal`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/signal/list` | 获取公开信号列表（信号广场） |
| GET | `/api/v1/c/signal/subscriptions` | 获取我的信号订阅列表 |
| GET | `/api/v1/c/signal/strategy/{strategy_id}/history` | 获取策略历史信号 |
| GET | `/api/v1/c/signal/{signal_id}` | 获取信号详情 |
| POST | `/api/v1/c/signal/subscribe` | 订阅策略信号通知 |
| DELETE | `/api/v1/c/signal/subscriptions/{subscription_id}` | 取消信号订阅 |

### M端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/signal/pending` | 获取待审核信号列表 |
| PUT | `/api/v1/m/signal/{signal_id}/approve` | 审核信号 |
| POST | `/api/v1/m/signal/` | 手动创建信号记录 |

---

## C端接口详情

### 1. 获取公开信号列表（信号广场）

**GET** `/api/v1/c/signal/list`

查询所有公开展示的策略信号，支持按交易对、信号类型、策略过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbol | string | 否 | - | 交易对过滤 |
| signal_type | string | 否 | - | 信号类型: buy/sell/close |
| strategy_id | string | 否 | - | 策略ID过滤 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "strategy_id": "strategy_001",
      "strategy_name": "BTC均线策略",
      "symbol": "BTC/USDT",
      "exchange": "binance",
      "signal_type": "buy",
      "price": 91000.0,
      "quantity": 0.1,
      "confidence": 0.85,
      "timeframe": "1h",
      "reason": "MA20上穿MA60",
      "status": "pending",
      "is_public": true,
      "subscriber_count": 15,
      "created_at": "2025-02-24T19:03:23Z"
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
      "id": 1,
      "strategy_id": "strategy_001",
      "notify_type": "realtime",
      "is_active": true,
      "created_at": "2025-02-24T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 3. 获取策略历史信号

**GET** `/api/v1/c/signal/strategy/{strategy_id}/history`

查询指定策略产生的所有历史信号记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

---

### 4. 获取信号详情

**GET** `/api/v1/c/signal/{signal_id}`

根据信号ID查询详细信息。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 信号不存在 |

---

### 5. 订阅策略信号通知

**POST** `/api/v1/c/signal/subscribe`

订阅指定策略的信号推送，支持实时/每日/每周通知。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要订阅的策略ID |
| notify_type | string | 否 | `"realtime"` | 通知方式: realtime/daily/weekly |

#### 响应示例

```json
{
  "id": 1,
  "strategy_id": "strategy_001",
  "notify_type": "realtime",
  "is_active": true,
  "message": "订阅成功"
}
```

---

### 6. 取消信号订阅

**DELETE** `/api/v1/c/signal/subscriptions/{subscription_id}`

取消对指定策略信号的订阅。

#### 响应示例

```json
{
  "success": true,
  "message": "已取消订阅"
}
```

---

## M端接口详情

### 1. 获取待审核信号列表

**GET** `/api/v1/m/signal/pending`

查询所有尚未设置公开状态的信号记录，供管理员审核。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

---

### 2. 审核信号

**PUT** `/api/v1/m/signal/{signal_id}/approve`

设置信号是否在信号广场公开展示。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_public | boolean | 是 | 是否公开 |
| reason | string | 否 | 审核原因 |

#### 响应示例

```json
{
  "success": true,
  "signal": {...},
  "message": "审核完成"
}
```

---

### 3. 手动创建信号记录

**POST** `/api/v1/m/signal/`

手动向系统写入一条信号记录，用于测试或手动操作。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 策略ID |
| strategy_name | string | 否 | - | 策略名称 |
| symbol | string | 是 | - | 交易对 |
| exchange | string | 否 | `"binance"` | 交易所 |
| signal_type | string | 是 | - | 信号类型: buy/sell/close |
| price | float | 是 | - | 信号价格 |
| quantity | float | 否 | - | 数量 |
| confidence | float | 否 | - | 信心度 |
| timeframe | string | 否 | - | K线周期 |
| reason | string | 否 | - | 信号原因 |
| indicators | object | 否 | - | 指标数据 |
| is_public | boolean | 否 | `false` | 是否公开 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 信号/订阅不存在 |
