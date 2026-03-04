"""
模拟交易相关仓储
"""

from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from quant_trading_system.models.strategy import (
    SimulationTrade,
    SimulationPosition,
    SimulationLog,
)
from quant_trading_system.core.snowflake import generate_snowflake_id


class SimulationTradeRepository:
    """模拟交易记录仓储"""

    @staticmethod
    def create(db: Session, data: dict[str, Any]) -> SimulationTrade:
        """创建模拟交易记录"""
        trade = SimulationTrade(**data)
        if not trade.id:
            trade.id = generate_snowflake_id()
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    def list_by_strategy(
        db: Session,
        user_strategy_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SimulationTrade], int]:
        """分页查询模拟交易记录"""
        query = db.query(SimulationTrade).filter(
            SimulationTrade.user_strategy_id == user_strategy_id,
        )
        total = query.count()
        trades = (
            query.order_by(desc(SimulationTrade.trade_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return trades, total


class SimulationPositionRepository:
    """模拟持仓仓储"""

    @staticmethod
    def list_by_strategy(
        db: Session,
        user_strategy_id: int,
        *,
        status: Optional[str] = None,
    ) -> list[SimulationPosition]:
        """查询模拟持仓"""
        query = db.query(SimulationPosition).filter(
            SimulationPosition.user_strategy_id == user_strategy_id,
        )
        if status:
            query = query.filter(SimulationPosition.status == status)
        return query.order_by(desc(SimulationPosition.open_time)).all()


class SimulationLogRepository:
    """模拟运行日志仓储"""

    @staticmethod
    def create(db: Session, data: dict[str, Any]) -> SimulationLog:
        """创建模拟日志"""
        log = SimulationLog(**data)
        if not log.id:
            log.id = generate_snowflake_id()
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_by_strategy(
        db: Session,
        user_strategy_id: int,
        *,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> list[SimulationLog]:
        """查询模拟日志"""
        query = db.query(SimulationLog).filter(
            SimulationLog.user_strategy_id == user_strategy_id,
        )
        if level:
            query = query.filter(SimulationLog.level == level)
        return query.order_by(desc(SimulationLog.log_time)).limit(limit).all()
