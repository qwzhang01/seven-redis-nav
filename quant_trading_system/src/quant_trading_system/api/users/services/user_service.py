"""
用户业务逻辑服务层

处理所有与用户相关的业务逻辑，包括用户管理、认证、API密钥管理等。
"""

import structlog
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.core.invitation_utils import InvitationUtils
from quant_trading_system.core.password_utils import PasswordUtils
from quant_trading_system.core.jwt_utils import JWTUtils
from quant_trading_system.core.config import settings
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.api.users.repositories.user_repository import (
    UserRepository, ExchangeRepository, APIKeyRepository
)

logger = structlog.get_logger(__name__)


class UserService:
    """用户业务逻辑服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.exchange_repo = ExchangeRepository(db)
        self.api_key_repo = APIKeyRepository(db)

    async def register_user(self, username: str, password: str, email: str,
                            invitation_code: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """用户注册业务逻辑"""
        # 检查用户名是否已存在
        if await self.user_repo.get_user_by_username(username):
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        if await self.user_repo.get_user_by_email(email):
            raise ValueError("邮箱已存在")

        # 验证邀请码并获取邀请人ID
        inviter_id = await self._validate_and_get_inviter_id(invitation_code)
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
        user = await self.user_repo.create_user(user_data)

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

    async def _validate_and_get_inviter_id(self, invitation_code: str) -> Optional[int]:
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
        inviter_user = await self.user_repo.get_user_by_invitation_code(invitation_code)
        if inviter_user:
            return inviter_user.id

        # 如果找不到对应的邀请人，返回None
        return None

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证业务逻辑"""
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            raise ValueError("用户不存在，请注册后登录！")  # 改为抛出异常

        if not PasswordUtils.verify_password(password, user.password_hash):
            raise ValueError("密码错误，请重新输入")  # 改为抛出异常

        # 更新最后登录时间
        await self.user_repo.update_last_login_time(user.id)

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

    async def refresh_token(self, refresh_token_str: str) -> Optional[Dict[str, Any]]:
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
        user = await self.user_repo.get_user_by_username(username)
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

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码业务逻辑"""
        user = await self.user_repo.get_user_by_id(user_id)
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
        return await self.user_repo.update_user_password(user_id, new_password_hash)

    async def reset_password(self, username: str, new_password: str) -> bool:
        """重置密码业务逻辑"""
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            return False

        # 验证新密码强度
        is_valid, error_msg = PasswordUtils.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # 生成新密码哈希
        new_password_hash = PasswordUtils.hash_password(new_password)

        # 更新密码
        return await self.user_repo.update_user_password(user.id, new_password_hash)

    async def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新个人信息业务逻辑"""
        user = await self.user_repo.update_user_profile(user_id, profile_data)
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

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户信息"""
        user = await self.user_repo.get_user_by_id(user_id)
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

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息"""
        user = await self.user_repo.get_user_by_username(username)
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

    async def get_exchanges(self, exchange_type: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取交易所列表（支持按类型和状态过滤）"""
        exchanges = await self.exchange_repo.get_exchanges(exchange_type, status)
        return [
            {
                "id": str(exchange.id),
                "exchange_code": exchange.exchange_code,
                "exchange_name": exchange.exchange_name,
                "exchange_type": exchange.exchange_type,
                "base_url": exchange.base_url,
                "api_doc_url": exchange.api_doc_url,
                "status": exchange.status,
                "supported_pairs": exchange.supported_pairs,
                "rate_limits": exchange.rate_limits,
                "create_time": exchange.create_time,
                "update_time": exchange.update_time,
            }
            for exchange in exchanges
        ]

    async def get_exchange_info(self, exchange_id: int) -> Optional[Dict[str, Any]]:
        """获取交易所信息业务逻辑"""
        exchange = await self.exchange_repo.get_exchange_by_id(exchange_id)
        if not exchange:
            return None

        return {
            "id": exchange.id,
            "name": exchange.exchange_name,
            "code": exchange.exchange_code,
            "region": exchange.region,
            "status": exchange.status,
        }

    async def create_api_key(self, user_id: int, exchange_id: int, label: str,
                     api_key: str, secret_key: str,
                     passphrase: Optional[str] = None,
                     permissions: Optional[Dict] = None) -> Dict[str, Any]:
        """创建API密钥业务逻辑"""
        # 检查交易所是否存在
        exchange = await self.exchange_repo.get_exchange_by_id(exchange_id)
        if not exchange:
            raise ValueError("交易所不存在")

        # 检查是否已存在该交易所的API密钥
        existing = await self.api_key_repo.get_api_key_by_exchange(user_id, exchange_id)
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

        api_key_obj = await self.api_key_repo.create_api_key(api_key_data)

        return {
            "id": api_key_obj.id,
            "exchange_id": api_key_obj.exchange_id,
            "label": api_key_obj.label,
            "status": api_key_obj.status,
            "created_at": api_key_obj.create_time.isoformat(),
        }

    async def get_user_api_keys(self, user_id: int) -> Dict[str, Any]:
        """获取用户API密钥列表业务逻辑"""
        api_keys = await self.api_key_repo.get_user_api_keys(user_id)

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

    async def get_api_key_detail(self, user_id: int, api_key_id: int) -> Optional[Dict[str, Any]]:
        """获取API密钥详情业务逻辑"""
        api_key = await self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return None

        return {
            "id": api_key.id,
            "exchange_id": api_key.exchange_id,
            "label": api_key.label,
            "status": api_key.status,
            "created_at": api_key.create_time.isoformat(),
        }

    async def update_api_key(self, user_id: int, api_key_id: int, label: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """更新API密钥业务逻辑"""
        api_key = await self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return None

        update_data = {}
        if label:
            update_data["label"] = label

        updated_api_key = await self.api_key_repo.update_api_key(api_key_id, update_data)
        if not updated_api_key:
            return None

        return {
            "id": updated_api_key.id,
            "exchange_id": updated_api_key.exchange_id,
            "label": updated_api_key.label,
            "status": updated_api_key.status,
            "created_at": updated_api_key.create_time.isoformat(),
        }

    async def delete_api_key(self, user_id: int, api_key_id: int) -> bool:
        """删除API密钥业务逻辑"""
        api_key = await self.api_key_repo.get_api_key_by_id(api_key_id)
        if not api_key or api_key.user_id != user_id:
            return False

        return await self.api_key_repo.delete_api_key(api_key_id)

    async def get_invitation_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户邀请统计信息"""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 获取被邀请用户列表
        invited_users = await self.user_repo.get_invited_users(user_id)
        total_invited = len(invited_users)

        # 计算活跃用户数（这里简单定义为有登录记录的用户）
        active_invited = sum(1 for u in invited_users if u.last_login_time)

        # 计算总奖励（这里需要根据业务逻辑计算）
        total_reward = None  # 实际项目中需要根据业务规则计算

        return {
            "invitation_code": user.invitation_code,
            "total_invited_users": total_invited,
            "active_invited_users": active_invited,
            "total_reward": total_reward
        }

    async def get_invited_users_list(self, user_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取被邀请用户分页列表"""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 获取被邀请用户列表
        invited_users = await self.user_repo.get_invited_users(user_id)

        # 分页处理
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = invited_users[start_index:end_index]

        # 格式化响应数据
        items = []
        for user in paginated_users:
            items.append({
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "level": user.user_type,  # 使用user_type作为level
                "invited_at": user.registration_time.isoformat(),
                "reward": None  # 实际项目中需要根据业务规则计算
            })

        return {
            "items": items,
            "total": len(invited_users),
            "page": page,
            "page_size": page_size
        }
