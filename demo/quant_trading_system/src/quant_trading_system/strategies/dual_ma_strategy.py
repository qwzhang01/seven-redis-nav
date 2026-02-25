"""
双均线策略
========

双均线交叉策略：当快线上穿慢线时买入，下穿时卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar, TimeFrame
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.technical import EMA


@register_strategy
class DualMAStrategy(Strategy):
    """
    双均线策略

    当快线上穿慢线时买入，下穿时卖出
    """
    id:int = 152410378779754498
    name: ClassVar[str] = "ma_cross"
    description: ClassVar[str] = "双均线交叉策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "fast_period": {"type": int, "default": 5, "min": 1},
        "slow_period": {"type": int, "default": 20, "min": 1},
    }

    symbols: ClassVar[list[str]] = ["BTC/USDT"]
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.M15]

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_fast_ma: float | None = None
        self._prev_slow_ma: float | None = None
        self._close_prices: list[float] = []

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        # 收集收盘价数据
        self._close_prices.append(bar.close)

        # 确保有足够的数据计算双均线
        if len(self._close_prices) < self.params["slow_period"]:
            return None

        # 计算快慢均线
        close_array = np.array(self._close_prices)

        # 计算快线EMA
        fast_ema = EMA._calculate_ema(close_array, self.params["fast_period"])
        fast_ma_current = fast_ema[-1]

        # 计算慢线EMA
        slow_ema = EMA._calculate_ema(close_array, self.params["slow_period"])
        slow_ma_current = slow_ema[-1]

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
