"""
模拟交易服务
"""

from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.api.strategies.repositories import (
    SimulationTradeRepository,
    SimulationPositionRepository,
    SimulationLogRepository,
)
from quant_trading_system.api.strategies.repositories.preset_strategy_repository import PresetStrategyRepository
from quant_trading_system.models.strategy import UserStrategy

logger = structlog.get_logger(__name__)

# ---- 策略类型 → 指标配置映射 ----
# 定义每种预设策略类型所使用的指标及其前端展示配置
STRATEGY_INDICATOR_CONFIG: dict[str, list[dict[str, Any]]] = {
    "bollinger_band": [
        {
            "indicator": "BOLL",
            "param_keys": {"period": "period", "std_dev": "std_dev"},
            "outputs": [
                {"key": "middle", "label": "BOLL中轨", "type": "line", "pane": "main", "color": "#FFD700"},
                {"key": "upper", "label": "BOLL上轨", "type": "line", "pane": "main", "color": "#FF6347"},
                {"key": "lower", "label": "BOLL下轨", "type": "line", "pane": "main", "color": "#4169E1"},
            ],
        },
    ],
    "ma_cross": [
        {
            "indicator": "EMA",
            "param_keys": {"period": "fast_period"},
            "suffix": "fast",
            "outputs": [
                {"key": "ema", "label": "EMA快线", "type": "line", "pane": "main", "color": "#FF6600"},
            ],
        },
        {
            "indicator": "EMA",
            "param_keys": {"period": "slow_period"},
            "suffix": "slow",
            "outputs": [
                {"key": "ema", "label": "EMA慢线", "type": "line", "pane": "main", "color": "#0066FF"},
            ],
        },
    ],
    "macd_cross": [
        {
            "indicator": "MACD",
            "param_keys": {"fast_period": "fast_period", "slow_period": "slow_period", "signal_period": "signal_period"},
            "outputs": [
                {"key": "macd", "label": "MACD", "type": "line", "pane": "sub", "color": "#FF6600"},
                {"key": "signal", "label": "Signal", "type": "line", "pane": "sub", "color": "#0066FF"},
                {"key": "histogram", "label": "Histogram", "type": "histogram", "pane": "sub", "color": "#26a69a"},
            ],
        },
    ],
    "rsi_ob_os": [
        {
            "indicator": "RSI",
            "param_keys": {"period": "period"},
            "outputs": [
                {"key": "rsi", "label": "RSI", "type": "line", "pane": "sub", "color": "#9C27B0"},
            ],
        },
    ],
}


class SimulationService:
    """模拟交易服务"""

    @staticmethod
    async def get_indicators(
        db: AsyncSession,
        user_strategy_id: int,
        *,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """
        获取策略指标历史数据

        根据策略关联的预设策略类型，确定使用的指标，
        从数据库查询K线数据后用指标引擎计算。

        Args:
            db: 数据库会话
            user_strategy_id: 用户策略实例ID
            start_time: 开始时间戳(ms)
            end_time: 结束时间戳(ms)
            limit: K线条数

        Returns:
            包含指标数据的字典
        """
        # 1. 查询用户策略及其关联的预设策略
        result = await db.execute(
            select(UserStrategy).where(
                UserStrategy.id == user_strategy_id,
                UserStrategy.enable_flag == True,
            )
        )
        strategy = result.scalars().first()

        if not strategy:
            return {"strategy_id": str(user_strategy_id), "indicators": []}

        preset = await PresetStrategyRepository.get_by_id(db, strategy.preset_strategy_id)
        if not preset:
            return {"strategy_id": str(user_strategy_id), "indicators": []}

        # 2. 获取策略参数（用户自定义参数 → 预设默认参数 → 兜底）
        user_params = strategy.params or {}
        default_params = preset.default_params or {}
        merged_params = {**default_params, **user_params}

        # 3. 确定策略使用的指标配置
        # 优先使用策略代码名(preset.strategy_type对应的代码name)查找配置
        indicator_configs = SimulationService._resolve_indicator_config(preset, merged_params)

        if not indicator_configs:
            return {"strategy_id": str(user_strategy_id), "indicators": []}

        # 4. 获取K线数据
        symbol = (strategy.symbols or preset.symbols or ["BTCUSDT"])[0]
        # 统一为不带分隔符的格式
        symbol_key = symbol.replace("/", "").replace("-", "")
        timeframe = strategy.timeframe or preset.timeframe or "1h"

        try:
            bars = SimulationService._get_bars(symbol_key, timeframe, start_time, end_time, limit)
        except Exception as e:
            logger.error("获取K线数据失败", error=str(e), symbol=symbol_key, timeframe=timeframe)
            return {"strategy_id": str(user_strategy_id), "indicators": []}

        if bars is None or len(bars) == 0:
            return {"strategy_id": str(user_strategy_id), "indicators": []}

        # 5. 用指标引擎计算并格式化
        from quant_trading_system.indicators.indicator_engine import get_indicator_engine
        engine = get_indicator_engine()

        indicators_data: list[dict[str, Any]] = []

        for cfg in indicator_configs:
            indicator_name = cfg["indicator"]
            # 从合并后的策略参数中提取指标参数
            indicator_params = {}
            for ind_key, strat_key in cfg["param_keys"].items():
                if strat_key in merged_params:
                    indicator_params[ind_key] = merged_params[strat_key]

            try:
                result = engine.calculate(indicator_name, bars, **indicator_params)
            except Exception as e:
                logger.warning("指标计算失败", indicator=indicator_name, error=str(e))
                continue

            suffix = cfg.get("suffix", "")

            # 提取时间戳数组（转为秒级int）
            ts_array = bars.timestamp.astype("datetime64[s]").astype(np.int64)

            for output_cfg in cfg["outputs"]:
                key = output_cfg["key"]
                values = result.values.get(key)
                if values is None:
                    continue

                # 构造数据点（过滤NaN）
                data_points = []
                for i in range(len(values)):
                    if not np.isnan(values[i]):
                        data_points.append({
                            "time": int(ts_array[i]),
                            "value": round(float(values[i]), 8),
                        })

                name = f"{indicator_name}_{key}"
                if suffix:
                    name = f"{indicator_name}_{suffix}_{key}"

                indicators_data.append({
                    "name": name,
                    "label": output_cfg["label"],
                    "type": output_cfg["type"],
                    "pane": output_cfg["pane"],
                    "color": output_cfg["color"],
                    "data": data_points,
                })

        return {
            "strategy_id": str(user_strategy_id),
            "symbol": symbol_key,
            "timeframe": timeframe,
            "indicators": indicators_data,
        }

    @staticmethod
    def _resolve_indicator_config(
        preset,
        merged_params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        根据预设策略解析指标配置

        优先从 STRATEGY_INDICATOR_CONFIG 中按策略代码名匹配，
        如果匹配不到，则尝试根据 params_schema 中的参数名推断。
        """
        # 遍历注册的策略代码类，找到与 preset 匹配的
        from quant_trading_system.strategy import get_strategy_class, list_strategies

        for strategy_name in list_strategies():
            strategy_cls = get_strategy_class(strategy_name)
            if strategy_cls and hasattr(strategy_cls, "id") and strategy_cls.id == preset.id:
                if strategy_name in STRATEGY_INDICATOR_CONFIG:
                    return STRATEGY_INDICATOR_CONFIG[strategy_name]

        # 兜底：通过 strategy_type 做模糊匹配
        # 检查参数名推断指标
        configs: list[dict[str, Any]] = []
        param_keys = set(merged_params.keys())

        if {"fast_period", "slow_period", "signal_period"} <= param_keys:
            configs = STRATEGY_INDICATOR_CONFIG.get("macd_cross", [])
        elif {"period", "std_dev"} <= param_keys:
            configs = STRATEGY_INDICATOR_CONFIG.get("bollinger_band", [])
        elif {"fast_period", "slow_period"} <= param_keys:
            configs = STRATEGY_INDICATOR_CONFIG.get("ma_cross", [])
        elif "period" in param_keys and ("overbought" in param_keys or "oversold" in param_keys):
            configs = STRATEGY_INDICATOR_CONFIG.get("rsi_ob_os", [])

        return configs

    @staticmethod
    def _get_bars(
        symbol: str,
        timeframe: str,
        start_time: Optional[int],
        end_time: Optional[int],
        limit: int,
    ):
        """获取K线数据（BarArray）

        直接调用 MarketDataReader 的同步方法，
        避免在同步/异步上下文中混用 asyncio.run 导致的事件循环冲突。
        """
        from quant_trading_system.services.market.market_data_reader import get_market_data_reader

        query_service = get_market_data_reader()

        # 转换时间参数
        if end_time:
            end_dt = datetime.utcfromtimestamp(end_time / 1000)
        else:
            end_dt = datetime.utcnow()

        if start_time:
            start_dt = datetime.utcfromtimestamp(start_time / 1000)
        else:
            # 默认往前推足够的时间窗口
            start_dt = end_dt - timedelta(days=30)

        return query_service.get_kline_data_sync(symbol, timeframe, start_dt, end_dt, limit)

    @staticmethod
    async def get_trades(db: AsyncSession, user_strategy_id: int, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """获取模拟交易记录"""
        trades, total = await SimulationTradeRepository.list_by_strategy(
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
    async def get_positions(db: AsyncSession, user_strategy_id: int) -> dict[str, Any]:
        """获取模拟持仓"""
        positions = await SimulationPositionRepository.list_by_strategy(
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
    async def get_logs(
        db: AsyncSession,
        user_strategy_id: int,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """获取模拟运行日志"""
        logs = await SimulationLogRepository.list_by_strategy(
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
    async def get_trade_marks(
        db: AsyncSession,
        user_strategy_id: int,
        *,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """获取模拟交易点标记（用于K线图标注买卖点）"""
        trades, _ = await SimulationTradeRepository.list_by_strategy(
            db, user_strategy_id, page=1, page_size=limit,
        )
        marks = []
        for t in trades:
            if t.trade_time:
                timestamp = int(t.trade_time.timestamp())
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
