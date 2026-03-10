"""
RSI + 布林带 + SuperTrend 多周期共振高频策略
=============================================

结合 RSI Primed、布林带（BB）和超级趋势（SuperTrend）的多周期共振高频策略。
5分钟（大周期方向）+ 1分钟（执行周期）

策略核心思想：
- 5M SuperTrend 定方向：只在超级趋势看涨时做多，看跌时做空
- 1M 布林带 + RSI(7) 找入场时机

多头入场条件：
    ① 5M SuperTrend 看涨（绿色）
    ② 1M 价格触碰中轨或跌破布林带下轨
    ③ 1M RSI(7) 曾低于30（超卖），且当前 RSI 向上勾头或穿过35

空头入场条件：
    ① 5M SuperTrend 看跌（红色）
    ② 1M 价格触碰中轨或突破布林带上轨
    ③ 1M RSI(7) 曾高于70（超买），且当前 RSI 向下勾头或跌破65

风控逻辑：
    - 止盈：60%
    - 止损：进场挂浮亏100%对锁单，触发对冲
    - 盈利3单平掉一个对冲单子
    - 平仓订单数量大于8单，平掉一个对冲单子
    - 一个币种套住切换做第二个币种
"""

from typing import Any, ClassVar

import numpy as np
import structlog

from quant_trading_system.core.enums import KlineInterval, SignalType
from quant_trading_system.indicators.base import IndicatorRegistry
from quant_trading_system.models.market import Bar
from quant_trading_system.strategy.base import Strategy, register_strategy
from quant_trading_system.strategy.strategy_signal import StrategySignal

logger = structlog.get_logger(__name__)


@register_strategy
class RSIBBSuperTrendStrategy(Strategy):
    """
    RSI + 布林带 + SuperTrend 多周期共振高频策略

    5分钟 SuperTrend 定方向，1分钟 RSI + BB 捕捉极短线进场。
    配合对冲止损与分批止盈的风控体系。
    """

    id: ClassVar[int] = 152410378779754501
    name: ClassVar[str] = "rsi_bb_supertrend"
    description: ClassVar[str] = "RSI+布林带+SuperTrend多周期共振高频策略"
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Quant Team"

    params_def: ClassVar[dict[str, dict[str, Any]]] = {
        # SuperTrend 参数（5M 周期）
        "st_atr_period": {
            "type": int,
            "default": 10,
            "min": 1,
            "max": 100,
            "description": "SuperTrend ATR 周期",
        },
        "st_multiplier": {
            "type": float,
            "default": 3.0,
            "min": 0.5,
            "max": 10.0,
            "description": "SuperTrend ATR 乘数",
        },
        # 布林带参数（1M 周期）
        "bb_period": {
            "type": int,
            "default": 20,
            "min": 5,
            "max": 100,
            "description": "布林带周期",
        },
        "bb_std_dev": {
            "type": float,
            "default": 2.0,
            "min": 0.5,
            "max": 5.0,
            "description": "布林带标准差倍数",
        },
        # RSI 参数（1M 周期）
        "rsi_period": {
            "type": int,
            "default": 7,
            "min": 2,
            "max": 50,
            "description": "RSI 周期",
        },
        "rsi_oversold": {
            "type": float,
            "default": 30.0,
            "min": 5.0,
            "max": 50.0,
            "description": "RSI 超卖阈值",
        },
        "rsi_oversold_exit": {
            "type": float,
            "default": 35.0,
            "min": 10.0,
            "max": 60.0,
            "description": "RSI 超卖回升确认阈值",
        },
        "rsi_overbought": {
            "type": float,
            "default": 70.0,
            "min": 50.0,
            "max": 95.0,
            "description": "RSI 超买阈值",
        },
        "rsi_overbought_exit": {
            "type": float,
            "default": 65.0,
            "min": 40.0,
            "max": 90.0,
            "description": "RSI 超买回落确认阈值",
        },
        # 止盈参数
        "take_profit_pct": {
            "type": float,
            "default": 0.6,
            "min": 0.01,
            "max": 5.0,
            "description": "止盈百分比（如0.6表示60%）",
        },
        # 对冲风控参数
        "hedge_loss_pct": {
            "type": float,
            "default": 1.0,
            "min": 0.1,
            "max": 5.0,
            "description": "触发对冲的浮亏百分比（如1.0表示100%）",
        },
        "profit_orders_to_close_hedge": {
            "type": int,
            "default": 3,
            "min": 1,
            "max": 20,
            "description": "盈利几单后平掉一个对冲单",
        },
        "max_close_orders_to_close_hedge": {
            "type": int,
            "default": 8,
            "min": 1,
            "max": 50,
            "description": "平仓订单数量达到此值时，平掉一个对冲单",
        },
        # BB 中轨容差
        "bb_middle_tolerance": {
            "type": float,
            "default": 0.001,
            "min": 0.0001,
            "max": 0.01,
            "description": "价格触碰布林带中轨的容差比例",
        },
    }

    # 默认交易品种（支持多币种切换）
    symbols: ClassVar[tuple[str, ...]] = ("BTC/USDT", "ETH/USDT")
    # 订阅周期：1分钟（执行）+ 5分钟（趋势）
    timeframes: ClassVar[tuple[KlineInterval, ...]] = (
        KlineInterval.MIN_1,
        KlineInterval.MIN_5,
    )

    def __init__(self, **params: Any) -> None:
        super().__init__(**params)
        # 周期定义
        self._entry_tf: KlineInterval = KlineInterval.MIN_1   # 执行周期
        self._trend_tf: KlineInterval = KlineInterval.MIN_5   # 趋势周期

        # ===== 内部状态跟踪 =====
        # RSI 状态：记录每个品种是否曾经进入超卖/超买区域
        # {symbol: bool}
        self._rsi_was_oversold: dict[str, bool] = {}
        self._rsi_was_overbought: dict[str, bool] = {}

        # 对冲管理状态
        # {symbol: 当前对冲单数量}
        self._hedge_count: dict[str, int] = {}
        # {symbol: 盈利平仓计数（用于判断是否该平对冲单）}
        self._profit_close_count: dict[str, int] = {}
        # {symbol: 总平仓订单计数}
        self._total_close_count: dict[str, int] = {}
        # {symbol: 是否被"套住"（需要切换到下一个币种）}
        self._symbol_locked: dict[str, bool] = {}

        # 当前活跃交易的品种索引
        self._active_symbol_index: int = 0

        # ===== 指标实例缓存（避免每根K线重复创建） =====
        self._st_indicator: Any = None
        self._bb_indicator: Any = None
        self._rsi_indicator: Any = None

        # 指标计算窗口大小（只取最近 N 根K线计算，避免 O(n²) 复杂度）
        # SuperTrend 需要 ATR 预热 + 足够的趋势判断缓冲
        self._st_calc_window: int = 200
        # 布林带需要 bb_period 预热 + 缓冲
        self._bb_calc_window: int = 100
        # RSI 需要 rsi_period 预热 + 缓冲
        self._rsi_calc_window: int = 50

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """策略初始化"""
        for sym in self.symbols:
            self._rsi_was_oversold[sym] = False
            self._rsi_was_overbought[sym] = False
            self._hedge_count[sym] = 0
            self._profit_close_count[sym] = 0
            self._total_close_count[sym] = 0
            self._symbol_locked[sym] = False

        # 预创建指标实例（线程安全、避免热路径上反复查找注册表）
        st_atr_period = self.params["st_atr_period"]
        st_multiplier = self.params["st_multiplier"]
        bb_period = self.params["bb_period"]
        bb_std_dev = self.params["bb_std_dev"]
        rsi_period = self.params["rsi_period"]

        self._st_indicator = IndicatorRegistry.create(
            "SUPERTREND", atr_period=st_atr_period, multiplier=st_multiplier
        )
        self._bb_indicator = IndicatorRegistry.create(
            "BOLL", period=bb_period, std_dev=bb_std_dev
        )
        self._rsi_indicator = IndicatorRegistry.create(
            "RSI", period=rsi_period
        )

        # 动态计算窗口大小
        self._st_calc_window = max(200, st_atr_period * 10)
        self._bb_calc_window = max(100, bb_period * 3)
        self._rsi_calc_window = max(50, rsi_period * 5)

        logger.info(
            "RSIBBSuperTrend strategy initialized",
            entry_tf=self._entry_tf.value,
            trend_tf=self._trend_tf.value,
            symbols=list(self.symbols),
            params=self.params,
            st_calc_window=self._st_calc_window,
            bb_calc_window=self._bb_calc_window,
            rsi_calc_window=self._rsi_calc_window,
        )

    # ------------------------------------------------------------------
    # 核心回调：on_bar
    # ------------------------------------------------------------------

    def on_bar(self, bar: Bar) -> StrategySignal | list[StrategySignal] | None:
        """
        K线数据回调

        仅在1分钟K线到达时执行完整判断逻辑。
        5分钟K线数据由引擎自动更新到 context.bars 中。
        """
        # 仅在执行周期（1M）K线到达时判断
        if bar.timeframe != self._entry_tf:
            return None

        symbol = bar.symbol

        # 如果当前品种被套住，跳过
        if self._symbol_locked.get(symbol, False):
            return None

        # 判断是否为当前活跃品种
        if len(self.symbols) > 1:
            active_symbol = self.symbols[self._active_symbol_index]
            if symbol != active_symbol:
                return None

        # ---------- 获取多周期 K 线数据 ----------
        entry_bars = self.context.get_bars(symbol, self._entry_tf)
        trend_bars = self.context.get_bars(symbol, self._trend_tf)

        if entry_bars is None or trend_bars is None:
            return None

        # 数据量检查
        bb_period = self.params["bb_period"]
        rsi_period = self.params["rsi_period"]
        st_atr_period = self.params["st_atr_period"]

        min_entry_len = max(bb_period, rsi_period) + 5
        if len(entry_bars) < min_entry_len:
            return None
        if len(trend_bars) < st_atr_period + 2:
            return None

        # ---------- 计算 5M SuperTrend（只取最近 N 根，O(1) 切片） ----------
        n_trend = len(trend_bars)
        w_st = min(self._st_calc_window, n_trend)
        try:
            st_result = self._st_indicator.calculate(
                close=trend_bars.close[-w_st:],
                high=trend_bars.high[-w_st:],
                low=trend_bars.low[-w_st:],
            )
        except (RuntimeError, ValueError):
            return None

        st_direction = st_result["direction"]
        if len(st_direction) == 0 or np.isnan(st_direction[-1]):
            return None

        trend_direction = float(st_direction[-1])  # 1.0=看涨, -1.0=看跌

        # ---------- 计算 1M 布林带（只取最近 N 根） ----------
        n_entry = len(entry_bars)
        w_bb = min(self._bb_calc_window, n_entry)
        try:
            bb_result = self._bb_indicator.calculate(
                close=entry_bars.close[-w_bb:],
            )
        except (RuntimeError, ValueError):
            return None

        bb_upper = bb_result["upper"]
        bb_middle = bb_result["middle"]
        bb_lower = bb_result["lower"]

        if np.isnan(bb_upper[-1]) or np.isnan(bb_middle[-1]) or np.isnan(bb_lower[-1]):
            return None

        # ---------- 计算 1M RSI（只取最近 N 根） ----------
        w_rsi = min(self._rsi_calc_window, n_entry)
        try:
            rsi_result = self._rsi_indicator.calculate(
                close=entry_bars.close[-w_rsi:],
            )
        except (RuntimeError, ValueError):
            return None

        rsi_values = rsi_result["rsi"]
        if len(rsi_values) < 2 or np.isnan(rsi_values[-1]) or np.isnan(rsi_values[-2]):
            return None

        rsi_current = float(rsi_values[-1])
        rsi_prev = float(rsi_values[-2])
        close_current = float(entry_bars.close[-1])

        # ---------- 更新 RSI 超卖/超买状态记录 ----------
        self._update_rsi_state(symbol, rsi_current)

        # ---------- 已有持仓时的风控处理 ----------
        position = self.get_position(symbol)
        signals = self._check_risk_management(symbol, position, close_current)

        # ---------- 开仓判断（无持仓或持仓为0时） ----------
        if position is None or position.quantity == 0:
            entry_signal = self._check_entry(
                symbol=symbol,
                bar=bar,
                trend_direction=trend_direction,
                close_current=close_current,
                rsi_current=rsi_current,
                rsi_prev=rsi_prev,
                bb_upper=float(bb_upper[-1]),
                bb_middle=float(bb_middle[-1]),
                bb_lower=float(bb_lower[-1]),
            )
            if entry_signal is not None:
                if signals:
                    signals.append(entry_signal)
                else:
                    signals = [entry_signal]

        if signals:
            return signals if len(signals) > 1 else signals[0]
        return None

    # ------------------------------------------------------------------
    # RSI 状态追踪
    # ------------------------------------------------------------------

    def _update_rsi_state(self, symbol: str, rsi_current: float) -> None:
        """
        更新 RSI 超卖/超买状态。
        当 RSI 进入超卖区（<30）时标记 oversold=True；
        当 RSI 进入超买区（>70）时标记 overbought=True。
        当信号触发后在入场方法中重置。
        """
        oversold_threshold = self.params["rsi_oversold"]
        overbought_threshold = self.params["rsi_overbought"]

        if rsi_current < oversold_threshold:
            self._rsi_was_oversold[symbol] = True
        if rsi_current > overbought_threshold:
            self._rsi_was_overbought[symbol] = True

    # ------------------------------------------------------------------
    # 开仓判断
    # ------------------------------------------------------------------

    def _check_entry(
        self,
        symbol: str,
        bar: Bar,
        trend_direction: float,
        close_current: float,
        rsi_current: float,
        rsi_prev: float,
        bb_upper: float,
        bb_middle: float,
        bb_lower: float,
    ) -> StrategySignal | None:
        """
        综合判断是否满足开仓条件。

        多头条件：
            ① 5M SuperTrend 看涨 (direction == 1)
            ② 1M 价格触碰中轨或跌破下轨
            ③ 1M RSI(7) 曾低于30，且当前向上勾头或穿过35

        空头条件：
            ① 5M SuperTrend 看跌 (direction == -1)
            ② 1M 价格触碰中轨或突破上轨
            ③ 1M RSI(7) 曾高于70，且当前向下勾头或跌破65
        """
        tolerance = self.params["bb_middle_tolerance"]

        # ============ 多头判断 ============
        if trend_direction == 1.0:
            # 条件②：价格触碰中轨或跌破下轨
            touch_middle = abs(close_current - bb_middle) / bb_middle <= tolerance
            below_lower = close_current <= bb_lower
            bb_condition_long = touch_middle or below_lower

            if not bb_condition_long:
                return None

            # 条件③：RSI 曾低于30，且当前向上勾头或穿过35
            rsi_exit_threshold = self.params["rsi_oversold_exit"]
            rsi_turning_up = rsi_current > rsi_prev  # 向上勾头
            rsi_cross_up = rsi_current >= rsi_exit_threshold  # 穿过35

            if not self._rsi_was_oversold.get(symbol, False):
                return None
            if not (rsi_turning_up or rsi_cross_up):
                return None

            # ---- 满足多头入场条件 ----
            entry_price = close_current
            take_profit = entry_price * (1 + self.params["take_profit_pct"])
            # 对锁止损：不设传统止损，而是在浮亏达到100%时触发对冲
            # 这里用 stop_loss 字段记录对冲触发价
            hedge_trigger_price = entry_price * (1 - self.params["hedge_loss_pct"])

            # 重置超卖状态
            self._rsi_was_oversold[symbol] = False

            bb_desc = "触碰中轨" if touch_middle else "跌破下轨"
            return self.open_long(
                symbol=symbol,
                price=entry_price,
                stop_loss=hedge_trigger_price,
                take_profit=take_profit,
                reason=(
                    f"RSI_BB_ST Long | "
                    f"5M SuperTrend=看涨 | "
                    f"1M BB {bb_desc} close={close_current:.4f} "
                    f"mid={bb_middle:.4f} lower={bb_lower:.4f} | "
                    f"RSI={rsi_current:.2f} prev={rsi_prev:.2f} "
                    f"(曾超卖) | tp={take_profit:.4f} hedge@{hedge_trigger_price:.4f}"
                ),
            )

        # ============ 空头判断 ============
        elif trend_direction == -1.0:
            # 条件②：价格触碰中轨或突破上轨
            touch_middle = abs(close_current - bb_middle) / bb_middle <= tolerance
            above_upper = close_current >= bb_upper
            bb_condition_short = touch_middle or above_upper

            if not bb_condition_short:
                return None

            # 条件③：RSI 曾高于70，且当前向下勾头或跌破65
            rsi_exit_threshold = self.params["rsi_overbought_exit"]
            rsi_turning_down = rsi_current < rsi_prev  # 向下勾头
            rsi_cross_down = rsi_current <= rsi_exit_threshold  # 跌破65

            if not self._rsi_was_overbought.get(symbol, False):
                return None
            if not (rsi_turning_down or rsi_cross_down):
                return None

            # ---- 满足空头入场条件 ----
            entry_price = close_current
            take_profit = entry_price * (1 - self.params["take_profit_pct"])
            # 对冲触发价
            hedge_trigger_price = entry_price * (1 + self.params["hedge_loss_pct"])

            # 重置超买状态
            self._rsi_was_overbought[symbol] = False

            bb_desc = "触碰中轨" if touch_middle else "突破上轨"
            return self.open_short(
                symbol=symbol,
                price=entry_price,
                stop_loss=hedge_trigger_price,
                take_profit=take_profit,
                reason=(
                    f"RSI_BB_ST Short | "
                    f"5M SuperTrend=看跌 | "
                    f"1M BB {bb_desc} close={close_current:.4f} "
                    f"mid={bb_middle:.4f} upper={bb_upper:.4f} | "
                    f"RSI={rsi_current:.2f} prev={rsi_prev:.2f} "
                    f"(曾超买) | tp={take_profit:.4f} hedge@{hedge_trigger_price:.4f}"
                ),
            )

        return None

    # ------------------------------------------------------------------
    # 风控管理
    # ------------------------------------------------------------------

    def _check_risk_management(
        self,
        symbol: str,
        position: Any,
        close_current: float,
    ) -> list[StrategySignal] | None:
        """
        风控检查：
        1. 止盈：浮盈达到 take_profit_pct 时平仓
        2. 对冲：浮亏达到 hedge_loss_pct 时挂对锁单（反向开仓对冲）
        3. 盈利 profit_orders_to_close_hedge 单后平掉一个对冲单
        4. 总平仓订单 >= max_close_orders_to_close_hedge 时平掉一个对冲单
        5. 币种套住时切换品种
        """
        if position is None or position.quantity == 0:
            return None

        signals: list[StrategySignal] = []
        entry_price = position.avg_price if hasattr(position, 'avg_price') else 0.0
        qty = position.quantity

        if entry_price <= 0:
            return None

        # 判断持仓方向
        is_long = qty > 0

        # 计算浮盈/浮亏百分比
        if is_long:
            pnl_pct = (close_current - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - close_current) / entry_price

        take_profit_pct = self.params["take_profit_pct"]
        hedge_loss_pct = self.params["hedge_loss_pct"]

        # ---- 1. 止盈判断 ----
        if pnl_pct >= take_profit_pct:
            if is_long:
                signal = self.close_long(
                    symbol=symbol,
                    price=close_current,
                    quantity=abs(qty),
                    reason=f"止盈平多 | pnl={pnl_pct:.2%} >= {take_profit_pct:.0%}",
                )
            else:
                signal = self.close_short(
                    symbol=symbol,
                    price=close_current,
                    quantity=abs(qty),
                    reason=f"止盈平空 | pnl={pnl_pct:.2%} >= {take_profit_pct:.0%}",
                )
            signals.append(signal)

            # 更新盈利平仓计数
            self._profit_close_count[symbol] = self._profit_close_count.get(symbol, 0) + 1
            self._total_close_count[symbol] = self._total_close_count.get(symbol, 0) + 1

            # 检查是否需要平对冲单
            hedge_signals = self._check_close_hedge(symbol, close_current, is_long)
            if hedge_signals:
                signals.extend(hedge_signals)

            return signals

        # ---- 2. 对冲判断：浮亏达到阈值时反向开仓对锁 ----
        if pnl_pct <= -hedge_loss_pct:
            if is_long:
                # 多头浮亏，开空对冲
                hedge_signal = self.open_short(
                    symbol=symbol,
                    price=close_current,
                    quantity=abs(qty),
                    reason=f"对冲开空 | 多头浮亏={pnl_pct:.2%} 触发对锁",
                )
            else:
                # 空头浮亏，开多对冲
                hedge_signal = self.open_long(
                    symbol=symbol,
                    price=close_current,
                    quantity=abs(qty),
                    reason=f"对冲开多 | 空头浮亏={pnl_pct:.2%} 触发对锁",
                )
            signals.append(hedge_signal)
            self._hedge_count[symbol] = self._hedge_count.get(symbol, 0) + 1

            # 标记币种被套住，切换到下一个品种
            self._symbol_locked[symbol] = True
            self._switch_to_next_symbol(symbol)

            logger.info(
                "对冲触发，币种被锁定",
                symbol=symbol,
                hedge_count=self._hedge_count[symbol],
                pnl_pct=f"{pnl_pct:.2%}",
            )
            return signals

        return None

    def _check_close_hedge(
        self,
        symbol: str,
        close_current: float,
        is_long: bool,
    ) -> list[StrategySignal] | None:
        """
        检查是否需要平掉一个对冲单。

        条件：
        1. 盈利满 profit_orders_to_close_hedge 单
        2. 总平仓订单 >= max_close_orders_to_close_hedge
        """
        hedge_count = self._hedge_count.get(symbol, 0)
        if hedge_count <= 0:
            return None

        profit_count = self._profit_close_count.get(symbol, 0)
        total_close = self._total_close_count.get(symbol, 0)

        need_close_hedge = False

        # 条件1：盈利 N 单平一个对冲
        target_profit = self.params["profit_orders_to_close_hedge"]
        if profit_count >= target_profit:
            need_close_hedge = True
            self._profit_close_count[symbol] = profit_count - target_profit

        # 条件2：总平仓订单达标
        target_total = self.params["max_close_orders_to_close_hedge"]
        if total_close >= target_total:
            need_close_hedge = True
            self._total_close_count[symbol] = total_close - target_total

        if not need_close_hedge:
            return None

        # 平掉一个对冲单（对冲单方向与原始持仓相反）
        self._hedge_count[symbol] = hedge_count - 1

        if is_long:
            # 原始持仓是多头，对冲单是空头，平空
            signal = self.close_short(
                symbol=symbol,
                price=close_current,
                reason=f"平对冲空单 | 盈利计数={profit_count} 总平仓={total_close} 剩余对冲={hedge_count - 1}",
            )
        else:
            # 原始持仓是空头，对冲单是多头，平多
            signal = self.close_long(
                symbol=symbol,
                price=close_current,
                reason=f"平对冲多单 | 盈利计数={profit_count} 总平仓={total_close} 剩余对冲={hedge_count - 1}",
            )

        # 如果对冲单全部平完，解锁币种
        if self._hedge_count[symbol] <= 0:
            self._symbol_locked[symbol] = False
            logger.info("对冲单全部平完，币种解锁", symbol=symbol)

        return [signal]

    # ------------------------------------------------------------------
    # 币种切换
    # ------------------------------------------------------------------

    def _switch_to_next_symbol(self, locked_symbol: str) -> None:
        """
        当前币种被套住时，切换到下一个可用的币种。
        如果所有币种都被锁定，则不切换（等待解锁）。
        """
        if len(self.symbols) <= 1:
            return

        for i in range(len(self.symbols)):
            next_index = (self._active_symbol_index + 1 + i) % len(self.symbols)
            next_symbol = self.symbols[next_index]
            if not self._symbol_locked.get(next_symbol, False):
                self._active_symbol_index = next_index
                logger.info(
                    "切换活跃交易品种",
                    from_symbol=locked_symbol,
                    to_symbol=next_symbol,
                )
                return

        logger.warning("所有币种均被锁定，等待解锁", symbols=list(self.symbols))

    # ------------------------------------------------------------------
    # 交易事件回调
    # ------------------------------------------------------------------

    def on_trade(self, trade: Any) -> None:
        """成交回调，用于更新内部计数"""
        super().on_trade(trade)

    def on_position(self, position: Any) -> None:
        """持仓更新回调"""
        pass
