"""
C 端用户路由模块
===============

提供普通用户（C端）的用户管理功能：
- 注册、登录、密码管理
- 个人信息维护
- 交易所 API 密钥管理

认证方式：JWT Token（Bearer Token）

重构说明：
- API层只处理HTTP请求和响应
- 业务逻辑委托给services层处理
- 数据验证使用models层的Pydantic模型
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from quant_trading_system.services.database.database import get_db
from quant_trading_system.api.users.services.user_service import UserService
from quant_trading_system.api.users.models.user_models import (
    UserResponse, RegisterRequest, LoginRequest, LoginResponse,
    ChangePasswordRequest, ResetPasswordRequest, UpdateProfileRequest,
    ExchangeInfo, CreateAPIKeyRequest, APIKeyResponse, APIKeyListResponse,
    UpdateAPIKeyRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    """从拦截器验证后的request.state中获取当前用户信息"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(status_code=401, detail="未认证的用户")

    user_service = UserService(db)
    user = user_service.user_repo.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

    return {
        "id": user.id,
        "username": user.username,
        "user_type": user.user_type
    }


# ─────────────────────────────────────────────
# 1. 注册与登录（公开接口）
# ─────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    用户注册

    注册新用户账户，成功后返回用户基本信息。
    """
    user_service = UserService(db)

    try:
        user_info = user_service.register_user(
            username=request.username,
            password=request.password,
            email=request.email,
            nickname=request.nickname,
            phone=request.phone
        )
        return UserResponse(**user_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    用户登录

    验证用户名和密码，成功后返回 JWT Token。
    """
    user_service = UserService(db)

    auth_result = user_service.authenticate_user(request.username, request.password)
    if not auth_result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return LoginResponse(**auth_result)


# ─────────────────────────────────────────────
# 2. 密码管理（需要认证）
# ─────────────────────────────────────────────

@router.post("/password/change")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    修改当前用户密码
    """
    user_service = UserService(db)

    try:
        success = user_service.change_password(
            user_id=current_user["id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        if not success:
            raise HTTPException(status_code=401, detail="原密码错误")

        return {"success": True, "message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password/reset")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    重置用户密码（管理员或忘记密码功能）
    """
    user_service = UserService(db)

    try:
        success = user_service.reset_password(request.username, request.new_password)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {"success": True, "message": "密码重置成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────
# 3. 个人信息管理（需要认证）
# ─────────────────────────────────────────────

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    更新当前用户个人信息
    """
    user_service = UserService(db)

    profile_data = {}
    if request.nickname:
        profile_data["nickname"] = request.nickname
    if request.email:
        profile_data["email"] = request.email
    if request.phone:
        profile_data["phone"] = request.phone
    if request.avatar_url:
        profile_data["avatar_url"] = request.avatar_url

    user_info = user_service.update_profile(current_user["id"], profile_data)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return UserResponse(**user_info)


# ─────────────────────────────────────────────
# 4. 交易所 API 密钥管理（需要认证）
# ─────────────────────────────────────────────

@router.get("/exchanges/{exchange_id}", response_model=ExchangeInfo)
async def get_exchange_info(
    exchange_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeInfo:
    """
    获取交易所信息
    """
    user_service = UserService(db)

    exchange_info = user_service.get_exchange_info(exchange_id)
    if not exchange_info:
        raise HTTPException(status_code=404, detail="交易所不存在")

    return ExchangeInfo(**exchange_info)


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    创建交易所 API 密钥
    """
    user_service = UserService(db)

    try:
        api_key_info = user_service.create_api_key(
            user_id=current_user["id"],
            exchange_id=request.exchange_id,
            label=request.label,
            api_key=request.api_key,
            secret_key=request.secret_key,
            passphrase=request.passphrase,
            permissions=request.permissions
        )
        return APIKeyResponse(**api_key_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyListResponse:
    """
    获取当前用户的 API 密钥列表
    """
    user_service = UserService(db)

    api_keys_info = user_service.get_user_api_keys(current_user["id"])
    return APIKeyListResponse(**api_keys_info)


@router.get("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    获取指定 API 密钥详情
    """
    user_service = UserService(db)

    api_key_info = user_service.get_api_key_detail(current_user["id"], api_key_id)
    if not api_key_info:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权访问")

    return APIKeyResponse(**api_key_info)


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    request: UpdateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    更新 API 密钥信息（仅可更新标签）
    """
    user_service = UserService(db)

    api_key_info = user_service.update_api_key(current_user["id"], api_key_id, request.label)
    if not api_key_info:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权修改")

    return APIKeyResponse(**api_key_info)


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    删除 API 密钥（软删除）
    """
    user_service = UserService(db)

    success = user_service.delete_api_key(current_user["id"], api_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权删除")

    return {"success": True, "message": "API 密钥删除成功"}
