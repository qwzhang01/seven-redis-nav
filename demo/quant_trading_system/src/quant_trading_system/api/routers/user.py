"""
用户管理路由模块
===========

提供用户注册、登录、密码管理、用户信息查询和交易所API密钥管理功能。

主要功能：
- 用户注册和登录
- 密码修改和重置
- 用户信息管理
- 交易所API密钥管理
- 交易所信息查询
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import EmailStr

from quant_trading_system.models.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyListResponse,
    ExchangeInfo,
    ExchangeListResponse,
    UserListResponse,
    UserType,
    APIKeyStatus
)

# 创建用户路由实例
router = APIRouter()

# JWT配置（实际项目中应从配置文件中读取）
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HTTP Bearer认证
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据"
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )


# 模拟数据库操作（实际项目中应使用真实的数据库操作）
class MockDatabase:
    """模拟数据库操作类"""

    def __init__(self):
        self.users = {}
        self.exchanges = {}
        self.api_keys = {}

        # 初始化一些示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        # 示例交易所
        self.exchanges = {
            "binance": ExchangeInfo(
                id="1",
                exchange_code="binance",
                exchange_name="币安",
                exchange_type="spot",
                base_url="https://api.binance.com",
                api_doc_url="https://binance-docs.github.io/apidocs/",
                status="active",
                supported_pairs={"BTCUSDT", "ETHUSDT", "BNBUSDT"},
                rate_limits={"requests_per_minute": 1200},
                create_time=datetime.now(),
                update_time=datetime.now()
            ),
            "okx": ExchangeInfo(
                id="2",
                exchange_code="okx",
                exchange_name="欧易",
                exchange_type="spot",
                base_url="https://www.okx.com",
                api_doc_url="https://www.okx.com/docs/",
                status="active",
                supported_pairs={"BTC-USDT", "ETH-USDT", "OKB-USDT"},
                rate_limits={"requests_per_minute": 300},
                create_time=datetime.now(),
                update_time=datetime.now()
            )
        }


db = MockDatabase()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    用户注册

    注册新用户账户，需要提供用户名、邮箱和密码等信息。

    参数：
    - username: 用户名（唯一）
    - nickname: 昵称
    - email: 邮箱地址（唯一）
    - password: 密码（至少6位）

    返回：
    - 注册成功的用户信息
    """
    # 检查用户名是否已存在
    if user_data.username in db.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    for user in db.users.values():
        if user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱地址已存在"
            )

    # 创建用户（实际项目中应对密码进行哈希处理）
    user_id = str(len(db.users) + 1)
    user = UserResponse(
        id=user_id,
        username=user_data.username,
        nickname=user_data.nickname,
        email=user_data.email,
        phone=user_data.phone,
        avatar_url=user_data.avatar_url,
        user_type=user_data.user_type,
        email_verified=False,
        phone_verified=False,
        registration_time=datetime.now(),
        last_login_time=None,
        status="active",
        create_time=datetime.now(),
        update_time=datetime.now()
    )

    db.users[user_data.username] = user

    return user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    用户登录

    使用用户名/邮箱和密码进行登录，返回JWT访问令牌。

    参数：
    - username: 用户名或邮箱
    - password: 密码

    返回：
    - access_token: JWT访问令牌
    - token_type: 令牌类型（bearer）
    - expires_in: 过期时间（秒）
    - user: 用户信息
    """
    # 模拟用户验证（实际项目中应验证密码哈希）
    user = None
    for u in db.users.values():
        if u.username == login_data.username or u.email == login_data.username:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 模拟密码验证（实际项目中应使用密码哈希验证）
    if login_data.password != "password123":  # 示例密码
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 更新最后登录时间
    user.last_login_time = datetime.now()

    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
        user=user
    )


@router.post("/password/change")
async def change_password(
    password_data: PasswordChangeRequest,
    username: str = Depends(verify_token)
):
    """
    修改密码

    用户登录后修改自己的密码。

    参数：
    - old_password: 旧密码
    - new_password: 新密码

    返回：
    - 修改成功消息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 模拟旧密码验证（实际项目中应验证密码哈希）
    if password_data.old_password != "password123":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 模拟密码修改（实际项目中应对新密码进行哈希处理）
    user.update_time = datetime.now()

    return {"message": "密码修改成功"}


@router.post("/password/reset")
async def reset_password(
    background_tasks: BackgroundTasks,
    reset_data: PasswordResetRequest
):
    """
    忘记密码重置

    通过邮箱验证码重置密码。

    参数：
    - email: 邮箱地址
    - verification_code: 验证码
    - new_password: 新密码

    返回：
    - 重置成功消息
    """
    # 查找用户
    user = None
    for u in db.users.values():
        if u.email == reset_data.email:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邮箱地址不存在"
        )

    # 模拟验证码验证（实际项目中应验证邮箱验证码）
    if reset_data.verification_code != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # 模拟密码重置（实际项目中应对新密码进行哈希处理）
    user.update_time = datetime.now()

    return {"message": "密码重置成功"}


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(username: str = Depends(verify_token)):
    """
    获取用户账号信息

    获取当前登录用户的详细信息。

    返回：
    - 用户详细信息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    username: str = Depends(verify_token)
):
    """
    更新用户信息

    更新当前登录用户的个人信息。

    参数：
    - nickname: 昵称（可选）
    - email: 邮箱地址（可选）
    - phone: 手机号（可选）
    - avatar_url: 头像URL（可选）

    返回：
    - 更新后的用户信息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 更新用户信息
    if user_update.nickname is not None:
        user.nickname = user_update.nickname
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.avatar_url is not None:
        user.avatar_url = user_update.avatar_url

    user.update_time = datetime.now()

    return user


@router.get("/exchanges", response_model=ExchangeListResponse)
async def get_exchanges(
    exchange_type: Optional[str] = None,
    status: Optional[str] = None
):
    """
    获取交易所列表

    获取支持的交易所信息列表，可按类型和状态筛选。

    参数：
    - exchange_type: 交易所类型筛选（spot/futures/margin）
    - status: 状态筛选（active/inactive）

    返回：
    - 交易所列表
    """
    exchanges = list(db.exchanges.values())

    # 筛选
    if exchange_type:
        exchanges = [e for e in exchanges if e.exchange_type == exchange_type]
    if status:
        exchanges = [e for e in exchanges if e.status == status]

    return ExchangeListResponse(total=len(exchanges), items=exchanges)


@router.get("/exchanges/{exchange_id}", response_model=ExchangeInfo)
async def get_exchange(exchange_id: str):
    """
    获取交易所详情

    根据交易所ID获取详细信息。

    参数：
    - exchange_id: 交易所ID

    返回：
    - 交易所详细信息
    """
    exchange = db.exchanges.get(exchange_id)
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在"
        )

    return exchange


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    username: str = Depends(verify_token)
):
    """
    添加API密钥

    为用户添加交易所API密钥，需要经过后台审核。

    参数：
    - exchange_id: 交易所ID
    - label: 标签
    - api_key: API密钥
    - secret_key: Secret密钥
    - passphrase: 密码短语（可选）
    - permissions: 权限配置（可选）

    返回：
    - 创建的API密钥信息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查交易所是否存在
    exchange = db.exchanges.get(api_key_data.exchange_id)
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在"
        )

    # 创建API密钥记录
    api_key_id = str(len(db.api_keys) + 1)
    api_key = APIKeyResponse(
        id=api_key_id,
        user_id=user.id,
        exchange_id=api_key_data.exchange_id,
        label=api_key_data.label,
        api_key=api_key_data.api_key,
        status=APIKeyStatus.PENDING,
        review_reason=None,
        approved_by=None,
        approved_time=None,
        last_used_time=None,
        create_time=datetime.now(),
        update_time=datetime.now()
    )

    db.api_keys[api_key_id] = api_key

    return api_key


@router.get("/api-keys", response_model=APIKeyListResponse)
async def get_api_keys(
    status: Optional[str] = None,
    username: str = Depends(verify_token)
):
    """
    获取API密钥列表

    获取当前用户的API密钥列表，可按状态筛选。

    参数：
    - status: 状态筛选（pending/approved/rejected/disabled）

    返回：
    - API密钥列表
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 获取用户的API密钥
    user_api_keys = [
        api_key for api_key in db.api_keys.values()
        if api_key.user_id == user.id
    ]

    # 筛选
    if status:
        user_api_keys = [api_key for api_key in user_api_keys if api_key.status == status]

    return APIKeyListResponse(total=len(user_api_keys), items=user_api_keys)


@router.get("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: str,
    username: str = Depends(verify_token)
):
    """
    获取API密钥详情

    根据ID获取API密钥的详细信息。

    参数：
    - api_key_id: API密钥ID

    返回：
    - API密钥详细信息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.api_keys.get(api_key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )

    # 检查权限
    if api_key.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此API密钥"
        )

    return api_key


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: str,
    api_key_update: APIKeyUpdate,
    username: str = Depends(verify_token)
):
    """
    更新API密钥

    更新API密钥的标签、权限或状态。

    参数：
    - api_key_id: API密钥ID
    - label: 标签（可选）
    - permissions: 权限配置（可选）
    - status: 状态（可选）

    返回：
    - 更新后的API密钥信息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.api_keys.get(api_key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )

    # 检查权限
    if api_key.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此API密钥"
        )

    # 更新API密钥信息
    if api_key_update.label is not None:
        api_key.label = api_key_update.label
    if api_key_update.permissions is not None:
        api_key.permissions = api_key_update.permissions
    if api_key_update.status is not None:
        api_key.status = api_key_update.status

    api_key.update_time = datetime.now()

    return api_key


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    username: str = Depends(verify_token)
):
    """
    删除API密钥

    删除指定的API密钥记录。

    参数：
    - api_key_id: API密钥ID

    返回：
    - 删除成功消息
    """
    user = db.users.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.api_keys.get(api_key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )

    # 检查权限
    if api_key.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此API密钥"
        )

    # 删除API密钥
    del db.api_keys[api_key_id]

    return {"message": "API密钥删除成功"}
