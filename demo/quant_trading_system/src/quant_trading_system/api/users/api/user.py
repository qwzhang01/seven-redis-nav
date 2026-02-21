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

from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# 导入数据库模型和配置
from quant_trading_system.models.database import User, Exchange, UserExchangeAPI
from quant_trading_system.models.user import (
    UserCreate, UserResponse, UserUpdate,
    LoginRequest, LoginResponse,
    PasswordChangeRequest, PasswordResetRequest,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyListResponse,
    ExchangeInfo,
    UserType, APIKeyStatus
)
from quant_trading_system.services.database.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id

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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
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
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱地址已存在"
        )

    # 创建用户（实际项目中应对密码进行哈希处理）
    user_id = generate_snowflake_id()

    # 密码哈希处理
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), salt)

    new_user = User(
        id=user_id,
        username=user_data.username,
        nickname=user_data.nickname,
        password_hash=hashed_password.decode('utf-8'),
        email=user_data.email,
        phone=user_data.phone,
        avatar_url=user_data.avatar_url,
        user_type=user_data.user_type.value if hasattr(user_data.user_type, 'value') else user_data.user_type,
        email_verified=False,
        phone_verified=False,
        registration_time=datetime.utcnow(),
        last_login_time=None,
        status="active",
        create_by="system",
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow(),
        enable_flag=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 转换为响应模型
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        nickname=new_user.nickname,
        email=new_user.email,
        phone=new_user.phone,
        avatar_url=new_user.avatar_url,
        user_type=UserType(new_user.user_type),
        email_verified=new_user.email_verified,
        phone_verified=new_user.phone_verified,
        registration_time=new_user.registration_time,
        last_login_time=new_user.last_login_time,
        status=new_user.status,
        create_time=new_user.create_time,
        update_time=new_user.update_time
    )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
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
    # 根据用户名或邮箱查找用户
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username),
        User.enable_flag == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码（实际项目中应使用密码哈希验证）
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 更新最后登录时间
    user.last_login_time = datetime.utcnow()
    user.update_time = datetime.utcnow()
    db.commit()

    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )

    # 转换为响应模型
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        user_type=UserType(user.user_type),
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        registration_time=user.registration_time,
        last_login_time=user.last_login_time,
        status=user.status,
        create_time=user.create_time,
        update_time=user.update_time
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
        user=user_response
    )


@router.post("/password/change")
async def change_password(
    password_data: PasswordChangeRequest,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
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
    user = db.query(User).filter(
        User.username == username,
        User.enable_flag == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 验证旧密码
    if not bcrypt.checkpw(password_data.old_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    # 对新密码进行哈希处理
    salt = bcrypt.gensalt()
    new_hashed_password = bcrypt.hashpw(password_data.new_password.encode('utf-8'), salt)

    # 更新密码和更新时间
    user.password_hash = new_hashed_password.decode('utf-8')
    user.update_time = datetime.utcnow()
    db.commit()

    return {"message": "密码修改成功"}


@router.post("/password/reset")
async def reset_password(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
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
    user = db.query(User).filter(User.email == reset_data.email).first()
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
    user.update_time = datetime.utcnow()
    db.commit()

    return {"message": "密码重置成功"}


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
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
    user = db.query(User).filter(User.username == username).first()
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

    user.update_time = datetime.utcnow()
    db.commit()

    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        user_type=UserType(user.user_type),
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        registration_time=user.registration_time,
        last_login_time=user.last_login_time,
        status=user.status,
        create_time=user.create_time,
        update_time=user.update_time
    )


@router.get("/exchanges/{exchange_id}", response_model=ExchangeInfo)
async def get_exchange(
    exchange_id: int,
    db: Session = Depends(get_db)
):
    """
    获取交易所详情

    根据交易所ID获取详细信息。

    参数：
    - exchange_id: 交易所ID

    返回：
    - 交易所详细信息
    """
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在"
        )

    return ExchangeInfo(
        id=exchange.id,
        exchange_code=exchange.exchange_code,
        exchange_name=exchange.exchange_name,
        exchange_type=exchange.exchange_type,
        base_url=exchange.base_url,
        api_doc_url=exchange.api_doc_url,
        status=exchange.status,
        supported_pairs=exchange.supported_pairs,
        rate_limits=exchange.rate_limits,
        create_time=exchange.create_time,
        update_time=exchange.update_time
    )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
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
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查交易所是否存在
    exchange = db.query(Exchange).filter(Exchange.id == api_key_data.exchange_id).first()
    if not exchange:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所不存在"
        )

    # 创建 API 密钥记录
    api_key_id = generate_snowflake_id()

    new_api_key = UserExchangeAPI(
        id=api_key_id,
        user_id=user.id,
        exchange_id=api_key_data.exchange_id,
        label=api_key_data.label,
        api_key=api_key_data.api_key,
        secret_key=api_key_data.secret_key,
        passphrase=api_key_data.passphrase,
        permissions=api_key_data.permissions,
        status="pending",
        create_by=username,
        create_time=datetime.utcnow(),
        update_time=datetime.utcnow()
    )

    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)

    return APIKeyResponse(
        id=new_api_key.id,
        user_id=new_api_key.user_id,
        exchange_id=new_api_key.exchange_id,
        label=new_api_key.label,
        api_key=new_api_key.api_key,
        status=APIKeyStatus(new_api_key.status),
        review_reason=new_api_key.review_reason,
        approved_by=new_api_key.approved_by,
        approved_time=new_api_key.approved_time,
        last_used_time=new_api_key.last_used_time,
        create_time=new_api_key.create_time,
        update_time=new_api_key.update_time
    )


@router.get("/api-keys", response_model=APIKeyListResponse)
async def get_api_keys(
    status: Optional[str] = None,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    获取API密钥列表

    获取当前用户的API密钥列表，可按状态筛选。

    参数：
    - status: 状态筛选（pending/approved/rejected/disabled）

    返回：
    - API密钥列表
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 获取用户的API密钥
    query = db.query(UserExchangeAPI).filter(UserExchangeAPI.user_id == user.id)
    if status:
        query = query.filter(UserExchangeAPI.status == status)

    user_api_keys = query.all()

    # 转换为响应模型
    api_key_items = []
    for api_key in user_api_keys:
        api_key_items.append(APIKeyResponse(
            id=api_key.id,
            user_id=api_key.user_id,
            exchange_id=api_key.exchange_id,
            label=api_key.label,
            api_key=api_key.api_key,
            status=APIKeyStatus(api_key.status),
            review_reason=api_key.review_reason,
            approved_by=api_key.approved_by,
            approved_time=api_key.approved_time,
            last_used_time=api_key.last_used_time,
            create_time=api_key.create_time,
            update_time=api_key.update_time
        ))

    return APIKeyListResponse(total=len(api_key_items), items=api_key_items)


@router.get("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: int,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    获取API密钥详情

    根据ID获取API密钥的详细信息。

    参数：
    - api_key_id: API密钥ID

    返回：
    - API密钥详细信息
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
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

    return APIKeyResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        exchange_id=api_key.exchange_id,
        label=api_key.label,
        api_key=api_key.api_key,
        status=APIKeyStatus(api_key.status),
        review_reason=api_key.review_reason,
        approved_by=api_key.approved_by,
        approved_time=api_key.approved_time,
        last_used_time=api_key.last_used_time,
        create_time=api_key.create_time,
        update_time=api_key.update_time
    )


@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    api_key_update: APIKeyUpdate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
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
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
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

    api_key.update_time = datetime.utcnow()
    db.commit()

    return APIKeyResponse(
        id=api_key.id,
        user_id=api_key.user_id,
        exchange_id=api_key.exchange_id,
        label=api_key.label,
        api_key=api_key.api_key,
        status=APIKeyStatus(api_key.status),
        review_reason=api_key.review_reason,
        approved_by=api_key.approved_by,
        approved_time=api_key.approved_time,
        last_used_time=api_key.last_used_time,
        create_time=api_key.create_time,
        update_time=api_key.update_time
    )


@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    删除API密钥

    删除指定的API密钥记录。

    参数：
    - api_key_id: API密钥ID

    返回：
    - 删除成功消息
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    api_key = db.query(UserExchangeAPI).filter(UserExchangeAPI.id == api_key_id).first()
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
    db.delete(api_key)
    db.commit()

    return {"message": "API密钥删除成功"}
