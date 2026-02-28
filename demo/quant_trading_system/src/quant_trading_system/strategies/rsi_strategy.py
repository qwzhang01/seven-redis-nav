"""
RSI超买超卖策略
==============

RSI低于超卖线买入，高于超买线卖出
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.technical import RSI


@register_strategy
class RSIStrategy(Strategy):
    """
    RSI超买超卖策略

    RSI低于超卖线买入，高于超买线卖出
    """
    id:int = 152410378779754500
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
        self._close_prices: list[float] = []
        self._prev_rsi: float | None = None

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        # 收集收盘价数据
        self._close_prices.append(bar.close)

        # 确保有足够的数据计算RSI
        if len(self._close_prices) < self.params["period"] + 1:
            return None

        # 使用RSI类的计算方法
        close_array = np.array(self._close_prices)

        # 创建RSI实例并计算
        rsi_indicator = RSI(period=self.params["period"])
        rsi_result = rsi_indicator.calculate(close_array)
        rsi_current = rsi_result.values["rsi"][-1]

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

    @staticmethod
    def _calculate_rsi(prices: np.ndarray, period: int) -> np.ndarray:
        """计算RSI指标"""
        n = len(prices)
        rsi = np.full(n, np.nan, dtype=float)

        if n < period + 1:
            return rsi

        # 计算价格变化
        delta = np.diff(prices, prepend=prices[0])

        # 分离涨跌
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # 计算平均涨跌（Wilder平滑）
        avg_gain = np.full(n, np.nan)
        avg_loss = np.full(n, np.nan)

        # 初始值使用SMA
        avg_gain[period] = np.mean(gain[1:period + 1])
        avg_loss[period] = np.mean(loss[1:period + 1])

        # Wilder平滑
        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period

        # 计算RSI
        for i in range(period, n):
            if avg_loss[i] == 0:
                rsi[i] = 100
            else:
                rs = avg_gain[i] / avg_loss[i]
                rsi[i] = 100 - 100 / (1 + rs)

        return rsi
