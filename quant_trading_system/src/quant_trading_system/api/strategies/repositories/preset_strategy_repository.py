"""
预设策略仓储
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.models.strategy import PresetStrategy
from quant_trading_system.core.snowflake import generate_snowflake_id


class PresetStrategyRepository:
    """系统预设策略仓储"""

    @staticmethod
    async def create(db: AsyncSession, data: dict[str, Any]) -> PresetStrategy:
        """创建预设策略"""
        strategy = PresetStrategy(**data)
        if not strategy.id:
            strategy.id = generate_snowflake_id()
        db.add(strategy)
        await db.commit()
        await db.refresh(strategy)
        return strategy

    @staticmethod
    async def get_by_id(db: AsyncSession, strategy_id: int) -> Optional[PresetStrategy]:
        """根据ID获取预设策略"""
        result = await db.execute(
            select(PresetStrategy).where(
                PresetStrategy.id == strategy_id,
                PresetStrategy.enable_flag == True,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def list_all(
        db: AsyncSession,
        *,
        keyword: Optional[str] = None,
        market_type: Optional[str] = None,
        strategy_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        is_published: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PresetStrategy], int]:
        """分页查询预设策略列表"""
        stmt = select(PresetStrategy).where(PresetStrategy.enable_flag == True)
        count_stmt = select(func.count()).select_from(PresetStrategy).where(PresetStrategy.enable_flag == True)

        if keyword:
            stmt = stmt.where(PresetStrategy.name.ilike(f"%{keyword}%"))
            count_stmt = count_stmt.where(PresetStrategy.name.ilike(f"%{keyword}%"))
        if market_type:
            stmt = stmt.where(PresetStrategy.market_type == market_type)
            count_stmt = count_stmt.where(PresetStrategy.market_type == market_type)
        if strategy_type:
            stmt = stmt.where(PresetStrategy.strategy_type == strategy_type)
            count_stmt = count_stmt.where(PresetStrategy.strategy_type == strategy_type)
        if risk_level:
            stmt = stmt.where(PresetStrategy.risk_level == risk_level)
            count_stmt = count_stmt.where(PresetStrategy.risk_level == risk_level)
        if status:
            stmt = stmt.where(PresetStrategy.status == status)
            count_stmt = count_stmt.where(PresetStrategy.status == status)
        if is_published is not None:
            stmt = stmt.where(PresetStrategy.is_published == is_published)
            count_stmt = count_stmt.where(PresetStrategy.is_published == is_published)

        total = (await db.execute(count_stmt)).scalar() or 0
        result = await db.execute(
            stmt.order_by(desc(PresetStrategy.sort_order), desc(PresetStrategy.create_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        strategies = result.scalars().all()
        return strategies, total

    @staticmethod
    async def list_featured(db: AsyncSession, limit: int = 10) -> list[PresetStrategy]:
        """获取推荐策略"""
        result = await db.execute(
            select(PresetStrategy)
            .where(
                PresetStrategy.enable_flag == True,
                PresetStrategy.is_published == True,
                PresetStrategy.is_featured == True,
            )
            .order_by(desc(PresetStrategy.sort_order), desc(PresetStrategy.create_time))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, strategy_id: int, data: dict[str, Any]) -> Optional[PresetStrategy]:
        """更新预设策略"""
        result = await db.execute(
            select(PresetStrategy).where(PresetStrategy.id == strategy_id)
        )
        strategy = result.scalars().first()
        if not strategy:
            return None
        for key, value in data.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
        strategy.update_time = datetime.utcnow()
        await db.commit()
        await db.refresh(strategy)
        return strategy

    @staticmethod
    async def delete(db: AsyncSession, strategy_id: int) -> bool:
        """逻辑删除预设策略"""
        result = await db.execute(
            select(PresetStrategy).where(PresetStrategy.id == strategy_id)
        )
        strategy = result.scalars().first()
        if not strategy:
            return False
        strategy.enable_flag = False
        strategy.update_time = datetime.utcnow()
        await db.commit()
        return True

    @staticmethod
    async def publish(db: AsyncSession, strategy_id: int) -> Optional[PresetStrategy]:
        """上架策略"""
        return await PresetStrategyRepository.update(db, strategy_id, {"is_published": True})

    @staticmethod
    async def unpublish(db: AsyncSession, strategy_id: int) -> Optional[PresetStrategy]:
        """下架策略"""
        return await PresetStrategyRepository.update(db, strategy_id, {"is_published": False})
