"""
MACD策略
========

基于MACD金叉死叉的交易策略
"""

from typing import Any, ClassVar
import numpy as np

from quant_trading_system.models.market import Bar, TimeFrame
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.technical import MACD


@register_strategy
class MACDStrategy(Strategy):
    """
    MACD策略

    基于MACD金叉死叉的交易策略
    """

    id: int = 152410378779754499
    name: ClassVar[str] = "macd_cross"
    description: ClassVar[str] = "MACD交叉策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "fast_period": {"type": int, "default": 12},
        "slow_period": {"type": int, "default": 26},
        "signal_period": {"type": int, "default": 9},
    }

    symbols: ClassVar[list[str]] = ["BTC/USDT"]
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.H1]

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._prev_macd: float | None = None
        self._prev_signal: float | None = None
        self._close_prices: list[float] = []

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        # 收集收盘价数据
        self._close_prices.append(bar.close)

        # 确保有足够的数据计算MACD
        min_period = max(self.params["fast_period"], self.params["slow_period"], self.params["signal_period"])
        if len(self._close_prices) < min_period:
            return None

        # 使用MACD类的计算方法
        close_array = np.array(self._close_prices)

        # 创建MACD实例并计算
        macd_indicator = MACD(
            fast_period=self.params["fast_period"],
            slow_period=self.params["slow_period"],
            signal_period=self.params["signal_period"]
        )
        macd_result = macd_indicator.calculate(close_array)

        macd_current = macd_result.values["macd"][-1]
        signal_current = macd_result.values["signal"][-1]

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

    @staticmethod
    def calculate(close: np.ndarray, fast_period: int, slow_period: int, signal_period: int) -> dict:
        """计算MACD指标"""
        # 计算快慢EMA
        fast_ema = MACDStrategy._calculate_ema(close, fast_period)
        slow_ema = MACDStrategy._calculate_ema(close, slow_period)

        # MACD线
        macd = fast_ema - slow_ema

        # 信号线
        signal = MACDStrategy._calculate_ema(macd[~np.isnan(macd)], signal_period)

        # 填充信号线
        signal_full = np.full_like(close, np.nan)
        valid_start = np.where(~np.isnan(macd))[0]
        if len(valid_start) > 0:
            start_idx = valid_start[0]
            signal_full[start_idx:start_idx + len(signal)] = signal

        # 柱状图
        histogram = macd - signal_full

        return {
            "values": {
                "macd": macd,
                "signal": signal_full,
                "histogram": histogram
            }
        }

    @staticmethod
    def _calculate_ema(data: np.ndarray, period: int) -> np.ndarray:
        """计算EMA"""
        alpha = 2 / (period + 1)
        ema = np.full_like(data, np.nan, dtype=float)

        if len(data) < period:
            return ema

        # 初始值使用SMA
        ema[period - 1] = np.mean(data[:period])

        # 递推计算
        for i in range(period, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

        return ema
