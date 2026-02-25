"""
用户相关数据模型定义

定义用户相关的Pydantic模型，用于API层的请求和响应数据验证。
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    nickname: str
    email: str
    phone: Optional[str] = None
    user_type: str
    registration_time: str


class RegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str
    password: str
    email: EmailStr
    nickname: str
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """用户登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access_token 过期时间（秒）
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access_token 过期时间（秒）


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    username: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求模型"""
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class ExchangeInfo(BaseModel):
    """交易所信息响应模型"""
    id: int
    name: str
    code: str
    region: Optional[str] = None
    status: str


class CreateAPIKeyRequest(BaseModel):
    """创建API密钥请求模型"""
    exchange_id: int
    label: str
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None
    permissions: Optional[dict] = None


class APIKeyResponse(BaseModel):
    """API密钥响应模型"""
    id: int
    exchange_id: int
    label: str
    status: str
    created_at: str


class APIKeyListResponse(BaseModel):
    """API密钥列表响应模型"""
    items: list[APIKeyResponse]
    total: int


class UpdateAPIKeyRequest(BaseModel):
    """更新API密钥请求模型"""
    label: Optional[str] = None
