"""
C 端用户路由模块
===============

提供普通用户（C端）的用户管理功能：
- 注册、登录、密码管理
- 个人信息维护
- 交易所 API 密钥管理

认证方式：JWT Token（Bearer Token）
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import User, Exchange, UserExchangeAPI
from quant_trading_system.services.database.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.core.jwt_utils import JWTUtils

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


class ExchangeInfo(BaseModel):
    """交易所信息响应模型"""
    id: int
    name: str
    code: str
    region: Optional[str] = None
    status: str


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """从拦截器验证后的request.state中获取当前用户"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(status_code=401, detail="未认证的用户")

    user = db.query(User).filter(User.username == username, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


# ─────────────────────────────────────────────
# 1. 注册与登录（公开接口）
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    user_type: str
    created_at: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    用户注册

    注册新用户账户，成功后返回用户基本信息。

    参数：
    - username: 用户名（必填，唯一）
    - password: 密码（必填，至少6位）
    - email   : 邮箱（可选）
    - phone   : 手机号（可选）

    返回：
    - 用户基本信息

    异常：
    - 400: 用户名已存在
    - 400: 密码不符合要求
    """
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 密码长度检查
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位",
        )

    # 创建用户
    user = User(
        id=generate_snowflake_id(),
        username=request.username,
        password=request.password,  # 实际应用中应使用密码哈希
        email=request.email,
        phone=request.phone,
        user_type="customer",
        enable_flag=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        user_type=user.user_type,
        created_at=user.created_at.isoformat(),
    )


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    用户登录

    验证用户名和密码，成功后返回 JWT Token。

    参数：
    - username: 用户名
    - password: 密码

    返回：
    - access_token: JWT 访问令牌
    - token_type : Token 类型（固定为 bearer）
    - user       : 用户基本信息

    异常：
    - 401: 用户名或密码错误
    """
    user = db.query(User).filter(
        User.username == request.username,
        User.enable_flag == True,
    ).first()

    if not user or user.password != request.password:  # 实际应用中应使用密码哈希验证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 生成 JWT Token
    jwt_utils = JWTUtils()
    token = jwt_utils.create_user_token(user.id, user.username, user.user_type)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            user_type=user.user_type,
            created_at=user.created_at.isoformat(),
        ),
    )


# ─────────────────────────────────────────────
# 2. 密码管理（需要认证）
# ─────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


@router.post("/password/change")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    修改当前用户密码

    参数：
    - old_password: 原密码
    - new_password: 新密码

    返回：
    - 操作结果

    异常：
    - 401: 原密码错误
    - 400: 新密码不符合要求
    """
    # 验证原密码
    if current_user.password != request.old_password:  # 实际应用中应使用密码哈希验证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="原密码错误",
        )

    # 新密码长度检查
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6位",
        )

    # 更新密码
    current_user.password = request.new_password  # 实际应用中应使用密码哈希
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "密码修改成功"}


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    username: str
    new_password: str


@router.post("/password/reset")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    重置用户密码（管理员或忘记密码功能）

    参数：
    - username    : 用户名
    - new_password: 新密码

    返回：
    - 操作结果

    异常：
    - 404: 用户不存在
    - 400: 新密码不符合要求
    """
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 新密码长度检查
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6位",
        )

    # 重置密码
    user.password = request.new_password  # 实际应用中应使用密码哈希
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "密码重置成功"}


# ─────────────────────────────────────────────
# 3. 个人信息管理（需要认证）
# ─────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    """更新个人信息请求"""
    email: Optional[str] = None
    phone: Optional[str] = None


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    更新当前用户个人信息

    参数：
    - email: 新邮箱（可选）
    - phone: 新手机号（可选）

    返回：
    - 更新后的用户信息
    """
    if request.email:
        current_user.email = request.email
    if request.phone:
        current_user.phone = request.phone

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        user_type=current_user.user_type,
        created_at=current_user.created_at.isoformat(),
    )


# ─────────────────────────────────────────────
# 4. 交易所 API 密钥管理（需要认证）
# ─────────────────────────────────────────────

@router.get("/exchanges/{exchange_id}", response_model=ExchangeInfo)
async def get_exchange_info(
    exchange_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeInfo:
    """
    获取交易所信息

    参数：
    - exchange_id: 交易所ID

    返回：
    - 交易所基本信息

    异常：
    - 404: 交易所不存在
    """
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在",
        )

    return ExchangeInfo(
        id=exchange.id,
        name=exchange.name,
        code=exchange.code,
        region=exchange.region,
        status=exchange.status,
    )


class CreateAPIKeyRequest(BaseModel):
    """创建 API 密钥请求"""
    exchange_id: int
    api_key: str
    secret_key: str
    nickname: Optional[str] = None


class APIKeyResponse(BaseModel):
    """API 密钥响应"""
    id: int
    exchange_id: int
    nickname: Optional[str]
    created_at: str


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    创建交易所 API 密钥

    参数：
    - exchange_id: 交易所ID
    - api_key    : API Key
    - secret_key : Secret Key
    - nickname   : 密钥别名（可选）

    返回：
    - 创建的 API 密钥信息

    异常：
    - 404: 交易所不存在
    - 400: 该交易所的 API 密钥已存在
    """
    # 检查交易所是否存在
    exchange = db.query(Exchange).filter(Exchange.id == request.exchange_id).first()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在",
        )

    # 检查是否已存在该交易所的 API 密钥
    existing = db.query(UserExchangeAPI).filter(
        UserExchangeAPI.user_id == current_user.id,
        UserExchangeAPI.exchange_id == request.exchange_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该交易所的 API 密钥已存在",
        )

    api_key = UserExchangeAPI(
        id=generate_snowflake_id(),
        user_id=current_user.id,
        exchange_id=request.exchange_id,
        api_key=request.api_key,
        secret_key=request.secret_key,
        nickname=request.nickname,
        enable_flag=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        exchange_id=api_key.exchange_id,
        nickname=api_key.nickname,
        created_at=api_key.created_at.isoformat(),
    )


class APIKeyListResponse(BaseModel):
    """API 密钥列表响应"""
    items: list[APIKeyResponse]
    total: int


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyListResponse:
    """
    获取当前用户的 API 密钥列表

    返回：
    - items: API 密钥列表
    - total: 总数量
    """
    api_keys = db.query(UserExchangeAPI).filter(
        UserExchangeAPI.user_id == current_user.id,
        UserExchangeAPI.enable_flag == True,
    ).all()

    items = [
        APIKeyResponse(
            id=ak.id,
            exchange_id=ak.exchange_id,
            nickname=ak.nickname,
            created_at=ak.created_at.isoformat(),
        )
        for ak in api_keys
    ]

    return APIKeyListResponse(items=items, total=len(items))


@router.get("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    获取指定 API 密钥详情

    参数：
    - api_key_id: API 密钥ID

    返回：
    - API 密钥详情

    异常：
    - 404: API 密钥不存在
    - 403: 无权访问该密钥
    """
    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 密钥不存在",
        )

    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该 API 密钥",
        )

    return APIKeyResponse(
        id=api_key.id,
        exchange_id=api_key.exchange_id,
        nickname=api_key.nickname,
        created_at=api_key.created_at.isoformat(),
    )


class UpdateAPIKeyRequest(BaseModel):
    """更新 API 密钥请求"""
    nickname: Optional[str] = None


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    request: UpdateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> APIKeyResponse:
    """
    更新 API 密钥信息（仅可更新别名）

    参数：
    - api_key_id: API 密钥ID
    - nickname  : 新的密钥别名

    返回：
    - 更新后的 API 密钥信息

    异常：
    - 404: API 密钥不存在
    - 403: 无权修改该密钥
    """
    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 密钥不存在",
        )

    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该 API 密钥",
        )

    if request.nickname:
        api_key.nickname = request.nickname
    api_key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        exchange_id=api_key.exchange_id,
        nickname=api_key.nickname,
        created_at=api_key.created_at.isoformat(),
    )


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    删除 API 密钥（软删除）

    参数：
    - api_key_id: API 密钥ID

    返回：
    - 操作结果

    异常：
    - 404: API 密钥不存在
    - 403: 无权删除该密钥
    """
    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API 密钥不存在",
        )

    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该 API 密钥",
        )

    api_key.enable_flag = False
    api_key.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "API 密钥删除成功"}
