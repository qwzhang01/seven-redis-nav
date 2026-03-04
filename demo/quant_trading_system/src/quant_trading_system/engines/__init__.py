"""
引擎模块
========

仅导出 engines/ 目录下的引擎代码。
业务服务请直接从 services/ 子模块导入。
"""

# ── 1. 全局事件引擎 ──
from quant_trading_system.engines.event_engine import (  # noqa: F401
    EventEngine,
    EventType,
    EventPriority,
    Event,
    EventHandler,
    SyncEventHandler,
    get_event_engine,
)

# ── 2. 行情事件总线 ──
from quant_trading_system.engines.market_event_bus import (  # noqa: F401
    MarketEventBus,
    MarketEventType,
    MarketEvent,
    MarketSubscriber,
)

# ── 3. 信号事件总线 ──
from quant_trading_system.engines.signal_event_bus import (  # noqa: F401
    SignalEventBus,
    SignalEventType,
    SignalEvent,
    signal_event_bus,
)


def get_signal_event_bus() -> SignalEventBus:
    """获取信号事件总线单例"""
    return signal_event_bus


__all__ = [
    # 全局事件引擎
    "EventEngine",
    "EventType",
    "EventPriority",
    "Event",
    "EventHandler",
    "SyncEventHandler",
    "get_event_engine",
    # 行情事件总线
    "MarketEventBus",
    "MarketEventType",
    "MarketEvent",
    "MarketSubscriber",
    # 信号事件总线
    "SignalEventBus",
    "SignalEventType",
    "SignalEvent",
    "signal_event_bus",
    "get_signal_event_bus",
]
