"""
健康检查业务域
===============

提供系统健康检查和监控功能，包括基础健康检查、数据库检查、系统指标等。

模块组成：
- api: 健康检查API路由
- schemas: 健康检查数据模型和验证模式
- services: 健康检查业务逻辑服务
- repositories: 健康检查数据访问层
- models: 健康检查数据模型定义
"""

from .api.health import router as health_router

__all__ = [
    "health_router",
]
