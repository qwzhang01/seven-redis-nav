"""
预设策略服务
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.api.strategies.repositories import PresetStrategyRepository


class PresetStrategyService:
    """系统预设策略服务"""

    @staticmethod
    def create(db: Session, data: dict[str, Any], operator: str = "system") -> dict[str, Any]:
        """创建预设策略"""
        data["create_by"] = operator
        strategy = PresetStrategyRepository.create(db, data)
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    def get_detail(db: Session, strategy_id: int) -> Optional[dict[str, Any]]:
        """获取预设策略详情"""
        strategy = PresetStrategyRepository.get_by_id(db, strategy_id)
        if not strategy:
            return None
        return PresetStrategyService._to_detail_dict(strategy)

    @staticmethod
    def list_strategies(
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
    ) -> dict[str, Any]:
        """查询预设策略列表"""
        strategies, total = PresetStrategyRepository.list_all(
            db,
            keyword=keyword,
            market_type=market_type,
            strategy_type=strategy_type,
            risk_level=risk_level,
            status=status,
            is_published=is_published,
            page=page,
            page_size=page_size,
        )
        return {
            "strategies": [PresetStrategyService._to_dict(s) for s in strategies],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def get_featured(db: Session, limit: int = 10) -> list[dict[str, Any]]:
        """获取推荐策略"""
        strategies = PresetStrategyRepository.list_featured(db, limit)
        return [PresetStrategyService._to_dict(s) for s in strategies]

    @staticmethod
    def update(db: Session, strategy_id: int, data: dict[str, Any], operator: str = "system") -> Optional[dict[str, Any]]:
        """更新预设策略"""
        data["update_by"] = operator
        strategy = PresetStrategyRepository.update(db, strategy_id, data)
        if not strategy:
            return None
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    def delete(db: Session, strategy_id: int) -> bool:
        """删除预设策略"""
        return PresetStrategyRepository.delete(db, strategy_id)

    @staticmethod
    def publish(db: Session, strategy_id: int, operator: str = "system") -> Optional[dict[str, Any]]:
        """上架策略"""
        strategy = PresetStrategyRepository.update(db, strategy_id, {
            "is_published": True,
            "update_by": operator,
        })
        if not strategy:
            return None
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    def unpublish(db: Session, strategy_id: int, operator: str = "system") -> Optional[dict[str, Any]]:
        """下架策略"""
        strategy = PresetStrategyRepository.update(db, strategy_id, {
            "is_published": False,
            "update_by": operator,
        })
        if not strategy:
            return None
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    def _to_dict(strategy) -> dict[str, Any]:
        """基本信息字典"""
        return {
            "id": str(strategy.id),
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type,
            "market_type": strategy.market_type,
            "risk_level": strategy.risk_level,
            "exchange": strategy.exchange,
            "symbols": strategy.symbols,
            "timeframe": strategy.timeframe,
            "total_return": float(strategy.total_return) if strategy.total_return else None,
            "max_drawdown": float(strategy.max_drawdown) if strategy.max_drawdown else None,
            "sharpe_ratio": float(strategy.sharpe_ratio) if strategy.sharpe_ratio else None,
            "win_rate": float(strategy.win_rate) if strategy.win_rate else None,
            "running_days": strategy.running_days,
            "status": strategy.status,
            "is_published": strategy.is_published,
            "is_featured": strategy.is_featured,
            "create_time": strategy.create_time.isoformat() + "Z" if strategy.create_time else None,
        }

    @staticmethod
    def _to_detail_dict(strategy) -> dict[str, Any]:
        """详情字典"""
        d = PresetStrategyService._to_dict(strategy)
        d.update({
            "detail": strategy.detail,
            "logic_description": strategy.logic_description,
            "params_schema": strategy.params_schema,
            "default_params": strategy.default_params,
            "risk_params": strategy.risk_params,
            "advanced_params": strategy.advanced_params,
            "risk_warning": strategy.risk_warning,
            "sort_order": strategy.sort_order,
        })
        return d
