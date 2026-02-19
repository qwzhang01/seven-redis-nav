"""
Admin 行情管理路由包
===================

提供行情订阅配置管理和手动同步任务管理的 API 接口。
"""

from fastapi import APIRouter

from quant_trading_system.api.admin.api.subscription import router as subscription_router
from quant_trading_system.api.admin.api.sync_task import router as sync_task_router

# Admin 行情管理聚合路由
admin_market_router = APIRouter()

admin_market_router.include_router(
    subscription_router,
    prefix="/subscriptions",
    tags=["Admin-订阅管理"],
)
admin_market_router.include_router(
    sync_task_router,
    prefix="/sync-tasks",
    tags=["Admin-同步任务"],
)

__all__ = ["admin_market_router"]
