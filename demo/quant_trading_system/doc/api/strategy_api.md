# 策略管理 API 文档

## 概述

策略管理模块提供策略相关的全部 API 接口，包含三大子模块：

- **C 端策略管理**：面向普通用户，支持浏览预设策略、创建实盘/模拟策略实例、策略启停控制、表现查询等
- **Admin 端策略管理**：面向管理员，支持预设策略 CRUD、上架/下架、启停控制、表现和信号查询等
- **C 端模拟交易**：面向普通用户，提供模拟交易 K 线、指标、买卖点标记、持仓、交易记录和运行日志查询

## 基础信息

| 模块 | 基础 URL | 说明 |
|------|----------|------|
| C 端策略管理 | `/api/v1/c/strategy` | 普通用户策略操作 |
| Admin 端策略管理 | `/api/v1/m/strategy` | 管理员策略操作 |
| C 端模拟交易 | `/api/v1/c/simulation` | 模拟交易数据查询 |

- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 一、C 端策略管理接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/strategy/featured` | 获取首页推荐策略 |
| GET | `/api/v1/c/strategy/list` | 获取系统预设策略列表 |
| GET | `/api/v1/c/strategy/preset/{strategy_id}` | 获取预设策略详情 |
| GET | `/api/v1/c/strategy/my` | 获取当前用户策略实例列表 |
| POST | `/api/v1/c/strategy/create` | 创建实盘策略 |
| POST | `/api/v1/c/strategy/simulate` | 创建模拟策略 |
| GET | `/api/v1/c/strategy/{strategy_id}` | 获取用户策略实例详情 |
| PUT | `/api/v1/c/strategy/{strategy_id}` | 更新策略参数 |
| DELETE | `/api/v1/c/strategy/{strategy_id}` | 删除策略 |
| GET | `/api/v1/c/strategy/{strategy_id}/performance` | 获取策略性能指标 |
| GET | `/api/v1/c/strategy/{strategy_id}/signals` | 获取策略信号历史 |
| POST | `/api/v1/c/strategy/{strategy_id}/start` | 启动策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/stop` | 停止策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/pause` | 暂停策略 |
| POST | `/api/v1/c/strategy/{strategy_id}/resume` | 恢复策略 |

---

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
  "strategies": [
    {
      "id": 1,
      "name": "MA 交叉策略",
      "description": "基于均线交叉的趋势策略",
      "risk_level": "medium",
      "total_return": 15.5,
      "is_featured": true
    }
  ],
  "total": 1
}
```

---

### 2. 获取系统预设策略列表

**GET** `/api/v1/c/strategy/list`

获取已上架的系统预设策略列表，支持按多条件筛选和分页。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 按策略名称搜索 |
| market_type | string | 否 | - | 市场类型：`spot` / `futures` / `margin` |
| strategy_type | string | 否 | - | 策略类型 |
| risk_level | string | 否 | - | 风险等级：`low` / `medium` / `high` |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "strategies": [...],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

### 3. 获取预设策略详情

**GET** `/api/v1/c/strategy/preset/{strategy_id}`

获取系统预设策略的完整信息，包含策略介绍、逻辑说明、参数配置、风险提示等。

> **注意**：仅返回已上架的策略，未上架策略返回 404。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| strategy_id | integer | 预设策略 ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在或未上架 |

---

### 4. 获取当前用户策略实例列表

**GET** `/api/v1/c/strategy/my`

获取当前登录用户创建的策略实例列表，支持按运行模式和状态筛选。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| mode | string | 否 | - | 运行模式：`live` / `simulate` |
| status | string | 否 | - | 策略状态 |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

---

### 5. 创建实盘策略

**POST** `/api/v1/c/strategy/create`

根据系统预设策略创建实盘交易策略实例。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| preset_strategy_id | string | 是 | - | 预设策略 ID |
| name | string | 是 | - | 策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | `[]` | 交易标的列表 |
| timeframe | string | 否 | `"1h"` | K 线时间周期 |
| leverage | integer | 否 | `1` | 杠杆倍数 |
| initial_capital | float | 否 | `10000.0` | 初始资金 |
| params | object | 否 | `{}` | 策略参数配置 |
| trade_mode | string | 否 | `"both"` | 交易方向：`both` / `long` / `short` |
| take_profit | float | 否 | - | 止盈比例 |
| stop_loss | float | 否 | - | 止损比例 |
| stop_mode | string | 否 | `"both"` | 止损模式 |
| max_positions | integer | 否 | `10` | 最大持仓数 |
| max_orders | integer | 否 | `50` | 最大订单数 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "mode": "live",
  "message": "实盘策略创建成功"
}
```

---

### 6. 创建模拟策略

**POST** `/api/v1/c/strategy/simulate`

根据系统预设策略创建模拟交易策略实例，使用虚拟资金。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| preset_strategy_id | string | 是 | - | 预设策略 ID |
| name | string | 否 | `""` | 策略名称（为空时自动生成） |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | `[]` | 交易标的列表 |
| timeframe | string | 否 | `"1h"` | K 线时间周期 |
| leverage | integer | 否 | `1` | 杠杆倍数 |
| initial_capital | float | 否 | `10000.0` | 初始资金 |
| params | object | 否 | `{}` | 策略参数配置 |
| trade_mode | string | 否 | `"both"` | 交易方向 |
| take_profit | float | 否 | - | 止盈比例 |
| stop_loss | float | 否 | - | 止损比例 |
| stop_mode | string | 否 | `"both"` | 止损模式 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 456,
  "mode": "simulate",
  "initial_capital": 10000.0,
  "message": "模拟策略创建成功"
}
```

---

### 7. 获取用户策略实例详情

**GET** `/api/v1/c/strategy/{strategy_id}`

获取用户自己创建的策略实例详情，包含策略配置、运行状态和统计信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| strategy_id | integer | 策略实例 ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据 |
| 404 | 策略不存在或无权访问 |

---

### 8. 更新策略参数

**PUT** `/api/v1/c/strategy/{strategy_id}`

更新用户策略的参数配置。仅传入需要修改的字段。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| params | object | 否 | 策略参数配置 |
| take_profit | float | 否 | 止盈比例 |
| stop_loss | float | 否 | 止损比例 |
| stop_mode | string | 否 | 止损模式 |
| max_positions | integer | 否 | 最大持仓数 |
| max_orders | integer | 否 | 最大订单数 |

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "message": "策略更新成功"
}
```

---

### 9. 删除策略

**DELETE** `/api/v1/c/strategy/{strategy_id}`

删除用户自己创建的策略实例。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": "123",
  "message": "策略删除成功"
}
```

---

### 10. 获取策略性能指标

**GET** `/api/v1/c/strategy/{strategy_id}/performance`

返回策略运行的各项性能统计指标。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在或无权访问 |

---

### 11. 获取策略信号历史

**GET** `/api/v1/c/strategy/{strategy_id}/signals`

查询指定策略生成的交易信号历史记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| limit | integer | 否 | `100` | 返回数量（1-1000） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "signals": [],
  "total": 0
}
```

---

### 12. 启动策略

**POST** `/api/v1/c/strategy/{strategy_id}/start`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "message": "策略启动成功"
}
```

---

### 13. 停止策略

**POST** `/api/v1/c/strategy/{strategy_id}/stop`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "message": "策略停止成功"
}
```

---

### 14. 暂停策略

**POST** `/api/v1/c/strategy/{strategy_id}/pause`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "message": "策略暂停成功"
}
```

---

### 15. 恢复策略

**POST** `/api/v1/c/strategy/{strategy_id}/resume`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 123,
  "message": "策略恢复成功"
}
```

---

## 二、Admin 端策略管理接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/strategy/list` | 获取策略列表（管理端） |
| GET | `/api/v1/m/strategy/types` | 获取可用策略类型 |
| POST | `/api/v1/m/strategy/create` | 新增预设策略 |
| GET | `/api/v1/m/strategy/{strategy_id}` | 获取策略详情 |
| PUT | `/api/v1/m/strategy/{strategy_id}` | 编辑策略 |
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

### 1. 获取策略列表（管理端）

**GET** `/api/v1/m/strategy/list`

管理端获取所有预设策略列表，支持按多条件筛选，包括上架状态。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 按策略名称搜索 |
| market_type | string | 否 | - | 市场类型 |
| strategy_type | string | 否 | - | 策略类型 |
| risk_level | string | 否 | - | 风险等级：`low` / `medium` / `high` |
| status | string | 否 | - | 策略状态 |
| is_published | boolean | 否 | - | 是否已上架 |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

---

### 2. 获取可用策略类型

**GET** `/api/v1/m/strategy/types`

返回所有策略类型枚举信息。

#### 响应示例

```json
{
  "types": [
    {"name": "ma_cross", "label": "均线交叉"},
    {"name": "rsi", "label": "RSI 策略"}
  ]
}
```

---

### 3. 新增预设策略

**POST** `/api/v1/m/strategy/create`

管理员创建系统预设策略模板。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| name | string | 是 | - | 策略名称 |
| description | string | 否 | - | 策略简介 |
| detail | string | 否 | - | 策略详细说明 |
| strategy_type | string | 是 | - | 策略类型 |
| market_type | string | 否 | `"spot"` | 市场类型 |
| risk_level | string | 否 | `"medium"` | 风险等级 |
| exchange | string | 否 | `"binance"` | 交易所 |
| symbols | array[string] | 否 | - | 交易标的列表 |
| timeframe | string | 否 | `"1h"` | K 线时间周期 |
| logic_description | string | 否 | - | 策略逻辑说明 |
| params_schema | object | 否 | - | 参数定义 Schema |
| default_params | object | 否 | - | 默认参数值 |
| risk_params | object | 否 | - | 风险参数 |
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

### 4. 获取策略详情

**GET** `/api/v1/m/strategy/{strategy_id}`

管理端查看预设策略完整信息。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| strategy_id | integer | 策略 ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 策略不存在 |

---

### 5. 编辑策略

**PUT** `/api/v1/m/strategy/{strategy_id}`

更新预设策略的基本信息和配置。仅传入需要修改的字段。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 策略名称 |
| description | string | 否 | 策略简介 |
| detail | string | 否 | 策略详细说明 |
| strategy_type | string | 否 | 策略类型 |
| market_type | string | 否 | 市场类型 |
| risk_level | string | 否 | 风险等级 |
| exchange | string | 否 | 交易所 |
| symbols | array[string] | 否 | 交易标的列表 |
| timeframe | string | 否 | K 线时间周期 |
| logic_description | string | 否 | 策略逻辑说明 |
| params_schema | object | 否 | 参数定义 Schema |
| default_params | object | 否 | 默认参数值 |
| risk_params | object | 否 | 风险参数 |
| advanced_params | object | 否 | 高级参数 |
| risk_warning | string | 否 | 风险提示 |
| total_return | float | 否 | 总收益率 |
| max_drawdown | float | 否 | 最大回撤 |
| sharpe_ratio | float | 否 | 夏普比率 |
| win_rate | float | 否 | 胜率 |
| running_days | integer | 否 | 运行天数 |
| is_featured | boolean | 否 | 是否推荐 |
| sort_order | integer | 否 | 排序权重 |

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

### 9. 启动策略（管理端）

**POST** `/api/v1/m/strategy/{strategy_id}/start`

管理员启动预设策略的运行。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略启动成功"
}
```

---

### 10. 停止策略（管理端）

**POST** `/api/v1/m/strategy/{strategy_id}/stop`

管理员停止预设策略的运行。

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略停止成功"
}
```

---

### 11. 暂停策略（管理端）

**POST** `/api/v1/m/strategy/{strategy_id}/pause`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略暂停成功"
}
```

---

### 12. 恢复策略（管理端）

**POST** `/api/v1/m/strategy/{strategy_id}/resume`

#### 响应示例

```json
{
  "success": true,
  "strategy_id": 1,
  "message": "策略恢复成功"
}
```

---

### 13. 获取策略表现（管理端）

**GET** `/api/v1/m/strategy/{strategy_id}/performance`

查看预设策略的核心表现指标。

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
| limit | integer | 否 | `100` | 返回数量（1-1000） |

#### 响应示例

```json
{
  "strategy_id": 1,
  "signals": [],
  "total": 0
}
```

---

## 三、C 端模拟交易接口

### 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/simulation/{strategy_id}/klines` | 获取模拟交易 K 线数据 |
| GET | `/api/v1/c/simulation/{strategy_id}/indicators` | 获取策略指标数据 |
| GET | `/api/v1/c/simulation/{strategy_id}/trade-marks` | 获取交易买卖点标记 |
| GET | `/api/v1/c/simulation/{strategy_id}/positions` | 获取当前模拟持仓 |
| GET | `/api/v1/c/simulation/{strategy_id}/trades` | 获取模拟交易记录 |
| GET | `/api/v1/c/simulation/{strategy_id}/logs` | 获取模拟运行日志 |

---

### 1. 获取模拟交易 K 线数据

**GET** `/api/v1/c/simulation/{strategy_id}/klines`

获取模拟交易的 K 线历史数据，支持分页加载。前端拖动图表时可传入 `end_time` 获取更早数据。返回数据按时间升序排列，`time` 为 Unix 秒级时间戳。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| timeframe | string | 否 | - | K 线周期，默认与策略配置一致 |
| start_time | integer | 否 | - | 开始时间戳（毫秒） |
| end_time | integer | 否 | - | 结束时间戳（毫秒） |
| limit | integer | 否 | `500` | 返回条数（1-2000） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "data": [
    {
      "time": 1708000000,
      "open": 42000.0,
      "high": 42500.0,
      "low": 41800.0,
      "close": 42300.0,
      "volume": 1500.5
    }
  ]
}
```

---

### 2. 获取策略指标数据

**GET** `/api/v1/c/simulation/{strategy_id}/indicators`

返回策略使用的技术指标数据，包含指标类型、颜色、面板和数据。

- `pane` 字段指示指标显示在主图（`main`）还是副图（`sub` / `sub2`）
- `type` 字段指示绘制类型：`line`（线图）、`histogram`（柱状图）、`area`（面积图）

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| start_time | integer | 否 | - | 开始时间戳（毫秒） |
| end_time | integer | 否 | - | 结束时间戳（毫秒） |
| limit | integer | 否 | `500` | 返回条数（1-2000） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "indicators": [
    {
      "name": "MA5",
      "type": "line",
      "pane": "main",
      "color": "#FF6600",
      "data": [{"time": 1708000000, "value": 42100.0}]
    }
  ]
}
```

---

### 3. 获取交易买卖点标记

**GET** `/api/v1/c/simulation/{strategy_id}/trade-marks`

返回策略运行中的买卖交易点，用于在 K 线图上标注。买入标记使用绿色位于 K 线下方，卖出标记使用红色位于 K 线上方。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| start_time | integer | 否 | - | 开始时间戳（毫秒） |
| end_time | integer | 否 | - | 结束时间戳（毫秒） |
| limit | integer | 否 | `100` | 返回条数（1-500） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "marks": [
    {
      "time": 1708000000,
      "type": "buy",
      "price": 42000.0,
      "color": "#00CC00",
      "position": "belowBar"
    }
  ]
}
```

---

### 4. 获取当前模拟持仓

**GET** `/api/v1/c/simulation/{strategy_id}/positions`

返回策略当前持仓列表和汇总信息。

#### 响应示例

```json
{
  "strategy_id": "123",
  "positions": [
    {
      "symbol": "BTC/USDT",
      "side": "long",
      "amount": 0.1,
      "entry_price": 42000.0,
      "unrealized_pnl": 300.0
    }
  ],
  "total_unrealized_pnl": 300.0
}
```

---

### 5. 获取模拟交易记录

**GET** `/api/v1/c/simulation/{strategy_id}/trades`

分页查询策略的模拟交易历史记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `20` | 每页条数（1-100） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "trades": [
    {
      "trade_id": "t_001",
      "symbol": "BTC/USDT",
      "side": "buy",
      "price": 42000.0,
      "amount": 0.1,
      "realized_pnl": 0,
      "time": 1708000000
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 6. 获取模拟运行日志

**GET** `/api/v1/c/simulation/{strategy_id}/logs`

查询策略模拟运行产生的日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别：`info` / `warn` / `error` / `trade` |
| limit | integer | 否 | `50` | 返回条数（1-200） |

#### 响应示例

```json
{
  "strategy_id": "123",
  "logs": [
    {
      "time": "2025-02-01T10:00:00Z",
      "level": "info",
      "message": "策略启动成功"
    }
  ],
  "total": 1
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 |
| 401 | 未提供认证凭据 |
| 404 | 策略不存在或无权访问 |
| 500 | 服务器内部错误 |
