"""
行情数据服务模块（重构版）

架构：
- MarketEventBus：行情事件总线（发布/订阅模式核心）
- ExchangeConnector：交易所连接器（适配器模式，只负责对接交易所）
- MarketSubscriber：行情订阅器接口（策略模式，3个具体实现）
- HistoricalDataSyncer：历史数据同步器（配置驱动 + 事件机制）
- MarketService：统一对外接口（门面模式）
- KLineEngine：K线内存缓冲与合成
"""

from quant_trading_system.services.market.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
    MarketSubscriber,
)
from quant_trading_system.services.market.exchange_connector import (
    BinanceConnector,
    ExchangeConnector,
    MockConnector,
    WebSocketClient,
)
from quant_trading_system.services.market.market_subscribers import (
    DatabaseSubscriber,
    TradingEngineSubscriber,
    WebSocketSubscriber,
)
from quant_trading_system.services.market.historical_kline_syncer import (
    HistoricalKlineSyncer,
    SyncerConfig,
)

from quant_trading_system.services.market.kline_engine import KLineEngine
from quant_trading_system.services.market.market_service import MarketService

__all__ = [
    # 事件总线
    "MarketEventBus",
    "MarketEvent",
    "MarketEventType",
    "MarketSubscriber",
    # 交易所连接器
    "ExchangeConnector",
    "BinanceConnector",
    "MockConnector",
    "WebSocketClient",
    # 订阅器
    "DatabaseSubscriber",
    "WebSocketSubscriber",
    "TradingEngineSubscriber",
    # 历史数据同步
    "HistoricalKlineSyncer",
    "SyncerConfig",
    # K线引擎
    "KLineEngine",
    # 对外服务
    "MarketService",
]
