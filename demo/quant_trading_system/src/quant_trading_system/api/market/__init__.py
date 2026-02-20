"""
市场数据业务域
===============

提供市场行情数据服务，包括行情订阅、K线数据、实时Tick、市场深度等功能。
Admin 端行情管理（订阅配置、手动同步任务）也归属本域。

模块组成：
- api: 市场数据API路由
- schemas: 市场数据模型和验证模式
- services: 市场数据业务逻辑服务
- repositories: 市场数据访问层
- models: 市场数据模型定义
"""

from .api.market import router as market_router
from .api.subscription import router as subscription_router
from .api.sync_task import router as sync_task_router

__all__ = [
    "market_router",
    "subscription_router",
    "sync_task_router",
]
