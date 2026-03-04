"""
预设策略仓储
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from quant_trading_system.models.strategy import PresetStrategy
from quant_trading_system.core.snowflake import generate_snowflake_id


class PresetStrategyRepository:
    """系统预设策略仓储"""

    @staticmethod
    def create(db: Session, data: dict[str, Any]) -> PresetStrategy:
        """创建预设策略"""
        strategy = PresetStrategy(**data)
        if not strategy.id:
            strategy.id = generate_snowflake_id()
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy

    @staticmethod
    def get_by_id(db: Session, strategy_id: int) -> Optional[PresetStrategy]:
        """根据ID获取预设策略"""
        return db.query(PresetStrategy).filter(
            PresetStrategy.id == strategy_id,
            PresetStrategy.enable_flag == True,
        ).first()

    @staticmethod
    def list_all(
        db: Session,
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
        query = db.query(PresetStrategy).filter(PresetStrategy.enable_flag == True)

        if keyword:
            query = query.filter(PresetStrategy.name.ilike(f"%{keyword}%"))
        if market_type:
            query = query.filter(PresetStrategy.market_type == market_type)
        if strategy_type:
            query = query.filter(PresetStrategy.strategy_type == strategy_type)
        if risk_level:
            query = query.filter(PresetStrategy.risk_level == risk_level)
        if status:
            query = query.filter(PresetStrategy.status == status)
        if is_published is not None:
            query = query.filter(PresetStrategy.is_published == is_published)

        total = query.count()
        strategies = (
            query.order_by(desc(PresetStrategy.sort_order), desc(PresetStrategy.create_time))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return strategies, total

    @staticmethod
    def list_featured(db: Session, limit: int = 10) -> list[PresetStrategy]:
        """获取推荐策略"""
        return (
            db.query(PresetStrategy)
            .filter(
                PresetStrategy.enable_flag == True,
                PresetStrategy.is_published == True,
                PresetStrategy.is_featured == True,
            )
            .order_by(desc(PresetStrategy.sort_order), desc(PresetStrategy.create_time))
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(db: Session, strategy_id: int, data: dict[str, Any]) -> Optional[PresetStrategy]:
        """更新预设策略"""
        strategy = db.query(PresetStrategy).filter(PresetStrategy.id == strategy_id).first()
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
        """逻辑删除预设策略"""
        strategy = db.query(PresetStrategy).filter(PresetStrategy.id == strategy_id).first()
        if not strategy:
            return False
        strategy.enable_flag = False
        strategy.update_time = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def publish(db: Session, strategy_id: int) -> Optional[PresetStrategy]:
        """上架策略"""
        return PresetStrategyRepository.update(db, strategy_id, {"is_published": True})

    @staticmethod
    def unpublish(db: Session, strategy_id: int) -> Optional[PresetStrategy]:
        """下架策略"""
        return PresetStrategyRepository.update(db, strategy_id, {"is_published": False})
