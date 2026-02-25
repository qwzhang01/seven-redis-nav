#!/usr/bin/env python3
"""
JWT工具模块
===========

提供统一的JWT令牌创建、验证和管理功能。
集中管理JWT配置，消除代码重复和配置不一致问题。
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from quant_trading_system.core.config import settings


class JWTUtils:
    """JWT工具类"""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.JWT_EXPIRE_MINUTES
        self.refresh_expire_days = settings.JWT_REFRESH_EXPIRE_DAYS

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建JWT访问令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间间隔，如未提供则使用默认配置

        Returns:
            JWT令牌字符串
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌字符串

        Returns:
            解码后的令牌数据

        Raises:
            HTTPException: 令牌无效或过期时抛出异常
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期"
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的令牌: {str(exc)}"
            )

    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建JWT刷新令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间间隔，如未提供则使用默认配置（7天）

        Returns:
            JWT刷新令牌字符串
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",  # 标识这是刷新令牌
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT刷新令牌

        Args:
            token: JWT刷新令牌字符串

        Returns:
            解码后的令牌数据

        Raises:
            HTTPException: 令牌无效、过期或类型不正确时抛出异常
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 验证令牌类型必须是 refresh
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌：令牌类型不正确"
                )

            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已过期，请重新登录"
            )
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"无效的刷新令牌: {str(exc)}"
            )

    def create_user_token(self, user_id: int, username: str, user_type: str) -> str:
        """
        创建用户JWT令牌（专为用户认证设计）

        Args:
            user_id: 用户ID
            username: 用户名
            user_type: 用户类型

        Returns:
            JWT令牌字符串
        """
        payload = {
            "user_id": user_id,
            "sub": username,
            "user_type": user_type,
        }
        return self.create_access_token(payload)

    def create_user_refresh_token(self, user_id: int, username: str, user_type: str) -> str:
        """
        创建用户JWT刷新令牌（专为用户认证设计）

        Args:
            user_id: 用户ID
            username: 用户名
            user_type: 用户类型

        Returns:
            JWT刷新令牌字符串
        """
        payload = {
            "user_id": user_id,
            "sub": username,
            "user_type": user_type,
        }
        return self.create_refresh_token(payload)

    def verify_user_token(self, token: str) -> Dict[str, Any]:
        """
        验证用户JWT令牌

        Args:
            token: JWT令牌字符串

        Returns:
            包含用户信息的令牌数据
        """
        payload = self.verify_token(token)

        # 验证必要的用户字段
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌缺少用户标识"
            )

        return payload


def get_jwt_utils() -> JWTUtils:
    """获取JWT工具实例（用于依赖注入）"""
    return JWTUtils()
