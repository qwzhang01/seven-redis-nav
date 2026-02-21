"""
用户管理业务域
===============

提供完整的用户管理功能，包括用户注册、登录、密码管理、API密钥管理等。

模块组成：
- api: 用户管理API路由（只处理HTTP请求）
- models: 数据模型定义（Pydantic模型）
- services: 业务逻辑服务层
- repositories: 数据访问层
- schemas: 数据模型和验证模式
"""

from .api.user import router as user_router
from .api.admin_user import router as admin_user_router

# 导入模型层
from .models.user_models import (
    UserResponse, RegisterRequest, LoginRequest, LoginResponse,
    ChangePasswordRequest, ResetPasswordRequest, UpdateProfileRequest,
    ExchangeInfo, CreateAPIKeyRequest, APIKeyResponse, APIKeyListResponse,
    UpdateAPIKeyRequest
)

# 导入服务层
from .services.user_service import UserService

# 导入数据访问层
from .repositories.user_repository import UserRepository, ExchangeRepository, APIKeyRepository

__all__ = [
    # 路由
    "user_router",
    "admin_user_router",

    # 模型
    "UserResponse", "RegisterRequest", "LoginRequest", "LoginResponse",
    "ChangePasswordRequest", "ResetPasswordRequest", "UpdateProfileRequest",
    "ExchangeInfo", "CreateAPIKeyRequest", "APIKeyResponse", "APIKeyListResponse",
    "UpdateAPIKeyRequest",

    # 服务
    "UserService",

    # 数据访问
    "UserRepository", "ExchangeRepository", "APIKeyRepository",
]
