# 统计分析 API 文档

## 概述

统计分析模块提供系统运行统计数据的查询接口，供管理员监控系统状态。包括系统概览、用户统计、策略统计、交易统计和行情数据统计。

## 基础信息

- **基础URL**: `/api/v1/m/stats`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **权限要求**：所有统计接口均需要管理员权限。

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

返回系统核心指标的汇总数据。

#### 响应示例

```json
{
  "total_users": 100,
  "active_users_today": 25,
  "new_users_today": 5,
  "total_strategies": 10,
  "running_strategies": 3,
  "total_signals": 500,
  "signals_today": 15,
  "subscriptions": 20,
  "ws_connections": 8,
  "ws_channel_stats": {...},
  "timestamp": "2025-02-24T19:00:00Z"
}
```

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
  "total_users": 100,
  "user_type_dist": {"customer": 95, "admin": 5},
  "status_dist": {"active": 90, "inactive": 8, "locked": 2},
  "daily_new_users": [
    {"date": "2025-02-18", "count": 3},
    {"date": "2025-02-19", "count": 5}
  ],
  "days": 7
}
```

---

### 3. 策略统计数据

**GET** `/api/v1/m/stats/strategies`

返回策略运行状态、信号产生等统计数据。

#### 响应示例

```json
{
  "total_strategies": 10,
  "state_dist": {"running": 3, "stopped": 5, "paused": 2},
  "strategies": [...],
  "signal_by_strategy": [
    {"strategy_id": "strategy_001", "strategy_name": "BTC均线策略", "signal_count": 150}
  ],
  "signal_type_dist": {"buy": 200, "sell": 180, "close": 120}
}
```

---

### 4. 交易统计数据

**GET** `/api/v1/m/stats/trading`

返回订单、成交、持仓等交易统计数据。

#### 响应示例

```json
{
  "active_orders": 5,
  "total_positions": 3,
  "total_equity": 150000.0,
  "account_info": {
    "total_balance": 150000.0,
    "available_balance": 140000.0,
    "margin_balance": 150000.0
  },
  "signals_executed_today": 8,
  "timestamp": "2025-02-24T19:00:00Z"
}
```

---

### 5. 行情数据统计

**GET** `/api/v1/m/stats/market`

返回行情订阅、K线数据量等统计数据。

#### 响应示例

```json
{
  "subscribed_symbols": 15,
  "subscriptions_count": 5,
  "running_subscriptions": 3,
  "kline_records_total": 1500000,
  "market_service_stats": {...},
  "timestamp": "2025-02-24T19:00:00Z"
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证 |
| 403 | 权限不足（需管理员权限） |
| 503 | 交易系统未启动（影响部分统计数据） |
