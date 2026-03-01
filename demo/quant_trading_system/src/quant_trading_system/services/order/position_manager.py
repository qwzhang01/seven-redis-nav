"""
仓位管理器
==========

统一的仓位管理，适用于回测/模拟/实盘三种模式。
负责：
- 持仓更新（加仓均价、减仓盈亏）
- 未实现盈亏计算
- 已实现盈亏跟踪
"""

from typing import Any

import structlog

from quant_trading_system.core.enums import OrderSide
from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.trading import Position, Trade

logger = structlog.get_logger(__name__)


class PositionManager:
    """
    统一仓位管理器

    负责所有模式下的持仓更新和盈亏计算
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
    ) -> None:
        self._event_engine = event_engine

        # 持仓 {symbol: Position}
        self._positions: dict[str, Position] = {}

    def update_from_trade(self, trade: Trade) -> Position:
        """
        根据成交更新持仓

        Args:
            trade: 成交记录

        Returns:
            更新后的持仓
        """
        symbol = trade.symbol

        if symbol not in self._positions:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=0.0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                last_price=trade.price,
                strategy_id=trade.strategy_id,
            )

        position = self._positions[symbol]

        if trade.side == OrderSide.BUY:
            # 买入：加仓，加权平均成本
            if position.quantity == 0:
                position.quantity = trade.quantity
                position.avg_price = trade.price
            else:
                total_cost = position.quantity * position.avg_price + trade.quantity * trade.price
                position.quantity += trade.quantity
                position.avg_price = total_cost / position.quantity
        else:
            # 卖出：减仓，计算已实现盈亏
            if position.quantity > 0:
                reduce_quantity = min(trade.quantity, position.quantity)
                realized_pnl = (trade.price - position.avg_price) * reduce_quantity
                position.realized_pnl += realized_pnl
                position.quantity -= reduce_quantity

                # 完全平仓，重置均价
                if position.quantity <= 0:
                    position.quantity = 0.0
                    position.avg_price = 0.0

        # 更新最新价格
        position.last_price = trade.price

        # 更新未实现盈亏
        self._update_unrealized_pnl(position)

        logger.debug(
            "持仓更新",
            symbol=symbol,
            side=trade.side.value,
            quantity=f"{position.quantity:.6f}",
            avg_price=f"{position.avg_price:.4f}",
            realized_pnl=f"{position.realized_pnl:.4f}",
        )

        return position

    def update_market_price(self, symbol: str, price: float) -> None:
        """
        更新品种的市场价格，重新计算未实现盈亏

        Args:
            symbol: 交易品种
            price: 最新市场价格
        """
        position = self._positions.get(symbol)
        if position and position.quantity > 0:
            position.last_price = price
            self._update_unrealized_pnl(position)

    def update_all_market_prices(self, prices: dict[str, float]) -> None:
        """
        批量更新市场价格

        Args:
            prices: {symbol: price}
        """
        for symbol, price in prices.items():
            self.update_market_price(symbol, price)

    def _update_unrealized_pnl(self, position: Position) -> None:
        """更新未实现盈亏"""
        if position.quantity > 0:
            position.unrealized_pnl = (position.last_price - position.avg_price) * position.quantity
        else:
            position.unrealized_pnl = 0.0

    def get_position(self, symbol: str) -> Position | None:
        """获取持仓"""
        return self._positions.get(symbol)

    def get_all_positions(self) -> dict[str, Position]:
        """获取所有持仓"""
        return dict(self._positions)

    def get_total_position_value(self) -> float:
        """获取总持仓市值"""
        return sum(pos.notional_value for pos in self._positions.values())

    def get_total_unrealized_pnl(self) -> float:
        """获取总未实现盈亏"""
        return sum(pos.unrealized_pnl for pos in self._positions.values())

    def get_total_realized_pnl(self) -> float:
        """获取总已实现盈亏"""
        return sum(pos.realized_pnl for pos in self._positions.values())

    def reset(self) -> None:
        """重置所有持仓"""
        self._positions.clear()

    @property
    def positions(self) -> dict[str, Position]:
        """获取持仓引用（供 StrategyContext 使用）"""
        return self._positions

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_positions": len(self._positions),
            "active_positions": sum(1 for p in self._positions.values() if p.quantity > 0),
            "total_position_value": self.get_total_position_value(),
            "total_unrealized_pnl": self.get_total_unrealized_pnl(),
            "total_realized_pnl": self.get_total_realized_pnl(),
        }
