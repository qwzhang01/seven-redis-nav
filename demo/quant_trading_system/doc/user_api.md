# 用户管理与交易所API接口文档

## 概述

本文档描述了量化交易系统的用户管理和交易所API管理接口。所有接口都遵循RESTful设计原则，使用JSON格式进行数据交换。

## 基础信息

- **基础URL**: `/api/v1/user`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证说明

所有需要认证的接口都需要在请求头中包含有效的JWT令牌：

```http
Authorization: Bearer <token>
```

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
    "error_type": "错误类型"
}
```

## 用户管理接口

### 1. 用户注册

**POST** `/api/v1/user/register`

注册新用户账户。

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
    "success": true,
    "data": {
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
        "status": "active"
    },
    "message": "注册成功"
}
```

### 2. 用户登录

**POST** `/api/v1/user/login`

用户登录获取访问令牌。

#### 请求参数
```json
{
    "username": "testuser",
    "password": "password123"
}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
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
            "status": "active"
        }
    },
    "message": "登录成功"
}
```

### 3. 修改密码

**POST** `/api/v1/user/password/change`

修改当前登录用户的密码。

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
    "success": true,
    "data": null,
    "message": "密码修改成功"
}
```

### 4. 忘记密码重置

**POST** `/api/v1/user/password/reset`

通过邮箱验证码重置密码。

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
    "success": true,
    "data": null,
    "message": "密码重置成功"
}
```

### 5. 获取用户信息

**GET** `/api/v1/user/profile`

获取当前登录用户的详细信息。

#### 响应示例
```json
{
    "success": true,
    "data": {
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
        "status": "active"
    },
    "message": "获取成功"
}
```

### 6. 更新用户信息

**PUT** `/api/v1/user/profile`

更新当前登录用户的个人信息。

#### 请求参数
```json
{
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "phone": "13900139000",
    "avatar_url": "https://example.com/new-avatar.jpg"
}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
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
        "status": "active"
    },
    "message": "更新成功"
}
```

## 交易所管理接口

### 1. 获取交易所列表

**GET** `/api/v1/user/exchanges`

获取支持的交易所列表，支持按类型和状态筛选。

#### 查询参数
- `exchange_type` (可选): spot/futures/margin
- `status` (可选): active/inactive

#### 响应示例
```json
{
    "success": true,
    "data": {
        "total": 3,
        "items": [
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
            },
            {
                "id": "uuid2",
                "exchange_code": "okx",
                "exchange_name": "欧易",
                "exchange_type": "spot",
                "base_url": "https://www.okx.com",
                "api_doc_url": "https://www.okx.com/docs/",
                "status": "active",
                "supported_pairs": ["BTC-USDT", "ETH-USDT", "OKB-USDT"],
                "rate_limits": {"requests_per_minute": 300},
                "create_time": "2026-02-14T10:00:00Z",
                "update_time": "2026-02-14T10:00:00Z"
            }
        ]
    },
    "message": "获取成功"
}
```

### 2. 获取交易所详情

**GET** `/api/v1/user/exchanges/{exchange_id}`

根据交易所ID获取详细信息。

#### 响应示例
```json
{
    "success": true,
    "data": {
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
    },
    "message": "获取成功"
}
```

## API密钥管理接口

### 1. 添加API密钥

**POST** `/api/v1/user/api-keys`

为用户添加交易所API密钥，需要经过后台审核。

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
    "success": true,
    "data": {
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
    },
    "message": "API密钥添加成功，等待审核"
}
```

### 2. 获取API密钥列表

**GET** `/api/v1/user/api-keys`

获取当前用户的API密钥列表，支持按状态筛选。

#### 查询参数
- `status` (可选): pending/approved/rejected/disabled

#### 响应示例
```json
{
    "success": true,
    "data": {
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
    },
    "message": "获取成功"
}
```

### 3. 获取API密钥详情

**GET** `/api/v1/user/api-keys/{api_key_id}`

根据ID获取API密钥的详细信息。

#### 响应示例
```json
{
    "success": true,
    "data": {
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
    "message": "获取成功"
}
```

### 4. 更新API密钥

**PUT** `/api/v1/user/api-keys/{api_key_id}`

更新API密钥的标签、权限或状态。

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

#### 响应示例
```json
{
    "success": true,
    "data": {
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
    },
    "message": "更新成功"
}
```

### 5. 删除API密钥

**DELETE** `/api/v1/user/api-keys/{api_key_id}`

删除指定的API密钥记录。

#### 响应示例
```json
{
    "success": true,
    "data": null,
    "message": "API密钥删除成功"
}
```

## 错误码说明

| 错误码 | 错误类型 | 描述 |
|--------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权访问 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 500 | Internal Server Error | 服务器内部错误 |

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
import json

# 基础配置
BASE_URL = "http://localhost:8000/api/v1/user"

# 登录获取令牌
def login(username, password):
    response = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["data"]["access_token"]
    else:
        raise Exception(f"登录失败: {response.text}")

# 获取用户信息
def get_user_profile(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/profile", headers=headers)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"获取用户信息失败: {response.text}")

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
        return response.json()["data"]
    else:
        raise Exception(f"添加API密钥失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    try:
        # 登录
        token = login("testuser", "password123")
        print("登录成功")
        
        # 获取用户信息
        profile = get_user_profile(token)
        print(f"用户信息: {profile['nickname']}")
        
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

- **v1.0.0** (2026-02-14): 初始版本，包含完整的用户管理和交易所API管理功能

---

**注意**: 本文档描述的接口为示例接口，实际实现可能根据具体需求进行调整。
