"""
双均线策略
========

双均线交叉策略：当快线上穿慢线时买入，下穿时卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.strategy.base import Strategy, register_strategy
from quant_trading_system.strategy.strategy_signal import StrategySignal


@register_strategy
class DualMAStrategy(Strategy):
    """
    双均线策略

    当快线上穿慢线时买入，下穿时卖出
    """
    id: ClassVar[int] = 152410378779754498
    name: ClassVar[str] = "ma_cross"
    description: ClassVar[str] = "双均线交叉策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "fast_period": {"type": int, "default": 5, "min": 1},
        "slow_period": {"type": int, "default": 20, "min": 1},
    }

    symbols: ClassVar[tuple[str, ...]] = ("BTC/USDT",)
    timeframes: ClassVar[tuple[KlineInterval, ...]] = (KlineInterval.MIN_15,)

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_fast_ma: float | None = None
        self._prev_slow_ma: float | None = None

    def on_bar(self, bar: Bar) -> StrategySignal | list[StrategySignal] | None:
        # 通过指标引擎计算快慢EMA
        try:
            fast_result = self.calculate_indicator(
                "EMA",
                period=self.params["fast_period"],
            )
            slow_result = self.calculate_indicator(
                "EMA",
                period=self.params["slow_period"],
            )
        except (RuntimeError, ValueError):
            # 上下文未就绪或数据不足
            return None

        fast_ma_current = fast_result["ema"][-1]
        slow_ma_current = slow_result["ema"][-1]

        # 检查是否为NaN（数据不足时）
        if np.isnan(fast_ma_current) or np.isnan(slow_ma_current):
            return None

        signal = None

        # 检查均线交叉
        if self._prev_fast_ma is not None and self._prev_slow_ma is not None:
            # 金叉：快线上穿慢线
            if (self._prev_fast_ma <= self._prev_slow_ma and
                fast_ma_current > slow_ma_current):
                signal = self.buy(
                    bar.symbol,
                    reason=f"EMA golden cross: fast({fast_ma_current:.2f}) > slow({slow_ma_current:.2f})"
                )

            # 死叉：快线下穿慢线
            elif (self._prev_fast_ma >= self._prev_slow_ma and
                  fast_ma_current < slow_ma_current):
                signal = self.sell(
                    bar.symbol,
                    reason=f"EMA death cross: fast({fast_ma_current:.2f}) < slow({slow_ma_current:.2f})"
                )

        # 更新前值
        self._prev_fast_ma = fast_ma_current
        self._prev_slow_ma = slow_ma_current

        return signal
