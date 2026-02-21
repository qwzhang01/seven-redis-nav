import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from quant_trading_system.models.user import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    PasswordChangeRequest, PasswordResetRequest, APIKeyCreate, APIKeyUpdate,
    UserType, UserStatus, APIKeyStatus
)
from quant_trading_system.models.database import User, Exchange, UserExchangeAPI
from quant_trading_system.services.database.database import get_db as get_db_session


class UserService:
    """用户服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.jwt_secret = "your-secret-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.jwt_expire_minutes = 30

    def hash_password(self, password: str) -> str:
        """密码哈希处理"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def create_jwt_token(self, user_id: int, username: str, user_type: UserType) -> str:
        """创建JWT令牌"""
        payload = {
            "user_id": user_id,
            "username": username,
            "user_type": user_type.value,
            "exp": datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的Token"
            )

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """用户注册"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在"
            )

        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(
            User.email == user_data.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已存在"
            )

        # 创建新用户
        hashed_password = self.hash_password(user_data.password)

        new_user = User(
            username=user_data.username,
            nickname=user_data.nickname,
            password_hash=hashed_password,
            email=user_data.email,
            phone=user_data.phone,
            avatar_url=user_data.avatar_url,
            user_type=user_data.user_type.value,
            registration_time=datetime.utcnow(),
            status=UserStatus.ACTIVE.value,
            create_by="system",
            create_time=datetime.utcnow(),
            enable_flag=True
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return self._user_to_response(new_user)

    def login_user(self, login_data: LoginRequest) -> LoginResponse:
        """用户登录"""
        # 根据用户名或邮箱查找用户
        user = self.db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if not self.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        if user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用"
            )

        # 更新最后登录时间
        user.last_login_time = datetime.utcnow()
        user.update_time = datetime.utcnow()
        self.db.commit()

        # 生成JWT令牌
        token = self.create_jwt_token(
            user.id,
            user.username,
            UserType(user.user_type)
        )

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=self.jwt_expire_minutes * 60,
            user=self._user_to_response(user)
        )

    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据ID获取用户信息"""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.enable_flag == True
        ).first()

        if not user:
            return None

        return self._user_to_response(user)

    def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """根据用户名获取用户信息"""
        user = self.db.query(User).filter(
            User.username == username,
            User.enable_flag == True
        ).first()

        if not user:
            return None

        return self._user_to_response(user)

    def update_user_profile(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        """更新用户信息"""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.enable_flag == True
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 更新字段
        if update_data.nickname is not None:
            user.nickname = update_data.nickname
        if update_data.email is not None:
            user.email = update_data.email
            user.email_verified = False  # 邮箱变更后需要重新验证
        if update_data.phone is not None:
            user.phone = update_data.phone
            user.phone_verified = False  # 手机号变更后需要重新验证
        if update_data.avatar_url is not None:
            user.avatar_url = update_data.avatar_url

        user.update_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        return self._user_to_response(user)

    def change_password(self, user_id: int, password_data: PasswordChangeRequest) -> bool:
        """修改密码"""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.enable_flag == True
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 验证旧密码
        if not self.verify_password(password_data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="旧密码错误"
            )

        # 更新密码
        user.password_hash = self.hash_password(password_data.new_password)
        user.update_time = datetime.utcnow()
        self.db.commit()

        return True

    def reset_password(self, reset_data: PasswordResetRequest) -> bool:
        """重置密码"""
        # TODO: 实现邮箱验证码验证逻辑
        # 这里简化处理，实际应该验证验证码

        user = self.db.query(User).filter(
            User.email == reset_data.email,
            User.enable_flag == True
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="邮箱对应的用户不存在"
            )

        # 更新密码
        user.password_hash = self.hash_password(reset_data.new_password)
        user.update_time = datetime.utcnow()
        self.db.commit()

        return True

    def get_exchanges(self, exchange_type: Optional[str] = None,
                     status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取交易所列表"""
        query = self.db.query(Exchange).filter(Exchange.enable_flag == True)

        if exchange_type:
            query = query.filter(Exchange.exchange_type == exchange_type)
        if status:
            query = query.filter(Exchange.status == status)

        exchanges = query.all()

        return [
            {
                "id": exchange.id,
                "exchange_code": exchange.exchange_code,
                "exchange_name": exchange.exchange_name,
                "exchange_type": exchange.exchange_type,
                "base_url": exchange.base_url,
                "api_doc_url": exchange.api_doc_url,
                "status": exchange.status,
                "supported_pairs": exchange.supported_pairs,
                "rate_limits": exchange.rate_limits,
                "create_time": exchange.create_time,
                "update_time": exchange.update_time
            }
            for exchange in exchanges
        ]

    def get_exchange_by_id(self, exchange_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取交易所信息"""
        exchange = self.db.query(Exchange).filter(
            Exchange.id == exchange_id,
            Exchange.enable_flag == True
        ).first()

        if not exchange:
            return None

        return {
            "id": exchange.id,
            "exchange_code": exchange.exchange_code,
            "exchange_name": exchange.exchange_name,
            "exchange_type": exchange.exchange_type,
            "base_url": exchange.base_url,
            "api_doc_url": exchange.api_doc_url,
            "status": exchange.status,
            "supported_pairs": exchange.supported_pairs,
            "rate_limits": exchange.rate_limits,
            "create_time": exchange.create_time,
            "update_time": exchange.update_time
        }

    def add_api_key(self, user_id: int, api_key_data: APIKeyCreate) -> Dict[str, Any]:
        """添加API密钥"""
        # 检查交易所是否存在
        exchange = self.db.query(Exchange).filter(
            Exchange.id == api_key_data.exchange_id,
            Exchange.enable_flag == True
        ).first()

        if not exchange:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="交易所不存在"
            )

        # 检查标签是否重复
        existing_label = self.db.query(UserExchangeAPI).filter(
            UserExchangeAPI.user_id == user_id,
            UserExchangeAPI.label == api_key_data.label,
            UserExchangeAPI.enable_flag == True
        ).first()

        if existing_label:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="标签已存在"
            )

        # 创建API密钥记录
        new_api_key = UserExchangeAPI(
            user_id=user_id,
            exchange_id=api_key_data.exchange_id,
            label=api_key_data.label,
            api_key=api_key_data.api_key,
            secret_key=api_key_data.secret_key,
            passphrase=api_key_data.passphrase,
            permissions=api_key_data.permissions,
            status=APIKeyStatus.PENDING.value,
            create_by=user_id,
            create_time=datetime.utcnow(),
            enable_flag=True
        )

        self.db.add(new_api_key)
        self.db.commit()
        self.db.refresh(new_api_key)

        return self._api_key_to_response(new_api_key)

    def get_user_api_keys(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取用户的API密钥列表"""
        query = self.db.query(UserExchangeAPI).filter(
            UserExchangeAPI.user_id == user_id,
            UserExchangeAPI.enable_flag == True
        )

        if status:
            query = query.filter(UserExchangeAPI.status == status)

        api_keys = query.all()

        return [self._api_key_to_response(api_key) for api_key in api_keys]

    def get_api_key_by_id(self, api_key_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """根据ID获取API密钥信息"""
        query = self.db.query(UserExchangeAPI).filter(
            UserExchangeAPI.id == api_key_id,
            UserExchangeAPI.enable_flag == True
        )

        if user_id:
            query = query.filter(UserExchangeAPI.user_id == user_id)

        api_key = query.first()

        if not api_key:
            return None

        return self._api_key_to_response(api_key)

    def update_api_key(self, api_key_id: int, user_id: int,
                      update_data: APIKeyUpdate) -> Dict[str, Any]:
        """更新API密钥"""
        api_key = self.db.query(UserExchangeAPI).filter(
            UserExchangeAPI.id == api_key_id,
            UserExchangeAPI.user_id == user_id,
            UserExchangeAPI.enable_flag == True
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API密钥不存在"
            )

        # 更新字段
        if update_data.label is not None:
            api_key.label = update_data.label
        if update_data.permissions is not None:
            api_key.permissions = update_data.permissions
        if update_data.status is not None:
            api_key.status = update_data.status.value

        api_key.update_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(api_key)

        return self._api_key_to_response(api_key)

    def delete_api_key(self, api_key_id: int, user_id: int) -> bool:
        """删除API密钥"""
        api_key = self.db.query(UserExchangeAPI).filter(
            UserExchangeAPI.id == api_key_id,
            UserExchangeAPI.user_id == user_id,
            UserExchangeAPI.enable_flag == True
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API密钥不存在"
            )

        # 逻辑删除
        api_key.enable_flag = False
        api_key.update_time = datetime.utcnow()
        self.db.commit()

        return True

    def _user_to_response(self, user: User) -> UserResponse:
        """将User对象转换为UserResponse"""
        return UserResponse(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            email_verified=user.email_verified,
            phone=user.phone,
            phone_verified=user.phone_verified,
            avatar_url=user.avatar_url,
            user_type=UserType(user.user_type),
            registration_time=user.registration_time,
            last_login_time=user.last_login_time,
            status=UserStatus(user.status),
            create_time=user.create_time,
            update_time=user.update_time
        )

    def _api_key_to_response(self, api_key: UserExchangeAPI) -> Dict[str, Any]:
        """将API密钥对象转换为响应格式"""
        return {
            "id": api_key.id,
            "user_id": api_key.user_id,
            "exchange_id": api_key.exchange_id,
            "label": api_key.label,
            "api_key": api_key.api_key,
            "status": api_key.status,
            "review_reason": api_key.review_reason,
            "approved_by": api_key.approved_by,
            "approved_time": api_key.approved_time,
            "last_used_time": api_key.last_used_time,
            "create_time": api_key.create_time,
            "update_time": api_key.update_time
        }


def get_user_service() -> UserService:
    """获取用户服务实例"""
    db = next(get_db_session())
    return UserService(db)
