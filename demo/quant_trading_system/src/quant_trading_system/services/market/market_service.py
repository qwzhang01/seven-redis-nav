"""
行情服务（重构版）
==================

统一的行情数据服务对外接口。

架构重构要点：
1. 交易所对接层（ExchangeConnector）—— 纯粹负责对接交易所
2. 行情事件总线（MarketEventBus）—— 发布/订阅模式解耦生产与消费
3. 三个订阅器各司其职：
   - DatabaseSubscriber：行情数据异步存储到数据库
   - WebSocketSubscriber：实时行情推送到前端 WebSocket
   - TradingEngineSubscriber：行情数据转发给交易引擎
4. 历史数据同步器（HistoricalDataSyncer）—— 配置驱动 + 事件机制异步拉取

对外提供：
- 历史行情查询接口
- 实时行情 WebSocket 订阅（通过 WebSocketSubscriber 自动推送）
- 添加/移除交易所数据源
- 订阅/取消订阅交易对

设计模式：
- 门面模式（Facade Pattern）：MarketService 作为行情子系统的统一入口
- 依赖注入（DI）：事件总线、连接器、订阅器通过构造函数注入
"""

import asyncio
from typing import Any

import structlog

from quant_trading_system.core.config import settings
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.models.market import Bar, BarArray

# 事件总线
from quant_trading_system.engines.market_event_bus import (
    MarketEventBus,
    MarketEventType,
)

# 交易所连接器
from quant_trading_system.exchange_adapter.binance_connector import (
    BinanceConnector,
    ExchangeConnector,
)

# 订阅器
from quant_trading_system.services.market.market_subscribers import (
    DatabaseSubscriber,
    TradingEngineSubscriber,
    WebSocketSubscriber,
)

# 历史数据同步器
from quant_trading_system.services.market.historical_kline_syncer import (
    HistoricalKlineSyncer,
    SyncerConfig,
)
from quant_trading_system.exchange_adapter.binance_rest_client import BinanceRestClient

# K线引擎（保持原有实现，负责内存缓冲和K线合成）
from quant_trading_system.services.market.kline_engine import KLineEngine

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 单例工厂
# ═══════════════════════════════════════════════════════════════

def get_market_service(event_engine: Any = None) -> "MarketService":
    """
    获取 MarketService 单例实例

    Args:
        event_engine: 系统事件引擎（仅首次创建时生效）

    Returns:
        MarketService 实例
    """
    from quant_trading_system.core.container import container

    if container._market_service is None:
        container.market_service = MarketService()

    return container.market_service


# ═══════════════════════════════════════════════════════════════
# MarketService（门面模式）
# ═══════════════════════════════════════════════════════════════

class MarketService:
    """
    行情服务（门面模式）

    作为行情子系统的统一入口，协调以下组件：
    - MarketEventBus：事件分发中心
    - ExchangeConnector：交易所连接器（多个）
    - 3个订阅器：数据库存储、WebSocket推送、交易引擎
    - HistoricalDataSyncer：历史数据同步器
    - KLineEngine：K线内存缓冲与合成

    使用流程：
        service = MarketService()
        await service.start()
        await service.add_exchange("binance")
        await service.subscribe(["BTC/USDT"], exchange="binance")
    """

    def __init__(
        self,
    ) -> None:
        # ── 核心组件 ──
        self._event_bus = MarketEventBus()
        self._kline_engine = KLineEngine()

        # ── 交易所连接器 ──
        self._connectors: dict[str, ExchangeConnector] = {}

        # ── 3个订阅器 ──
        self._db_subscriber = DatabaseSubscriber()
        self._ws_subscriber = WebSocketSubscriber()
        self._trading_subscriber = TradingEngineSubscriber()

        # 注入 KLineEngine 引用给交易引擎订阅器
        self._trading_subscriber.set_kline_engine(self._kline_engine)

        # ── 历史数据同步器 ──
        self._historical_syncer = HistoricalKlineSyncer(
            binance_api=BinanceRestClient(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_SECRET_KEY,
            ),
            event_bus=self._event_bus,
        )

        # ── 运行状态 ──
        self._running = False

        # ── 统计 ──
        self._tick_count = 0
        self._kline_count = 0
        self._depth_count = 0

    async def start(self) -> None:
        """
        启动行情服务

        流程：
        1. 注册3个订阅器到事件总线
        2. 启动所有订阅器
        3. 启动所有已添加的连接器
        4. 如果配置了启动时同步，执行历史数据同步
        """
        if self._running:
            return

        self._running = True

        # ── 注册订阅器到事件总线 ──
        self._register_subscribers()

        # ── 启动所有订阅器 ──
        await self._event_bus.start_all_subscribers()

        # ── 启动所有连接器 ──
        for connector in self._connectors.values():
            await connector.start()

        # ── 启动时历史数据同步 ──
        if self._historical_syncer.config.sync_on_startup:
            asyncio.create_task(
                self._historical_syncer.sync_on_startup(),
                name="historical-sync-on-startup",
            )

        logger.info(
            "行情服务已启动",
            connectors=list(self._connectors.keys()),
            subscribers=self._event_bus.stats.get("subscribers", []),
        )

    async def stop(self) -> None:
        """停止行情服务"""
        if not self._running:
            return

        self._running = False

        # 停止所有连接器
        for connector in self._connectors.values():
            await connector.stop()

        # 停止所有订阅器
        await self._event_bus.stop_all_subscribers()

        # 关闭历史同步器的 API 客户端
        self._historical_syncer.close()

        logger.info("行情服务已停止")

    def _register_subscribers(self) -> None:
        """注册3个订阅器到事件总线"""
        # 实时行情事件类型
        realtime_events = [
            MarketEventType.TICK,
            MarketEventType.KLINE,
            MarketEventType.DEPTH,
        ]

        # 1. 数据库存储订阅器 —— 订阅所有实时 + 历史事件
        self._event_bus.subscribe_many(realtime_events, self._db_subscriber)
        self._event_bus.subscribe(MarketEventType.HISTORICAL_KLINE, self._db_subscriber)

        # 2. WebSocket 前端推送订阅器 —— 仅订阅实时事件
        self._event_bus.subscribe_many(realtime_events, self._ws_subscriber)

        # 3. 交易引擎订阅器 —— 订阅 Tick 和 K线
        self._event_bus.subscribe(MarketEventType.TICK, self._trading_subscriber)
        self._event_bus.subscribe(MarketEventType.KLINE, self._trading_subscriber)

    # ═══════════════════════════════════════════════════════════
    # 交易所管理
    # ═══════════════════════════════════════════════════════════

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
            exchange: 交易所名称 (binance, mock)
            market_type: 市场类型 (spot, futures)
            api_key: API 密钥
            api_secret: API 密钥
        """
        connector_key = f"{exchange}_{market_type}"

        if connector_key in self._connectors:
            logger.warning("交易所已添加", exchange=exchange)
            return

        # 创建连接器（适配器模式）
        connector: ExchangeConnector
        if exchange == "binance":
            connector = BinanceConnector(
                event_bus=self._event_bus,
                market_type=market_type,
                api_key=api_key or settings.BINANCE_API_KEY,
                api_secret=api_secret or settings.BINANCE_SECRET_KEY,
            )
        elif exchange == "mock":
            from quant_trading_system.mock.mock_connector import MockConnector
            connector = MockConnector(
                event_bus=self._event_bus,
                tick_interval=kwargs.get("tick_interval", 0.5),
                depth_interval=kwargs.get("depth_interval", 1.0),
                kline_intervals=kwargs.get("kline_intervals", ["1m", "5m", "15m", "1h"]),
            )
        else:
            logger.error("不支持的交易所", exchange=exchange)
            return

        self._connectors[connector_key] = connector

        # 如果服务已运行，立即启动连接器
        if self._running:
            await connector.start()

        logger.info("交易所已添加", exchange=exchange, market_type=market_type)

    # ═══════════════════════════════════════════════════════════
    # 行情订阅
    # ═══════════════════════════════════════════════════════════

    async def subscribe(
        self,
        symbols: list[str],
        exchange: str = "binance",
        market_type: str = "spot",
    ) -> None:
        """
        订阅实时行情

        Args:
            symbols: 交易对列表
            exchange: 交易所
            market_type: 市场类型
        """
        connector_key = f"{exchange}_{market_type}"
        connector = self._connectors.get(connector_key)

        if not connector:
            logger.error("交易所未添加", exchange=exchange, market_type=market_type)
            return

        await connector.subscribe(symbols)
        logger.info("已订阅行情", symbols=symbols, exchange=exchange)

    async def unsubscribe(
        self,
        symbols: list[str],
        exchange: str = "binance",
        market_type: str = "spot",
    ) -> None:
        """取消订阅"""
        connector_key = f"{exchange}_{market_type}"
        connector = self._connectors.get(connector_key)
        if not connector:
            return
        await connector.unsubscribe(symbols)

    # ═══════════════════════════════════════════════════════════
    # 历史数据查询（对外接口）
    # ═══════════════════════════════════════════════════════════

    def get_bars(
        self,
        symbol: str,
        timeframe: KlineInterval,
        limit: int | None = None,
    ) -> list[Bar]:
        """获取K线数据（从内存缓冲区）"""
        return self._kline_engine.get_bars(symbol, timeframe, limit)

    def get_bar_array(
        self,
        symbol: str,
        timeframe: KlineInterval,
        limit: int | None = None,
    ) -> BarArray:
        """获取K线数组"""
        return self._kline_engine.get_bar_array(symbol, timeframe, limit)

    def get_current_bar(
        self,
        symbol: str,
        timeframe: KlineInterval,
    ) -> Bar | None:
        """获取当前未完成的K线"""
        return self._kline_engine.get_current_bar(symbol, timeframe)

    async def load_history(
        self,
        symbols: list[str] | None = None,
        timeframes: list[KlineInterval] | None = None,
        limit: int = 500,
        exchange: str = "binance",
        source: str = "exchange",
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        拉取历史K线数据并预加载到内存缓冲区

        兼容旧接口，内部委托给 KLineEngine。

        Args:
            symbols: 交易对列表
            timeframes: 时间周期列表
            limit: 拉取数量
            exchange: 交易所
            source: 数据源 ("exchange" 或 "database")
            save_to_db: 是否保存到数据库

        Returns:
            加载统计
        """
        return await self._kline_engine.load_history(
            symbols=symbols,
            timeframes=timeframes,
            limit=limit,
            exchange=exchange,
            source=source,
            save_to_db=save_to_db,
        )

    # ═══════════════════════════════════════════════════════════
    # 属性与统计
    # ═══════════════════════════════════════════════════════════

    @property
    def event_bus(self) -> MarketEventBus:
        """获取事件总线（供外部注册自定义订阅器）"""
        return self._event_bus

    @property
    def kline_engine(self) -> KLineEngine:
        """获取K线引擎"""
        return self._kline_engine

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "running": self._running,
            "connectors": list(self._connectors.keys()),
            "event_bus": self._event_bus.stats,
            "kline_stats": self._kline_engine.stats,
            "historical_syncer": self._historical_syncer.stats,
        }
