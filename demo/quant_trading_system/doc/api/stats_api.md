# 统计分析 API 文档

## 概述

统计分析模块提供系统运行统计数据的查询接口，供管理员监控系统整体状态，包括用户统计、策略统计、交易统计、行情数据统计等。

## 基础信息

- **基础URL**: `/api/v1/m/stats`
- **认证方式**: JWT Bearer Token（管理员权限）
- **数据格式**: JSON

> **注意**：部分接口依赖交易系统运行（编排器实例），若系统未启动，相关字段可能返回默认值。

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

返回系统核心指标的汇总数据，包括用户数、策略数、信号数、订阅数、WebSocket 连接数等。

#### 请求参数

无

#### 响应示例

```json
{
  "total_users": 150,
  "active_users_today": 32,
  "new_users_today": 5,
  "total_strategies": 8,
  "running_strategies": 3,
  "total_signals": 1024,
  "signals_today": 45,
  "subscriptions": 12,
  "ws_connections": 6,
  "ws_channel_stats": {
    "market": 3,
    "trading": 2,
    "strategy": 1
  },
  "timestamp": "2025-02-25T12:00:00.000000"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| total_users | integer | 总用户数（启用状态） |
| active_users_today | integer | 今日活跃用户数（今日有登录记录） |
| new_users_today | integer | 今日新增用户数 |
| total_strategies | integer | 总策略数（编排器中加载的策略） |
| running_strategies | integer | 运行中策略数 |
| total_signals | integer | 总信号记录数 |
| signals_today | integer | 今日信号数 |
| subscriptions | integer | 订阅配置数量 |
| ws_connections | integer | 当前 WebSocket 连接数 |
| ws_channel_stats | object | WebSocket 各频道连接统计 |
| timestamp | string | 统计时间（ISO格式） |

---

### 2. 用户统计数据

**GET** `/api/v1/m/stats/users`

返回用户注册、活跃趋势等统计数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| days | integer | 否 | `7` | 统计天数（1-90） |

#### 响应示例

```json
{
  "total_users": 150,
  "user_type_dist": {
    "normal": 140,
    "admin": 10
  },
  "status_dist": {
    "active": 145,
    "inactive": 5
  },
  "daily_new_users": [
    {"date": "2025-02-19", "count": 3},
    {"date": "2025-02-20", "count": 5},
    {"date": "2025-02-21", "count": 2},
    {"date": "2025-02-22", "count": 4},
    {"date": "2025-02-23", "count": 1},
    {"date": "2025-02-24", "count": 6},
    {"date": "2025-02-25", "count": 5}
  ],
  "days": 7
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| total_users | integer | 总用户数（启用状态） |
| user_type_dist | object | 用户类型分布（类型 → 数量） |
| status_dist | object | 用户状态分布（状态 → 数量） |
| daily_new_users | array | 每日新增用户趋势列表 |
| daily_new_users[].date | string | 日期（YYYY-MM-DD） |
| daily_new_users[].count | integer | 当日新增用户数 |
| days | integer | 统计天数 |

---

### 3. 策略统计数据

**GET** `/api/v1/m/stats/strategies`

返回策略运行状态、信号产生等统计数据。

#### 请求参数

无

#### 响应示例

```json
{
  "total_strategies": 8,
  "state_dist": {
    "running": 3,
    "stopped": 4,
    "error": 1
  },
  "strategies": [
    {
      "strategy_id": "ma_cross_001",
      "name": "MA Cross",
      "state": "running",
      "symbols": ["BTCUSDT", "ETHUSDT"]
    }
  ],
  "signal_by_strategy": [
    {
      "strategy_id": "ma_cross_001",
      "strategy_name": "MA Cross",
      "signal_count": 256
    }
  ],
  "signal_type_dist": {
    "buy": 520,
    "sell": 504
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| total_strategies | integer | 总策略数 |
| state_dist | object | 策略状态分布（状态 → 数量） |
| strategies | array | 策略详情列表 |
| strategies[].strategy_id | string | 策略唯一标识 |
| strategies[].name | string | 策略名称 |
| strategies[].state | string | 策略状态（running/stopped/error等） |
| strategies[].symbols | array | 策略关注的交易对列表 |
| signal_by_strategy | array | 各策略信号数量排行（Top 20） |
| signal_by_strategy[].strategy_id | string | 策略ID |
| signal_by_strategy[].strategy_name | string | 策略名称 |
| signal_by_strategy[].signal_count | integer | 信号总数 |
| signal_type_dist | object | 信号类型分布（类型 → 数量） |

---

### 4. 交易统计数据

**GET** `/api/v1/m/stats/trading`

返回订单、持仓、账户资产等交易统计数据。

#### 请求参数

无

#### 响应示例

```json
{
  "active_orders": 5,
  "total_positions": 3,
  "total_equity": 1050000.0,
  "account_info": {
    "total_balance": 1050000.0,
    "available_balance": 800000.0,
    "margin_balance": 250000.0
  },
  "signals_executed_today": 12,
  "timestamp": "2025-02-25T12:00:00.000000"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| active_orders | integer | 当前活跃订单数 |
| total_positions | integer | 当前持仓数量 |
| total_equity | float | 总资产（账户总余额） |
| account_info | object | 账户详细信息 |
| account_info.total_balance | float | 账户总余额 |
| account_info.available_balance | float | 可用余额 |
| account_info.margin_balance | float | 保证金余额 |
| signals_executed_today | integer | 今日已执行信号数 |
| timestamp | string | 统计时间（ISO格式） |

---

### 5. 行情数据统计

**GET** `/api/v1/m/stats/market`

返回行情订阅、K线数据量等统计数据。

#### 请求参数

无

#### 响应示例

```json
{
  "subscribed_symbols": 15,
  "subscriptions_count": 12,
  "running_subscriptions": 8,
  "kline_records_total": 5000000,
  "market_service_stats": {},
  "timestamp": "2025-02-25T12:00:00.000000"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| subscribed_symbols | integer | 已订阅交易对数量 |
| subscriptions_count | integer | 订阅配置总数量 |
| running_subscriptions | integer | 运行中的订阅数量 |
| kline_records_total | integer | K线记录总数（TimescaleDB） |
| market_service_stats | object | 行情服务运行统计 |
| timestamp | string | 统计时间（ISO格式） |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证或Token无效 |
| 403 | 无管理员权限 |
| 503 | 交易系统未启动（编排器不可用） |
| 500 | 服务器内部错误 |
