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
)

# ── 4. 信号监听引擎（延迟导入，避免循环依赖） ──
# SignalStreamEngine 依赖 services → strategy，而 strategy 又依赖 engines，
# 因此在模块初始化阶段不能直接导入，需通过 __getattr__ 延迟加载。


def __getattr__(name: str):
    if name == "SignalStreamEngine":
        from quant_trading_system.engines.signal_stream_engine import SignalStreamEngine
        return SignalStreamEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    # 信号监听引擎
    "SignalStreamEngine",
]
