# Admin 端 API 密钥审核 — 详细接口文档

## 一、概述

| 项目 | 说明 |
|------|------|
| 功能模块 | Admin 端 C 端用户 API 密钥审核管理 |
| 后端接口 | `src/quant_trading_system/api/users/api/admin_user.py` |
| 接口前缀 | `/api/v1/m/users/api-keys` |
| 认证方式 | Bearer Token（`Authorization: Bearer <access_token>`） |
| 权限要求 | 管理员权限（`user_type === 'admin'`） |

---

## 二、接口清单

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| 1 | `GET` | `/api/v1/m/users/api-keys` | 获取 API 密钥审核列表（支持筛选和分页） |
| 2 | `GET` | `/api/v1/m/users/api-keys/{api_key_id}` | 获取单条 API 密钥详情 |
| 3 | `PUT` | `/api/v1/m/users/api-keys/{api_key_id}/review` | 提交 API 密钥审核结果 |

---

## 三、接口详情

### 3.1 获取 API 密钥审核列表

**接口说明**

获取系统中所有用户的 API 密钥列表，支持按审核状态筛选和分页查询。

**请求**

```
GET /api/v1/m/users/api-keys
```

**Query 参数**

| 参数名 | 类型 | 必填 | 说明 | 默认值 | 约束 |
|--------|------|------|------|--------|------|
| `review_status` | `string` | 否 | 审核状态筛选：`pending` / `approved` / `rejected` | - | 可选 |
| `page` | `integer` | 否 | 页码 | `1` | `>= 1` |
| `page_size` | `integer` | 否 | 每页数量 | `50` | `1 <= size <= 100` |

**请求示例**

```http
GET /api/v1/m/users/api-keys?review_status=pending&page=1&page_size=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应体**

```json
{
  "success": true,
  "data": {
    "total": 12,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "id": 1001,
        "user_id": 501,
        "user_name": "张三",
        "exchange_id": 1,
        "exchange_name": "币安",
        "label": "我的币安主账户",
        "api_key": "abc123xyz456def789",
        "secret_key_masked": "abc***789",
        "status": "pending",
        "review_status": "pending",
        "review_reason": null,
        "reviewed_by": null,
        "reviewed_at": null,
        "permissions": {
          "spot_trading": true,
          "margin_trading": false,
          "futures_trading": false,
          "withdraw": false
        },
        "created_at": "2026-03-10T08:30:00Z",
        "updated_at": null
      }
    ],
    "statistics": {
      "pending_count": 5,
      "approved_count": 3,
      "rejected_count": 4
    }
  }
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.total` | `integer` | 符合条件的总记录数 |
| `data.page` | `integer` | 当前页码 |
| `data.page_size` | `integer` | 每页数量 |
| `data.items[]` | `array` | API 密钥列表 |
| `data.statistics` | `object` | 审核状态统计 |
| `data.statistics.pending_count` | `integer` | 待审核数量 |
| `data.statistics.approved_count` | `integer` | 已通过数量 |
| `data.statistics.rejected_count` | `integer` | 已拒绝数量 |

**错误码**

| HTTP 状态码 | 错误信息 | 说明 |
|-------------|----------|------|
| `401` | `未提供认证凭据` | Authorization 头缺失或无效 |
| `401` | `用户不存在` | Token 对应的用户不存在 |
| `403` | `权限不足，仅管理员可操作` | 当前用户不是管理员 |

---

### 3.2 获取单条 API 密钥详情

**接口说明**

根据 API 密钥 ID 获取详细的密钥信息，包括完整的 API Key（非脱敏）。

**请求**

```
GET /api/v1/m/users/api-keys/{api_key_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `api_key_id` | `integer` | 是 | API 密钥 ID |

**请求示例**

```http
GET /api/v1/m/users/api-keys/1001
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**响应体**

```json
{
  "success": true,
  "data": {
    "id": 1001,
    "user_id": 501,
    "user_name": "张三",
    "exchange_id": 1,
    "exchange_name": "币安",
    "label": "我的币安主账户",
    "api_key": "abc123xyz456def789",
    "secret_key": "sk_1234567890abcdef",
    "status": "pending",
    "review_status": "pending",
    "review_reason": null,
    "reviewed_by": null,
    "reviewed_at": null,
    "permissions": {
      "spot_trading": true,
      "margin_trading": false,
      "futures_trading": false,
      "withdraw": false
    },
    "created_at": "2026-03-10T08:30:00Z",
    "updated_at": null
  }
}
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | `integer` | API 密钥 ID |
| `data.user_id` | `integer` | 用户 ID |
| `data.user_name` | `string` | 用户名 |
| `data.exchange_id` | `integer` | 交易所 ID |
| `data.exchange_name` | `string` | 交易所名称 |
| `data.label` | `string` | 密钥标签 |
| `data.api_key` | `string` | API Key（完整显示） |
| `data.secret_key` | `string` | Secret Key（完整显示） |
| `data.status` | `string` | 密钥状态 |
| `data.review_status` | `string` | 审核状态 |
| `data.review_reason` | `string` | 审核原因 |
| `data.reviewed_by` | `string` | 审核人 |
| `data.reviewed_at` | `string` | 审核时间 |
| `data.permissions` | `object` | 权限配置 |
| `data.created_at` | `string` | 创建时间 |
| `data.updated_at` | `string` | 更新时间 |

**错误码**

| HTTP 状态码 | 错误信息 | 说明 |
|-------------|----------|------|
| `401` | `未提供认证凭据` | Authorization 头缺失或无效 |
| `401` | `用户不存在` | Token 对应的用户不存在 |
| `403` | `权限不足，仅管理员可操作` | 当前用户不是管理员 |
| `404` | `API密钥不存在` | 指定的 API 密钥 ID 不存在 |
| `404` | `用户不存在` | 密钥对应的用户不存在 |

---

### 3.3 提交 API 密钥审核结果

**接口说明**

管理员对 API 密钥进行审核，通过或拒绝申请。审核后记录审核人、审核时间和审核原因。

**请求**

```
PUT /api/v1/m/users/api-keys/{api_key_id}/review
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `api_key_id` | `integer` | 是 | API 密钥 ID |

**请求体**

```json
{
  "result": "approved",
  "reason": "密钥格式正确，权限配置合规"
}
```

**请求体字段**

| 字段名 | 类型 | 必填 | 说明 | 约束 |
|--------|------|------|------|------|
| `result` | `string` | 是 | 审核结果 | `approved` 或 `rejected` |
| `reason` | `string` | 否 | 审核原因 | 最大长度 500 字符 |

**请求示例（通过）**

```http
PUT /api/v1/m/users/api-keys/1001/review
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "result": "approved",
  "reason": "密钥格式正确，权限配置合规"
}
```

**请求示例（拒绝）**

```http
PUT /api/v1/m/users/api-keys/1001/review
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "result": "rejected",
  "reason": "检测到提现权限，存在安全风险，请关闭后重新提交"
}
```

**响应体**

```json
{
  "success": true,
  "data": {
    "id": 1001,
    "user_id": 501,
    "user_name": "张三",
    "exchange_id": 1,
    "exchange_name": "币安",
    "label": "我的币安主账户",
    "api_key": "abc123xyz456def789",
    "secret_key_masked": "abc***789",
    "status": "approved",
    "review_status": "approved",
    "review_reason": "密钥格式正确，权限配置合规",
    "reviewed_by": "admin_user",
    "reviewed_at": "2026-03-11T14:00:00Z",
    "permissions": {
      "spot_trading": true,
      "margin_trading": false,
      "futures_trading": false,
      "withdraw": false
    },
    "created_at": "2026-03-10T08:30:00Z",
    "updated_at": "2026-03-11T14:00:00Z"
  },
  "message": "API密钥审核通过成功"
}
```

**错误码**

| HTTP 状态码 | 错误信息 | 说明 |
|-------------|----------|------|
| `400` | `审核结果必须是 'approved' 或 'rejected'` | result 参数值非法 |
| `401` | `未提供认证凭据` | Authorization 头缺失或无效 |
| `401` | `用户不存在` | Token 对应的用户不存在 |
| `403` | `权限不足，仅管理员可操作` | 当前用户不是管理员 |
| `404` | `API密钥不存在` | 指定的 API 密钥 ID 不存在 |
| `409` | `该API密钥已被审核，不可重复操作` | 密钥已审核，不能重复审核 |

---

## 四、数据字典

### 4.1 审核状态（review_status）

| 值 | 含义 | 前端展示 | 颜色 |
|----|------|----------|------|
| `pending` | 待审核 | 待审核 | 琥珀色 `text-amber-400` |
| `approved` | 已通过 | 已通过 | 绿色 `text-emerald-400` |
| `rejected` | 已拒绝 | 已拒绝 | 红色 `text-red-400` |

### 4.2 密钥状态（status）

| 值 | 含义 | 说明 |
|----|------|------|
| `pending` | 待审核 | 用户提交后初始状态 |
| `approved` | 已通过 | 管理员审核通过 |
| `rejected` | 已拒绝 | 管理员审核拒绝 |

### 4.3 权限字段（permissions）

| 字段 | 含义 | 风险等级 |
|------|------|----------|
| `spot_trading` | 现货交易权限 | 低风险 |
| `margin_trading` | 杠杆交易权限 | 中风险 |
| `futures_trading` | 合约交易权限 | 高风险 |
| `withdraw` | 提现权限 | 极高风险 |

**审核建议**：
- 低风险权限：可自动通过
- 中高风险权限：需人工审核
- 提现权限：严格审核，建议拒绝或要求额外验证

---

## 五、数据库字段映射

| 响应字段 | 数据库字段 | 说明 |
|----------|------------|------|
| `review_status` | `status` | 审核状态与密钥状态使用同一字段 |
| `reviewed_by` | `approved_by` | 审核人用户名 |
| `reviewed_at` | `approved_time` | 审核时间 |
| `created_at` | `create_time` | 创建时间 |
| `updated_at` | `update_time` | 更新时间 |

---

## 六、安全规范

### 6.1 密钥脱敏规则

- **列表接口**：Secret Key 显示为 `abc***789`（前3位 + "***" + 后3位）
- **详情接口**：显示完整的 API Key 和 Secret Key（仅管理员可见）
- **日志记录**：所有 Secret Key 在日志中必须脱敏处理

### 6.2 权限控制

- 仅管理员可访问 `/api/v1/m/users/` 路径下的所有接口
- 管理员不能锁定自己的账户
- 已审核的密钥不可重复审核

### 6.3 审核流程

1. 用户提交 API 密钥申请（状态：`pending`）
2. 管理员查看待审核列表
3. 管理员审核密钥（通过/拒绝）
4. 系统记录审核信息并更新状态
5. 用户收到审核结果通知

---

## 七、前端集成建议

### 7.1 页面布局

```
API密钥审核管理
├── 顶部统计卡片
│   ├── 待审核 (5)
│   ├── 已通过 (3)
│   └── 已拒绝 (4)
├── 筛选工具栏
│   ├── 审核状态下拉框
│   ├── 搜索框
│   └── 分页控件
└── 数据表格
    ├── 用户信息列
    ├── 交易所列
    ├── 密钥标签列
    ├── 审核状态列（带颜色标识）
    ├── 创建时间列
    └── 操作列（查看详情、审核）
```

### 7.2 交互流程

1. **列表页面**：显示所有 API 密钥，支持筛选和搜索
2. **详情弹窗**：点击查看详情，显示完整密钥信息
3. **审核弹窗**：点击审核按钮，选择通过/拒绝并填写原因
4. **状态更新**：审核后自动刷新列表和统计数据

---

## 八、错误处理最佳实践

### 8.1 前端错误处理

- `401/403`：跳转到登录页面或权限不足提示页
- `404`：显示"记录不存在"提示，返回列表页
- `409`：显示"已审核"提示，刷新页面数据
- `500`：显示系统错误提示，提供重试按钮

### 8.2 后端错误日志

- 记录所有审核操作的详细日志
- 监控异常审核行为（如频繁拒绝合法申请）
- 定期清理过期的审核记录

---

## 九、版本历史

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|----------|--------|
| v1.0 | 2026-03-11 | 初始版本 | AI Assistant |

---

*文档最后更新：2026-03-11*
