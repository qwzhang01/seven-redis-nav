"""
回测引擎
========

事件驱动的回测引擎，职责精简为：
- 历史数据回放
- 驱动策略产生信号
- 委托 OrderProcessor 处理订单/仓位/账户
- 委托 StrategyEvaluator 计算绩效
- 收集权益曲线并计算回测结果
"""

import time
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, BarArray, BarArrayView
from quant_trading_system.core.enums import KlineInterval, StrategyState
from quant_trading_system.strategy import Strategy, StrategyContext
from quant_trading_system.strategy import StrategySignal
from quant_trading_system.indicators.indicator_engine import (
    get_indicator_engine,
)
from quant_trading_system.services.order.order_executor import (
    BacktestExecutor,
    ExecutionConfig,
)
from quant_trading_system.services.order.position_manager import PositionManager
from quant_trading_system.services.order.account_manager import AccountManager
from quant_trading_system.services.order.order_processor import (
    OrderProcessor,
    OrderProcessorConfig,
)
from quant_trading_system.services.evaluation.strategy_evaluator import StrategyEvaluator
from quant_trading_system.services.risk.risk_manager import RiskManager, RiskConfig

logger = structlog.get_logger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""

    # 初始资金
    initial_capital: float = 1000000.0

    # 手续费率
    commission_rate: float = 0.0004
    min_commission: float = 0.0

    # 滑点配置
    slippage_rate: float = 0.0001  # 滑点比例
    slippage_fixed: float = 0.0    # 固定滑点

    # 资金管理
    position_sizing: str = "fixed"  # fixed, percent, kelly
    fixed_quantity: float = 1.0
    percent_risk: float = 0.02

    # 时间范围
    start_time: float = 0.0
    end_time: float = 0.0

    # 其他
    margin_rate: float = 1.0  # 保证金率（1.0 = 全额）

    # 风控配置（可选）
    risk_config: RiskConfig | None = None


@dataclass
class BacktestResult:
    """回测结果"""

    # 基本信息
    strategy_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_days: float = 0.0

    # 收益指标
    initial_capital: float = 0.0
    final_capital: float = 0.0
    total_return: float = 0.0
    annual_return: float = 0.0

    # 风险指标
    max_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0

    # 费用统计
    total_commission: float = 0.0
    total_slippage: float = 0.0

    # 详细数据
    equity_curve: list[float] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_days": self.duration_days,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration": self.max_drawdown_duration,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "avg_trade": self.avg_trade,
            "max_win": self.max_win,
            "max_loss": self.max_loss,
            "total_commission": self.total_commission,
            "total_slippage": self.total_slippage,
        }


class BacktestEngine:
    """
    回测引擎

    职责：
    - 历史数据回放，驱动策略产生信号
    - 委托 OrderProcessor 处理信号→订单→仓位→账户的完整流程
    - 委托 StrategyEvaluator 增量计算策略绩效
    - 驱动 RiskManager 进行回测风控
    - 收集权益曲线并生成回测结果
    """

    def __init__(
        self,
        config: BacktestConfig | None = None,
        use_database: bool = False,
    ) -> None:
        self.config = config or BacktestConfig()
        self.use_database = use_database

        # 指标引擎
        self._indicator_engine = get_indicator_engine()

        # 数据查询服务（如果使用数据库）
        self._data_query_service = None
        if use_database:
            from quant_trading_system.services.market.market_data_reader import get_market_data_reader
            self._data_query_service = get_market_data_reader()

        # ---- 核心模块（统一订单管理） ----
        self._position_manager = PositionManager()
        self._account_manager = AccountManager()

        executor = BacktestExecutor(config=ExecutionConfig(
            commission_rate=self.config.commission_rate,
            min_commission=self.config.min_commission,
            slippage_rate=self.config.slippage_rate,
            slippage_fixed=self.config.slippage_fixed,
        ))

        # 风控管理器（回测模式，无事件引擎）
        self._risk_manager = RiskManager(
            config=self.config.risk_config,
        ) if self.config.risk_config else None

        self._order_processor = OrderProcessor(
            executor=executor,
            position_manager=self._position_manager,
            account_manager=self._account_manager,
            risk_manager=self._risk_manager,
            config=OrderProcessorConfig(
                position_sizing=self.config.position_sizing,
                fixed_quantity=self.config.fixed_quantity,
                percent_risk=self.config.percent_risk,
            ),
        )

        # 策略评价器（回测模式，同步调用）
        self._evaluator = StrategyEvaluator(
            initial_equity=self.config.initial_capital,
        )

        # 权益曲线
        self._equity_curve: list[tuple[float, float]] = []  # [(timestamp, equity)]

        # K线数据
        self._bar_data: dict[str, dict[KlineInterval, BarArray]] = {}

        # 当前时间
        self._current_time: float = 0.0

    def run(
        self,
        strategy: Strategy,
        bars: dict[str, BarArray] | BarArray | dict[str, dict[KlineInterval, BarArray]],
    ) -> BacktestResult:
        """
        运行回测

        Args:
            strategy: 策略实例
            bars: K线数据，支持以下格式:
                - BarArray: 单品种单周期
                - {symbol: BarArray}: 多品种单周期
                - {symbol: {timeframe: BarArray}}: 多品种多周期

        Returns:
            回测结果
        """
        logger.info(f"Starting backtest", strategy=strategy.name)
        start_time = time.time()

        # 标准化为 {symbol: {timeframe: BarArray}} 格式
        multi_tf_bars = self._normalize_bars(bars)

        # 初始化
        self._initialize(strategy, multi_tf_bars)

        # 运行回测
        self._run_backtest(strategy, multi_tf_bars)

        # 计算结果
        result = self._calculate_result(strategy)

        elapsed = time.time() - start_time
        logger.info(f"Backtest completed",
                   strategy=strategy.name,
                   duration=elapsed,
                   trades=result.total_trades,
                   return_pct=f"{result.total_return:.2%}")

        return result

    async def run_from_database(
        self,
        strategy: Strategy,
        symbols: list[str],
        timeframes: list[KlineInterval],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> BacktestResult:
        """
        从TimescaleDB获取数据并运行回测

        Args:
            strategy: 策略实例
            symbols: 交易对列表
            timeframes: 时间框架列表
            start_time: 开始时间
            end_time: 结束时间
            limit: 最大数据条数

        Returns:
            回测结果
        """
        if not self.use_database or not self._data_query_service:
            raise ValueError("Database mode is not enabled or data query service is not available")

        logger.info("Starting backtest from database",
                   strategy=strategy.name,
                   symbols=symbols,
                   timeframes=[tf.value for tf in timeframes],
                   start_time=start_time,
                   end_time=end_time)

        # 从数据库获取数据
        bars = await self._data_query_service.get_multiple_kline_data(
            symbols=symbols,
            timeframes=timeframes,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        # 转换为回测引擎需要的格式
        normalized_bars = {}
        for symbol, tf_data in bars.items():
            normalized_bars[symbol] = {}
            for timeframe, bar_array in tf_data.items():
                if len(bar_array.timestamp) > 0:  # 确保有数据
                    normalized_bars[symbol][timeframe] = bar_array

        return self.run(strategy, normalized_bars)

    @staticmethod
    def _normalize_bars(
        bars: dict[str, BarArray] | BarArray | dict[str, dict[KlineInterval, BarArray]],
    ) -> dict[str, dict[KlineInterval, BarArray]]:
        """将各种输入格式统一为 {symbol: {timeframe: BarArray}}"""
        if isinstance(bars, BarArray):
            return {bars.symbol: {bars.timeframe: bars}}

        # 检查第一个 value 的类型来判断嵌套层级
        first_val = next(iter(bars.values()))
        if isinstance(first_val, BarArray):
            # {symbol: BarArray} 格式
            return {sym: {ba.timeframe: ba} for sym, ba in bars.items()}
        elif isinstance(first_val, dict):
            # 已经是 {symbol: {timeframe: BarArray}} 格式
            return bars  # type: ignore

        raise ValueError(f"Unsupported bars format: {type(first_val)}")

    def _initialize(
        self,
        strategy: Strategy,
        bars: dict[str, dict[KlineInterval, BarArray]]
    ) -> None:
        """初始化回测环境"""
        # 重置 OrderProcessor 和评价器
        self._order_processor.reset()
        self._evaluator.reset()
        self._equity_curve.clear()

        # 创建账户
        account = self._account_manager.create_account(
            initial_capital=self.config.initial_capital,
            account_id="backtest",
        )

        # 初始化风控
        if self._risk_manager:
            self._risk_manager.set_account(account)
            self._risk_manager.set_positions(self._position_manager.positions)

        # 初始化评价器
        self._evaluator.set_initial_equity(self.config.initial_capital)

        # 存储K线数据（多周期）
        self._bar_data.clear()
        all_timeframes: list[KlineInterval] = []
        for symbol, tf_bars in bars.items():
            self._bar_data[symbol] = {}
            for tf, bar_array in tf_bars.items():
                self._bar_data[symbol][tf] = bar_array
                if tf not in all_timeframes:
                    all_timeframes.append(tf)

        # 创建策略上下文（使用 PositionManager 的持仓引用）
        context = StrategyContext(
            strategy_id=strategy.strategy_id,
            symbols=list(bars.keys()),
            timeframes=all_timeframes,
            indicator_engine=self._indicator_engine,
            account=account,
            positions=self._position_manager.positions,
            bars=self._bar_data,
            is_backtest=True,
        )
        strategy.set_context(context)

        # 初始化策略
        strategy.state = StrategyState.INITIALIZING
        strategy.on_init()
        strategy.state = StrategyState.RUNNING
        strategy.on_start()

    def _run_backtest(
        self,
        strategy: Strategy,
        bars: dict[str, dict[KlineInterval, BarArray]]
    ) -> None:
        """执行回测（支持多周期）—— 使用 BarArrayView 零拷贝优化"""
        # 确定主时间轴：取最小周期作为驱动周期
        main_symbol = list(bars.keys())[0]
        tf_bars = bars[main_symbol]

        # 按周期秒数排序，最小的作为主驱动
        tf_seconds = {
            KlineInterval.MIN_1: 60, KlineInterval.MIN_5: 300, KlineInterval.MIN_15: 900,
            KlineInterval.MIN_30: 1800, KlineInterval.HOUR_1: 3600, KlineInterval.HOUR_4: 14400,
            KlineInterval.DAY_1: 86400, KlineInterval.WEEK_1: 604800,
        }
        sorted_tfs = sorted(tf_bars.keys(), key=lambda t: tf_seconds.get(t, 0))
        main_tf = sorted_tfs[0]
        main_bars = tf_bars[main_tf]

        # 预热期（确保有足够的数据计算指标）
        warmup_period = 100

        # --- 预处理阶段：构建视图和缓存时间戳 ---
        # 1) 确保所有 BarArray 的 numpy 缓存已构建
        for symbol, symbol_tf_bars in bars.items():
            for tf, bar_array in symbol_tf_bars.items():
                bar_array.ensure_numpy_cache()

        # 2) 为每个 (symbol, tf) 创建 BarArrayView，直接写入 strategy.context.bars
        #    注意：Pydantic 在初始化时深拷贝了 dict，所以必须直接操作 context.bars
        views: dict[str, dict[KlineInterval, BarArrayView]] = {}
        ctx_bars = strategy.context.bars  # 获取 context 持有的（已拷贝的）字典引用
        for symbol, symbol_tf_bars in bars.items():
            views[symbol] = {}
            if symbol not in ctx_bars:
                ctx_bars[symbol] = {}
            for tf, bar_array in symbol_tf_bars.items():
                view = BarArrayView(bar_array)
                views[symbol][tf] = view
                ctx_bars[symbol][tf] = view  # 直接写入 context.bars

        # 3) 预计算主周期时间戳毫秒数组（避免逐根转换）
        main_ts_ms = main_bars.get_timestamp_ms()

        # 4) 预计算高周期时间戳毫秒数组并缓存
        higher_tf_ts_ms: dict[str, dict[KlineInterval, np.ndarray]] = {}
        for symbol, symbol_tf_bars in bars.items():
            higher_tf_ts_ms[symbol] = {}
            for tf, bar_array in symbol_tf_bars.items():
                if tf != main_tf:
                    higher_tf_ts_ms[symbol][tf] = bar_array.get_timestamp_ms()

        # 5) 预取主周期的 numpy 数组引用（避免循环内反复 property 调用）
        main_open_arr = main_bars.open
        main_high_arr = main_bars.high
        main_low_arr = main_bars.low
        main_close_arr = main_bars.close
        main_volume_arr = main_bars.volume

        # --- 回测进度跟踪 ---
        total_bars = len(main_bars) - warmup_period
        backtest_start_time = time.time()
        last_progress_pct = -1
        progress_interval = 10
        trade_count_at_last_log = 0

        logger.info(
            "Backtest loop started",
            strategy=strategy.name,
            symbol=main_symbol,
            timeframe=main_tf.value,
            total_bars=total_bars,
            warmup_period=warmup_period,
            total_data_bars=len(main_bars),
        )

        # 高周期上一次的 end_idx 缓存（利用时间单调递增，使用 searchsorted 增量查找）
        higher_tf_last_end: dict[str, dict[KlineInterval, int]] = {}
        for symbol in higher_tf_ts_ms:
            higher_tf_last_end[symbol] = {}
            for tf in higher_tf_ts_ms[symbol]:
                higher_tf_last_end[symbol][tf] = 0

        # 遍历主周期K线
        for i in range(warmup_period, len(main_bars)):
            # --- 进度日志 ---
            processed = i - warmup_period + 1
            progress_pct = int(processed * 100 / total_bars) if total_bars > 0 else 100

            if progress_pct // progress_interval > last_progress_pct // progress_interval or processed == total_bars:
                elapsed = time.time() - backtest_start_time
                bars_per_sec = processed / elapsed if elapsed > 0 else 0
                eta = (total_bars - processed) / bars_per_sec if bars_per_sec > 0 else 0
                new_trades = len(self._order_processor.trades) - trade_count_at_last_log

                logger.info(
                    "Backtest progress",
                    strategy=strategy.name,
                    progress=f"{progress_pct}%",
                    processed_bars=processed,
                    total_bars=total_bars,
                    elapsed=f"{elapsed:.1f}s",
                    speed=f"{bars_per_sec:.0f} bars/s",
                    eta=f"{eta:.1f}s",
                    trades_so_far=len(self._order_processor.trades),
                    new_trades=new_trades,
                    current_equity=f"{self._equity_curve[-1][1]:,.2f}" if self._equity_curve else "N/A",
                )
                last_progress_pct = progress_pct
                trade_count_at_last_log = len(self._order_processor.trades)

            # 当前主周期时间戳（直接从预计算数组取值，O(1)）
            current_ts_ms = main_ts_ms[i]

            # 更新所有周期的视图范围（O(1) 操作，无数据拷贝）
            for symbol, symbol_views in views.items():
                for tf, view in symbol_views.items():
                    if tf == main_tf:
                        # 主周期：直接设置 end = i + 1
                        view.set_end(i + 1)
                    else:
                        # 高周期：利用时间单调递增，从上次位置开始搜索
                        ts_arr = higher_tf_ts_ms[symbol][tf]
                        if len(ts_arr) > 0:
                            last_end = higher_tf_last_end[symbol][tf]
                            # 从 last_end 开始向右搜索（因为时间单调递增）
                            end_idx = last_end
                            while end_idx < len(ts_arr) and ts_arr[end_idx] <= current_ts_ms:
                                end_idx += 1
                            higher_tf_last_end[symbol][tf] = end_idx
                            view.set_end(end_idx)
                        else:
                            view.set_end(0)

            # 更新当前时间
            self._current_time = current_ts_ms
            strategy.context.current_time = self._current_time

            # 创建当前Bar（主周期）—— 直接从预取的数组引用取值
            bar = Bar(
                symbol=main_symbol,
                exchange=main_bars.exchange,
                timeframe=main_tf,
                timestamp=current_ts_ms,
                open=float(main_open_arr[i]),
                high=float(main_high_arr[i]),
                low=float(main_low_arr[i]),
                close=float(main_close_arr[i]),
                volume=float(main_volume_arr[i]),
                is_closed=True,
            )

            # 更新持仓市场价格（修复多品种同价bug：使用对应品种的价格）
            self._position_manager.update_market_price(bar.symbol, bar.close)

            # 驱动风控的 on_bar（事中风控）
            if self._risk_manager:
                self._risk_manager.on_bar(bar)

            # 调用策略产生信号
            try:
                signals = strategy.on_bar(bar)

                # 通过 OrderProcessor 处理信号
                if signals:
                    if isinstance(signals, StrategySignal):
                        signals = [signals]

                    for signal in signals:
                        result = self._order_processor.process_signal_sync(signal, bar.close)

                        # 通知评价器和风控
                        if result and result.success and result.trade:
                            self._evaluator.on_trade(result.trade)
                            if self._risk_manager:
                                self._risk_manager.on_order_filled(result.trade)

            except Exception as e:
                logger.error(f"Strategy error at bar {i}", error=str(e))

            # 记录权益
            total_position_value = self._position_manager.get_total_position_value()
            equity = self._account_manager.calculate_equity(total_position_value)
            self._equity_curve.append((self._current_time, equity))

            # 通知评价器更新权益曲线
            self._evaluator.on_equity_update(equity, strategy.strategy_id)

        # --- 回测循环结束汇总 ---
        total_elapsed = time.time() - backtest_start_time
        final_equity = self._equity_curve[-1][1] if self._equity_curve else self.config.initial_capital
        total_return = (final_equity - self.config.initial_capital) / self.config.initial_capital
        logger.info(
            "Backtest loop finished",
            strategy=strategy.name,
            total_bars_processed=total_bars,
            total_trades=len(self._order_processor.trades),
            total_elapsed=f"{total_elapsed:.2f}s",
            avg_speed=f"{total_bars / total_elapsed:.0f} bars/s" if total_elapsed > 0 else "N/A",
            final_equity=f"{final_equity:,.2f}",
            total_return=f"{total_return:.2%}",
            total_commission=f"{self._order_processor.total_commission:,.2f}",
        )

        # 停止策略
        strategy.state = StrategyState.STOPPED
        strategy.on_stop()

    def _calculate_result(self, strategy: Strategy) -> BacktestResult:
        """计算回测结果"""
        result = BacktestResult()

        result.strategy_name = strategy.name
        result.initial_capital = self.config.initial_capital

        if not self._equity_curve:
            return result

        # 时间范围
        result.start_time = self._equity_curve[0][0]
        result.end_time = self._equity_curve[-1][0]
        result.duration_days = (result.end_time - result.start_time) / (86400 * 1000)

        # 最终权益
        result.final_capital = self._equity_curve[-1][1]

        # 收益计算
        result.total_return = (
            result.final_capital - result.initial_capital
        ) / result.initial_capital

        # 问题4修复：极短回测期（< 7天）不做年化，避免年化收益爆炸
        min_annualize_days = 7
        if result.duration_days >= min_annualize_days:
            if result.total_return > -1:
                annualized_factor = 365 / result.duration_days
                result.annual_return = float(np.exp(np.log(1 + result.total_return) * annualized_factor) - 1)
            else:
                result.annual_return = -1.0
        elif result.duration_days > 0:
            # 回测期不足 7 天，直接使用总收益率，不做年化
            result.annual_return = result.total_return
        else:
            result.annual_return = 0.0

        # 权益曲线转为numpy数组
        equity_array = np.array([e[1] for e in self._equity_curve])

        # 计算收益率序列
        returns = np.diff(equity_array) / equity_array[:-1]
        result.daily_returns = returns.tolist()
        result.equity_curve = equity_array.tolist()

        # 风险指标
        result.volatility = float(np.std(returns) * np.sqrt(252)) if len(returns) > 0 else 0

        # 最大回撤
        peak = np.maximum.accumulate(equity_array)
        drawdown = (peak - equity_array) / peak
        result.max_drawdown = float(np.max(drawdown))

        # 问题3修复：计算最大回撤持续时间（从峰值到恢复至新峰值的最长周期，单位天）
        max_dd_duration = 0.0
        dd_start_ts = 0.0
        timestamps = np.array([e[0] for e in self._equity_curve])
        for j in range(1, len(equity_array)):
            if equity_array[j] < peak[j]:
                # 处于回撤中
                if dd_start_ts == 0.0:
                    dd_start_ts = timestamps[j - 1]  # 记录回撤开始时间（前一根的峰值时刻）
            else:
                # 已恢复到新峰值
                if dd_start_ts > 0.0:
                    duration = (timestamps[j] - dd_start_ts) / (86400 * 1000)
                    max_dd_duration = max(max_dd_duration, duration)
                    dd_start_ts = 0.0
        # 如果回测结束时仍处于回撤中
        if dd_start_ts > 0.0:
            duration = (timestamps[-1] - dd_start_ts) / (86400 * 1000)
            max_dd_duration = max(max_dd_duration, duration)
        result.max_drawdown_duration = max_dd_duration

        # 夏普比率（假设无风险利率为0）
        if result.volatility > 0:
            result.sharpe_ratio = result.annual_return / result.volatility

        # 问题2修复：计算 Sortino Ratio（只考虑下行风险）
        if len(returns) > 0:
            downside_returns = returns[returns < 0]
            downside_std = float(np.std(downside_returns) * np.sqrt(252)) if len(downside_returns) > 0 else 0.0
            if downside_std > 0:
                result.sortino_ratio = result.annual_return / downside_std

        # Calmar比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annual_return / result.max_drawdown

        # 从评价器获取交易统计
        evaluator_metrics = self._evaluator.get_metrics(strategy.strategy_id)
        if evaluator_metrics:
            result.winning_trades = evaluator_metrics.winning_trades
            result.losing_trades = evaluator_metrics.losing_trades
            result.win_rate = evaluator_metrics.win_rate
            result.profit_factor = evaluator_metrics.profit_factor
            result.avg_win = evaluator_metrics.avg_win
            result.avg_loss = evaluator_metrics.avg_loss
            result.avg_trade = evaluator_metrics.avg_trade_pnl
            result.max_win = evaluator_metrics.max_win
            result.max_loss = evaluator_metrics.max_loss

        # 从 OrderProcessor 获取费用和交易统计
        result.total_trades = len(self._order_processor.trades)
        result.total_commission = self._order_processor.total_commission
        result.total_slippage = self._order_processor.total_slippage

        # 交易记录
        result.trades = [t.to_dict() for t in self._order_processor.trades]

        return result

    @property
    def order_processor(self) -> OrderProcessor:
        """获取订单处理器"""
        return self._order_processor

    @property
    def evaluator(self) -> StrategyEvaluator:
        """获取策略评价器"""
        return self._evaluator

    @property
    def position_manager(self) -> PositionManager:
        """获取仓位管理器"""
        return self._position_manager

    @property
    def account_manager(self) -> AccountManager:
        """获取账户管理器"""
        return self._account_manager
