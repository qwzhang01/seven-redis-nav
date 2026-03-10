"""
行情数据服务模块
================

架构：
- MarketService：统一对外接口（门面模式）
- KLineEngine：K线内存缓冲与合成
- KLineHistoryLoader：历史K线数据加载
- MarketDataWriter：行情数据写入（存储到 TimescaleDB）
- MarketDataReader：行情数据读取（从 TimescaleDB 查询）
- DatabaseSubscriber：行情数据异步存储订阅器
- WebSocketSubscriber：实时行情前端推送订阅器
- IndicatorSubscriber：指标计算推送订阅器
- MarketDataDispatcher：行情数据分发器（转发给事件引擎和K线引擎）
- HistoricalKlineSyncer：历史数据同步器
"""

from quant_trading_system.services.market.historical_kline_syncer import (
    HistoricalKlineSyncer,
)
from quant_trading_system.services.market.kline_engine import KLineEngine, \
    KLineBuffer
from quant_trading_system.services.market.kline_history_loader import \
    KLineHistoryLoader
from quant_trading_system.services.market.market_data_reader import (
    MarketDataReader,
    get_market_data_reader,
)
from quant_trading_system.services.market.market_data_writer import (
    MarketDataWriter,
    get_market_data_writer,
)
# ── 本模块核心类 ──
from quant_trading_system.services.market.market_service import MarketService
from quant_trading_system.services.market.market_subscribers import (
    DatabaseSubscriber,
    WebSocketSubscriber,
    MarketDataDispatcher,
    IndicatorSubscriber
)

__all__ = [
    # 对外服务
    "MarketService",
    # K线引擎
    "KLineEngine",
    "KLineBuffer",
    "KLineHistoryLoader",
    # 数据读写
    "MarketDataWriter",
    "get_market_data_writer",
    "MarketDataReader",
    "get_market_data_reader",
    # 订阅器
    "DatabaseSubscriber",
    "WebSocketSubscriber",
    "IndicatorSubscriber",
    "MarketDataDispatcher",
    # 历史数据同步
    "HistoricalKlineSyncer",
]
