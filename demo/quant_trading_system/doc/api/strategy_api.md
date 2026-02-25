# 策略管理 API 文档

## 概述

策略管理模块提供系统预设策略的完整生命周期管理接口，基于数据库驱动，支持预设策略浏览、用户策略实例创建（实盘/模拟）、策略启停控制、性能查询等功能。同时提供模拟交易专用接口，支持 K 线数据、指标数据、交易点标记、持仓和日志查询。

分为以下三个部分：
- **C端策略接口**：面向普通用户，策略浏览、创建、控制、查询
- **C端模拟交易接口**：面向普通用户，模拟交易数据查询
- **M端策略接口**：面向管理员，预设策略 CRUD 和上架/下架管理

## 基础信息

- **C端策略基础URL**: `/api/v1/c/strategy`
- **C端模拟交易基础URL**: `/api/v1/c/simulation`
- **M端策略基础URL**: `/api/v1/m/strategy`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### C端策略接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/strategy/featured` | 获取首页推荐策略 |
| GET | `/api/v1/c/strategy/types` | 获取可用策略类型 |
| GET | `/api/v1/c/strategy/list` | 获取系统预设策略列表 |
| GET | `/api/v1/c/strategy/preset/{strategy_id}` | 获取预设策略详情 |
| GET | `/api/v1/c/strategy/my` | 获取当前用户的策略实例列表 |
| POST | `/api/v1/c/strategy/create` | 创建实盘策略 |
| POST | `/api/v1/c/strategy/simulate` | 创建模拟策略 |
| GET | `/api/v1/c/strategy/{strategy_id}` | 获取用户策略实例详情 |
| PUT | `/api/v1/c/strategy/{strategy_id}` | 更新策略参数 |
| DELETE | `/api/v1/c/strategy/{strategy_id}` | 删除策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/resume` | 恢复策略 |
| GET | `/api/v1/c/strategy/{strategy_id}/performance` | 获取策略性能指标 |
| GET | `/api/v1/c/strategy/{strategy_id}/signals` | 获取策略信号历史 |

### C端模拟交易专用接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/simulation/{strategy_id}/klines` | 获取模拟K线历史数据 |
| GET | `/api/v1/c/simulation/{strategy_id}/indicators` | 获取策略指标历史数据 |
| GET | `/api/v1/c/simulation/{strategy_id}/trade-marks` | 获取交易买卖点标记 |
| GET | `/api/v1/c/simulation/{strategy_id}/positions` | 获取当前模拟持仓 |
| GET | `/api/v1/c/simulation/{strategy_id}/trades` | 获取模拟交易记录 |
| GET | `/api/v1/c/simulation/{strategy_id}/logs` | 获取模拟运行日志 |

### M端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/strategy/list` | 获取策略列表 |
| GET | `/api/v1/m/strategy/types` | 获取可用策略类型 |
| POST | `/api/v1/m/strategy/create` | 创建预设策略 |
| GET | `/api/v1/m/strategy/{strategy_id}` | 获取策略详情 |
| PUT | `/api/v1/m/strategy/{strategy_id}` | 更新策略 |
| DELETE | `/api/v1/m/strategy/{strategy_id}` | 删除策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/publish` | 上架策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/unpublish` | 下架策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/resume` | 恢复策略 |
| GET | `/api/v1/m/strategy/{strategy_id}/performance` | 获取策略表现 |
| GET | `/api/v1/m/strategy/{strategy_id}/signals` | 获取策略信号历史 |

---

## C端策略接口详情

### 1. 获取首页推荐策略

**GET** `/api/v1/c/strategy/featured`

返回系统推荐的优质预设策略列表，用于首页展示。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `10` | 返回数量限制（1-50） |

#### 响应示例

```json
{
  "strategies": [...],
  "total": 5
}
```

---

### 2. 获取可用策略类型

**GET** `/api/v1/c/strategy/types`

返回所有策略类型枚举信息。

#### 响应示例

```json
{
  "types": [
    {"value": "grid", "label": "网格交易", "description": "在设定价格区间内自动高抛低吸"},
    {"value": "trend", "label": "趋势跟踪", "description": "追踪市场趋势方向进行交易"}
  ]
}
```

---

### 3. 获取系统预设策略列表

**GET** `/api/v1/c/strategy/list`

获取所有已上架的系统预设策略，支持筛选、搜索和分页。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 按策略名称模糊搜索 |
| market_type | string | 否 | - | 市场类型: spot/futures/margin |
| strategy_type | string | 否 | - | 策略类型 |
| risk_level | string | 否 | - | 风险等级: low/medium/high |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 4. 获取预设策略详情

**GET** `/api/v1/c/strategy/preset/{strategy_id}`

获取单个系统预设策略的完整信息，包含策略介绍、逻辑说明、参数配置、风险提示等。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 预设策略ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在或未上架 |

---

### 5. 获取当前用户的策略实例列表

**GET** `/api/v1/c/strategy/my`

获取当前登录用户创建的所有策略实例（实盘+模拟），支持按运行模式和状态筛选。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| mode | string | 否 | - | 运行模式: live/simulate |
| status | string | 否 | - | 策略状态 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "items": [...],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

---

### 6. 创建实盘策略

**POST** `/api/v1/c/strategy/create`

根据系统预设策略创建实盘交易策略实例。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| preset_strategy_id | string | 是 | - | 预设策略ID |
| name | string | 是 | - | 策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | `[]` | 交易对列表 |
| timeframe | string | 否 | `"1h"` | K线时间周期 |
| leverage | integer | 否 | `1` | 杠杆倍数 |
| initial_capital | float | 否 | `10000.0` | 初始资金(USDT) |
| params | object | 否 | `{}` | 策略自定义参数 |
| trade_mode | string | 否 | `"both"` | 开仓模式: both/long_only/short_only |
| take_profit | float | 否 | - | 止盈百分比 |
| stop_loss | float | 否 | - | 止损百分比 |
| stop_mode | string | 否 | `"both"` | 止盈止损模式: both/tp_only/sl_only |
| max_positions | integer | 否 | `10` | 最大持仓数 |
| max_orders | integer | 否 | `50` | 最大订单数 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 12345,
  "mode": "live",
  "message": "实盘策略创建成功"
}
```

---

### 7. 创建模拟策略

**POST** `/api/v1/c/strategy/simulate`

根据系统预设策略创建模拟交易策略实例，使用虚拟资金。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| preset_strategy_id | string | 是 | - | 预设策略ID |
| name | string | 否 | 自动生成 | 策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | `[]` | 交易对列表 |
| timeframe | string | 否 | `"1h"` | K线时间周期 |
| leverage | integer | 否 | `1` | 杠杆倍数 |
| initial_capital | float | 否 | `10000.0` | 模拟初始资金(USDT) |
| params | object | 否 | `{}` | 策略自定义参数 |
| trade_mode | string | 否 | `"both"` | 开仓模式 |
| take_profit | float | 否 | - | 止盈百分比 |
| stop_loss | float | 否 | - | 止损百分比 |
| stop_mode | string | 否 | `"both"` | 止盈止损模式 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 12346,
  "mode": "simulate",
  "initial_capital": 10000.0,
  "message": "模拟策略创建成功"
}
```

---

### 8. 获取用户策略实例详情

**GET** `/api/v1/c/strategy/{strategy_id}`

获取当前用户指定策略实例的详细信息，包含策略配置、运行状态和统计信息。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 策略实例ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证 |
| 404 | 策略不存在或无权访问 |

---

### 9. 更新策略参数

**PUT** `/api/v1/c/strategy/{strategy_id}`

更新当前用户指定策略的参数配置。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| params | object | 否 | 策略自定义参数 |
| take_profit | float | 否 | 止盈百分比 |
| stop_loss | float | 否 | 止损百分比 |
| stop_mode | string | 否 | 止盈止损模式 |
| max_positions | integer | 否 | 最大持仓数 |
| max_orders | integer | 否 | 最大订单数 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 12345,
  "message": "策略更新成功"
}
```

---

### 10. 删除策略

**DELETE** `/api/v1/c/strategy/{strategy_id}`

删除当前用户指定的策略实例。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "12345",
  "message": "策略删除成功"
}
```

---

### 11-14. 启动/停止/暂停/恢复策略

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/resume` | 恢复策略 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 12345,
  "message": "策略启动成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在或无权操作 |

---

### 15. 获取策略性能指标

**GET** `/api/v1/c/strategy/{strategy_id}/performance`

获取策略运行的各项性能统计指标。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 策略实例ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在或无权访问 |

---

### 16. 获取策略信号历史

**GET** `/api/v1/c/strategy/{strategy_id}/signals`

查询指定策略生成的交易信号历史记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回信号数量限制（1-1000） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "signals": [],
  "total": 0
}
```

---

## C端模拟交易接口详情

> **说明**：模拟交易接口挂载在 `/api/v1/c/simulation/` 下，所有接口均需认证，且只能访问自己创建的策略。

### 1. 获取模拟K线历史数据

**GET** `/api/v1/c/simulation/{strategy_id}/klines`

获取模拟交易的 K 线历史数据，支持分页加载。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 策略实例ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| timeframe | string | 否 | 策略配置值 | K线周期 |
| start_time | integer | 否 | - | 开始时间戳(ms) |
| end_time | integer | 否 | - | 结束时间戳(ms) |
| limit | integer | 否 | `500` | 返回条数（1-2000） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "symbol": "BTC/USDT",
  "timeframe": "5m",
  "data": [
    {
      "time": 1708000000,
      "open": 91000.0,
      "high": 91500.0,
      "low": 90800.0,
      "close": 91200.0,
      "volume": 125.5
    }
  ]
}
```

> **说明**：`time` 为 Unix 秒级时间戳（lightweight-charts 要求），数据按时间升序排列。

---

### 2. 获取策略指标历史数据

**GET** `/api/v1/c/simulation/{strategy_id}/indicators`

获取策略使用的技术指标数据，用于在 K 线图上叠加显示。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| start_time | integer | 否 | - | 开始时间戳(ms) |
| end_time | integer | 否 | - | 结束时间戳(ms) |
| limit | integer | 否 | `500` | 返回条数（1-2000） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "indicators": [
    {
      "name": "MA20",
      "type": "line",
      "color": "#2196F3",
      "pane": "main",
      "data": [{"time": 1708000000, "value": 91100.0}]
    },
    {
      "name": "RSI",
      "type": "line",
      "color": "#FF9800",
      "pane": "sub",
      "data": [{"time": 1708000000, "value": 65.3}]
    }
  ]
}
```

> **字段说明**：
> - `pane`: 指标显示面板 — `main`(主图)、`sub`(副图)、`sub2`(第二副图)
> - `type`: 绘制类型 — `line`(线图)、`histogram`(柱状图)、`area`(面积图)

---

### 3. 获取交易买卖点标记

**GET** `/api/v1/c/simulation/{strategy_id}/trade-marks`

获取策略运行中的买卖交易点，用于在 K 线图上标注。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| start_time | integer | 否 | - | 开始时间戳(ms) |
| end_time | integer | 否 | - | 结束时间戳(ms) |
| limit | integer | 否 | `100` | 返回条数（1-500） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "marks": [
    {
      "time": 1708000000,
      "position": "belowBar",
      "color": "#26a69a",
      "shape": "arrowUp",
      "text": "买入 91000",
      "side": "buy",
      "price": 91000.0,
      "quantity": 0.1,
      "pnl": null
    },
    {
      "time": 1708005000,
      "position": "aboveBar",
      "color": "#ef5350",
      "shape": "arrowDown",
      "text": "卖出 91500 +500",
      "side": "sell",
      "price": 91500.0,
      "quantity": 0.1,
      "pnl": 500.0
    }
  ]
}
```

> **标记规则**：
> - 买入标记：绿色(`#26a69a`)，位于K线下方(`belowBar`)，向上箭头(`arrowUp`)
> - 卖出标记：红色(`#ef5350`)，位于K线上方(`aboveBar`)，向下箭头(`arrowDown`)

---

### 4. 获取当前模拟持仓

**GET** `/api/v1/c/simulation/{strategy_id}/positions`

获取策略当前持仓列表和汇总信息。

#### 响应示例

```json
{
  "strategy_id": "12345",
  "positions": [
    {
      "symbol": "BTC/USDT",
      "direction": "long",
      "amount": "0.5 BTC",
      "entry_price": 90123.45,
      "current_price": 91476.14,
      "pnl": 676.35,
      "pnl_ratio": 1.5,
      "open_time": "2025-02-24T10:30:00Z"
    }
  ],
  "total_value": 12456.0,
  "unrealized_pnl": 676.35
}
```

---

### 5. 获取模拟交易记录

**GET** `/api/v1/c/simulation/{strategy_id}/trades`

分页查询策略的模拟交易历史记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页条数（1-100） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "total": 50,
  "page": 1,
  "page_size": 20,
  "trades": [
    {
      "id": "trade_001",
      "symbol": "BTC/USDT",
      "side": "buy",
      "price": 91000.00,
      "amount": 0.1,
      "value": 9100.0,
      "fee": 9.1,
      "pnl": null,
      "time": "2025-02-24T16:30:15Z"
    }
  ]
}
```

---

### 6. 获取模拟运行日志

**GET** `/api/v1/c/simulation/{strategy_id}/logs`

查询策略模拟运行产生的日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别: info/warn/error/trade |
| limit | integer | 否 | `50` | 返回条数（1-200） |

#### 响应示例

```json
{
  "strategy_id": "12345",
  "logs": [
    {
      "time": "2025-02-24T19:03:23Z",
      "level": "info",
      "message": "策略运行正常，当前持仓3个"
    }
  ]
}
```

---

## M端接口详情

### 1. 获取策略列表（管理端）

**GET** `/api/v1/m/strategy/list`

管理端获取所有策略列表，支持多维度筛选。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 按策略名称搜索 |
| market_type | string | 否 | - | 市场类型 |
| strategy_type | string | 否 | - | 策略类型 |
| risk_level | string | 否 | - | 风险等级: low/medium/high |
| status | string | 否 | - | 策略状态 |
| is_published | boolean | 否 | - | 是否已上架 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 2. 获取可用策略类型

**GET** `/api/v1/m/strategy/types`

返回所有策略类型枚举信息，与C端相同。

---

### 3. 创建预设策略

**POST** `/api/v1/m/strategy/create`

管理员创建系统预设策略模板。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 策略名称 |
| description | string | 否 | - | 策略简要说明 |
| detail | string | 否 | - | 策略详细介绍 |
| strategy_type | string | 是 | - | 策略类型 |
| market_type | string | 否 | `"spot"` | 市场类型 |
| risk_level | string | 否 | `"medium"` | 风险等级 |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | - | 交易对列表 |
| timeframe | string | 否 | `"1h"` | K线时间周期 |
| logic_description | string | 否 | - | 策略逻辑说明 |
| params_schema | object | 否 | - | 参数配置定义 |
| default_params | object | 否 | - | 默认参数值 |
| risk_params | object | 否 | - | 风控参数 |
| advanced_params | object | 否 | - | 高级参数 |
| risk_warning | string | 否 | - | 风险提示 |
| is_featured | boolean | 否 | `false` | 是否推荐 |
| sort_order | integer | 否 | `0` | 排序权重 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略创建成功"
}
```

---

### 4. 获取策略详情（管理端）

**GET** `/api/v1/m/strategy/{strategy_id}`

管理端查看预设策略完整信息。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| strategy_id | integer | 是 | 预设策略ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 5. 更新策略

**PUT** `/api/v1/m/strategy/{strategy_id}`

更新预设策略的基本信息和配置，支持更新所有创建时的字段以及以下额外字段：

| 额外字段 | 类型 | 描述 |
|----------|------|------|
| total_return | float | 策略收益率 |
| max_drawdown | float | 最大回撤 |
| sharpe_ratio | float | 夏普比率 |
| win_rate | float | 胜率 |
| running_days | integer | 运行天数 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略更新成功"
}
```

---

### 6. 删除策略

**DELETE** `/api/v1/m/strategy/{strategy_id}`

逻辑删除预设策略。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "1",
  "message": "策略删除成功"
}
```

---

### 7. 上架策略

**POST** `/api/v1/m/strategy/{strategy_id}/publish`

将策略设为已发布状态，对 C 端用户可见。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略上架成功"
}
```

---

### 8. 下架策略

**POST** `/api/v1/m/strategy/{strategy_id}/unpublish`

将策略设为未发布状态，从 C 端隐藏。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略下架成功"
}
```

---

### 9-12. 启动/停止/暂停/恢复策略（管理端）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/m/strategy/{strategy_id}/resume` | 恢复策略 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略启动成功"
}
```

---

### 13. 获取策略表现（管理端）

**GET** `/api/v1/m/strategy/{strategy_id}/performance`

获取预设策略的表现数据。

#### 响应示例

```json
{
  "strategy_id": 1,
  "performance": {
    "total_return": 15.5,
    "max_drawdown": -5.2,
    "sharpe_ratio": 1.8,
    "win_rate": 0.65,
    "running_days": 30
  }
}
```

---

### 14. 获取策略信号历史（管理端）

**GET** `/api/v1/m/strategy/{strategy_id}/signals`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回信号数量限制（1-1000） |

#### 响应示例

```json
{
  "strategy_id": 1,
  "signals": [],
  "total": 0
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 404 | 策略不存在或无权访问 |
| 429 | 请求过于频繁 |
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
