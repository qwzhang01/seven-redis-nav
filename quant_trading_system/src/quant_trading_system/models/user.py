"""
用户领域 ORM 模型
=================

User / Exchange / UserExchangeAPI
"""

from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, BigInteger
from sqlalchemy.orm import relationship

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class User(Base):
    """用户信息模型"""
    __tablename__ = "user_info"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    username = Column(String(64), nullable=False, unique=True)
    nickname = Column(String(128), nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    email_verified = Column(Boolean, default=False)
    phone = Column(String(32))
    phone_verified = Column(Boolean, default=False)
    avatar_url = Column(String(512))
    user_type = Column(String(32), default="customer")
    registration_time = Column(DateTime, default=datetime.utcnow)
    last_login_time = Column(DateTime)
    status = Column(String(32), default="active")
    invitation_code = Column(String(64), nullable=False)
    inviter_id = Column(BigInteger)
    create_by = Column(String(64), default="system")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    api_keys = relationship("UserExchangeAPI", back_populates="user",
                            foreign_keys="[UserExchangeAPI.user_id]",
                            primaryjoin="User.id == UserExchangeAPI.user_id")
    inviter = relationship("User", remote_side=[id], backref="invited_users",
                           foreign_keys=[inviter_id],
                           primaryjoin="User.inviter_id == User.id")


class Exchange(Base):
    """交易所信息模型"""
    __tablename__ = "exchange_info"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    exchange_code = Column(String(32), nullable=False)
    exchange_name = Column(String(128), nullable=False)
    exchange_type = Column(String(32), default="spot")
    base_url = Column(String(512), nullable=False)
    api_doc_url = Column(String(512))
    status = Column(String(32), default="active")
    supported_pairs = Column(JSON)
    rate_limits = Column(JSON)
    create_by = Column(String(64), default="system")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    api_keys = relationship("UserExchangeAPI", back_populates="exchange",
                            foreign_keys="[UserExchangeAPI.exchange_id]",
                            primaryjoin="Exchange.id == UserExchangeAPI.exchange_id")


class UserExchangeAPI(Base):
    """用户交易所API密钥模型"""
    __tablename__ = "user_exchange_api"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False)
    exchange_id = Column(BigInteger, nullable=False)
    label = Column(String(128), nullable=False)
    api_key = Column(String(512), nullable=False)
    secret_key = Column(String(512), nullable=False)
    passphrase = Column(String(512))
    permissions = Column(JSON)
    status = Column(String(32), default="pending")
    review_reason = Column(Text)
    approved_by = Column(String(64))
    approved_time = Column(DateTime)
    last_used_time = Column(DateTime)
    create_by = Column(String(64))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    user = relationship("User", back_populates="api_keys", foreign_keys=[user_id],
                        primaryjoin="UserExchangeAPI.user_id == User.id")
    exchange = relationship("Exchange", back_populates="api_keys",
                            foreign_keys=[exchange_id],
                            primaryjoin="UserExchangeAPI.exchange_id == Exchange.id")
