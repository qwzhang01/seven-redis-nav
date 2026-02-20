# 策略回测 API 文档

## 概述

回测模块提供策略回测相关的 API 接口，支持回测执行、结果查询、权益曲线获取、交易记录查询和历史记录管理等功能。

## 基础信息

- **基础URL**: `/api/v1/c/backtest`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有回测接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

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

执行指定策略的回测，异步运行并返回回测任务ID。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_type | string | 是 | - | 策略类型名称（系统注册的策略类型） |
| symbol | string | 是 | - | 交易标的符号，如 `BTCUSDT` |
| timeframe | string | 否 | `"1m"` | K线时间周期 |
| start_time | string | 是 | - | 回测开始时间（ISO 8601格式） |
| end_time | string | 是 | - | 回测结束时间（ISO 8601格式） |
| initial_capital | float | 否 | `1000000.0` | 初始资金 |
| commission_rate | float | 否 | `0.0004` | 手续费率（默认 0.04%） |
| slippage_rate | float | 否 | `0.0001` | 滑点率（默认 0.01%） |
| params | object | 否 | `{}` | 策略参数配置字典 |

**timeframe 枚举值：**

| 值 | 描述 |
|----|------|
| `1m` | 1 分钟 |
| `5m` | 5 分钟 |
| `15m` | 15 分钟 |
| `30m` | 30 分钟 |
| `1h` | 1 小时 |
| `4h` | 4 小时 |
| `1d` | 1 天 |
| `1w` | 1 周 |

```json
{
  "strategy_type": "ma_cross",
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "start_time": "2025-01-01T00:00:00Z",
  "end_time": "2026-01-01T00:00:00Z",
  "initial_capital": 1000000.0,
  "commission_rate": 0.0004,
  "slippage_rate": 0.0001,
  "params": {
    "fast_period": 10,
    "slow_period": 30
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "backtest_id": "backtest_a1b2c3d4",
  "message": "Backtest started successfully"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| backtest_id | string | 回测任务唯一标识 |
| message | string | 操作结果描述 |

> **说明**：回测为异步执行，提交后立即返回 `backtest_id`，可通过 `GET /backtest/{backtest_id}` 轮询查询结果。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 参数错误（如未知策略类型、无效时间周期、开始时间晚于结束时间） |
| 500 | 回测启动失败 |

---

### 2. 获取回测历史列表

**GET** `/api/v1/c/backtest/list`

查询所有历史回测任务的简要信息列表。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `20` | 返回记录数量限制（1-100） |

#### 请求示例

```
GET /api/v1/c/backtest/list?limit=10
```

#### 响应示例

```json
{
  "backtests": [
    {
      "backtest_id": "backtest_a1b2c3d4",
      "status": "completed",
      "strategy_name": "ma_cross",
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2026-01-01T00:00:00Z",
      "total_return": 0.235,
      "total_trades": 128
    },
    {
      "backtest_id": "backtest_e5f6g7h8",
      "status": "failed",
      "strategy_name": "Unknown",
      "start_time": null,
      "end_time": null,
      "total_return": 0,
      "total_trades": 0
    }
  ],
  "total": 2
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| backtests | array[object] | 回测任务列表 |
| backtests[].backtest_id | string | 回测任务ID |
| backtests[].status | string | 回测状态：completed/running/failed |
| backtests[].strategy_name | string | 策略名称 |
| backtests[].start_time | string\|null | 回测开始时间 |
| backtests[].end_time | string\|null | 回测结束时间 |
| backtests[].total_return | float | 总收益率 |
| backtests[].total_trades | integer | 总交易次数 |
| total | integer | 总回测任务数 |

---

### 3. 获取回测结果

**GET** `/api/v1/c/backtest/{backtest_id}`

查询指定回测ID的详细结果和统计指标。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| backtest_id | string | 是 | 回测任务唯一标识 |

#### 响应示例（已完成）

```json
{
  "backtest_id": "backtest_a1b2c3d4",
  "status": "completed",
  "result": {
    "strategy_name": "ma_cross",
    "start_time": "2025-01-01T00:00:00Z",
    "end_time": "2026-01-01T00:00:00Z",
    "initial_capital": 1000000.0,
    "final_capital": 1235000.0,
    "total_return": 0.235,
    "annualized_return": 0.235,
    "max_drawdown": 0.08,
    "sharpe_ratio": 1.85,
    "win_rate": 0.62,
    "total_trades": 128,
    "profit_trades": 79,
    "loss_trades": 49
  }
}
```

#### 响应示例（运行中）

```json
{
  "backtest_id": "backtest_a1b2c3d4",
  "status": "running",
  "result": null,
  "message": "Backtest is still running"
}
```

#### 响应示例（失败）

```json
{
  "backtest_id": "backtest_a1b2c3d4",
  "status": "failed",
  "result": null,
  "error": "数据库中无对应时间段的K线数据"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务ID |
| status | string | 回测状态：completed/running/failed |
| result | object\|null | 回测结果统计指标（运行中或失败时为 null） |
| result.initial_capital | float | 初始资金 |
| result.final_capital | float | 最终资金 |
| result.total_return | float | 总收益率 |
| result.annualized_return | float | 年化收益率 |
| result.max_drawdown | float | 最大回撤 |
| result.sharpe_ratio | float | 夏普比率 |
| result.win_rate | float | 胜率 |
| result.total_trades | integer | 总交易次数 |
| result.profit_trades | integer | 盈利交易次数 |
| result.loss_trades | integer | 亏损交易次数 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 回测任务不存在 |

---

### 4. 获取回测权益曲线

**GET** `/api/v1/c/backtest/{backtest_id}/equity`

查询回测过程中的权益变化曲线数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| backtest_id | string | 是 | 回测任务唯一标识 |

#### 响应示例

```json
{
  "backtest_id": "backtest_a1b2c3d4",
  "equity_curve": [
    {"timestamp": "2025-01-01T00:00:00Z", "equity": 1000000.0},
    {"timestamp": "2025-02-01T00:00:00Z", "equity": 1050000.0},
    {"timestamp": "2025-03-01T00:00:00Z", "equity": 1020000.0},
    {"timestamp": "2026-01-01T00:00:00Z", "equity": 1235000.0}
  ]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务ID |
| equity_curve | array[object] | 权益曲线数据列表 |
| equity_curve[].timestamp | string | 时间戳 |
| equity_curve[].equity | float | 当时的账户权益 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 回测失败，无法获取权益曲线 |
| 404 | 回测任务不存在 |

---

### 5. 获取回测交易记录

**GET** `/api/v1/c/backtest/{backtest_id}/trades`

查询回测过程中产生的所有交易记录。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| backtest_id | string | 是 | 回测任务唯一标识 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回记录数量限制（1-1000） |

#### 请求示例

```
GET /api/v1/c/backtest/backtest_a1b2c3d4/trades?limit=50
```

#### 响应示例

```json
{
  "backtest_id": "backtest_a1b2c3d4",
  "trades": [
    {
      "trade_id": "trade_001",
      "symbol": "BTCUSDT",
      "side": "buy",
      "price": 50000.0,
      "quantity": 0.1,
      "timestamp": "2025-01-15T10:00:00Z",
      "commission": 2.0,
      "pnl": 500.0
    }
  ],
  "total": 128
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| backtest_id | string | 回测任务ID |
| trades | array[object] | 交易记录列表 |
| total | integer | 总交易记录数 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 回测失败，无法获取交易记录 |
| 404 | 回测任务不存在 |

---

### 6. 删除回测记录

**DELETE** `/api/v1/c/backtest/{backtest_id}`

删除指定的回测任务记录（包括结果数据）。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| backtest_id | string | 是 | 回测任务唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "backtest_id": "backtest_a1b2c3d4",
  "message": "Backtest deleted successfully"
}
```

> **说明**：若指定的回测任务不存在，接口仍返回成功（幂等操作）。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如未知策略类型、无效时间周期、回测失败等） |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 404 | 回测任务不存在 |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 500 | 服务器内部错误（回测启动失败） |

## 回测状态说明

| 状态 | 描述 |
|------|------|
| running | 回测正在执行中 |
| completed | 回测已完成，可查询结果 |
| failed | 回测执行失败，可查看错误信息 |

## 使用示例

### Python客户端示例

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1/c/backtest"

def run_backtest(token, strategy_type, symbol, start_time, end_time, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "strategy_type": strategy_type,
        "symbol": symbol,
        "timeframe": "1h",
        "start_time": start_time,
        "end_time": end_time,
        "initial_capital": 1000000.0,
        "params": params or {}
    }
    response = requests.post(f"{BASE_URL}/run", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["backtest_id"]
    else:
        raise Exception(f"启动回测失败: {response.text}")

def wait_for_result(token, backtest_id, timeout=300):
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f"{BASE_URL}/{backtest_id}", headers=headers)
        data = response.json()
        if data["status"] == "completed":
            return data["result"]
        elif data["status"] == "failed":
            raise Exception(f"回测失败: {data.get('error')}")
        time.sleep(2)
    raise TimeoutError("回测超时")

# 使用示例
if __name__ == "__main__":
    token = "your_jwt_token"
    
    # 启动回测
    backtest_id = run_backtest(
        token,
        strategy_type="ma_cross",
        symbol="BTCUSDT",
        start_time="2025-01-01T00:00:00Z",
        end_time="2026-01-01T00:00:00Z",
        params={"fast_period": 10, "slow_period": 30}
    )
    print(f"回测已启动，ID: {backtest_id}")
    
    # 等待结果
    result = wait_for_result(token, backtest_id)
    print(f"回测完成！总收益率: {result['total_return']:.2%}")
    print(f"最大回撤: {result['max_drawdown']:.2%}")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
```
