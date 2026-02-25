# 行情 API 文档

## 概述

行情模块提供市场行情数据相关的 API 接口，支持行情订阅、K 线数据查询、实时 Tick 数据、市场深度等功能。同时提供管理员端的订阅配置管理、同步任务管理和历史数据同步接口。

## 基础信息

- **C端基础URL**: `/api/v1/c/market`
- **Admin端订阅管理URL**: `/api/v1/m/market/subscriptions`
- **Admin端同步任务URL**: `/api/v1/m/market/sync-tasks`
- **Admin端历史同步URL**: `/api/v1/m/market/historical-sync`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有行情接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/market/subscribe` | 订阅行情数据 |
| POST | `/api/v1/c/market/unsubscribe` | 取消行情订阅 |
| GET | `/api/v1/c/market/kline/{symbol}` | 获取 K 线数据 |
| GET | `/api/v1/c/market/tick/{symbol}` | 获取最新 Tick 数据 |
| GET | `/api/v1/c/market/depth/{symbol}` | 获取市场深度数据 |
| GET | `/api/v1/c/market/symbols` | 获取已订阅的交易对列表 |
| GET | `/api/v1/c/market/stats` | 获取行情服务统计信息 |

### Admin端 — 订阅配置管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/subscriptions` | 创建订阅配置 |
| GET | `/api/v1/m/market/subscriptions` | 获取订阅列表 |
| GET | `/api/v1/m/market/subscriptions/statistics` | 获取订阅统计信息 |
| GET | `/api/v1/m/market/subscriptions/{id}` | 获取订阅详情 |
| PUT | `/api/v1/m/market/subscriptions/{id}` | 更新订阅配置 |
| DELETE | `/api/v1/m/market/subscriptions/{id}` | 删除订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/start` | 启动订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/pause` | 暂停订阅 |
| POST | `/api/v1/m/market/subscriptions/{id}/stop` | 停止订阅 |

### Admin端 — 同步任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/sync-tasks` | 创建同步任务 |
| GET | `/api/v1/m/market/sync-tasks` | 获取同步任务列表 |
| GET | `/api/v1/m/market/sync-tasks/{id}` | 获取同步任务详情 |
| POST | `/api/v1/m/market/sync-tasks/{id}/cancel` | 取消同步任务 |

### Admin端 — 历史数据同步

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/market/historical-sync` | 创建历史数据同步任务 |
| GET | `/api/v1/m/market/historical-sync` | 获取历史同步任务列表 |
| GET | `/api/v1/m/market/historical-sync/{id}` | 获取任务详情 |
| POST | `/api/v1/m/market/historical-sync/{id}/cancel` | 取消同步任务 |
| GET | `/api/v1/m/market/historical-sync/status/executor` | 获取同步执行器状态 |
| POST | `/api/v1/m/market/historical-sync/executor/start` | 启动同步执行器 |
| POST | `/api/v1/m/market/historical-sync/executor/stop` | 停止同步执行器 |

---

## C端接口详情

### 1. 订阅行情数据

**POST** `/api/v1/c/market/subscribe`

向市场服务订阅指定交易对的实时行情数据。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbols | array[string] | 是 | - | 交易对列表（不能为空） |
| exchange | string | 否 | `"binance"` | 交易所名称（binance/okx/bybit/bitget） |
| market_type | string | 否 | `"spot"` | 市场类型（spot/futures/margin） |

#### 响应示例

```json
{
  "success": true,
  "message": "已订阅 2 个交易对",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

---

### 2. 取消行情订阅

**POST** `/api/v1/c/market/unsubscribe`

取消对指定交易对的行情数据订阅。请求体与订阅接口相同。

#### 响应示例

```json
{
  "success": true,
  "message": "已取消订阅 2 个交易对",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

---

### 3. 获取 K 线数据

**GET** `/api/v1/c/market/kline/{symbol}`

查询指定交易对和时间周期的历史 K 线数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| timeframe | string | 否 | `"1m"` | K线周期（1m/5m/15m/30m/1h/4h/1d/1w） |
| limit | integer | 否 | `100` | 返回数量（1-1000） |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": 1708000000,
      "open": 91000.0,
      "high": 91500.0,
      "low": 90800.0,
      "close": 91200.0,
      "volume": 125.5
    }
  ],
  "count": 1
}
```

---

### 4. 获取最新 Tick 数据

**GET** `/api/v1/c/market/tick/{symbol}`

查询指定交易对的最新 Tick 行情数据。

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "last_price": 91200.0,
  "bid_price": 91199.0,
  "ask_price": 91201.0,
  "volume": 12345.6,
  "timestamp": 1708000000
}
```

---

### 5. 获取市场深度数据

**GET** `/api/v1/c/market/depth/{symbol}`

查询指定交易对的买卖盘深度数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `20` | 深度档位数量 |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "bids": [{"price": 91199.0, "size": 0.5}],
  "asks": [{"price": 91201.0, "size": 0.3}],
  "timestamp": 1708000000
}
```

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
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

---

### 7. 获取行情服务统计信息

**GET** `/api/v1/c/market/stats`

查询市场服务的运行统计数据和性能指标。

---

## Admin端 — 订阅配置管理接口详情

> **权限要求**：以下接口均需管理员权限。

### 1. 创建订阅配置

**POST** `/api/v1/m/market/subscriptions`

创建新的数据订阅配置，初始状态为 `stopped`。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 订阅名称 |
| exchange | string | 是 | - | 交易所（Binance/OKX/Bybit/Bitget） |
| market_type | string | 否 | `"spot"` | 市场类型 |
| data_type | string | 是 | - | 数据类型（kline/ticker/depth/trade/orderbook） |
| symbols | array[string] | 是 | - | 交易对列表（不能为空） |
| interval | string | 条件必填 | - | K线周期（data_type=kline时必填） |
| config | object | 否 | 默认配置 | 高级配置（auto_restart/max_retries/batch_size/sync_interval） |

#### 响应示例

```json
{
  "success": true,
  "message": "订阅创建成功",
  "data": {
    "id": "123456",
    "name": "BTC K线订阅",
    "exchange": "Binance",
    "status": "stopped",
    ...
  }
}
```

---

### 2. 获取订阅列表

**GET** `/api/v1/m/market/subscriptions`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | - | 按交易所筛选 |
| data_type | string | 否 | - | 按数据类型筛选 |
| status | string | 否 | - | 按状态筛选：running/paused/stopped |
| search | string | 否 | - | 按名称模糊搜索 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

---

### 3. 获取订阅统计信息

**GET** `/api/v1/m/market/subscriptions/statistics`

返回各状态订阅数量、总记录数、错误数以及按交易所/数据类型的分布。

---

### 4. 获取/更新/删除订阅

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/market/subscriptions/{id}` | 获取订阅详情 |
| PUT | `/api/v1/m/market/subscriptions/{id}` | 更新订阅配置（name/symbols/interval/config） |
| DELETE | `/api/v1/m/market/subscriptions/{id}` | 删除订阅（级联删除关联同步任务） |

---

### 5. 启动/暂停/停止订阅

| 方法 | 路径 | 允许源状态 | 目标状态 |
|------|------|-----------|---------|
| POST | `/{id}/start` | stopped, paused | running |
| POST | `/{id}/pause` | running | paused |
| POST | `/{id}/stop` | running, paused | stopped |

---

## Admin端 — 同步任务管理接口详情

### 1. 创建同步任务

**POST** `/api/v1/m/market/sync-tasks`

为指定订阅创建手动历史数据同步任务，初始状态为 `pending`。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| subscription_id | string | 是 | 订阅ID |
| start_time | datetime | 是 | 开始时间（ISO格式） |
| end_time | datetime | 是 | 结束时间（ISO格式，必须晚于开始时间） |

---

### 2. 获取同步任务列表

**GET** `/api/v1/m/market/sync-tasks`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| subscription_id | string | 否 | - | 按订阅ID筛选 |
| status | string | 否 | - | 按状态筛选：pending/running/completed/failed/cancelled |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量 |

---

### 3. 获取同步任务详情

**GET** `/api/v1/m/market/sync-tasks/{task_id}`

---

### 4. 取消同步任务

**POST** `/api/v1/m/market/sync-tasks/{task_id}/cancel`

取消处于 `pending` 或 `running` 状态的同步任务。

---

## Admin端 — 历史数据同步接口详情

### 1. 创建历史数据同步任务

**POST** `/api/v1/m/market/historical-sync`

创建独立的历史数据同步任务，不依赖现有订阅配置。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 任务名称 |
| exchange | string | 是 | - | 交易所 |
| data_type | string | 是 | - | 数据类型（kline/ticker/depth/trade/orderbook） |
| symbols | array[string] | 是 | - | 交易对列表 |
| interval | string | 条件必填 | - | K线周期（data_type=kline时必填） |
| start_time | datetime | 是 | - | 开始时间 |
| end_time | datetime | 是 | - | 结束时间 |
| batch_size | integer | 否 | `1000` | 批次大小（1-5000） |

---

### 2. 获取历史同步任务列表

**GET** `/api/v1/m/market/historical-sync`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| exchange | string | 否 | - | 按交易所筛选 |
| data_type | string | 否 | - | 按数据类型筛选 |
| status | string | 否 | - | 按状态筛选 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量 |

---

### 3. 获取任务详情 / 取消任务

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/market/historical-sync/{task_id}` | 获取任务详情 |
| POST | `/api/v1/m/market/historical-sync/{task_id}/cancel` | 取消任务（pending/running状态） |

---

### 4. 同步执行器控制

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/market/historical-sync/status/executor` | 获取执行器运行状态 |
| POST | `/api/v1/m/market/historical-sync/executor/start` | 启动同步执行器 |
| POST | `/api/v1/m/market/historical-sync/executor/stop` | 停止同步执行器 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如不支持的交易所/时间周期） |
| 401 | 未提供认证凭据或令牌无效 |
| 403 | 权限不足（Admin端接口需要管理员权限） |
| 404 | 资源不存在（订阅/任务不存在） |
| 503 | 交易系统未启动 |
