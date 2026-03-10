"""
模拟交易相关仓储
"""

from typing import Any, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.models.strategy import (
    SimulationTrade,
    SimulationPosition,
    SimulationLog,
)
from quant_trading_system.core.snowflake import generate_snowflake_id


class SimulationTradeRepository:
    """模拟交易记录仓储"""

    @staticmethod
    async def create(db: AsyncSession, data: dict[str, Any]) -> SimulationTrade:
        """创建模拟交易记录"""
        trade = SimulationTrade(**data)
        if not trade.id:
            trade.id = generate_snowflake_id()
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        return trade

    @staticmethod
    async def list_by_strategy(
        db: AsyncSession,
        user_strategy_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SimulationTrade], int]:
        """分页查询模拟交易记录"""
        stmt = select(SimulationTrade).where(
            SimulationTrade.user_strategy_id == user_strategy_id,
        )
        count_stmt = select(func.count()).select_from(SimulationTrade).where(
            SimulationTrade.user_strategy_id == user_strategy_id,
        )
        total = (await db.execute(count_stmt)).scalar() or 0
        result = await db.execute(
            stmt.order_by(desc(SimulationTrade.trade_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        trades = result.scalars().all()
        return trades, total


class SimulationPositionRepository:
    """模拟持仓仓储"""

    @staticmethod
    async def list_by_strategy(
        db: AsyncSession,
        user_strategy_id: int,
        *,
        status: Optional[str] = None,
    ) -> list[SimulationPosition]:
        """查询模拟持仓"""
        stmt = select(SimulationPosition).where(
            SimulationPosition.user_strategy_id == user_strategy_id,
        )
        if status:
            stmt = stmt.where(SimulationPosition.status == status)
        result = await db.execute(stmt.order_by(desc(SimulationPosition.open_time)))
        return result.scalars().all()


class SimulationLogRepository:
    """模拟运行日志仓储"""

    @staticmethod
    async def create(db: AsyncSession, data: dict[str, Any]) -> SimulationLog:
        """创建模拟日志"""
        log = SimulationLog(**data)
        if not log.id:
            log.id = generate_snowflake_id()
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def list_by_strategy(
        db: AsyncSession,
        user_strategy_id: int,
        *,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> list[SimulationLog]:
        """查询模拟日志"""
        stmt = select(SimulationLog).where(
            SimulationLog.user_strategy_id == user_strategy_id,
        )
        if level:
            stmt = stmt.where(SimulationLog.level == level)
        result = await db.execute(stmt.order_by(desc(SimulationLog.log_time)).limit(limit))
        return result.scalars().all()
