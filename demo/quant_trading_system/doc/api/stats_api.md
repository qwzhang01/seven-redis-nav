# 统计分析 API 文档

## 概述

统计分析模块提供系统运行统计数据的查询接口，供管理员监控系统整体状态，包括用户统计、策略统计、交易统计和行情数据统计等。

## 基础信息

- **基础URL**: `/api/v1/m/stats`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有统计接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

> **注意**：部分统计接口依赖交易系统运行，若系统未启动相关字段将返回默认值（0 或空对象）。

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/stats/overview` | 系统概览统计 |
| GET | `/api/v1/m/stats/users` | 用户统计数据 |
| GET | `/api/v1/m/stats/strategies` | 策略统计数据 |
| GET | `/api/v1/m/stats/trading` | 交易统计数据 |
| GET | `/api/v1/m/stats/market` | 行情数据统计 |

---

## 接口详情

### 1. 系统概览统计

**GET** `/api/v1/m/stats/overview`

返回系统核心指标的汇总数据，包括用户数、策略数、信号数、WebSocket连接数等。

#### 响应示例

```json
{
  "total_users": 1250,
  "active_users_today": 85,
  "new_users_today": 12,
  "total_strategies": 8,
  "running_strategies": 3,
  "total_signals": 5420,
  "signals_today": 36,
  "subscriptions": 5,
  "ws_connections": 42,
  "ws_channel_stats": {
    "market": 30,
    "trading": 8,
    "strategy": 4
  },
  "timestamp": "2026-02-21T02:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| total_users | integer | 总用户数（已启用） |
| active_users_today | integer | 今日活跃用户数（今日有登录记录） |
| new_users_today | integer | 今日新增用户数 |
| total_strategies | integer | 总策略数（从策略引擎获取） |
| running_strategies | integer | 运行中策略数 |
| total_signals | integer | 总信号数 |
| signals_today | integer | 今日信号数 |
| subscriptions | integer | 订阅配置总数 |
| ws_connections | integer | 当前 WebSocket 连接数 |
| ws_channel_stats | object | 各 WebSocket 频道连接数统计 |
| timestamp | string | 统计时间（ISO 8601格式） |

> **注意**：`total_strategies` 和 `running_strategies` 从交易引擎实时获取，若系统未启动则返回 `0`。

---

### 2. 用户统计数据

**GET** `/api/v1/m/stats/users`

返回用户注册、活跃趋势等统计数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| days | integer | 否 | `7` | 统计天数（1-90） |

#### 请求示例

```
GET /api/v1/m/stats/users?days=30
```

#### 响应示例

```json
{
  "total_users": 1250,
  "user_type_dist": {
    "customer": 1200,
    "admin": 50
  },
  "status_dist": {
    "active": 1230,
    "disabled": 20
  },
  "daily_new_users": [
    {"date": "2026-02-15", "count": 8},
    {"date": "2026-02-16", "count": 12},
    {"date": "2026-02-17", "count": 5},
    {"date": "2026-02-18", "count": 15},
    {"date": "2026-02-19", "count": 10},
    {"date": "2026-02-20", "count": 9},
    {"date": "2026-02-21", "count": 12}
  ],
  "days": 7
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| total_users | integer | 总用户数（已启用） |
| user_type_dist | object | 用户类型分布（键为用户类型，值为数量） |
| status_dist | object | 用户状态分布（键为状态，值为数量） |
| daily_new_users | array[object] | 每日新增用户趋势 |
| daily_new_users[].date | string | 日期（YYYY-MM-DD格式） |
| daily_new_users[].count | integer | 当日新增用户数 |
| days | integer | 统计天数 |

---

### 3. 策略统计数据

**GET** `/api/v1/m/stats/strategies`

返回策略运行状态、信号产生等统计数据。

#### 响应示例

```json
{
  "total_strategies": 8,
  "state_dist": {
    "running": 3,
    "stopped": 4,
    "paused": 1
  },
  "strategies": [
    {
      "strategy_id": "strategy_uuid_1",
      "name": "BTC均线策略",
      "state": "running",
      "symbols": ["BTCUSDT"]
    },
    {
      "strategy_id": "strategy_uuid_2",
      "name": "ETH动量策略",
      "state": "stopped",
      "symbols": ["ETHUSDT"]
    }
  ],
  "signal_by_strategy": [
    {
      "strategy_id": "strategy_uuid_1",
      "strategy_name": "BTC均线策略",
      "signal_count": 320
    },
    {
      "strategy_id": "strategy_uuid_2",
      "strategy_name": "ETH动量策略",
      "signal_count": 180
    }
  ],
  "signal_type_dist": {
    "buy": 250,
    "sell": 230,
    "close": 20
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| total_strategies | integer | 总策略数 |
| state_dist | object | 策略状态分布（键为状态，值为数量） |
| strategies | array[object] | 策略列表（最多20条，从策略引擎获取） |
| strategies[].strategy_id | string | 策略ID |
| strategies[].name | string | 策略名称 |
| strategies[].state | string | 策略状态 |
| strategies[].symbols | array[string] | 监控的交易对列表 |
| signal_by_strategy | array[object] | 各策略信号数量（按信号数量降序，最多20条） |
| signal_by_strategy[].strategy_id | string | 策略ID |
| signal_by_strategy[].strategy_name | string | 策略名称 |
| signal_by_strategy[].signal_count | integer | 信号总数 |
| signal_type_dist | object | 信号类型分布（键为信号类型，值为数量） |

> **注意**：`total_strategies`、`state_dist` 和 `strategies` 字段从交易引擎实时获取，若系统未启动则返回空值。`signal_by_strategy` 和 `signal_type_dist` 从数据库查询。

---

### 4. 交易统计数据

**GET** `/api/v1/m/stats/trading`

返回订单、成交、持仓等交易统计数据。

#### 响应示例

```json
{
  "active_orders": 5,
  "total_positions": 3,
  "total_equity": 100000.0,
  "account_info": {
    "total_balance": 100000.0,
    "available_balance": 95000.0,
    "margin_balance": 5000.0
  },
  "signals_executed_today": 12,
  "timestamp": "2026-02-21T02:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| active_orders | integer | 活跃订单数（从交易引擎获取） |
| total_positions | integer | 持仓数量（从交易引擎获取） |
| total_equity | float | 总资产（从账户信息获取） |
| account_info | object | 账户信息 |
| account_info.total_balance | float | 总余额 |
| account_info.available_balance | float | 可用余额 |
| account_info.margin_balance | float | 保证金余额 |
| signals_executed_today | integer | 今日已执行信号数（从数据库查询） |
| timestamp | string | 统计时间（ISO 8601格式） |

> **注意**：`active_orders`、`total_positions`、`total_equity` 和 `account_info` 从交易引擎实时获取，若系统未启动则返回 `0` 或空对象。

---

### 5. 行情数据统计

**GET** `/api/v1/m/stats/market`

返回行情订阅、K线数据量等统计数据。

#### 响应示例

```json
{
  "subscribed_symbols": 10,
  "subscriptions_count": 5,
  "running_subscriptions": 3,
  "kline_records_total": 1500000,
  "market_service_stats": {
    "total_ticks": 500000,
    "total_bars": 50000,
    "connected_collectors": 2,
    "uptime_seconds": 86400
  },
  "timestamp": "2026-02-21T02:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| subscribed_symbols | integer | 已订阅交易对数量（从行情服务获取） |
| subscriptions_count | integer | 订阅配置总数（从数据库查询） |
| running_subscriptions | integer | 运行中订阅数量（从数据库查询） |
| kline_records_total | integer | K线记录总数（从 TimescaleDB 查询，查询失败时为 0） |
| market_service_stats | object | 行情服务统计信息（从行情服务获取） |
| timestamp | string | 统计时间（ISO 8601格式） |

> **注意**：`subscribed_symbols` 和 `market_service_stats` 从行情服务实时获取，若系统未启动则返回 `0` 或空对象。`kline_records_total` 需要 TimescaleDB 连接，若连接失败则返回 `0`。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 503 | 交易系统未启动（部分字段依赖系统运行） |

## 数据来源说明

统计数据来自多个数据源，各接口的数据来源如下：

| 接口 | 数据库数据 | 实时引擎数据 |
|------|-----------|-------------|
| `/overview` | 用户数、信号数、订阅数 | 策略数、WebSocket连接数 |
| `/users` | 用户注册趋势、类型分布 | - |
| `/strategies` | 信号数量统计 | 策略状态、策略列表 |
| `/trading` | 今日执行信号数 | 订单数、持仓数、账户信息 |
| `/market` | 订阅配置数 | 已订阅交易对数、行情服务统计、K线总数 |

> **提示**：当交易系统未启动时，依赖实时引擎的字段将返回默认值（`0` 或空对象 `{}`），不会返回错误。
