"""
排行榜 Admin 端路由
==================

提供管理员刷新排行榜快照的功能。
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from quant_trading_system.models.database import LeaderboardSnapshot, SignalTradeRecord, Signal
from quant_trading_system.services.database.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id

router = APIRouter()

PERIODS = ["daily", "weekly", "monthly", "all_time"]
PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30, "all_time": 3650}


@router.post("/refresh")
async def refresh_leaderboard(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    手动刷新排行榜快照（管理员）

    重新计算并写入最新的排行榜快照数据。
    通常由定时任务自动触发，也可手动调用。

    返回：
    - success      : 操作是否成功
    - message      : 操作结果描述
    - snapshot_time: 快照时间
    """
    snapshot_time = datetime.utcnow()
    _compute_and_save_snapshots(db, snapshot_time)
    db.commit()

    return {
        "success": True,
        "message": "排行榜快照已刷新",
        "snapshot_time": snapshot_time.isoformat(),
    }


def _compute_and_save_snapshots(db: Session, snapshot_time: datetime) -> None:
    """
    计算并保存排行榜快照

    基于 signal_trade_record 表中的交易数据，按信号源聚合统计胜率、交易数量等指标，
    生成各周期的排行榜快照。
    """
    for period in PERIODS:
        days = PERIOD_DAYS[period]
        start_time = snapshot_time - timedelta(days=days)

        # 按信号源聚合交易统计
        rows = db.query(
            SignalTradeRecord.signal_id,
            Signal.name.label("signal_name"),
            func.count(SignalTradeRecord.id).label("total_trades"),
            func.sum(
                (SignalTradeRecord.pnl > 0).cast("integer")
            ).label("win_count"),
            func.sum(SignalTradeRecord.pnl).label("total_pnl"),
        ).join(
            Signal, Signal.id == SignalTradeRecord.signal_id
        ).filter(
            SignalTradeRecord.traded_at >= start_time,
            SignalTradeRecord.traded_at <= snapshot_time,
        ).group_by(
            SignalTradeRecord.signal_id,
            Signal.name,
        ).order_by(
            func.count(SignalTradeRecord.id).desc()
        ).limit(100).all()

        for rank, row in enumerate(rows, start=1):
            total = row.total_trades or 0
            win_count = 0
            try:
                win_count = int(row.win_count or 0)
            except Exception:
                pass
            win_rate = win_count / total if total > 0 else 0.0
            total_pnl = float(row.total_pnl or 0)

            snapshot = LeaderboardSnapshot(
                id=generate_snowflake_id(),
                rank_type="signal",
                period=period,
                rank_position=rank,
                entity_id=str(row.signal_id),
                entity_name=row.signal_name or str(row.signal_id),
                entity_type="strategy_signal",
                total_return=total_pnl,
                annual_return=None,
                max_drawdown=None,
                sharpe_ratio=None,
                win_rate=win_rate,
                total_trades=total,
                profit_factor=None,
                stat_start_time=start_time,
                stat_end_time=snapshot_time,
                snapshot_time=snapshot_time,
                created_at=snapshot_time,
            )
            db.add(snapshot)
