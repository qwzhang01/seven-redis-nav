# 用户管理与交易所API接口文档

## 概述

本文档描述了量化交易系统的用户管理、交易所API管理、信号跟单管理接口，以及管理员端的用户管理接口。所有接口都遵循RESTful设计原则，使用JSON格式进行数据交换。

## 基础信息

- **C端基础URL**: `/api/v1/c/user`
- **C端信号跟单URL**: `/api/v1/c/user/signal-follows`
- **M端用户管理URL**: `/api/v1/m/users`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证说明

所有需要认证的接口都需要在请求头中包含有效的JWT令牌：

```http
Authorization: Bearer <token>
```

**无需认证的公开接口（白名单）：**
- `POST /api/v1/c/user/register` — 用户注册
- `POST /api/v1/c/user/login` — 用户登录
- `POST /api/v1/c/user/password/reset` — 忘记密码重置

## C 端接口列表

### 用户管理接口

| 方法 | 路径 | 认证 | 描述 |
|------|------|------|------|
| POST | `/api/v1/c/user/register` | 否 | 用户注册 |
| POST | `/api/v1/c/user/login` | 否 | 用户登录 |
| POST | `/api/v1/c/user/password/change` | 是 | 修改密码 |
| POST | `/api/v1/c/user/password/reset` | 否 | 忘记密码重置 |
| PUT | `/api/v1/c/user/profile` | 是 | 更新用户信息 |
| GET | `/api/v1/c/user/exchanges/{exchange_id}` | 是 | 获取交易所详情 |
| POST | `/api/v1/c/user/api-keys` | 是 | 添加API密钥 |
| GET | `/api/v1/c/user/api-keys` | 是 | 获取API密钥列表 |
| GET | `/api/v1/c/user/api-keys/{api_key_id}` | 是 | 获取API密钥详情 |
| PUT | `/api/v1/c/user/api-keys/{api_key_id}` | 是 | 更新API密钥 |
| DELETE | `/api/v1/c/user/api-keys/{api_key_id}` | 是 | 删除API密钥 |

### 信号跟单接口

| 方法 | 路径 | 认证 | 描述 |
|------|------|------|------|
| GET | `/api/v1/c/user/signal-follows` | 是 | 获取我的跟单列表 |
| POST | `/api/v1/c/user/signal-follows` | 是 | 创建跟单 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}` | 是 | 获取跟单详情 |
| PUT | `/api/v1/c/user/signal-follows/{follow_id}/config` | 是 | 更新跟单配置 |
| POST | `/api/v1/c/user/signal-follows/{follow_id}/stop` | 是 | 停止跟单 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}/positions` | 是 | 获取跟单持仓列表 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}/trades` | 是 | 获取跟单交易记录 |

## M 端接口列表（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/users` | 获取用户列表 |
| GET | `/api/v1/m/users/{user_id}` | 获取用户详情 |
| PUT | `/api/v1/m/users/{user_id}` | 更新用户信息 |
| PUT | `/api/v1/m/users/{user_id}/status` | 更新用户状态 |

---

## C 端用户管理接口详情

### 1. 用户注册

**POST** `/api/v1/c/user/register`

注册新用户账户。无需认证。

#### 请求参数

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名（唯一） |
| nickname | string | 否 | 昵称 |
| email | string | 是 | 邮箱地址（唯一） |
| password | string | 是 | 密码（至少6位） |
| phone | string | 否 | 手机号 |
| avatar_url | string | 否 | 头像URL |

```json
{
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "password": "password123",
    "phone": "13800138000",
    "avatar_url": "https://example.com/avatar.jpg"
}
```

#### 响应示例

> 注册成功返回 HTTP **201 Created**。

```json
{
    "id": "uuid",
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "email_verified": false,
    "phone": "13800138000",
    "phone_verified": false,
    "avatar_url": "https://example.com/avatar.jpg",
    "user_type": "customer",
    "registration_time": "2026-02-14T10:00:00Z",
    "last_login_time": null,
    "status": "active",
    "create_time": "2026-02-14T10:00:00Z",
    "update_time": "2026-02-14T10:00:00Z"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 用户名已存在 / 邮箱地址已存在 |

---

### 2. 用户登录

**POST** `/api/v1/c/user/login`

用户登录获取访问令牌。无需认证。

#### 请求参数

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱地址 |
| password | string | 是 | 密码 |

```json
{
    "username": "testuser",
    "password": "password123"
}
```

> **说明**：`username` 字段支持用户名或邮箱地址登录。

#### 响应示例

```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
        "id": "uuid",
        "username": "testuser",
        "nickname": "测试用户",
        "email": "test@example.com",
        "email_verified": false,
        "phone": "13800138000",
        "phone_verified": false,
        "avatar_url": "https://example.com/avatar.jpg",
        "user_type": "customer",
        "registration_time": "2026-02-14T10:00:00Z",
        "last_login_time": "2026-02-14T10:05:00Z",
        "status": "active",
        "create_time": "2026-02-14T10:00:00Z",
        "update_time": "2026-02-14T10:05:00Z"
    }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| access_token | string | JWT 访问令牌 |
| token_type | string | 令牌类型（bearer） |
| expires_in | integer | 过期时间（秒），默认 1800 秒（30 分钟） |
| user | object | 用户信息 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 用户名或密码错误 |
| 403 | 账户已被禁用 |

---

### 3. 修改密码

**POST** `/api/v1/c/user/password/change`

修改当前登录用户的密码。需要认证。

#### 请求参数

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码 |

```json
{
    "old_password": "oldpassword123",
    "new_password": "newpassword456"
}
```

#### 响应示例

```json
{
    "message": "密码修改成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 旧密码错误 |
| 404 | 用户不存在 |

---

### 4. 忘记密码重置

**POST** `/api/v1/c/user/password/reset`

通过邮箱验证码重置密码。无需认证。

#### 请求参数

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| verification_code | string | 是 | 邮箱验证码 |
| new_password | string | 是 | 新密码 |

```json
{
    "email": "test@example.com",
    "verification_code": "123456",
    "new_password": "newpassword456"
}
```

#### 响应示例

```json
{
    "message": "密码重置成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 验证码错误 |
| 404 | 邮箱地址不存在 |

---

### 5. 更新用户信息

**PUT** `/api/v1/c/user/profile`

更新当前登录用户的个人信息。需要认证。

#### 请求参数

> **说明**：所有字段均为可选，仅传入需要修改的字段。

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| email | string | 否 | 邮箱地址 |
| phone | string | 否 | 手机号 |
| avatar_url | string | 否 | 头像URL |

```json
{
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "phone": "13900139000",
    "avatar_url": "https://example.com/new-avatar.jpg"
}
```

#### 响应示例

返回更新后的完整用户信息（格式同注册响应）。

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 用户不存在 |

---

### 6. 获取交易所详情

**GET** `/api/v1/c/user/exchanges/{exchange_id}`

根据交易所ID获取详细信息。需要认证。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| exchange_id | integer | 是 | 交易所ID |

#### 响应示例

```json
{
    "id": 1,
    "exchange_code": "binance",
    "exchange_name": "币安",
    "exchange_type": "spot",
    "base_url": "https://api.binance.com",
    "api_doc_url": "https://binance-docs.github.io/apidocs/",
    "status": "active",
    "supported_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "rate_limits": {"requests_per_minute": 1200},
    "create_time": "2026-02-14T10:00:00Z",
    "update_time": "2026-02-14T10:00:00Z"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 交易所不存在 |

---

## C 端 API 密钥管理接口详情

### 1. 添加API密钥

**POST** `/api/v1/c/user/api-keys`

为用户添加交易所API密钥，需要经过后台审核。需要认证。

#### 请求参数

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| exchange_id | integer | 是 | 交易所ID |
| label | string | 是 | 密钥标签 |
| api_key | string | 是 | API密钥 |
| secret_key | string | 是 | Secret密钥 |
| passphrase | string | 否 | 密码短语（部分交易所需要） |
| permissions | object | 否 | 权限配置 |

```json
{
    "exchange_id": 1,
    "label": "币安主账户",
    "api_key": "your_api_key_here",
    "secret_key": "your_secret_key_here",
    "passphrase": "your_passphrase",
    "permissions": {
        "spot_trading": true,
        "margin_trading": false,
        "futures_trading": false,
        "withdraw": false
    }
}
```

#### 响应示例

> 添加成功返回 HTTP **201 Created**，密钥初始状态为 `pending`（待审核）。

```json
{
    "id": "api_key_uuid",
    "user_id": "user_uuid",
    "exchange_id": 1,
    "label": "币安主账户",
    "api_key": "your_api_key_here",
    "status": "pending",
    "review_reason": null,
    "approved_by": null,
    "approved_time": null,
    "last_used_time": null,
    "create_time": "2026-02-14T10:00:00Z",
    "update_time": "2026-02-14T10:00:00Z"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | API密钥记录ID |
| user_id | string | 所属用户ID |
| exchange_id | integer | 所属交易所ID |
| label | string | 密钥标签 |
| api_key | string | API密钥（明文） |
| status | string | 审核状态：pending/approved/rejected/disabled |
| review_reason | string\|null | 审核备注 |
| approved_by | string\|null | 审核人 |
| approved_time | string\|null | 审核时间 |
| last_used_time | string\|null | 最后使用时间 |
| create_time | string | 创建时间 |
| update_time | string | 更新时间 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 用户不存在 / 交易所不存在 |

---

### 2. 获取API密钥列表

**GET** `/api/v1/c/user/api-keys`

获取当前用户的API密钥列表，支持按状态筛选。需要认证。

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 否 | 状态筛选：pending/approved/rejected/disabled |

#### 响应示例

```json
{
    "total": 1,
    "items": [
        {
            "id": "api_key_uuid1",
            "user_id": "user_uuid",
            "exchange_id": 1,
            "label": "币安主账户",
            "api_key": "your_api_key_here",
            "status": "approved",
            "review_reason": "密钥权限设置合理",
            "approved_by": "admin",
            "approved_time": "2026-02-14T10:05:00Z",
            "last_used_time": "2026-02-14T10:10:00Z",
            "create_time": "2026-02-14T10:00:00Z",
            "update_time": "2026-02-14T10:05:00Z"
        }
    ]
}
```

---

### 3. 获取API密钥详情

**GET** `/api/v1/c/user/api-keys/{api_key_id}`

根据ID获取API密钥的详细信息。需要认证，且只能查看自己的密钥。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| api_key_id | integer | 是 | API密钥ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此API密钥 |
| 404 | API密钥不存在 |

---

### 4. 更新API密钥

**PUT** `/api/v1/c/user/api-keys/{api_key_id}`

更新API密钥的标签、权限或状态。需要认证，且只能修改自己的密钥。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| api_key_id | integer | 是 | API密钥ID |

#### 请求参数

> **说明**：所有字段均为可选，仅传入需要修改的字段。

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| label | string | 否 | 密钥标签 |
| permissions | object | 否 | 权限配置 |
| status | string | 否 | 状态 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权修改此API密钥 |
| 404 | API密钥不存在 |

---

### 5. 删除API密钥

**DELETE** `/api/v1/c/user/api-keys/{api_key_id}`

删除指定的API密钥记录。需要认证，且只能删除自己的密钥。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| api_key_id | integer | 是 | API密钥ID |

#### 响应示例

```json
{
    "message": "API密钥删除成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权删除此API密钥 |
| 404 | API密钥不存在 |

---

## C 端信号跟单接口详情

> **说明**：信号跟单接口挂载在 `/api/v1/c/user/signal-follows` 下，所有接口均需要认证。

### 跟单数据结构

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 跟单ID |
| user_id | integer | 用户ID |
| strategy_id | string | 跟单的策略ID |
| signal_name | string | 信号/策略名称 |
| exchange | string | 交易所 |
| follow_amount | float | 跟单资金（USDT） |
| current_value | float | 当前净值 |
| follow_ratio | float | 跟单比例（0~1） |
| stop_loss | float\|null | 止损比例（0~1） |
| total_return | float | 累计收益率 |
| max_drawdown | float | 最大回撤 |
| current_drawdown | float | 当前回撤 |
| today_return | float | 今日收益率 |
| win_rate | float | 胜率 |
| total_trades | integer | 总交易次数 |
| win_trades | integer | 盈利交易次数 |
| loss_trades | integer | 亏损交易次数 |
| avg_win | float | 平均盈利 |
| avg_loss | float | 平均亏损 |
| profit_factor | float | 盈利因子 |
| risk_level | string | 风险等级 |
| status | string | 跟单状态：following/stopped/paused |
| follow_days | integer | 跟单天数 |
| start_time | string\|null | 开始时间 |
| stop_time | string\|null | 停止时间 |
| return_curve | array | 收益曲线数据 |
| return_curve_labels | array | 收益曲线标签 |
| create_time | string | 创建时间 |
| update_time | string | 更新时间 |

---

### 1. 获取我的跟单列表

**GET** `/api/v1/c/user/signal-follows`

查询当前用户的所有跟单记录，支持按状态筛选和分页。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | - | 状态筛选：following/stopped/paused |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123456,
        "user_id": 789,
        "strategy_id": "alice__111",
        "signal_name": "BTC均线策略",
        "exchange": "binance",
        "follow_amount": 10000.0,
        "current_value": 10500.0,
        "follow_ratio": 1.0,
        "stop_loss": 0.1,
        "total_return": 0.05,
        "max_drawdown": 0.02,
        "current_drawdown": 0.0,
        "today_return": 0.01,
        "win_rate": 0.65,
        "total_trades": 20,
        "win_trades": 13,
        "loss_trades": 7,
        "avg_win": 150.0,
        "avg_loss": 80.0,
        "profit_factor": 1.87,
        "risk_level": "low",
        "status": "following",
        "follow_days": 10,
        "start_time": "2026-02-11T10:00:00",
        "stop_time": null,
        "return_curve": [],
        "return_curve_labels": [],
        "create_time": "2026-02-11T10:00:00",
        "update_time": "2026-02-21T10:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  }
}
```

---

### 2. 创建跟单

**POST** `/api/v1/c/user/signal-follows`

为当前用户创建一条新的信号跟单记录。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要跟单的策略ID |
| signal_name | string | 是 | - | 信号/策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| follow_amount | float | 是 | - | 跟单资金（USDT，必须大于0） |
| follow_ratio | float | 否 | `1.0` | 跟单比例（0~1） |
| stop_loss | float | 否 | null | 止损比例（0~1，可选） |

```json
{
  "strategy_id": "alice__111",
  "signal_name": "BTC均线策略",
  "exchange": "binance",
  "follow_amount": 10000.0,
  "follow_ratio": 1.0,
  "stop_loss": 0.1
}
```

#### 响应示例

```json
{
  "success": true,
  "data": { "...跟单完整信息..." },
  "message": "跟单创建成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 参数校验失败（如资金为0、比例超范围、已存在活跃跟单） |

---

### 3. 获取跟单详情

**GET** `/api/v1/c/user/signal-follows/{follow_id}`

根据跟单ID查询完整的跟单详情，包含绩效统计、收益曲线、配置信息等。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_id | integer | 是 | 跟单ID |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 4. 更新跟单配置

**PUT** `/api/v1/c/user/signal-follows/{follow_id}/config`

修改跟单的资金、比例或止损设置。仅允许修改状态为 `following` 的跟单。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_id | integer | 是 | 跟单ID |

#### 请求体

> **说明**：所有字段均为可选，仅传入需要修改的字段。

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_amount | float | 否 | 跟单资金（USDT） |
| follow_ratio | float | 否 | 跟单比例（0~1） |
| stop_loss | float | 否 | 止损比例（0~1） |

```json
{
  "follow_amount": 20000.0,
  "follow_ratio": 0.5,
  "stop_loss": 0.15
}
```

#### 响应示例

```json
{
  "success": true,
  "data": { "...更新后的跟单信息..." },
  "message": "跟单配置更新成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 参数校验失败 / 跟单已停止无法修改 |
| 403 | 无权操作此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 5. 停止跟单

**POST** `/api/v1/c/user/signal-follows/{follow_id}/stop`

将指定跟单的状态设置为 `stopped`，同时关闭所有未平仓持仓。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_id | integer | 是 | 跟单ID |

#### 响应示例

```json
{
  "success": true,
  "data": { "...跟单信息..." },
  "message": "跟单已停止"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 跟单已停止 |
| 403 | 无权操作此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 6. 获取跟单持仓列表

**GET** `/api/v1/c/user/signal-follows/{follow_id}/positions`

查询指定跟单的持仓记录，默认返回当前未平仓持仓。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_id | integer | 是 | 跟单ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | - | 持仓状态筛选：open/closed |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "follow_order_id": "123456",
        "symbol": "BTCUSDT",
        "side": "buy",
        "amount": 0.01,
        "entry_price": 50000.0,
        "current_price": 52000.0,
        "pnl": 20.0,
        "pnl_percent": 0.04,
        "status": "open",
        "open_time": "2026-02-21T10:00:00",
        "close_time": null
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 持仓ID |
| follow_order_id | string | 关联跟单ID |
| symbol | string | 交易对 |
| side | string | 方向（buy/sell） |
| amount | float | 持仓数量 |
| entry_price | float | 开仓价格 |
| current_price | float | 当前价格 |
| pnl | float | 盈亏金额 |
| pnl_percent | float | 盈亏百分比 |
| status | string | 持仓状态（open/closed） |
| open_time | string | 开仓时间 |
| close_time | string\|null | 平仓时间 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

### 7. 获取跟单交易记录

**GET** `/api/v1/c/user/signal-follows/{follow_id}/trades`

查询指定跟单的历史成交记录，支持按交易对和方向筛选。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_id | integer | 是 | 跟单ID |

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| symbol | string | 否 | - | 交易对过滤（自动转大写） |
| side | string | 否 | - | 方向过滤：buy/sell（自动转小写） |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "follow_order_id": "123456",
        "position_id": "789",
        "symbol": "BTCUSDT",
        "side": "buy",
        "price": 50000.0,
        "amount": 0.01,
        "total": 500.0,
        "pnl": null,
        "fee": 0.2,
        "signal_record_id": "signal_uuid",
        "trade_time": "2026-02-21T10:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 交易记录ID |
| follow_order_id | string | 关联跟单ID |
| position_id | string\|null | 关联持仓ID |
| symbol | string | 交易对 |
| side | string | 方向（buy/sell） |
| price | float | 成交价格 |
| amount | float | 成交数量 |
| total | float | 成交金额 |
| pnl | float\|null | 盈亏金额 |
| fee | float | 手续费 |
| signal_record_id | string\|null | 关联信号记录ID |
| trade_time | string | 成交时间 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 无权访问此跟单记录 |
| 404 | 跟单记录不存在 |

---

## M 端用户管理接口详情

> **说明**：M 端用户管理接口仅供管理员使用，需要管理员权限（`user_type = admin`）。

### 1. 获取用户列表

**GET** `/api/v1/m/users`

支持按用户名/邮箱/昵称搜索，按状态和类型筛选，分页返回。同时返回顶部统计数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| search | string | 否 | - | 按用户名、邮箱或昵称模糊搜索 |
| status | string | 否 | - | 状态筛选：active/inactive/locked |
| user_type | string | 否 | - | 类型筛选：customer/admin |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（最大100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "username": "testuser",
        "nickname": "测试用户",
        "email": "test@example.com",
        "phone": "13800138000",
        "avatar_url": null,
        "user_type": "customer",
        "email_verified": false,
        "phone_verified": false,
        "registration_time": "2026-02-14T10:00:00",
        "last_login_time": "2026-02-21T10:00:00",
        "status": "active",
        "create_time": "2026-02-14T10:00:00",
        "update_time": "2026-02-21T10:00:00"
      }
    ],
    "statistics": {
      "total_users": 1250,
      "active_users": 1200,
      "today_new": 12,
      "locked_users": 5
    }
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| data.total | integer | 符合筛选条件的用户总数 |
| data.items | array[object] | 用户列表 |
| data.statistics.total_users | integer | 全量用户总数 |
| data.statistics.active_users | integer | 活跃用户数 |
| data.statistics.today_new | integer | 今日新增用户数 |
| data.statistics.locked_users | integer | 已锁定用户数 |

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据 |
| 403 | 权限不足，仅管理员可操作 |

---

### 2. 获取用户详情

**GET** `/api/v1/m/users/{user_id}`

根据用户 ID 返回用户的完整信息。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "phone": "13800138000",
    "avatar_url": null,
    "user_type": "customer",
    "email_verified": false,
    "phone_verified": false,
    "registration_time": "2026-02-14T10:00:00",
    "last_login_time": "2026-02-21T10:00:00",
    "status": "active",
    "create_time": "2026-02-14T10:00:00",
    "update_time": "2026-02-21T10:00:00"
  }
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 403 | 权限不足，仅管理员可操作 |
| 404 | 用户不存在 |

---

### 3. 更新用户信息

**PUT** `/api/v1/m/users/{user_id}`

管理员可修改用户的昵称、邮箱、手机号和用户类型。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 请求体

> **说明**：所有字段均为可选，仅传入需要修改的字段。

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| email | string | 否 | 邮箱地址（唯一性校验） |
| phone | string | 否 | 手机号 |
| user_type | string | 否 | 用户类型：customer/admin |

```json
{
  "nickname": "新昵称",
  "user_type": "admin"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": { "...更新后的用户信息..." },
  "message": "用户信息更新成功"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 邮箱地址已被其他用户使用 |
| 403 | 权限不足，仅管理员可操作 |
| 404 | 用户不存在 |

---

### 4. 更新用户状态

**PUT** `/api/v1/m/users/{user_id}/status`

管理员可将用户状态设置为 `active`（解锁）、`inactive` 或 `locked`（锁定）。不允许管理员锁定自己。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | integer | 是 | 用户ID |

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 是 | 目标状态：active/inactive/locked |

```json
{
  "status": "locked"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": { "...更新后的用户信息..." },
  "message": "用户已锁定"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 不能锁定自己的账户 |
| 403 | 权限不足，仅管理员可操作 |
| 404 | 用户不存在 |

---

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误（如用户名已存在、旧密码错误、参数校验失败等） |
| 401 | 未授权访问（未提供 Token、Token 无效或已过期） |
| 403 | 权限不足（如账户已被禁用、无权访问他人资源、非管理员操作） |
| 404 | 资源不存在（用户、交易所、API密钥、跟单记录不存在） |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 500 | 服务器内部错误 |

## 安全注意事项

1. **API密钥安全**: API密钥和Secret密钥在传输过程中必须使用HTTPS加密
2. **权限最小化**: 只开启必要的交易权限，避免开启提现等高危权限
3. **定期更换**: 建议定期更换API密钥
4. **IP白名单**: 在交易所平台设置IP白名单限制
5. **监控告警**: 设置异常交易行为监控和告警机制

## 使用示例

### Python客户端示例

```python
import requests

# 基础配置
BASE_URL = "http://localhost:8000/api/v1/c/user"

# 登录获取令牌
def login(username, password):
    response = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        raise Exception(f"登录失败: {response.text}")

# 更新用户信息
def update_profile(token, nickname):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{BASE_URL}/profile", headers=headers, json={
        "nickname": nickname
    })
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"更新失败: {response.text}")

# 添加API密钥
def add_api_key(token, exchange_id, label, api_key, secret_key):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api-keys", headers=headers, json={
        "exchange_id": exchange_id,
        "label": label,
        "api_key": api_key,
        "secret_key": secret_key,
        "permissions": {
            "spot_trading": True,
            "margin_trading": False,
            "futures_trading": False,
            "withdraw": False
        }
    })
    
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"添加API密钥失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    try:
        # 登录
        token = login("testuser", "password123")
        print("登录成功")
        
        # 更新用户信息
        profile = update_profile(token, "新昵称")
        print(f"更新成功: {profile['nickname']}")
        
        # 添加API密钥
        api_key = add_api_key(
            token, 
            "uuid1", 
            "币安主账户", 
            "your_api_key", 
            "your_secret_key"
        )
        print(f"API密钥添加成功: {api_key['id']}")
        
    except Exception as e:
        print(f"操作失败: {e}")
```

## 更新日志

- **v1.1.0** (2026-02-19): 路由前缀更新为 `/api/v1/c/user`，新增认证中间件，移除 `GET /profile` 和 `GET /exchanges` 列表接口，补充各接口错误响应说明
- **v1.0.0** (2026-02-14): 初始版本，包含完整的用户管理和交易所API管理功能

---

**注意**: 本文档描述的接口为示例接口，实际实现可能根据具体需求进行调整。
