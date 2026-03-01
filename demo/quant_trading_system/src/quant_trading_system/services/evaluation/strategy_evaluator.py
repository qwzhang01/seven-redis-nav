"""
策略评价器
==========

订阅订单成交事件，增量计算策略绩效指标。
支持：
- 实时增量计算胜率、盈亏比、夏普比率等指标
- 订阅 ORDER_FILLED 事件，订单成交后触发计算
- 按策略分组统计
"""

import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import structlog

from quant_trading_system.core.enums import OrderSide
from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.trading import Trade, Position

logger = structlog.get_logger(__name__)


@dataclass
class StrategyMetrics:
    """策略绩效指标（增量更新）"""

    strategy_id: str = ""

    # 交易统计
    total_trades: int = 0
    buy_trades: int = 0
    sell_trades: int = 0

    # 盈亏统计（基于平仓交易）
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0

    # 派生指标
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade_pnl: float = 0.0
    expectancy: float = 0.0

    # 权益相关
    equity_curve: list[float] = field(default_factory=list)
    peak_equity: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0

    # 费用统计
    total_commission: float = 0.0

    # 时间
    first_trade_time: float = 0.0
    last_trade_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转为字典"""
        return {
            "strategy_id": self.strategy_id,
            "total_trades": self.total_trades,
            "buy_trades": self.buy_trades,
            "sell_trades": self.sell_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "avg_trade_pnl": self.avg_trade_pnl,
            "expectancy": self.expectancy,
            "max_win": self.max_win,
            "max_loss": self.max_loss,
            "total_profit": self.total_profit,
            "total_loss": self.total_loss,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "total_commission": self.total_commission,
        }


class StrategyEvaluator:
    """
    策略评价器

    订阅 ORDER_FILLED 事件，增量计算策略绩效指标。
    按策略分组管理指标。
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
        initial_equity: float = 0.0,
    ) -> None:
        self._event_engine = event_engine
        self._initial_equity = initial_equity

        # 按策略分组的绩效指标
        self._metrics: dict[str, StrategyMetrics] = {}

        # 按策略分组的持仓成本 {strategy_id: {symbol: avg_price}}
        self._entry_prices: dict[str, dict[str, float]] = defaultdict(dict)

        # 当前权益
        self._current_equity = initial_equity

        # 全局统计
        self._all_trades: list[Trade] = []

    async def start(self) -> None:
        """启动评价器，注册事件监听"""
        if self._event_engine:
            self._event_engine.register(
                EventType.ORDER_FILLED, self._on_order_filled
            )
            logger.info("策略评价器已启动，已订阅 ORDER_FILLED 事件")

    async def stop(self) -> None:
        """停止评价器"""
        if self._event_engine:
            self._event_engine.unregister(
                EventType.ORDER_FILLED, self._on_order_filled
            )
            logger.info("策略评价器已停止")

    async def _on_order_filled(self, event: Event) -> None:
        """处理订单成交事件"""
        trade = event.data
        if isinstance(trade, Trade):
            self.on_trade(trade)

    def on_trade(self, trade: Trade) -> None:
        """
        处理成交（支持同步调用，用于回测模式）

        Args:
            trade: 成交记录
        """
        strategy_id = trade.strategy_id or "default"
        self._all_trades.append(trade)

        # 获取或创建策略指标
        if strategy_id not in self._metrics:
            self._metrics[strategy_id] = StrategyMetrics(
                strategy_id=strategy_id,
            )

        metrics = self._metrics[strategy_id]

        # 更新交易计数
        metrics.total_trades += 1
        metrics.total_commission += trade.commission

        if metrics.first_trade_time == 0:
            metrics.first_trade_time = trade.timestamp
        metrics.last_trade_time = trade.timestamp

        if trade.side == OrderSide.BUY:
            metrics.buy_trades += 1
            # 记录买入成本
            self._entry_prices[strategy_id][trade.symbol] = trade.price
        else:
            metrics.sell_trades += 1
            # 计算平仓盈亏
            entry_price = self._entry_prices[strategy_id].get(trade.symbol, 0)
            if entry_price > 0:
                pnl = (trade.price - entry_price) * trade.quantity - trade.commission
                self._update_pnl_stats(metrics, pnl)
                # 清除成本记录
                self._entry_prices[strategy_id].pop(trade.symbol, None)

        # 更新派生指标
        self._recalculate_derived(metrics)

        logger.debug(
            "策略评价更新",
            strategy_id=strategy_id,
            total_trades=metrics.total_trades,
            win_rate=f"{metrics.win_rate:.2%}",
        )

    def on_equity_update(self, equity: float, strategy_id: str = "default") -> None:
        """
        更新权益曲线（用于计算回撤等指标）

        Args:
            equity: 当前权益
            strategy_id: 策略ID
        """
        if strategy_id not in self._metrics:
            self._metrics[strategy_id] = StrategyMetrics(
                strategy_id=strategy_id,
            )

        metrics = self._metrics[strategy_id]
        metrics.equity_curve.append(equity)

        # 更新峰值和回撤
        if equity > metrics.peak_equity:
            metrics.peak_equity = equity

        if metrics.peak_equity > 0:
            metrics.current_drawdown = (metrics.peak_equity - equity) / metrics.peak_equity
            metrics.max_drawdown = max(metrics.max_drawdown, metrics.current_drawdown)

        self._current_equity = equity

    def _update_pnl_stats(self, metrics: StrategyMetrics, pnl: float) -> None:
        """更新盈亏统计"""
        if pnl > 0:
            metrics.winning_trades += 1
            metrics.total_profit += pnl
            metrics.max_win = max(metrics.max_win, pnl)
        elif pnl < 0:
            metrics.losing_trades += 1
            metrics.total_loss += abs(pnl)
            metrics.max_loss = max(metrics.max_loss, abs(pnl))

    def _recalculate_derived(self, metrics: StrategyMetrics) -> None:
        """重新计算派生指标"""
        closed_trades = metrics.winning_trades + metrics.losing_trades

        if closed_trades > 0:
            metrics.win_rate = metrics.winning_trades / closed_trades

            net_pnl = metrics.total_profit - metrics.total_loss
            metrics.avg_trade_pnl = net_pnl / closed_trades

        if metrics.winning_trades > 0:
            metrics.avg_win = metrics.total_profit / metrics.winning_trades

        if metrics.losing_trades > 0:
            metrics.avg_loss = metrics.total_loss / metrics.losing_trades

        if metrics.total_loss > 0:
            metrics.profit_factor = metrics.total_profit / metrics.total_loss

        # 期望值
        metrics.expectancy = (
            metrics.win_rate * metrics.avg_win -
            (1 - metrics.win_rate) * metrics.avg_loss
        )

    def get_metrics(self, strategy_id: str = "default") -> StrategyMetrics | None:
        """获取策略绩效指标"""
        return self._metrics.get(strategy_id)

    def get_all_metrics(self) -> dict[str, StrategyMetrics]:
        """获取所有策略的绩效指标"""
        return dict(self._metrics)

    def set_initial_equity(self, equity: float) -> None:
        """设置初始权益"""
        self._initial_equity = equity
        self._current_equity = equity

    def reset(self) -> None:
        """重置所有指标"""
        self._metrics.clear()
        self._entry_prices.clear()
        self._all_trades.clear()
        self._current_equity = self._initial_equity

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "strategy_count": len(self._metrics),
            "total_trades": len(self._all_trades),
            "metrics": {
                sid: m.to_dict()
                for sid, m in self._metrics.items()
            },
        }
