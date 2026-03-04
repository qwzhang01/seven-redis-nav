"""
布林带策略
==========

价格触及下轨买入，触及上轨卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.strategy.base import Strategy, register_strategy
from quant_trading_system.strategy.strategy_signal import StrategySignal


@register_strategy
class BollingerBandStrategy(Strategy):
    """
    布林带策略

    价格触及下轨买入，触及上轨卖出
    """
    id: ClassVar[int] = 152410378779754497
    name: ClassVar[str] = "bollinger_band"
    description: ClassVar[str] = "布林带策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20},
        "std_dev": {"type": float, "default": 2.0},
    }

    symbols: ClassVar[tuple[str, ...]] = ("BTC/USDT",)
    timeframes: ClassVar[tuple[KlineInterval, ...]] = (KlineInterval.HOUR_1,)

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_position: str | None = None

    def on_bar(self, bar: Bar) -> StrategySignal | list[StrategySignal] | None:
        # 通过指标引擎计算布林带
        try:
            boll_result = self.calculate_indicator(
                "BOLL",
                period=self.params["period"],
                std_dev=self.params["std_dev"],
            )
        except (RuntimeError, ValueError):
            # 上下文未就绪或数据不足
            return None

        upper_current = boll_result["upper"][-1]
        lower_current = boll_result["lower"][-1]
        middle_current = boll_result["middle"][-1]

        # 检查是否为NaN（数据不足时）
        if np.isnan(upper_current) or np.isnan(lower_current) or np.isnan(middle_current):
            return None

        signal = None

        # 触及下轨买入信号
        if bar.close <= lower_current:
            if self._prev_position != "lower_touch":
                signal = self.buy(
                    bar.symbol,
                    reason=f"Price touched lower band: {bar.close:.2f} <= {lower_current:.2f}"
                )
                self._prev_position = "lower_touch"

        # 触及上轨卖出信号
        elif bar.close >= upper_current:
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
