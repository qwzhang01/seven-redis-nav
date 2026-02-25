# 行情数据 API 文档

## 概述

行情模块提供市场数据相关的 API 接口，包含 C 端行情查询（订阅、K线、Tick、深度等）和 Admin 端管理功能（订阅配置管理、手动同步任务、历史数据同步）。

## 基础信息

- **C端基础URL**: `/api/v1/c/market`
- **Admin端订阅管理URL**: `/api/v1/m/market/subscriptions`
- **Admin端同步任务URL**: `/api/v1/m/market/sync-tasks`
- **Admin端历史同步URL**: `/api/v1/m/market/historical-sync`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **注意**：C端行情接口依赖交易系统运行，若系统未启动将返回 `503` 错误。Admin端接口需要管理员权限。

---

## 一、C端 - 行情数据接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/market/subscribe` | 订阅行情数据 |
| POST | `/api/v1/c/market/unsubscribe` | 取消行情订阅 |
| GET | `/api/v1/c/market/kline/{symbol}` | 获取K线数据 |
| GET | `/api/v1/c/market/tick/{symbol}` | 获取最新Tick数据 |
| GET | `/api/v1/c/market/depth/{symbol}` | 获取市场深度数据 |
| GET | `/api/v1/c/market/symbols` | 获取已订阅的交易对列表 |
| GET | `/api/v1/c/market/stats` | 获取行情服务统计信息 |

---

### 1. 订阅行情数据

**POST** `/api/v1/c/market/subscribe`

向市场服务订阅指定交易对的实时行情数据。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbols | array[string] | 是 | - | 要订阅的交易对列表，不能为空 |
| exchange | string | 否 | `"binance"` | 交易所名称，可选值：binance、okx、bybit、bitget |
| market_type | string | 否 | `"spot"` | 市场类型，可选值：spot、futures、margin |

#### 响应示例

```json
{
  "success": true,
  "message": "已订阅 2 个交易对",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 交易对列表为空 / 不支持的交易所 / 不支持的市场类型 |
| 503 | 交易系统未启动 |

---

### 2. 取消行情订阅

**POST** `/api/v1/c/market/unsubscribe`

取消对指定交易对的行情数据订阅。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbols | array[string] | 是 | - | 要取消订阅的交易对列表，不能为空 |
| exchange | string | 否 | `"binance"` | 交易所名称，可选值：binance、okx、bybit、bitget |
| market_type | string | 否 | `"spot"` | 市场类型，可选值：spot、futures、margin |

#### 响应示例

```json
{
  "success": true,
  "message": "已取消订阅 2 个交易对",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

---

### 3. 获取K线数据

**GET** `/api/v1/c/market/kline/{symbol}`

查询指定交易对和时间周期的历史K线数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| timeframe | string | 否 | `"1m"` | 时间周期，可选值：1m、5m、15m、30m、1h、4h、1d、1w |
| limit | integer | 否 | `100` | 返回K线数量限制（1-1000） |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": 1708000000,
      "open": 42000.5,
      "high": 42500.0,
      "low": 41800.0,
      "close": 42300.0,
      "volume": 1500.5
    }
  ],
  "count": 1
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 无效的时间周期 |
| 503 | 交易系统未启动 |

---

### 4. 获取最新Tick数据

**GET** `/api/v1/c/market/tick/{symbol}`

查询指定交易对的最新Tick行情数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "last_price": 42300.0,
  "bid_price": 42299.5,
  "ask_price": 42300.5,
  "volume": 1500.5,
  "timestamp": 1708000000
}
```

> **说明**：若无Tick数据，所有数值字段返回 `0`。

---

### 5. 获取市场深度数据

**GET** `/api/v1/c/market/depth/{symbol}`

查询指定交易对的买卖盘深度数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对符号 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `20` | 深度档位数量限制 |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "bids": [
    {"price": 42299.5, "size": 1.5},
    {"price": 42298.0, "size": 2.0}
  ],
  "asks": [
    {"price": 42300.5, "size": 1.2},
    {"price": 42301.0, "size": 0.8}
  ],
  "timestamp": 1708000000
}
```

> **说明**：若无深度数据，bids/asks 返回空列表，timestamp 返回 `0`。

---

### 6. 获取已订阅的交易对列表

**GET** `/api/v1/c/market/symbols`

查询指定交易所和市场类型下已订阅的交易对列表。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | `"binance"` | 交易所名称 |
| market_type | string | 否 | `"spot"` | 市场类型 |

#### 响应示例

```json
{
  "exchange": "binance",
  "market_type": "spot",
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
}
```

---

### 7. 获取行情服务统计信息

**GET** `/api/v1/c/market/stats`

查询市场服务的运行统计数据和性能指标。

#### 响应示例

```json
{
  "total_symbols": 10,
  "total_ticks": 50000,
  "total_bars": 120000,
  "uptime": 3600
}
```

---

## 二、Admin端 - 订阅配置管理接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/subscriptions` | 创建订阅配置 |
| GET | `/api/v1/m/market/subscriptions` | 获取订阅列表 |
| GET | `/api/v1/m/market/subscriptions/statistics` | 获取订阅统计信息 |
| GET | `/api/v1/m/market/subscriptions/{subscription_id}` | 获取订阅详情 |
| PUT | `/api/v1/m/market/subscriptions/{subscription_id}` | 更新订阅配置 |
| DELETE | `/api/v1/m/market/subscriptions/{subscription_id}` | 删除订阅 |
| POST | `/api/v1/m/market/subscriptions/{subscription_id}/start` | 启动订阅 |
| POST | `/api/v1/m/market/subscriptions/{subscription_id}/pause` | 暂停订阅 |
| POST | `/api/v1/m/market/subscriptions/{subscription_id}/stop` | 停止订阅 |

---

### 1. 创建订阅配置

**POST** `/api/v1/m/market/subscriptions`

创建新的数据订阅配置并持久化保存，初始状态为 `stopped`。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 订阅名称 |
| exchange | string | 是 | - | 交易所名称，可选值：Binance、OKX、Bybit、Bitget（不区分大小写） |
| market_type | string | 否 | `"spot"` | 市场类型 |
| data_type | string | 是 | - | 数据类型，可选值：kline、ticker、depth、trade、orderbook |
| symbols | array[string] | 是 | - | 交易对列表，不能为空 |
| interval | string | 条件必填 | - | K线周期，data_type 为 kline 时必填，可选值：1m、5m、15m、1h、4h、1d |
| config | object | 否 | 见下方 | 订阅高级配置 |

**config 字段说明：**

| 字段 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| auto_restart | boolean | `true` | 是否自动重启 |
| max_retries | integer | `3` | 最大重试次数 |
| batch_size | integer | `1000` | 批次大小 |
| sync_interval | integer | `60` | 同步间隔（秒） |

#### 响应示例（201）

```json
{
  "success": true,
  "message": "订阅创建成功",
  "data": {
    "id": "1234567890",
    "name": "BTC K线订阅",
    "exchange": "Binance",
    "market_type": "spot",
    "data_type": "kline",
    "symbols": ["BTCUSDT"],
    "interval": "1m",
    "status": "stopped",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "last_sync_time": null,
    "total_records": 0,
    "error_count": 0,
    "last_error": null,
    "config": {
      "auto_restart": true,
      "max_retries": 3,
      "batch_size": 1000,
      "sync_interval": 60
    }
  }
}
```

---

### 2. 获取订阅列表

**GET** `/api/v1/m/market/subscriptions`

支持按交易所、数据类型、状态筛选，以及按名称模糊搜索，结果分页返回。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | - | 按交易所筛选 |
| data_type | string | 否 | - | 按数据类型筛选 |
| status | string | 否 | - | 按状态筛选：running/paused/stopped |
| search | string | 否 | - | 按名称模糊搜索 |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "1234567890",
        "name": "BTC K线订阅",
        "exchange": "Binance",
        "market_type": "spot",
        "data_type": "kline",
        "symbols": ["BTCUSDT"],
        "interval": "1m",
        "status": "running",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "last_sync_time": "2025-01-01T01:00:00",
        "total_records": 5000,
        "error_count": 0,
        "last_error": null,
        "config": {}
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3. 获取订阅统计信息

**GET** `/api/v1/m/market/subscriptions/statistics`

返回各状态订阅数量、总记录数、错误数以及按交易所/数据类型的分布。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "total_subscriptions": 5,
    "running_subscriptions": 3,
    "paused_subscriptions": 1,
    "stopped_subscriptions": 1,
    "total_records": 150000,
    "total_errors": 2,
    "by_exchange": {
      "Binance": 3,
      "OKX": 2
    },
    "by_data_type": {
      "kline": 3,
      "ticker": 1,
      "depth": 1
    }
  }
}
```

---

### 4. 获取订阅详情

**GET** `/api/v1/m/market/subscriptions/{subscription_id}`

根据订阅 ID 返回完整的订阅配置信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": "1234567890",
    "name": "BTC K线订阅",
    "exchange": "Binance",
    "market_type": "spot",
    "data_type": "kline",
    "symbols": ["BTCUSDT"],
    "interval": "1m",
    "status": "running",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "last_sync_time": "2025-01-01T01:00:00",
    "total_records": 5000,
    "error_count": 0,
    "last_error": null,
    "config": {}
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

### 5. 更新订阅配置

**PUT** `/api/v1/m/market/subscriptions/{subscription_id}`

支持更新名称、交易对列表、K线周期和高级配置（所有字段可选）。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 订阅名称 |
| symbols | array[string] | 否 | 交易对列表，不能为空 |
| interval | string | 否 | K线周期，可选值：1m、5m、15m、1h、4h、1d |
| config | object | 否 | 订阅高级配置（合并更新，保留未传字段的原值） |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅更新成功",
  "data": {
    "id": "1234567890",
    "name": "BTC K线订阅-已更新",
    "status": "running",
    "updated_at": "2025-01-01T02:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

### 6. 删除订阅

**DELETE** `/api/v1/m/market/subscriptions/{subscription_id}`

删除指定订阅配置，同时级联删除关联的同步任务。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅已删除"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订阅不存在 |

---

### 7. 启动订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/start`

将 `stopped` 或 `paused` 状态的订阅切换为 `running`。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅已启动",
  "data": {
    "id": "1234567890",
    "status": "running",
    "updated_at": "2025-01-01T02:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作 |
| 404 | 订阅不存在 |

---

### 8. 暂停订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/pause`

将 `running` 状态的订阅切换为 `paused`，保留配置和数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅已暂停",
  "data": {
    "id": "1234567890",
    "status": "paused",
    "updated_at": "2025-01-01T02:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作（仅 running 状态可暂停） |
| 404 | 订阅不存在 |

---

### 9. 停止订阅

**POST** `/api/v1/m/market/subscriptions/{subscription_id}/stop`

将 `running` 或 `paused` 状态的订阅切换为 `stopped`。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| subscription_id | string | 订阅唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅已停止",
  "data": {
    "id": "1234567890",
    "status": "stopped",
    "updated_at": "2025-01-01T02:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许执行此操作 |
| 404 | 订阅不存在 |

---

### 订阅状态流转图

```
stopped ──start──▶ running ──pause──▶ paused
   ▲                  │                  │
   │                  │                  │
   └────stop──────────┘                  │
   └────stop─────────────────────────────┘
   └────start────────────────────────────┘
```

---

## 三、Admin端 - 手动同步任务接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/sync-tasks` | 创建同步任务 |
| GET | `/api/v1/m/market/sync-tasks` | 获取同步任务列表 |
| GET | `/api/v1/m/market/sync-tasks/{task_id}` | 获取同步任务详情 |
| POST | `/api/v1/m/market/sync-tasks/{task_id}/cancel` | 取消同步任务 |

---

### 1. 创建同步任务

**POST** `/api/v1/m/market/sync-tasks`

为指定订阅创建一个手动历史数据同步任务，任务初始状态为 `pending`。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 关联的订阅ID |
| start_time | string(datetime) | 是 | 同步开始时间（ISO格式） |
| end_time | string(datetime) | 是 | 同步结束时间（ISO格式），必须晚于开始时间 |

#### 响应示例（201）

```json
{
  "success": true,
  "message": "同步任务已创建",
  "data": {
    "id": "9876543210",
    "subscription_id": "1234567890",
    "subscription_name": "BTC K线订阅",
    "exchange": "Binance",
    "symbols": ["BTCUSDT"],
    "data_type": "kline",
    "interval": "1m",
    "start_time": "2025-01-01T00:00:00",
    "end_time": "2025-02-01T00:00:00",
    "status": "pending",
    "progress": 0,
    "total_records": 0,
    "synced_records": 0,
    "error_message": null,
    "created_at": "2025-02-01T00:00:00",
    "updated_at": "2025-02-01T00:00:00",
    "completed_at": null
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 结束时间必须晚于开始时间 |
| 404 | 订阅不存在 |

---

### 2. 获取同步任务列表

**GET** `/api/v1/m/market/sync-tasks`

支持按订阅 ID 和状态筛选，结果按创建时间倒序分页返回。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| subscription_id | string | 否 | - | 按订阅ID筛选 |
| status | string | 否 | - | 按状态筛选：pending/running/completed/failed/cancelled |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "9876543210",
        "subscription_id": "1234567890",
        "subscription_name": "BTC K线订阅",
        "exchange": "Binance",
        "symbols": ["BTCUSDT"],
        "data_type": "kline",
        "interval": "1m",
        "start_time": "2025-01-01T00:00:00",
        "end_time": "2025-02-01T00:00:00",
        "status": "completed",
        "progress": 100,
        "total_records": 44640,
        "synced_records": 44640,
        "error_message": null,
        "created_at": "2025-02-01T00:00:00",
        "updated_at": "2025-02-01T01:30:00",
        "completed_at": "2025-02-01T01:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3. 获取同步任务详情

**GET** `/api/v1/m/market/sync-tasks/{task_id}`

根据任务 ID 返回完整的同步任务信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | string | 同步任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": "9876543210",
    "subscription_id": "1234567890",
    "subscription_name": "BTC K线订阅",
    "exchange": "Binance",
    "symbols": ["BTCUSDT"],
    "data_type": "kline",
    "interval": "1m",
    "start_time": "2025-01-01T00:00:00",
    "end_time": "2025-02-01T00:00:00",
    "status": "running",
    "progress": 45,
    "total_records": 44640,
    "synced_records": 20088,
    "error_message": null,
    "created_at": "2025-02-01T00:00:00",
    "updated_at": "2025-02-01T00:45:00",
    "completed_at": null
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 同步任务不存在 |

---

### 4. 取消同步任务

**POST** `/api/v1/m/market/sync-tasks/{task_id}/cancel`

取消处于 `pending` 或 `running` 状态的同步任务。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | string | 同步任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "同步任务已取消",
  "data": {
    "id": "9876543210",
    "status": "cancelled",
    "updated_at": "2025-02-01T00:30:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许取消（仅 pending/running 状态可取消） |
| 404 | 同步任务不存在 |

---

## 四、Admin端 - 历史数据同步接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/historical-sync` | 创建历史数据同步任务 |
| GET | `/api/v1/m/market/historical-sync` | 获取历史同步任务列表 |
| GET | `/api/v1/m/market/historical-sync/{task_id}` | 获取任务详情 |
| POST | `/api/v1/m/market/historical-sync/{task_id}/cancel` | 取消同步任务 |
| GET | `/api/v1/m/market/historical-sync/status/executor` | 获取执行器状态 |
| POST | `/api/v1/m/market/historical-sync/executor/start` | 启动执行器 |
| POST | `/api/v1/m/market/historical-sync/executor/stop` | 停止执行器 |

---

### 1. 创建历史数据同步任务

**POST** `/api/v1/m/market/historical-sync`

创建独立的历史数据同步任务，不依赖现有订阅配置。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 任务名称 |
| exchange | string | 是 | - | 交易所名称，可选值：Binance、OKX、Bybit、Bitget（不区分大小写） |
| data_type | string | 是 | - | 数据类型，可选值：kline、ticker、depth、trade、orderbook |
| symbols | array[string] | 是 | - | 交易对列表，不能为空 |
| interval | string | 条件必填 | - | K线周期，data_type 为 kline 时必填，可选值：1m、5m、15m、1h、4h、1d |
| start_time | string(datetime) | 是 | - | 同步开始时间（ISO格式） |
| end_time | string(datetime) | 是 | - | 同步结束时间（ISO格式），必须晚于开始时间 |
| batch_size | integer | 否 | `1000` | 批次大小（1-5000） |

#### 响应示例（201）

```json
{
  "success": true,
  "message": "历史数据同步任务已创建",
  "data": {
    "id": "5555555555",
    "name": "BTC历史K线同步",
    "exchange": "Binance",
    "data_type": "kline",
    "symbols": ["BTCUSDT"],
    "interval": "1m",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2025-01-01T00:00:00",
    "batch_size": 1000,
    "status": "pending",
    "progress": 0,
    "total_records": 0,
    "synced_records": 0,
    "error_message": null,
    "created_at": "2025-02-01T00:00:00",
    "updated_at": "2025-02-01T00:00:00",
    "completed_at": null
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 422 | 参数校验失败（不支持的交易所/数据类型/K线周期、交易对为空、结束时间不晚于开始时间、批次大小超范围） |

---

### 2. 获取历史同步任务列表

**GET** `/api/v1/m/market/historical-sync`

支持按交易所、数据类型、状态筛选，结果按创建时间倒序分页返回。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | - | 按交易所筛选 |
| data_type | string | 否 | - | 按数据类型筛选 |
| status | string | 否 | - | 按状态筛选：pending/running/completed/failed/cancelled |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "5555555555",
        "name": "BTC历史K线同步",
        "exchange": "Binance",
        "data_type": "kline",
        "symbols": ["BTCUSDT"],
        "interval": "1m",
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2025-01-01T00:00:00",
        "batch_size": 1000,
        "status": "completed",
        "progress": 100,
        "total_records": 525600,
        "synced_records": 525600,
        "error_message": null,
        "created_at": "2025-02-01T00:00:00",
        "updated_at": "2025-02-01T05:00:00",
        "completed_at": "2025-02-01T05:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 3. 获取历史同步任务详情

**GET** `/api/v1/m/market/historical-sync/{task_id}`

根据任务 ID 返回完整的历史数据同步任务信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | string | 任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": "5555555555",
    "name": "BTC历史K线同步",
    "exchange": "Binance",
    "data_type": "kline",
    "symbols": ["BTCUSDT"],
    "interval": "1m",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2025-01-01T00:00:00",
    "batch_size": 1000,
    "status": "running",
    "progress": 60,
    "total_records": 525600,
    "synced_records": 315360,
    "error_message": null,
    "created_at": "2025-02-01T00:00:00",
    "updated_at": "2025-02-01T03:00:00",
    "completed_at": null
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 历史数据同步任务不存在 |

---

### 4. 取消历史同步任务

**POST** `/api/v1/m/market/historical-sync/{task_id}/cancel`

取消处于 `pending` 或 `running` 状态的历史数据同步任务。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| task_id | string | 任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "message": "历史数据同步任务已取消",
  "data": {
    "id": "5555555555",
    "status": "cancelled",
    "updated_at": "2025-02-01T01:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 当前状态不允许取消（仅 pending/running 状态可取消） |
| 404 | 历史数据同步任务不存在 |

---

### 5. 获取历史同步执行器状态

**GET** `/api/v1/m/market/historical-sync/status/executor`

返回执行器的运行状态、活跃任务数量等信息。

#### 响应示例

```json
{
  "success": true,
  "data": {
    "executor_running": true,
    "active_tasks": 2,
    "task_ids": ["5555555555", "6666666666"],
    "max_concurrent_tasks": 3,
    "check_interval": 10,
    "max_retries": 3
  }
}
```

---

### 6. 启动历史同步执行器

**POST** `/api/v1/m/market/historical-sync/executor/start`

手动启动历史数据同步任务执行器。

#### 响应示例

```json
{
  "success": true,
  "message": "历史数据同步执行器已启动"
}
```

> **说明**：若执行器已在运行中，返回 `"历史数据同步执行器已在运行中"`。

---

### 7. 停止历史同步执行器

**POST** `/api/v1/m/market/historical-sync/executor/stop`

手动停止历史数据同步任务执行器。

#### 响应示例

```json
{
  "success": true,
  "message": "历史数据同步执行器已停止"
}
```

> **说明**：若执行器已停止，返回 `"历史数据同步执行器已停止"`。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 / 状态不允许操作 |
| 401 | 未提供认证凭据 / 用户不存在 |
| 403 | 权限不足（Admin接口需要管理员权限） |
| 404 | 资源不存在（订阅/任务） |
| 422 | 请求体参数校验失败 |
| 503 | 交易系统未启动（C端接口） |
