"""
用户管理业务域
===============

提供完整的用户管理功能，包括用户注册、登录、密码管理、API密钥管理等。

模块组成：
- api: 用户管理API路由
- schemas: 数据模型和验证模式
- services: 业务逻辑服务
- repositories: 数据访问层
- models: 数据模型定义
"""

from .api.user import router as user_router
from .api.admin_user import router as admin_user_router

__all__ = [
    "user_router",
    "admin_user_router",
]
