"""
用户策略实例仓储
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.models.strategy import UserStrategy
from quant_trading_system.core.snowflake import generate_snowflake_id


class UserStrategyRepository:
    """用户策略实例仓储"""

    @staticmethod
    async def create(db: AsyncSession, data: dict[str, Any]) -> UserStrategy:
        """创建用户策略实例"""
        strategy = UserStrategy(**data)
        if not strategy.id:
            strategy.id = generate_snowflake_id()
        db.add(strategy)
        await db.commit()
        await db.refresh(strategy)
        return strategy

    @staticmethod
    async def get_by_id(db: AsyncSession, strategy_id: int) -> Optional[UserStrategy]:
        """根据ID获取用户策略"""
        result = await db.execute(
            select(UserStrategy).where(
                UserStrategy.id == strategy_id,
                UserStrategy.enable_flag == True,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_by_id_and_user(db: AsyncSession, strategy_id: int, user_id: int) -> Optional[UserStrategy]:
        """根据ID和用户ID获取用户策略（权限校验）"""
        result = await db.execute(
            select(UserStrategy).where(
                UserStrategy.id == strategy_id,
                UserStrategy.user_id == user_id,
                UserStrategy.enable_flag == True,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: int,
        *,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserStrategy], int]:
        """分页查询用户策略列表"""
        stmt = select(UserStrategy).where(
            UserStrategy.user_id == user_id,
            UserStrategy.enable_flag == True,
        )
        count_stmt = select(func.count()).select_from(UserStrategy).where(
            UserStrategy.user_id == user_id,
            UserStrategy.enable_flag == True,
        )

        if mode:
            stmt = stmt.where(UserStrategy.mode == mode)
            count_stmt = count_stmt.where(UserStrategy.mode == mode)
        if status:
            stmt = stmt.where(UserStrategy.status == status)
            count_stmt = count_stmt.where(UserStrategy.status == status)

        total = (await db.execute(count_stmt)).scalar() or 0
        result = await db.execute(
            stmt.order_by(desc(UserStrategy.create_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        strategies = result.scalars().all()
        return strategies, total

    @staticmethod
    async def update(db: AsyncSession, strategy_id: int, data: dict[str, Any]) -> Optional[UserStrategy]:
        """更新用户策略"""
        result = await db.execute(
            select(UserStrategy).where(UserStrategy.id == strategy_id)
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
        """逻辑删除用户策略"""
        result = await db.execute(
            select(UserStrategy).where(UserStrategy.id == strategy_id)
        )
        strategy = result.scalars().first()
        if not strategy:
            return False
        strategy.enable_flag = False
        strategy.update_time = datetime.utcnow()
        await db.commit()
        return True
