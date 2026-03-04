"""
RSI超买超卖策略
==============

RSI低于超卖线买入，高于超买线卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.strategy.base import Strategy, register_strategy
from quant_trading_system.strategy.strategy_signal import StrategySignal


@register_strategy
class RSIStrategy(Strategy):
    """
    RSI超买超卖策略

    RSI低于超卖线买入，高于超买线卖出
    """
    id: ClassVar[int] = 152410378779754500
    name: ClassVar[str] = "rsi_ob_os"
    description: ClassVar[str] = "RSI超买超卖策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14},
        "overbought": {"type": float, "default": 70.0},
        "oversold": {"type": float, "default": 30.0},
    }

    symbols: ClassVar[tuple[str, ...]] = ("BTC/USDT",)
    timeframes: ClassVar[tuple[KlineInterval, ...]] = (KlineInterval.HOUR_4,)

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_rsi: float | None = None

    def on_bar(self, bar: Bar) -> StrategySignal | list[StrategySignal] | None:
        # 通过指标引擎计算RSI
        try:
            rsi_result = self.calculate_indicator(
                "RSI",
                period=self.params["period"],
            )
        except (RuntimeError, ValueError):
            # 上下文未就绪或数据不足
            return None

        rsi_current = rsi_result["rsi"][-1]

        # 检查是否为NaN（数据不足时）
        if np.isnan(rsi_current):
            return None

        signal = None

        # 超卖买入信号
        if rsi_current < self.params["oversold"]:
            # 检查是否从超卖区域回升
            if self._prev_rsi is not None and self._prev_rsi <= rsi_current:
                signal = self.buy(
                    bar.symbol,
                    reason=f"RSI oversold and rising: {rsi_current:.2f}"
                )

        # 超买卖出信号
        elif rsi_current > self.params["overbought"]:
            # 检查是否从超买区域回落
            if self._prev_rsi is not None and self._prev_rsi >= rsi_current:
                signal = self.sell(
                    bar.symbol,
                    reason=f"RSI overbought and falling: {rsi_current:.2f}"
                )

        # 更新前值
        self._prev_rsi = rsi_current

        return signal
