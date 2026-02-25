# 排行榜 API 文档

## 概述

排行榜模块提供策略和信号的排行榜查询功能（C端），以及管理员刷新排行榜快照的功能（M端）。

## 基础信息

- **C端基础URL**: `/api/v1/c/leaderboard`
- **M端基础URL**: `/api/v1/m/leaderboard`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

---

## 接口列表

### C端接口（普通用户）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/c/leaderboard` | 获取综合排行榜 |
| GET | `/api/v1/c/leaderboard/strategy` | 策略收益排行 |
| GET | `/api/v1/c/leaderboard/signal` | 信号准确率排行 |

### M端接口（管理员）

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/m/leaderboard/refresh` | 手动刷新排行榜快照 |

---

## C端接口详情

### 1. 获取综合排行榜

**GET** `/api/v1/c/leaderboard`

返回策略和信号的综合排行榜数据。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期: daily/weekly/monthly/all_time |
| limit | integer | 否 | `20` | 返回数量（1-100） |

#### 响应示例

```json
{
  "period": "weekly",
  "snapshot_time": "2025-02-24T19:00:00Z",
  "strategy_ranking": [...],
  "signal_ranking": [...]
}
```

---

### 2. 策略收益排行

**GET** `/api/v1/c/leaderboard/strategy`

按收益率、夏普比率或胜率对策略进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期 |
| sort_by | string | 否 | `"total_return"` | 排序字段: total_return/sharpe_ratio/win_rate |
| limit | integer | 否 | `20` | 返回数量 |

#### 响应示例

```json
{
  "items": [
    {
      "rank_position": 1,
      "entity_id": "strategy_001",
      "entity_name": "BTC均线策略",
      "total_return": 25.5,
      "sharpe_ratio": 2.1,
      "win_rate": 0.68,
      "max_drawdown": -5.2,
      "total_trades": 150
    }
  ],
  "total": 20,
  "period": "weekly",
  "sort_by": "total_return",
  "snapshot_time": "2025-02-24T19:00:00Z"
}
```

---

### 3. 信号准确率排行

**GET** `/api/v1/c/leaderboard/signal`

按信号准确率（胜率）对策略信号进行排名。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| period | string | 否 | `"weekly"` | 统计周期 |
| limit | integer | 否 | `20` | 返回数量 |

---

## M端接口详情

### 1. 手动刷新排行榜快照

**POST** `/api/v1/m/leaderboard/refresh`

重新计算并写入最新的排行榜快照数据。通常由定时任务自动触发，也可手动调用。

#### 响应示例

```json
{
  "success": true,
  "message": "排行榜快照已刷新",
  "snapshot_time": "2025-02-24T19:00:00Z"
}
```

---

## 排行榜数据字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| rank_position | integer | 排名位置 |
| entity_id | string | 实体ID |
| entity_name | string | 实体名称 |
| entity_type | string | 实体类型 |
| owner_id | string | 所有者ID |
| owner_name | string | 所有者名称 |
| total_return | float | 总收益率 |
| annual_return | float | 年化收益率 |
| max_drawdown | float | 最大回撤 |
| sharpe_ratio | float | 夏普比率 |
| win_rate | float | 胜率 |
| total_trades | integer | 总交易次数 |
| profit_factor | float | 盈亏比 |
| stat_start_time | string | 统计开始时间 |
| stat_end_time | string | 统计结束时间 |
| snapshot_time | string | 快照时间 |

---

## 错误码说明

| HTTP 状态码 | 描述 |
|-------------|------|
| 401 | 未认证 |
| 403 | 权限不足（M端接口需管理员权限） |
