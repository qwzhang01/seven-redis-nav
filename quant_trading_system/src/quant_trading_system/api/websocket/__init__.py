"""
WebSocket 实时推送模块
=====================

提供行情、交易、策略信号的实时 WebSocket 推送服务。

模块列表：
- manager    : WebSocket 连接管理器（核心）
- market_ws  : 行情实时推送路由
- trading_ws : 交易事件推送路由
- strategy_ws: 策略信号推送路由
"""

from .manager import ws_manager
from .market_ws import router as market_ws_router
from .trading_ws import router as trading_ws_router
from .strategy_ws import router as strategy_ws_router

__all__ = [
    "ws_manager",
    "market_ws_router",
    "trading_ws_router",
    "strategy_ws_router",
]
