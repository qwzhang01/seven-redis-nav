# 用户管理 API 文档

## 概述

用户管理模块提供用户注册登录、Token 刷新、个人信息维护、交易所 API 密钥管理等功能（C端），以及管理员对用户的查询和管理功能（M端）。

## 基础信息

- **C端基础URL**: `/api/v1/c/user`
- **M端用户管理URL**: `/api/v1/m/users`
- **认证方式**: JWT Bearer Token
  - `access_token`：短期有效（默认30分钟），用于接口认证
  - `refresh_token`：长期有效（默认7天），用于在 access_token 过期后换取新令牌
- **数据格式**: JSON

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/c/user/register` | 用户注册 | 否 |
| POST | `/api/v1/c/user/login` | 用户登录，返回 access_token + refresh_token | 否 |
| POST | `/api/v1/c/user/token/refresh` | 刷新 Token，换取新的 token 对 | 否 |
| POST | `/api/v1/c/user/password/change` | 修改密码 | 是 |
| POST | `/api/v1/c/user/password/reset` | 重置密码 | 否 |
| PUT | `/api/v1/c/user/profile` | 更新个人信息 | 是 |
| GET | `/api/v1/c/user/exchanges/{exchange_id}` | 获取交易所信息 | 是 |
| POST | `/api/v1/c/user/api-keys` | 创建 API 密钥 | 是 |
| GET | `/api/v1/c/user/api-keys` | 获取 API 密钥列表 | 是 |
| GET | `/api/v1/c/user/api-keys/{api_key_id}` | 获取 API 密钥详情 | 是 |
| PUT | `/api/v1/c/user/api-keys/{api_key_id}` | 更新 API 密钥 | 是 |
| DELETE | `/api/v1/c/user/api-keys/{api_key_id}` | 删除 API 密钥 | 是 |

### C端 — 信号跟单接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/c/user/signal-follows` | 获取我的跟单列表 | 是 |
| POST | `/api/v1/c/user/signal-follows` | 创建跟单 | 是 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}` | 获取跟单详情 | 是 |
| PUT | `/api/v1/c/user/signal-follows/{follow_id}/config` | 更新跟单配置 | 是 |
| POST | `/api/v1/c/user/signal-follows/{follow_id}/stop` | 停止跟单 | 是 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}/positions` | 获取跟单持仓 | 是 |
| GET | `/api/v1/c/user/signal-follows/{follow_id}/trades` | 获取跟单交易记录 | 是 |

### M端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/users` | 获取用户列表 |
| GET | `/api/v1/m/users/{user_id}` | 获取用户详情 |
| PUT | `/api/v1/m/users/{user_id}` | 更新用户信息 |
| PUT | `/api/v1/m/users/{user_id}/status` | 更新用户状态 |

---

## C端接口详情

### 1. 用户注册

**POST** `/api/v1/c/user/register`

注册新用户账户。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| email | string | 否 | 邮箱 |
| nickname | string | 否 | 昵称 |
| phone | string | 否 | 手机号 |

#### 响应：`201 Created`，返回用户基本信息。

---

### 2. 用户登录

**POST** `/api/v1/c/user/login`

验证用户名和密码，成功后返回 JWT Token 对（access_token + refresh_token）。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| access_token | string | 短期有效令牌（默认30分钟），用于接口认证 |
| refresh_token | string | 长期有效令牌（默认7天），用于刷新 token |
| token_type | string | 固定值 `"bearer"` |
| expires_in | integer | access_token 有效时长（秒） |
| user | object | 用户基本信息 |

#### 响应示例

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "alice",
    "nickname": "Alice"
  }
}
```

---

### 3. 刷新 Token

**POST** `/api/v1/c/user/token/refresh`

使用 refresh_token 换取新的 access_token 和 refresh_token。当 access_token 过期时，前端应调用此接口，而非要求用户重新登录。

**使用场景**：
1. 前端检测到 access_token 过期（HTTP 401）
2. 前端使用本地保存的 refresh_token 调用此接口
3. 获取新的 token 对后，替换本地存储并重试原请求

> **注意**：若 refresh_token 也过期，则需要用户重新登录。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| refresh_token | string | 是 | 登录时获取的刷新令牌 |

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| access_token | string | 新的短期有效令牌 |
| refresh_token | string | 新的长期有效令牌 |
| token_type | string | 固定值 `"bearer"` |
| expires_in | integer | access_token 有效时长（秒） |

#### 响应示例

```json
{
  "access_token": "eyJ...(new)",
  "refresh_token": "eyJ...(new)",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 无效的刷新令牌、令牌已过期或用户不存在 |

---

### 4. 修改密码

**POST** `/api/v1/c/user/password/change`

> **需要认证**

修改当前登录用户的密码。需要提供原密码和新密码，验证原密码正确后更新为新密码。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码 |

---

### 5. 重置密码

**POST** `/api/v1/c/user/password/reset`

用于忘记密码场景，通过用户名重置密码。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| new_password | string | 是 | 新密码 |

---

### 6. 更新个人信息

**PUT** `/api/v1/c/user/profile`

> **需要认证**

更新当前用户的个人信息。支持更新以下字段（均为可选，仅传入需要更新的字段）。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| avatar_url | string | 否 | 头像URL |

---

### 7. 交易所 API 密钥管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/user/exchanges/{exchange_id}` | 获取交易所信息 |
| POST | `/api/v1/c/user/api-keys` | 创建 API 密钥 |
| GET | `/api/v1/c/user/api-keys` | 获取 API 密钥列表 |
| GET | `/api/v1/c/user/api-keys/{api_key_id}` | 获取 API 密钥详情 |
| PUT | `/api/v1/c/user/api-keys/{api_key_id}` | 更新 API 密钥（仅可更新标签） |
| DELETE | `/api/v1/c/user/api-keys/{api_key_id}` | 删除 API 密钥（软删除） |

#### 创建 API 密钥请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| exchange_id | integer | 是 | 交易所ID |
| label | string | 是 | 密钥标签 |
| api_key | string | 是 | API Key |
| secret_key | string | 是 | Secret Key |
| passphrase | string | 否 | Passphrase（部分交易所需要） |
| permissions | list | 否 | 权限列表 |

---

## C端 — 信号跟单接口详情

### 1. 获取我的跟单列表

**GET** `/api/v1/c/user/signal-follows`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | - | 状态筛选: following/stopped/paused |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

---

### 2. 创建跟单

**POST** `/api/v1/c/user/signal-follows`

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| strategy_id | string | 是 | - | 要跟单的策略ID |
| signal_name | string | 是 | - | 信号/策略名称 |
| exchange | string | 否 | `"binance"` | 交易所 |
| follow_amount | float | 是 | - | 跟单资金(USDT)，必须>0 |
| follow_ratio | float | 否 | `1.0` | 跟单比例(0~1) |
| stop_loss | float | 否 | - | 止损比例(0~1) |

---

### 3. 获取跟单详情

**GET** `/api/v1/c/user/signal-follows/{follow_id}`

返回跟单完整信息，包含绩效统计、收益曲线等。

---

### 4. 更新跟单配置

**PUT** `/api/v1/c/user/signal-follows/{follow_id}/config`

修改跟单的资金、比例或止损设置。仅允许修改 `following` 状态的跟单。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| follow_amount | float | 否 | 跟单资金 |
| follow_ratio | float | 否 | 跟单比例 |
| stop_loss | float | 否 | 止损比例 |

---

### 5. 停止跟单

**POST** `/api/v1/c/user/signal-follows/{follow_id}/stop`

停止跟单并关闭所有未平仓持仓。

---

### 6. 获取跟单持仓

**GET** `/api/v1/c/user/signal-follows/{follow_id}/positions`

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| status | string | 否 | - | 持仓状态: open/closed |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量 |

---

### 7. 获取跟单交易记录

**GET** `/api/v1/c/user/signal-follows/{follow_id}/trades`

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| symbol | string | 否 | 交易对过滤 |
| side | string | 否 | 方向过滤: buy/sell |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

---

## M端接口详情

> **权限要求**：以下接口均需管理员权限。

### 1. 获取用户列表

**GET** `/api/v1/m/users`

支持搜索、状态/类型筛选、分页，同时返回顶部统计数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| search | string | 否 | - | 按用户名/邮箱/昵称模糊搜索 |
| status | string | 否 | - | 状态筛选: active/inactive/locked |
| user_type | string | 否 | - | 类型筛选: customer/admin |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `20` | 每页数量（1-100） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [...],
    "statistics": {
      "total_users": 100,
      "active_users": 80,
      "today_new": 5,
      "locked_users": 2
    }
  }
}
```

---

### 2. 获取用户详情

**GET** `/api/v1/m/users/{user_id}`

---

### 3. 更新用户信息

**PUT** `/api/v1/m/users/{user_id}`

管理员可修改用户的昵称、邮箱、手机号和用户类型。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| nickname | string | 否 | 昵称 |
| email | string | 否 | 邮箱（需唯一） |
| phone | string | 否 | 手机号 |
| user_type | string | 否 | 用户类型: customer/admin |

---

### 4. 更新用户状态

**PUT** `/api/v1/m/users/{user_id}/status`

管理员可锁定/解锁用户。不允许管理员锁定自己。

#### 请求体

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 是 | 用户状态: active/inactive/locked |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误（如用户名已存在、密码不符合要求等） |
| 401 | 未认证或认证失败（Token 过期、无效的 refresh_token 等） |
| 403 | 权限不足 |
| 404 | 用户/资源不存在 |

---

## Token 刷新流程

```
用户登录
  │
  ├─→ 获取 access_token（30分钟） + refresh_token（7天）
  │
  ├─→ 使用 access_token 调用业务接口
  │     │
  │     ├─→ 成功：正常返回数据
  │     │
  │     └─→ 401 错误（access_token 过期）
  │           │
  │           ├─→ 使用 refresh_token 调用 POST /token/refresh
  │           │     │
  │           │     ├─→ 成功：获取新的 token 对，重试原请求
  │           │     │
  │           │     └─→ 失败：refresh_token 也过期 → 重新登录
  │           │
  │           └─→ 无 refresh_token → 重新登录
```
