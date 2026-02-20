# 系统管理 API 文档

## 概述

系统管理模块提供系统信息查询、配置查询、健康检查、性能指标监控等功能，同时包含用于 Kubernetes 探针的就绪检查和存活检查接口。

## 基础信息

- **系统管理基础URL**: `/api/v1/m/system`
- **健康检查基础URL**: `/api/v1/m/health`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有系统管理接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### 系统管理接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/system/info` | 获取系统基本信息 |
| GET | `/api/v1/m/system/config` | 获取系统配置信息 |
| GET | `/api/v1/m/system/health` | 系统组件健康检查 |
| GET | `/api/v1/m/system/metrics` | 获取系统性能指标 |

### 健康检查接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/m/health/` | 基础健康检查 |
| GET | `/api/v1/m/health/db` | 数据库健康检查 |
| GET | `/api/v1/m/health/full` | 完整健康检查 |
| GET | `/api/v1/m/health/ready` | 就绪检查（Kubernetes探针） |
| GET | `/api/v1/m/health/live` | 存活检查（Kubernetes探针） |
| GET | `/api/v1/m/health/metrics` | 系统资源指标 |

---

## 系统管理接口详情

### 1. 获取系统基本信息

**GET** `/api/v1/m/system/info`

查询量化交易系统的版本、环境、运行状态等基本信息。

#### 响应示例

```json
{
  "name": "量化交易系统",
  "version": "1.0.0",
  "env": "development",
  "debug": true,
  "trading_mode": "paper",
  "trading_running": true
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 系统名称 |
| version | string | 系统版本号 |
| env | string | 运行环境（development/production） |
| debug | boolean | 调试模式状态 |
| trading_mode | string\|null | 交易模式（paper/live/backtest），系统未启动时为 null |
| trading_running | boolean | 交易系统是否正在运行 |

---

### 2. 获取系统配置信息

**GET** `/api/v1/m/system/config`

查询系统的公开配置参数，不包含敏感信息（如API密钥等）。

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

| 字段 | 类型 | 描述 |
|------|------|------|
| trading | object | 交易相关配置 |
| trading.order_timeout | integer | 订单超时时间（秒） |
| trading.default_slippage | float | 默认滑点率 |
| trading.default_commission_rate | float | 默认手续费率 |
| strategy | object | 策略相关配置 |
| strategy.max_concurrent_strategies | integer | 最大并发策略数 |
| strategy.backtest_start_capital | float | 回测初始资金 |

---

### 3. 系统组件健康检查

**GET** `/api/v1/m/system/health`

检查系统各核心组件的运行状态，评估系统整体健康度。

#### 响应示例（系统正常）

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

#### 响应示例（系统降级）

```json
{
  "status": "degraded",
  "checks": {
    "api": true,
    "event_engine": false,
    "market_service": false,
    "strategy_engine": false,
    "trading_engine": false
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 系统整体状态：`healthy`（正常）或 `degraded`（降级） |
| checks | object | 各组件健康状态 |
| checks.api | boolean | API服务状态 |
| checks.event_engine | boolean | 事件引擎状态 |
| checks.market_service | boolean | 市场服务状态 |
| checks.strategy_engine | boolean | 策略引擎状态 |
| checks.trading_engine | boolean | 交易引擎状态 |

---

### 4. 获取系统性能指标

**GET** `/api/v1/m/system/metrics`

查询系统各核心组件的性能统计数据和运行指标。

#### 响应示例

```json
{
  "event_engine": {
    "total_events": 10000,
    "events_per_second": 50
  },
  "market_service": {
    "total_ticks": 100000,
    "connected_collectors": 2
  },
  "strategy_engine": {
    "active_strategies": 3,
    "total_signals": 500
  },
  "trading_engine": {
    "total_orders": 200,
    "filled_orders": 180
  },
  "risk_manager": {
    "max_drawdown": 0.05,
    "current_exposure": 5000.0
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| event_engine | object | 事件引擎统计信息 |
| market_service | object | 市场服务统计信息 |
| strategy_engine | object | 策略引擎统计信息 |
| trading_engine | object | 交易引擎统计信息 |
| risk_manager | object | 风险管理器统计信息 |

> **注意**：当系统未启动时，所有统计信息字段返回空对象 `{}`。

---

## 健康检查接口详情

### 1. 基础健康检查

**GET** `/api/v1/m/health/`

检查 API 服务是否正常运行，适用于负载均衡器的健康探针。

#### 响应示例

```json
{
  "status": "healthy",
  "message": "服务运行正常",
  "timestamp": "2026-02-19T10:00:00",
  "version": "1.0.0",
  "checks": {
    "api": {
      "status": "healthy",
      "message": "API服务正常"
    }
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 健康状态：`healthy` 或 `unhealthy` |
| message | string | 状态描述 |
| timestamp | string | 检查时间 |
| version | string | 服务版本号 |
| checks | object | 各项检查结果 |

---

### 2. 数据库健康检查

**GET** `/api/v1/m/health/db`

检查数据库连接是否正常。

#### 响应示例（正常）

```json
{
  "status": "healthy",
  "message": "数据库连接正常",
  "timestamp": "2026-02-19T10:00:00",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "数据库连接正常"
    }
  }
}
```

#### 响应示例（异常）

```json
{
  "status": "unhealthy",
  "message": "数据库连接失败: Connection refused",
  "timestamp": "2026-02-19T10:00:00",
  "version": "1.0.0",
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

检查所有关键组件的健康状态，包括数据库、关键数据表、系统资源等。

#### 响应示例

```json
{
  "status": "healthy",
  "message": "系统运行正常",
  "timestamp": "2026-02-19T10:00:00",
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
      "message": "磁盘使用率: 60.0%",
      "details": {
        "total": "500GB",
        "used": "300GB",
        "percent": 60.0
      }
    },
    "process": {
      "status": "healthy",
      "message": "进程运行正常",
      "details": {
        "pid": 12345,
        "memory_mb": 256,
        "cpu_percent": 2.5
      }
    }
  }
}
```

**检查项说明：**

| 检查项 | 描述 | 告警阈值 |
|--------|------|----------|
| api | API服务状态 | - |
| database | 数据库连接状态 | 连接失败时 unhealthy |
| user_table | 用户数据表状态 | 查询失败时 unhealthy |
| exchange_table | 交易所数据表状态 | 查询失败时 unhealthy |
| api_key_table | API密钥数据表状态 | 查询失败时 unhealthy |
| memory | 内存使用情况 | 使用率 ≥ 90% 时 warning |
| cpu | CPU使用情况 | 使用率 ≥ 80% 时 warning |
| disk | 磁盘使用情况 | 使用率 ≥ 90% 时 warning |
| process | 当前进程状态 | - |

---

### 4. 就绪检查

**GET** `/api/v1/m/health/ready`

用于 Kubernetes 就绪探针（Readiness Probe），检查服务是否准备好接收流量。

#### 响应示例（就绪）

```json
{
  "status": "ready",
  "timestamp": "2026-02-19T10:00:00.000000"
}
```

HTTP 状态码：`200 OK`

#### 响应示例（未就绪）

```json
{
  "status": "not ready",
  "timestamp": "2026-02-19T10:00:00.000000"
}
```

HTTP 状态码：`503 Service Unavailable`

---

### 5. 存活检查

**GET** `/api/v1/m/health/live`

用于 Kubernetes 存活探针（Liveness Probe），检查服务进程是否存活。

#### 响应示例（存活）

```json
{
  "status": "alive",
  "timestamp": "2026-02-19T10:00:00.000000"
}
```

HTTP 状态码：`200 OK`

#### 响应示例（异常）

```json
{
  "status": "dead",
  "timestamp": "2026-02-19T10:00:00.000000"
}
```

HTTP 状态码：`503 Service Unavailable`

---

### 6. 系统资源指标

**GET** `/api/v1/m/health/metrics`

返回系统运行指标，可用于监控系统（如 Prometheus、Grafana）。

#### 响应示例

```json
{
  "timestamp": "2026-02-19T10:00:00.000000",
  "system": {
    "platform": "macOS-14.0-arm64",
    "python_version": "3.11.0",
    "hostname": "server-01",
    "uptime": 1708300800.0
  },
  "cpu": {
    "cores": 8,
    "usage_percent": 12.5,
    "load_average": [1.2, 1.5, 1.8]
  },
  "memory": {
    "total": 17179869184,
    "available": 9663676416,
    "used": 7516192768,
    "percent": 43.7
  },
  "disk": {
    "total": 536870912000,
    "used": 322122547200,
    "free": 214748364800,
    "percent": 60.0
  },
  "network": {
    "bytes_sent": 1073741824,
    "bytes_recv": 2147483648,
    "packets_sent": 1000000,
    "packets_recv": 2000000
  }
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| timestamp | string | 采集时间 |
| system | object | 系统基本信息 |
| system.platform | string | 操作系统平台 |
| system.python_version | string | Python版本 |
| system.hostname | string | 主机名 |
| system.uptime | float | 系统启动时间（Unix时间戳） |
| cpu | object | CPU信息 |
| cpu.cores | integer | CPU核心数 |
| cpu.usage_percent | float | CPU使用率（%） |
| cpu.load_average | array[float]\|null | 系统负载（1/5/15分钟），Windows下为 null |
| memory | object | 内存信息（字节） |
| memory.total | integer | 总内存 |
| memory.available | integer | 可用内存 |
| memory.used | integer | 已用内存 |
| memory.percent | float | 内存使用率（%） |
| disk | object | 磁盘信息（字节） |
| disk.total | integer | 总磁盘空间 |
| disk.used | integer | 已用磁盘空间 |
| disk.free | integer | 可用磁盘空间 |
| disk.percent | float | 磁盘使用率（%） |
| network | object | 网络IO统计 |
| network.bytes_sent | integer | 发送字节数 |
| network.bytes_recv | integer | 接收字节数 |
| network.packets_sent | integer | 发送数据包数 |
| network.packets_recv | integer | 接收数据包数 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |
| 503 | 服务不可用（就绪/存活检查失败） |

## 健康状态说明

| 状态值 | 描述 |
|--------|------|
| healthy | 组件运行正常 |
| unhealthy | 组件运行异常，需要关注 |
| warning | 组件运行正常但存在潜在风险（如资源使用率较高） |
| degraded | 系统整体降级，部分组件异常 |
