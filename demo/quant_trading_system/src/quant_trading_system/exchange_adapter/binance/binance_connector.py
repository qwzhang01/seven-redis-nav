"""
币安交易所连接器
================

纯粹负责对接币安交易所，职责单一：
- WebSocket 实时数据流连接与订阅管理
- 将交易所原始数据转换为统一格式后，通过事件总线发布
"""

from typing import Any

import structlog

from quant_trading_system.engines.market_event_bus import (
    MarketEventType, MarketEventBus,
)
from quant_trading_system.exchange_adapter.base import ExchangeConnector
from quant_trading_system.exchange_adapter.binance.binance_base import (
    BinanceConfig,
    BinanceDataConverter,
)
from quant_trading_system.exchange_adapter.ws_client import WebSocketClient

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 币安交易所连接器
# ═══════════════════════════════════════════════════════════════

class BinanceConnector(ExchangeConnector):
    """
    币安交易所连接器

    只负责：
    - 连接币安 WebSocket
    - 订阅/取消订阅行情数据流
    - 解析消息并发布到事件总线
    """

    def __init__(
        self,
        event_bus: MarketEventBus,
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
    ) -> None:
        super().__init__(name="binance", event_bus=event_bus)

        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret

        ws_url = BinanceConfig.get_ws_url(market_type)
        self._ws_client = WebSocketClient(
            url=ws_url,
            name=f"binance-{market_type}",
        )
        self._ws_client.set_callbacks(
            on_message=self._on_message,
            on_connect=self._on_connect,
        )
        self._sub_id = 0

    @classmethod
    def _build_streams(cls, symbols: list[str]) -> list[str]:
        """
        为给定交易对列表构建完整的 WebSocket 数据流名称列表。
        包含 trade、ticker、depth、所有K线周期。

        Args:
            symbols: 交易对列表

        Returns:
            WebSocket stream 名称列表
        """
        streams = []
        for symbol in symbols:
            s = symbol.lower().replace("/", "")
            streams.extend([f"{s}@trade", f"{s}@ticker", f"{s}@depth20@100ms"])
            streams.extend([f"{s}@kline_{interval}" for interval in BinanceConfig.ALL_KLINE_INTERVALS])
        return streams

    async def start(self) -> None:
        """启动币安连接器"""
        if self._running:
            return
        self._running = True
        connect_result = await self._ws_client.connect()

        # 发布连接事件
        await self._publish(
            MarketEventType.CONNECTED,
            {"market_type": self.market_type, "connected": connect_result},
        )
        logger.info("币安连接器已启动", market_type=self.market_type, connected=connect_result)

    async def stop(self) -> None:
        """停止币安连接器"""
        self._running = False
        await self._ws_client.disconnect()
        await self._publish(MarketEventType.DISCONNECTED, {"market_type": self.market_type})
        logger.info("币安连接器已停止")

    async def subscribe(self, symbols: list[str]) -> None:
        """订阅行情数据流"""
        if not self._ws_client.is_connected:
            logger.warning("WebSocket 未连接，无法订阅", symbols=symbols)
            return

        streams = self._build_streams(symbols)

        if not streams:
            logger.warning("所有同步选项均已禁用，无数据流可订阅", symbols=symbols)
            self._subscriptions.update(symbols)
            return

        self._sub_id += 1
        await self._ws_client.send({
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        })
        self._subscriptions.update(symbols)
        logger.info("已订阅币安行情", symbols=symbols, stream_count=len(streams))

    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        if not self._ws_client.is_connected:
            return

        streams = self._build_streams(symbols)

        self._sub_id += 1
        await self._ws_client.send({
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        })
        self._subscriptions.difference_update(symbols)
        logger.info("已取消订阅币安行情", symbols=symbols)

    async def _on_connect(self) -> None:
        """连接成功回调：重新订阅"""
        if self._subscriptions:
            await self.subscribe(list(self._subscriptions))

    async def _on_message(self, data: dict[str, Any]) -> None:
        """
        消息分发（模板方法）：解析消息类型并发布对应事件
        """
        if "e" in data:
            event_type = data["e"]
            if event_type == "trade":
                tick_data = BinanceDataConverter.convert_trade_data(data)
                await self._publish(MarketEventType.TICK, tick_data, symbol=tick_data.get("symbol", ""))
            elif event_type == "24hrTicker":
                ticker_data = BinanceDataConverter.convert_ticker_data(data)
                await self._publish(MarketEventType.TICK, ticker_data, symbol=ticker_data.get("symbol", ""))
            elif event_type == "depthUpdate":
                depth_data = BinanceDataConverter.convert_depth_data(data)
                await self._publish(MarketEventType.DEPTH, depth_data, symbol=depth_data.get("symbol", ""))
            elif event_type == "kline":
                kline_data = BinanceDataConverter.convert_kline_data(data)
                await self._publish(MarketEventType.KLINE, kline_data, symbol=kline_data.get("symbol", ""))
        elif "result" in data:
            logger.info("币安订阅响应", result=data.get("result"), id=data.get("id"))
        elif "lastUpdateId" in data and ("bids" in data or "asks" in data):
            depth_data = BinanceDataConverter.convert_depth_data(data)
            # 从 _stream 字段解析 symbol
            stream_name = data.get("_stream", "")
            symbol = stream_name.split("@")[0].upper() if stream_name else ""
            if not symbol and len(self._subscriptions) == 1:
                symbol = list(self._subscriptions)[0].upper().replace("/", "")
            depth_data["symbol"] = symbol
            await self._publish(MarketEventType.DEPTH, depth_data, symbol=symbol)
