"""
排行榜路由模块
=============

提供策略和信号的排行榜查询功能。

C 端接口（普通用户）：
- GET /              : 获取综合排行榜
- GET /strategy      : 策略收益排行
- GET /signal        : 信号准确率排行

M 端接口（管理员）：
- POST /refresh      : 手动刷新排行榜快照
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from quant_trading_system.models.leaderboard import LeaderboardSnapshot
from quant_trading_system.services.database.database import get_db

router = APIRouter()


def _snapshot_to_dict(s: LeaderboardSnapshot) -> dict:
    """将 LeaderboardSnapshot ORM 对象转换为字典"""
    return {
        "id": s.id,
        "rank_type": s.rank_type,
        "period": s.period,
        "rank_position": s.rank_position,
        "entity_id": s.entity_id,
        "entity_name": s.entity_name,
        "entity_type": s.entity_type,
        "owner_id": str(s.owner_id) if s.owner_id else None,
        "owner_name": s.owner_name,
        "total_return": float(s.total_return) if s.total_return is not None else None,
        "annual_return": float(s.annual_return) if s.annual_return is not None else None,
        "max_drawdown": float(s.max_drawdown) if s.max_drawdown is not None else None,
        "sharpe_ratio": float(s.sharpe_ratio) if s.sharpe_ratio is not None else None,
        "win_rate": float(s.win_rate) if s.win_rate is not None else None,
        "total_trades": s.total_trades,
        "profit_factor": float(s.profit_factor) if s.profit_factor is not None else None,
        "stat_start_time": s.stat_start_time.isoformat() if s.stat_start_time else None,
        "stat_end_time": s.stat_end_time.isoformat() if s.stat_end_time else None,
        "snapshot_time": s.snapshot_time.isoformat() if s.snapshot_time else None,
    }


def _get_latest_snapshot_time(db: Session, rank_type: str, period: str) -> Optional[datetime]:
    """获取最新快照时间"""
    result = db.query(func.max(LeaderboardSnapshot.snapshot_time)).filter(
        LeaderboardSnapshot.rank_type == rank_type,
        LeaderboardSnapshot.period == period,
    ).scalar()
    return result


# ─────────────────────────────────────────────
# C 端接口
# ─────────────────────────────────────────────

@router.get("")
async def get_leaderboard(
    period: str = Query("weekly", description="统计周期: daily/weekly/monthly/all_time"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取综合排行榜

    返回策略和信号的综合排行榜数据。

    参数：
    - period: 统计周期（daily/weekly/monthly/all_time）
    - limit : 返回数量（最多100）

    返回：
    - strategy_ranking: 策略排行
    - signal_ranking  : 信号排行
    - period          : 统计周期
    - snapshot_time   : 快照时间
    """
    strategy_items = _query_leaderboard(db, "strategy", period, limit)
    signal_items = _query_leaderboard(db, "signal", period, limit)

    snapshot_time = _get_latest_snapshot_time(db, "strategy", period)

    return {
        "period": period,
        "snapshot_time": snapshot_time.isoformat() if snapshot_time else None,
        "strategy_ranking": strategy_items,
        "signal_ranking": signal_items,
    }


@router.get("/strategy")
async def get_strategy_leaderboard(
    period: str = Query("weekly", description="统计周期: daily/weekly/monthly/all_time"),
    sort_by: str = Query("total_return", description="排序字段: total_return/sharpe_ratio/win_rate"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    策略收益排行榜

    按收益率、夏普比率或胜率对策略进行排名。

    参数：
    - period : 统计周期（daily/weekly/monthly/all_time）
    - sort_by: 排序字段（total_return/sharpe_ratio/win_rate）
    - limit  : 返回数量

    返回：
    - items       : 排行榜列表
    - total       : 总数量
    - period      : 统计周期
    - sort_by     : 排序字段
    - snapshot_time: 快照时间
    """
    items = _query_leaderboard(db, "strategy", period, limit, sort_by=sort_by)
    snapshot_time = _get_latest_snapshot_time(db, "strategy", period)

    return {
        "items": items,
        "total": len(items),
        "period": period,
        "sort_by": sort_by,
        "snapshot_time": snapshot_time.isoformat() if snapshot_time else None,
    }


@router.get("/signal")
async def get_signal_leaderboard(
    period: str = Query("weekly", description="统计周期: daily/weekly/monthly/all_time"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    信号准确率排行榜

    按信号准确率（胜率）对策略信号进行排名。

    参数：
    - period: 统计周期
    - limit : 返回数量

    返回：
    - items       : 排行榜列表
    - total       : 总数量
    - period      : 统计周期
    - snapshot_time: 快照时间
    """
    items = _query_leaderboard(db, "signal", period, limit, sort_by="win_rate")
    snapshot_time = _get_latest_snapshot_time(db, "signal", period)

    return {
        "items": items,
        "total": len(items),
        "period": period,
        "snapshot_time": snapshot_time.isoformat() if snapshot_time else None,
    }


def _query_leaderboard(
    db: Session,
    rank_type: str,
    period: str,
    limit: int,
    sort_by: str = "total_return",
) -> list[dict]:
    """查询排行榜快照数据"""
    snapshot_time = _get_latest_snapshot_time(db, rank_type, period)
    if not snapshot_time:
        return []

    # 允许的排序字段白名单
    sort_field_map = {
        "total_return": LeaderboardSnapshot.total_return,
        "sharpe_ratio": LeaderboardSnapshot.sharpe_ratio,
        "win_rate": LeaderboardSnapshot.win_rate,
        "annual_return": LeaderboardSnapshot.annual_return,
    }
    order_col = sort_field_map.get(sort_by, LeaderboardSnapshot.total_return)

    items = db.query(LeaderboardSnapshot).filter(
        LeaderboardSnapshot.rank_type == rank_type,
        LeaderboardSnapshot.period == period,
        LeaderboardSnapshot.snapshot_time == snapshot_time,
    ).order_by(desc(order_col)).limit(limit).all()

    return [_snapshot_to_dict(s) for s in items]
