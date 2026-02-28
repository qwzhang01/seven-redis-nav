from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from quant_trading_system.models.exchange import ExchangeType, ExchangeStatus


class UserType(str, Enum):
    """用户类型"""
    CUSTOMER = "customer"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class APIKeyStatus(str, Enum):
    """API密钥状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISABLED = "disabled"


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    nickname: str = Field(..., min_length=1, max_length=128, description="昵称")
    email: EmailStr = Field(..., description="邮箱地址")
    phone: Optional[str] = Field(None, max_length=32, description="手机号")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")
    user_type: UserType = Field(default=UserType.CUSTOMER, description="用户类型")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserUpdate(BaseModel):
    """用户更新模型"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=128, description="昵称")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    phone: Optional[str] = Field(None, max_length=32, description="手机号")
    avatar_url: Optional[str] = Field(None, max_length=512, description="头像URL")


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    email_verified: bool
    phone_verified: bool
    user_type: UserType
    registration_time: datetime
    last_login_time: Optional[datetime]
    status: UserStatus
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")
    verification_code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class ExchangeInfo(BaseModel):
    """交易所信息模型"""
    id: int
    exchange_code: str
    exchange_name: str
    exchange_type: ExchangeType
    base_url: str
    api_doc_url: Optional[str]
    status: ExchangeStatus
    supported_pairs: Optional[Dict[str, Any]]
    rate_limits: Optional[Dict[str, Any]]
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    """密钥创建模型"""
    exchange_id: int = Field(..., description="交易所ID")
    label: str = Field(..., min_length=1, max_length=128, description="标签")
    api_key: str = Field(..., min_length=1, max_length=512, description="API密钥")
    secret_key: str = Field(..., min_length=1, max_length=512, description="Secret密钥")
    passphrase: Optional[str] = Field(None, max_length=512, description="密码短语")
    permissions: Optional[Dict[str, Any]] = Field(default=None, description="权限配置")


class APIKeyUpdate(BaseModel):
    """API密钥更新模型"""
    label: Optional[str] = Field(None, min_length=1, max_length=128, description="标签")
    permissions: Optional[Dict[str, Any]] = Field(None, description="权限配置")
    status: Optional[APIKeyStatus] = Field(None, description="状态")


class APIKeyResponse(BaseModel):
    """密钥响应模型"""
    id: int
    user_id: int
    exchange_id: int
    label: str
    api_key: str
    status: APIKeyStatus
    review_reason: Optional[str]
    approved_by: Optional[str]
    approved_time: Optional[datetime]
    last_used_time: Optional[datetime]
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """API密钥列表响应模型"""
    total: int
    items: List[APIKeyResponse]


class ExchangeListResponse(BaseModel):
    """交易所列表响应模型"""
    total: int
    items: List[ExchangeInfo]


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    total: int
    items: List[UserResponse]


# 为API响应添加成功状态包装
class APIResponse(BaseModel):
    """API响应包装模型"""
    success: bool
    data: Optional[Any] = None
    message: str
    error: Optional[str] = None
    error_type: Optional[str] = None


# 用户列表响应包装
class UserListAPIResponse(APIResponse):
    """用户列表API响应"""
    data: UserListResponse


# 交易所列表响应包装
class ExchangeListAPIResponse(APIResponse):
    """交易所列表API响应"""
    data: ExchangeListResponse


# API密钥列表响应包装
class APIKeyListAPIResponse(APIResponse):
    """API密钥列表API响应"""
    data: APIKeyListResponse
