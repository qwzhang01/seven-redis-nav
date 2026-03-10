# 系统管理 API 文档

## 概述

系统管理模块提供系统信息查询、配置管理、健康检查、性能监控和全局枚举查询等功能，涵盖 Admin 端系统管理接口、健康检查接口以及 C 端枚举查询接口。

## 基础信息

- **Admin 系统管理 URL**: `/api/v1/m/system`
- **Admin 健康检查 URL**: `/api/v1/m/health`
- **C 端枚举查询 URL**: `/api/v1/c/enum`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### Admin 端 - 系统管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/system/info` | 获取系统基本信息 |
| GET | `/api/v1/m/system/config` | 获取系统配置信息 |
| GET | `/api/v1/m/system/health` | 系统健康检查（简要） |
| GET | `/api/v1/m/system/metrics` | 获取系统性能指标 |

### Admin 端 - 健康检查

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/health/` | 基础健康检查 |
| GET | `/api/v1/m/health/db` | 数据库健康检查 |
| GET | `/api/v1/m/health/full` | 完整健康检查 |
| GET | `/api/v1/m/health/ready` | 就绪检查（K8s 就绪探针） |
| GET | `/api/v1/m/health/live` | 存活检查（K8s 存活探针） |
| GET | `/api/v1/m/health/metrics` | 系统指标接口 |

### C 端 - 枚举查询

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/enum/list` | 获取所有可用枚举名称列表 |
| GET | `/api/v1/c/enum/{enum_name}` | 按枚举名称获取枚举 KV 信息 |
| GET | `/api/v1/c/enum/batch/{enum_names}` | 批量获取多个枚举 KV 信息 |

---

## 接口详情

---

## 一、Admin 端 - 系统管理

### 1. 获取系统基本信息

**GET** `/api/v1/m/system/info`

查询量化交易系统的版本、环境、运行状态等基本信息。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 系统名称 |
| version | string | 系统版本号 |
| env | string | 运行环境（development/production） |
| debug | boolean | 调试模式状态 |
| trading_mode | string \| null | 交易模式（live/backtest），系统未启动时为 null |
| trading_running | boolean | 交易系统是否正在运行 |

#### 响应示例

```json
{
  "name": "QuantTradingSystem",
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

查询系统的公开配置参数，不包含敏感信息如 API 密钥等。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| trading | object | 交易相关配置 |
| trading.order_timeout | number | 订单超时时间 |
| trading.default_slippage | number | 默认滑点率 |
| trading.default_commission_rate | number | 默认手续费率 |
| strategy | object | 策略相关配置 |
| strategy.max_concurrent_strategies | integer | 最大并发策略数 |
| strategy.backtest_start_capital | number | 回测初始资金 |

#### 响应示例

```json
{
  "trading": {
    "order_timeout": 30,
    "default_slippage": 0.0001,
    "default_commission_rate": 0.0004
  },
  "strategy": {
    "max_concurrent_strategies": 10,
    "backtest_start_capital": 1000000.0
  }
}
```

---

### 3. 系统健康检查（简要）

**GET** `/api/v1/m/system/health`

检查系统各核心组件的运行状态，评估系统整体健康度。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 系统整体状态（healthy/degraded） |
| checks | object | 各组件健康状态检查结果 |
| checks.api | boolean | API 服务状态 |
| checks.event_engine | boolean | 事件引擎状态 |
| checks.market_service | boolean | 市场服务状态 |
| checks.strategy_engine | boolean | 策略引擎状态 |
| checks.trading_engine | boolean | 交易引擎状态 |

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

查询系统各核心组件的性能统计数据和运行指标。当系统未启动时返回空的统计信息字典。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| event_engine | object | 事件引擎统计信息 |
| market_service | object | 市场服务统计信息 |
| strategy_engine | object | 策略引擎统计信息 |
| trading_engine | object | 交易引擎统计信息 |
| risk_manager | object | 风险管理器统计信息 |

#### 响应示例

```json
{
  "event_engine": {},
  "market_service": {},
  "strategy_engine": {},
  "trading_engine": {},
  "risk_manager": {}
}
```

---

## 二、Admin 端 - 健康检查

### 1. 基础健康检查

**GET** `/api/v1/m/health/`

检查 API 服务是否正常运行，返回标准的健康检查响应。

#### 响应字段（HealthResponse）

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 健康状态（healthy/unhealthy） |
| message | string | 状态描述 |
| timestamp | string | 检查时间（ISO 格式） |
| version | string | 系统版本号 |
| checks | object \| null | 各组件检查结果 |

#### 响应示例

```json
{
  "status": "healthy",
  "message": "服务运行正常",
  "timestamp": "2025-01-01T12:00:00",
  "version": "1.0.0",
  "checks": {
    "api": {
      "status": "healthy",
      "message": "API服务正常"
    }
  }
}
```

---

### 2. 数据库健康检查

**GET** `/api/v1/m/health/db`

检查数据库连接是否正常。

#### 响应示例

**正常：**

```json
{
  "status": "healthy",
  "message": "数据库连接正常",
  "timestamp": "2025-01-01T12:00:00",
  "version": "",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "数据库连接正常"
    }
  }
}
```

**异常：**

```json
{
  "status": "unhealthy",
  "message": "数据库连接失败: Connection refused",
  "timestamp": "2025-01-01T12:00:00",
  "version": "",
  "checks": {
    "database": {
      "status": "unhealthy",
      "message": "数据库连接异常: Connection refused"
    }
  }
}
```

---

### 3. 完整健康检查

**GET** `/api/v1/m/health/full`

检查所有关键组件的健康状态，包括 API 服务、数据库、关键数据表、系统资源（内存/CPU/磁盘）和进程信息。

#### 响应 checks 包含的检查项

| 检查项 | 描述 |
|--------|------|
| api | API 服务状态 |
| database | 数据库连接状态 |
| user_table | 用户表状态 |
| exchange_table | 交易所表状态 |
| api_key_table | API 密钥表状态 |
| memory | 内存使用情况（使用率 ≥90% 为 warning） |
| cpu | CPU 使用率（使用率 ≥80% 为 warning） |
| disk | 磁盘使用情况（使用率 ≥90% 为 warning） |
| process | 进程运行信息（PID、内存占用、CPU 占用） |

#### 响应示例

```json
{
  "status": "healthy",
  "message": "系统运行正常",
  "timestamp": "2025-01-01T12:00:00",
  "version": "1.0.0",
  "checks": {
    "api": {
      "status": "healthy",
      "message": "API服务正常"
    },
    "database": {
      "status": "healthy",
      "message": "数据库连接正常"
    },
    "user_table": {
      "status": "healthy",
      "message": "用户表正常"
    },
    "exchange_table": {
      "status": "healthy",
      "message": "交易所表正常"
    },
    "api_key_table": {
      "status": "healthy",
      "message": "API密钥表正常"
    },
    "memory": {
      "status": "healthy",
      "message": "内存使用率: 45.2%",
      "details": {
        "total": "16GB",
        "used": "7GB",
        "percent": 45.2
      }
    },
    "cpu": {
      "status": "healthy",
      "message": "CPU使用率: 12.5%",
      "details": {
        "cores": 8,
        "percent": 12.5
      }
    },
    "disk": {
      "status": "healthy",
      "message": "磁盘使用率: 60.3%",
      "details": {
        "total": "512GB",
        "used": "308GB",
        "percent": 60.3
      }
    },
    "process": {
      "status": "healthy",
      "message": "进程运行正常",
      "details": {
        "pid": 12345,
        "memory_mb": 128,
        "cpu_percent": 2.5
      }
    }
  }
}
```

---

### 4. 就绪检查

**GET** `/api/v1/m/health/ready`

用于 Kubernetes 就绪探针，检查服务是否已准备好接收流量。

#### 响应示例

**就绪（200）：**

```json
{
  "status": "ready",
  "timestamp": "2025-01-01T12:00:00"
}
```

**未就绪（503）：**

```json
{
  "status": "not ready",
  "timestamp": "2025-01-01T12:00:00"
}
```

---

### 5. 存活检查

**GET** `/api/v1/m/health/live`

用于 Kubernetes 存活探针，检查服务是否仍在运行。

#### 响应示例

**存活（200）：**

```json
{
  "status": "alive",
  "timestamp": "2025-01-01T12:00:00"
}
```

**异常（503）：**

```json
{
  "status": "dead",
  "timestamp": "2025-01-01T12:00:00"
}
```

---

### 6. 系统指标接口

**GET** `/api/v1/m/health/metrics`

返回系统运行指标，可用于监控系统，包含系统平台信息、CPU、内存、磁盘和网络信息。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| timestamp | string | 采集时间（ISO 格式） |
| system | object | 系统平台信息 |
| system.platform | string | 操作系统平台 |
| system.python_version | string | Python 版本 |
| system.hostname | string | 主机名 |
| system.uptime | number | 系统启动时间戳 |
| cpu | object | CPU 信息 |
| cpu.cores | integer | CPU 核心数 |
| cpu.usage_percent | number | CPU 使用率 |
| cpu.load_average | array \| null | 系统负载平均值 |
| memory | object | 内存信息 |
| memory.total | integer | 总内存（字节） |
| memory.available | integer | 可用内存（字节） |
| memory.used | integer | 已用内存（字节） |
| memory.percent | number | 内存使用率 |
| disk | object | 磁盘信息 |
| disk.total | integer | 总磁盘空间（字节） |
| disk.used | integer | 已用磁盘空间（字节） |
| disk.free | integer | 可用磁盘空间（字节） |
| disk.percent | number | 磁盘使用率 |
| network | object | 网络信息 |
| network.bytes_sent | integer | 发送字节数 |
| network.bytes_recv | integer | 接收字节数 |
| network.packets_sent | integer | 发送数据包数 |
| network.packets_recv | integer | 接收数据包数 |

#### 响应示例

```json
{
  "timestamp": "2025-01-01T12:00:00",
  "system": {
    "platform": "Linux-5.15.0-x86_64",
    "python_version": "3.11.5",
    "hostname": "quant-server",
    "uptime": 1704067200
  },
  "cpu": {
    "cores": 8,
    "usage_percent": 12.5,
    "load_average": [1.2, 0.8, 0.5]
  },
  "memory": {
    "total": 17179869184,
    "available": 8589934592,
    "used": 8589934592,
    "percent": 50.0
  },
  "disk": {
    "total": 549755813888,
    "used": 274877906944,
    "free": 274877906944,
    "percent": 50.0
  },
  "network": {
    "bytes_sent": 1073741824,
    "bytes_recv": 2147483648,
    "packets_sent": 1000000,
    "packets_recv": 2000000
  }
}
```

---

## 三、C 端 - 枚举查询

### 1. 获取所有可用枚举名称列表

**GET** `/api/v1/c/enum/list`

返回系统中注册的所有枚举类名称，前端可根据名称获取对应枚举详情。

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| enums | array | 枚举名称列表 |

#### 响应示例

```json
{
  "enums": [
    "RiskLevel",
    "StrategyStatus",
    "MarketType",
    "OrderType"
  ]
}
```

---

### 2. 按枚举名称获取枚举 KV 信息

**GET** `/api/v1/c/enum/{enum_name}`

根据枚举名称返回该枚举的所有选项，包含 value（值）、label（中文标签）、description（描述）。前端可用于渲染下拉框、筛选器等组件。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| enum_name | string | 是 | 枚举名称（如 RiskLevel、StrategyStatus 等） |

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 枚举名称 |
| items | array | 枚举选项列表 |
| items[].value | string | 枚举值 |
| items[].label | string | 中文标签 |
| items[].description | string | 描述信息 |

#### 响应示例

```json
{
  "name": "RiskLevel",
  "items": [
    {
      "value": "low",
      "label": "低风险",
      "description": "低风险等级"
    },
    {
      "value": "medium",
      "label": "中风险",
      "description": "中等风险等级"
    },
    {
      "value": "high",
      "label": "高风险",
      "description": "高风险等级"
    }
  ]
}
```

#### 错误响应

| HTTP 状态码 | 描述 |
|-------------|------|
| 404 | 枚举名称不存在 |

---

### 3. 批量获取多个枚举 KV 信息

**GET** `/api/v1/c/enum/batch/{enum_names}`

支持一次请求获取多个枚举信息，枚举名称用英文逗号分隔。不存在的枚举名称会被自动忽略。

#### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| enum_names | string | 是 | 逗号分隔的枚举名称（如 `RiskLevel,StrategyStatus,MarketType`） |

#### 响应字段

| 字段 | 类型 | 描述 |
|------|------|------|
| enums | object | 枚举字典，key 为枚举名称，value 为枚举选项列表 |

#### 响应示例

```json
{
  "enums": {
    "RiskLevel": [
      {
        "value": "low",
        "label": "低风险",
        "description": "低风险等级"
      }
    ],
    "StrategyStatus": [
      {
        "value": "running",
        "label": "运行中",
        "description": "策略正在运行"
      }
    ]
  }
}
```

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 200 | 请求成功 |
| 404 | 枚举名称不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务未就绪 |
