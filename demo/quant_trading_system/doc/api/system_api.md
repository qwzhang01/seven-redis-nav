# 系统管理 API 文档

## 概述

系统管理模块提供系统信息查询、配置管理、健康检查、性能指标监控和全局枚举查询等功能。

## 基础信息

- **M端系统管理URL**: `/api/v1/m/system`
- **M端健康检查URL**: `/api/v1/m/health`
- **C端枚举查询URL**: `/api/v1/c/enum`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### M端 — 系统管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/system/info` | 获取系统基本信息 |
| GET | `/api/v1/m/system/config` | 获取系统配置信息 |
| GET | `/api/v1/m/system/health` | 系统健康检查 |
| GET | `/api/v1/m/system/metrics` | 获取系统性能指标 |

### M端 — 健康检查（详细）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/health/` | 基础健康检查 |
| GET | `/api/v1/m/health/db` | 数据库健康检查 |
| GET | `/api/v1/m/health/full` | 完整健康检查（含系统资源） |
| GET | `/api/v1/m/health/ready` | 就绪检查（K8s readiness） |
| GET | `/api/v1/m/health/live` | 存活检查（K8s liveness） |
| GET | `/api/v1/m/health/metrics` | 系统硬件指标 |

### M端 — 日志审计

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/logs/system` | 系统操作日志 |
| GET | `/api/v1/m/logs/trading` | 交易日志 |
| GET | `/api/v1/m/logs/risk` | 风控日志 |
| GET | `/api/v1/m/logs/audit` | 审计日志（全量） |
| GET | `/api/v1/m/logs/risk/alerts` | 风控告警列表 |
| PUT | `/api/v1/m/logs/risk/alerts/{alert_id}/resolve` | 标记告警已处理 |

### C端 — 全局枚举查询

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/enum/list` | 获取所有可用枚举名称 |
| GET | `/api/v1/c/enum/{enum_name}` | 按名称获取枚举值 |
| GET | `/api/v1/c/enum/batch/{enum_names}` | 批量获取枚举值 |

---

## M端系统管理接口详情

### 1. 获取系统基本信息

**GET** `/api/v1/m/system/info`

#### 响应示例

```json
{
  "name": "quant-trading-system",
  "version": "1.0.0",
  "env": "development",
  "debug": true,
  "trading_mode": "paper",
  "trading_running": true
}
```

---

### 2. 获取系统配置信息

**GET** `/api/v1/m/system/config`

返回系统的公开配置参数（不含敏感信息）。

#### 响应示例

```json
{
  "trading": {
    "order_timeout": 30,
    "default_slippage": 0.01,
    "default_commission_rate": 0.001
  },
  "strategy": {
    "max_concurrent_strategies": 10,
    "backtest_start_capital": 1000000
  }
}
```

---

### 3. 系统健康检查

**GET** `/api/v1/m/system/health`

检查系统各核心组件的运行状态。

#### 响应示例

```json
{
  "status": "healthy",
  "checks": {
    "api": true,
    "event_engine": true,
    "market_service": true,
    "strategy_engine": true,
    "trading_engine": true
  }
}
```

---

### 4. 获取系统性能指标

**GET** `/api/v1/m/system/metrics`

查询系统各核心组件的性能统计数据。

---

## M端健康检查接口详情

### 1. 基础健康检查

**GET** `/api/v1/m/health/`

检查 API 服务是否正常运行。

---

### 2. 数据库健康检查

**GET** `/api/v1/m/health/db`

检查数据库连接是否正常。

---

### 3. 完整健康检查

**GET** `/api/v1/m/health/full`

检查所有关键组件的健康状态，包括 API 服务、数据库、关键数据表（user_info、exchange_info、user_exchange_api），以及系统资源（CPU、内存、磁盘、进程）。

#### 响应示例

```json
{
  "status": "healthy",
  "message": "系统运行正常",
  "timestamp": "2025-02-24T19:00:00Z",
  "version": "1.0.0",
  "checks": {
    "api": {"status": "healthy", "message": "API服务正常"},
    "database": {"status": "healthy", "message": "数据库连接正常"},
    "memory": {
      "status": "healthy",
      "message": "内存使用率: 45.2%",
      "details": {"total": "16GB", "used": "7GB", "percent": 45.2}
    },
    "cpu": {
      "status": "healthy",
      "message": "CPU使用率: 12.5%"
    },
    "disk": {
      "status": "healthy",
      "message": "磁盘使用率: 60.1%"
    }
  }
}
```

---

### 4. K8s 探针

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/health/ready` | 就绪检查（返回 200/503） |
| GET | `/api/v1/m/health/live` | 存活检查（返回 200/503） |

---

### 5. 系统硬件指标

**GET** `/api/v1/m/health/metrics`

返回系统运行指标，包含平台信息、CPU、内存、磁盘和网络统计。

---

## M端日志审计接口详情

### 1. 系统操作日志

**GET** `/api/v1/m/logs/system`

查询系统级别的操作日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL |
| username | string | 否 | - | 用户名过滤 |
| start_time | datetime | 否 | - | 开始时间 |
| end_time | datetime | 否 | - | 结束时间 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `50` | 每页数量（1-200） |

---

### 2. 交易日志

**GET** `/api/v1/m/logs/trading`

查询交易相关的操作日志记录。查询参数与系统操作日志相同。

---

### 3. 风控日志

**GET** `/api/v1/m/logs/risk`

查询风控相关的操作日志记录。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| level | string | 否 | - | 日志级别 |
| start_time | datetime | 否 | - | 开始时间 |
| end_time | datetime | 否 | - | 结束时间 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `50` | 每页数量 |

---

### 4. 审计日志（全量）

**GET** `/api/v1/m/logs/audit`

查询所有类别的审计日志，支持多维度过滤。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| category | string | 否 | - | 日志分类: system/trading/strategy/user/risk/market |
| level | string | 否 | - | 日志级别 |
| username | string | 否 | - | 用户名过滤 |
| action | string | 否 | - | 操作关键词过滤 |
| start_time | datetime | 否 | - | 开始时间 |
| end_time | datetime | 否 | - | 结束时间 |
| page | integer | 否 | `1` | 页码 |
| page_size | integer | 否 | `50` | 每页数量 |

---

### 5. 风控告警列表

**GET** `/api/v1/m/logs/risk/alerts`

查询风控告警记录。

#### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| severity | string | 否 | 严重程度: info/warning/critical |
| alert_type | string | 否 | 告警类型: drawdown/position_limit/loss_limit/volatility |
| is_resolved | boolean | 否 | 是否已处理 |
| strategy_id | string | 否 | 策略ID过滤 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

---

### 6. 标记告警已处理

**PUT** `/api/v1/m/logs/risk/alerts/{alert_id}/resolve`

将指定的风控告警标记为已处理状态。

#### 请求体

| 字段 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| resolved_by | string | 否 | `"admin"` | 处理人 |
| note | string | 否 | - | 处理备注 |

---

## C端枚举查询接口详情

### 1. 获取所有可用枚举名称

**GET** `/api/v1/c/enum/list`

返回系统中注册的所有枚举类名称。

#### 响应示例

```json
{
  "enums": ["RiskLevel", "StrategyStatus", "MarketType", "StrategyType", ...]
}
```

---

### 2. 按名称获取枚举值

**GET** `/api/v1/c/enum/{enum_name}`

根据枚举名称返回该枚举的所有选项。

#### 响应示例

```json
{
  "name": "RiskLevel",
  "items": [
    {"value": "low", "label": "低风险", "description": "保守型策略，回撤较小"},
    {"value": "medium", "label": "中风险", "description": "均衡型策略"},
    {"value": "high", "label": "高风险", "description": "激进型策略"}
  ]
}
```

---

### 3. 批量获取枚举值

**GET** `/api/v1/c/enum/batch/{enum_names}`

一次请求获取多个枚举信息，枚举名称用英文逗号分隔。

**示例**: `/api/v1/c/enum/batch/RiskLevel,StrategyStatus,MarketType`

#### 响应示例

```json
{
  "enums": {
    "RiskLevel": [...],
    "StrategyStatus": [...],
    "MarketType": [...]
  }
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 枚举/告警不存在 |
| 503 | 系统未启动 |
