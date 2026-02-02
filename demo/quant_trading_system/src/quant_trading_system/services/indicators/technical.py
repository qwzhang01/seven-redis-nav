"""
技术指标实现
============

实现常用的技术分析指标
"""

from typing import Any, ClassVar

import numpy as np

from quant_trading_system.services.indicators.base import (
    Indicator,
    IndicatorResult,
    register_indicator,
)


@register_indicator
class SMA(Indicator):
    """
    简单移动平均线 (Simple Moving Average)
    """
    
    name: ClassVar[str] = "SMA"
    description: ClassVar[str] = "简单移动平均线"
    indicator_type: ClassVar[str] = "trend"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20, "min": 1, "max": 500},
    }
    
    outputs: ClassVar[list[str]] = ["sma"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        period = self.params["period"]
        
        # 使用卷积计算SMA
        if len(close) < period:
            sma = np.full_like(close, np.nan)
        else:
            kernel = np.ones(period) / period
            sma = np.convolve(close, kernel, mode="valid")
            # 填充前面的NaN
            sma = np.concatenate([np.full(period - 1, np.nan), sma])
        
        return IndicatorResult(
            name=self.name,
            values={"sma": sma},
            params=self.params,
        )


@register_indicator
class EMA(Indicator):
    """
    指数移动平均线 (Exponential Moving Average)
    """
    
    name: ClassVar[str] = "EMA"
    description: ClassVar[str] = "指数移动平均线"
    indicator_type: ClassVar[str] = "trend"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20, "min": 1, "max": 500},
    }
    
    outputs: ClassVar[list[str]] = ["ema"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        period = self.params["period"]
        
        ema = self._calculate_ema(close, period)
        
        return IndicatorResult(
            name=self.name,
            values={"ema": ema},
            params=self.params,
        )
    
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


@register_indicator
class MACD(Indicator):
    """
    MACD指标 (Moving Average Convergence Divergence)
    """
    
    name: ClassVar[str] = "MACD"
    description: ClassVar[str] = "平滑异同移动平均线"
    indicator_type: ClassVar[str] = "trend"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "fast_period": {"type": int, "default": 12, "min": 1},
        "slow_period": {"type": int, "default": 26, "min": 1},
        "signal_period": {"type": int, "default": 9, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["macd", "signal", "histogram"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        fast_period = self.params["fast_period"]
        slow_period = self.params["slow_period"]
        signal_period = self.params["signal_period"]
        
        # 计算快慢EMA
        fast_ema = EMA._calculate_ema(close, fast_period)
        slow_ema = EMA._calculate_ema(close, slow_period)
        
        # MACD线
        macd = fast_ema - slow_ema
        
        # 信号线
        signal = EMA._calculate_ema(macd[~np.isnan(macd)], signal_period)
        
        # 填充信号线
        signal_full = np.full_like(close, np.nan)
        valid_start = np.where(~np.isnan(macd))[0]
        if len(valid_start) > 0:
            start_idx = valid_start[0]
            signal_full[start_idx:start_idx + len(signal)] = signal
        
        # 柱状图
        histogram = macd - signal_full
        
        return IndicatorResult(
            name=self.name,
            values={
                "macd": macd,
                "signal": signal_full,
                "histogram": histogram,
            },
            params=self.params,
        )


@register_indicator
class RSI(Indicator):
    """
    相对强弱指标 (Relative Strength Index)
    """
    
    name: ClassVar[str] = "RSI"
    description: ClassVar[str] = "相对强弱指标"
    indicator_type: ClassVar[str] = "momentum"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14, "min": 1, "max": 100},
    }
    
    outputs: ClassVar[list[str]] = ["rsi"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        period = self.params["period"]
        
        # 计算价格变化
        delta = np.diff(close, prepend=close[0])
        
        # 分离涨跌
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # 计算平均涨跌
        avg_gain = self._smooth_average(gain, period)
        avg_loss = self._smooth_average(loss, period)
        
        # 计算RSI
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
        rsi = 100 - 100 / (1 + rs)
        
        # 前period个值设为NaN
        rsi[:period] = np.nan
        
        return IndicatorResult(
            name=self.name,
            values={"rsi": rsi},
            params=self.params,
        )
    
    @staticmethod
    def _smooth_average(data: np.ndarray, period: int) -> np.ndarray:
        """平滑平均（Wilder平滑）"""
        result = np.full_like(data, np.nan, dtype=float)
        
        if len(data) < period:
            return result
        
        # 初始值使用SMA
        result[period - 1] = np.mean(data[:period])
        
        # Wilder平滑
        for i in range(period, len(data)):
            result[i] = (result[i - 1] * (period - 1) + data[i]) / period
        
        return result


@register_indicator
class KDJ(Indicator):
    """
    KDJ随机指标
    """
    
    name: ClassVar[str] = "KDJ"
    description: ClassVar[str] = "随机指标"
    indicator_type: ClassVar[str] = "momentum"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "k_period": {"type": int, "default": 9, "min": 1},
        "d_period": {"type": int, "default": 3, "min": 1},
        "j_period": {"type": int, "default": 3, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["k", "d", "j"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None:
            raise ValueError("KDJ requires high and low prices")
        
        k_period = self.params["k_period"]
        d_period = self.params["d_period"]
        
        n = len(close)
        rsv = np.full(n, np.nan)
        
        # 计算RSV
        for i in range(k_period - 1, n):
            highest = np.max(high[i - k_period + 1:i + 1])
            lowest = np.min(low[i - k_period + 1:i + 1])
            
            if highest != lowest:
                rsv[i] = (close[i] - lowest) / (highest - lowest) * 100
            else:
                rsv[i] = 50
        
        # 计算K值
        k = np.full(n, np.nan)
        k[k_period - 1] = 50  # 初始值
        
        for i in range(k_period, n):
            k[i] = (2 / 3) * k[i - 1] + (1 / 3) * rsv[i]
        
        # 计算D值
        d = np.full(n, np.nan)
        d[k_period - 1] = 50  # 初始值
        
        for i in range(k_period, n):
            d[i] = (2 / 3) * d[i - 1] + (1 / 3) * k[i]
        
        # 计算J值
        j = 3 * k - 2 * d
        
        return IndicatorResult(
            name=self.name,
            values={"k": k, "d": d, "j": j},
            params=self.params,
        )


@register_indicator
class BOLL(Indicator):
    """
    布林带 (Bollinger Bands)
    """
    
    name: ClassVar[str] = "BOLL"
    description: ClassVar[str] = "布林带"
    indicator_type: ClassVar[str] = "volatility"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20, "min": 1},
        "std_dev": {"type": float, "default": 2.0, "min": 0.1},
    }
    
    outputs: ClassVar[list[str]] = ["middle", "upper", "lower"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        period = self.params["period"]
        std_dev = self.params["std_dev"]
        
        n = len(close)
        middle = np.full(n, np.nan)
        upper = np.full(n, np.nan)
        lower = np.full(n, np.nan)
        
        for i in range(period - 1, n):
            window = close[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window, ddof=1)
            
            middle[i] = mean
            upper[i] = mean + std_dev * std
            lower[i] = mean - std_dev * std
        
        return IndicatorResult(
            name=self.name,
            values={
                "middle": middle,
                "upper": upper,
                "lower": lower,
            },
            params=self.params,
        )


@register_indicator
class ATR(Indicator):
    """
    真实波幅 (Average True Range)
    """
    
    name: ClassVar[str] = "ATR"
    description: ClassVar[str] = "平均真实波幅"
    indicator_type: ClassVar[str] = "volatility"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["atr"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None:
            raise ValueError("ATR requires high and low prices")
        
        period = self.params["period"]
        
        # 计算真实波幅
        tr = np.zeros(len(close))
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(close)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1])
            )
        
        # 计算ATR（使用Wilder平滑）
        atr = np.full_like(close, np.nan)
        
        if len(close) >= period:
            atr[period - 1] = np.mean(tr[:period])
            
            for i in range(period, len(close)):
                atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        
        return IndicatorResult(
            name=self.name,
            values={"atr": atr},
            params=self.params,
        )


@register_indicator
class CCI(Indicator):
    """
    商品通道指标 (Commodity Channel Index)
    """
    
    name: ClassVar[str] = "CCI"
    description: ClassVar[str] = "商品通道指标"
    indicator_type: ClassVar[str] = "momentum"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 20, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["cci"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None:
            raise ValueError("CCI requires high and low prices")
        
        period = self.params["period"]
        
        # 典型价格
        tp = (high + low + close) / 3
        
        n = len(close)
        cci = np.full(n, np.nan)
        
        for i in range(period - 1, n):
            window = tp[i - period + 1:i + 1]
            mean = np.mean(window)
            mad = np.mean(np.abs(window - mean))  # 平均绝对偏差
            
            if mad != 0:
                cci[i] = (tp[i] - mean) / (0.015 * mad)
            else:
                cci[i] = 0
        
        return IndicatorResult(
            name=self.name,
            values={"cci": cci},
            params=self.params,
        )


@register_indicator
class OBV(Indicator):
    """
    能量潮指标 (On Balance Volume)
    """
    
    name: ClassVar[str] = "OBV"
    description: ClassVar[str] = "能量潮指标"
    indicator_type: ClassVar[str] = "volume"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {}
    
    outputs: ClassVar[list[str]] = ["obv"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if volume is None:
            raise ValueError("OBV requires volume data")
        
        obv = np.zeros(len(close))
        obv[0] = volume[0]
        
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif close[i] < close[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        
        return IndicatorResult(
            name=self.name,
            values={"obv": obv},
            params=self.params,
        )


@register_indicator
class MFI(Indicator):
    """
    资金流量指标 (Money Flow Index)
    """
    
    name: ClassVar[str] = "MFI"
    description: ClassVar[str] = "资金流量指标"
    indicator_type: ClassVar[str] = "volume"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["mfi"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None or volume is None:
            raise ValueError("MFI requires high, low and volume data")
        
        period = self.params["period"]
        
        # 典型价格
        tp = (high + low + close) / 3
        
        # 资金流量
        mf = tp * volume
        
        n = len(close)
        mfi = np.full(n, np.nan)
        
        for i in range(period, n):
            positive_mf = 0.0
            negative_mf = 0.0
            
            for j in range(i - period + 1, i + 1):
                if tp[j] > tp[j - 1]:
                    positive_mf += mf[j]
                elif tp[j] < tp[j - 1]:
                    negative_mf += mf[j]
            
            if negative_mf != 0:
                mfr = positive_mf / negative_mf
                mfi[i] = 100 - 100 / (1 + mfr)
            else:
                mfi[i] = 100
        
        return IndicatorResult(
            name=self.name,
            values={"mfi": mfi},
            params=self.params,
        )


@register_indicator
class WR(Indicator):
    """
    威廉指标 (Williams %R)
    """
    
    name: ClassVar[str] = "WR"
    description: ClassVar[str] = "威廉指标"
    indicator_type: ClassVar[str] = "momentum"
    
    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "period": {"type": int, "default": 14, "min": 1},
    }
    
    outputs: ClassVar[list[str]] = ["wr"]
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None:
            raise ValueError("WR requires high and low prices")
        
        period = self.params["period"]
        
        n = len(close)
        wr = np.full(n, np.nan)
        
        for i in range(period - 1, n):
            highest = np.max(high[i - period + 1:i + 1])
            lowest = np.min(low[i - period + 1:i + 1])
            
            if highest != lowest:
                wr[i] = -100 * (highest - close[i]) / (highest - lowest)
            else:
                wr[i] = -50
        
        return IndicatorResult(
            name=self.name,
            values={"wr": wr},
            params=self.params,
        )
