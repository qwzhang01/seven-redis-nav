# API需求总结

## 📊 快速概览

**分析日期**: 2026-02-19  
**前端页面**: 实时数据订阅管理 (`/admin/data-subscription`)  
**现有API文档**: `doc/market_api.md`

---

## ✅ 结论

### 现有API是否够用？

**❌ 不够用**

现有的 `market_api.md` 接口主要提供**行情数据查询**功能，但**缺少订阅配置管理**的核心接口。

### 满足度评估

| 维度 | 完成度 | 说明 |
|------|--------|------|
| 前端功能 | 100% ✅ | 所有UI和交互已完整实现 |
| 后端API | 10% ❌ | 仅有基础行情查询接口 |
| 整体可用性 | 0% ❌ | 缺少核心管理接口，无法使用 |

---

## 🔴 必须补充的接口（13个）

### 1. 订阅配置管理（5个接口）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/subscriptions` | 创建订阅配置 |
| GET | `/admin/subscriptions` | 获取订阅列表（支持筛选） |
| GET | `/admin/subscriptions/{id}` | 获取订阅详情 |
| PUT | `/admin/subscriptions/{id}` | 更新订阅配置 |
| DELETE | `/admin/subscriptions/{id}` | 删除订阅 |

### 2. 订阅状态控制（3个接口）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/subscriptions/{id}/start` | 启动订阅 |
| POST | `/admin/subscriptions/{id}/pause` | 暂停订阅 |
| POST | `/admin/subscriptions/{id}/stop` | 停止订阅 |

### 3. 手动同步管理（4个接口）

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/sync-tasks` | 创建同步任务 |
| GET | `/admin/sync-tasks` | 获取同步任务列表 |
| GET | `/admin/sync-tasks/{id}` | 获取同步任务详情 |
| POST | `/admin/sync-tasks/{id}/cancel` | 取消同步任务 |

### 4. 统计信息（1个接口）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/admin/subscriptions/statistics` | 获取订阅统计信息 |

---

## 📋 核心数据结构

### 订阅配置（Subscription）

```json
{
  "id": "sub_123456",
  "name": "Binance BTC/USDT K线",
  "exchange": "binance",
  "market_type": "spot",
  "data_type": "kline",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "interval": "1h",
  "status": "running",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-02-19T05:30:00Z",
  "last_sync_time": "2024-02-19T05:30:00Z",
  "total_records": 1250000,
  "error_count": 3,
  "config": {
    "auto_restart": true,
    "max_retries": 3,
    "batch_size": 1000,
    "sync_interval": 60
  }
}
```

### 同步任务（SyncTask）

```json
{
  "id": "task_789012",
  "subscription_id": "sub_123456",
  "subscription_name": "Binance BTC/USDT K线",
  "exchange": "binance",
  "symbols": ["BTCUSDT"],
  "data_type": "kline",
  "start_time": "2024-02-01T00:00:00Z",
  "end_time": "2024-02-19T00:00:00Z",
  "status": "running",
  "progress": 65,
  "total_records": 10000,
  "synced_records": 6500,
  "error_message": null,
  "created_at": "2024-02-19T04:00:00Z",
  "completed_at": null
}
```

---

## 🎯 开发优先级

### 第一阶段（核心功能）- 5-7天

**必须实现，否则页面无法使用**

1. 订阅CRUD（创建、查询、更新、删除）
2. 订阅状态控制（启动、暂停、停止）
3. 手动同步（创建任务、查询任务列表）

### 第二阶段（增强功能）- 3-4天

**提升用户体验**

1. 详情查询接口
2. 任务取消功能
3. 统计信息接口

### 第三阶段（优化功能）- 3-5天

**可选，但建议实现**

1. WebSocket实时推送
2. 批量操作接口
3. 错误日志详情

---

## 💾 数据库设计

### 订阅表（subscriptions）

```sql
CREATE TABLE subscriptions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) DEFAULT 'spot',
    data_type VARCHAR(20) NOT NULL,
    symbols JSON NOT NULL,
    interval VARCHAR(10),
    status VARCHAR(20) DEFAULT 'stopped',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_sync_time TIMESTAMP NULL,
    total_records BIGINT DEFAULT 0,
    error_count INT DEFAULT 0,
    last_error TEXT,
    config JSON,
    INDEX idx_exchange (exchange),
    INDEX idx_status (status),
    INDEX idx_data_type (data_type)
);
```

### 同步任务表（sync_tasks）

```sql
CREATE TABLE sync_tasks (
    id VARCHAR(50) PRIMARY KEY,
    subscription_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress INT DEFAULT 0,
    total_records BIGINT DEFAULT 0,
    synced_records BIGINT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_status (status)
);
```

---

## 📚 相关文档

- **[API_GAP_ANALYSIS.md](./API_GAP_ANALYSIS.md)** - 详细的API差距分析文档（包含完整接口定义）
- **[market_api.md](./market_api.md)** - 现有的行情API文档
- **[DATA_SUBSCRIPTION_FEATURE.md](../DATA_SUBSCRIPTION_FEATURE.md)** - 前端功能文档

---

## 🚀 快速开始

### 后端开发者

1. 阅读 [API_GAP_ANALYSIS.md](./API_GAP_ANALYSIS.md) 了解详细接口定义
2. 按照优先级实现第一阶段的8个核心接口
3. 创建数据库表结构
4. 实现订阅状态管理和任务调度逻辑

### 前端开发者

1. 前端功能已完整实现，无需修改
2. 等待后端API完成后，替换模拟数据为真实API调用
3. 在 `src/api/subscription.ts` 中实现API调用方法

---

## ⚠️ 重要提醒

1. **现有API不能直接使用**
   - `/market/subscribe` 和 `/market/unsubscribe` 是临时订阅，不支持持久化
   - 需要全新的 `/admin/subscriptions` 系列接口

2. **状态管理很重要**
   - 订阅状态：stopped → running → paused → stopped
   - 任务状态：pending → running → completed/failed

3. **数据一致性**
   - 订阅删除时需要级联删除相关的同步任务
   - 订阅状态变更需要记录日志

4. **性能考虑**
   - 同步任务应该异步执行
   - 使用消息队列处理大量数据同步
   - 实现任务进度的实时更新机制

---

**预估总工时**: 11-16天（包含测试和文档）  
**建议开始时间**: 立即  
**预期完成时间**: 2-3周

---

**文档版本**: v1.0  
**创建日期**: 2026-02-19
