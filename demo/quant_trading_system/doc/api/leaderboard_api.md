# 排行榜 API 文档

## 概述

排行榜模块提供策略和信号的排行榜查询功能，支持按不同统计周期查看策略收益排名和信号准确率排名。管理员端提供手动刷新排行榜快照的功能。

## 基础信息

- **C端基础URL**: `/api/v1/c/leaderboard`
- **Admin端基础URL**: `/api/v1/m/leaderboard`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

> **认证说明**：所有排行榜接口均需要在请求头中携带有效的 JWT 令牌：
> ```http
> Authorization: Bearer <token>
> ```

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/leaderboard` | 获取综合排行榜 |
| GET | `/api/v1/c/leaderboard/strategy` | 策略收益排行榜 |
| GET | `/api/v1/c/leaderboard/signal` | 信号准确率排行榜 |

### Admin端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/leaderboard/refresh` | 手动刷新排行榜快照 |

---

## C端接口详情

### 1. 获取综合排行榜

**GET** `/api/v1/c/leaderboard`

返回策略和信号的综合排行榜数据，同时包含策略收益排名和信号准确率排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：daily/weekly/monthly/all_time |
| limit | integer | 否 | `20` | 返回数量（1-100） |

**period 枚举值：**

| 值 | 描述 |
|----|------|
| `daily` | 日榜（最近1天） |
| `weekly` | 周榜（最近7天） |
| `monthly` | 月榜（最近30天） |
| `all_time` | 总榜（全部时间） |

#### 请求示例

```
GET /api/v1/c/leaderboard?period=weekly&limit=10
```

#### 响应示例

```json
{
  "period": "weekly",
  "snapshot_time": "2026-02-21T00:00:00",
  "strategy_ranking": [
    {
      "id": "snapshot_uuid",
      "rank_type": "strategy",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_uuid",
      "entity_name": "BTC均线策略",
      "entity_type": "strategy",
      "owner_id": "user_uuid",
      "owner_name": "trader01",
      "total_return": 0.235,
      "annual_return": 1.22,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.85,
      "win_rate": 0.62,
      "total_trades": 128,
      "profit_factor": 2.1,
      "stat_start_time": "2026-02-14T00:00:00",
      "stat_end_time": "2026-02-21T00:00:00",
      "snapshot_time": "2026-02-21T00:00:00"
    }
  ],
  "signal_ranking": [
    {
      "id": "snapshot_uuid2",
      "rank_type": "signal",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_uuid2",
      "entity_name": "ETH动量策略",
      "entity_type": "strategy_signal",
      "owner_id": null,
      "owner_name": null,
      "total_return": null,
      "annual_return": null,
      "max_drawdown": null,
      "sharpe_ratio": 0.85,
      "win_rate": 0.78,
      "total_trades": 50,
      "profit_factor": null,
      "stat_start_time": "2026-02-14T00:00:00",
      "stat_end_time": "2026-02-21T00:00:00",
      "snapshot_time": "2026-02-21T00:00:00"
    }
  ]
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| period | string | 统计周期 |
| snapshot_time | string\|null | 快照生成时间 |
| strategy_ranking | array[object] | 策略排行榜列表 |
| signal_ranking | array[object] | 信号排行榜列表 |

**排行榜条目字段说明：**

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 快照记录ID |
| rank_type | string | 排名类型（strategy/signal） |
| period | string | 统计周期 |
| rank_position | integer | 排名位置 |
| entity_id | string | 实体ID（策略ID） |
| entity_name | string | 实体名称（策略名称） |
| entity_type | string | 实体类型 |
| owner_id | string\|null | 所有者用户ID |
| owner_name | string\|null | 所有者用户名 |
| total_return | float\|null | 总收益率 |
| annual_return | float\|null | 年化收益率 |
| max_drawdown | float\|null | 最大回撤 |
| sharpe_ratio | float\|null | 夏普比率（信号排行中表示平均置信度） |
| win_rate | float\|null | 胜率（信号排行中表示执行率） |
| total_trades | integer\|null | 总交易/信号数量 |
| profit_factor | float\|null | 盈利因子 |
| stat_start_time | string\|null | 统计开始时间 |
| stat_end_time | string\|null | 统计结束时间 |
| snapshot_time | string\|null | 快照时间 |

---

### 2. 策略收益排行榜

**GET** `/api/v1/c/leaderboard/strategy`

按收益率、夏普比率或胜率对策略进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：daily/weekly/monthly/all_time |
| sort_by | string | 否 | `"total_return"` | 排序字段：total_return/sharpe_ratio/win_rate/annual_return |
| limit | integer | 否 | `20` | 返回数量（1-100） |

**sort_by 枚举值：**

| 值 | 描述 |
|----|------|
| `total_return` | 按总收益率排序 |
| `sharpe_ratio` | 按夏普比率排序 |
| `win_rate` | 按胜率排序 |
| `annual_return` | 按年化收益率排序 |

#### 请求示例

```
GET /api/v1/c/leaderboard/strategy?period=monthly&sort_by=sharpe_ratio&limit=10
```

#### 响应示例

```json
{
  "items": [
    {
      "id": "snapshot_uuid",
      "rank_type": "strategy",
      "period": "monthly",
      "rank_position": 1,
      "entity_id": "strategy_uuid",
      "entity_name": "BTC均线策略",
      "entity_type": "strategy",
      "owner_id": "user_uuid",
      "owner_name": "trader01",
      "total_return": 0.235,
      "annual_return": 1.22,
      "max_drawdown": 0.08,
      "sharpe_ratio": 1.85,
      "win_rate": 0.62,
      "total_trades": 128,
      "profit_factor": 2.1,
      "stat_start_time": "2026-01-21T00:00:00",
      "stat_end_time": "2026-02-21T00:00:00",
      "snapshot_time": "2026-02-21T00:00:00"
    }
  ],
  "total": 1,
  "period": "monthly",
  "sort_by": "sharpe_ratio",
  "snapshot_time": "2026-02-21T00:00:00"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array[object] | 排行榜列表（字段同综合排行榜条目） |
| total | integer | 返回数量 |
| period | string | 统计周期 |
| sort_by | string | 排序字段 |
| snapshot_time | string\|null | 快照时间 |

---

### 3. 信号准确率排行榜

**GET** `/api/v1/c/leaderboard/signal`

按信号执行率（胜率）对策略信号进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期：daily/weekly/monthly/all_time |
| limit | integer | 否 | `20` | 返回数量（1-100） |

#### 请求示例

```
GET /api/v1/c/leaderboard/signal?period=weekly&limit=20
```

#### 响应示例

```json
{
  "items": [
    {
      "id": "snapshot_uuid",
      "rank_type": "signal",
      "period": "weekly",
      "rank_position": 1,
      "entity_id": "strategy_uuid",
      "entity_name": "ETH动量策略",
      "entity_type": "strategy_signal",
      "owner_id": null,
      "owner_name": null,
      "total_return": null,
      "annual_return": null,
      "max_drawdown": null,
      "sharpe_ratio": 0.85,
      "win_rate": 0.78,
      "total_trades": 50,
      "profit_factor": null,
      "stat_start_time": "2026-02-14T00:00:00",
      "stat_end_time": "2026-02-21T00:00:00",
      "snapshot_time": "2026-02-21T00:00:00"
    }
  ],
  "total": 1,
  "period": "weekly",
  "snapshot_time": "2026-02-21T00:00:00"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| items | array[object] | 排行榜列表 |
| total | integer | 返回数量 |
| period | string | 统计周期 |
| snapshot_time | string\|null | 快照时间 |

> **说明**：信号排行榜中，`win_rate` 表示信号执行率（已执行信号数/总信号数），`sharpe_ratio` 字段存储的是平均置信度，`total_trades` 表示总信号数量。

---

## Admin端接口详情

### 1. 手动刷新排行榜快照

**POST** `/api/v1/m/leaderboard/refresh`

重新计算并写入最新的排行榜快照数据。通常由定时任务自动触发，也可手动调用。

> **说明**：刷新操作会基于 `signal_records` 表中的信号数据，按策略统计各周期（daily/weekly/monthly/all_time）的信号执行率等指标，生成新的排行榜快照。

#### 响应示例

```json
{
  "success": true,
  "message": "排行榜快照已刷新",
  "snapshot_time": "2026-02-21T02:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 操作是否成功 |
| message | string | 操作结果描述 |
| snapshot_time | string | 本次快照生成时间（ISO 8601格式） |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未提供认证凭据或令牌无效/已过期 |
| 429 | 请求过于频繁（每 IP 每 60 秒最多 200 次） |

## 统计周期说明

| 周期 | 描述 | 统计天数 |
|------|------|----------|
| daily | 日榜 | 最近 1 天 |
| weekly | 周榜 | 最近 7 天 |
| monthly | 月榜 | 最近 30 天 |
| all_time | 总榜 | 最近 3650 天（约10年） |

## 排行榜数据说明

排行榜数据基于**快照机制**，即定期（或手动触发）计算并保存排行榜数据，查询时直接读取最新快照，不实时计算。

- **策略排行**：基于策略的历史交易数据计算收益率、夏普比率、胜率等指标
- **信号排行**：基于 `signal_records` 表中的信号记录，统计各策略的信号执行率和平均置信度

> **注意**：若尚未生成快照（如系统刚启动），排行榜接口将返回空列表。可调用 `POST /api/v1/m/leaderboard/refresh` 手动生成初始快照。
