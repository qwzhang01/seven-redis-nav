"""
Admin 端（管理员）路由聚合包
============================

包含所有面向管理员的 API 接口，统一挂载在 /api/v1/m/ 前缀下。

模块列表：
- strategy          : 策略创建、启停、参数管理
- system            : 系统信息、配置、健康检查、性能指标
- market            : 行情订阅配置管理、手动同步任务管理
- stats             : 系统统计分析（用户/策略/交易/行情）
- logs              : 日志审计（系统/交易/风控/审计日志、风控告警）
- signal_admin      : 信号审核管理
- leaderboard_admin : 排行榜刷新管理
"""

from fastapi import APIRouter

from quant_trading_system.api.strategies.api.strategy import router as strategy_router
from quant_trading_system.api.system.api.system import router as system_router
from quant_trading_system.api.system.api.health import router as health_router
from quant_trading_system.api.market.api.subscription import router as subscription_router
from quant_trading_system.api.market.api.sync_task import router as sync_task_router
from quant_trading_system.api.stats.api.stats import router as stats_router
from quant_trading_system.api.logs.api.logs import router as logs_router
from quant_trading_system.api.signal.api.signal_admin import router as signal_admin_router
from quant_trading_system.api.leaderboard.api.leaderboard_admin import router as leaderboard_admin_router

# Admin 端聚合路由
m_router = APIRouter()

m_router.include_router(strategy_router, prefix="/strategy", tags=["Admin-策略管理"])
m_router.include_router(system_router, prefix="/system", tags=["Admin-系统管理"])
m_router.include_router(health_router, prefix="", tags=["Admin-健康检查"])
m_router.include_router(subscription_router, prefix="/market/subscriptions", tags=["Admin-订阅管理"])
m_router.include_router(sync_task_router, prefix="/market/sync-tasks", tags=["Admin-同步任务"])
m_router.include_router(stats_router, prefix="/stats", tags=["Admin-统计分析"])
m_router.include_router(logs_router, prefix="/logs", tags=["Admin-日志审计"])
m_router.include_router(signal_admin_router, prefix="/signal", tags=["Admin-信号管理"])
m_router.include_router(leaderboard_admin_router, prefix="/leaderboard", tags=["Admin-排行榜管理"])

__all__ = ["m_router"]
