"""
策略管理业务域
===============

提供策略的完整生命周期管理，包括策略创建、启动、停止、监控等功能。

模块组成：
- api: 策略管理API路由
- schemas: 策略数据模型和验证模式
- services: 策略业务逻辑服务
- repositories: 策略数据访问层
- models: 策略数据模型定义
"""

from .api.strategy_admin import router as strategy_router
from .api.strategy import router as strategy_c_router

__all__ = [
    "strategy_router",
    "strategy_c_router",
]
