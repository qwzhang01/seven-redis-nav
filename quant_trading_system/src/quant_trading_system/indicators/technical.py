"""
技术指标实现
============

实现常用的技术分析指标
"""

from typing import Any, ClassVar

import numpy as np

from quant_trading_system.indicators.base import (
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

        # 填充信号线（防御越界）
        signal_full = np.full_like(close, np.nan)
        valid_start = np.where(~np.isnan(macd))[0]
        if len(valid_start) > 0:
            start_idx = valid_start[0]
            available_len = min(len(signal), len(close) - start_idx)
            if available_len > 0:
                signal_full[start_idx:start_idx + available_len] = signal[:available_len]

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
        n = len(close)

        if n < period + 1:
            return IndicatorResult(
                name=self.name,
                values={"rsi": np.full(n, np.nan)},
                params=self.params,
            )

        # 计算价格变化
        delta = np.diff(close, prepend=close[0])

        # 分离涨跌
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        # 使用向量化 Wilder 平滑
        avg_gain = self._smooth_average_fast(gain, period)
        avg_loss = self._smooth_average_fast(loss, period)

        # 计算RSI（安全除法，避免 divide by zero 警告）
        rsi = np.full(n, np.nan)
        valid = ~np.isnan(avg_gain) & ~np.isnan(avg_loss)
        # avg_loss == 0 且 avg_gain > 0 → RSI = 100
        # avg_loss == 0 且 avg_gain == 0 → RSI = 50
        # 否则正常计算
        mask_zero_loss = valid & (avg_loss == 0)
        mask_normal = valid & (avg_loss != 0)

        rsi[mask_zero_loss & (avg_gain > 0)] = 100.0
        rsi[mask_zero_loss & (avg_gain == 0)] = 50.0

        if np.any(mask_normal):
            rs = avg_gain[mask_normal] / avg_loss[mask_normal]
            rsi[mask_normal] = 100.0 - 100.0 / (1.0 + rs)

        # 前 period 个值设为 NaN
        rsi[:period] = np.nan

        return IndicatorResult(
            name=self.name,
            values={"rsi": rsi},
            params=self.params,
        )

    @staticmethod
    def _smooth_average_fast(data: np.ndarray, period: int) -> np.ndarray:
        """向量化 Wilder 平滑（使用 scipy-style 递推的纯 numpy 实现）

        Wilder 递推: y[i] = (y[i-1] * (period-1) + x[i]) / period
        等价于指数平滑: y[i] = alpha * x[i] + (1-alpha) * y[i-1], alpha = 1/period

        虽然递推关系无法完全向量化，但对于小窗口（<500）
        直接 for 循环在 numpy scalar 上比创建临时数组更快。
        这里保持 for 循环但使用 float 变量避免数组索引开销。
        """
        n = len(data)
        result = np.full(n, np.nan, dtype=np.float64)

        if n < period:
            return result

        # 初始值使用 SMA
        alpha = 1.0 / period
        one_minus_alpha = 1.0 - alpha
        prev = float(np.mean(data[:period]))
        result[period - 1] = prev

        # 使用 float 标量递推（比 result[i-1] 数组索引快 ~3x）
        for i in range(period, n):
            prev = alpha * data[i] + one_minus_alpha * prev
            result[i] = prev

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

        if n < period:
            nan_arr = np.full(n, np.nan)
            return IndicatorResult(
                name=self.name,
                values={"middle": nan_arr, "upper": nan_arr.copy(), "lower": nan_arr.copy()},
                params=self.params,
            )

        # 向量化滑动窗口均值（使用 cumsum 技巧，O(n)）
        cs = np.cumsum(close)
        cs_padded = np.concatenate([[0.0], cs])
        # middle[i] = mean(close[i-period+1 : i+1])
        middle = np.full(n, np.nan)
        middle[period - 1:] = (cs_padded[period:] - cs_padded[:n - period + 1]) / period

        # 向量化滑动窗口标准差（使用 cumsum of squares 技巧，O(n)）
        cs2 = np.cumsum(close * close)
        cs2_padded = np.concatenate([[0.0], cs2])
        sum_sq = cs2_padded[period:] - cs2_padded[:n - period + 1]
        sum_vals = cs_padded[period:] - cs_padded[:n - period + 1]
        # ddof=1 的标准差: sqrt((sum_sq - sum_vals²/n) / (n-1))
        variance = (sum_sq - sum_vals * sum_vals / period) / (period - 1)
        # 防止浮点误差导致负方差
        variance = np.maximum(variance, 0.0)
        std_arr = np.sqrt(variance)

        upper = np.full(n, np.nan)
        lower = np.full(n, np.nan)
        upper[period - 1:] = middle[period - 1:] + std_dev * std_arr
        lower[period - 1:] = middle[period - 1:] - std_dev * std_arr

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


@register_indicator
class SuperTrend(Indicator):
    """
    超级趋势指标 (SuperTrend)

    基于 ATR 的趋势跟踪指标。
    - 当价格在 SuperTrend 线之上时为看涨（绿色），direction = 1
    - 当价格在 SuperTrend 线之下时为看跌（红色），direction = -1

    输出:
        supertrend: SuperTrend 线的值
        direction:  1 表示看涨，-1 表示看跌
    """

    name: ClassVar[str] = "SUPERTREND"
    description: ClassVar[str] = "超级趋势指标"
    indicator_type: ClassVar[str] = "trend"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "atr_period": {"type": int, "default": 10, "min": 1, "max": 200},
        "multiplier": {"type": float, "default": 3.0, "min": 0.1, "max": 20.0},
    }

    outputs: ClassVar[list[str]] = ["supertrend", "direction"]

    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        open: np.ndarray | None = None,
        volume: np.ndarray | None = None,
    ) -> IndicatorResult:
        if high is None or low is None:
            raise ValueError("SuperTrend requires high and low prices")

        atr_period = self.params["atr_period"]
        multiplier = self.params["multiplier"]
        n = len(close)

        supertrend = np.full(n, np.nan)
        direction = np.full(n, np.nan)

        if n < atr_period + 1:
            return IndicatorResult(
                name=self.name,
                values={"supertrend": supertrend, "direction": direction},
                params=self.params,
            )

        # ---- 向量化计算 True Range ----
        tr = np.empty(n)
        tr[0] = high[0] - low[0]
        hl = high[1:] - low[1:]
        hc = np.abs(high[1:] - close[:-1])
        lc = np.abs(low[1:] - close[:-1])
        tr[1:] = np.maximum(np.maximum(hl, hc), lc)

        # ---- ATR（Wilder 平滑，标量递推优化） ----
        atr = np.full(n, np.nan)
        alpha = 1.0 / atr_period
        one_minus_alpha = 1.0 - alpha
        prev_atr = float(np.mean(tr[:atr_period]))
        atr[atr_period - 1] = prev_atr

        for i in range(atr_period, n):
            prev_atr = alpha * tr[i] + one_minus_alpha * prev_atr
            atr[i] = prev_atr

        # ---- 向量化计算基础上/下轨 ----
        hl2 = (high + low) * 0.5
        basic_upper = hl2 + multiplier * atr
        basic_lower = hl2 - multiplier * atr

        # ---- SuperTrend 主循环（标量优化，减少数组索引开销） ----
        final_upper = np.full(n, np.nan)
        final_lower = np.full(n, np.nan)

        start = atr_period - 1

        fu = float(basic_upper[start])
        fl = float(basic_lower[start])
        final_upper[start] = fu
        final_lower[start] = fl

        cur_dir = 1.0 if close[start] > fu else -1.0
        direction[start] = cur_dir
        supertrend[start] = fl if cur_dir == 1.0 else fu

        # 预取为局部变量，避免循环内属性查找
        _close = close
        _bu = basic_upper
        _bl = basic_lower

        for i in range(start + 1, n):
            prev_close = _close[i - 1]
            bu_i = _bu[i]
            bl_i = _bl[i]

            # 上轨平滑
            if prev_close <= fu:
                fu = min(bu_i, fu)
            else:
                fu = bu_i
            final_upper[i] = fu

            # 下轨平滑
            if prev_close >= fl:
                fl = max(bl_i, fl)
            else:
                fl = bl_i
            final_lower[i] = fl

            # 方向判定
            c_i = _close[i]
            if cur_dir == 1.0:
                if c_i < fl:
                    cur_dir = -1.0
            else:
                if c_i > fu:
                    cur_dir = 1.0

            direction[i] = cur_dir
            supertrend[i] = fl if cur_dir == 1.0 else fu

        return IndicatorResult(
            name=self.name,
            values={"supertrend": supertrend, "direction": direction},
            params=self.params,
        )
