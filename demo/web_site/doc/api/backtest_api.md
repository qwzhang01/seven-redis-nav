# 回测 API 文档

## 概述

回测模块提供策略回测相关的 API 接口，支持回测执行、结果查询、权益曲线和交易记录获取、历史记录管理等功能。

## 基础信息

- **基础URL**: `/api/v1/c/backtest`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **注意**：回测接口依赖交易系统运行，若系统未启动将返回 `503` 错误。

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/backtest/run` | 运行策略回测 |
| GET | `/api/v1/c/backtest/list` | 获取回测历史列表 |
| GET | `/api/v1/c/backtest/{backtest_id}` | 获取回测结果 |
| GET | `/api/v1/c/backtest/{backtest_id}/equity` | 获取回测权益曲线 |
| GET | `/api/v1/c/backtest/{backtest_id}/trades` | 获取回测交易记录 |
| DELETE | `/api/v1/c/backtest/{backtest_id}` | 删除回测记录 |

---

## 接口详情

### 1. 运行策略回测

**POST** `/api/v1/c/backtest/run`

执行指定策略的回测，异步运行，返回回测任务ID。回测引擎会从数据库获取历史数据并执行策略回测。

#### 请求体（BacktestRequest）

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_type | string | 是 | - | 策略类型名称 |
| symbol | string | 是 | - | 交易标的符号 |
| timeframe | string | 否 | `"1m"` | K线时间周期，可选值：`1m`、`5m`、`15m`、`30m`、`1h`、`4h`、`1d`、`1w` |
| start_time | string | 是 | - | 回测开始时间（ISO格式） |
| end_time | string | 是 | - | 回测结束时间（ISO格式） |
| initial_capital | float | 否 | `1000000.0` | 初始资金 |
| commission_rate | float | 否 | `0.0004` | 手续费率 |
| slippage_rate | float | 否 | `0.0001` | 滑点率 |
| params | object | 否 | `{}` | 策略参数配置字典 |

#### 请求示例

```json
{
  "strategy_type": "ma_cross",
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "start_time": "2025-01-01T00:00:00Z",
  "end_time": "2025-02-01T00:00:00Z",
  "initial_capital": 1000000.0,
  "commission_rate": 0.0004,
  "slippage_rate": 0.0001,
  "params": {
    "fast_period": 5,
    "slow_period": 20
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "backtest_id": "backtest_123456789",
  "message": "Backtest started successfully"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 未知策略类型 / 无效时间周期 / 无效时间格式 / 开始时间晚于或等于结束时间 |
| 500 | 回测执行失败 |

---

### 2. 获取回测历史列表

**GET** `/api/v1/c/backtest/list`

查询所有历史回测任务的简要信息列表。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `20` | 返回数量限制（1-100） |

#### 响应示例

```json
{
  "backtests": [
    {
      "backtest_id": "backtest_123456789",
      "status": "completed",
      "strategy_name": "ma_cross",
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2025-02-01T00:00:00Z",
      "total_return": 15.5,
      "total_trades": 42
    }
  ],
  "total": 1
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| backtests | array | 回测任务列表 |
| backtests[].backtest_id | string | 回测任务唯一标识 |
| backtests[].status | string | 回测状态：`completed` / `failed` |
| backtests[].strategy_name | string | 策略名称 |
| backtests[].start_time | string | 回测开始时间 |
| backtests[].end_time | string | 回测结束时间 |
| backtests[].total_return | float | 总收益率 |
| backtests[].total_trades | integer | 总交易次数 |
| total | integer | 总回测任务数 |

---

### 3. 获取回测结果

**GET** `/api/v1/c/backtest/{backtest_id}`

查询指定回测ID的详细结果和统计指标。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务唯一标识 |

#### 响应示例（回测完成）

```json
{
  "backtest_id": "backtest_123456789",
  "status": "completed",
  "result": {
    "total_return": 15.5,
    "max_drawdown": -5.2,
    "sharpe_ratio": 1.8,
    "total_trades": 42
  }
}
```

#### 响应示例（回测运行中）

```json
{
  "backtest_id": "backtest_123456789",
  "status": "running",
  "result": null,
  "message": "Backtest is still running"
}
```

#### 响应示例（回测失败）

```json
{
  "backtest_id": "backtest_123456789",
  "status": "failed",
  "result": null,
  "error": "错误信息描述"
}
```

#### 状态说明

| 状态 | 描述 |
|------|------|
| running | 回测正在执行中（实例存在但尚无结果） |
| completed | 回测已完成 |
| failed | 回测执行失败 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 回测任务不存在 |

---

### 4. 获取回测权益曲线

**GET** `/api/v1/c/backtest/{backtest_id}/equity`

查询回测过程中的权益变化曲线数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务唯一标识 |

#### 响应示例

```json
{
  "backtest_id": "backtest_123456789",
  "equity_curve": [
    {"timestamp": 1708000000, "equity": 1000000.0},
    {"timestamp": 1708003600, "equity": 1005000.0}
  ]
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 回测执行失败，无法获取权益曲线 |
| 404 | 回测任务不存在 |

---

### 5. 获取回测交易记录

**GET** `/api/v1/c/backtest/{backtest_id}/trades`

查询回测过程中产生的所有交易记录。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务唯一标识 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回数量限制（1-1000） |

#### 响应示例

```json
{
  "backtest_id": "backtest_123456789",
  "trades": [
    {
      "timestamp": 1708000000,
      "side": "buy",
      "price": 42000.0,
      "quantity": 0.1,
      "pnl": 150.0
    }
  ],
  "total": 42
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 回测执行失败，无法获取交易记录 |
| 404 | 回测任务不存在 |

---

### 6. 删除回测记录

**DELETE** `/api/v1/c/backtest/{backtest_id}`

删除指定的回测任务记录。同时清除回测实例和回测结果数据。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "backtest_id": "backtest_123456789",
  "message": "Backtest deleted successfully"
}
```

> **注意**：即使指定的 backtest_id 不存在，该接口也会返回成功，不会报错。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（无效策略类型/时间周期/时间格式）或回测失败 |
| 404 | 回测任务不存在 |
| 500 | 服务器内部错误 |
