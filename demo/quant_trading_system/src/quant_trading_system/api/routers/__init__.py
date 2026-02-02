"""API路由模块"""

from quant_trading_system.api.routers.market import router as market_router
from quant_trading_system.api.routers.strategy import router as strategy_router
from quant_trading_system.api.routers.trading import router as trading_router
from quant_trading_system.api.routers.backtest import router as backtest_router
from quant_trading_system.api.routers.system import router as system_router

__all__ = [
    "market_router",
    "strategy_router",
    "trading_router",
    "backtest_router",
    "system_router",
]
