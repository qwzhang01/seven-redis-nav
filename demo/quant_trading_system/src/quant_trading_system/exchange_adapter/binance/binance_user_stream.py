"""
币安 User Data Stream 管理器
==============================

通过 python-binance 库监听币安用户数据流，实时接收以下事件：
- executionReport: 订单状态变化（新订单、成交、取消等）
- outboundAccountPosition: 账户余额变化
- balanceUpdate: 余额更新

核心流程：
1. 使用 python-binance 的 AsyncClient 创建异步客户端
2. 使用 BinanceSocketManager 建立 WebSocket 连接
3. python-binance 内部自动管理 listenKey 的创建与续期
4. 解析事件并通过回调函数分发

使用说明：
    manager = BinanceUserStreamManager(api_key, api_secret, account_type="spot")
    manager.on_order_update = my_order_callback
    await manager.start()
    ...
    await manager.stop()
"""

import asyncio
import time
from typing import Any, Callable, Coroutine, Optional

import structlog
from binance.async_client import AsyncClient
from binance.ws.streams import BinanceSocketManager

from quant_trading_system.exchange_adapter.binance.binance_rest_client import \
    BinanceRestClient

from src.quant_trading_system.core.enums import DefaultTradingPair

logger = structlog.get_logger(__name__)

# 回调函数类型：接收事件字典，返回协程
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class BinanceUserStreamManager:
    """
    币安 User Data Stream 管理器

    基于 python-binance 库，管理 WebSocket 连接，
    接收实时订单/账户事件并通过回调分发。

    python-binance 内部自动处理：
    - listenKey 创建与续期
    - WebSocket 心跳

    本类额外提供：
    - WebSocket 自动重连（指数退避）
    - 优雅关闭
    - 事件回调分发
    """

    # WebSocket 重连参数
    RECONNECT_BASE_DELAY = 1.0  # 初始重连延迟（秒）
    RECONNECT_MAX_DELAY = 60.0  # 最大重连延迟（秒）
    RECONNECT_MAX_RETRIES = 50  # 最大重连次数（0=无限）

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        account_type: str = "spot",
        testnet: bool = False,
        proxy_url: str | None = None,
    ):
        """
        初始化管理器

        Args:
            api_key: 币安 API Key
            api_secret: 币安 API Secret
            account_type: 账户类型 spot/futures
            testnet: 是否使用测试网
            proxy_url: 代理地址（如 socks5://127.0.0.1:7891）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_type = account_type
        self.testnet = testnet
        self.proxy_url = proxy_url

        # python-binance 客户端
        self._client: Optional[AsyncClient] = None
        self._bm: Optional[BinanceSocketManager] = None

        # 状态
        self._running = False
        self._ws_task: Optional[asyncio.Task] = None
        self._reconnect_count = 0

        # 事件回调
        self.on_order_update: Optional[EventCallback] = None
        self.on_account_update: Optional[EventCallback] = None
        self.on_balance_update: Optional[EventCallback] = None
        self.on_any_event: Optional[EventCallback] = None

        # 快照回调：启动时拉取历史数据后触发，参数为 {"open_orders": [...], "positions": [...], "account": {...}, "recent_trades": [...]}
        self.on_snapshot_ready: Optional[EventCallback] = None

        # REST 客户端（用于拉取历史数据，复用 BinanceRestClient 避免两套实现）
        self._rest_client = BinanceRestClient(
            api_key=api_key,
            api_secret=api_secret,
            market_type=account_type,
            testnet=testnet,
            proxy_url=proxy_url,
        )

        # 统计
        self._events_received = 0
        self._last_event_time: Optional[float] = None
        self._connected_since: Optional[float] = None

    # ── AsyncClient 生命周期 ──────────────────────────────────

    async def _create_client(self) -> AsyncClient:
        """
        创建 python-binance AsyncClient

        Returns:
            AsyncClient 实例
        """
        logger.info(
            f"正在创建 AsyncClient: "
            f"account_type={self.account_type}, "
            f"testnet={self.testnet}, "
            f"api_key={self.api_key[:8]}...{self.api_key[-4:] if len(self.api_key) > 12 else '***'}"
        )

        if self.proxy_url:
            logger.info(f"AsyncClient 使用代理: {self.proxy_url}")

        client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.testnet,
            https_proxy=self.proxy_url,
        )

        # 同步服务器时间，计算并设置时间偏移量，避免 -1021 Timestamp 错误
        try:
            server_time = await client.get_server_time()
            local_time = int(time.time() * 1000)
            client.timestamp_offset = server_time['serverTime'] - local_time
            logger.info(f"服务器时间偏移量已同步: offset={client.timestamp_offset}ms")
        except Exception as e:
            logger.warning(f"同步服务器时间失败（将使用本地时间）: {e}")

        logger.info("AsyncClient 创建成功")
        return client

    async def _close_client(self) -> None:
        """关闭 AsyncClient"""
        if self._client:
            try:
                await self._client.close_connection()
                logger.info("AsyncClient 已关闭")
            except Exception as e:
                logger.warning(f"关闭 AsyncClient 失败（可忽略）: {e}")
            finally:
                self._client = None
                self._bm = None

    # ── 确保客户端可用 ────────────────────────────────────────

    async def _ensure_client(self) -> AsyncClient:
        """
        确保 AsyncClient 可用，若未创建则自动创建

        Returns:
            AsyncClient 实例

        Raises:
            RuntimeError: 如果无法创建客户端
        """
        if self._client is None:
            self._client = await self._create_client()
            self._bm = BinanceSocketManager(self._client)
        return self._client

    # ── WebSocket 连接与事件处理 ──────────────────────────────

    async def _ws_loop(self) -> None:
        """WebSocket 连接主循环（含自动重连）"""
        while self._running:
            try:
                # 创建或重建 AsyncClient
                logger.info(
                    f"WebSocket 循环开始: account_type={self.account_type}, "
                    f"testnet={self.testnet}, "
                    f"reconnect_count={self._reconnect_count}"
                )

                # 每次重连时重新创建客户端，确保 listenKey 是新的
                await self._close_client()
                self._client = await self._create_client()
                self._bm = BinanceSocketManager(self._client)

                # 根据账户类型选择对应的 user socket
                if self.account_type == "spot":
                    socket = self._bm.user_socket()
                    logger.info("正在连接现货 User Data Stream...")
                else:
                    socket = self._bm.futures_user_socket()
                    logger.info("正在连接合约 User Data Stream...")

                async with socket as stream:
                    self._connected_since = time.time()
                    self._reconnect_count = 0
                    logger.info(
                        f"✅ 币安 User Data Stream 已连接, "
                        f"account_type={self.account_type}, "
                        f"connected_at={self._connected_since}"
                    )

                    # 为 REST 客户端同步服务器时间，避免签名请求出现 -1021 错误
                    try:
                        await self._rest_client.async_sync_server_time()
                    except Exception as e:
                        logger.warning(
                            f"REST 客户端同步服务器时间失败（将使用本地时间）: {e}")

                    while self._running:
                        try:
                            # 设置超时以便能定期检查 _running 状态
                            msg = await asyncio.wait_for(stream.recv(), timeout=30.0)
                            if msg and isinstance(msg, dict):
                                await self._handle_message(msg)
                        except asyncio.TimeoutError:
                            # 超时只是用于检查 _running 状态，不是错误
                            continue

            except asyncio.CancelledError:
                logger.info("WebSocket 循环被取消")
                break
            except Exception as e:
                logger.error(
                    f"WebSocket 错误: {e}, "
                    f"error_type={type(e).__name__}, "
                    f"account_type={self.account_type}, "
                    f"reconnect_count={self._reconnect_count}",
                    exc_info=True,
                )

            # 重连逻辑
            if not self._running:
                break

            self._connected_since = None
            self._reconnect_count += 1

            if 0 < self.RECONNECT_MAX_RETRIES < self._reconnect_count:
                logger.error(
                    f"达到最大重连次数 {self.RECONNECT_MAX_RETRIES}，停止重连, "
                    f"account_type={self.account_type}"
                )
                self._running = False
                break

            delay = min(
                self.RECONNECT_BASE_DELAY * (2 ** (self._reconnect_count - 1)),
                self.RECONNECT_MAX_DELAY,
            )
            logger.info(
                f"将在 {delay:.1f} 秒后重连（第 {self._reconnect_count} 次）, "
                f"account_type={self.account_type}"
            )
            await asyncio.sleep(delay)

    async def _handle_message(self, event: dict[str, Any]) -> None:
        """
        解析并分发 WebSocket 消息

        python-binance 已将 JSON 解析为字典，直接处理即可。

        币安 User Data Stream 事件类型：
        - executionReport: 现货订单更新
        - ORDER_TRADE_UPDATE: 合约订单更新
        - outboundAccountPosition: 现货账户更新
        - ACCOUNT_UPDATE: 合约账户更新
        - balanceUpdate: 余额更新
        """
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

    # ── 启动时拉取初始快照（直接调用 BinanceRestClient） ─────────

    async def fetch_initial_snapshot(self) -> dict[str, Any]:
        """
        拉取启动时的初始快照

        并发拉取当前挂单、持仓、账户信息，并通过 on_snapshot_ready 回调通知上层。
        直接调用 BinanceRestClient 的异步方法，不做多余的中间封装。

        Returns:
            快照数据字典:
            {
                "open_orders": [...],    # 当前挂单
                "positions": [...],      # 当前持仓
                "account": {...},        # 账户信息
            }
        """
        logger.info(f"开始拉取初始快照: account_type={self.account_type}")

        # 并发拉取各项数据（直接使用 _rest_client）
        open_orders_task = asyncio.create_task(
            self._safe_fetch(self._rest_client.async_get_open_orders, "open_orders")
        )
        positions_task = asyncio.create_task(
            self._safe_fetch(self._rest_client.async_get_positions, "positions")
        )
        account_task = asyncio.create_task(
            self._safe_fetch(self._rest_client.async_get_account_info, "account")
        )

        results = await asyncio.gather(open_orders_task, positions_task, account_task)

        snapshot = {
            "open_orders": results[0] or [],
            "positions": results[1] or [],
            "account": results[2] or {},
        }

        logger.info(
            f"📸 初始快照拉取完成: account_type={self.account_type}, "
            f"open_orders={len(snapshot['open_orders'])}, "
            f"positions={len(snapshot['positions'])}, "
            f"has_account={'yes' if snapshot['account'] else 'no'}"
        )

        # 通知上层
        if self.on_snapshot_ready:
            try:
                await self.on_snapshot_ready(snapshot)
            except Exception as e:
                logger.error(f"快照回调执行失败: {e}", exc_info=True)

        return snapshot

    async def _safe_fetch(self, fetch_func, name: str) -> Any:
        """
        安全执行拉取操作，异常时返回 None 而不中断其他拉取

        Args:
            fetch_func: 异步拉取函数
            name: 数据名称（用于日志）

        Returns:
            拉取结果或 None
        """
        try:
            return await fetch_func()
        except Exception as e:
            logger.error(f"拉取 {name} 失败（不影响其他数据）: {e}")
            return None

    # ── 启动 / 停止 ──────────────────────────────────────────

    async def start(self) -> None:
        """
        启动 User Data Stream 监听

        创建 AsyncClient，通过 BinanceSocketManager 建立 WebSocket 连接。
        python-binance 自动处理 listenKey 的创建和续期。
        """
        if self._running:
            logger.warning("User Data Stream 已在运行中")
            return

        self._running = True
        self._reconnect_count = 0

        try:
            await self.fetch_initial_snapshot()

            self._rest_client.__setattr__("market_type", "futures")
            for symbol in DefaultTradingPair.values():
                trade = self._rest_client.get_my_trades(symbol=symbol)
                logger.info(f"trade: {trade}")
                orders = self._rest_client.get_all_orders(symbol=symbol)
                logger.info(f"orders: {orders}")

            self._rest_client.__setattr__("market_type", "spot")
            for symbol in DefaultTradingPair.values():
                trade = self._rest_client.get_my_trades(symbol=symbol)
                logger.info(f"trade: {trade}")
                orders = self._rest_client.get_all_orders(symbol=symbol)
                logger.info(f"orders: {orders}")

        except Exception as e:
            logger.error(f"启动时拉取历史快照失败（不影响实时流）: {e}", exc_info=True)

        # 启动 WebSocket 连接协程
        self._ws_task = asyncio.create_task(self._ws_loop(),
                                            name="binance_user_stream_ws")

        logger.info("币安 User Data Stream 管理器已启动")

    async def stop(self) -> None:
        """
        停止 User Data Stream 监听

        关闭 WebSocket 连接，释放资源。
        """
        if not self._running:
            return

        logger.info("正在停止币安 User Data Stream...")
        self._running = False

        # 取消后台任务
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        self._ws_task = None
        self._connected_since = None

        # 关闭 AsyncClient（内部会清理 listenKey 和 WebSocket 连接）
        await self._close_client()

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
        now = time.time()
        uptime = (now - self._connected_since) if self._connected_since else 0

        return {
            "running": self._running,
            "connected": self.is_connected,
            "account_type": self.account_type,
            "connected_since": self._connected_since,
            "uptime_seconds": round(uptime, 1),
            "events_received": self._events_received,
            "last_event_time": self._last_event_time,
            "reconnect_count": self._reconnect_count,
        }
