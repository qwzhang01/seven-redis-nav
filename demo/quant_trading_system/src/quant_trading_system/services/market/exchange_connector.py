"""
交易所连接器
============

纯粹负责对接交易所，职责单一：
- WebSocket 实时数据流连接与订阅管理
- REST API 历史数据拉取
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

import asyncio
import json
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
)
from quant_trading_system.services.market.common_utils import (
    BinanceConfig,
    BinanceDataConverter,
)

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# WebSocket 客户端（保持原有稳定实现）
# ═══════════════════════════════════════════════════════════════

@dataclass
class ConnectionStats:
    """连接统计"""
    connect_count: int = 0
    disconnect_count: int = 0
    reconnect_count: int = 0
    message_count: int = 0
    error_count: int = 0
    last_message_time: float = 0.0
    latency_sum: float = 0.0
    latency_count: int = 0

    @property
    def avg_latency(self) -> float:
        if self.latency_count > 0:
            return self.latency_sum / self.latency_count
        return 0.0


class WebSocketClient:
    """
    WebSocket 客户端

    提供通用的 WebSocket 连接管理：连接、接收、心跳、断线重连。
    """

    def __init__(
        self,
        url: str,
        name: str = "ws_client",
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 10,
    ) -> None:
        self.url = url
        self.name = name
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._ws: Any = None
        self._connected = False
        self._running = False
        self._reconnect_count = 0

        # 消息回调
        self._on_message: Any = None
        self._on_connect: Any = None
        self._on_disconnect: Any = None

        self.stats = ConnectionStats()
        self._receive_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

    def set_callbacks(self, on_message=None, on_connect=None, on_disconnect=None):
        """设置回调函数"""
        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

    async def connect(self) -> bool:
        """连接到 WebSocket 服务器"""
        if self._connected:
            return True

        try:
            import websockets

            self._ws = await websockets.connect(
                self.url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
            )
            self._connected = True
            self._running = True
            self._reconnect_count = 0
            self.stats.connect_count += 1

            logger.info("WebSocket 已连接", name=self.name, url=self.url)

            self._receive_task = asyncio.create_task(
                self._receive_loop(), name=f"{self.name}-receive"
            )
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(), name=f"{self.name}-heartbeat"
            )

            if self._on_connect:
                await self._on_connect()

            return True

        except Exception as e:
            logger.error("WebSocket 连接失败", name=self.name, error=str(e))
            self.stats.error_count += 1
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False

        for task in [self._receive_task, self._heartbeat_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        self._connected = False
        self.stats.disconnect_count += 1
        logger.info("WebSocket 已断开", name=self.name)

        if self._on_disconnect:
            await self._on_disconnect()

    async def send(self, data: dict[str, Any] | str) -> bool:
        """发送数据"""
        if not self._connected or not self._ws:
            return False
        try:
            msg = json.dumps(data) if isinstance(data, dict) else data
            await self._ws.send(msg)
            return True
        except Exception as e:
            logger.error("WebSocket 发送失败", name=self.name, error=str(e))
            self.stats.error_count += 1
            return False

    async def _receive_loop(self) -> None:
        """接收消息循环"""
        while self._running and self._connected:
            try:
                if not self._ws:
                    break

                message = await self._ws.recv()
                recv_time = time.time() * 1000
                self.stats.message_count += 1
                self.stats.last_message_time = recv_time

                data = json.loads(message) if isinstance(message, str) else json.loads(message.decode())

                # 处理 combined stream 格式
                if "stream" in data and "data" in data:
                    inner_data = data["data"]
                    inner_data["_stream"] = data["stream"]
                    data = inner_data

                # 计算延迟
                msg_time = data.get("T") or data.get("timestamp")
                if msg_time:
                    latency = recv_time - msg_time
                    self.stats.latency_sum += latency
                    self.stats.latency_count += 1

                if self._on_message:
                    await self._on_message(data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("WebSocket 接收异常", name=self.name, error=str(e))
                self.stats.error_count += 1
                if self._running:
                    await self._reconnect()
                break

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self._running and self._connected:
            try:
                await asyncio.sleep(self.ping_interval)
                if self._ws and self._connected:
                    pong = await self._ws.ping()
                    await asyncio.wait_for(pong, timeout=self.ping_timeout)
            except asyncio.TimeoutError:
                logger.warning("WebSocket ping 超时", name=self.name)
                if self._running:
                    await self._reconnect()
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("WebSocket 心跳异常", name=self.name, error=str(e))

    async def _reconnect(self) -> None:
        """重连"""
        if not self._running:
            return

        self._connected = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        while self._running and self._reconnect_count < self.max_reconnect_attempts:
            self._reconnect_count += 1
            self.stats.reconnect_count += 1
            logger.debug("WebSocket 重连中", name=self.name, attempt=self._reconnect_count)
            await asyncio.sleep(self.reconnect_delay)
            if await self.connect():
                return

        logger.error("WebSocket 达到最大重连次数", name=self.name)

    @property
    def is_connected(self) -> bool:
        return self._connected


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

        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")
            streams.extend([
                f"{symbol_lower}@trade",
                f"{symbol_lower}@ticker",
            ])

            streams.append(f"{symbol_lower}@depth20@100ms")

            streams.extend([
                f"{symbol_lower}@kline_1s",
                f"{symbol_lower}@kline_1m",
                f"{symbol_lower}@kline_3m",
                f"{symbol_lower}@kline_5m",
                f"{symbol_lower}@kline_15m",
                f"{symbol_lower}@kline_30m",
                f"{symbol_lower}@kline_1h",
                f"{symbol_lower}@kline_2h",
                f"{symbol_lower}@kline_4h",
                f"{symbol_lower}@kline_6h",
                f"{symbol_lower}@kline_8h",
                f"{symbol_lower}@kline_12h",
                f"{symbol_lower}@kline_1d",
                f"{symbol_lower}@kline_3d",
                f"{symbol_lower}@kline_1w",
                f"{symbol_lower}@kline_1M",
            ])

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

        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")

            streams.extend([f"{symbol_lower}@trade", f"{symbol_lower}@ticker"])

            streams.append(f"{symbol_lower}@depth20@100ms")

            streams.extend([
                f"{symbol_lower}@kline_1s", f"{symbol_lower}@kline_1m",
                f"{symbol_lower}@kline_3m", f"{symbol_lower}@kline_5m",
                f"{symbol_lower}@kline_15m", f"{symbol_lower}@kline_30m",
                f"{symbol_lower}@kline_1h", f"{symbol_lower}@kline_2h",
                f"{symbol_lower}@kline_4h", f"{symbol_lower}@kline_6h",
                f"{symbol_lower}@kline_8h", f"{symbol_lower}@kline_12h",
                f"{symbol_lower}@kline_1d", f"{symbol_lower}@kline_3d",
                f"{symbol_lower}@kline_1w", f"{symbol_lower}@kline_1M",
            ])

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


# ═══════════════════════════════════════════════════════════════
# MockConnector 已迁移至 quant_trading_system.mock.mock_connector
# 请从 quant_trading_system.mock 导入 MockConnector
# ═══════════════════════════════════════════════════════════════
