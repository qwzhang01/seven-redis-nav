# 策略管理 API 文档

## 概述

策略管理模块提供策略的完整生命周期管理接口，支持策略创建、启动、停止、暂停、恢复、参数更新、删除以及信号历史查询等功能。

## 基础信息

- **基础URL**: `/api/v1/m/strategy`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有策略管理接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

> **注意**：策略管理接口依赖交易系统运行，若系统未启动将返回 `503` 错误。

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/strategy/list` | 获取策略列表 |
| GET | `/api/v1/m/strategy/types` | 获取可用策略类型 |
| POST | `/api/v1/m/strategy/create` | 创建策略 |
| GET | `/api/v1/m/strategy/{strategy_id}` | 获取策略详情 |
| PUT | `/api/v1/m/strategy/{strategy_id}` | 更新策略参数 |
| DELETE | `/api/v1/m/strategy/{strategy_id}` | 删除策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/resume` | 恢复策略 |
| GET | `/api/v1/m/strategy/{strategy_id}/signals` | 获取策略信号历史 |

---

## 接口详情

### 1. 获取策略列表

**GET** `/api/v1/m/strategy/list`

查询系统中所有已创建的策略基本信息列表。

#### 响应示例

```json
{
  "strategies": [
    {
      "strategy_id": "strategy_uuid_1",
      "name": "BTC均线策略",
      "state": "running",
      "symbols": ["BTCUSDT"],
      "timeframes": ["1h"]
    },
    {
      "strategy_id": "strategy_uuid_2",
      "name": "ETH动量策略",
      "state": "stopped",
      "symbols": ["ETHUSDT"],
      "timeframes": ["15m", "1h"]
    }
  ],
  "total": 2
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategies | array[object] | 策略信息列表 |
| strategies[].strategy_id | string | 策略唯一标识 |
| strategies[].name | string | 策略名称 |
| strategies[].state | string | 策略状态（running/stopped/paused） |
| strategies[].symbols | array[string] | 监控的交易对列表 |
| strategies[].timeframes | array[string] | 使用的时间周期列表 |
| total | integer | 策略总数 |

---

### 2. 获取可用策略类型

**GET** `/api/v1/m/strategy/types`

查询系统中所有已注册的策略类型及其配置信息。

#### 响应示例

```json
{
  "types": [
    {
      "name": "ma_cross",
      "description": "均线交叉策略：当快速均线上穿慢速均线时买入，下穿时卖出",
      "params": {
        "fast_period": {
          "type": "int",
          "default": 10,
          "description": "快速均线周期"
        },
        "slow_period": {
          "type": "int",
          "default": 30,
          "description": "慢速均线周期"
        }
      },
      "timeframes": ["1m", "5m", "15m", "1h"]
    }
  ]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| types | array[object] | 策略类型信息列表 |
| types[].name | string | 策略类型名称 |
| types[].description | string | 策略描述 |
| types[].params | object | 策略参数定义（键为参数名，值为参数描述） |
| types[].params[参数名].type | string | 参数类型（int/float/str/bool） |
| types[].params[参数名].default | any | 参数默认值 |
| types[].params[参数名].description | string | 参数描述 |
| types[].timeframes | array[string] | 支持的时间周期列表 |

---

### 3. 创建策略

**POST** `/api/v1/m/strategy/create`

根据指定的策略类型和参数创建新的策略实例。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 策略名称（用户自定义） |
| strategy_type | string | 是 | 策略类型名称（系统注册的策略类型） |
| symbols | array[string] | 是 | 策略监控的交易对列表 |
| params | object | 否 | 策略参数配置字典，默认为空 |

```json
{
  "name": "BTC均线策略",
  "strategy_type": "ma_cross",
  "symbols": ["BTCUSDT"],
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
  "strategy_id": "strategy_uuid",
  "message": "Strategy created"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| strategy_id | string | 新创建的策略ID |
| message | string | 操作结果描述 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 未知的策略类型 |
| 503 | 交易系统未启动 |

---

### 4. 获取策略详情

**GET** `/api/v1/m/strategy/{strategy_id}`

查询指定策略的详细信息和运行状态。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "strategy_id": "strategy_uuid",
  "name": "BTC均线策略",
  "state": "running",
  "params": {
    "fast_period": 10,
    "slow_period": 30
  },
  "symbols": ["BTCUSDT"],
  "timeframes": ["1h"],
  "stats": {
    "signal_count": 42
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategy_id | string | 策略ID |
| name | string | 策略名称 |
| state | string | 策略状态（running/stopped/paused） |
| params | object | 策略参数配置 |
| symbols | array[string] | 监控的交易对列表 |
| timeframes | array[string] | 使用的时间周期列表 |
| stats | object | 策略统计信息 |
| stats.signal_count | integer | 已生成的信号总数 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 5. 更新策略参数

**PUT** `/api/v1/m/strategy/{strategy_id}`

更新指定策略的参数配置。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| params | object | 否 | 要更新的策略参数字典（合并更新） |

```json
{
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
  "strategy_id": "strategy_uuid",
  "message": "Strategy updated"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 6. 删除策略

**DELETE** `/api/v1/m/strategy/{strategy_id}`

从系统中删除指定的策略实例。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy deleted"
}
```

---

### 7. 启动策略

**POST** `/api/v1/m/strategy/{strategy_id}/start`

启动指定的策略实例，开始接收行情数据并生成交易信号。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy started"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 8. 停止策略

**POST** `/api/v1/m/strategy/{strategy_id}/stop`

停止指定的策略实例，不再接收行情数据和生成交易信号。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy stopped"
}
```

---

### 9. 暂停策略

**POST** `/api/v1/m/strategy/{strategy_id}/pause`

暂停指定的策略实例，暂时停止生成交易信号但保持订阅行情数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy paused"
}
```

---

### 10. 恢复策略

**POST** `/api/v1/m/strategy/{strategy_id}/resume`

恢复之前暂停的策略实例，重新开始生成交易信号。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy resumed"
}
```

---

### 11. 获取策略信号历史

**GET** `/api/v1/m/strategy/{strategy_id}/signals`

查询指定策略生成的交易信号历史记录。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回信号数量限制（1-1000） |

#### 响应示例

```json
{
  "strategy_id": "strategy_uuid",
  "signals": [],
  "total": 0
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategy_id | string | 策略ID |
| signals | array | 信号历史记录列表 |
| total | integer | 总信号数量 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如未知策略类型） |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 404 | 策略不存在 |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 503 | 交易系统未启动，请先启动系统后再调用 |

## 策略状态说明

| 状态 | 描述 |
|------|------|
| running | 策略运行中，正在接收行情并生成信号 |
| stopped | 策略已停止，不接收行情也不生成信号 |
| paused | 策略已暂停，继续接收行情但不生成信号 |

## 策略状态流转

```
stopped ──start──▶ running ──pause──▶ paused
   ▲                  │                  │
   └──────stop────────┘◀───resume────────┘
                       │
                    stop▼
                  stopped
```

| 当前状态 | 可执行操作 |
|----------|-----------|
| stopped | start |
| running | stop、pause |
| paused | stop、resume |
