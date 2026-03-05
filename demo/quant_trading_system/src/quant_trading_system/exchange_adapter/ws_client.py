"""
通用 WebSocket 客户端
====================

提供通用的 WebSocket 连接管理：连接、接收、心跳、断线重连。
不绑定任何特定交易所，可被任何 WebSocket 场景复用。
"""

import asyncio
import json
import ssl
import time
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger(__name__)
# 修复 websockets 13.x 在 Python 3.12.7+ 上的 AttributeError('characters_written')
# 原因：Python 3.12.7 移除了 StreamWriter.characters_written，websockets 13.x 仍在访问
# 升级 websockets>=14.0 后可删除此补丁
if not hasattr(asyncio.StreamWriter, "characters_written"):
    asyncio.StreamWriter.characters_written = 0


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
        proxy_url: Optional[str] = None,
    ) -> None:
        self.url = url
        self.name = name
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.proxy_url = proxy_url

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
        """连接到 WebSocket 服务器（支持代理）"""
        if self._connected:
            return True

        try:
            import websockets

            connect_kwargs: dict[str, Any] = {
                "ping_interval": self.ping_interval,
                "ping_timeout": self.ping_timeout,
            }

            # 如果配置了代理，通过 python-socks 建立代理隧道
            if self.proxy_url:
                try:
                    from python_socks.async_.asyncio import Proxy

                    parsed = urlparse(self.url)
                    dest_host = parsed.hostname or ""
                    # WebSocket 默认端口：wss=443, ws=80
                    dest_port = parsed.port or (443 if parsed.scheme == "wss" else 80)

                    proxy = Proxy.from_url(self.proxy_url)
                    sock = await proxy.connect(dest_host=dest_host, dest_port=dest_port)
                    connect_kwargs["sock"] = sock

                    # wss:// 需要显式传入 SSL 参数，因为通过 sock 连接时
                    # websockets 不会自动根据 URI scheme 推断 TLS
                    if parsed.scheme == "wss":
                        ssl_context = ssl.create_default_context()
                        ssl_context.check_hostname = False  # ← 新增
                        ssl_context.verify_mode = ssl.CERT_NONE  # ← 新增
                        connect_kwargs["ssl"] = ssl_context
                        connect_kwargs["server_hostname"] = dest_host

                    logger.info(
                        "WebSocket 通过代理连接",
                        name=self.name,
                        proxy=self.proxy_url,
                        dest=f"{dest_host}:{dest_port}",
                    )
                except ImportError:
                    logger.warning(
                        "python-socks 未安装，忽略代理配置。"
                        "请运行: pip install python-socks[asyncio]",
                        name=self.name,
                    )

            self._ws = await websockets.connect(
                self.url,
                **connect_kwargs,
                open_timeout=15,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                classmethod=10
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

        except websockets.exceptions.InvalidHandshake as e:
            logger.error("WebSocket 连接失败", name=self.name, exc_info=True)

            self.stats.error_count += 1
            return False
        except OSError as ose:
            if hasattr(ose, 'characters_written'):
                logger.error(
                    "OSError with characters_written: %s (可能非阻塞写部分成功)", ose)
            else:
                logger.error("OSError: %s", ose)

            self.stats.error_count += 1
            return False
        except Exception as e:
            logger.error("连接异常", exc_info=True)
            if hasattr(e, '__cause__') and e.__cause__:
                logger.error("Cause: %s", e.__cause__)
            # 如果 _ws 已部分创建，检查 transport
            if self._ws is not None:
                transport = getattr(self._ws, 'transport', None)
                if transport:
                    logger.debug("Transport attrs: %s", dir(transport))

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
            logger.error("WebSocket 发送失败", name=self.name, exc_info=True)
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
                logger.error("WebSocket 接收异常", name=self.name, exc_info=True)
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
                logger.error("WebSocket 心跳异常", name=self.name, exc_info=True)

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
