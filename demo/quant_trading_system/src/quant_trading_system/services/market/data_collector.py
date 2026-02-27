"""
数据采集器模块
==============

实现多交易所数据采集，支持：
- WebSocket 实时数据订阅
- REST API 历史数据获取
- 断线重连机制
- 数据质量监控
- TimescaleDB 实时数据存储
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import structlog

from quant_trading_system.core.config import settings
from quant_trading_system.services.database.data_store import get_data_store
from quant_trading_system.services.market.common_utils import (
    TimeUtils,
    BinanceDataConverter,
    BinanceConfig,
    OKXDataConverter,
    OKXConfig
)

logger = structlog.get_logger(__name__)


# 数据回调类型
DataCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


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
    WebSocket 客户端基类

    提供通用的 WebSocket 连接管理
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

        # 回调函数
        self._on_message: DataCallback | None = None
        self._on_connect: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._on_disconnect: Callable[[], Coroutine[Any, Any, None]] | None = None

        # 统计信息
        self.stats = ConnectionStats()

        # 任务
        self._receive_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None

    def set_callbacks(
        self,
        on_message: DataCallback | None = None,
        on_connect: Callable[[], Coroutine[Any, Any, None]] | None = None,
        on_disconnect: Callable[[], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        """设置回调函数"""
        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        if self._connected:
            logger.info(f"WebSocket already connected, skipping", name=self.name)
            return True

        try:
            import websockets

            logger.info(f"WebSocket connecting...", name=self.name, url=self.url)

            self._ws = await websockets.connect(
                self.url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
            )

            self._connected = True
            self._running = True
            self._reconnect_count = 0
            self.stats.connect_count += 1

            logger.info(f"WebSocket connected successfully", name=self.name, url=self.url)

            # 启动接收任务
            self._receive_task = asyncio.create_task(
                self._receive_loop(),
                name=f"{self.name}-receive"
            )

            # 启动心跳任务
            self._heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(),
                name=f"{self.name}-heartbeat"
            )

            # 调用连接回调
            if self._on_connect:
                await self._on_connect()

            return True

        except Exception as e:
            logger.error(f"WebSocket connect failed",
                        name=self.name,
                        url=self.url,
                        error=str(e),
                        error_type=type(e).__name__)
            self.stats.error_count += 1
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False

        # 取消任务
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # 关闭连接
        if self._ws:
            await self._ws.close()
            self._ws = None

        self._connected = False
        self.stats.disconnect_count += 1

        logger.info(f"WebSocket disconnected", name=self.name)

        if self._on_disconnect:
            await self._on_disconnect()

    async def send(self, data: dict[str, Any] | str) -> bool:
        """发送数据"""
        if not self._connected or not self._ws:
            return False

        try:
            if isinstance(data, dict):
                await self._ws.send(json.dumps(data))
            else:
                await self._ws.send(data)
            return True
        except Exception as e:
            logger.error(f"WebSocket send failed",
                        name=self.name,
                        error=str(e))
            self.stats.error_count += 1
            return False

    async def _receive_loop(self) -> None:
        """接收消息循环"""
        while self._running and self._connected:
            try:
                if not self._ws:
                    logger.warning(f"WebSocket object is None in receive loop", name=self.name)
                    break

                message = await self._ws.recv()
                recv_time = time.time() * 1000

                self.stats.message_count += 1
                self.stats.last_message_time = recv_time

                # 每100条消息打印一次统计
                if self.stats.message_count % 100 == 0:
                    logger.debug(f"WebSocket message stats",
                               name=self.name,
                               total_messages=self.stats.message_count,
                               avg_latency=f"{self.stats.avg_latency:.1f}ms")

                # 解析消息
                if isinstance(message, str):
                    data = json.loads(message)
                else:
                    data = json.loads(message.decode())

                # 处理 combined stream 格式
                # combined stream 消息格式: {"stream": "btcusdt@depth20@100ms", "data": {...}}
                if "stream" in data and "data" in data:
                    stream_name = data["stream"]
                    inner_data = data["data"]
                    # 将 stream 名称注入到内层数据中，便于后续识别 symbol
                    inner_data["_stream"] = stream_name
                    data = inner_data

                # 计算延迟
                if "T" in data or "timestamp" in data:
                    msg_time = data.get("T") or data.get("timestamp")
                    if msg_time:
                        latency = recv_time - msg_time
                        self.stats.latency_sum += latency
                        self.stats.latency_count += 1

                # 调用消息回调
                if self._on_message:
                    await self._on_message(data)

            except asyncio.CancelledError:
                logger.info(f"WebSocket receive loop cancelled", name=self.name)
                break
            except Exception as e:
                logger.error(f"WebSocket receive error",
                           name=self.name,
                           error=str(e),
                           error_type=type(e).__name__)
                self.stats.error_count += 1

                # 尝试重连
                if self._running:
                    logger.info(f"Attempting reconnect after receive error", name=self.name)
                    await self._reconnect()
                break

    async def _heartbeat_loop(self) -> None:
        """心跳循环"""
        while self._running and self._connected:
            try:
                await asyncio.sleep(self.ping_interval)

                if self._ws and self._connected:
                    # 发送ping
                    pong = await self._ws.ping()
                    await asyncio.wait_for(pong, timeout=self.ping_timeout)

            except asyncio.TimeoutError:
                logger.warning(f"WebSocket ping timeout", name=self.name)
                if self._running:
                    await self._reconnect()
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"WebSocket heartbeat error",
                           name=self.name,
                           error=str(e))

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

            logger.debug(f"Reconnecting WebSocket",
                       name=self.name,
                       attempt=self._reconnect_count)

            await asyncio.sleep(self.reconnect_delay)

            if await self.connect():
                return

        logger.error(f"Max reconnect attempts reached", name=self.name)

    @property
    def is_connected(self) -> bool:
        return self._connected


class DataCollector(ABC):
    """
    数据采集器抽象基类

    定义数据采集的标准接口
    """

    def __init__(self, name: str = "collector", enable_storage: bool = True) -> None:
        self.name = name
        self._running = False
        self._subscriptions: set[str] = set()
        self.enable_storage = enable_storage

        # 数据回调
        self._callbacks: dict[str, list[DataCallback]] = defaultdict(list)

        # 数据存储服务
        self._data_store = None
        if enable_storage:
            self._data_store = get_data_store()

    @abstractmethod
    async def start(self) -> None:
        """启动采集器"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """停止采集器"""
        pass

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """订阅品种"""
        pass

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        pass

    def add_callback(
        self,
        data_type: str,
        callback: DataCallback
    ) -> None:
        """添加数据回调"""
        self._callbacks[data_type].append(callback)

    def remove_callback(
        self,
        data_type: str,
        callback: DataCallback
    ) -> None:
        """移除数据回调"""
        if callback in self._callbacks[data_type]:
            self._callbacks[data_type].remove(callback)

    async def _notify(self, data_type: str, data: dict[str, Any]) -> None:
        """通知所有回调"""
        callbacks = self._callbacks.get(data_type, [])
        if callbacks:
            await asyncio.gather(
                *[cb(data) for cb in callbacks],
                return_exceptions=True
            )

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def subscriptions(self) -> set[str]:
        return self._subscriptions.copy()


class BinanceDataCollector(DataCollector):
    """
    币安数据采集器

    支持现货和期货数据采集
    """

    def __init__(
        self,
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
        enable_storage: bool = True,
    ) -> None:
        super().__init__(name="binance", enable_storage=enable_storage)

        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret

        # 使用共享配置获取WebSocket端点
        ws_url = BinanceConfig.get_ws_url(market_type)

        # WebSocket客户端
        self._ws_client = WebSocketClient(
            url=ws_url,
            name=f"binance-{market_type}",
        )
        self._ws_client.set_callbacks(
            on_message=self._on_message,
            on_connect=self._on_connect,
        )

        # 订阅ID计数
        self._sub_id = 0

    async def start(self) -> None:
        """启动采集器"""
        if self._running:
            logger.info(f"Binance data collector already running, skipping start",
                       market_type=self.market_type)
            return

        self._running = True

        # 启动数据存储服务
        if self.enable_storage and self._data_store:
            logger.info(f"Starting data store service", market_type=self.market_type)
            await self._data_store.start()

        logger.info(f"Connecting WebSocket for Binance",
                   market_type=self.market_type,
                   ws_url=self._ws_client.url)
        connect_result = await self._ws_client.connect()

        logger.info(f"Binance data collector started",
                   market_type=self.market_type,
                   storage_enabled=self.enable_storage,
                   ws_connected=connect_result,
                   ws_url=self._ws_client.url)

    async def stop(self) -> None:
        """停止采集器"""
        self._running = False
        await self._ws_client.disconnect()

        # 关闭数据存储服务
        if self.enable_storage and self._data_store:
            await self._data_store.stop()

        logger.info(f"Binance data collector stopped")

    async def subscribe(self, symbols: list[str]) -> None:
        """订阅品种"""
        logger.info(f"BinanceDataCollector.subscribe called",
                   symbols=symbols,
                   ws_connected=self._ws_client.is_connected,
                   ws_url=self._ws_client.url,
                   running=self._running)
        if not self._ws_client.is_connected:
            logger.warning(f"WebSocket not connected, cannot subscribe",
                          symbols=symbols,
                          ws_url=self._ws_client.url,
                          reconnect_count=self._ws_client._reconnect_count)
            return

        # 构建订阅参数（根据配置开关决定订阅哪些数据流）
        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")
            if settings.SYNC_TICK:
                streams.extend([
                    f"{symbol_lower}@trade",        # 逐笔成交
                    f"{symbol_lower}@ticker",       # 24小时行情
                ])
            if settings.SYNC_DEPTH:
                streams.append(f"{symbol_lower}@depth20@100ms")  # 深度数据
            if settings.SYNC_KLINE:
                streams.extend([
                    f"{symbol_lower}@kline_1m",     # 1分钟K线
                    f"{symbol_lower}@kline_5m",     # 5分钟K线
                    f"{symbol_lower}@kline_15m",    # 15分钟K线
                    f"{symbol_lower}@kline_30m",    # 30分钟K线
                    f"{symbol_lower}@kline_1h",     # 1小时K线
                    f"{symbol_lower}@kline_2h",     # 2小时K线
                    f"{symbol_lower}@kline_4h",     # 4小时K线
                    f"{symbol_lower}@kline_6h",     # 6小时K线
                    f"{symbol_lower}@kline_8h",     # 8小时K线
                    f"{symbol_lower}@kline_12h",    # 12小时K线
                    f"{symbol_lower}@kline_1d",     # 1天K线
                    f"{symbol_lower}@kline_3d",     # 3天K线
                    f"{symbol_lower}@kline_1w",     # 1周K线
                    f"{symbol_lower}@kline_1M",     # 1月K线
                ])

        if not streams:
            logger.warning("No data streams to subscribe (all sync options are disabled)",
                          symbols=symbols)
            self._subscriptions.update(symbols)
            return

        self._sub_id += 1

        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        }

        # 发送订阅请求
        logger.info(f"Sending subscribe request to Binance WebSocket",
                   sub_id=self._sub_id,
                   stream_count=len(streams),
                   streams=streams)
        send_result = await self._ws_client.send(subscribe_msg)
        logger.info(f"Subscribe request sent",
                   send_result=send_result,
                   sub_id=self._sub_id)

        self._subscriptions.update(symbols)
        logger.info(f"Subscribed to symbols with kline data",
                   symbols=symbols,
                   stream_count=len(streams))

    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        if not self._ws_client.is_connected:
            return

        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")
            if settings.SYNC_TICK:
                streams.extend([
                    f"{symbol_lower}@trade",
                    f"{symbol_lower}@ticker",
                ])
            if settings.SYNC_DEPTH:
                streams.append(f"{symbol_lower}@depth20@100ms")
            if settings.SYNC_KLINE:
                streams.extend([
                    f"{symbol_lower}@kline_1m",     # 1分钟K线
                    f"{symbol_lower}@kline_5m",     # 5分钟K线
                    f"{symbol_lower}@kline_15m",    # 15分钟K线
                    f"{symbol_lower}@kline_30m",    # 30分钟K线
                    f"{symbol_lower}@kline_1h",     # 1小时K线
                    f"{symbol_lower}@kline_2h",     # 2小时K线
                    f"{symbol_lower}@kline_4h",     # 4小时K线
                    f"{symbol_lower}@kline_6h",     # 6小时K线
                    f"{symbol_lower}@kline_8h",     # 8小时K线
                    f"{symbol_lower}@kline_12h",    # 12小时K线
                    f"{symbol_lower}@kline_1d",     # 1天K线
                    f"{symbol_lower}@kline_3d",     # 3天K线
                    f"{symbol_lower}@kline_1w",     # 1周K线
                    f"{symbol_lower}@kline_1M",     # 1月K线
                ])

        self._sub_id += 1

        await self._ws_client.send({
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        })

        self._subscriptions.difference_update(symbols)
        logger.info(f"Unsubscribed from symbols",
                   symbols=symbols,
                   stream_count=len(streams))

    async def _on_connect(self) -> None:
        """连接成功回调"""
        logger.info(f"Binance WebSocket on_connect callback fired",
                   existing_subscriptions=list(self._subscriptions))
        # 重新订阅
        if self._subscriptions:
            logger.info(f"Re-subscribing existing symbols after reconnect",
                       symbols=list(self._subscriptions))
            await self.subscribe(list(self._subscriptions))

    async def _on_message(self, data: dict[str, Any]) -> None:
        """消息处理回调"""
        # 处理不同类型的消息
        if "e" in data:
            event_type = data["e"]
            if event_type == "trade":
                await self._process_trade(data)
            elif event_type == "24hrTicker":
                await self._process_ticker(data)
            elif event_type == "depthUpdate":
                await self._process_depth(data)
            elif event_type == "kline":
                await self._process_kline(data)
            else:
                logger.debug(f"Unhandled event type",
                           event_type=event_type,
                           data=data)
        elif "result" in data:
            # 订阅/取消订阅的响应
            logger.info(f"Binance subscription response",
                       result=data.get("result"),
                       id=data.get("id"))
        elif "lastUpdateId" in data and ("bids" in data or "asks" in data):
            # depth20@100ms 有限档深度信息流（无 "e" 字段）
            await self._process_depth(data)
        else:
            logger.debug(f"Binance unknown message format",
                        data_keys=list(data.keys()),
                        data=data)

    async def _process_trade(self, data: dict[str, Any]) -> None:
        """处理成交数据"""
        from quant_trading_system.models.market import Tick

        # 使用共享工具转换数据
        tick_data = BinanceDataConverter.convert_trade_data(data)

        # 创建Tick对象
        tick = Tick(
            timestamp=tick_data["timestamp"],
            symbol=tick_data["symbol"],
            exchange="binance",
            last_price=tick_data["last_price"],
            price=tick_data["last_price"],
            volume=tick_data["volume"],
            bid=0.0,
            ask=0.0,
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", tick_data)

    async def _process_ticker(self, data: dict[str, Any]) -> None:
        """处理Ticker数据"""
        from quant_trading_system.models.market import Tick

        # 使用共享工具转换数据
        tick_data = BinanceDataConverter.convert_ticker_data(data)

        # 创建Tick对象
        tick = Tick(
            timestamp=tick_data["timestamp"],
            symbol=tick_data["symbol"],
            exchange="binance",
            last_price=tick_data["last_price"],
            price=tick_data["last_price"],
            volume=tick_data["volume"],
            bid=tick_data["bid_price"],
            ask=tick_data["ask_price"],
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", tick_data)

    async def _process_depth(self, data: dict[str, Any]) -> None:
        """处理深度数据（兼容增量深度流和有限档深度流）"""
        from datetime import datetime
        from quant_trading_system.models.market import Depth

        # 使用共享工具转换数据
        depth_data = BinanceDataConverter.convert_depth_data(data)

        # 对于有限档深度流，symbol 需要从 stream 名称中解析
        symbol = depth_data["symbol"]
        if not symbol:
            # 从 _stream 字段解析 symbol（combined stream 注入）
            # stream 格式示例: "btcusdt@depth20@100ms"
            stream_name = data.get("_stream", "")
            if stream_name:
                symbol = stream_name.split("@")[0].upper()
            elif self._subscriptions and len(self._subscriptions) == 1:
                symbol = list(self._subscriptions)[0].upper().replace("/", "")
            else:
                logger.warning("Cannot determine symbol for depth data",
                             stream=stream_name,
                             subscriptions=list(self._subscriptions))
                return

        # 创建Depth对象
        depth = Depth(
            timestamp=TimeUtils.timestamp_to_datetime(depth_data["timestamp"]) if depth_data["timestamp"] else datetime.now(),
            symbol=symbol,
            exchange="binance",
            bids=depth_data["bids"],
            asks=depth_data["asks"],
            sequence=depth_data.get("sequence"),
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_depth(depth)

        await self._notify("depth", depth_data)

    async def _process_kline(self, data: dict[str, Any]) -> None:
        """处理 Binance K线数据"""
        from quant_trading_system.models.market import Bar, TimeFrame

        kline_data = BinanceDataConverter.convert_kline_data(data)
        if not kline_data or not kline_data.get("symbol"):
            logger.warning("Invalid Binance kline data", data=data)
            return

        # 创建Bar对象
        bar = Bar(
            timestamp=kline_data["timestamp"],
            symbol=kline_data["symbol"],
            exchange="binance",
            timeframe=TimeFrame(kline_data["interval"]),
            open=kline_data["open"],
            high=kline_data["high"],
            low=kline_data["low"],
            close=kline_data["close"],
            volume=kline_data["volume"],
            is_closed=kline_data["is_closed"],
        )

        # 存储到数据库（仅已关闭的K线）
        if bar.is_closed and self.enable_storage and self._data_store:
            await self._data_store.store_kline(bar)

        logger.debug(f"Processed Binance kline data",
                   symbol=kline_data["symbol"],
                   interval=kline_data["interval"],
                   open=kline_data["open"],
                   close=kline_data["close"],
                   is_closed=kline_data["is_closed"])

        await self._notify("kline", kline_data)


class OKXDataCollector(DataCollector):
    """
    OKX 数据采集器
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = "",
        enable_storage: bool = True,
    ) -> None:
        super().__init__(name="okx", enable_storage=enable_storage)

        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

        # 使用共享配置获取WebSocket端点
        ws_url = OKXConfig.get_ws_url()

        self._ws_client = WebSocketClient(
            url=ws_url,
            name="okx",
        )
        self._ws_client.set_callbacks(
            on_message=self._on_message,
            on_connect=self._on_connect,
        )

    async def start(self) -> None:
        if self._running:
            return

        self._running = True

        # 启动数据存储服务
        if self.enable_storage and self._data_store:
            await self._data_store.start()

        await self._ws_client.connect()

        logger.info("OKX data collector started", storage_enabled=self.enable_storage)

    async def stop(self) -> None:
        self._running = False
        await self._ws_client.disconnect()

        # 关闭数据存储服务
        if self.enable_storage and self._data_store:
            await self._data_store.stop()

        logger.info("OKX data collector stopped")

    async def subscribe(self, symbols: list[str]) -> None:
        if not self._ws_client.is_connected:
            return

        # 根据配置开关决定订阅哪些频道
        args = []
        for symbol in symbols:
            inst_id = symbol.replace("/", "-")
            if settings.SYNC_TICK:
                args.extend([
                    {"channel": "trades", "instId": inst_id},
                    {"channel": "tickers", "instId": inst_id},
                ])
            if settings.SYNC_DEPTH:
                args.append({"channel": "books5", "instId": inst_id})
            if settings.SYNC_KLINE:
                args.extend([
                    {"channel": "candle1m", "instId": inst_id},  # 1分钟K线
                    {"channel": "candle5m", "instId": inst_id},  # 5分钟K线
                    {"channel": "candle15m", "instId": inst_id}, # 15分钟K线
                    {"channel": "candle1H", "instId": inst_id},  # 1小时K线
                ])

        if not args:
            logger.warning("No channels to subscribe (all sync options are disabled)",
                          symbols=symbols)
            self._subscriptions.update(symbols)
            return

        await self._ws_client.send({
            "op": "subscribe",
            "args": args,
        })

        self._subscriptions.update(symbols)
        logger.info(f"Subscribed to symbols",
                   symbols=symbols,
                   channel_count=len(args),
                   sync_tick=settings.SYNC_TICK,
                   sync_depth=settings.SYNC_DEPTH,
                   sync_kline=settings.SYNC_KLINE)

    async def unsubscribe(self, symbols: list[str]) -> None:
        if not self._ws_client.is_connected:
            return

        args = []
        for symbol in symbols:
            inst_id = symbol.replace("/", "-")
            if settings.SYNC_TICK:
                args.extend([
                    {"channel": "trades", "instId": inst_id},
                    {"channel": "tickers", "instId": inst_id},
                ])
            if settings.SYNC_DEPTH:
                args.append({"channel": "books5", "instId": inst_id})
            if settings.SYNC_KLINE:
                args.extend([
                    {"channel": "candle1m", "instId": inst_id},
                    {"channel": "candle5m", "instId": inst_id},
                    {"channel": "candle15m", "instId": inst_id},
                    {"channel": "candle1H", "instId": inst_id},
                ])

        await self._ws_client.send({
            "op": "unsubscribe",
            "args": args,
        })

        self._subscriptions.difference_update(symbols)
        logger.info(f"Unsubscribed from symbols",
                   symbols=symbols,
                   channel_count=len(args))

    async def _on_connect(self) -> None:
        if self._subscriptions:
            await self.subscribe(list(self._subscriptions))

    async def _on_message(self, data: dict[str, Any]) -> None:
        if "arg" not in data or "data" not in data:
            return

        channel = data["arg"].get("channel", "")

        # 记录接收到的消息
        logger.debug(f"Received OKX WebSocket message",
                    channel=channel,
                    data=data)

        if channel == "trades":
            await self._process_trades(data)
        elif channel == "tickers":
            await self._process_ticker(data)
        elif channel == "books5":
            await self._process_depth(data)
        elif channel.startswith("candle"):
            await self._process_kline(data)
        else:
            logger.debug(f"Unhandled channel type",
                       channel=channel,
                       data=data)

    async def _process_trades(self, data: dict[str, Any]) -> None:
        from quant_trading_system.models.market import Tick

        # 使用共享工具转换数据
        trade_data = OKXDataConverter.convert_trade_data(data)

        # 创建Tick对象
        tick = Tick(
            timestamp=trade_data["timestamp"],
            symbol=trade_data["symbol"],
            exchange="okx",
            last_price=trade_data["last_price"],
            price=trade_data["last_price"],
            volume=trade_data["volume"],
            bid=0.0,
            ask=0.0,
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", trade_data)

    async def _process_ticker(self, data: dict[str, Any]) -> None:
        from quant_trading_system.models.market import Tick

        # 使用共享工具转换数据
        ticker_data = OKXDataConverter.convert_ticker_data(data)

        # 创建Tick对象
        tick = Tick(
            timestamp=ticker_data["timestamp"],
            symbol=ticker_data["symbol"],
            exchange="okx",
            last_price=ticker_data["last_price"],
            price=ticker_data["last_price"],
            volume=ticker_data["volume"],
            bid=ticker_data["bid_price"],
            ask=ticker_data["ask_price"],
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", ticker_data)

    async def _process_depth(self, data: dict[str, Any]) -> None:
        from datetime import datetime
        from quant_trading_system.models.market import Depth

        # 使用共享工具转换数据
        depth_data = OKXDataConverter.convert_depth_data(data)

        # 创建Depth对象
        depth = Depth(
            timestamp=datetime.fromtimestamp(depth_data["timestamp"] / 1000),
            symbol=depth_data["symbol"],
            exchange="okx",
            bids=depth_data["bids"],
            asks=depth_data["asks"],
        )

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_depth(depth)

        await self._notify("depth", depth_data)
