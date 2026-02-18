# 量化交易系统 - 用户管理模块

## 概述

本系统是一个完整的量化交易平台用户管理模块，提供用户注册、登录、密码管理、交易所API密钥管理等功能。系统基于FastAPI框架开发，使用PostgreSQL数据库存储数据，支持JWT认证。

## 功能特性

### 用户管理
- ✅ 用户注册与登录
- ✅ 用户信息管理（昵称、邮箱、手机号、头像等）
- ✅ 密码修改与重置
- ✅ JWT令牌认证
- ✅ 用户权限管理（普通用户/管理员）

### 交易所管理
- ✅ 交易所信息管理（币安、欧易、火币等）
- ✅ 交易所API密钥管理
- ✅ API密钥审核机制
- ✅ 权限控制与安全设置

### 安全特性
- ✅ 密码哈希加密（bcrypt）
- ✅ JWT令牌认证
- ✅ API密钥安全存储
- ✅ 输入验证与错误处理
- ✅ 防SQL注入攻击

## 系统架构

```
quant_trading_system/
├── src/quant_trading_system/
│   ├── api/                          # API接口层
│   │   ├── main.py                   # FastAPI应用入口
│   │   └── routers/                  # 路由模块
│   │       ├── user.py               # 用户管理路由
│   │       └── __init__.py
│   ├── models/                       # 数据模型层
│   │   ├── user.py                   # 用户相关模型
│   │   └── __init__.py
│   ├── services/                     # 业务逻辑层
│   │   ├── user_service.py           # 用户服务
│   │   └── database/                 # 数据库服务
│   └── __init__.py
├── database/                         # 数据库相关
│   └── schema.sql                    # 数据库建表脚本
├── doc/                              # 文档
│   ├── user.md                       # 用户系统设计文档
│   └── user_api.md                   # API接口文档
├── tests/                            # 测试
│   └── test_user_api.py              # API测试脚本
└── requirements.txt                  # 依赖包列表
```

## 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 12+
- TimescaleDB（可选，用于时序数据存储）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据库配置

1. 创建PostgreSQL数据库：
```sql
CREATE DATABASE quant_trading;
```

2. 启用TimescaleDB扩展（可选）：
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

3. 执行建表脚本：
```bash
psql -d quant_trading -f database/schema.sql
```

### 配置环境变量

创建 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/quant_trading

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 邮件服务配置（用于密码重置）
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-email-password

# 应用配置
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### 启动服务

```bash
# 开发模式
uvicorn quant_trading_system.api.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn quant_trading_system.api.main:app --host 0.0.0.0 --port 8000
```

服务启动后，访问 http://localhost:8000/docs 查看API文档。

## API使用说明

### 基础URL
```
http://localhost:8000/api/v1/user
```

### 认证方式
所有需要认证的API都需要在请求头中包含JWT令牌：
```
Authorization: Bearer <your-jwt-token>
```

### 主要API接口

#### 1. 用户注册
```http
POST /api/v1/user/register
Content-Type: application/json

{
    "username": "testuser",
    "nickname": "测试用户",
    "email": "test@example.com",
    "password": "password123",
    "phone": "13800138000",
    "avatar_url": "https://example.com/avatar.jpg"
}
```

#### 2. 用户登录
```http
POST /api/v1/user/login
Content-Type: application/json

{
    "username": "testuser",
    "password": "password123"
}
```

#### 3. 获取用户信息
```http
GET /api/v1/user/profile
Authorization: Bearer <token>
```

#### 4. 修改用户信息
```http
PUT /api/v1/user/profile
Authorization: Bearer <token>
Content-Type: application/json

{
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "phone": "13900139000"
}
```

#### 5. 修改密码
```http
POST /api/v1/user/password/change
Authorization: Bearer <token>
Content-Type: application/json

{
    "old_password": "oldpassword",
    "new_password": "newpassword"
}
```

#### 6. 获取交易所列表
```http
GET /api/v1/user/exchanges
Authorization: Bearer <token>
```

#### 7. 添加API密钥
```http
POST /api/v1/user/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
    "exchange_id": "uuid",
    "label": "币安主账户",
    "api_key": "your_api_key",
    "secret_key": "your_secret_key",
    "passphrase": "your_passphrase",
    "permissions": {
        "spot_trading": true,
        "margin_trading": false,
        "futures_trading": false,
        "withdraw": false
    }
}
```

#### 8. 获取API密钥列表
```http
GET /api/v1/user/api-keys
Authorization: Bearer <token>
```

## 数据库设计

### 核心数据表

#### 1. user_info（用户信息表）
- id: UUID主键
- username: 用户名（唯一）
- nickname: 昵称
- password_hash: 密码哈希
- email: 邮箱（唯一）
- phone: 手机号
- user_type: 用户类型（customer/admin）
- status: 用户状态（active/inactive/locked）
- 公共字段：create_by, create_time, update_by, update_time, enable_flag

#### 2. exchange_info（交易所信息表）
- id: UUID主键
- exchange_code: 交易所代码（binance/okx/huobi）
- exchange_name: 交易所名称
- exchange_type: 交易类型（spot/futures/margin）
- base_url: API基础URL
- status: 状态（active/inactive）
- 公共字段：create_by, create_time, update_by, update_time, enable_flag

#### 3. user_exchange_api（用户交易所API表）
- id: UUID主键
- user_id: 用户ID（外键）
- exchange_id: 交易所ID（外键）
- label: API密钥标签
- api_key: API密钥
- secret_key: Secret密钥
- status: 审核状态（pending/approved/rejected/disabled）
- review_reason: 审核原因
- 公共字段：create_by, create_time, update_by, update_time, enable_flag

### 时序数据表（TimescaleDB）

#### 4. kline_data（K线数据表）
- 时序表，用于存储K线数据
- 支持高效的时间范围查询

#### 5. tick_data（实时行情表）
- 时序表，用于存储实时行情数据

#### 6. depth_data（深度数据表）
- 时序表，用于存储深度数据

## 安全最佳实践

### 1. 密码安全
- 使用bcrypt进行密码哈希
- 密码最小长度6位
- 支持密码复杂度验证

### 2. API密钥安全
- API密钥需要后台审核
- 支持权限最小化原则
- 建议定期更换API密钥

### 3. 数据传输安全
- 使用HTTPS加密传输
- JWT令牌过期时间设置
- 敏感信息不记录日志

### 4. 数据库安全
- 使用参数化查询防止SQL注入
- 敏感字段加密存储
- 定期备份数据库

## 测试

### 运行API测试
```bash
python tests/test_user_api.py
```

### 测试覆盖功能
- ✅ 用户注册
- ✅ 用户登录
- ✅ 用户信息获取
- ✅ 用户信息更新
- ✅ 密码修改
- ✅ 交易所列表获取
- ✅ API密钥添加

## 部署建议

### 开发环境
- 使用SQLite或本地PostgreSQL
- 启用调试模式
- 使用自签名证书测试HTTPS

### 生产环境
- 使用PostgreSQL + TimescaleDB
- 配置SSL证书
- 设置防火墙规则
- 启用数据库备份
- 配置监控和告警

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "quant_trading_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL配置
   - 确认PostgreSQL服务运行状态
   - 验证数据库用户权限

2. **JWT令牌无效**
   - 检查JWT_SECRET_KEY配置
   - 确认令牌未过期
   - 验证令牌签名算法

3. **API密钥审核失败**
   - 检查权限设置是否合理
   - 确认交易所API接口可用性
   - 验证网络连接

### 日志查看
```bash
# 查看应用日志
tail -f /var/log/quant_trading.log

# 查看数据库日志
tail -f /var/log/postgresql/postgresql-*.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 编写测试用例
5. 提交Pull Request

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 联系方式

如有问题或建议，请联系：
- 邮箱：support@quant-trading.com
- 项目地址：https://github.com/your-org/quant-trading-system

---

**注意**: 本系统为量化交易平台的核心组件，部署到生产环境前请进行充分的安全测试和性能测试。
