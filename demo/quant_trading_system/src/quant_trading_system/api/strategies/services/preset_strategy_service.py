"""
预设策略服务
"""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.api.strategies.repositories import PresetStrategyRepository


class PresetStrategyService:
    """系统预设策略服务"""

    @staticmethod
    async def create(db: AsyncSession, data: dict[str, Any], operator: str = "system") -> dict[str, Any]:
        """创建预设策略"""
        data["create_by"] = operator
        strategy = await PresetStrategyRepository.create(db, data)
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    async def get_detail(db: AsyncSession, strategy_id: int) -> Optional[dict[str, Any]]:
        """获取预设策略详情"""
        strategy = await PresetStrategyRepository.get_by_id(db, strategy_id)
        if not strategy:
            return None
        return PresetStrategyService._to_detail_dict(strategy)

    @staticmethod
    async def list_strategies(
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
    ) -> dict[str, Any]:
        """查询预设策略列表"""
        strategies, total = await PresetStrategyRepository.list_all(
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
    async def get_featured(db: AsyncSession, limit: int = 10) -> list[dict[str, Any]]:
        """获取推荐策略"""
        strategies = await PresetStrategyRepository.list_featured(db, limit)
        return [PresetStrategyService._to_dict(s) for s in strategies]

    @staticmethod
    async def update(db: AsyncSession, strategy_id: int, data: dict[str, Any], operator: str = "system") -> Optional[dict[str, Any]]:
        """更新预设策略"""
        data["update_by"] = operator
        strategy = await PresetStrategyRepository.update(db, strategy_id, data)
        if not strategy:
            return None
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    async def delete(db: AsyncSession, strategy_id: int) -> bool:
        """删除预设策略"""
        return await PresetStrategyRepository.delete(db, strategy_id)

    @staticmethod
    async def publish(db: AsyncSession, strategy_id: int, operator: str = "system") -> Optional[dict[str, Any]]:
        """上架策略"""
        strategy = await PresetStrategyRepository.update(db, strategy_id, {
            "is_published": True,
            "update_by": operator,
        })
        if not strategy:
            return None
        return PresetStrategyService._to_dict(strategy)

    @staticmethod
    async def unpublish(db: AsyncSession, strategy_id: int, operator: str = "system") -> Optional[dict[str, Any]]:
        """下架策略"""
        strategy = await PresetStrategyRepository.update(db, strategy_id, {
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
