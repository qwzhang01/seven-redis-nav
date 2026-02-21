# 策略管理 API 文档

## 概述

策略管理模块提供策略的完整生命周期管理接口，支持策略创建、启动、停止、暂停、恢复、参数更新、删除以及信号历史查询等功能。分为 M 端（管理员）和 C 端（普通用户）两套接口。

## 基础信息

- **M端基础URL**: `/api/v1/m/strategy`
- **C端基础URL**: `/api/v1/c/strategy`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有策略管理接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

> **注意**：策略管理接口依赖交易系统运行，若系统未启动将返回 `503` 错误。

---

## M 端接口列表（管理员）

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
| POST | `/api/v1/m/strategy/{strategy_id}/publish` | 发布策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/unpublish` | 下架策略 |
| GET | `/api/v1/m/strategy/{strategy_id}/performance` | 获取策略性能指标 |
| GET | `/api/v1/m/strategy/{strategy_id}/signals` | 获取策略信号历史 |

---

## C 端接口列表（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/strategy/featured` | 获取首页优选策略 |
| GET | `/api/v1/c/strategy/types` | 获取可用策略类型 |
| GET | `/api/v1/c/strategy/list` | 获取当前用户的策略列表 |
| POST | `/api/v1/c/strategy/create` | 创建实盘策略 |
| POST | `/api/v1/c/strategy/simulate` | 创建模拟交易策略 |
| GET | `/api/v1/c/strategy/{strategy_id}` | 获取策略详情 |
| PUT | `/api/v1/c/strategy/{strategy_id}` | 更新策略参数 |
| DELETE | `/api/v1/c/strategy/{strategy_id}` | 删除策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/resume` | 恢复策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/subscribe` | 订阅策略 |
| DELETE | `/api/v1/c/strategy/{strategy_id}/subscribe` | 取消订阅策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/favorite` | 收藏策略 |
| DELETE | `/api/v1/c/strategy/{strategy_id}/favorite` | 取消收藏策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/like` | 点赞策略 |
| DELETE | `/api/v1/c/strategy/{strategy_id}/like` | 取消点赞策略 |
| GET | `/api/v1/c/strategy/{strategy_id}/performance` | 获取策略性能指标 |
| GET | `/api/v1/c/strategy/{strategy_id}/signals` | 获取策略信号历史 |

---

## M 端接口详情

### 1. 获取策略列表

**GET** `/api/v1/m/strategy/list`

查询系统中所有已创建的策略基本信息列表，支持关键词搜索、状态筛选和分页。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 按策略名称关键词模糊搜索 |
| state | string | 否 | - | 按状态筛选：running/stopped/paused |
| page | integer | 否 | `1` | 页码（从1开始） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

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
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
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
| total | integer | 符合条件的策略总数 |
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |

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
    "signal_count": 42,
    "trade_count": 20
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
| stats.trade_count | integer | 累计交易次数 |

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

### 11. 发布策略

**POST** `/api/v1/m/strategy/{strategy_id}/publish`

将指定策略设为已发布状态，使其对 C 端用户可见。发布后用户可在策略广场中浏览和订阅该策略。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy published"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 12. 下架策略

**POST** `/api/v1/m/strategy/{strategy_id}/unpublish`

将指定策略设为未发布状态，从 C 端策略广场中隐藏。下架后用户无法在策略广场中看到该策略，但已订阅的用户不受影响。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "strategy_uuid",
  "message": "Strategy unpublished"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 13. 获取策略性能指标

**GET** `/api/v1/m/strategy/{strategy_id}/performance`

查询指定策略的运行性能统计数据。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "strategy_id": "strategy_uuid",
  "performance": {
    "signal_count": 42,
    "trade_count": 20,
    "running_seconds": 3600.0,
    "total_return": null,
    "max_drawdown": null,
    "sharpe_ratio": null,
    "win_rate": null
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategy_id | string | 策略ID |
| performance.signal_count | integer | 累计信号数 |
| performance.trade_count | integer | 累计交易次数 |
| performance.running_seconds | float | 运行时长（秒） |
| performance.total_return | float\|null | 累计收益率（待接入实际数据） |
| performance.max_drawdown | float\|null | 最大回撤（待接入实际数据） |
| performance.sharpe_ratio | float\|null | 夏普比率（待接入实际数据） |
| performance.win_rate | float\|null | 胜率（待接入实际数据） |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 14. 获取策略信号历史

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

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

## C 端接口详情

> **说明**：C 端策略接口面向普通用户，策略 ID 格式为 `{username}__{strategy_id}`，实现用户隔离。用户只能操作自己创建的策略，不能操作其他用户的策略。

### 1. 获取首页优选策略

**GET** `/api/v1/c/strategy/featured`

返回系统推荐的优质策略列表，用于首页展示。优选策略从已发布（`published=True`）的策略中按信号数量降序排列。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `10` | 返回策略数量（1-50） |

#### 响应示例

```json
{
  "strategies": [
    {
      "strategy_id": "alice__123456",
      "name": "BTC均线策略",
      "state": "running",
      "symbols": ["BTCUSDT"],
      "timeframes": ["1h"],
      "signal_count": 128
    }
  ],
  "total": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| strategies | array[object] | 优选策略列表 |
| strategies[].strategy_id | string | 策略唯一标识 |
| strategies[].name | string | 策略名称 |
| strategies[].state | string | 策略状态 |
| strategies[].symbols | array[string] | 监控的交易对列表 |
| strategies[].timeframes | array[string] | 使用的时间周期列表 |
| strategies[].signal_count | integer | 累计信号数（用于排序参考） |
| total | integer | 返回数量 |

---

### 2. 获取可用策略类型

**GET** `/api/v1/c/strategy/types`

查询系统中所有已注册的策略类型及其配置信息，普通用户可查看所有可用策略类型，用于创建策略时选择。

响应格式与 M 端相同，参见 [M端-获取可用策略类型](#2-获取可用策略类型)。

---

### 3. 获取当前用户的策略列表

**GET** `/api/v1/c/strategy/list`

查询当前登录用户创建的所有策略基本信息列表，支持状态筛选和分页。用户只能看到自己创建的策略。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| state | string | 否 | - | 按状态筛选：running/stopped/paused |
| page | integer | 否 | `1` | 页码（从1开始） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "strategies": [
    {
      "strategy_id": "alice__123456",
      "name": "BTC均线策略",
      "state": "running",
      "symbols": ["BTCUSDT"],
      "timeframes": ["1h"]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据 |

---

### 4. 创建实盘策略

**POST** `/api/v1/c/strategy/create`

根据指定的策略类型和参数为当前用户创建新的实盘策略实例。策略 ID 会自动绑定当前用户，实现用户隔离。

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
  "strategy_id": "alice__123456789",
  "message": "Strategy created"
}
```

> **说明**：策略 ID 格式为 `{username}__{snowflake_id}`，自动绑定当前用户。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 未知的策略类型 |
| 401 | 未提供认证凭据 |

---

### 5. 创建模拟交易策略

**POST** `/api/v1/c/strategy/simulate`

为当前用户创建一个模拟交易（纸交易）策略实例。模拟策略与实盘策略共享相同的行情数据，但不产生真实订单。策略 ID 带有 `sim__` 前缀以区分模拟和实盘。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_type | string | 是 | - | 策略类型名称 |
| symbols | array[string] | 是 | - | 策略监控的交易对列表 |
| params | object | 否 | `{}` | 策略参数配置字典 |
| initial_capital | float | 否 | `10000.0` | 模拟初始资金（USDT） |

```json
{
  "strategy_type": "ma_cross",
  "symbols": ["BTCUSDT"],
  "params": {
    "fast_period": 10,
    "slow_period": 30
  },
  "initial_capital": 10000.0
}
```

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__sim__123456789",
  "mode": "simulate",
  "initial_capital": 10000.0,
  "message": "Simulate strategy created"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| strategy_id | string | 新创建的模拟策略ID（含 sim__ 前缀） |
| mode | string | 交易模式（simulate） |
| initial_capital | float | 模拟初始资金 |
| message | string | 操作结果描述 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 未知的策略类型 |
| 401 | 未提供认证凭据 |

---

### 6. 获取策略详情（C端）

**GET** `/api/v1/c/strategy/{strategy_id}`

查询当前用户指定策略的详细信息和运行状态。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "strategy_id": "alice__123456",
  "name": "BTC均线策略",
  "state": "running",
  "params": {
    "fast_period": 10,
    "slow_period": 30
  },
  "symbols": ["BTCUSDT"],
  "timeframes": ["1h"],
  "stats": {
    "signal_count": 42,
    "trade_count": 20
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问该策略（非本人策略） |
| 404 | 策略不存在 |

---

### 7. 更新策略参数（C端）

**PUT** `/api/v1/c/strategy/{strategy_id}`

更新当前用户指定策略的参数配置。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| params | object | 否 | 要更新的策略参数字典（合并更新） |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "message": "Strategy updated"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权操作该策略 |
| 404 | 策略不存在 |

---

### 8. 删除策略（C端）

**DELETE** `/api/v1/c/strategy/{strategy_id}`

从系统中删除当前用户指定的策略实例。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "message": "Strategy deleted"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权操作该策略 |

---

### 9-12. 启动/停止/暂停/恢复策略（C端）

与 M 端操作相同，但仅限操作当前用户自己的策略。

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/resume` | 恢复策略 |

响应格式与 M 端相同。

**额外错误响应：**

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权操作该策略 |
| 404 | 策略不存在（仅 start 接口） |

---

### 13. 订阅策略

**POST** `/api/v1/c/strategy/{strategy_id}/subscribe`

订阅指定的公开策略，订阅后可接收该策略的信号通知。用户可订阅任意已发布的策略，不限于自己创建的策略。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy subscribed"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 14. 取消订阅策略

**DELETE** `/api/v1/c/strategy/{strategy_id}/subscribe`

取消对指定策略的订阅，不再接收该策略的信号通知。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy unsubscribed"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 15. 收藏策略

**POST** `/api/v1/c/strategy/{strategy_id}/favorite`

将指定策略加入当前用户的收藏列表，方便后续快速访问。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy favorited"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 16. 取消收藏策略

**DELETE** `/api/v1/c/strategy/{strategy_id}/favorite`

将指定策略从当前用户的收藏列表中移除。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy unfavorited"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 17. 点赞策略

**POST** `/api/v1/c/strategy/{strategy_id}/like`

为指定策略点赞，每个用户对同一策略只能点赞一次。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy liked"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 18. 取消点赞策略

**DELETE** `/api/v1/c/strategy/{strategy_id}/like`

取消对指定策略的点赞。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | string | 是 | 策略唯一标识 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "alice__123456",
  "username": "bob",
  "message": "Strategy unliked"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 19. 获取策略性能指标（C端）

**GET** `/api/v1/c/strategy/{strategy_id}/performance`

查询当前用户指定策略的运行性能统计数据。

响应格式与 M 端相同，参见 [M端-获取策略性能指标](#13-获取策略性能指标)。

**额外错误响应：**

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问该策略 |

---

### 20. 获取策略信号历史（C端）

**GET** `/api/v1/c/strategy/{strategy_id}/signals`

查询当前用户指定策略生成的交易信号历史记录。

响应格式与 M 端相同，参见 [M端-获取策略信号历史](#14-获取策略信号历史)。

**额外错误响应：**

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问该策略 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如未知策略类型） |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 403 | 权限不足（C端：无权操作他人策略） |
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

## C 端策略 ID 说明

C 端策略 ID 格式为 `{username}__{snowflake_id}`，例如 `alice__123456789`。

- 模拟策略 ID 格式为 `{username}__sim__{snowflake_id}`，例如 `alice__sim__123456789`
- 用户只能操作以自己用户名开头的策略
- 订阅、收藏、点赞操作不受此限制，可操作任意已发布策略
