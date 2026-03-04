"""
用户策略实例仓储
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from quant_trading_system.models.strategy import UserStrategy
from quant_trading_system.core.snowflake import generate_snowflake_id


class UserStrategyRepository:
    """用户策略实例仓储"""

    @staticmethod
    def create(db: Session, data: dict[str, Any]) -> UserStrategy:
        """创建用户策略实例"""
        strategy = UserStrategy(**data)
        if not strategy.id:
            strategy.id = generate_snowflake_id()
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def get_by_id(db: Session, strategy_id: int) -> Optional[UserStrategy]:
        """根据ID获取用户策略"""
        return db.query(UserStrategy).filter(
            UserStrategy.id == strategy_id,
            UserStrategy.enable_flag == True,
        ).first()

    @staticmethod
    def get_by_id_and_user(db: Session, strategy_id: int, user_id: int) -> Optional[UserStrategy]:
        """根据ID和用户ID获取用户策略（权限校验）"""
        return db.query(UserStrategy).filter(
            UserStrategy.id == strategy_id,
            UserStrategy.user_id == user_id,
            UserStrategy.enable_flag == True,
        ).first()

    @staticmethod
    def list_by_user(
        db: Session,
        user_id: int,
        *,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserStrategy], int]:
        """分页查询用户策略列表"""
        query = db.query(UserStrategy).filter(
            UserStrategy.user_id == user_id,
            UserStrategy.enable_flag == True,
        )

        if mode:
            query = query.filter(UserStrategy.mode == mode)
        if status:
            query = query.filter(UserStrategy.status == status)

        total = query.count()
        strategies = (
            query.order_by(desc(UserStrategy.create_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return strategies, total

    @staticmethod
    def update(db: Session, strategy_id: int, data: dict[str, Any]) -> Optional[UserStrategy]:
        """更新用户策略"""
        strategy = db.query(UserStrategy).filter(UserStrategy.id == strategy_id).first()
        if not strategy:
            return None
        for key, value in data.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
        strategy.update_time = datetime.utcnow()
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def delete(db: Session, strategy_id: int) -> bool:
        """逻辑删除用户策略"""
        strategy = db.query(UserStrategy).filter(UserStrategy.id == strategy_id).first()
        if not strategy:
            return False
        strategy.enable_flag = False
        strategy.update_time = datetime.utcnow()
        db.commit()
        return True
