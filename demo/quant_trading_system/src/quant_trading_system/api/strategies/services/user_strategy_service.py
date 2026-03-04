"""
用户策略实例服务
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.api.strategies.repositories import UserStrategyRepository
from quant_trading_system.core.enums import StrategyStatus, StrategyMode


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
