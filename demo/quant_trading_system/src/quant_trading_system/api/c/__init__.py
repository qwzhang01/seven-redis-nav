"""
C 端（普通用户）路由聚合包
==========================

包含所有面向普通用户的 API 接口，统一挂载在 /api/v1/c/ 前缀下。

模块列表：
- user       : 用户注册、登录、密码管理、API 密钥管理
- market     : 行情订阅、K线、Tick、深度数据
- trading    : 下单、订单管理、持仓、账户
- backtest   : 策略回测
- signal     : 信号广场、信号订阅
- leaderboard: 排行榜
"""

from fastapi import APIRouter

from quant_trading_system.api.users.api.user import router as user_router
from quant_trading_system.api.users.api.signal_follow import router as signal_follow_router
from quant_trading_system.api.market.api.market import router as market_router
from quant_trading_system.api.trading.api.trading import router as trading_router
from quant_trading_system.api.backtest.api.backtest import router as backtest_router
from quant_trading_system.api.signal.api.signal import router as signal_router
from quant_trading_system.api.leaderboard.api.leaderboard import router as leaderboard_router

# C 端聚合路由
c_router = APIRouter()

c_router.include_router(user_router, prefix="/user", tags=["C端-用户管理"])
c_router.include_router(signal_follow_router, prefix="/user/signal-follows", tags=["C端-信号跟单"])
c_router.include_router(market_router, prefix="/market", tags=["C端-行情数据"])
c_router.include_router(trading_router, prefix="/trading", tags=["C端-交易管理"])
c_router.include_router(backtest_router, prefix="/backtest", tags=["C端-策略回测"])
c_router.include_router(signal_router, prefix="/signal", tags=["C端-信号广场"])
c_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["C端-排行榜"])

__all__ = ["c_router"]
