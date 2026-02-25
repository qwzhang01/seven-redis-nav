"""
用户业务逻辑服务层

处理所有与用户相关的业务逻辑，包括用户管理、认证、API密钥管理等。
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from quant_trading_system.core.invitation_utils import InvitationUtils
from quant_trading_system.core.password_utils import PasswordUtils
from quant_trading_system.core.jwt_utils import JWTUtils
from quant_trading_system.core.config import settings
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.api.users.repositories.user_repository import (
    UserRepository, ExchangeRepository, APIKeyRepository
)

logger = logging.getLogger(__name__)


class UserService:
    """用户业务逻辑服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.exchange_repo = ExchangeRepository(db)
        self.api_key_repo = APIKeyRepository(db)

    def register_user(self, username: str, password: str, email: str,
                     invitation_code: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """用户注册业务逻辑"""
        # 检查用户名是否已存在
        if self.user_repo.get_user_by_username(username):
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        if self.user_repo.get_user_by_email(email):
            raise ValueError("邮箱已存在")

        # 验证邀请码并获取邀请人ID
        inviter_id = self._validate_and_get_inviter_id(invitation_code)
        if not inviter_id:
            raise ValueError("邀请码无效或已被使用")

        # 验证密码强度
        is_valid, error_msg = PasswordUtils.validate_password_strength(password)
        if not is_valid:
            raise ValueError(error_msg)

        # 生成密码哈希
        password_hash = PasswordUtils.hash_password(password)

        # 创建用户数据（将username赋值给nickname）
        user_data = {
            "id": generate_snowflake_id(),
            "username": username,
            "nickname": username,  # 将username赋值给nickname
            "password_hash": password_hash,
            "email": email,
            "phone": phone,
            "invitation_code": InvitationUtils.generate_invitation_code(5),  # 添加邀请码字段
            "inviter_id": inviter_id,  # 邀请人ID
            "user_type": "customer",
            "registration_time": datetime.utcnow(),
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow(),
        }

        # 创建用户
        user = self.user_repo.create_user(user_data)

        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "phone": user.phone,
            "user_type": user.user_type,
            "registration_time": user.registration_time.isoformat(),
            "invitation_code": user.invitation_code,
            "inviter_id": user.inviter_id,
        }

    def _validate_and_get_inviter_id(self, invitation_code: str) -> Optional[int]:
        """
        验证邀请码并获取邀请人ID

        验证逻辑：
        1. 检查邀请码是否有效（格式、是否已被使用等）
        2. 根据邀请码查找对应的邀请人用户
        3. 返回邀请人ID，如果无效则返回None

        TODO: 当invitation_codes表实现后，需要完善此方法
        """
        # 检查邀请码格式
        if not invitation_code or len(invitation_code) < 4:
            return None

        # 根据邀请码查找邀请人用户
        # 这里假设邀请码就是邀请人的用户名或特定标识
        # 实际项目中应该查询invitation_codes表获取邀请人ID
        inviter_user = self.user_repo.get_user_by_invitation_code(invitation_code)
        if inviter_user:
            return inviter_user.id

        # 如果找不到对应的邀请人，返回None
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证业务逻辑"""
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return None

        # 验证密码
        if not PasswordUtils.verify_password(password, user.password_hash):
            return None

        # 更新最后登录时间
        self.user_repo.update_last_login_time(user.id)

        # 生成JWT Token
        jwt_utils = JWTUtils()
        access_token = jwt_utils.create_user_token(user.id, user.username, user.user_type)
        refresh_token = jwt_utils.create_user_refresh_token(user.id, user.username, user.user_type)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,  # 转换为秒
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "phone": user.phone,
                "user_type": user.user_type,
                "registration_time": user.registration_time.isoformat(),
                "invitation_code": user.invitation_code,
                "inviter_id": user.inviter_id,
            }
        }

    def refresh_token(self, refresh_token_str: str) -> Optional[Dict[str, Any]]:
        """刷新令牌业务逻辑

        验证 refresh_token，签发新的 access_token 和 refresh_token。
        """
        jwt_utils = JWTUtils()

        # 验证 refresh_token（内部会检查过期和类型）
        payload = jwt_utils.verify_refresh_token(refresh_token_str)

        # 从 payload 中提取用户信息
        username = payload.get("sub")
        user_id = payload.get("user_id")
        user_type = payload.get("user_type")

        if not username or not user_id:
            return None

        # 验证用户是否仍然存在且有效
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return None

        # 签发新的 access_token 和 refresh_token
        new_access_token = jwt_utils.create_user_token(user.id, user.username, user.user_type)
        new_refresh_token = jwt_utils.create_user_refresh_token(user.id, user.username, user.user_type)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,  # 转换为秒
        }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码业务逻辑"""
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return False

        # 验证原密码
        if not PasswordUtils.verify_password(old_password, user.password_hash):
            return False

        # 验证新密码强度
        is_valid, error_msg = PasswordUtils.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # 生成新密码哈希
        new_password_hash = PasswordUtils.hash_password(new_password)

        # 更新密码
        return self.user_repo.update_user_password(user_id, new_password_hash)

    def reset_password(self, username: str, new_password: str) -> bool:
        """重置密码业务逻辑"""
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return False

        # 验证新密码强度
        is_valid, error_msg = PasswordUtils.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # 生成新密码哈希
        new_password_hash = PasswordUtils.hash_password(new_password)

        # 更新密码
        return self.user_repo.update_user_password(user.id, new_password_hash)

    def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新个人信息业务逻辑"""
        user = self.user_repo.update_user_profile(user_id, profile_data)
        if not user:
            return None

        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "phone": user.phone,
            "user_type": user.user_type,
            "registration_time": user.registration_time.isoformat(),
            "invitation_code": user.invitation_code,
            "inviter_id": user.inviter_id,
        }

    def get_exchange_info(self, exchange_id: int) -> Optional[Dict[str, Any]]:
        """获取交易所信息业务逻辑"""
        exchange = self.exchange_repo.get_exchange_by_id(exchange_id)
        if not exchange:
            return None

        return {
            "id": exchange.id,
            "name": exchange.exchange_name,
            "code": exchange.exchange_code,
            "region": exchange.region,
            "status": exchange.status,
        }

    def create_api_key(self, user_id: int, exchange_id: int, label: str,
                     api_key: str, secret_key: str,
                     passphrase: Optional[str] = None,
                     permissions: Optional[Dict] = None) -> Dict[str, Any]:
        """创建API密钥业务逻辑"""
        # 检查交易所是否存在
        exchange = self.exchange_repo.get_exchange_by_id(exchange_id)
        if not exchange:
            raise ValueError("交易所不存在")

        # 检查是否已存在该交易所的API密钥
        existing = self.api_key_repo.get_api_key_by_exchange(user_id, exchange_id)
        if existing:
            raise ValueError("该交易所的API密钥已存在")

        # 创建API密钥数据
        api_key_data = {
            "id": generate_snowflake_id(),
            "user_id": user_id,
            "exchange_id": exchange_id,
            "label": label,
            "api_key": api_key,
            "secret_key": secret_key,
            "passphrase": passphrase,
            "permissions": permissions,
            "status": "pending",
            "create_by": "user",
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow(),
        }

        api_key_obj = self.api_key_repo.create_api_key(api_key_data)

        return {
            "id": api_key_obj.id,
            "exchange_id": api_key_obj.exchange_id,
            "label": api_key_obj.label,
            "status": api_key_obj.status,
            "created_at": api_key_obj.create_time.isoformat(),
        }

    def get_user_api_keys(self, user_id: int) -> Dict[str, Any]:
        """获取用户API密钥列表业务逻辑"""
        api_keys = self.api_key_repo.get_user_api_keys(user_id)

        items = [
            {
                "id": ak.id,
                "exchange_id": ak.exchange_id,
                "label": ak.label,
                "status": ak.status,
                "created_at": ak.create_time.isoformat(),
            }
            for ak in api_keys
        ]

        return {
            "items": items,
            "total": len(items)
        }

    def get_api_key_detail(self, user_id: int, api_key_id: int) -> Optional[Dict[str, Any]]:
        """获取API密钥详情业务逻辑"""
        api_key = self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return None

        return {
            "id": api_key.id,
            "exchange_id": api_key.exchange_id,
            "label": api_key.label,
            "status": api_key.status,
            "created_at": api_key.create_time.isoformat(),
        }

    def update_api_key(self, user_id: int, api_key_id: int, label: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """更新API密钥业务逻辑"""
        api_key = self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return None

        update_data = {}
        if label:
            update_data["label"] = label

        updated_api_key = self.api_key_repo.update_api_key(api_key_id, update_data)
        if not updated_api_key:
            return None

        return {
            "id": updated_api_key.id,
            "exchange_id": updated_api_key.exchange_id,
            "label": updated_api_key.label,
            "status": updated_api_key.status,
            "created_at": updated_api_key.create_time.isoformat(),
        }

    def delete_api_key(self, user_id: int, api_key_id: int) -> bool:
        """删除API密钥业务逻辑"""
        api_key = self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return False

        return self.api_key_repo.delete_api_key(api_key_id)
