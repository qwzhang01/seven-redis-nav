# 交易管理 API 文档

## 概述

交易模块提供交易执行和订单管理相关的 API 接口，支持下单、撤单、订单查询、持仓管理、账户信息查询等完整的交易生命周期管理功能。

## 基础信息

- **基础URL**: `/api/v1/c/trading`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有交易接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

> **注意**：交易接口依赖交易系统运行，若系统未启动将返回 `503` 错误。

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/c/trading/order` | 下单 |
| DELETE | `/api/v1/c/trading/order/{order_id}` | 取消订单 |
| POST | `/api/v1/c/trading/order/cancel-all` | 取消所有订单 |
| GET | `/api/v1/c/trading/orders` | 获取订单列表 |
| GET | `/api/v1/c/trading/order/{order_id}` | 获取订单详情 |
| GET | `/api/v1/c/trading/trades` | 获取成交记录 |
| GET | `/api/v1/c/trading/positions` | 获取持仓列表 |
| GET | `/api/v1/c/trading/position/{symbol}` | 获取单个持仓详情 |
| GET | `/api/v1/c/trading/account` | 获取账户信息 |
| GET | `/api/v1/c/trading/risk` | 获取风险信息 |

---

## 接口详情

### 1. 下单

**POST** `/api/v1/c/trading/order`

提交新的交易订单到交易引擎执行。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |
| side | string | 是 | 交易方向：`buy` 或 `sell` |
| order_type | string | 是 | 订单类型：`market`（市价单）或 `limit`（限价单） |
| quantity | float | 是 | 交易数量 |
| price | float | 否 | 限价单价格（限价单必填，市价单可不填） |
| strategy_id | string | 否 | 关联策略ID，默认为空（手动下单） |

```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "order_type": "limit",
  "quantity": 0.01,
  "price": 50000.0,
  "strategy_id": ""
}
```

> **说明**：
> - **市价单**：立即按当前市场价格成交，无需指定 `price`
> - **限价单**：按指定价格或更优价格成交，需指定 `price`

#### 响应示例

```json
{
  "success": true,
  "order_id": "order_uuid",
  "message": "Order submitted"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| order_id | string | 新创建的订单ID |
| message | string | 操作结果描述 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 订单被拒绝（如风控拦截、参数不合法） |
| 503 | 交易系统未启动 |

---

### 2. 取消订单

**DELETE** `/api/v1/c/trading/order/{order_id}`

取消指定的未成交订单。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| order_id | string | 是 | 订单ID |

#### 请求示例

```
DELETE /api/v1/c/trading/order/order_uuid
```

#### 响应示例

```json
{
  "success": true,
  "order_id": "order_uuid",
  "message": "Order cancelled"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 取消失败（如订单已成交或已取消） |
| 503 | 交易系统未启动 |

---

### 3. 取消所有订单

**POST** `/api/v1/c/trading/order/cancel-all`

取消所有未成交订单，可选择指定交易对。

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 否 | 指定交易对，为空则取消所有订单 |

#### 请求示例

```
POST /api/v1/c/trading/order/cancel-all?symbol=BTCUSDT
```

#### 响应示例

```json
{
  "success": true,
  "cancelled_count": 3,
  "message": "All orders cancelled"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| cancelled_count | integer | 取消的订单数量 |
| message | string | 操作结果描述 |

---

### 4. 获取订单列表

**GET** `/api/v1/c/trading/orders`

查询订单列表，支持按状态和交易对过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | `"active"` | 订单状态：`active`（仅活跃订单）或 `all`（所有订单） |
| symbol | string | 否 | - | 交易对过滤 |
| limit | integer | 否 | `100` | 返回记录数量限制（1-1000） |

#### 请求示例

```
GET /api/v1/c/trading/orders?status=active&symbol=BTCUSDT&limit=50
```

#### 响应示例

```json
{
  "orders": [
    {
      "order_id": "order_uuid",
      "symbol": "BTCUSDT",
      "side": "buy",
      "type": "limit",
      "status": "open",
      "quantity": 0.01,
      "price": 50000.0,
      "strategy_id": ""
    }
  ],
  "total": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| orders | array[object] | 订单信息列表 |
| orders[].order_id | string | 订单ID |
| orders[].symbol | string | 交易对 |
| orders[].side | string | 交易方向（buy/sell） |
| orders[].type | string | 订单类型（market/limit） |
| orders[].status | string | 订单状态（open/filled/cancelled/rejected） |
| orders[].quantity | float | 订单数量 |
| orders[].price | float | 订单价格 |
| orders[].strategy_id | string | 关联策略ID |
| total | integer | 总订单数量 |

---

### 5. 获取订单详情

**GET** `/api/v1/c/trading/order/{order_id}`

查询指定订单的详细信息。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| order_id | string | 是 | 订单ID |

#### 响应示例

```json
{
  "order_id": "order_uuid",
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "limit",
  "status": "filled",
  "quantity": 0.01,
  "filled_quantity": 0.01,
  "price": 50000.0,
  "avg_price": 49998.5
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| order_id | string | 订单ID |
| symbol | string | 交易对 |
| side | string | 交易方向（buy/sell） |
| type | string | 订单类型（market/limit） |
| status | string | 订单状态 |
| quantity | float | 订单数量 |
| filled_quantity | float | 已成交数量 |
| price | float | 订单价格 |
| avg_price | float | 平均成交价格 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订单不存在 |

---

### 6. 获取成交记录

**GET** `/api/v1/c/trading/trades`

查询成交记录，支持按交易对和订单ID过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbol | string | 否 | - | 交易对过滤 |
| order_id | string | 否 | - | 订单ID过滤 |
| limit | integer | 否 | `100` | 返回记录数量限制（1-1000） |

#### 请求示例

```
GET /api/v1/c/trading/trades?symbol=BTCUSDT&limit=50
```

#### 响应示例

```json
{
  "trades": [
    {
      "trade_id": "trade_uuid",
      "order_id": "order_uuid",
      "symbol": "BTCUSDT",
      "side": "buy",
      "price": 49998.5,
      "quantity": 0.01,
      "commission": 0.0004
    }
  ],
  "total": 1
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| trades | array[object] | 成交记录列表 |
| trades[].trade_id | string | 成交ID |
| trades[].order_id | string | 关联订单ID |
| trades[].symbol | string | 交易对 |
| trades[].side | string | 交易方向（buy/sell） |
| trades[].price | float | 成交价格 |
| trades[].quantity | float | 成交数量 |
| trades[].commission | float | 手续费 |
| total | integer | 总成交记录数 |

---

### 7. 获取持仓列表

**GET** `/api/v1/c/trading/positions`

查询所有持仓的详细信息。

#### 响应示例

```json
{
  "positions": [
    {
      "symbol": "BTCUSDT",
      "quantity": 0.05,
      "avg_price": 50000.0,
      "last_price": 52000.0,
      "unrealized_pnl": 100.0,
      "realized_pnl": 50.0,
      "value": 2600.0
    }
  ],
  "total_value": 2600.0
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| positions | array[object] | 持仓信息列表 |
| positions[].symbol | string | 交易对 |
| positions[].quantity | float | 持仓数量 |
| positions[].avg_price | float | 平均成本价 |
| positions[].last_price | float | 最新价格 |
| positions[].unrealized_pnl | float | 未实现盈亏 |
| positions[].realized_pnl | float | 已实现盈亏 |
| positions[].value | float | 持仓价值（数量 × 最新价） |
| total_value | float | 所有持仓总价值 |

---

### 8. 获取单个持仓详情

**GET** `/api/v1/c/trading/position/{symbol}`

查询指定交易对的持仓详细信息。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 `BTCUSDT` |

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "quantity": 0.05,
  "avg_price": 50000.0,
  "current_price": 52000.0,
  "unrealized_pnl": 100.0,
  "realized_pnl": 50.0
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| symbol | string | 交易对 |
| quantity | float | 持仓数量（无持仓时返回 0） |
| avg_price | float | 平均成本价 |
| current_price | float | 当前价格 |
| unrealized_pnl | float | 未实现盈亏 |
| realized_pnl | float | 已实现盈亏 |

> **注意**：若该交易对无持仓，所有数值字段将返回 `0`，不会返回 404 错误。

---

### 9. 获取账户信息

**GET** `/api/v1/c/trading/account`

查询账户余额、保证金等账户信息。

#### 响应示例

```json
{
  "total_equity": 100000.0,
  "available_margin": 95000.0,
  "used_margin": 5000.0,
  "balances": {
    "USDT": {
      "free": 95000.0,
      "locked": 5000.0,
      "total": 100000.0
    },
    "BTC": {
      "free": 0.05,
      "locked": 0.0,
      "total": 0.05
    }
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| total_equity | float | 总资产 |
| available_margin | float | 可用保证金 |
| used_margin | float | 已用保证金 |
| balances | object | 各币种余额信息 |
| balances[币种].free | float | 可用余额 |
| balances[币种].locked | float | 冻结余额 |
| balances[币种].total | float | 总余额 |

> **注意**：若账户信息未初始化，返回所有字段为 `0` 的空账户信息。

---

### 10. 获取风险信息

**GET** `/api/v1/c/trading/risk`

查询风险管理器的统计信息和风险指标。

#### 响应示例

```json
{
  "max_drawdown": 0.05,
  "current_exposure": 5000.0,
  "leverage_ratio": 1.05,
  "risk_level": "low"
}
```

> **说明**：返回字段由风险管理器的具体实现决定，可能包含最大回撤、风险敞口、杠杆率、风险等级等指标。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如订单被拒绝、取消失败等） |
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 404 | 资源不存在（订单不存在） |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 503 | 交易系统未启动，请先启动系统后再调用 |

## 订单状态说明

| 状态 | 描述 |
|------|------|
| open | 未成交（挂单中） |
| filled | 已完全成交 |
| partially_filled | 部分成交 |
| cancelled | 已取消 |
| rejected | 已拒绝 |

## 使用示例

### Python客户端示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/c/trading"

def place_order(token, symbol, side, order_type, quantity, price=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
    }
    if price is not None:
        payload["price"] = price
    
    response = requests.post(f"{BASE_URL}/order", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"下单失败: {response.text}")

def get_positions(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/positions", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取持仓失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    token = "your_jwt_token"
    
    # 限价买入
    result = place_order(token, "BTCUSDT", "buy", "limit", 0.01, 50000.0)
    print(f"下单成功，订单ID: {result['order_id']}")
    
    # 查看持仓
    positions = get_positions(token)
    for pos in positions["positions"]:
        print(f"{pos['symbol']}: 数量={pos['quantity']}, 未实现盈亏={pos['unrealized_pnl']}")
```
