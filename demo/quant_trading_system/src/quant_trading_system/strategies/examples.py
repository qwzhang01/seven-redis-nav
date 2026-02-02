"""
示例策略
========

提供一些内置的示例策略
"""

from typing import Any, ClassVar

from quant_trading_system.models.market import Bar, TimeFrame
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal, SignalType


@register_strategy
class DualMAStrategy(Strategy):
    """
    双均线策略
    
    当快线上穿慢线时买入，下穿时卖出
    """
    
    name: ClassVar[str] = "dual_ma"
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
    
    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        # 计算均线
        try:
            fast_result = self.calculate_indicator(
                "SMA", 
                period=self.params["fast_period"]
            )
            slow_result = self.calculate_indicator(
                "SMA", 
                period=self.params["slow_period"]
            )
        except Exception:
            return None
        
        fast_ma = fast_result["sma"][-1]
        slow_ma = slow_result["sma"][-1]
        
        signal = None
        
        # 金叉买入
        if (self._prev_fast_ma is not None and 
            self._prev_slow_ma is not None):
            
            if (self._prev_fast_ma < self._prev_slow_ma and 
                fast_ma > slow_ma):
                signal = self.buy(
                    bar.symbol,
                    reason="MA golden cross"
                )
            
            # 死叉卖出
            elif (self._prev_fast_ma > self._prev_slow_ma and 
                  fast_ma < slow_ma):
                position = self.get_position(bar.symbol)
                if position and position.quantity > 0:
                    signal = self.sell(
                        bar.symbol,
                        quantity=position.quantity,
                        reason="MA death cross"
                    )
        
        # 保存当前均线值
        self._prev_fast_ma = fast_ma
        self._prev_slow_ma = slow_ma
        
        return signal


@register_strategy
class MACDStrategy(Strategy):
    """
    MACD策略
    
    基于MACD金叉死叉的交易策略
    """
    
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
        self._prev_histogram: float | None = None
    
    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        try:
            result = self.calculate_indicator(
                "MACD",
                fast_period=self.params["fast_period"],
                slow_period=self.params["slow_period"],
                signal_period=self.params["signal_period"],
            )
        except Exception:
            return None
        
        histogram = result["histogram"][-1]
        
        signal = None
        
        if self._prev_histogram is not None:
            # MACD柱由负转正，买入
            if self._prev_histogram < 0 and histogram > 0:
                signal = self.buy(
                    bar.symbol,
                    reason="MACD histogram crossover"
                )
            
            # MACD柱由正转负，卖出
            elif self._prev_histogram > 0 and histogram < 0:
                position = self.get_position(bar.symbol)
                if position and position.quantity > 0:
                    signal = self.sell(
                        bar.symbol,
                        quantity=position.quantity,
                        reason="MACD histogram crossunder"
                    )
        
        self._prev_histogram = histogram
        
        return signal


@register_strategy
class RSIStrategy(Strategy):
    """
    RSI超买超卖策略
    
    RSI低于超卖线买入，高于超买线卖出
    """
    
    name: ClassVar[str] = "rsi_ob_os"
    description: ClassVar[str] = "RSI超买超卖策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14},
        "overbought": {"type": float, "default": 70.0},
        "oversold": {"type": float, "default": 30.0},
    }
    
    symbols: ClassVar[list[str]] = ["BTC/USDT"]
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.H4]
    
    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        self._in_position = False
    
    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        try:
            result = self.calculate_indicator(
                "RSI",
                period=self.params["period"],
            )
        except Exception:
            return None
        
        rsi = result["rsi"][-1]
        
        signal = None
        
        # 超卖买入
        if rsi < self.params["oversold"] and not self._in_position:
            signal = self.buy(
                bar.symbol,
                reason=f"RSI oversold: {rsi:.2f}"
            )
            self._in_position = True
        
        # 超买卖出
        elif rsi > self.params["overbought"] and self._in_position:
            position = self.get_position(bar.symbol)
            if position and position.quantity > 0:
                signal = self.sell(
                    bar.symbol,
                    quantity=position.quantity,
                    reason=f"RSI overbought: {rsi:.2f}"
                )
                self._in_position = False
        
        return signal


@register_strategy
class BollingerBandStrategy(Strategy):
    """
    布林带策略
    
    价格触及下轨买入，触及上轨卖出
    """
    
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
        self._in_position = False
    
    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        try:
            result = self.calculate_indicator(
                "BOLL",
                period=self.params["period"],
                std_dev=self.params["std_dev"],
            )
        except Exception:
            return None
        
        upper = result["upper"][-1]
        lower = result["lower"][-1]
        middle = result["middle"][-1]
        
        signal = None
        
        # 触及下轨买入
        if bar.close <= lower and not self._in_position:
            signal = self.buy(
                bar.symbol,
                reason=f"Price touched lower band: {bar.close:.2f}"
            )
            self._in_position = True
        
        # 触及上轨卖出
        elif bar.close >= upper and self._in_position:
            position = self.get_position(bar.symbol)
            if position and position.quantity > 0:
                signal = self.sell(
                    bar.symbol,
                    quantity=position.quantity,
                    reason=f"Price touched upper band: {bar.close:.2f}"
                )
                self._in_position = False
        
        return signal
