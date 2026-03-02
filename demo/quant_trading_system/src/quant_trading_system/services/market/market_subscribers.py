"""
行情订阅器集合
==============

实现3个独立的行情订阅器，各自处理不同的关注点：

1. DatabaseSubscriber  —— 将行情数据异步存储到数据库（TimescaleDB）
2. WebSocketSubscriber —— 将行情数据推送到前端 WebSocket 客户端
3. TradingEngineSubscriber —— 将行情数据转发给实盘/模拟交易引擎

设计模式：
- 策略模式（Strategy Pattern）：每个订阅器用不同策略处理同一事件
- 单一职责原则（SRP）：每个订阅器只做一件事
- 开闭原则（OCP）：新增消费逻辑只需添加新订阅器，无需修改事件总线
"""

import asyncio
from typing import Any

import structlog

from quant_trading_system.core import settings
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.services.market.market_event_bus import (
    MarketEvent,
    MarketEventType,
    MarketSubscriber,
)

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. 数据库存储订阅器
# ═══════════════════════════════════════════════════════════════

class DatabaseSubscriber(MarketSubscriber):
    """
    数据库存储订阅器

    职责：将接收到的行情数据异步存储到 TimescaleDB。
    支持 Tick、K线、深度和历史K线数据的存储。

    使用场景：
    - 实时行情数据持久化
    - 历史数据同步后的存储
    """

    def __init__(self) -> None:
        self._data_store: Any = None

    @property
    def name(self) -> str:
        return "DatabaseSubscriber"

    async def start(self) -> None:
        """启动：初始化数据存储服务"""
        from quant_trading_system.services.database.data_store import get_data_store

        self._data_store = get_data_store()
        await self._data_store.start()
        logger.info("数据库存储订阅器已启动")

    async def stop(self) -> None:
        """停止：刷新缓冲区并关闭"""
        if self._data_store:
            await self._data_store.flush_all()
            await self._data_store.stop()
        logger.info("数据库存储订阅器已停止")

    async def on_event(self, event: MarketEvent) -> None:
        """处理行情事件：存储到数据库"""
        if not self._data_store:
            return

        if event.type == MarketEventType.TICK:
            await self._store_tick(event.data)
        elif event.type == MarketEventType.KLINE:
            await self._store_kline(event.data)
        elif event.type == MarketEventType.DEPTH:
            await self._store_depth(event.data)
        elif event.type == MarketEventType.HISTORICAL_KLINE:
            await self._store_historical_kline(event.data)

    async def _store_tick(self, data: dict[str, Any]) -> None:
        if not settings.SYNC_TICK:
            return

        """存储 Tick 数据"""
        from quant_trading_system.models.market import Tick

        tick = Tick(
            timestamp=data.get("timestamp", 0),
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            last_price=data.get("last_price", 0.0),
            price=data.get("last_price", 0.0),
            volume=data.get("volume", 0.0),
            bid=data.get("bid_price", 0.0),
            ask=data.get("ask_price", 0.0),
        )
        await self._data_store.store_tick(tick)

    async def _store_kline(self, data: dict[str, Any]) -> None:
        if not settings.SYNC_KLINE:
            return

        """存储 K线数据（仅已闭合的K线）"""
        if not data.get("is_closed", False):
            return

        from quant_trading_system.models.market import Bar

        bar = Bar(
            timestamp=data.get("timestamp", 0),
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            timeframe=KlineInterval(data.get("interval", "1m")),
            open=data.get("open", 0.0),
            high=data.get("high", 0.0),
            low=data.get("low", 0.0),
            close=data.get("close", 0.0),
            volume=data.get("volume", 0.0),
            is_closed=True,
        )
        await self._data_store.store_kline(bar)

    async def _store_depth(self, data: dict[str, Any]) -> None:
        if not settings.SYNC_DEPTH:
            return

        """存储深度数据"""
        import time
        from quant_trading_system.models.market import Depth

        timestamp = data.get("timestamp", 0)
        depth = Depth(
            timestamp=float(timestamp) if timestamp else time.time() * 1000,
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            bids=Depth.parse_levels(data.get("bids", [])),
            asks=Depth.parse_levels(data.get("asks", [])),
            sequence=data.get("sequence"),
        )
        await self._data_store.store_depth(depth)

    async def _store_historical_kline(self, data: dict[str, Any]) -> None:
        """
        存储历史K线批量数据

        data 格式: {
            "bars": [Bar, Bar, ...],  # Bar 对象列表
        }
        """
        bars = data.get("bars", [])
        for bar in bars:
            await self._data_store.store_kline(bar)

        # 批量刷新
        if bars:
            await self._data_store.flush_all()
            logger.debug("历史K线数据已存储", count=len(bars))


# ═══════════════════════════════════════════════════════════════
# 2. WebSocket 前端推送订阅器
# ═══════════════════════════════════════════════════════════════

class WebSocketSubscriber(MarketSubscriber):
    """
    WebSocket 前端推送订阅器

    职责：将行情数据推送到前端 WebSocket 客户端。
    通过现有的 ws_manager 广播机制发送给订阅了对应频道的前端用户。

    支持推送：
    - Ticker 行情（ticker/{symbol}）
    - K线数据（kline/{symbol}/{timeframe}）
    - 深度数据（depth/{symbol}）
    """

    @property
    def name(self) -> str:
        return "WebSocketSubscriber"

    async def on_event(self, event: MarketEvent) -> None:
        """处理行情事件：推送到前端 WebSocket"""
        try:
            if event.type == MarketEventType.TICK:
                await self._push_ticker(event.data)
            elif event.type == MarketEventType.KLINE:
                await self._push_kline(event.data)
            elif event.type == MarketEventType.DEPTH:
                await self._push_depth(event.data)
        except Exception as e:
            # WebSocket 推送失败不应影响其他逻辑
            logger.debug("WebSocket 推送失败", error=str(e), event_type=event.type.name)

    async def _push_ticker(self, data: dict[str, Any]) -> None:
        """推送 Ticker 到前端"""
        from quant_trading_system.api.websocket.market_ws import push_ticker

        symbol_key = data.get("symbol", "").replace("/", "").replace("-", "")
        if not symbol_key:
            return

        await push_ticker(symbol_key, {
            "symbol": data.get("symbol", ""),
            "exchange": data.get("exchange", ""),
            "last_price": data.get("last_price", 0.0),
            "bid_price": data.get("bid_price", 0.0),
            "ask_price": data.get("ask_price", 0.0),
            "volume": data.get("volume", 0.0),
            "turnover": data.get("turnover", 0.0),
            "timestamp": data.get("timestamp", 0),
        })

    async def _push_kline(self, data: dict[str, Any]) -> None:
        """推送 K线 到前端（包括未闭合和已闭合）"""
        from quant_trading_system.api.websocket.market_ws import push_kline

        symbol_key = data.get("symbol", "").replace("/", "").replace("-", "")
        timeframe = data.get("interval", "1m")
        if not symbol_key:
            return

        await push_kline(symbol_key, timeframe, {
            "symbol": data.get("symbol", ""),
            "exchange": data.get("exchange", ""),
            "timeframe": timeframe,
            "timestamp": data.get("timestamp", 0),
            "open": data.get("open", 0.0),
            "high": data.get("high", 0.0),
            "low": data.get("low", 0.0),
            "close": data.get("close", 0.0),
            "volume": data.get("volume", 0.0),
            "is_closed": data.get("is_closed", False),
        })

    async def _push_depth(self, data: dict[str, Any]) -> None:
        """推送深度数据到前端"""
        from quant_trading_system.api.websocket.market_ws import push_depth

        symbol_key = data.get("symbol", "").replace("/", "").replace("-", "")
        if not symbol_key:
            return

        await push_depth(symbol_key, {
            "symbol": data.get("symbol", ""),
            "exchange": data.get("exchange", ""),
            "bids": data.get("bids", []),
            "asks": data.get("asks", []),
            "timestamp": data.get("timestamp", 0),
        })


# ═══════════════════════════════════════════════════════════════
# 3. 交易引擎订阅器
# ═══════════════════════════════════════════════════════════════

class TradingEngineSubscriber(MarketSubscriber):
    """
    交易引擎订阅器

    职责：将行情数据转发给实盘/模拟交易引擎。
    交易引擎接收数据后计算交易指标、触发策略信号等。

    工作流程：
    1. 接收 Tick/K线 事件
    2. 转换为模型对象
    3. 通过全局事件引擎（EventEngine）发送 TICK/BAR 事件
    4. K线数据同时更新 KLineEngine 的内存缓冲区
    """

    def __init__(self) -> None:
        self._event_engine: Any = None
        self._kline_engine: Any = None

    @property
    def name(self) -> str:
        return "TradingEngineSubscriber"

    async def start(self) -> None:
        """启动：获取事件引擎和K线引擎的引用"""
        try:
            from quant_trading_system.core.container import container
            self._event_engine = container.event_engine
        except Exception as e:
            logger.warning("获取事件引擎失败，交易事件将不会被分发", error=str(e))

        logger.info("交易引擎订阅器已启动")

    async def stop(self) -> None:
        """停止"""
        logger.info("交易引擎订阅器已停止")

    def set_kline_engine(self, kline_engine: Any) -> None:
        """注入 KLineEngine 引用（由 MarketService 调用）"""
        self._kline_engine = kline_engine

    async def on_event(self, event: MarketEvent) -> None:
        """处理行情事件：转发给交易引擎"""
        if event.type == MarketEventType.TICK:
            await self._process_tick(event.data)
        elif event.type == MarketEventType.KLINE:
            await self._process_kline(event.data)

    async def _process_tick(self, data: dict[str, Any]) -> None:
        """处理 Tick 事件：发布到系统事件引擎 + 合成K线"""
        from quant_trading_system.models.market import Tick
        from quant_trading_system.core.events import Event, EventType

        tick = Tick(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            timestamp=data.get("timestamp", 0),
            last_price=data.get("last_price", 0.0),
            bid_price=data.get("bid_price", 0.0),
            ask_price=data.get("ask_price", 0.0),
            bid_size=data.get("bid_size", 0.0),
            ask_size=data.get("ask_size", 0.0),
            volume=data.get("volume", 0.0),
            turnover=data.get("turnover", 0.0),
            is_trade=data.get("is_trade", False),
            trade_id=data.get("trade_id", ""),
        )

        # 发送到全局事件引擎（供策略等模块消费）
        if self._event_engine:
            await self._event_engine.put(Event(type=EventType.TICK, data=tick))

        # 驱动K线合成引擎
        if self._kline_engine:
            await self._kline_engine.process_tick(tick)

    async def _process_kline(self, data: dict[str, Any]) -> None:
        """处理 K线事件：更新缓冲区 + 发布已闭合K线到事件引擎"""
        from quant_trading_system.models.market import Bar
        from quant_trading_system.core.events import Event, EventType

        bar = Bar(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            timestamp=data.get("timestamp", 0),
            timeframe=KlineInterval(data.get("interval", "1m")),
            open=data.get("open", 0.0),
            high=data.get("high", 0.0),
            low=data.get("low", 0.0),
            close=data.get("close", 0.0),
            volume=data.get("volume", 0.0),
            is_closed=data.get("is_closed", False),
        )

        # 更新 KLineEngine 缓冲区
        if self._kline_engine:
            symbol_key = bar.symbol.replace("/", "").replace("-", "")
            self._kline_engine.update_bar_from_ws(symbol_key, bar)

        # 仅已闭合K线发送到全局事件引擎
        if bar.is_closed and self._event_engine:
            await self._event_engine.put(Event(type=EventType.BAR, data=bar))
