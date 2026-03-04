"""
交易所连接器
============

纯粹负责对接交易所，职责单一：
- WebSocket 实时数据流连接与订阅管理
- 将交易所原始数据转换为统一格式后，通过事件总线发布

设计原则：
- 单一职责原则（SRP）：只处理交易所通信，不关心数据如何消费
- 适配器模式（Adapter Pattern）：将不同交易所的API统一适配为内部标准接口
- 模板方法模式（Template Method Pattern）：基类定义流程骨架，子类实现具体细节

每个交易所对应一个 Connector 子类，所有子类共享：
- WebSocket 连接管理（连接、断线重连、心跳）
- 消息接收与解析流程
- 通过 MarketEventBus 发布行情事件
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
)
from quant_trading_system.exchange_adapter.binance_base import (
    BinanceConfig,
    BinanceDataConverter,
)
from quant_trading_system.exchange_adapter.ws_client import WebSocketClient

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 交易所连接器抽象基类
# ═══════════════════════════════════════════════════════════════

class ExchangeConnector(ABC):
    """
    交易所连接器抽象基类（适配器模式 + 模板方法模式）

    职责：
    1. 管理与交易所的 WebSocket 连接
    2. 接收交易所推送的原始数据
    3. 将数据转换为统一格式
    4. 通过 MarketEventBus 发布事件

    不负责：
    - 数据存储（由 DatabaseSubscriber 处理）
    - WebSocket 前端推送（由 WebSocketSubscriber 处理）
    - 交易信号计算（由 TradingEngineSubscriber 处理）
    """

    def __init__(self, name: str, event_bus: MarketEventBus) -> None:
        self._name = name
        self._event_bus = event_bus
        self._running = False
        self._subscriptions: set[str] = set()

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def start(self) -> None:
        """启动连接器"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止连接器"""
        ...

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """订阅交易对"""
        ...

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        ...

    async def _publish(
        self,
        event_type: MarketEventType,
        data: dict[str, Any],
        exchange: str = "",
        symbol: str = "",
    ) -> None:
        """便捷方法：发布事件到事件总线"""
        event = MarketEvent(
            type=event_type,
            data=data,
            exchange=exchange or self._name,
            symbol=symbol,
        )
        await self._event_bus.publish(event)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def subscriptions(self) -> set[str]:
        return self._subscriptions.copy()


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
