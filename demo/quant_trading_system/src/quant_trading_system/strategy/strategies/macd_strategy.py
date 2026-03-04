"""
MACD策略
========

基于MACD金叉死叉的交易策略
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.strategy.base import Strategy, register_strategy
from quant_trading_system.strategy.strategy_signal import StrategySignal


@register_strategy
class MACDStrategy(Strategy):
    """
    MACD策略

    基于MACD金叉死叉的交易策略
    """

    id: ClassVar[int] = 152410378779754499
    name: ClassVar[str] = "macd_cross"
    description: ClassVar[str] = "MACD交叉策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "fast_period": {"type": int, "default": 12},
        "slow_period": {"type": int, "default": 26},
        "signal_period": {"type": int, "default": 9},
    }

    symbols: ClassVar[tuple[str, ...]] = ("BTC/USDT",)
    timeframes: ClassVar[tuple[KlineInterval, ...]] = (KlineInterval.HOUR_1,)

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_macd: float | None = None
        self._prev_signal: float | None = None

    def on_bar(self, bar: Bar) -> StrategySignal | list[StrategySignal] | None:
        # 通过指标引擎计算MACD
        try:
            macd_result = self.calculate_indicator(
                "MACD",
                fast_period=self.params["fast_period"],
                slow_period=self.params["slow_period"],
                signal_period=self.params["signal_period"],
            )
        except (RuntimeError, ValueError):
            # 上下文未就绪或数据不足
            return None

        macd_current = macd_result["macd"][-1]
        signal_current = macd_result["signal"][-1]

        # 检查是否为NaN（数据不足时）
        if np.isnan(macd_current) or np.isnan(signal_current):
            return None

        signal = None

        # 检查MACD交叉
        if self._prev_macd is not None and self._prev_signal is not None:
            # 金叉：MACD线上穿信号线
            if (self._prev_macd <= self._prev_signal and
                macd_current > signal_current):
                signal = self.buy(
                    bar.symbol,
                    reason=f"MACD golden cross: MACD({macd_current:.4f}) > Signal({signal_current:.4f})"
                )

            # 死叉：MACD线下穿信号线
            elif (self._prev_macd >= self._prev_signal and
                  macd_current < signal_current):
                signal = self.sell(
                    bar.symbol,
                    reason=f"MACD death cross: MACD({macd_current:.4f}) < Signal({signal_current:.4f})"
                )

        # 更新前值
        self._prev_macd = macd_current
        self._prev_signal = signal_current

        return signal
