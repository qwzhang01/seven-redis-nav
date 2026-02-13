"""
API路由模块
===========

量化交易系统API路由模块，提供完整的交易系统接口。

模块组成：
- market_router: 市场数据接口，提供行情订阅、K线数据、市场深度等功能
- strategy_router: 策略管理接口，提供策略创建、启动、停止、监控等功能
- trading_router: 交易执行接口，提供下单、撤单、持仓查询、账户信息等功能
- backtest_router: 回测接口，提供策略回测执行和结果查询功能
- system_router: 系统管理接口，提供系统状态、配置、健康检查等功能

这些路由模块共同构成了量化交易系统的完整API接口层。
"""

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
