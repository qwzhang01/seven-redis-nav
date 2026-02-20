"""
系统管理业务域
===============

提供系统管理和监控功能，包括系统信息、配置查询、健康检查、性能指标等。
原 health 业务域合并至本域。

模块组成：
- api: 系统管理API路由
- schemas: 系统数据模型和验证模式
- services: 系统业务逻辑服务
- repositories: 系统数据访问层
- models: 系统数据模型定义
"""

from .api.system import router as system_router
from .api.health import router as health_router

__all__ = [
    "system_router",
    "health_router",
]
