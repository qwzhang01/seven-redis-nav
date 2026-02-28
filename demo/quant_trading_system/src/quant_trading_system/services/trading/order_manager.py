"""
订单管理器
==========

管理订单生命周期，包括：
- 订单创建和验证
- 订单状态跟踪
- 订单历史记录
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, Callable, Coroutine

import structlog

from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.core.enums import OrderSide, OrderStatus, OrderType, SignalType
from quant_trading_system.models.trading import (
    Order,
    Trade,
)
from quant_trading_system.services.strategy.signal import Signal

logger = structlog.get_logger(__name__)


# 订单回调类型
OrderCallback = Callable[[Order], Coroutine[Any, Any, None]]
TradeCallback = Callable[[Trade], Coroutine[Any, Any, None]]


class OrderManager:
    """
    订单管理器

    职责：
    - 订单创建和验证
    - 订单状态管理
    - 订单查询和统计
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
    ) -> None:
        self._event_engine = event_engine

        # 订单存储
        self._orders: dict[str, Order] = {}

        # 活跃订单索引
        self._active_orders: dict[str, Order] = {}

        # 按策略分组的订单
        self._orders_by_strategy: dict[str, list[str]] = defaultdict(list)

        # 按品种分组的订单
        self._orders_by_symbol: dict[str, list[str]] = defaultdict(list)

        # 成交记录
        self._trades: dict[str, Trade] = {}

        # 回调
        self._order_callbacks: list[OrderCallback] = []
        self._trade_callbacks: list[TradeCallback] = []

        # 统计
        self._total_orders = 0
        self._filled_orders = 0
        self._cancelled_orders = 0
        self._rejected_orders = 0

    def create_order(
        self,
        symbol: str,
        exchange: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        stop_price: float = 0.0,
        strategy_id: str = "",
        signal_id: str = "",
        **kwargs: Any,
    ) -> Order:
        """
        创建订单

        Args:
            symbol: 交易对
            exchange: 交易所
            side: 买卖方向
            order_type: 订单类型
            quantity: 数量
            price: 价格
            stop_price: 触发价格
            strategy_id: 策略ID
            signal_id: 信号ID

        Returns:
            订单对象
        """
        order = Order(
            symbol=symbol,
            exchange=exchange,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            strategy_id=strategy_id,
            signal_id=signal_id,
            **kwargs,
        )

        # 存储订单
        self._orders[order.order_id] = order
        self._active_orders[order.order_id] = order
        self._orders_by_strategy[strategy_id].append(order.order_id)
        self._orders_by_symbol[symbol].append(order.order_id)

        self._total_orders += 1

        logger.info(f"Order created",
                   order_id=order.order_id,
                   symbol=symbol,
                   side=side.value,
                   quantity=quantity)

        return order

    def create_order_from_signal(
        self,
        signal: Signal,
        exchange: str = "",
    ) -> Order:
        """
        从信号创建订单

        Args:
            signal: 交易信号
            exchange: 交易所

        Returns:
            订单对象
        """
        # 确定订单方向
        if signal.signal_type in (SignalType.BUY, SignalType.OPEN_LONG):
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL

        # 确定订单类型
        if signal.price > 0:
            order_type = OrderType.LIMIT
        else:
            order_type = OrderType.MARKET

        return self.create_order(
            symbol=signal.symbol,
            exchange=exchange,
            side=side,
            order_type=order_type,
            quantity=signal.quantity,
            price=signal.price,
            strategy_id=signal.strategy_id,
            signal_id=signal.signal_id,
        )

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        filled_qty: float = 0.0,
        filled_price: float = 0.0,
        commission: float = 0.0,
        exchange_order_id: str = "",
    ) -> None:
        """
        更新订单状态

        Args:
            order_id: 订单ID
            status: 新状态
            filled_qty: 成交数量
            filled_price: 成交价格
            commission: 手续费
            exchange_order_id: 交易所订单ID
        """
        order = self._orders.get(order_id)
        if order is None:
            logger.warning(f"Order not found", order_id=order_id)
            return

        old_status = order.status
        order.status = status
        order.update_time = time.time() * 1000

        if exchange_order_id:
            order.exchange_order_id = exchange_order_id

        # 更新成交信息
        if filled_qty > 0:
            order.update_fill(filled_qty, filled_price, commission)

        # 更新活跃订单索引
        if order.is_finished and order_id in self._active_orders:
            del self._active_orders[order_id]

            if status == OrderStatus.FILLED:
                self._filled_orders += 1
            elif status == OrderStatus.CANCELLED:
                self._cancelled_orders += 1
            elif status == OrderStatus.REJECTED:
                self._rejected_orders += 1

        logger.info(f"Order status updated",
                   order_id=order_id,
                   old_status=old_status.value,
                   new_status=status.value)

        # 发送事件
        if self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.ORDER,
                data=order,
            ))

        # 调用回调
        await self._notify_order_update(order)

    async def on_trade(
        self,
        order_id: str,
        trade_id: str,
        price: float,
        quantity: float,
        commission: float = 0.0,
        commission_asset: str = "",
        exchange_trade_id: str = "",
    ) -> None:
        """
        处理成交回报

        Args:
            order_id: 订单ID
            trade_id: 成交ID
            price: 成交价格
            quantity: 成交数量
            commission: 手续费
            commission_asset: 手续费币种
            exchange_trade_id: 交易所成交ID
        """
        order = self._orders.get(order_id)
        if order is None:
            logger.warning(f"Order not found for trade", order_id=order_id)
            return

        # 创建成交记录
        trade = Trade(
            symbol=order.symbol,
            exchange=order.exchange,
            trade_id=trade_id,
            order_id=order_id,
            exchange_trade_id=exchange_trade_id,
            side=order.side,
            price=price,
            quantity=quantity,
            amount=price * quantity,
            commission=commission,
            commission_asset=commission_asset,
            strategy_id=order.strategy_id,
        )

        self._trades[trade_id] = trade

        # 更新订单状态
        order.update_fill(quantity, price, commission, commission_asset)

        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
            if order.order_id in self._active_orders:
                del self._active_orders[order.order_id]
                self._filled_orders += 1
        else:
            order.status = OrderStatus.PARTIAL_FILLED

        logger.info(f"Trade received",
                   trade_id=trade_id,
                   order_id=order_id,
                   price=price,
                   quantity=quantity)

        # 发送事件
        if self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.ORDER_FILLED,
                data=trade,
            ))

        # 调用回调
        await self._notify_trade(trade)
        await self._notify_order_update(order)

    def get_order(self, order_id: str) -> Order | None:
        """获取订单"""
        return self._orders.get(order_id)

    def get_active_orders(self) -> list[Order]:
        """获取所有活跃订单"""
        return list(self._active_orders.values())

    def get_orders_by_symbol(self, symbol: str) -> list[Order]:
        """获取某个品种的所有订单"""
        order_ids = self._orders_by_symbol.get(symbol, [])
        return [self._orders[oid] for oid in order_ids if oid in self._orders]

    def get_orders_by_strategy(self, strategy_id: str) -> list[Order]:
        """获取某个策略的所有订单"""
        order_ids = self._orders_by_strategy.get(strategy_id, [])
        return [self._orders[oid] for oid in order_ids if oid in self._orders]

    def get_active_orders_by_symbol(self, symbol: str) -> list[Order]:
        """获取某个品种的活跃订单"""
        return [o for o in self._active_orders.values() if o.symbol == symbol]

    def get_trade(self, trade_id: str) -> Trade | None:
        """获取成交记录"""
        return self._trades.get(trade_id)

    def get_trades_by_order(self, order_id: str) -> list[Trade]:
        """获取某个订单的所有成交"""
        return [t for t in self._trades.values() if t.order_id == order_id]

    def add_order_callback(self, callback: OrderCallback) -> None:
        """添加订单回调"""
        self._order_callbacks.append(callback)

    def add_trade_callback(self, callback: TradeCallback) -> None:
        """添加成交回调"""
        self._trade_callbacks.append(callback)

    async def _notify_order_update(self, order: Order) -> None:
        """通知订单更新"""
        if self._order_callbacks:
            tasks = [cb(order) for cb in self._order_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _notify_trade(self, trade: Trade) -> None:
        """通知成交"""
        if self._trade_callbacks:
            tasks = [cb(trade) for cb in self._trade_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_orders": self._total_orders,
            "active_orders": len(self._active_orders),
            "filled_orders": self._filled_orders,
            "cancelled_orders": self._cancelled_orders,
            "rejected_orders": self._rejected_orders,
            "total_trades": len(self._trades),
        }
