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

from quant_trading_system.services.market.market_event_bus import (
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
# 模拟交易对配置
# ═══════════════════════════════════════════════════════════════

@dataclass
class SymbolConfig:
    """单个交易对的模拟参数"""
    base_price: float          # 基准价格
    volatility: float = 0.002  # 单次波动率（±0.2%）
    base_volume: float = 1.0   # 基准成交量
    depth_levels: int = 10     # 深度档位数
    spread_pct: float = 0.0005 # 买卖价差百分比


# 预置主流币种的合理基准价格
DEFAULT_SYMBOL_CONFIGS: dict[str, SymbolConfig] = {
    "BTCUSDT":  SymbolConfig(base_price=66824.75000000, volatility=0.0015, base_volume=0.5),
    "ETHUSDT":  SymbolConfig(base_price=1975.37000000,  volatility=0.002,  base_volume=5.0),
    "SOLUSDT":  SymbolConfig(base_price=84.90000000,   volatility=0.003,  base_volume=20.0),
    "BNBUSDT":  SymbolConfig(base_price=620.0,   volatility=0.002,  base_volume=3.0),
    "XRPUSDT":  SymbolConfig(base_price=2.3,     volatility=0.003,  base_volume=500.0),
    "ADAUSDT":  SymbolConfig(base_price=0.75,    volatility=0.003,  base_volume=1000.0),
    "DOGEUSDT": SymbolConfig(base_price=0.22,    volatility=0.004,  base_volume=5000.0),
    "DOTUSDT":  SymbolConfig(base_price=7.5,     volatility=0.003,  base_volume=50.0),
}


@dataclass
class _SymbolState:
    """运行时：单个交易对的实时状态"""
    last_price: float
    bid_price: float = 0.0
    ask_price: float = 0.0
    # 当前 1m K 线缓存
    kline_open: float = 0.0
    kline_high: float = 0.0
    kline_low: float = 0.0
    kline_close: float = 0.0
    kline_volume: float = 0.0
    kline_start_ts: float = 0.0  # 毫秒时间戳
    # 趋势状态（模拟微趋势）
    trend: float = 0.0
    trend_remaining: int = 0


# ═══════════════════════════════════════════════════════════════
# Mock 交易所连接器（开发环境）
# ═══════════════════════════════════════════════════════════════

class MockConnector(ExchangeConnector):
    """
    模拟交易所连接器（开发/测试环境使用）

    生成模拟行情数据并通过事件总线直接发布，功能包括：
    - 模拟 ticker（逐笔行情）   ：默认每 500ms 推送一次
    - 模拟 kline（1m K线）       ：每秒推送实时更新，每 60s 推送 is_closed=True
    - 模拟 depth（买卖深度）     ：默认每 1s 推送一次
    - 价格采用带微趋势的随机游走，视觉上更真实
    - 可通过 subscribe / unsubscribe 动态增减交易对
    """

    def __init__(
        self,
        event_bus: MarketEventBus,
        tick_interval: float = 0.5,
        depth_interval: float = 1.0,
        kline_intervals: list[str] | None = None,
    ) -> None:
        super().__init__(name="mock", event_bus=event_bus)
        self.tick_interval = tick_interval
        self.depth_interval = depth_interval
        self.kline_intervals = kline_intervals or [
            "1s", "1m", "3m", "5m", "15m", "30m",
            "1h", "2h", "4h", "6h", "8h", "12h",
            "1d", "3d", "1w", "1M",
        ]

        # 运行时状态：symbol_key → _SymbolState
        self._states: dict[str, _SymbolState] = {}

        # 后台任务
        self._tick_task: asyncio.Task | None = None
        self._depth_task: asyncio.Task | None = None
        self._kline_task: asyncio.Task | None = None

    # ── 生命周期 ────────────────────────────────────────────────

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        logger.info("🎭 MockConnector 启动",
                     tick_interval=self.tick_interval,
                     depth_interval=self.depth_interval,
                     kline_intervals=self.kline_intervals)

        # 启动后台推送任务（根据配置开关决定是否启动）
        self._tick_task = asyncio.create_task(self._tick_loop(), name="mock-tick")
        self._depth_task = asyncio.create_task(self._depth_loop(), name="mock-depth")
        self._kline_task = asyncio.create_task(self._kline_loop(), name="mock-kline")

        await self._publish(MarketEventType.CONNECTED, {"mock": True})
        logger.info("🎭 MockConnector 已启动")

    async def stop(self) -> None:
        self._running = False

        for task in [self._tick_task, self._depth_task, self._kline_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._tick_task = None
        self._depth_task = None
        self._kline_task = None

        await self._publish(MarketEventType.DISCONNECTED, {"mock": True})
        logger.info("🎭 MockConnector 已停止")

    # ── 订阅管理 ────────────────────────────────────────────────

    async def subscribe(self, symbols: list[str]) -> None:
        """
        订阅交易对

        symbols 格式与真实连接器一致，如 ["BTC/USDT", "ETH/USDT"]
        内部自动转换为 BTCUSDT 格式。
        """
        for raw_symbol in symbols:
            symbol_key = raw_symbol.replace("/", "").replace("-", "").upper()

            if symbol_key in self._states:
                continue

            # 获取预置配置或使用默认值
            cfg = DEFAULT_SYMBOL_CONFIGS.get(
                symbol_key,
                SymbolConfig(base_price=100.0, volatility=0.003, base_volume=10.0),
            )

            # 初始化运行时状态
            now_ms = time.time() * 1000
            # K 线开始时间对齐到分钟
            kline_start = (int(now_ms) // 60000) * 60000

            state = _SymbolState(
                last_price=cfg.base_price,
                bid_price=cfg.base_price * (1 - cfg.spread_pct),
                ask_price=cfg.base_price * (1 + cfg.spread_pct),
                kline_open=cfg.base_price,
                kline_high=cfg.base_price,
                kline_low=cfg.base_price,
                kline_close=cfg.base_price,
                kline_volume=0.0,
                kline_start_ts=float(kline_start),
            )
            self._states[symbol_key] = state
            self._subscriptions.add(raw_symbol)

        logger.info("🎭 Mock 订阅", symbols=symbols,
                     active_symbols=list(self._states.keys()))

    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        for raw_symbol in symbols:
            symbol_key = raw_symbol.replace("/", "").replace("-", "").upper()
            self._states.pop(symbol_key, None)
            self._subscriptions.discard(raw_symbol)

        logger.info("🎭 Mock 取消订阅", symbols=symbols)

    # ── 价格模拟引擎 ────────────────────────────────────────────

    def _next_price(self, symbol_key: str) -> float:
        """
        生成下一个价格（带微趋势的随机游走）

        模拟效果：
        - 70% 时间在小幅波动
        - 偶尔出现一段持续的微趋势（连续涨/跌 5~20 个 tick）
        - 偶尔出现短暂的大波动（模拟成交异动）
        """
        state = self._states[symbol_key]
        cfg = DEFAULT_SYMBOL_CONFIGS.get(
            symbol_key,
            SymbolConfig(base_price=state.last_price),
        )

        # 微趋势切换
        if state.trend_remaining <= 0:
            if random.random() < 0.3:
                # 30% 概率进入一段趋势
                state.trend = random.choice([-1, 1]) * cfg.volatility * random.uniform(0.3, 1.0)
                state.trend_remaining = random.randint(5, 20)
            else:
                state.trend = 0.0
                state.trend_remaining = random.randint(3, 10)

        state.trend_remaining -= 1

        # 基础随机波动
        noise = random.gauss(0, cfg.volatility)

        # 偶尔大波动（2% 概率）
        if random.random() < 0.02:
            noise *= random.uniform(2.0, 4.0)

        # 叠加趋势
        change_pct = noise + state.trend * 0.3

        new_price = state.last_price * (1 + change_pct)

        # 价格不能为负
        new_price = max(new_price, state.last_price * 0.9)

        state.last_price = new_price

        # 更新买卖价
        spread = new_price * cfg.spread_pct
        state.bid_price = new_price - spread / 2
        state.ask_price = new_price + spread / 2

        return new_price

    # ── Tick 推送循环 ───────────────────────────────────────────

    async def _tick_loop(self) -> None:
        """定时生成并推送 tick 数据"""
        while self._running:
            try:
                await asyncio.sleep(self.tick_interval)

                for symbol_key, state in list(self._states.items()):
                    cfg = DEFAULT_SYMBOL_CONFIGS.get(
                        symbol_key,
                        SymbolConfig(base_price=state.last_price),
                    )

                    price = self._next_price(symbol_key)
                    now_ms = time.time() * 1000

                    # 模拟成交量
                    volume = cfg.base_volume * random.uniform(0.1, 3.0)

                    tick_data = {
                        "symbol": symbol_key,
                        "exchange": "mock",
                        "timestamp": now_ms,
                        "last_price": round(price, self._price_decimals(price)),
                        "bid_price": round(state.bid_price, self._price_decimals(price)),
                        "ask_price": round(state.ask_price, self._price_decimals(price)),
                        "bid_size": round(cfg.base_volume * random.uniform(0.5, 5.0), 4),
                        "ask_size": round(cfg.base_volume * random.uniform(0.5, 5.0), 4),
                        "volume": round(volume, 4),
                        "turnover": round(volume * price, 2),
                        "is_trade": True,
                        "trade_id": f"mock_{int(now_ms)}_{random.randint(1000, 9999)}",
                    }

                    # 更新 1m K 线缓存
                    self._update_kline_state(symbol_key, price, volume, now_ms)

                    await self._publish(MarketEventType.TICK, tick_data, symbol=symbol_key)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockConnector tick 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── Kline 推送循环 ──────────────────────────────────────────

    async def _kline_loop(self) -> None:
        """定时推送 K 线数据（每秒检查一次是否需要推送关闭的 K 线）"""
        while self._running:
            try:
                await asyncio.sleep(1.0)
                now_ms = time.time() * 1000

                for symbol_key, state in list(self._states.items()):
                    # 推送所有配置的 K 线周期
                    for interval in self.kline_intervals:
                        interval_ms = self._interval_to_ms(interval)
                        current_kline_start = (int(now_ms) // interval_ms) * interval_ms

                        # 判断当前 K 线是否已关闭
                        is_closed = False
                        if interval == "1m":
                            # 1m 由内部状态精确维护
                            if state.kline_start_ts < current_kline_start:
                                is_closed = True
                        else:
                            # 其他周期：在新周期开始的前 2 秒内推送上一个周期的关闭
                            time_in_period = now_ms - current_kline_start
                            if time_in_period < 2000:
                                is_closed = True

                        kline_data = {
                            "symbol": symbol_key,
                            "exchange": "mock",
                            "timestamp": state.kline_start_ts if interval == "1m" else float(current_kline_start),
                            "interval": interval,
                            "open": round(state.kline_open, self._price_decimals(state.kline_open)),
                            "high": round(state.kline_high, self._price_decimals(state.kline_high)),
                            "low": round(state.kline_low, self._price_decimals(state.kline_low)),
                            "close": round(state.kline_close, self._price_decimals(state.kline_close)),
                            "volume": round(state.kline_volume, 4),
                            "is_closed": is_closed,
                        }

                        await self._publish(MarketEventType.KLINE, kline_data, symbol=symbol_key)

                    # 如果 1m K 线已关闭，重置状态
                    current_minute_start = (int(now_ms) // 60000) * 60000
                    if state.kline_start_ts < current_minute_start:
                        state.kline_open = state.last_price
                        state.kline_high = state.last_price
                        state.kline_low = state.last_price
                        state.kline_close = state.last_price
                        state.kline_volume = 0.0
                        state.kline_start_ts = float(current_minute_start)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockConnector kline 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── Depth 推送循环 ──────────────────────────────────────────

    async def _depth_loop(self) -> None:
        """定时生成并推送 depth 数据"""
        while self._running:
            try:
                await asyncio.sleep(self.depth_interval)

                for symbol_key, state in list(self._states.items()):
                    cfg = DEFAULT_SYMBOL_CONFIGS.get(
                        symbol_key,
                        SymbolConfig(base_price=state.last_price),
                    )

                    now_ms = time.time() * 1000
                    decimals = self._price_decimals(state.last_price)

                    # 生成买盘（由高到低）
                    bids = []
                    for i in range(cfg.depth_levels):
                        price = state.bid_price * (1 - i * cfg.spread_pct * 0.5)
                        size = cfg.base_volume * random.uniform(0.5, 10.0)
                        bids.append([round(price, decimals), round(size, 4)])

                    # 生成卖盘（由低到高）
                    asks = []
                    for i in range(cfg.depth_levels):
                        price = state.ask_price * (1 + i * cfg.spread_pct * 0.5)
                        size = cfg.base_volume * random.uniform(0.5, 10.0)
                        asks.append([round(price, decimals), round(size, 4)])

                    depth_data = {
                        "symbol": symbol_key,
                        "exchange": "mock",
                        "timestamp": now_ms,
                        "bids": bids,
                        "asks": asks,
                    }

                    await self._publish(MarketEventType.DEPTH, depth_data, symbol=symbol_key)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockConnector depth 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── 工具方法 ────────────────────────────────────────────────

    def _update_kline_state(
        self, symbol_key: str, price: float, volume: float, now_ms: float,
    ) -> None:
        """更新 1m K 线内存状态"""
        state = self._states.get(symbol_key)
        if not state:
            return

        current_minute_start = (int(now_ms) // 60000) * 60000

        # 如果进入了新的一分钟，先重置
        if state.kline_start_ts < current_minute_start:
            state.kline_open = price
            state.kline_high = price
            state.kline_low = price
            state.kline_close = price
            state.kline_volume = volume
            state.kline_start_ts = float(current_minute_start)
        else:
            state.kline_high = max(state.kline_high, price)
            state.kline_low = min(state.kline_low, price)
            state.kline_close = price
            state.kline_volume += volume

    @staticmethod
    def _price_decimals(price: float) -> int:
        """根据价格量级决定小数位数"""
        if price >= 10000:
            return 2
        elif price >= 100:
            return 3
        elif price >= 1:
            return 4
        elif price >= 0.01:
            return 5
        else:
            return 8

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        """将 K 线周期字符串转为毫秒"""
        mapping = {
            "1s": 1_000,
            "1m": 60_000,
            "3m": 180_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "2h": 7_200_000,
            "4h": 14_400_000,
            "6h": 21_600_000,
            "8h": 28_800_000,
            "12h": 43_200_000,
            "1d": 86_400_000,
            "3d": 259_200_000,
            "1w": 604_800_000,
            "1M": 2_592_000_000,  # 按 30 天近似
        }
        return mapping.get(interval, 60_000)
