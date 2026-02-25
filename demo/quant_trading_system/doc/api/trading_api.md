# 交易管理 API 文档

## 概述

交易模块提供交易执行和订单管理相关的 API 接口，支持完整的交易生命周期管理，包括下单、撤单、订单查询、持仓管理、账户信息和风险查询。

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
| symbol | string | 是 | 交易对符号 |
| side | string | 是 | 交易方向（buy/sell） |
| order_type | string | 是 | 订单类型（market/limit） |
| quantity | float | 是 | 交易数量 |
| price | float | 否 | 限价单价格（限价单必填） |
| strategy_id | string | 否 | 策略ID（可选，用于关联策略） |

#### 响应示例

```json
{
  "success": true,
  "order_id": "order_123456",
  "message": "Order submitted"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 订单被拒绝 |

---

### 2. 取消订单

**DELETE** `/api/v1/c/trading/order/{order_id}`

取消指定的未成交订单。

#### 响应示例

```json
{
  "success": true,
  "order_id": "order_123456",
  "message": "Order cancelled"
}
```

---

### 3. 取消所有订单

**POST** `/api/v1/c/trading/order/cancel-all`

取消所有未成交订单，可选择指定交易对。

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 否 | 交易对，为空则取消所有订单 |

#### 响应示例

```json
{
  "success": true,
  "cancelled_count": 5,
  "message": "All orders cancelled"
}
```

---

### 4. 获取订单列表

**GET** `/api/v1/c/trading/orders`

查询订单列表，支持按状态和交易对过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | `"active"` | 订单状态（active: 活跃订单, all: 所有订单） |
| symbol | string | 否 | - | 交易对过滤 |
| limit | integer | 否 | `100` | 返回数量（1-1000） |

#### 响应示例

```json
{
  "orders": [
    {
      "order_id": "order_123456",
      "symbol": "BTCUSDT",
      "side": "buy",
      "type": "limit",
      "status": "pending",
      "quantity": 0.1,
      "price": 91000.0,
      "strategy_id": "strategy_001"
    }
  ],
  "total": 1
}
```

---

### 5. 获取订单详情

**GET** `/api/v1/c/trading/order/{order_id}`

查询指定订单的详细信息。

#### 响应示例

```json
{
  "order_id": "order_123456",
  "symbol": "BTCUSDT",
  "side": "buy",
  "type": "limit",
  "status": "filled",
  "quantity": 0.1,
  "filled_quantity": 0.1,
  "price": 91000.0,
  "avg_price": 90950.0
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 订单不存在 |

---

### 6. 获取成交记录

**GET** `/api/v1/c/trading/trades`

查询成交记录，支持按交易对和订单ID过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 否 | 交易对过滤 |
| order_id | string | 否 | 订单ID过滤 |
| limit | integer | 否 | 返回数量（1-1000，默认100） |

#### 响应示例

```json
{
  "trades": [
    {
      "trade_id": "trade_001",
      "order_id": "order_123456",
      "symbol": "BTCUSDT",
      "side": "buy",
      "price": 91000.0,
      "quantity": 0.1,
      "commission": 0.91
    }
  ],
  "total": 1
}
```

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
      "quantity": 0.1,
      "avg_price": 91000.0,
      "last_price": 91500.0,
      "unrealized_pnl": 50.0,
      "realized_pnl": 120.0,
      "value": 9150.0
    }
  ],
  "total_value": 9150.0
}
```

---

### 8. 获取单个持仓详情

**GET** `/api/v1/c/trading/position/{symbol}`

查询指定交易对的持仓详细信息。

#### 响应示例

```json
{
  "symbol": "BTCUSDT",
  "quantity": 0.1,
  "avg_price": 91000.0,
  "current_price": 91500.0,
  "unrealized_pnl": 50.0,
  "realized_pnl": 120.0
}
```

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
    "USDT": {"free": 95000.0, "locked": 5000.0, "total": 100000.0}
  }
}
```

---

### 10. 获取风险信息

**GET** `/api/v1/c/trading/risk`

查询风险管理器的统计信息和风险指标。

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误或操作失败 |
| 401 | 未提供认证凭据 |
| 404 | 资源不存在 |
| 503 | 交易系统未启动 |

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
