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

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, BarArray, TimeFrame
from quant_trading_system.models.trading import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    PositionSide,
    Trade,
)
from quant_trading_system.models.account import Account, AccountType, Balance
from quant_trading_system.services.strategy.base import Strategy, StrategyContext, StrategyState
from quant_trading_system.services.strategy.signal import Signal, SignalType
from quant_trading_system.services.indicators.indicator_engine import (
    IndicatorEngine,
    get_indicator_engine,
)

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
    ) -> None:
        self.config = config or BacktestConfig()

        # 指标引擎
        self._indicator_engine = get_indicator_engine()

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
        self._bar_data: dict[str, dict[TimeFrame, BarArray]] = {}

        # 当前时间
        self._current_time: float = 0.0

        # 统计
        self._total_commission: float = 0.0
        self._total_slippage: float = 0.0

    def run(
        self,
        strategy: Strategy,
        bars: dict[str, BarArray] | BarArray,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            strategy: 策略实例
            bars: K线数据 {symbol: BarArray} 或单个 BarArray

        Returns:
            回测结果
        """
        logger.info(f"Starting backtest", strategy=strategy.name)
        start_time = time.time()

        # 标准化数据
        if isinstance(bars, BarArray):
            bars = {bars.symbol: bars}

        # 初始化
        self._initialize(strategy, bars)

        # 运行回测
        self._run_backtest(strategy, bars)

        # 计算结果
        result = self._calculate_result(strategy)

        elapsed = time.time() - start_time
        logger.info(f"Backtest completed",
                   strategy=strategy.name,
                   duration=elapsed,
                   trades=result.total_trades,
                   return_pct=f"{result.total_return:.2%}")

        return result

    def _initialize(
        self,
        strategy: Strategy,
        bars: dict[str, BarArray]
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

        # 存储K线数据
        for symbol, bar_array in bars.items():
            self._bar_data[symbol] = {bar_array.timeframe: bar_array}

        # 创建策略上下文
        context = StrategyContext(
            strategy_id=strategy.strategy_id,
            symbols=list(bars.keys()),
            timeframes=[list(bars.values())[0].timeframe],
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
        bars: dict[str, BarArray]
    ) -> None:
        """执行回测"""
        # 获取主要品种的K线
        main_symbol = list(bars.keys())[0]
        main_bars = bars[main_symbol]

        # 预热期（确保有足够的数据计算指标）
        warmup_period = 100

        # 遍历K线
        for i in range(warmup_period, len(main_bars)):
            # 更新context.bars，只包含截止到当前索引的数据（避免未来函数）
            for symbol, bar_array in bars.items():
                # 创建截止到当前索引的BarArray切片
                sliced_bars = BarArray(
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
                self._bar_data[symbol][bar_array.timeframe] = sliced_bars

            # 更新当前时间（将numpy.datetime64转换为毫秒时间戳）
            ts = main_bars.timestamp[i]
            if isinstance(ts, np.datetime64):
                self._current_time = float(ts.astype('datetime64[ms]').astype(np.int64))
            else:
                self._current_time = ts.timestamp() * 1000 if hasattr(ts, 'timestamp') else float(ts)

            strategy.context.current_time = self._current_time

            # 创建当前Bar
            ts = main_bars.timestamp[i]
            if isinstance(ts, np.datetime64):
                from datetime import datetime
                bar_timestamp = datetime.fromtimestamp(
                    float(ts.astype('datetime64[ms]').astype(np.int64)) / 1000
                )
            else:
                bar_timestamp = ts

            bar = Bar(
                symbol=main_symbol,
                exchange=main_bars.exchange,
                timeframe=main_bars.timeframe,
                timestamp=bar_timestamp,
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
        order = Order(
            symbol=symbol,
            exchange="backtest",
            side=OrderSide.BUY if signal.is_buy else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            price=exec_price,
            status=OrderStatus.FILLED,
            filled_quantity=quantity,
            avg_price=exec_price,
            commission=commission,
            create_time=self._current_time,
            strategy_id=signal.strategy_id,
        )
        self._orders.append(order)

        # 创建成交记录
        trade = Trade(
            symbol=symbol,
            exchange="backtest",
            order_id=order.order_id,
            side=order.side,
            price=exec_price,
            quantity=quantity,
            amount=quantity * exec_price,
            commission=commission,
            timestamp=self._current_time,
            strategy_id=signal.strategy_id,
        )
        self._trades.append(trade)

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
            self._positions[symbol] = Position(
                symbol=symbol,
                exchange="backtest",
                side=PositionSide.LONG if trade.side == OrderSide.BUY else PositionSide.SHORT,
            )

        position = self._positions[symbol]

        if trade.side == OrderSide.BUY:
            position.add_quantity(trade.quantity, trade.price)
        else:
            if position.quantity > 0:
                position.reduce_quantity(
                    min(trade.quantity, position.quantity),
                    trade.price
                )

    def _update_account_from_trade(self, trade: Trade) -> None:
        """根据成交更新账户"""
        if self._account is None:
            return

        cost = trade.amount + trade.commission

        if trade.side == OrderSide.BUY:
            self._account.deduct_balance("USDT", cost)
        else:
            self._account.add_balance("USDT", trade.amount - trade.commission)

    def _update_positions(self, current_price: float) -> None:
        """更新所有持仓的市值"""
        for position in self._positions.values():
            position.update_price(current_price)

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
            result.annual_return = (
                (1 + result.total_return) ** (365 / result.duration_days) - 1
            )

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
                profit = trade.amount - trade.commission
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
