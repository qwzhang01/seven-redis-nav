"""
回测引擎
========

事件驱动的回测引擎，支持：
- 历史数据回放
- 交易成本模拟
- 滑点模拟
- 资金管理
"""

import time
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, BarArray
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.core.enums import OrderSide, OrderStatus, OrderType, StrategyState
from quant_trading_system.models.trading import (
    Order,
    Position,
    Trade,
)
from quant_trading_system.models.account import Account, AccountType, Balance
from quant_trading_system.services.strategy.base import Strategy, StrategyContext
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.indicator_engine import (
    get_indicator_engine,
)
from quant_trading_system.services.database.data_query import get_data_query_service

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

    提供事件驱动的策略回测能力
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
            self._data_query_service = get_data_query_service()

        # 账户
        self._account: Account | None = None

        # 持仓 {symbol: Position}
        self._positions: dict[str, Position] = {}

        # 订单
        self._orders: list[Order] = []
        self._trades: list[Trade] = []

        # 权益曲线
        self._equity_curve: list[tuple[float, float]] = []  # [(timestamp, equity)]

        # K线数据
        self._bar_data: dict[str, dict[KlineInterval, BarArray]] = {}

        # 当前时间
        self._current_time: float = 0.0

        # 统计
        self._total_commission: float = 0.0
        self._total_slippage: float = 0.0

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
        # 创建账户
        from datetime import datetime

        # 创建初始余额
        usdt_balance = Balance(
            asset="USDT",
            free=self.config.initial_capital,
            locked=0.0,
            total=self.config.initial_capital
        )

        self._account = Account(
            id="backtest",
            type=AccountType.SPOT,
            balances={"USDT": usdt_balance},
            total_balance=self.config.initial_capital,
            available_balance=self.config.initial_capital,
            margin_balance=self.config.initial_capital,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            updated_at=datetime.now()
        )

        # 重置状态
        self._positions.clear()
        self._orders.clear()
        self._trades.clear()
        self._equity_curve.clear()
        self._total_commission = 0.0
        self._total_slippage = 0.0

        # 存储K线数据（多周期）
        self._bar_data.clear()
        all_timeframes: list[KlineInterval] = []
        for symbol, tf_bars in bars.items():
            self._bar_data[symbol] = {}
            for tf, bar_array in tf_bars.items():
                self._bar_data[symbol][tf] = bar_array
                if tf not in all_timeframes:
                    all_timeframes.append(tf)

        # 创建策略上下文
        context = StrategyContext(
            strategy_id=strategy.strategy_id,
            symbols=list(bars.keys()),
            timeframes=all_timeframes,
            indicator_engine=self._indicator_engine,
            account=self._account,
            positions=self._positions,
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
        """执行回测（支持多周期）"""
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

        # --- 回测进度跟踪 ---
        total_bars = len(main_bars) - warmup_period
        backtest_start_time = time.time()
        last_progress_pct = -1  # 上次打印的进度百分比
        progress_interval = 10  # 每 10% 打印一次进度
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

        # 遍历主周期K线
        for i in range(warmup_period, len(main_bars)):
            # --- 进度日志 ---
            processed = i - warmup_period + 1
            progress_pct = int(processed * 100 / total_bars) if total_bars > 0 else 100

            if progress_pct // progress_interval > last_progress_pct // progress_interval or processed == total_bars:
                elapsed = time.time() - backtest_start_time
                bars_per_sec = processed / elapsed if elapsed > 0 else 0
                eta = (total_bars - processed) / bars_per_sec if bars_per_sec > 0 else 0
                new_trades = len(self._trades) - trade_count_at_last_log

                logger.info(
                    "Backtest progress",
                    strategy=strategy.name,
                    progress=f"{progress_pct}%",
                    processed_bars=processed,
                    total_bars=total_bars,
                    elapsed=f"{elapsed:.1f}s",
                    speed=f"{bars_per_sec:.0f} bars/s",
                    eta=f"{eta:.1f}s",
                    trades_so_far=len(self._trades),
                    new_trades=new_trades,
                    current_equity=f"{self._equity_curve[-1][1]:,.2f}" if self._equity_curve else "N/A",
                )
                last_progress_pct = progress_pct
                trade_count_at_last_log = len(self._trades)
            # 当前主周期时间戳
            ts = main_bars.timestamp[i]
            if isinstance(ts, np.datetime64):
                current_ts_ms = float(ts.astype('datetime64[ms]').astype(np.int64))
            else:
                current_ts_ms = ts.timestamp() * 1000 if hasattr(ts, 'timestamp') else float(ts)

            # 更新所有周期的 context.bars 切片（避免未来函数）
            for symbol, symbol_tf_bars in bars.items():
                for tf, bar_array in symbol_tf_bars.items():
                    if tf == main_tf:
                        # 主周期：按索引切片
                        sliced = BarArray(
                            symbol=bar_array.symbol,
                            exchange=bar_array.exchange,
                            timeframe=bar_array.timeframe,
                            timestamp=bar_array.timestamp[:i+1],
                            open=bar_array.open[:i+1],
                            high=bar_array.high[:i+1],
                            low=bar_array.low[:i+1],
                            close=bar_array.close[:i+1],
                            volume=bar_array.volume[:i+1],
                            turnover=bar_array.turnover[:i+1] if bar_array.turnover is not None else None,
                        )
                    else:
                        # 高周期：按时间戳切片，只保留 <= 当前时间的K线
                        higher_ts = bar_array.timestamp
                        if len(higher_ts) > 0:
                            # 将时间戳转换为毫秒进行比较
                            if isinstance(higher_ts[0], np.datetime64):
                                higher_ts_ms = higher_ts.astype('datetime64[ms]').astype(np.int64).astype(float)
                            else:
                                higher_ts_ms = np.array([
                                    t.timestamp() * 1000 if hasattr(t, 'timestamp') else float(t)
                                    for t in higher_ts
                                ])
                            mask = higher_ts_ms <= current_ts_ms
                            end_idx = int(np.sum(mask))
                        else:
                            end_idx = 0

                        if end_idx > 0:
                            sliced = BarArray(
                                symbol=bar_array.symbol,
                                exchange=bar_array.exchange,
                                timeframe=bar_array.timeframe,
                                timestamp=bar_array.timestamp[:end_idx],
                                open=bar_array.open[:end_idx],
                                high=bar_array.high[:end_idx],
                                low=bar_array.low[:end_idx],
                                close=bar_array.close[:end_idx],
                                volume=bar_array.volume[:end_idx],
                                turnover=bar_array.turnover[:end_idx] if bar_array.turnover is not None else None,
                            )
                        else:
                            sliced = BarArray(
                                symbol=bar_array.symbol,
                                exchange=bar_array.exchange,
                                timeframe=bar_array.timeframe,
                            )

                    self._bar_data[symbol][tf] = sliced

            # 更新当前时间
            self._current_time = current_ts_ms
            strategy.context.current_time = self._current_time

            # 创建当前Bar（主周期）
            bar = Bar(
                symbol=main_symbol,
                exchange=main_bars.exchange,
                timeframe=main_tf,
                timestamp=current_ts_ms,
                open=float(main_bars.open[i]),
                high=float(main_bars.high[i]),
                low=float(main_bars.low[i]),
                close=float(main_bars.close[i]),
                volume=float(main_bars.volume[i]),
                is_closed=True,
            )

            # 更新持仓市值
            self._update_positions(bar.close)

            # 调用策略
            try:
                signals = strategy.on_bar(bar)

                # 处理信号
                if signals:
                    if isinstance(signals, Signal):
                        signals = [signals]

                    for signal in signals:
                        self._process_signal(signal, bar)

            except Exception as e:
                logger.error(f"Strategy error at bar {i}", error=str(e))

            # 记录权益
            equity = self._calculate_equity(bar.close)
            self._equity_curve.append((self._current_time, equity))

        # --- 回测循环结束汇总 ---
        total_elapsed = time.time() - backtest_start_time
        final_equity = self._equity_curve[-1][1] if self._equity_curve else self.config.initial_capital
        total_return = (final_equity - self.config.initial_capital) / self.config.initial_capital
        logger.info(
            "Backtest loop finished",
            strategy=strategy.name,
            total_bars_processed=total_bars,
            total_trades=len(self._trades),
            total_elapsed=f"{total_elapsed:.2f}s",
            avg_speed=f"{total_bars / total_elapsed:.0f} bars/s" if total_elapsed > 0 else "N/A",
            final_equity=f"{final_equity:,.2f}",
            total_return=f"{total_return:.2%}",
            total_commission=f"{self._total_commission:,.2f}",
        )

        # 停止策略
        strategy.state = StrategyState.STOPPED
        strategy.on_stop()

    def _process_signal(self, signal: Signal, bar: Bar) -> None:
        """处理交易信号"""
        symbol = signal.symbol
        price = bar.close

        # 计算滑点
        slippage = price * self.config.slippage_rate + self.config.slippage_fixed

        if signal.is_buy:
            exec_price = price + slippage
        else:
            exec_price = price - slippage

        self._total_slippage += abs(slippage)

        # 计算交易数量
        quantity = self._calculate_quantity(signal, exec_price)
        if quantity <= 0:
            return

        # 计算手续费
        commission = max(
            quantity * exec_price * self.config.commission_rate,
            self.config.min_commission
        )
        self._total_commission += commission

        # 创建订单
        import uuid
        from datetime import datetime
        from quant_trading_system.core.snowflake import generate_backtest_snowflake_id

        order = Order(
            id=str(generate_backtest_snowflake_id()),
            symbol=symbol,
            side=OrderSide.BUY if signal.is_buy else OrderSide.SELL,
            type=OrderType.MARKET,
            quantity=quantity,
            price=exec_price,
            status=OrderStatus.FILLED,
            created_at=datetime.fromtimestamp(self._current_time / 1000),
            updated_at=datetime.fromtimestamp(self._current_time / 1000),
        )
        self._orders.append(order)

        # 创建成交记录
        trade = Trade(
            id=str(generate_backtest_snowflake_id()),  # 添加Trade ID
            symbol=symbol,
            exchange="backtest",
            order_id=order.id,
            side=order.side,
            price=exec_price,
            quantity=quantity,
            amount=quantity * exec_price,
            commission=commission,
            timestamp=datetime.fromtimestamp(self._current_time / 1000),  # 修正timestamp格式
            strategy_id=signal.strategy_id,
        )
        self._trades.append(trade)

        logger.debug(
            "Backtest trade executed",
            trade_no=len(self._trades),
            side=order.side.value,
            symbol=symbol,
            price=f"{exec_price:.4f}",
            quantity=f"{quantity:.6f}",
            amount=f"{quantity * exec_price:,.2f}",
            commission=f"{commission:.4f}",
            signal_type=signal.signal_type.value if hasattr(signal, 'signal_type') else "N/A",
        )

        # 更新持仓
        self._update_position_from_trade(trade)

        # 更新账户
        self._update_account_from_trade(trade)

    def _calculate_quantity(self, signal: Signal, price: float) -> float:
        """计算交易数量"""
        if signal.quantity > 0:
            return signal.quantity

        if self.config.position_sizing == "fixed":
            return self.config.fixed_quantity

        elif self.config.position_sizing == "percent":
            # 按风险百分比计算
            equity = self._calculate_equity(price)
            risk_amount = equity * self.config.percent_risk
            return risk_amount / price

        return self.config.fixed_quantity

    def _update_position_from_trade(self, trade: Trade) -> None:
        """根据成交更新持仓"""
        symbol = trade.symbol

        if symbol not in self._positions:
            # 创建新持仓，提供所有必需字段
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=0.0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                last_price=trade.price
            )

        position = self._positions[symbol]

        if trade.side == OrderSide.BUY:
            # 买入逻辑
            if position.quantity == 0:
                position.quantity = trade.quantity
                position.avg_price = trade.price
            else:
                # 加仓逻辑
                total_cost = position.quantity * position.avg_price + trade.quantity * trade.price
                position.quantity += trade.quantity
                position.avg_price = total_cost / position.quantity
        else:
            # 卖出逻辑
            if position.quantity > 0:
                # 计算盈亏
                profit = (trade.price - position.avg_price) * trade.quantity
                position.realized_pnl += profit
                position.quantity -= trade.quantity

                # 如果完全平仓，重置平均价格
                if position.quantity == 0:
                    position.avg_price = 0.0

        # 更新最新价格
        position.last_price = trade.price

        # 更新未实现盈亏
        if position.quantity > 0:
            position.unrealized_pnl = (position.last_price - position.avg_price) * position.quantity
        else:
            position.unrealized_pnl = 0.0

    def _update_account_from_trade(self, trade: Trade) -> None:
        """根据成交更新账户"""
        if self._account is None:
            return

        cost = trade.quantity * trade.price + trade.commission

        if trade.side == OrderSide.BUY:
            # 买入：扣除USDT余额
            if "USDT" in self._account.balances:
                usdt_balance = self._account.balances["USDT"]
                usdt_balance.free -= cost
                usdt_balance.total = usdt_balance.free + usdt_balance.locked
                self._account.total_balance -= cost
                self._account.available_balance = usdt_balance.free
        else:
            # 卖出：增加USDT余额
            if "USDT" in self._account.balances:
                usdt_balance = self._account.balances["USDT"]
                usdt_balance.free += trade.quantity * trade.price - trade.commission
                usdt_balance.total = usdt_balance.free + usdt_balance.locked
                self._account.total_balance += trade.quantity * trade.price - trade.commission
                self._account.available_balance = usdt_balance.free

        # 更新账户时间
        from datetime import datetime
        self._account.updated_at = datetime.now()

    def _update_positions(self, current_price: float) -> None:
        """更新所有持仓的市值"""
        for position in self._positions.values():
            # 直接更新last_price字段
            position.last_price = current_price

            # 更新未实现盈亏
            if position.quantity > 0:
                position.unrealized_pnl = (position.last_price - position.avg_price) * position.quantity
            else:
                position.unrealized_pnl = 0.0

    def _calculate_equity(self, current_price: float) -> float:
        """计算当前权益"""
        if self._account is None:
            return 0.0

        # 现金
        equity = self._account.total_balance

        # 持仓市值
        for position in self._positions.values():
            equity += position.quantity * current_price

        return equity

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

        if result.duration_days > 0:
            # 使用对数计算年化收益率，避免复数问题
            if result.total_return > -1:  # 确保底数为正数
                annualized_factor = 365 / result.duration_days
                # 使用对数计算避免复数
                result.annual_return = float(np.exp(np.log(1 + result.total_return) * annualized_factor) - 1)
            else:
                result.annual_return = -1.0  # 如果总收益率为-100%或更低，年化收益率为-100%
        else:
            result.annual_return = 0.0  # 如果duration_days <= 0，年化收益率为0

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

        # 夏普比率（假设无风险利率为0）
        if result.volatility > 0:
            result.sharpe_ratio = result.annual_return / result.volatility

        # Calmar比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annual_return / result.max_drawdown

        # 交易统计
        result.total_trades = len(self._trades)
        result.total_commission = self._total_commission
        result.total_slippage = self._total_slippage

        # 计算胜率和盈亏
        profits = []
        for trade in self._trades:
            if trade.side == OrderSide.SELL:
                # 简化计算：卖出即为平仓
                profit = trade.quantity * trade.price - trade.commission  # 修复amount引用
                profits.append(profit)

        if profits:
            wins = [p for p in profits if p > 0]
            losses = [p for p in profits if p < 0]

            result.winning_trades = len(wins)
            result.losing_trades = len(losses)
            result.win_rate = len(wins) / len(profits) if profits else 0

            if wins:
                result.avg_win = np.mean(wins)
                result.max_win = max(wins)

            if losses:
                result.avg_loss = abs(np.mean(losses))
                result.max_loss = abs(min(losses))

            result.avg_trade = np.mean(profits)

            total_wins = sum(wins) if wins else 0
            total_losses = abs(sum(losses)) if losses else 0

            if total_losses > 0:
                result.profit_factor = total_wins / total_losses

        # 交易记录
        result.trades = [t.to_dict() for t in self._trades]

        return result
