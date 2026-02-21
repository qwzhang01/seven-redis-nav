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

from quant_trading_system.services.database.data_store import get_data_store

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

            logger.info(f"WebSocket connected", name=self.name, url=self.url)

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
                        error=str(e))
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
                    break

                message = await self._ws.recv()
                recv_time = time.time() * 1000

                self.stats.message_count += 1
                self.stats.last_message_time = recv_time

                # 解析消息
                if isinstance(message, str):
                    data = json.loads(message)
                else:
                    data = json.loads(message.decode())

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
                break
            except Exception as e:
                logger.error(f"WebSocket receive error",
                           name=self.name,
                           error=str(e))
                self.stats.error_count += 1

                # 尝试重连
                if self._running:
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

            logger.info(f"Reconnecting WebSocket",
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

    # WebSocket 端点
    SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
    FUTURES_WS_URL = "wss://fstream.binance.com/ws"

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

        # 选择WebSocket端点
        if market_type == "spot":
            ws_url = self.SPOT_WS_URL
        else:
            ws_url = self.FUTURES_WS_URL

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
            return

        self._running = True

        # 启动数据存储服务
        if self.enable_storage and self._data_store:
            await self._data_store.start()

        await self._ws_client.connect()

        logger.info(f"Binance data collector started",
                   market_type=self.market_type,
                   storage_enabled=self.enable_storage)

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
        if not self._ws_client.is_connected:
            return

        # 构建订阅参数
        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")
            streams.extend([
                f"{symbol_lower}@trade",        # 逐笔成交
                f"{symbol_lower}@ticker",       # 24小时行情
                f"{symbol_lower}@depth20@100ms", # 深度数据
            ])

        self._sub_id += 1

        # 发送订阅请求
        await self._ws_client.send({
            "method": "SUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        })

        self._subscriptions.update(symbols)
        logger.info(f"Subscribed to symbols", symbols=symbols)

    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        if not self._ws_client.is_connected:
            return

        streams = []
        for symbol in symbols:
            symbol_lower = symbol.lower().replace("/", "")
            streams.extend([
                f"{symbol_lower}@trade",
                f"{symbol_lower}@ticker",
                f"{symbol_lower}@depth20@100ms",
            ])

        self._sub_id += 1

        await self._ws_client.send({
            "method": "UNSUBSCRIBE",
            "params": streams,
            "id": self._sub_id,
        })

        self._subscriptions.difference_update(symbols)
        logger.info(f"Unsubscribed from symbols", symbols=symbols)

    async def _on_connect(self) -> None:
        """连接成功回调"""
        # 重新订阅
        if self._subscriptions:
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

    async def _process_trade(self, data: dict[str, Any]) -> None:
        """处理成交数据"""
        from datetime import datetime
        from quant_trading_system.models.market import Tick

        # 创建Tick对象
        tick = Tick(
            timestamp=datetime.fromtimestamp(data["T"] / 1000),
            symbol=data["s"],
            price=float(data["p"]),
            volume=float(data["q"]),
            bid=0.0,
            ask=0.0,
        )

        tick_data = {
            "symbol": data["s"],
            "exchange": "binance",
            "timestamp": data["T"],
            "last_price": float(data["p"]),
            "volume": float(data["q"]),
            "is_trade": True,
            "trade_id": str(data["t"]),
        }

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", tick_data)

    async def _process_ticker(self, data: dict[str, Any]) -> None:
        """处理Ticker数据"""
        from datetime import datetime
        from quant_trading_system.models.market import Tick

        # 创建Tick对象
        tick = Tick(
            timestamp=datetime.fromtimestamp(data["E"] / 1000),
            symbol=data["s"],
            price=float(data["c"]),
            volume=float(data["v"]),
            bid=float(data["b"]),
            ask=float(data["a"]),
        )

        tick_data = {
            "symbol": data["s"],
            "exchange": "binance",
            "timestamp": data["E"],
            "last_price": float(data["c"]),
            "bid_price": float(data["b"]),
            "ask_price": float(data["a"]),
            "bid_size": float(data["B"]),
            "ask_size": float(data["A"]),
            "volume": float(data["v"]),
            "turnover": float(data["q"]),
            "is_trade": False,
        }

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_tick(tick)

        await self._notify("tick", tick_data)

    async def _process_depth(self, data: dict[str, Any]) -> None:
        """处理深度数据"""
        from datetime import datetime
        from quant_trading_system.models.market import Depth

        # 创建Depth对象
        depth = Depth(
            timestamp=datetime.fromtimestamp(data["E"] / 1000),
            symbol=data["s"],
            bids=[[float(p), float(q)] for p, q in data.get("b", [])],
            asks=[[float(p), float(q)] for p, q in data.get("a", [])],
        )

        depth_data = {
            "symbol": data["s"],
            "exchange": "binance",
            "timestamp": data["E"],
            "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
        }

        # 存储到数据库
        if self.enable_storage and self._data_store:
            await self._data_store.store_depth(depth)

        await self._notify("depth", depth_data)


class OKXDataCollector(DataCollector):
    """
    OKX 数据采集器
    """

    WS_URL = "wss://ws.okx.com:8443/ws/v5/public"

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

        self._ws_client = WebSocketClient(
            url=self.WS_URL,
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

        args = []
        for symbol in symbols:
            inst_id = symbol.replace("/", "-")
            args.extend([
                {"channel": "trades", "instId": inst_id},
                {"channel": "tickers", "instId": inst_id},
                {"channel": "books5", "instId": inst_id},
            ])

        await self._ws_client.send({
            "op": "subscribe",
            "args": args,
        })

        self._subscriptions.update(symbols)

    async def unsubscribe(self, symbols: list[str]) -> None:
        if not self._ws_client.is_connected:
            return

        args = []
        for symbol in symbols:
            inst_id = symbol.replace("/", "-")
            args.extend([
                {"channel": "trades", "instId": inst_id},
                {"channel": "tickers", "instId": inst_id},
                {"channel": "books5", "instId": inst_id},
            ])

        await self._ws_client.send({
            "op": "unsubscribe",
            "args": args,
        })

        self._subscriptions.difference_update(symbols)

    async def _on_connect(self) -> None:
        if self._subscriptions:
            await self.subscribe(list(self._subscriptions))

    async def _on_message(self, data: dict[str, Any]) -> None:
        if "arg" not in data or "data" not in data:
            return

        channel = data["arg"].get("channel", "")

        if channel == "trades":
            await self._process_trades(data)
        elif channel == "tickers":
            await self._process_ticker(data)
        elif channel == "books5":
            await self._process_depth(data)

    async def _process_trades(self, data: dict[str, Any]) -> None:
        from datetime import datetime
        from quant_trading_system.models.market import Tick

        inst_id = data["arg"]["instId"]
        symbol = inst_id.replace("-", "/")

        for trade in data["data"]:
            # 创建Tick对象
            tick = Tick(
                timestamp=datetime.fromtimestamp(int(trade["ts"]) / 1000),
                symbol=symbol,
                price=float(trade["px"]),
                volume=float(trade["sz"]),
                bid=0.0,
                ask=0.0,
            )

            tick_data = {
                "symbol": symbol,
                "exchange": "okx",
                "timestamp": int(trade["ts"]),
                "last_price": float(trade["px"]),
                "volume": float(trade["sz"]),
                "is_trade": True,
                "trade_id": trade["tradeId"],
            }

            # 存储到数据库
            if self.enable_storage and self._data_store:
                await self._data_store.store_tick(tick)

            await self._notify("tick", tick_data)

    async def _process_ticker(self, data: dict[str, Any]) -> None:
        from datetime import datetime
        from quant_trading_system.models.market import Tick

        inst_id = data["arg"]["instId"]
        symbol = inst_id.replace("-", "/")

        for ticker in data["data"]:
            # 创建Tick对象
            tick = Tick(
                timestamp=datetime.fromtimestamp(int(ticker["ts"]) / 1000),
                symbol=symbol,
                price=float(ticker["last"]),
                volume=float(ticker["vol24h"]),
                bid=float(ticker["bidPx"]),
                ask=float(ticker["askPx"]),
            )

            tick_data = {
                "symbol": symbol,
                "exchange": "okx",
                "timestamp": int(ticker["ts"]),
                "last_price": float(ticker["last"]),
                "bid_price": float(ticker["bidPx"]),
                "ask_price": float(ticker["askPx"]),
                "bid_size": float(ticker["bidSz"]),
                "ask_size": float(ticker["askSz"]),
                "volume": float(ticker["vol24h"]),
                "is_trade": False,
            }

            # 存储到数据库
            if self.enable_storage and self._data_store:
                await self._data_store.store_tick(tick)

            await self._notify("tick", tick_data)

    async def _process_depth(self, data: dict[str, Any]) -> None:
        from datetime import datetime
        from quant_trading_system.models.market import Depth

        inst_id = data["arg"]["instId"]
        symbol = inst_id.replace("-", "/")

        for book in data["data"]:
            # 创建Depth对象
            depth = Depth(
                timestamp=datetime.fromtimestamp(int(book["ts"]) / 1000),
                symbol=symbol,
                bids=[[float(b[0]), float(b[1])] for b in book.get("bids", [])],
                asks=[[float(a[0]), float(a[1])] for a in book.get("asks", [])],
            )

            depth_data = {
                "symbol": symbol,
                "exchange": "okx",
                "timestamp": int(book["ts"]),
                "bids": [[float(b[0]), float(b[1])] for b in book.get("bids", [])],
                "asks": [[float(a[0]), float(a[1])] for a in book.get("asks", [])],
            }

            # 存储到数据库
            if self.enable_storage and self._data_store:
                await self._data_store.store_depth(depth)

            await self._notify("depth", depth_data)
