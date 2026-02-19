# 用户管理与交易所API接口文档

## 概述

本文档描述了量化交易系统的用户管理和交易所API管理接口。所有接口都遵循RESTful设计原则，使用JSON格式进行数据交换。

## 基础信息

- **基础URL**: `/api/v1/c/user`
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

## 通用响应格式

### 成功响应
```json
{
    "success": true,
    "data": {},
    "message": "操作成功"
}
```

### 错误响应
```json
{
    "success": false,
    "error": "错误描述",
    "message": "错误详情",
    "path": "/api/v1/c/user/..."
}
```

## 用户管理接口

### 1. 用户注册

**POST** `/api/v1/c/user/register`

注册新用户账户。无需认证。

#### 请求参数
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

> **注意**：注册成功返回 HTTP 201 Created。

### 2. 用户登录

**POST** `/api/v1/c/user/login`

用户登录获取访问令牌。无需认证。

#### 请求参数
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

### 3. 修改密码

**POST** `/api/v1/c/user/password/change`

修改当前登录用户的密码。需要认证。

#### 请求参数
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

### 4. 忘记密码重置

**POST** `/api/v1/c/user/password/reset`

通过邮箱验证码重置密码。无需认证。

#### 请求参数
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

### 5. 更新用户信息

**PUT** `/api/v1/c/user/profile`

更新当前登录用户的个人信息。需要认证。

#### 请求参数
```json
{
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "phone": "13900139000",
    "avatar_url": "https://example.com/new-avatar.jpg"
}
```

> **说明**：所有字段均为可选，仅传入需要修改的字段。

#### 响应示例
```json
{
    "id": "uuid",
    "username": "testuser",
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "email_verified": false,
    "phone": "13900139000",
    "phone_verified": false,
    "avatar_url": "https://example.com/new-avatar.jpg",
    "user_type": "customer",
    "registration_time": "2026-02-14T10:00:00Z",
    "last_login_time": "2026-02-14T10:05:00Z",
    "status": "active",
    "create_time": "2026-02-14T10:00:00Z",
    "update_time": "2026-02-14T10:15:00Z"
}
```

## 交易所管理接口

### 1. 获取交易所详情

**GET** `/api/v1/c/user/exchanges/{exchange_id}`

根据交易所ID获取详细信息。需要认证。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| exchange_id | string | 是 | 交易所ID（UUID） |

#### 响应示例
```json
{
    "id": "uuid1",
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

## API密钥管理接口

### 1. 添加API密钥

**POST** `/api/v1/c/user/api-keys`

为用户添加交易所API密钥，需要经过后台审核。需要认证。

#### 请求参数
```json
{
    "exchange_id": "uuid1",
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
```json
{
    "id": "api_key_uuid",
    "user_id": "user_uuid",
    "exchange_id": "uuid1",
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

> **注意**：添加成功返回 HTTP 201 Created，密钥初始状态为 `pending`（待审核）。

### 2. 获取API密钥列表

**GET** `/api/v1/c/user/api-keys`

获取当前用户的API密钥列表，支持按状态筛选。需要认证。

#### 查询参数
- `status` (可选): pending/approved/rejected/disabled

#### 响应示例
```json
{
    "total": 2,
    "items": [
        {
            "id": "api_key_uuid1",
            "user_id": "user_uuid",
            "exchange_id": "uuid1",
            "label": "币安主账户",
            "api_key": "your_api_key_here",
            "status": "approved",
            "review_reason": "密钥权限设置合理",
            "approved_by": "admin",
            "approved_time": "2026-02-14T10:05:00Z",
            "last_used_time": "2026-02-14T10:10:00Z",
            "create_time": "2026-02-14T10:00:00Z",
            "update_time": "2026-02-14T10:05:00Z"
        },
        {
            "id": "api_key_uuid2",
            "user_id": "user_uuid",
            "exchange_id": "uuid2",
            "label": "欧易跟单账户",
            "api_key": "your_api_key_here",
            "status": "pending",
            "review_reason": null,
            "approved_by": null,
            "approved_time": null,
            "last_used_time": null,
            "create_time": "2026-02-14T10:00:00Z",
            "update_time": "2026-02-14T10:00:00Z"
        }
    ]
}
```

### 3. 获取API密钥详情

**GET** `/api/v1/c/user/api-keys/{api_key_id}`

根据ID获取API密钥的详细信息。需要认证，且只能查看自己的密钥。

#### 响应示例
```json
{
    "id": "api_key_uuid1",
    "user_id": "user_uuid",
    "exchange_id": "uuid1",
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
```

### 4. 更新API密钥

**PUT** `/api/v1/c/user/api-keys/{api_key_id}`

更新API密钥的标签、权限或状态。需要认证，且只能修改自己的密钥。

#### 请求参数
```json
{
    "label": "币安主账户-修改",
    "permissions": {
        "spot_trading": true,
        "margin_trading": false,
        "futures_trading": false,
        "withdraw": false
    },
    "status": "approved"
}
```

> **说明**：所有字段均为可选，仅传入需要修改的字段。

#### 响应示例
```json
{
    "id": "api_key_uuid1",
    "user_id": "user_uuid",
    "exchange_id": "uuid1",
    "label": "币安主账户-修改",
    "api_key": "your_api_key_here",
    "status": "approved",
    "review_reason": "密钥权限设置合理",
    "approved_by": "admin",
    "approved_time": "2026-02-14T10:05:00Z",
    "last_used_time": "2026-02-14T10:10:00Z",
    "create_time": "2026-02-14T10:00:00Z",
    "update_time": "2026-02-14T10:15:00Z"
}
```

### 5. 删除API密钥

**DELETE** `/api/v1/c/user/api-keys/{api_key_id}`

删除指定的API密钥记录。需要认证，且只能删除自己的密钥。

#### 响应示例
```json
{
    "message": "API密钥删除成功"
}
```

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误（如用户名已存在、旧密码错误等） |
| 401 | 未授权访问（未提供 Token、Token 无效或已过期） |
| 403 | 权限不足（如账户已被禁用、无权访问他人资源） |
| 404 | 资源不存在（用户、交易所、API密钥不存在） |
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

- **v1.1.0** (2026-02-19): 路由前缀更新为 `/api/v1/c/user`，新增认证中间件，移除 `GET /profile` 和 `GET /exchanges` 列表接口
- **v1.0.0** (2026-02-14): 初始版本，包含完整的用户管理和交易所API管理功能

---

**注意**: 本文档描述的接口为示例接口，实际实现可能根据具体需求进行调整。
