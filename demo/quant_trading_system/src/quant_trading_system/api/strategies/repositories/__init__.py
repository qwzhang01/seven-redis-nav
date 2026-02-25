"""
策略模块数据访问层
=================

提供策略相关的数据库 CRUD 操作。
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import Session

from quant_trading_system.models.strategy import (
    PresetStrategy,
    UserStrategy,
    SimulationTrade,
    SimulationPosition,
    SimulationLog,
)
from quant_trading_system.core.snowflake import generate_snowflake_id


# ========== 预设策略 ==========

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


# ========== 用户策略实例 ==========

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


# ========== 模拟交易记录 ==========

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


# ========== 模拟持仓 ==========

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


# ========== 模拟日志 ==========

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
