"""
多周期趋势 + MA(11) 回调突破 + 固定盈亏比交易策略
================================================

策略核心思想：
- 高周期定方向，低周期找入场
- 只在趋势方向上交易，不逆势
- 回调后突破均线进场，避免追高/追低
- 使用结构止损 + 固定盈亏比止盈
- 所有关键变量可参数化

周期关联规则（固定）：
    入场周期    趋势参考周期
    15 分钟      1 小时
    30 分钟      2 小时
    1 小时       4 小时
    4 小时       日线

以 15 分钟入场 + 1 小时定方向 为默认配置，其余周期可通过参数切换。
"""

from typing import Any, ClassVar

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, TimeFrame
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal

logger = structlog.get_logger(__name__)

# 周期关联映射：入场周期 -> 趋势参考周期
TIMEFRAME_MAP: dict[TimeFrame, TimeFrame] = {
    TimeFrame.M15: TimeFrame.H1,
    TimeFrame.M30: TimeFrame.H4,   # 30分钟 -> 近似2小时用H4
    TimeFrame.H1: TimeFrame.H4,
    TimeFrame.H4: TimeFrame.D1,
}


@register_strategy
class MultiTimeframeMABreakoutStrategy(Strategy):
    """
    多周期趋势 + MA(11) 回调突破 + 固定盈亏比策略

    做多逻辑：
        ① 大周期趋势判断：当前大周期K线为阳线 且 开盘价在 MA(11) 之上
        ② 小周期回调突破：当前K线为阳线，前一根收盘 ≤ MA11，当前收盘 > MA11，
           且突破K线前面至少 min_pullback_bars 根、最多 max_pullback_bars 根K线收盘在 MA11 下方
        ③ 止损 = 回调结构最低价
        ④ 止盈 = 入场价 + (入场价 - 止损) × 盈亏比

    做空完全镜像。
    """

    name: ClassVar[str] = "mtf_ma_breakout"
    description: ClassVar[str] = "多周期趋势+MA(11)回调突破+固定盈亏比策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        "ma_period": {
            "type": int,
            "default": 11,
            "min": 2,
            "max": 200,
            "description": "移动平均线周期",
        },
        "risk_reward_ratio": {
            "type": float,
            "default": 2.0,
            "min": 0.5,
            "max": 10.0,
            "description": "盈亏比（止盈 = 风险 × 该值）",
        },
        "min_pullback_bars": {
            "type": int,
            "default": 3,
            "min": 1,
            "max": 20,
            "description": "回调结构最少K线根数（收盘在MA另一侧）",
        },
        "max_pullback_bars": {
            "type": int,
            "default": 5,
            "min": 2,
            "max": 50,
            "description": "回调结构最多K线根数（收盘在MA另一侧）",
        },
    }

    symbols: ClassVar[list[str]] = ["BTC/USDT"]
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.M15, TimeFrame.H1]

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        # 入场周期 & 趋势周期
        self._entry_tf: TimeFrame = self.timeframes[0]   # 默认 M15
        self._trend_tf: TimeFrame = self.timeframes[1] if len(self.timeframes) > 1 else TIMEFRAME_MAP.get(self._entry_tf, TimeFrame.H1)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        logger.info(
            "MultiTimeframeMABreakout initialized",
            entry_tf=self._entry_tf.value,
            trend_tf=self._trend_tf.value,
            params=self.params,
        )

    # ------------------------------------------------------------------
    # 核心回调：on_bar
    # ------------------------------------------------------------------

    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        """
        只在入场周期的K线触发时执行完整判断。
        趋势周期的K线仅用于更新 context 中的 bars 缓存（引擎自动处理）。
        """
        # 仅在入场周期 K 线到达时做判断
        if bar.timeframe != self._entry_tf:
            return None

        symbol = bar.symbol

        # ---------- 获取多周期 K 线数据 ----------
        entry_bars = self.context.get_bars(symbol, self._entry_tf)
        trend_bars = self.context.get_bars(symbol, self._trend_tf)

        if entry_bars is None or trend_bars is None:
            return None

        ma_period: int = self.params["ma_period"]

        # 入场周期至少需要 ma_period + max_pullback_bars 根 K 线
        min_entry_len = ma_period + self.params["max_pullback_bars"] + 1
        if len(entry_bars) < min_entry_len:
            return None
        if len(trend_bars) < ma_period + 1:
            return None

        # ---------- 计算 MA ----------
        entry_ma = self._calc_sma(entry_bars.close, ma_period)
        trend_ma = self._calc_sma(trend_bars.close, ma_period)

        # 如果 MA 尚未有效，跳过
        if np.isnan(entry_ma[-1]) or np.isnan(trend_ma[-1]):
            return None

        # ---------- 已有持仓时不重复开仓 ----------
        position = self.get_position(symbol)
        if position and position.quantity != 0:
            return None

        # ---------- 多空判断 ----------
        long_signal = self._check_long(
            symbol, bar, entry_bars, trend_bars, entry_ma, trend_ma
        )
        if long_signal is not None:
            return long_signal

        short_signal = self._check_short(
            symbol, bar, entry_bars, trend_bars, entry_ma, trend_ma
        )
        if short_signal is not None:
            return short_signal

        return None

    # ------------------------------------------------------------------
    # 做多判断
    # ------------------------------------------------------------------

    def _check_long(
        self,
        symbol: str,
        bar: Bar,
        entry_bars,
        trend_bars,
        entry_ma: np.ndarray,
        trend_ma: np.ndarray,
    ) -> Signal | None:
        """
        做多条件：
        ① 大周期：当前K线为阳线 且 开盘价 > MA(11)
        ② 小周期：当前K线阳线，前一根收盘 ≤ MA11，当前收盘 > MA11
           前面 min~max 根K线收盘在 MA11 下方（回调结构）
        ③ 止损 = 回调区间最低价
        ④ 止盈 = 入场价 + 风险 × RR
        """
        # ---- ① 大周期趋势 ----
        if len(trend_bars.close) < 1:
            return None

        trend_open_last = float(trend_bars.open[-1])
        trend_close_last = float(trend_bars.close[-1])
        trend_ma_last = float(trend_ma[-1])

        # 大周期阳线
        if trend_close_last <= trend_open_last:
            return None
        # 大周期开盘价在 MA 之上
        if trend_open_last <= trend_ma_last:
            return None

        # ---- ② 小周期回调突破 ----
        if len(entry_bars.close) < 2:
            return None

        entry_close = entry_bars.close
        entry_open = entry_bars.open
        entry_low = entry_bars.low

        cur_close = float(entry_close[-1])
        cur_open = float(entry_open[-1])
        prev_close = float(entry_close[-2])
        cur_ma = float(entry_ma[-1])
        prev_ma = float(entry_ma[-2])

        # 当前K线为阳线
        if cur_close <= cur_open:
            return None
        # 前一根收盘 ≤ MA，当前收盘 > MA（向上突破）
        if not (prev_close <= prev_ma and cur_close > cur_ma):
            return None

        # 回调结构：突破K线前面 min~max 根K线收盘在 MA 下方
        min_pb = self.params["min_pullback_bars"]
        max_pb = self.params["max_pullback_bars"]

        pullback_count = self._count_pullback_bars_below(entry_close, entry_ma, max_pb)
        if pullback_count < min_pb:
            return None

        # ---- ③ 止损 = 回调区间最低价 ----
        # 回调区间为当前K线前面 pullback_count 根K线 + 前一根
        lookback = pullback_count + 1  # 包含前一根（突破前最后一根）
        if len(entry_low) < lookback + 1:
            return None

        pullback_lows = entry_low[-(lookback + 1):-1]  # 不含当前K线
        stop_loss = float(np.min(pullback_lows))

        entry_price = cur_close
        if stop_loss >= entry_price:
            return None  # 无效止损

        # ---- ④ 止盈 ----
        risk = entry_price - stop_loss
        rr = self.params["risk_reward_ratio"]
        take_profit = entry_price + risk * rr

        return self.open_long(
            symbol=symbol,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=(
                f"MTF MA Breakout Long | "
                f"entry={entry_price:.4f} sl={stop_loss:.4f} tp={take_profit:.4f} "
                f"risk={risk:.4f} RR={rr} pullback_bars={pullback_count}"
            ),
        )

    # ------------------------------------------------------------------
    # 做空判断（完全镜像）
    # ------------------------------------------------------------------

    def _check_short(
        self,
        symbol: str,
        bar: Bar,
        entry_bars,
        trend_bars,
        entry_ma: np.ndarray,
        trend_ma: np.ndarray,
    ) -> Signal | None:
        """
        做空条件（做多的完全镜像）：
        ① 大周期：当前K线为阴线 且 开盘价 < MA(11)
        ② 小周期：当前K线阴线，前一根收盘 ≥ MA11，当前收盘 < MA11
           前面 min~max 根K线收盘在 MA11 上方（反弹结构）
        ③ 止损 = 反弹区间最高价
        ④ 止盈 = 入场价 - 风险 × RR
        """
        # ---- ① 大周期趋势 ----
        if len(trend_bars.close) < 1:
            return None

        trend_open_last = float(trend_bars.open[-1])
        trend_close_last = float(trend_bars.close[-1])
        trend_ma_last = float(trend_ma[-1])

        # 大周期阴线
        if trend_close_last >= trend_open_last:
            return None
        # 大周期开盘价在 MA 之下
        if trend_open_last >= trend_ma_last:
            return None

        # ---- ② 小周期反弹后向下突破 ----
        if len(entry_bars.close) < 2:
            return None

        entry_close = entry_bars.close
        entry_open = entry_bars.open
        entry_high = entry_bars.high

        cur_close = float(entry_close[-1])
        cur_open = float(entry_open[-1])
        prev_close = float(entry_close[-2])
        cur_ma = float(entry_ma[-1])
        prev_ma = float(entry_ma[-2])

        # 当前K线为阴线
        if cur_close >= cur_open:
            return None
        # 前一根收盘 ≥ MA，当前收盘 < MA（向下突破）
        if not (prev_close >= prev_ma and cur_close < cur_ma):
            return None

        # 反弹结构：前面 min~max 根K线收盘在 MA 上方
        min_pb = self.params["min_pullback_bars"]
        max_pb = self.params["max_pullback_bars"]

        pullback_count = self._count_pullback_bars_above(entry_close, entry_ma, max_pb)
        if pullback_count < min_pb:
            return None

        # ---- ③ 止损 = 反弹区间最高价 ----
        lookback = pullback_count + 1
        if len(entry_high) < lookback + 1:
            return None

        pullback_highs = entry_high[-(lookback + 1):-1]
        stop_loss = float(np.max(pullback_highs))

        entry_price = cur_close
        if stop_loss <= entry_price:
            return None  # 无效止损

        # ---- ④ 止盈 ----
        risk = stop_loss - entry_price
        rr = self.params["risk_reward_ratio"]
        take_profit = entry_price - risk * rr

        return self.open_short(
            symbol=symbol,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=(
                f"MTF MA Breakout Short | "
                f"entry={entry_price:.4f} sl={stop_loss:.4f} tp={take_profit:.4f} "
                f"risk={risk:.4f} RR={rr} pullback_bars={pullback_count}"
            ),
        )

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_sma(data: np.ndarray, period: int) -> np.ndarray:
        """计算简单移动平均线（与系统 SMA 指标一致的逻辑）"""
        if len(data) < period:
            return np.full_like(data, np.nan)
        kernel = np.ones(period) / period
        sma = np.convolve(data, kernel, mode="valid")
        return np.concatenate([np.full(period - 1, np.nan), sma])

    @staticmethod
    def _count_pullback_bars_below(
        close: np.ndarray,
        ma: np.ndarray,
        max_lookback: int,
    ) -> int:
        """
        从倒数第 2 根K线开始往前数，连续收盘 ≤ MA 的K线根数，
        最多数 max_lookback 根。
        """
        count = 0
        for i in range(2, 2 + max_lookback):
            idx = -i
            if abs(idx) > len(close):
                break
            if float(close[idx]) <= float(ma[idx]):
                count += 1
            else:
                break
        return count

    @staticmethod
    def _count_pullback_bars_above(
        close: np.ndarray,
        ma: np.ndarray,
        max_lookback: int,
    ) -> int:
        """
        从倒数第 2 根K线开始往前数，连续收盘 ≥ MA 的K线根数，
        最多数 max_lookback 根。
        """
        count = 0
        for i in range(2, 2 + max_lookback):
            idx = -i
            if abs(idx) > len(close):
                break
            if float(close[idx]) >= float(ma[idx]):
                count += 1
            else:
                break
        return count
