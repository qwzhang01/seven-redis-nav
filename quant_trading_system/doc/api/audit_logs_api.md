# 日志审计 API 文档

## 概述

日志审计模块提供系统日志、交易日志、风控日志和审计日志的查询接口，以及风控告警管理功能。仅限管理员（Admin）使用。

## 基础信息

- **基础URL**: `/api/v1/m/logs`
- **认证方式**: JWT Bearer Token（需管理员权限）
- **数据格式**: JSON

---

## 接口列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/logs/system` | 系统操作日志 |
| GET | `/api/v1/m/logs/trading` | 交易日志 |
| GET | `/api/v1/m/logs/risk` | 风控日志 |
| GET | `/api/v1/m/logs/audit` | 审计日志（全量） |
| GET | `/api/v1/m/logs/risk/alerts` | 风控告警列表 |
| PUT | `/api/v1/m/logs/risk/alerts/{alert_id}/resolve` | 标记告警已处理 |

---

## 接口详情

### 1. 系统操作日志

**GET** `/api/v1/m/logs/system`

查询系统级别的操作日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别过滤：`DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| username | string | 否 | - | 用户名过滤 |
| start_time | string | 否 | - | 开始时间（ISO 8601 格式） |
| end_time | string | 否 | - | 结束时间（ISO 8601 格式） |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "log_time": "2025-03-01T10:00:00",
      "log_level": "INFO",
      "log_category": "system",
      "user_id": "123",
      "username": "admin",
      "action": "login",
      "resource_type": "user",
      "resource_id": "123",
      "request_ip": "192.168.1.1",
      "request_path": "/api/v1/c/user/login",
      "request_method": "POST",
      "response_status": 200,
      "duration_ms": 50,
      "message": "用户登录成功",
      "extra_data": null
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 2
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array | 日志记录列表 |
| items[].id | integer | 日志ID |
| items[].log_time | string | 日志时间（ISO格式） |
| items[].log_level | string | 日志级别 |
| items[].log_category | string | 日志分类 |
| items[].user_id | string | 用户ID |
| items[].username | string | 用户名 |
| items[].action | string | 操作类型 |
| items[].resource_type | string | 资源类型 |
| items[].resource_id | string | 资源ID |
| items[].request_ip | string | 请求IP |
| items[].request_path | string | 请求路径 |
| items[].request_method | string | 请求方法 |
| items[].response_status | integer | 响应状态码 |
| items[].duration_ms | integer | 请求耗时（毫秒） |
| items[].message | string | 日志消息 |
| items[].extra_data | object | 额外数据 |
| total | integer | 总数量 |
| page | integer | 当前页码 |
| pages | integer | 总页数 |

---

### 2. 交易日志

**GET** `/api/v1/m/logs/trading`

查询交易相关的操作日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别过滤 |
| username | string | 否 | - | 用户名过滤 |
| start_time | string | 否 | - | 开始时间（ISO 8601 格式） |
| end_time | string | 否 | - | 结束时间（ISO 8601 格式） |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 10,
      "log_time": "2025-03-01T12:30:00",
      "log_level": "INFO",
      "log_category": "trading",
      "user_id": "456",
      "username": "trader01",
      "action": "place_order",
      "resource_type": "order",
      "resource_id": "order_789",
      "request_ip": "192.168.1.2",
      "request_path": "/api/v1/c/trading/orders",
      "request_method": "POST",
      "response_status": 200,
      "duration_ms": 120,
      "message": "下单成功",
      "extra_data": null
    }
  ],
  "total": 50,
  "page": 1,
  "pages": 1
}
```

> 响应字段说明同「系统操作日志」。

---

### 3. 风控日志

**GET** `/api/v1/m/logs/risk`

查询风控相关的操作日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别过滤 |
| start_time | string | 否 | - | 开始时间（ISO 8601 格式） |
| end_time | string | 否 | - | 结束时间（ISO 8601 格式） |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

> **注意**：风控日志不支持按用户名过滤。

#### 响应示例

```json
{
  "items": [
    {
      "id": 20,
      "log_time": "2025-03-01T14:00:00",
      "log_level": "WARNING",
      "log_category": "risk",
      "user_id": null,
      "username": null,
      "action": "drawdown_check",
      "resource_type": "strategy",
      "resource_id": "strategy_001",
      "request_ip": null,
      "request_path": null,
      "request_method": null,
      "response_status": null,
      "duration_ms": null,
      "message": "策略最大回撤超限",
      "extra_data": {"drawdown": -0.15}
    }
  ],
  "total": 10,
  "page": 1,
  "pages": 1
}
```

> 响应字段说明同「系统操作日志」。

---

### 4. 审计日志（全量）

**GET** `/api/v1/m/logs/audit`

查询所有类别的审计日志，支持多维度过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| category | string | 否 | - | 日志分类：`system` / `trading` / `strategy` / `user` / `risk` / `market` |
| level | string | 否 | - | 日志级别过滤 |
| username | string | 否 | - | 用户名过滤 |
| action | string | 否 | - | 操作关键词过滤（模糊匹配） |
| start_time | string | 否 | - | 开始时间（ISO 8601 格式） |
| end_time | string | 否 | - | 结束时间（ISO 8601 格式） |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "log_time": "2025-03-01T10:00:00",
      "log_level": "INFO",
      "log_category": "system",
      "user_id": "123",
      "username": "admin",
      "action": "login",
      "resource_type": "user",
      "resource_id": "123",
      "request_ip": "192.168.1.1",
      "request_path": "/api/v1/c/user/login",
      "request_method": "POST",
      "response_status": 200,
      "duration_ms": 50,
      "message": "用户登录成功",
      "extra_data": null
    }
  ],
  "total": 500,
  "page": 1,
  "pages": 10
}
```

> 响应字段说明同「系统操作日志」。

---

### 5. 风控告警列表

**GET** `/api/v1/m/logs/risk/alerts`

查询风控告警记录，支持按严重程度、类型、处理状态过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| severity | string | 否 | - | 严重程度：`info` / `warning` / `critical` |
| alert_type | string | 否 | - | 告警类型：`drawdown` / `position_limit` / `loss_limit` / `volatility` |
| is_resolved | boolean | 否 | - | 是否已处理 |
| strategy_id | string | 否 | - | 策略ID过滤 |
| page | integer | 否 | `1` | 页码（≥1） |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "alert_time": "2025-03-01T14:00:00",
      "alert_type": "drawdown",
      "severity": "critical",
      "strategy_id": "strategy_001",
      "symbol": "BTCUSDT",
      "user_id": "123",
      "title": "最大回撤告警",
      "message": "策略 strategy_001 回撤超过阈值 10%",
      "trigger_value": 0.15,
      "threshold_value": 0.10,
      "is_resolved": false,
      "resolved_at": null,
      "resolved_by": null,
      "extra_data": null,
      "created_at": "2025-03-01T14:00:00"
    }
  ],
  "total": 5,
  "page": 1,
  "pages": 1
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array | 告警记录列表 |
| items[].id | integer | 告警ID |
| items[].alert_time | string | 告警时间（ISO格式） |
| items[].alert_type | string | 告警类型 |
| items[].severity | string | 严重程度 |
| items[].strategy_id | string | 关联策略ID |
| items[].symbol | string | 交易对 |
| items[].user_id | string | 关联用户ID |
| items[].title | string | 告警标题 |
| items[].message | string | 告警消息 |
| items[].trigger_value | float | 触发值 |
| items[].threshold_value | float | 阈值 |
| items[].is_resolved | boolean | 是否已处理 |
| items[].resolved_at | string | 处理时间 |
| items[].resolved_by | string | 处理人 |
| items[].extra_data | object | 额外数据 |
| items[].created_at | string | 创建时间 |
| total | integer | 总数量 |
| page | integer | 当前页码 |
| pages | integer | 总页数 |

---

### 6. 标记告警已处理

**PUT** `/api/v1/m/logs/risk/alerts/{alert_id}/resolve`

将指定的风控告警标记为已处理状态。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| alert_id | integer | 告警ID |

#### 请求体（ResolveAlertRequest）

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| resolved_by | string | 否 | `"admin"` | 处理人 |
| note | string | 否 | - | 处理备注 |

#### 请求示例

```json
{
  "resolved_by": "admin",
  "note": "已检查，策略参数已调整"
}
```

#### 响应示例

```json
{
  "success": true,
  "alert": {
    "id": 1,
    "alert_time": "2025-03-01T14:00:00",
    "alert_type": "drawdown",
    "severity": "critical",
    "strategy_id": "strategy_001",
    "symbol": "BTCUSDT",
    "user_id": "123",
    "title": "最大回撤告警",
    "message": "策略 strategy_001 回撤超过阈值 10%",
    "trigger_value": 0.15,
    "threshold_value": 0.10,
    "is_resolved": true,
    "resolved_at": "2025-03-01T15:00:00",
    "resolved_by": "admin",
    "extra_data": {"resolve_note": "已检查，策略参数已调整"},
    "created_at": "2025-03-01T14:00:00"
  },
  "message": "告警已标记为处理"
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 告警不存在 |
| 400 | 告警已处理 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误或告警已处理 |
| 404 | 告警不存在 |
| 500 | 服务器内部错误 |
