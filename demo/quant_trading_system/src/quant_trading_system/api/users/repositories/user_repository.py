"""
用户数据访问层

处理所有与用户相关的数据库操作，包括用户管理、API密钥管理等。
"""

import structlog
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from quant_trading_system.models.user import User, Exchange, UserExchangeAPI

logger = structlog.get_logger(__name__)


class UserRepository:
    """用户数据访问类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username, User.enable_flag == True)
        )
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email, User.enable_flag == True)
        )
        return result.scalars().first()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据用户ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.enable_flag == True)
        )
        return result.scalars().first()

    async def get_user_by_invitation_code(self, invitation_code: str) -> Optional[User]:
        """根据邀请码获取用户"""
        result = await self.db.execute(
            select(User).where(User.invitation_code == invitation_code, User.enable_flag == True)
        )
        return result.scalars().first()

    async def create_user(self, user_data: dict) -> User:
        """创建新用户"""
        try:
            user = User(**user_data)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"创建用户失败: {e}")
            raise ValueError("用户名或邮箱已存在")

    async def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        """更新用户密码"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.password_hash = new_password_hash
        user.update_time = datetime.utcnow()
        await self.db.commit()
        return True

    async def update_user_profile(self, user_id: int, profile_data: dict) -> Optional[User]:
        """更新用户个人信息"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in profile_data.items():
            if value is not None:
                setattr(user, key, value)

        user.update_time = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_last_login_time(self, user_id: int) -> bool:
        """更新用户最后登录时间"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.last_login_time = datetime.utcnow()
        await self.db.commit()
        return True


class ExchangeRepository:
    """交易所数据访问类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_exchange_by_id(self, exchange_id: int) -> Optional[Exchange]:
        """根据ID获取交易所信息"""
        result = await self.db.execute(
            select(Exchange).where(Exchange.id == exchange_id, Exchange.enable_flag == True)
        )
        return result.scalars().first()

    async def get_all_exchanges(self) -> List[Exchange]:
        """获取所有启用的交易所"""
        result = await self.db.execute(
            select(Exchange).where(Exchange.enable_flag == True)
        )
        return result.scalars().all()

    async def get_exchanges(self, exchange_type: Optional[str] = None,
                            status: Optional[str] = None) -> List[Exchange]:
        """获取交易所列表（支持按类型和状态过滤）"""
        stmt = select(Exchange).where(Exchange.enable_flag == True)
        if exchange_type:
            stmt = stmt.where(Exchange.exchange_type == exchange_type)
        if status:
            stmt = stmt.where(Exchange.status == status)
        result = await self.db.execute(stmt)
        return result.scalars().all()


class APIKeyRepository:
    """API密钥数据访问类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_api_key_by_id(self, api_key_id: int) -> Optional[UserExchangeAPI]:
        """根据ID获取API密钥"""
        result = await self.db.execute(
            select(UserExchangeAPI).where(UserExchangeAPI.id == api_key_id)
        )
        return result.scalars().first()

    async def get_user_api_keys(self, user_id: int) -> List[UserExchangeAPI]:
        """获取用户的所有API密钥"""
        result = await self.db.execute(
            select(UserExchangeAPI).where(
                UserExchangeAPI.user_id == user_id,
                UserExchangeAPI.enable_flag == True,
            )
        )
        return result.scalars().all()

    async def get_api_key_by_exchange(self, user_id: int, exchange_id: int) -> Optional[UserExchangeAPI]:
        """根据用户和交易所获取API密钥"""
        result = await self.db.execute(
            select(UserExchangeAPI).where(
                UserExchangeAPI.user_id == user_id,
                UserExchangeAPI.exchange_id == exchange_id,
                UserExchangeAPI.enable_flag == True,
            )
        )
        return result.scalars().first()

    async def create_api_key(self, api_key_data: dict) -> UserExchangeAPI:
        """创建API密钥"""
        try:
            api_key = UserExchangeAPI(**api_key_data)
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)
            return api_key
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"创建API密钥失败: {e}")
            raise ValueError("API密钥创建失败")

    async def update_api_key(self, api_key_id: int, update_data: dict) -> Optional[UserExchangeAPI]:
        """更新API密钥信息"""
        api_key = await self.get_api_key_by_id(api_key_id)
        if not api_key:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(api_key, key, value)

        api_key.update_time = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def delete_api_key(self, api_key_id: int) -> bool:
        """软删除API密钥"""
        api_key = await self.get_api_key_by_id(api_key_id)
        if not api_key:
            return False

        api_key.enable_flag = False
        api_key.update_time = datetime.utcnow()
        await self.db.commit()
        return True
