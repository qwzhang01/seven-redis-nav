"""
Mock 币安 User Data Stream 管理器（开发环境专用）
=================================================

与 BinanceUserStreamManager 完全兼容的接口，
不连接真实 Binance WebSocket，而是：
1. 定时生成模拟的订单事件（executionReport）
2. 返回模拟的快照数据（持仓、挂单、账户信息）
3. 通过回调分发事件，驱动下游 SignalStreamEngine / FollowEngine 测试

用于开发环境联调和前端对接。
"""

import asyncio
import logging
import random
import time
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

# 回调函数类型
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

# ── 模拟数据常量 ──────────────────────────────────────────────

# 模拟交易对及其价格范围
MOCK_SYMBOLS = {
    "BTCUSDT": {"price_min": 85000, "price_max": 105000, "qty_min": 0.001, "qty_max": 0.05},
    "ETHUSDT": {"price_min": 1800, "price_max": 2500, "qty_min": 0.01, "qty_max": 0.5},
    "SOLUSDT": {"price_min": 120, "price_max": 200, "qty_min": 0.1, "qty_max": 5.0},
    "BNBUSDT": {"price_min": 550, "price_max": 700, "qty_min": 0.01, "qty_max": 1.0},
}

# 模拟账户余额
MOCK_BALANCES = [
    {"asset": "USDT", "free": "50000.00", "locked": "5000.00"},
    {"asset": "BTC", "free": "0.5", "locked": "0.0"},
    {"asset": "ETH", "free": "5.0", "locked": "1.0"},
    {"asset": "SOL", "free": "100.0", "locked": "0.0"},
    {"asset": "BNB", "free": "10.0", "locked": "0.0"},
]


def _random_price(symbol: str) -> float:
    """生成指定交易对的随机价格"""
    info = MOCK_SYMBOLS.get(symbol, {"price_min": 100, "price_max": 200})
    return round(random.uniform(info["price_min"], info["price_max"]), 2)


def _random_qty(symbol: str) -> float:
    """生成指定交易对的随机数量"""
    info = MOCK_SYMBOLS.get(symbol, {"qty_min": 0.01, "qty_max": 1.0})
    return round(random.uniform(info["qty_min"], info["qty_max"]), 6)


def _generate_order_id() -> int:
    """生成模拟订单ID"""
    return random.randint(10**15, 10**16 - 1)


def _generate_mock_execution_report(symbol: str | None = None) -> dict[str, Any]:
    """
    生成模拟的现货 executionReport 事件

    格式与币安 WebSocket 推送的 executionReport 完全一致。
    """
    if symbol is None:
        symbol = random.choice(list(MOCK_SYMBOLS.keys()))

    side = random.choice(["BUY", "SELL"])
    price = _random_price(symbol)
    qty = _random_qty(symbol)
    quote_qty = round(price * qty, 4)
    order_id = _generate_order_id()
    trade_time = int(time.time() * 1000)

    # 80% 概率 FILLED，20% 概率其他状态
    status_roll = random.random()
    if status_roll < 0.80:
        status = "FILLED"
    elif status_roll < 0.90:
        status = "PARTIALLY_FILLED"
        qty = round(qty * random.uniform(0.2, 0.8), 6)
        quote_qty = round(price * qty, 4)
    elif status_roll < 0.95:
        status = "NEW"
        qty = 0
        quote_qty = 0
    else:
        status = "CANCELED"
        qty = 0
        quote_qty = 0

    # 手续费
    commission = round(quote_qty * 0.001, 8) if quote_qty > 0 else 0

    return {
        "e": "executionReport",      # 事件类型
        "E": trade_time,             # 事件时间
        "s": symbol,                 # 交易对
        "c": f"mock_{order_id}",     # 客户端订单ID
        "S": side,                   # 交易方向
        "o": "MARKET",               # 订单类型
        "f": "GTC",                  # 有效方式
        "q": str(round(qty + random.uniform(0, 0.001), 6)),  # 原始数量
        "p": "0.00000000",           # 原始价格（市价单为0）
        "P": "0.00000000",           # 止损价格
        "F": "0.00000000",           # 冰山订单数量
        "g": -1,
        "C": "",
        "x": "TRADE" if status in ("FILLED", "PARTIALLY_FILLED") else status,  # 当前执行类型
        "X": status,                 # 当前订单状态
        "r": "NONE",                 # 拒绝原因
        "i": order_id,               # 订单ID
        "l": str(qty),               # 最后成交量
        "z": str(qty),               # 累计成交量
        "L": str(price),             # 最后成交价
        "n": str(commission),        # 手续费
        "N": "USDT",                 # 手续费资产
        "T": trade_time,             # 成交时间
        "t": random.randint(10**8, 10**9),  # 成交ID
        "I": random.randint(10**10, 10**11),
        "w": False,
        "m": False,
        "M": True,
        "O": trade_time - random.randint(0, 5000),  # 订单创建时间
        "Z": str(quote_qty),         # 累计报价数量
        "Y": str(quote_qty),         # 最后成交报价数量
        "Q": "0.00000000",
    }


class MockBinanceUserStreamManager:
    """
    Mock 币安 User Data Stream 管理器

    完全兼容 BinanceUserStreamManager 的接口，
    无需真实 API Key，通过定时器模拟订单事件。

    配置参数：
        event_interval: 模拟事件的发送间隔（秒），默认 15 秒
        symbols: 模拟的交易对列表，默认全部
    """

    def __init__(
        self,
        api_key: str = "mock_key",
        api_secret: str = "mock_secret",
        account_type: str = "spot",
        testnet: bool = False,
        event_interval: float = 15.0,
        symbols: list[str] | None = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_type = account_type
        self.testnet = testnet

        # Mock 特有配置
        self._event_interval = event_interval
        self._mock_symbols = symbols or list(MOCK_SYMBOLS.keys())

        # 状态
        self._running = False
        self._event_task: Optional[asyncio.Task] = None
        self._reconnect_count = 0

        # 事件回调（与真实版本完全一致）
        self.on_order_update: Optional[EventCallback] = None
        self.on_account_update: Optional[EventCallback] = None
        self.on_balance_update: Optional[EventCallback] = None
        self.on_any_event: Optional[EventCallback] = None
        self.on_snapshot_ready: Optional[EventCallback] = None

        # 统计
        self._events_received = 0
        self._last_event_time: Optional[float] = None
        self._connected_since: Optional[float] = None

    # ── 启动 / 停止 ──────────────────────────────────────────

    async def start(self) -> None:
        """启动 Mock 数据流"""
        if self._running:
            logger.warning("[Mock] User Data Stream 已在运行中")
            return

        self._running = True
        self._connected_since = time.time()
        self._reconnect_count = 0

        logger.info(
            f"🎭 [Mock] 币安 User Data Stream 已启动 "
            f"(account_type={self.account_type}, "
            f"interval={self._event_interval}s, "
            f"symbols={self._mock_symbols})"
        )

        # 拉取初始快照
        try:
            await self.fetch_initial_snapshot()
        except Exception as e:
            logger.error(f"[Mock] 拉取初始快照失败: {e}")

        # 启动定时事件生成器
        self._event_task = asyncio.create_task(
            self._event_generator_loop(),
            name="mock_binance_event_generator",
        )

    async def stop(self) -> None:
        """停止 Mock 数据流"""
        if not self._running:
            return

        self._running = False
        self._connected_since = None

        if self._event_task and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass

        self._event_task = None
        logger.info("🎭 [Mock] 币安 User Data Stream 已停止")

    # ── 定时事件生成器 ────────────────────────────────────────

    async def _event_generator_loop(self) -> None:
        """定时生成模拟订单事件"""
        while self._running:
            try:
                # 加一点随机抖动，让事件时间更自然
                jitter = random.uniform(-2.0, 2.0)
                await asyncio.sleep(max(3.0, self._event_interval + jitter))

                if not self._running:
                    break

                # 随机选一个交易对生成事件
                symbol = random.choice(self._mock_symbols)
                event = _generate_mock_execution_report(symbol)

                self._events_received += 1
                self._last_event_time = time.time()

                status = event.get("X", "")
                logger.info(
                    f"🎭 [Mock] 生成模拟订单事件: {symbol} {event['S']} "
                    f"status={status} qty={event['z']} price={event['L']}"
                )

                # 分发回调
                if self.on_any_event:
                    await self.on_any_event(event)

                if self.on_order_update:
                    await self.on_order_update(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Mock] 事件生成器异常: {e}", exc_info=True)
                await asyncio.sleep(5)

    # ── REST API 模拟（私有方法，仅供 fetch_initial_snapshot 内部使用） ──

    async def _mock_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """返回模拟的挂单数据"""
        orders = []
        # 随机生成 0~3 个挂单
        target_symbols = [symbol] if symbol else self._mock_symbols
        for sym in target_symbols:
            if random.random() < 0.3:  # 30% 概率有挂单
                price = _random_price(sym)
                orders.append({
                    "orderId": _generate_order_id(),
                    "symbol": sym,
                    "side": random.choice(["BUY", "SELL"]),
                    "type": "LIMIT",
                    "price": str(round(price * random.uniform(0.95, 1.05), 2)),
                    "origQty": str(_random_qty(sym)),
                    "executedQty": "0.0",
                    "status": "NEW",
                    "time": int(time.time() * 1000) - random.randint(0, 3600000),
                })

        logger.info(f"🎭 [Mock] 返回模拟挂单: count={len(orders)}, symbol={symbol or 'ALL'}")
        return orders

    async def _mock_all_orders(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """返回模拟的历史订单"""
        orders = []
        now_ms = int(time.time() * 1000)
        for i in range(min(limit, random.randint(5, 20))):
            price = _random_price(symbol)
            qty = _random_qty(symbol)
            side = random.choice(["BUY", "SELL"])
            status = random.choice(["FILLED", "FILLED", "FILLED", "CANCELED"])
            orders.append({
                "orderId": _generate_order_id(),
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "price": str(price),
                "origQty": str(qty),
                "executedQty": str(qty) if status == "FILLED" else "0.0",
                "cummulativeQuoteQty": str(round(price * qty, 4)) if status == "FILLED" else "0.0",
                "status": status,
                "time": now_ms - random.randint(0, 86400000 * 7),
            })

        logger.info(f"🎭 [Mock] 返回模拟历史订单: symbol={symbol}, count={len(orders)}")
        return orders

    async def _mock_trade_history(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """返回模拟的成交记录"""
        trades = []
        now_ms = int(time.time() * 1000)
        for i in range(min(limit, random.randint(3, 15))):
            price = _random_price(symbol)
            qty = _random_qty(symbol)
            is_buyer = random.choice([True, False])
            trades.append({
                "id": random.randint(10**8, 10**9),
                "orderId": _generate_order_id(),
                "symbol": symbol,
                "price": str(price),
                "qty": str(qty),
                "quoteQty": str(round(price * qty, 4)),
                "commission": str(round(price * qty * 0.001, 8)),
                "commissionAsset": "USDT",
                "time": now_ms - random.randint(0, 86400000 * 3),
                "isBuyer": is_buyer,
                "isMaker": random.choice([True, False]),
            })

        logger.info(f"🎭 [Mock] 返回模拟成交记录: symbol={symbol}, count={len(trades)}")
        return trades

    async def _mock_positions(self) -> list[dict[str, Any]]:
        """返回模拟的持仓数据"""
        positions = []
        for balance in MOCK_BALANCES:
            free = float(balance["free"])
            locked = float(balance["locked"])
            if free > 0 or locked > 0:
                positions.append({
                    "asset": balance["asset"],
                    "free": balance["free"],
                    "locked": balance["locked"],
                })

        logger.info(f"🎭 [Mock] 返回模拟持仓: count={len(positions)}")
        return positions

    async def _mock_account_info(self) -> dict[str, Any]:
        """返回模拟的账户信息"""
        account = {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": MOCK_BALANCES,
        }
        logger.info("🎭 [Mock] 返回模拟账户信息")
        return account

    async def fetch_initial_snapshot(self) -> dict[str, Any]:
        """模拟拉取初始快照"""
        logger.info(f"🎭 [Mock] 开始拉取模拟初始快照: account_type={self.account_type}")

        open_orders = await self._mock_open_orders()
        positions = await self._mock_positions()
        account = await self._mock_account_info()

        snapshot = {
            "open_orders": open_orders,
            "positions": positions,
            "account": account,
        }

        logger.info(
            f"🎭 [Mock] 初始快照拉取完成: "
            f"open_orders={len(snapshot['open_orders'])}, "
            f"positions={len(snapshot['positions'])}, "
            f"has_account=yes"
        )

        # 触发回调
        if self.on_snapshot_ready:
            try:
                await self.on_snapshot_ready(snapshot)
            except Exception as e:
                logger.error(f"[Mock] 快照回调执行失败: {e}", exc_info=True)

        return snapshot

    # ── 状态查询（兼容真实版本） ──────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        return self._running and self._connected_since is not None

    def get_status(self) -> dict[str, Any]:
        """获取当前状态（兼容真实版本格式）"""
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
            "mock": True,  # 标记为 Mock 模式
            "event_interval": self._event_interval,
        }
