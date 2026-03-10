"""
C 端用户路由模块
===============

提供普通用户（C端）的用户管理功能：
- 注册、登录、Token 刷新
- 密码管理（修改密码、重置密码）
- 个人信息维护
- 交易所 API 密钥管理

认证方式：JWT Token（Bearer Token）
- access_token：短期有效（默认30分钟），用于接口认证
- refresh_token：长期有效（默认7天），用于刷新 access_token

公开接口（无需认证）：
- POST /register    - 用户注册
- POST /login       - 用户登录，返回 access_token + refresh_token
- POST /token/refresh - 使用 refresh_token 换取新的 token 对
- POST /password/reset - 重置密码

认证接口（需要 Bearer Token）：
- POST /password/change   - 修改密码
- PUT  /profile           - 更新个人信息
- CRUD /api-keys          - 交易所 API 密钥管理

重构说明：
- API层只处理HTTP请求和响应
- 业务逻辑委托给services层处理
- 数据验证使用models层的Pydantic模型
"""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.api.users.models.user_models import (
    UserResponse, RegisterRequest, LoginRequest, LoginResponse,
    ChangePasswordRequest, ResetPasswordRequest, UpdateProfileRequest,
    ExchangeInfo, CreateAPIKeyRequest, APIKeyResponse, APIKeyListResponse,
    UpdateAPIKeyRequest, RefreshTokenRequest, RefreshTokenResponse
)
from quant_trading_system.api.users.services.user_service import UserService
from quant_trading_system.core.database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request,
                           db: AsyncSession = Depends(get_db)) -> dict:
    """从拦截器验证后的request.state中获取当前用户信息"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(status_code=401, detail="未认证的用户")

    user_service = UserService(db)
    user = await user_service.user_repo.get_user_by_username(username)
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

@router.post("/register",
             response_model=str,
             status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    用户注册

    注册新用户账户，成功后返回用户基本信息。

    - **username**: 用户名（唯一）
    - **password**: 密码
    - **email**: 邮箱
    - **invitation_code**: 邀请码（必填，用于验证邀请人身份）
    - **phone**: 手机号（可选）

    注意：
    - 注册时昵称将自动设置为用户名
    - 邀请码必须有效且未被使用，系统会根据邀请码找到对应的邀请人
    - 注册成功后，邀请人ID将被记录在用户信息中
    """
    user_service = UserService(db)

    try:
        await user_service.register_user(
            username=request.username,
            password=request.password,
            email=request.email,
            invitation_code=request.invitation_code,
            phone=request.phone
        )
        return ""
    except ValueError as e:
        return str(e)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    用户登录

    验证用户名和密码，成功后返回 JWT Token 对（access_token + refresh_token）。

    - **access_token**: 短期有效令牌（默认30分钟），用于接口认证
    - **refresh_token**: 长期有效令牌（默认7天），用于在 access_token 过期后换取新令牌
    - **expires_in**: access_token 的有效时长（秒）
    """
    user_service = UserService(db)
    try:
        auth_result = await user_service.authenticate_user(request.username,
                                                           request.password)
        return LoginResponse(**auth_result)
    except ValueError as e:
        return LoginResponse(remark=str(e))

@router.post("/token/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """
    刷新 Token（无需认证）

    使用 refresh_token 换取新的 access_token 和 refresh_token。
    当 access_token 过期时，前端应调用此接口，而非要求用户重新登录。

    **使用场景**：
    1. 前端检测到 access_token 过期（HTTP 401）
    2. 前端使用本地保存的 refresh_token 调用此接口
    3. 获取新的 token 对后，替换本地存储并重试原请求

    **注意**：若 refresh_token 也过期，则需要用户重新登录。

    - **refresh_token**: 登录时获取的刷新令牌
    """
    user_service = UserService(db)

    try:
        result = await user_service.refresh_token(request.refresh_token)
        if not result:
            raise HTTPException(status_code=401, detail="无效的刷新令牌或用户不存在")
        return RefreshTokenResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token刷新失败: {str(e)}")
        raise HTTPException(status_code=401, detail="Token刷新失败，请重新登录")


# ─────────────────────────────────────────────
# 2. 密码管理（需要认证）
# ─────────────────────────────────────────────

@router.post("/password/change")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    修改当前用户密码（需要认证）

    用户需要提供原密码和新密码，验证原密码正确后更新为新密码。

    - **old_password**: 当前密码
    - **new_password**: 新密码
    """
    user_service = UserService(db)

    try:
        success = await user_service.change_password(
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
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    重置用户密码（无需认证）

    用于忘记密码场景，通过用户名重置密码。

    - **username**: 要重置密码的用户名
    - **new_password**: 新密码
    """
    user_service = UserService(db)

    try:
        success = await user_service.reset_password(request.username,
                                                    request.new_password)
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
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    更新当前用户个人信息（需要认证）

    支持更新以下字段（均为可选，仅传入需要更新的字段）：

    - **nickname**: 昵称
    - **email**: 邮箱
    - **phone**: 手机号
    - **avatar_url**: 头像地址
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

    user_info = await user_service.update_profile(current_user["id"], profile_data)
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
    db: AsyncSession = Depends(get_db),
) -> ExchangeInfo:
    """
    获取交易所信息（需要认证）

    - **exchange_id**: 交易所 ID
    """
    user_service = UserService(db)

    exchange_info = await user_service.get_exchange_info(exchange_id)
    if not exchange_info:
        raise HTTPException(status_code=404, detail="交易所不存在")

    return ExchangeInfo(**exchange_info)


@router.post("/api-keys", response_model=APIKeyResponse,
             status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """
    创建交易所 API 密钥（需要认证）

    - **exchange_id**: 交易所 ID
    - **label**: 密钥标签/备注名
    - **api_key**: API Key
    - **secret_key**: Secret Key
    - **passphrase**: 密码短语（部分交易所需要）
    - **permissions**: 权限列表（可选）
    """
    user_service = UserService(db)

    try:
        api_key_info = await user_service.create_api_key(
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
    db: AsyncSession = Depends(get_db),
) -> APIKeyListResponse:
    """
    获取当前用户的 API 密钥列表（需要认证）

    返回当前用户创建的所有交易所 API 密钥。
    """
    user_service = UserService(db)

    api_keys_info = await user_service.get_user_api_keys(current_user["id"])
    return APIKeyListResponse(**api_keys_info)


@router.get("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """
    获取指定 API 密钥详情（需要认证）

    - **api_key_id**: API 密钥 ID
    """
    user_service = UserService(db)

    api_key_info = await user_service.get_api_key_detail(current_user["id"], api_key_id)
    if not api_key_info:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权访问")

    return APIKeyResponse(**api_key_info)


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    request: UpdateAPIKeyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """
    更新 API 密钥信息（需要认证，仅可更新标签）

    - **api_key_id**: API 密钥 ID
    - **label**: 新的标签名称
    """
    user_service = UserService(db)

    api_key_info = await user_service.update_api_key(current_user["id"], api_key_id,
                                                     request.label)
    if not api_key_info:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权修改")

    return APIKeyResponse(**api_key_info)


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    删除 API 密钥（需要认证，软删除）

    - **api_key_id**: 要删除的 API 密钥 ID
    """
    user_service = UserService(db)

    success = await user_service.delete_api_key(current_user["id"], api_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API 密钥不存在或无权删除")

    return {"success": True, "message": "API 密钥删除成功"}
