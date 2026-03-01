"""
交易引擎
========

负责策略的实盘和模拟交易，职责为：
- 管理策略实例的运行生命周期
- 接收信号事件，委托 OrderProcessor 处理
- 管理交易所网关连接
- 提供订单/持仓查询接口（委托给 OrderProcessor）
"""

from typing import Any, TYPE_CHECKING

import structlog

from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.core.enums import OrderStatus
from quant_trading_system.models.trading import Order
from quant_trading_system.services.strategy.signal import Signal

if TYPE_CHECKING:
    from quant_trading_system.services.order.order_processor import OrderProcessor
    from quant_trading_system.models.trading import Position

logger = structlog.get_logger(__name__)


class TradingEngine:
    """
    交易引擎

    职责：
    - 管理策略实例的实盘/模拟交易运行
    - 接收信号事件，委托 OrderProcessor 处理完整的信号→订单→仓位管道
    - 管理交易所网关连接
    - 提供订单/持仓/账户查询接口
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
    ) -> None:
        self._event_engine = event_engine

        # 订单处理器（由编排器注入）
        self._order_processor: "OrderProcessor | None" = None

        # 交易所网关 {exchange: gateway}
        self._gateways: dict[str, Any] = {}

        # 默认交易所
        self._default_exchange: str = ""

        # 运行状态
        self._running = False

    async def start(self) -> None:
        """启动交易引擎"""
        if self._running:
            return

        self._running = True

        # 注册信号事件处理
        if self._event_engine:
            self._event_engine.register(EventType.SIGNAL, self._on_signal)

        logger.info("Trading engine started")

    async def stop(self) -> None:
        """停止交易引擎"""
        if not self._running:
            return

        self._running = False

        # 取消注册事件
        if self._event_engine:
            self._event_engine.unregister(EventType.SIGNAL, self._on_signal)

        logger.info("Trading engine stopped")

    def set_order_processor(self, order_processor: "OrderProcessor") -> None:
        """设置订单处理器（由编排器注入）"""
        self._order_processor = order_processor

    def register_gateway(self, exchange: str, gateway: Any) -> None:
        """注册交易所网关"""
        self._gateways[exchange] = gateway
        if not self._default_exchange:
            self._default_exchange = exchange
        logger.info("Gateway registered", exchange=exchange)

    def set_default_exchange(self, exchange: str) -> None:
        """设置默认交易所"""
        self._default_exchange = exchange

    async def execute_signal(self, signal: Signal, market_price: float = 0.0) -> Order | None:
        """
        执行交易信号

        委托 OrderProcessor 处理完整的信号→订单→仓位管道。

        Args:
            signal: 交易信号
            market_price: 当前市场价格（如果为0则需要从行情获取）

        Returns:
            创建的订单，如果失败则返回 None
        """
        if not self._running:
            logger.warning("Trading engine not running")
            return None

        if self._order_processor is None:
            logger.error("OrderProcessor not configured")
            return None

        # 委托 OrderProcessor 处理
        result = await self._order_processor.process_signal(signal, market_price)

        if result and result.success and result.order:
            return result.order

        return None

    async def _on_signal(self, event: Event) -> None:
        """信号事件处理"""
        signal = event.data
        if isinstance(signal, Signal):
            # 从信号中获取市场价格（如果有）
            market_price = signal.price if signal.price > 0 else 0.0
            await self.execute_signal(signal, market_price)

    async def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if self._order_processor is None:
            return False

        # 查找订单
        for order in self._order_processor.orders:
            if order.order_id == order_id:
                order.status = OrderStatus.CANCELLED
                return True
        return False

    async def cancel_all_orders(self, symbol: str | None = None) -> int:
        """
        取消所有订单

        Args:
            symbol: 品种（可选，不指定则取消所有）

        Returns:
            取消的订单数量
        """
        if self._order_processor is None:
            return 0

        cancelled = 0
        for order in self._order_processor.orders:
            if order.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED):
                if symbol is None or order.symbol == symbol:
                    order.status = OrderStatus.CANCELLED
                    cancelled += 1

        return cancelled

    # ---- 查询接口（委托给 OrderProcessor） ----

    def get_positions(self) -> dict[str, "Position"]:
        """获取所有持仓"""
        if self._order_processor:
            return dict(self._order_processor.position_manager.positions)
        return {}

    def get_position(self, symbol: str) -> "Position | None":
        """获取特定持仓"""
        if self._order_processor:
            return self._order_processor.position_manager.get_position(symbol)
        return None

    def get_orders(self) -> list[Order]:
        """获取所有订单"""
        if self._order_processor:
            return list(self._order_processor.orders)
        return []

    def get_order(self, order_id: str) -> Order | None:
        """获取订单"""
        if self._order_processor:
            for order in self._order_processor.orders:
                if order.order_id == order_id:
                    return order
        return None

    async def on_tick_data(self, tick_data: dict) -> None:
        """处理Tick数据，更新持仓的最新价格"""
        if self._order_processor is None:
            return

        symbol = tick_data.get("symbol", "")
        last_price = tick_data.get("last_price", 0.0)

        if symbol and last_price > 0:
            self._order_processor.position_manager.update_market_price(
                symbol, last_price
            )

    async def on_order_update(self, order_update: dict) -> None:
        """处理外部订单更新（来自交易所网关）"""
        order_id = order_update.get("order_id", "")
        status = order_update.get("status")

        if order_id and status:
            for order in self._order_processor.orders:
                if order.order_id == order_id:
                    order.status = OrderStatus(status)
                    break

    async def on_trade_data(self, trade_data: dict) -> None:
        """处理外部成交数据（来自交易所网关）"""
        # 实盘交易中，成交数据来自交易所回报
        # 通过事件引擎发布 ORDER_FILLED 事件，驱动后续流程
        if self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.ORDER_FILLED,
                data=trade_data,
            ))

    @property
    def order_processor(self) -> "OrderProcessor | None":
        """获取订单处理器"""
        return self._order_processor

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        stats: dict[str, Any] = {
            "running": self._running,
            "gateways": list(self._gateways.keys()),
            "default_exchange": self._default_exchange,
        }
        if self._order_processor:
            stats["order_processor"] = self._order_processor.stats
        return stats
