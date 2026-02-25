"""
策略模块业务服务层
=================

封装策略相关的业务逻辑，协调仓储层和引擎层。
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.api.strategies.repositories import (
    PresetStrategyRepository,
    UserStrategyRepository,
    SimulationTradeRepository,
    SimulationPositionRepository,
    SimulationLogRepository,
)
from quant_trading_system.core.enums import (
    StrategyStatus,
    StrategyMode,
    MarketType,
    StrategyType,
    RiskLevel,
)


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


class UserStrategyService:
    """用户策略实例服务"""

    @staticmethod
    def create_live(db: Session, user_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """创建实盘策略"""
        data["user_id"] = user_id
        data["mode"] = StrategyMode.LIVE.value
        data["status"] = StrategyStatus.STOPPED.value
        data["create_by"] = str(user_id)
        strategy = UserStrategyRepository.create(db, data)
        return UserStrategyService._to_dict(strategy)

    @staticmethod
    def create_simulation(db: Session, user_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """创建模拟策略"""
        data["user_id"] = user_id
        data["mode"] = StrategyMode.SIMULATE.value
        data["status"] = StrategyStatus.STOPPED.value
        data["create_by"] = str(user_id)
        if "initial_capital" not in data:
            data["initial_capital"] = 10000
        data["current_value"] = data.get("initial_capital", 10000)
        strategy = UserStrategyRepository.create(db, data)
        return UserStrategyService._to_dict(strategy)

    @staticmethod
    def get_detail(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """获取用户策略详情"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        return UserStrategyService._to_detail_dict(strategy)

    @staticmethod
    def list_strategies(
        db: Session,
        user_id: int,
        *,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """查询用户策略列表"""
        strategies, total = UserStrategyRepository.list_by_user(
            db, user_id, mode=mode, status=status, page=page, page_size=page_size,
        )
        return {
            "strategies": [UserStrategyService._to_dict(s) for s in strategies],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def update(db: Session, strategy_id: int, user_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """更新用户策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        data["update_by"] = str(user_id)
        result = UserStrategyRepository.update(db, strategy_id, data)
        return UserStrategyService._to_dict(result) if result else None

    @staticmethod
    def delete(db: Session, strategy_id: int, user_id: int) -> bool:
        """删除用户策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return False
        return UserStrategyRepository.delete(db, strategy_id)

    @staticmethod
    def start(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """启动策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        result = UserStrategyRepository.update(db, strategy_id, {
            "status": StrategyStatus.RUNNING.value,
            "started_at": datetime.utcnow(),
        })
        return UserStrategyService._to_dict(result) if result else None

    @staticmethod
    def stop(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """停止策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        result = UserStrategyRepository.update(db, strategy_id, {
            "status": StrategyStatus.STOPPED.value,
            "stopped_at": datetime.utcnow(),
        })
        return UserStrategyService._to_dict(result) if result else None

    @staticmethod
    def pause(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """暂停策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        result = UserStrategyRepository.update(db, strategy_id, {
            "status": StrategyStatus.PAUSED.value,
        })
        return UserStrategyService._to_dict(result) if result else None

    @staticmethod
    def resume(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """恢复策略"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        result = UserStrategyRepository.update(db, strategy_id, {
            "status": StrategyStatus.RUNNING.value,
        })
        return UserStrategyService._to_dict(result) if result else None

    @staticmethod
    def get_performance(db: Session, strategy_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """获取策略表现"""
        strategy = UserStrategyRepository.get_by_id_and_user(db, strategy_id, user_id)
        if not strategy:
            return None
        return {
            "strategy_id": str(strategy.id),
            "performance": {
                "total_return": float(strategy.total_return) if strategy.total_return else 0,
                "today_return": float(strategy.today_return) if strategy.today_return else 0,
                "max_drawdown": float(strategy.max_drawdown) if strategy.max_drawdown else 0,
                "sharpe_ratio": float(strategy.sharpe_ratio) if strategy.sharpe_ratio else None,
                "calmar_ratio": float(strategy.calmar_ratio) if strategy.calmar_ratio else None,
                "sortino_ratio": float(strategy.sortino_ratio) if strategy.sortino_ratio else None,
                "win_rate": float(strategy.win_rate) if strategy.win_rate else 0,
                "total_trades": strategy.total_trades or 0,
                "signal_count": strategy.signal_count or 0,
                "var_value": float(strategy.var_value) if strategy.var_value else None,
                "volatility": float(strategy.volatility) if strategy.volatility else None,
                "current_value": float(strategy.current_value) if strategy.current_value else None,
                "initial_capital": float(strategy.initial_capital) if strategy.initial_capital else None,
            },
        }

    @staticmethod
    def _to_dict(strategy) -> dict[str, Any]:
        """基本信息字典"""
        return {
            "id": str(strategy.id),
            "user_id": str(strategy.user_id),
            "preset_strategy_id": str(strategy.preset_strategy_id),
            "name": strategy.name,
            "mode": strategy.mode,
            "exchange": strategy.exchange,
            "symbols": strategy.symbols,
            "timeframe": strategy.timeframe,
            "leverage": strategy.leverage,
            "initial_capital": float(strategy.initial_capital) if strategy.initial_capital else None,
            "status": strategy.status,
            "total_return": float(strategy.total_return) if strategy.total_return else 0,
            "today_return": float(strategy.today_return) if strategy.today_return else 0,
            "max_drawdown": float(strategy.max_drawdown) if strategy.max_drawdown else 0,
            "win_rate": float(strategy.win_rate) if strategy.win_rate else 0,
            "total_trades": strategy.total_trades or 0,
            "current_value": float(strategy.current_value) if strategy.current_value else None,
            "create_time": strategy.create_time.isoformat() + "Z" if strategy.create_time else None,
        }

    @staticmethod
    def _to_detail_dict(strategy) -> dict[str, Any]:
        """详情字典"""
        d = UserStrategyService._to_dict(strategy)
        d.update({
            "trade_mode": strategy.trade_mode,
            "take_profit": float(strategy.take_profit) if strategy.take_profit else None,
            "stop_loss": float(strategy.stop_loss) if strategy.stop_loss else None,
            "stop_mode": strategy.stop_mode,
            "max_positions": strategy.max_positions,
            "max_orders": strategy.max_orders,
            "max_consecutive_losses": strategy.max_consecutive_losses,
            "auto_cancel_orders": strategy.auto_cancel_orders,
            "auto_close_reverse": strategy.auto_close_reverse,
            "reverse_open": strategy.reverse_open,
            "running_days": strategy.running_days,
            "running_time_start": strategy.running_time_start,
            "running_time_end": strategy.running_time_end,
            "filters": strategy.filters,
            "params": strategy.params,
            "sharpe_ratio": float(strategy.sharpe_ratio) if strategy.sharpe_ratio else None,
            "calmar_ratio": float(strategy.calmar_ratio) if strategy.calmar_ratio else None,
            "sortino_ratio": float(strategy.sortino_ratio) if strategy.sortino_ratio else None,
            "signal_count": strategy.signal_count or 0,
            "started_at": strategy.started_at.isoformat() + "Z" if strategy.started_at else None,
            "stopped_at": strategy.stopped_at.isoformat() + "Z" if strategy.stopped_at else None,
        })
        return d


class SimulationService:
    """模拟交易服务"""

    @staticmethod
    def get_trades(db: Session, user_strategy_id: int, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """获取模拟交易记录"""
        trades, total = SimulationTradeRepository.list_by_strategy(
            db, user_strategy_id, page=page, page_size=page_size,
        )
        return {
            "strategy_id": str(user_strategy_id),
            "total": total,
            "page": page,
            "page_size": page_size,
            "trades": [
                {
                    "id": str(t.id),
                    "symbol": t.symbol,
                    "side": t.side,
                    "price": float(t.price),
                    "amount": float(t.amount),
                    "value": float(t.value) if t.value else None,
                    "fee": float(t.fee) if t.fee else 0,
                    "pnl": float(t.pnl) if t.pnl else None,
                    "time": t.trade_time.isoformat() + "Z" if t.trade_time else None,
                }
                for t in trades
            ],
        }

    @staticmethod
    def get_positions(db: Session, user_strategy_id: int) -> dict[str, Any]:
        """获取模拟持仓"""
        positions = SimulationPositionRepository.list_by_strategy(
            db, user_strategy_id, status="open",
        )
        total_value = sum(
            float(p.current_price or 0) * float(p.amount or 0) for p in positions
        )
        unrealized_pnl = sum(float(p.pnl or 0) for p in positions)
        return {
            "strategy_id": str(user_strategy_id),
            "positions": [
                {
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "amount": float(p.amount),
                    "entry_price": float(p.entry_price),
                    "current_price": float(p.current_price) if p.current_price else None,
                    "pnl": float(p.pnl) if p.pnl else 0,
                    "pnl_ratio": float(p.pnl_ratio) if p.pnl_ratio else 0,
                    "open_time": p.open_time.isoformat() + "Z" if p.open_time else None,
                }
                for p in positions
            ],
            "total_value": round(total_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
        }

    @staticmethod
    def get_logs(
        db: Session,
        user_strategy_id: int,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """获取模拟运行日志"""
        logs = SimulationLogRepository.list_by_strategy(
            db, user_strategy_id, level=level, limit=limit,
        )
        return {
            "strategy_id": str(user_strategy_id),
            "logs": [
                {
                    "time": log.log_time.isoformat() + "Z" if log.log_time else None,
                    "level": log.level,
                    "message": log.message,
                }
                for log in logs
            ],
        }

    @staticmethod
    def get_trade_marks(
        db: Session,
        user_strategy_id: int,
        *,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """获取模拟交易点标记（用于K线图标注买卖点）"""
        # 查询该策略的交易记录
        trades, _ = SimulationTradeRepository.list_by_strategy(
            db, user_strategy_id, page=1, page_size=limit,
        )
        marks = []
        for t in trades:
            if t.trade_time:
                timestamp = int(t.trade_time.timestamp())
                # 根据时间范围过滤
                if start_time and timestamp < start_time // 1000:
                    continue
                if end_time and timestamp > end_time // 1000:
                    continue

                is_buy = t.side in ("buy", "long")
                marks.append({
                    "time": timestamp,
                    "position": "belowBar" if is_buy else "aboveBar",
                    "color": "#26a69a" if is_buy else "#ef5350",
                    "shape": "arrowUp" if is_buy else "arrowDown",
                    "text": f"{'买入' if is_buy else '卖出'} {float(t.price):.2f}" + (
                        f" {'+' if float(t.pnl) > 0 else ''}{float(t.pnl):.2f}" if t.pnl else ""
                    ),
                    "side": t.side,
                    "price": float(t.price),
                    "quantity": float(t.amount),
                    "pnl": float(t.pnl) if t.pnl else None,
                })
        return {
            "strategy_id": str(user_strategy_id),
            "marks": marks,
        }
