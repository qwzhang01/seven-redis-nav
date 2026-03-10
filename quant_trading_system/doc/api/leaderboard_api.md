# 排行榜 API 文档

## 概述

排行榜模块提供策略和信号的排行榜查询功能，支持按不同统计周期和排序字段查看排名。管理员可手动刷新排行榜快照。

## 基础信息

- **C 端基础URL**: `/api/v1/c/leaderboard`
- **Admin 端基础URL**: `/api/v1/m/leaderboard`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### C 端（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/leaderboard` | 获取综合排行榜 |
| GET | `/api/v1/c/leaderboard/strategy` | 策略收益排行榜 |
| GET | `/api/v1/c/leaderboard/signal` | 信号准确率排行榜 |

### Admin 端（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/leaderboard/refresh` | 手动刷新排行榜快照 |

---

## C 端接口详情

### 1. 获取综合排行榜

**GET** `/api/v1/c/leaderboard`

返回策略和信号的综合排行榜数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：`daily` / `weekly` / `monthly` / `all_time` |
| limit | integer | 否 | `20` | 返回数量（1-100） |

#### 响应示例

```json
{
  "period": "weekly",
  "snapshot_time": "2025-02-01T12:00:00",
  "strategy_ranking": [
    {
      "id": 1,
      "rank_type": "strategy",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_001",
      "entity_name": "MA Cross",
      "entity_type": "strategy",
      "owner_id": "12345",
      "owner_name": "trader1",
      "total_return": 15.5,
      "annual_return": 120.0,
      "max_drawdown": -5.2,
      "sharpe_ratio": 1.8,
      "win_rate": 0.65,
      "total_trades": 42,
      "profit_factor": 2.1,
      "stat_start_time": "2025-01-25T00:00:00",
      "stat_end_time": "2025-02-01T00:00:00",
      "snapshot_time": "2025-02-01T12:00:00"
    }
  ],
  "signal_ranking": [
    {
      "id": 2,
      "rank_type": "signal",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_002",
      "entity_name": "RSI Signal",
      "entity_type": "strategy_signal",
      "owner_id": null,
      "owner_name": null,
      "total_return": null,
      "annual_return": null,
      "max_drawdown": null,
      "sharpe_ratio": 0.85,
      "win_rate": 0.72,
      "total_trades": 100,
      "profit_factor": null,
      "stat_start_time": "2025-01-25T00:00:00",
      "stat_end_time": "2025-02-01T00:00:00",
      "snapshot_time": "2025-02-01T12:00:00"
    }
  ]
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| period | string | 统计周期 |
| snapshot_time | string | 快照时间（ISO格式） |
| strategy_ranking | array | 策略排行榜列表 |
| signal_ranking | array | 信号排行榜列表 |

#### 排行榜条目字段

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer | 快照记录ID |
| rank_type | string | 排名类型：`strategy` / `signal` |
| period | string | 统计周期 |
| rank_position | integer | 排名位置 |
| entity_id | string | 实体ID（策略ID） |
| entity_name | string | 实体名称（策略名称） |
| entity_type | string | 实体类型 |
| owner_id | string | 所有者用户ID |
| owner_name | string | 所有者用户名 |
| total_return | float | 总收益率（可为null） |
| annual_return | float | 年化收益率（可为null） |
| max_drawdown | float | 最大回撤（可为null） |
| sharpe_ratio | float | 夏普比率（信号类型中为平均置信度） |
| win_rate | float | 胜率 |
| total_trades | integer | 总交易/信号数 |
| profit_factor | float | 盈亏比（可为null） |
| stat_start_time | string | 统计开始时间 |
| stat_end_time | string | 统计结束时间 |
| snapshot_time | string | 快照时间 |

---

### 2. 策略收益排行榜

**GET** `/api/v1/c/leaderboard/strategy`

按收益率、夏普比率或胜率对策略进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：`daily` / `weekly` / `monthly` / `all_time` |
| sort_by | string | 否 | `"total_return"` | 排序字段：`total_return` / `sharpe_ratio` / `win_rate` / `annual_return` |
| limit | integer | 否 | `20` | 返回数量（1-100） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 1,
      "rank_type": "strategy",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_001",
      "entity_name": "MA Cross",
      "entity_type": "strategy",
      "owner_id": "12345",
      "owner_name": "trader1",
      "total_return": 15.5,
      "annual_return": 120.0,
      "max_drawdown": -5.2,
      "sharpe_ratio": 1.8,
      "win_rate": 0.65,
      "total_trades": 42,
      "profit_factor": 2.1,
      "stat_start_time": "2025-01-25T00:00:00",
      "stat_end_time": "2025-02-01T00:00:00",
      "snapshot_time": "2025-02-01T12:00:00"
    }
  ],
  "total": 1,
  "period": "weekly",
  "sort_by": "total_return",
  "snapshot_time": "2025-02-01T12:00:00"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array | 排行榜条目列表（字段同上） |
| total | integer | 返回条目数量 |
| period | string | 统计周期 |
| sort_by | string | 排序字段 |
| snapshot_time | string | 快照时间 |

---

### 3. 信号准确率排行榜

**GET** `/api/v1/c/leaderboard/signal`

按信号准确率（胜率）对策略信号进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：`daily` / `weekly` / `monthly` / `all_time` |
| limit | integer | 否 | `20` | 返回数量（1-100） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 2,
      "rank_type": "signal",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_002",
      "entity_name": "RSI Signal",
      "entity_type": "strategy_signal",
      "owner_id": null,
      "owner_name": null,
      "total_return": null,
      "annual_return": null,
      "max_drawdown": null,
      "sharpe_ratio": 0.85,
      "win_rate": 0.72,
      "total_trades": 100,
      "profit_factor": null,
      "stat_start_time": "2025-01-25T00:00:00",
      "stat_end_time": "2025-02-01T00:00:00",
      "snapshot_time": "2025-02-01T12:00:00"
    }
  ],
  "total": 1,
  "period": "weekly",
  "snapshot_time": "2025-02-01T12:00:00"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array | 排行榜条目列表（字段同上） |
| total | integer | 返回条目数量 |
| period | string | 统计周期 |
| snapshot_time | string | 快照时间 |

---

## Admin 端接口详情

### 4. 手动刷新排行榜快照

**POST** `/api/v1/m/leaderboard/refresh`

重新计算并写入最新的排行榜快照数据。通常由定时任务自动触发，也可由管理员手动调用。

刷新逻辑：基于 `signal_trade_record` 表中的交易数据，按信号聚合统计胜率、交易数量等指标，生成 `daily` / `weekly` / `monthly` / `all_time` 四个周期的排行榜快照。

#### 请求体

无需请求体。

#### 响应示例

```json
{
  "success": true,
  "message": "排行榜快照已刷新",
  "snapshot_time": "2025-02-01T12:00:00.000000"
}
```

#### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| message | string | 操作结果描述 |
| snapshot_time | string | 快照时间（ISO格式） |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证或Token无效 |
| 403 | 无权限（Admin接口需管理员权限） |
| 500 | 服务器内部错误 |
