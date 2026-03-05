"""
信号 WebSocket 推送订阅器
=========================

监听信号事件总线上的订单事件和快照事件，
将最新的仓位变化推送到前端订阅的 WebSocket 频道。

职责单一：
- 接收事件 → 推送到前端 WebSocket
- 不涉及数据库操作
"""

import structlog
from typing import Any

from quant_trading_system.engines.signal_event_bus import (
    SignalEvent,
    SignalEventType,
    SignalSubscriber,
)

logger = structlog.get_logger(__name__)

# 需要推送到前端的订单事件类型
_WS_ORDER_EVENTS = {
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
}

# 需要推送到前端的快照事件类型
_WS_SNAPSHOT_EVENTS = {
    SignalEventType.SNAPSHOT_OPEN_ORDERS,
    SignalEventType.SNAPSHOT_POSITIONS,
    SignalEventType.SNAPSHOT_ACCOUNT,
    SignalEventType.SNAPSHOT_TRADE_HISTORY,
}

# 所有需要推送的事件类型集合（供外部注册使用）
WS_PUSH_EVENTS = _WS_ORDER_EVENTS | _WS_SNAPSHOT_EVENTS


class SignalWsSubscriber(SignalSubscriber):
    """
    信号 WebSocket 推送订阅器

    监听所有订单事件和快照事件，将最新的仓位变化推送到前端 WebSocket：
    - 实时订单事件 → 推送订单状态变化
    - 快照事件 → 推送持仓/挂单/账户快照
    """

    @property
    def name(self) -> str:
        return "SignalWsSubscriber"

    async def on_signal_event(self, event: SignalEvent) -> None:
        """根据事件类型推送到前端 WebSocket"""
        if event.type in _WS_ORDER_EVENTS:
            await self._push_order_event(event)
        elif event.type in _WS_SNAPSHOT_EVENTS:
            await self._push_snapshot_event(event)

    async def _push_order_event(self, event: SignalEvent) -> None:
        """
        推送实时订单事件到前端 WebSocket

        将订单状态变化（NEW / FILLED / PARTIALLY_FILLED / CANCELED）
        通过 WebSocket 推送到订阅了 signal/{signal_id} 频道的前端客户端。
        """
        data = event.data
        original_order_id = data.get("original_order_id", "")
        order_status = data.get("status", "")

        try:
            from quant_trading_system.api.websocket.trading_ws import push_copy_trade_signal

            await push_copy_trade_signal(
                signal_id=event.signal_id,
                event_type=event.type.name,
                trade_data={
                    "signal_id": event.signal_id,
                    "original_order_id": original_order_id,
                    "order_status": order_status,
                    "symbol": data.get("symbol", ""),
                    "side": data.get("side", ""),
                    "price": float(data.get("price", 0)),
                    "quantity": float(data.get("quantity", 0)),
                    "quote_quantity": float(data.get("quote_quantity", 0)),
                    "trade_time": data.get("trade_time", 0),
                    "commission": float(data.get("commission", 0)),
                    "commission_asset": data.get("commission_asset", ""),
                },
            )
            logger.debug(
                f"📤 已推送订单事件到前端: signal_id={event.signal_id}, "
                f"type={event.type.name}, symbol={data.get('symbol', '')}"
            )
        except Exception as e:
            # WebSocket 推送失败不应影响其他订阅器
            logger.debug(f"WebSocket 推送订单事件失败: {e}")

    async def _push_snapshot_event(self, event: SignalEvent) -> None:
        """
        推送快照事件到前端 WebSocket

        将启动时拉取的快照数据（持仓/挂单/账户/成交历史）
        通过 WebSocket 推送到订阅了 signal/{signal_id} 频道的前端客户端。
        """
        try:
            from quant_trading_system.api.websocket.trading_ws import push_copy_trade_signal

            snapshot_type = event.type.name  # 如 SNAPSHOT_POSITIONS
            await push_copy_trade_signal(
                signal_id=event.signal_id,
                event_type=snapshot_type,
                trade_data={
                    "signal_id": event.signal_id,
                    "snapshot_type": snapshot_type,
                    "data": event.data,
                },
            )
            logger.debug(
                f"📤 已推送快照事件到前端: signal_id={event.signal_id}, "
                f"type={snapshot_type}"
            )
        except Exception as e:
            logger.debug(f"WebSocket 推送快照事件失败: {e}")
