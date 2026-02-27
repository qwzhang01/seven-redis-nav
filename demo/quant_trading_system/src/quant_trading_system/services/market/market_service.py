"""
行情服务
========

统一的行情数据服务接口
"""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

import structlog

from quant_trading_system.core.config import settings
from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.market import Bar, Depth, Tick, TimeFrame
from quant_trading_system.services.market.data_collector import (
    BinanceDataCollector,
    DataCollector,
    OKXDataCollector,
)
from quant_trading_system.services.market.kline_engine import KLineEngine

logger = structlog.get_logger(__name__)

# 回调类型定义
TickCallback = Callable[[Tick], Coroutine[Any, Any, None]]
BarCallback = Callable[[Bar], Coroutine[Any, Any, None]]
DepthCallback = Callable[[Depth], Coroutine[Any, Any, None]]

# 全局MarketService实例
_market_service: "MarketService | None" = None


def get_market_service(event_engine: EventEngine | None = None) -> "MarketService":
    """
    获取MarketService单例实例

    Args:
        event_engine: 事件引擎实例，如果为None则创建新的

    Returns:
        MarketService实例
    """
    global _market_service

    if _market_service is None:
        _market_service = MarketService(event_engine=event_engine)

    return _market_service


class MarketService:
    """
    行情服务

    提供统一的行情数据接口，包括：
    - 多交易所数据聚合
    - K线合成
    - 数据订阅和分发
    - 数据缓存
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
    ) -> None:
        self._event_engine = event_engine

        # 数据采集器
        self._collectors: dict[str, DataCollector] = {}

        # K线引擎
        self._kline_engine = KLineEngine()

        # 回调
        self._tick_callbacks: list[TickCallback] = []
        self._bar_callbacks: dict[TimeFrame | None, list[BarCallback]] = defaultdict(list)
        self._depth_callbacks: list[DepthCallback] = []

        # 运行状态
        self._running = False

        # 统计
        self._tick_count = 0
        self._depth_count = 0
        self._kline_count = 0

    async def start(self) -> None:
        """启动行情服务"""
        if self._running:
            return

        self._running = True

        # 启动所有采集器
        for collector in self._collectors.values():
            await collector.start()

        logger.info("Market service started")

    async def stop(self) -> None:
        """停止行情服务"""
        if not self._running:
            return

        self._running = False

        # 停止所有采集器
        for collector in self._collectors.values():
            await collector.stop()

        logger.info("Market service stopped")

    async def add_exchange(
        self,
        exchange: str,
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
        **kwargs: Any,
    ) -> None:
        """
        添加交易所数据源

        Args:
            exchange: 交易所名称 (binance, okx, huobi 等)
            market_type: 市场类型 (spot, futures, swap)
            api_key: API密钥
            api_secret: API密钥
        """
        collector_key = f"{exchange}_{market_type}"

        if collector_key in self._collectors:
            logger.warning(f"Exchange already added", exchange=exchange)
            return

        # 创建采集器
        if exchange == "binance":
            collector = BinanceDataCollector(
                market_type=market_type,
                api_key=api_key or settings.BINANCE_API_KEY,
                api_secret=api_secret or settings.BINANCE_SECRET_KEY,
            )
        elif exchange == "okx":
            collector = OKXDataCollector(
                api_key=api_key or settings.OKX_API_KEY,
                api_secret=api_secret or settings.OKX_SECRET_KEY,
                passphrase=kwargs.get("passphrase", "") or settings.OKX_PASSPHRASE,
            )
        else:
            logger.error(f"Unsupported exchange", exchange=exchange)
            return

        # 设置回调
        collector.add_callback("tick", self._on_tick_data)
        collector.add_callback("depth", self._on_depth_data)
        collector.add_callback("kline", self._on_kline_data)

        self._collectors[collector_key] = collector

        # 如果服务已经在运行，立即启动新添加的采集器
        if self._running:
            logger.info(f"Market service is running, starting new collector immediately",
                       exchange=exchange, market_type=market_type)
            await collector.start()

        logger.info(f"Exchange added", exchange=exchange, market_type=market_type)

    async def subscribe(
        self,
        symbols: list[str],
        exchange: str = "binance",
        market_type: str = "spot",
    ) -> None:
        """
        订阅行情

        Args:
            symbols: 交易对列表
            exchange: 交易所
            market_type: 市场类型
        """
        collector_key = f"{exchange}_{market_type}"

        if collector_key not in self._collectors:
            logger.error(f"Exchange not found", exchange=exchange)
            return

        collector = self._collectors[collector_key]
        logger.info(f"Subscribing symbols on collector",
                   exchange=exchange, market_type=market_type,
                   symbols=symbols,
                   collector_running=collector.is_running,
                   ws_connected=getattr(collector, '_ws_client', None) and getattr(collector._ws_client, 'is_connected', False))
        await collector.subscribe(symbols)

    async def unsubscribe(
        self,
        symbols: list[str],
        exchange: str = "binance",
        market_type: str = "spot",
    ) -> None:
        """取消订阅"""
        collector_key = f"{exchange}_{market_type}"

        if collector_key not in self._collectors:
            return

        collector = self._collectors[collector_key]
        await collector.unsubscribe(symbols)

    def add_tick_callback(self, callback: TickCallback) -> None:
        """添加Tick回调"""
        self._tick_callbacks.append(callback)

    def add_bar_callback(
        self,
        callback: BarCallback,
        timeframe: TimeFrame | None = None,
    ) -> None:
        """添加K线回调"""
        self._bar_callbacks[timeframe].append(callback)
        self._kline_engine.add_callback(callback, timeframe)

    def add_depth_callback(self, callback: DepthCallback) -> None:
        """添加深度回调"""
        self._depth_callbacks.append(callback)

    async def _on_tick_data(self, data: dict[str, Any]) -> None:
        """处理Tick数据"""
        tick = Tick(
            symbol=data["symbol"],
            exchange=data["exchange"],
            timestamp=data["timestamp"],
            last_price=data["last_price"],
            bid_price=data.get("bid_price", 0.0),
            ask_price=data.get("ask_price", 0.0),
            bid_size=data.get("bid_size", 0.0),
            ask_size=data.get("ask_size", 0.0),
            volume=data.get("volume", 0.0),
            turnover=data.get("turnover", 0.0),
            is_trade=data.get("is_trade", False),
            trade_id=data.get("trade_id", ""),
        )

        self._tick_count += 1

        # 合成K线
        await self._kline_engine.process_tick(tick)

        # 发送事件
        if self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.TICK,
                data=tick,
            ))

        # 通知回调
        if self._tick_callbacks:
            tasks = [cb(tick) for cb in self._tick_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _on_kline_data(self, data: dict[str, Any]) -> None:
        """处理K线数据（来自交易所WebSocket推送）"""
        bar = Bar(
            symbol=data["symbol"],
            exchange=data["exchange"],
            timestamp=data["timestamp"],
            timeframe=TimeFrame(data["interval"]),
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            volume=data["volume"],
            is_closed=data.get("is_closed", False),
        )

        self._kline_count += 1

        # 更新K线引擎的缓冲区
        symbol_key = bar.symbol.replace("/", "").replace("-", "")
        self._kline_engine.update_bar_from_ws(symbol_key, bar)

        # 发送事件（仅已关闭的K线）
        if bar.is_closed and self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.BAR,
                data=bar,
            ))

        # 通知K线回调（仅已关闭的K线）
        if bar.is_closed:
            callbacks = self._bar_callbacks.get(bar.timeframe, []) + self._bar_callbacks.get(None, [])
            if callbacks:
                tasks = [cb(bar) for cb in callbacks]
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _on_depth_data(self, data: dict[str, Any]) -> None:
        """处理深度数据"""
        from quant_trading_system.models.market import DepthLevel

        depth = Depth(
            symbol=data["symbol"],
            exchange=data["exchange"],
            timestamp=data["timestamp"],
            bids=[DepthLevel(price=b[0], size=b[1]) for b in data.get("bids", [])],
            asks=[DepthLevel(price=a[0], size=a[1]) for a in data.get("asks", [])],
        )

        self._depth_count += 1

        # 发送事件
        if self._event_engine:
            await self._event_engine.put(Event(
                type=EventType.DEPTH,
                data=depth,
            ))

        # 通知回调
        if self._depth_callbacks:
            tasks = [cb(depth) for cb in self._depth_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        limit: int | None = None,
    ) -> list[Bar]:
        """获取K线数据"""
        return self._kline_engine.get_bars(symbol, timeframe, limit)

    def get_bar_array(
        self,
        symbol: str,
        timeframe: TimeFrame,
        limit: int | None = None,
    ):
        """获取K线数组"""
        return self._kline_engine.get_bar_array(symbol, timeframe, limit)

    async def load_history(
        self,
        symbols: list[str] | None = None,
        timeframes: list[TimeFrame] | None = None,
        limit: int = 500,
        exchange: str = "binance",
        source: str = "exchange",
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        拉取历史K线数据并预加载到内存缓冲区

        Args:
            symbols: 交易对列表，为 None 则使用 DefaultTradingPair 配置
            timeframes: 时间周期列表，为 None 则使用默认周期
            limit: 每个周期拉取的K线数量
            exchange: 交易所名称
            source: 数据源，"exchange" 从交易所拉取，"database" 从数据库加载
            save_to_db: 从交易所拉取后是否同时保存到数据库

        Returns:
            各交易对加载的K线数量统计
        """
        return await self._kline_engine.load_history(
            symbols=symbols,
            timeframes=timeframes,
            limit=limit,
            exchange=exchange,
            source=source,
            save_to_db=save_to_db,
        )

    def get_current_bar(
        self,
        symbol: str,
        timeframe: TimeFrame,
    ) -> Bar | None:
        """获取当前未完成的K线"""
        return self._kline_engine.get_current_bar(symbol, timeframe)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "running": self._running,
            "tick_count": self._tick_count,
            "depth_count": self._depth_count,
            "kline_count": self._kline_count,
            "collectors": list(self._collectors.keys()),
            "kline_stats": self._kline_engine.stats,
        }
