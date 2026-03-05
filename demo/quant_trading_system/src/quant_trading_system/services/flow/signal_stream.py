"""
单个信号流实例
==============

负责监听一个 subscribe 类型信号源的目标账户 WebSocket。
收到订单事件后解析并发布到事件总线。
"""

import logging
from typing import Any, Optional

from quant_trading_system.core.config import settings
from quant_trading_system.exchange_adapter.binance.binance_user_stream import (
    BinanceUserStreamManager,
)
from quant_trading_system.engines.signal_event_bus import (
    SignalEvent,
    SignalEventBus,
    SignalEventType,
    signal_event_bus,
)

logger = logging.getLogger(__name__)


class SignalStream:
    """
    单个信号流实例

    负责监听一个 subscribe 类型信号源的目标账户 WebSocket。
    收到订单事件后解析并发布到事件总线。
    """

    def __init__(
        self,
        signal_id: int,
        signal_name: str,
        target_api_key: str,
        target_api_secret: str,
        account_type: str = "spot",
        exchange: str = "binance",
        testnet: bool = False,
        watch_symbols: list[str] | None = None,
        event_bus: SignalEventBus | None = None,
    ):
        self.signal_id = signal_id
        self.signal_name = signal_name
        self.account_type = account_type
        self.exchange = exchange
        self.watch_symbols = set(
            s.upper().replace("/", "") for s in (watch_symbols or [])
        )

        self._event_bus = event_bus or signal_event_bus

        # 目标账户 WebSocket 监听器
        # 开发环境使用 Mock，不连接真实 Binance
        if settings.is_development:
            from quant_trading_system.exchange_adapter.mock.mock_binance_user_stream import (
                MockBinanceUserStreamManager,
            )
            self._stream_manager = MockBinanceUserStreamManager(
                api_key=target_api_key,
                api_secret=target_api_secret,
                account_type=account_type,
                testnet=testnet,
            )
        else:
            self._stream_manager = BinanceUserStreamManager(
                api_key=target_api_key,
                api_secret=target_api_secret,
                account_type=account_type,
                testnet=testnet,
                proxy_url=settings.exchange.proxy_url,
            )

        # 统计
        self._events_received = 0
        self._events_published = 0

    async def start(self) -> None:
        """启动信号流"""
        self._stream_manager.on_order_update = self._on_order_event
        self._stream_manager.on_account_update = self._on_account_event
        self._stream_manager.on_snapshot_ready = self._on_snapshot_ready
        await self._stream_manager.start()
        logger.info(f"信号流已启动: signal_id={self.signal_id}, name={self.signal_name}")

    async def stop(self) -> None:
        """停止信号流"""
        await self._stream_manager.stop()
        logger.info(f"信号流已停止: signal_id={self.signal_id}, name={self.signal_name}")

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        ws_status = self._stream_manager.get_status()
        return {
            "signal_id": self.signal_id,
            "signal_name": self.signal_name,
            "account_type": self.account_type,
            "exchange": self.exchange,
            "watch_symbols": list(self.watch_symbols) if self.watch_symbols else "all",
            "events_received": self._events_received,
            "events_published": self._events_published,
            "websocket": ws_status,
        }

    async def _on_order_event(self, event: dict[str, Any]) -> None:
        """
        处理订单事件回调

        解析 WebSocket 推送的订单事件，转换为标准化 SignalEvent 并发布。
        """
        event_type = event.get("e", "")
        self._events_received += 1

        # 解析事件
        if event_type == "executionReport":
            order_data = self._parse_spot_execution_report(event)
        elif event_type == "ORDER_TRADE_UPDATE":
            order_data = self._parse_futures_order_update(event)
        else:
            return

        if not order_data:
            return

        # 交易对过滤
        symbol = order_data.get("symbol", "")
        if self.watch_symbols and symbol not in self.watch_symbols:
            return

        # 根据订单状态决定事件类型
        status = order_data.get("status", "")
        if status == "FILLED":
            signal_event_type = SignalEventType.ORDER_FILLED
        elif status == "PARTIALLY_FILLED":
            signal_event_type = SignalEventType.ORDER_PARTIALLY_FILLED
        elif status == "NEW":
            signal_event_type = SignalEventType.ORDER_NEW
        elif status in ("CANCELED", "CANCELLED", "EXPIRED"):
            signal_event_type = SignalEventType.ORDER_CANCELED
        else:
            return

        # 只对 FILLED 记录详细日志
        if signal_event_type == SignalEventType.ORDER_FILLED:
            logger.info(
                f"📡 信号事件: signal_id={self.signal_id} {symbol} "
                f"{order_data.get('side')} qty={order_data.get('quantity'):.6f} "
                f"price={order_data.get('price'):.4f}"
            )

        # 发布到事件总线
        signal_event = SignalEvent(
            type=signal_event_type,
            signal_id=self.signal_id,
            data=order_data,
            exchange=self.exchange,
            symbol=symbol,
            raw_event=event,
        )
        await self._event_bus.publish(signal_event)
        self._events_published += 1

    async def _on_account_event(self, event: dict[str, Any]) -> None:
        """处理账户变化事件"""
        signal_event = SignalEvent(
            type=SignalEventType.ACCOUNT_UPDATE,
            signal_id=self.signal_id,
            data=event,
            exchange=self.exchange,
            raw_event=event,
        )
        await self._event_bus.publish(signal_event)

    async def _on_snapshot_ready(self, snapshot: dict[str, Any]) -> None:
        """
        处理启动时的历史快照回调

        将快照数据拆分为不同的事件类型发布到事件总线：
        - SNAPSHOT_OPEN_ORDERS: 当前挂单
        - SNAPSHOT_POSITIONS: 当前持仓
        - SNAPSHOT_ACCOUNT: 账户信息
        """
        logger.info(
            f"📸 收到初始快照: signal_id={self.signal_id}, "
            f"open_orders={len(snapshot.get('open_orders', []))}, "
            f"positions={len(snapshot.get('positions', []))}, "
            f"has_account={'yes' if snapshot.get('account') else 'no'}"
        )

        # 发布挂单快照
        if snapshot.get("open_orders"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_OPEN_ORDERS,
                signal_id=self.signal_id,
                data={"open_orders": snapshot["open_orders"]},
                exchange=self.exchange,
            ))

        # 发布持仓快照
        if snapshot.get("positions"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_POSITIONS,
                signal_id=self.signal_id,
                data={"positions": snapshot["positions"]},
                exchange=self.exchange,
            ))

        # 发布账户信息快照
        if snapshot.get("account"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_ACCOUNT,
                signal_id=self.signal_id,
                data={"account": snapshot["account"]},
                exchange=self.exchange,
            ))

    def _parse_spot_execution_report(self, event: dict) -> Optional[dict[str, Any]]:
        """解析现货订单事件"""
        try:
            executed_qty = float(event.get("z", 0))
            cum_quote = float(event.get("Z", 0))
            avg_price = (cum_quote / executed_qty) if executed_qty > 0 else 0
            commission = float(event.get("n", 0))
            commission_asset = event.get("N", "")

            return {
                "symbol": event.get("s", ""),
                "side": event.get("S", ""),
                "order_type": event.get("o", "MARKET"),
                "status": event.get("X", ""),
                "quantity": executed_qty,
                "price": avg_price,
                "quote_quantity": cum_quote,
                "original_order_id": str(event.get("i", "")),
                "trade_time": event.get("T", 0),
                "commission": commission,
                "commission_asset": commission_asset,
            }
        except (ValueError, TypeError) as e:
            logger.error(f"解析现货订单事件失败: {e}")
            return None

    def _parse_futures_order_update(self, event: dict) -> Optional[dict[str, Any]]:
        """解析合约订单事件"""
        try:
            order = event.get("o", {})
            qty = float(order.get("z", 0))
            avg_price = float(order.get("ap", 0))

            return {
                "symbol": order.get("s", ""),
                "side": order.get("S", ""),
                "order_type": order.get("o", "MARKET"),
                "status": order.get("X", ""),
                "quantity": qty,
                "price": avg_price,
                "quote_quantity": qty * avg_price,
                "original_order_id": str(order.get("i", "")),
                "trade_time": order.get("T", 0),
                "commission": float(order.get("n", 0)),
                "commission_asset": order.get("N", ""),
            }
        except (ValueError, TypeError) as e:
            logger.error(f"解析合约订单事件失败: {e}")
            return None
