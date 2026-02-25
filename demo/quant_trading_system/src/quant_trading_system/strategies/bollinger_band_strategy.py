"""
布林带策略
==========

价格触及下轨买入，触及上轨卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar, TimeFrame
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.technical import BOLL


@register_strategy
class BollingerBandStrategy(Strategy):
    """
    布林带策略

    价格触及下轨买入，触及上轨卖出
    """
    id:int = 152410378779754497
    name: ClassVar[str] = "bollinger_band"
    description: ClassVar[str] = "布林带策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20},
        "std_dev": {"type": float, "default": 2.0},
    }

    symbols: ClassVar[list[str]] = ["BTC/USDT"]
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.H1]

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._close_prices: list[float] = []
        self._prev_position: str | None = None

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        # 收集收盘价数据
        self._close_prices.append(bar.close)

        # 确保有足够的数据计算布林带
        if len(self._close_prices) < self.params["period"]:
            return None

        # 计算布林带指标
        close_array = np.array(self._close_prices)

        # 使用BOLL类的计算方法
        boll_indicator = BOLL(
            period=self.params["period"],
            std_dev=self.params["std_dev"]
        )
        boll_result = boll_indicator.calculate(close_array)

        upper_current = boll_result.values["upper"][-1]
        lower_current = boll_result.values["lower"][-1]
        middle_current = boll_result.values["middle"][-1]

        # 检查是否为NaN（数据不足时）
        if np.isnan(upper_current) or np.isnan(lower_current) or np.isnan(middle_current):
            return None

        signal = None

        # 触及下轨买入信号
        if bar.close <= lower_current:
            # 避免连续触发，检查是否从下轨反弹
            if self._prev_position != "lower_touch":
                signal = self.buy(
                    bar.symbol,
                    reason=f"Price touched lower band: {bar.close:.2f} <= {lower_current:.2f}"
                )
                self._prev_position = "lower_touch"

        # 触及上轨卖出信号
        elif bar.close >= upper_current:
            # 避免连续触发，检查是否从上轨回落
            if self._prev_position != "upper_touch":
                signal = self.sell(
                    bar.symbol,
                    reason=f"Price touched upper band: {bar.close:.2f} >= {upper_current:.2f}"
                )
                self._prev_position = "upper_touch"

        # 价格回到中间区域时重置状态
        elif lower_current < bar.close < upper_current:
            self._prev_position = None

        return signal

    @staticmethod
    def _calculate_bollinger_bands(prices: np.ndarray, period: int, std_dev: float) -> dict:
        """计算布林带指标"""
        n = len(prices)
        middle = np.full(n, np.nan, dtype=float)
        upper = np.full(n, np.nan, dtype=float)
        lower = np.full(n, np.nan, dtype=float)

        for i in range(period - 1, n):
            window = prices[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window, ddof=1)

            middle[i] = mean
            upper[i] = mean + std_dev * std
            lower[i] = mean - std_dev * std

        return {
            "middle": middle,
            "upper": upper,
            "lower": lower
        }
