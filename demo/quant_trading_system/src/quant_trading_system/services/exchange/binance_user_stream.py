"""
币安 User Data Stream 管理器
==============================

通过 WebSocket 监听币安用户数据流，实时接收以下事件：
- executionReport: 订单状态变化（新订单、成交、取消等）
- outboundAccountPosition: 账户余额变化
- balanceUpdate: 余额更新

核心流程：
1. 通过 REST API 创建/续期 listenKey
2. 建立 WebSocket 连接监听用户数据流
3. 解析事件并通过回调函数分发

使用说明：
    manager = BinanceUserStreamManager(api_key, api_secret, account_type="spot")
    manager.on_order_update = my_order_callback
    await manager.start()
    ...
    await manager.stop()
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Coroutine, Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

# 回调函数类型：接收事件字典，返回协程
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class BinanceUserStreamManager:
    """
    币安 User Data Stream 管理器

    管理 listenKey 生命周期和 WebSocket 连接，
    接收实时订单/账户事件并通过回调分发。

    支持：
    - 自动续期 listenKey（每 30 分钟）
    - WebSocket 自动重连（指数退避）
    - 优雅关闭
    """

    # 币安 API 基础URL
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"
    SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
    FUTURES_WS_URL = "wss://fstream.binance.com/ws"

    # 测试网
    SPOT_TESTNET_BASE_URL = "https://testnet.binance.vision"
    FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"
    SPOT_TESTNET_WS_URL = "wss://testnet.binance.vision/ws"
    FUTURES_TESTNET_WS_URL = "wss://stream.binancefuture.com/ws"

    # listenKey 续期间隔（30分钟，币安要求60分钟内续期）
    KEEPALIVE_INTERVAL = 30 * 60  # 秒

    # WebSocket 重连参数
    RECONNECT_BASE_DELAY = 1.0   # 初始重连延迟（秒）
    RECONNECT_MAX_DELAY = 60.0   # 最大重连延迟（秒）
    RECONNECT_MAX_RETRIES = 50   # 最大重连次数（0=无限）

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        account_type: str = "spot",
        testnet: bool = False,
    ):
        """
        初始化管理器

        Args:
            api_key: 币安 API Key
            api_secret: 币安 API Secret
            account_type: 账户类型 spot/futures
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_type = account_type
        self.testnet = testnet

        # 设置 URL
        if testnet:
            if account_type == "spot":
                self.base_url = self.SPOT_TESTNET_BASE_URL
                self.ws_base_url = self.SPOT_TESTNET_WS_URL
            else:
                self.base_url = self.FUTURES_TESTNET_BASE_URL
                self.ws_base_url = self.FUTURES_TESTNET_WS_URL
        else:
            if account_type == "spot":
                self.base_url = self.SPOT_BASE_URL
                self.ws_base_url = self.SPOT_WS_URL
            else:
                self.base_url = self.FUTURES_BASE_URL
                self.ws_base_url = self.FUTURES_WS_URL

        # 状态
        self._listen_key: Optional[str] = None
        self._running = False
        self._ws_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._reconnect_count = 0

        # 事件回调
        self.on_order_update: Optional[EventCallback] = None
        self.on_account_update: Optional[EventCallback] = None
        self.on_balance_update: Optional[EventCallback] = None
        self.on_any_event: Optional[EventCallback] = None

        # 统计
        self._events_received = 0
        self._last_event_time: Optional[float] = None
        self._connected_since: Optional[float] = None

    # ── listenKey REST API ────────────────────────────────────

    def _get_listen_key_path(self) -> str:
        """获取 listenKey API 路径"""
        if self.account_type == "spot":
            return "/api/v3/userDataStream"
        else:
            return "/fapi/v1/listenKey"

    async def _ensure_http_client(self) -> httpx.AsyncClient:
        """确保异步 HTTP 客户端可用"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
                verify=True,
            )
        return self._http_client

    async def _create_listen_key(self) -> str:
        """
        创建 listenKey

        Returns:
            listenKey 字符串

        Raises:
            httpx.HTTPStatusError: API 请求失败
        """
        client = await self._ensure_http_client()
        url = f"{self.base_url}{self._get_listen_key_path()}"
        headers = {"X-MBX-APIKEY": self.api_key}

        response = await client.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        listen_key = data["listenKey"]
        logger.info(f"已创建 listenKey: {listen_key[:8]}...")
        return listen_key

    async def _keepalive_listen_key(self) -> None:
        """续期 listenKey（PUT 请求）"""
        if not self._listen_key:
            return
        client = await self._ensure_http_client()
        url = f"{self.base_url}{self._get_listen_key_path()}"
        headers = {"X-MBX-APIKEY": self.api_key}
        params = {"listenKey": self._listen_key}

        response = await client.put(url, headers=headers, params=params)
        response.raise_for_status()
        logger.debug(f"listenKey 续期成功: {self._listen_key[:8]}...")

    async def _delete_listen_key(self) -> None:
        """删除 listenKey（DELETE 请求）"""
        if not self._listen_key:
            return
        try:
            client = await self._ensure_http_client()
            url = f"{self.base_url}{self._get_listen_key_path()}"
            headers = {"X-MBX-APIKEY": self.api_key}
            params = {"listenKey": self._listen_key}

            response = await client.delete(url, headers=headers, params=params)
            response.raise_for_status()
            logger.info(f"已删除 listenKey: {self._listen_key[:8]}...")
        except Exception as e:
            logger.warning(f"删除 listenKey 失败（可忽略）: {e}")

    # ── listenKey 自动续期 ────────────────────────────────────

    async def _keepalive_loop(self) -> None:
        """listenKey 定时续期循环"""
        while self._running:
            try:
                await asyncio.sleep(self.KEEPALIVE_INTERVAL)
                if self._running and self._listen_key:
                    await self._keepalive_listen_key()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"listenKey 续期失败: {e}")
                # 续期失败时尝试重新创建
                try:
                    self._listen_key = await self._create_listen_key()
                    logger.info("已重新创建 listenKey")
                except Exception as e2:
                    logger.error(f"重新创建 listenKey 也失败: {e2}")

    # ── WebSocket 连接与事件处理 ──────────────────────────────

    async def _ws_loop(self) -> None:
        """WebSocket 连接主循环（含自动重连）"""
        while self._running:
            try:
                # 创建或刷新 listenKey
                self._listen_key = await self._create_listen_key()
                ws_url = f"{self.ws_base_url}/{self._listen_key}"

                logger.info(f"正在连接币安 User Data Stream: {self.ws_base_url}...")

                async with websockets.connect(
                    ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=5,
                ) as ws:
                    self._connected_since = time.time()
                    self._reconnect_count = 0
                    logger.info("✅ 币安 User Data Stream 已连接")

                    async for message in ws:
                        if not self._running:
                            break
                        await self._handle_message(message)

            except asyncio.CancelledError:
                break
            except ConnectionClosed as e:
                logger.warning(f"WebSocket 连接关闭: code={e.code}, reason={e.reason}")
            except Exception as e:
                logger.error(f"WebSocket 错误: {e}")

            # 重连逻辑
            if not self._running:
                break

            self._connected_since = None
            self._reconnect_count += 1

            if 0 < self.RECONNECT_MAX_RETRIES < self._reconnect_count:
                logger.error(f"达到最大重连次数 {self.RECONNECT_MAX_RETRIES}，停止重连")
                self._running = False
                break

            delay = min(
                self.RECONNECT_BASE_DELAY * (2 ** (self._reconnect_count - 1)),
                self.RECONNECT_MAX_DELAY,
            )
            logger.info(f"将在 {delay:.1f} 秒后重连（第 {self._reconnect_count} 次）...")
            await asyncio.sleep(delay)

    async def _handle_message(self, raw_message: str) -> None:
        """
        解析并分发 WebSocket 消息

        币安 User Data Stream 事件类型：
        - executionReport: 现货订单更新
        - ORDER_TRADE_UPDATE: 合约订单更新
        - outboundAccountPosition: 现货账户更新
        - ACCOUNT_UPDATE: 合约账户更新
        - balanceUpdate: 余额更新
        """
        try:
            event = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning(f"收到无效 JSON: {raw_message[:200]}")
            return

        self._events_received += 1
        self._last_event_time = time.time()

        event_type = event.get("e", "")
        logger.debug(f"收到事件: {event_type}")

        # 分发到对应回调
        try:
            # 通用回调
            if self.on_any_event:
                await self.on_any_event(event)

            # 订单更新
            if event_type in ("executionReport", "ORDER_TRADE_UPDATE"):
                if self.on_order_update:
                    await self.on_order_update(event)

            # 账户更新
            elif event_type in ("outboundAccountPosition", "ACCOUNT_UPDATE"):
                if self.on_account_update:
                    await self.on_account_update(event)

            # 余额更新
            elif event_type == "balanceUpdate":
                if self.on_balance_update:
                    await self.on_balance_update(event)

        except Exception as e:
            logger.error(f"处理事件回调异常: {event_type}, 错误: {e}", exc_info=True)

    # ── 启动 / 停止 ──────────────────────────────────────────

    async def start(self) -> None:
        """
        启动 User Data Stream 监听

        创建 listenKey，建立 WebSocket 连接，启动续期循环。
        """
        if self._running:
            logger.warning("User Data Stream 已在运行中")
            return

        self._running = True
        self._reconnect_count = 0

        # 启动 WebSocket 连接协程
        self._ws_task = asyncio.create_task(self._ws_loop(), name="binance_user_stream_ws")

        # 启动 listenKey 续期协程
        self._keepalive_task = asyncio.create_task(
            self._keepalive_loop(), name="binance_user_stream_keepalive"
        )

        logger.info("币安 User Data Stream 管理器已启动")

    async def stop(self) -> None:
        """
        停止 User Data Stream 监听

        关闭 WebSocket 连接，删除 listenKey，释放资源。
        """
        if not self._running:
            return

        logger.info("正在停止币安 User Data Stream...")
        self._running = False

        # 取消后台任务
        for task in (self._ws_task, self._keepalive_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._ws_task = None
        self._keepalive_task = None

        # 删除 listenKey
        await self._delete_listen_key()
        self._listen_key = None
        self._connected_since = None

        # 关闭 HTTP 客户端
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("✅ 币安 User Data Stream 已停止")

    # ── 状态查询 ──────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    @property
    def is_connected(self) -> bool:
        """WebSocket 是否已连接"""
        return self._running and self._connected_since is not None

    def get_status(self) -> dict[str, Any]:
        """
        获取当前状态摘要

        Returns:
            {
                running: bool,
                connected: bool,
                account_type: str,
                listen_key: str (masked),
                connected_since: float,
                uptime_seconds: float,
                events_received: int,
                last_event_time: float,
                reconnect_count: int,
            }
        """
        now = time.time()
        uptime = (now - self._connected_since) if self._connected_since else 0

        return {
            "running": self._running,
            "connected": self.is_connected,
            "account_type": self.account_type,
            "listen_key": f"{self._listen_key[:8]}..." if self._listen_key else None,
            "connected_since": self._connected_since,
            "uptime_seconds": round(uptime, 1),
            "events_received": self._events_received,
            "last_event_time": self._last_event_time,
            "reconnect_count": self._reconnect_count,
        }
