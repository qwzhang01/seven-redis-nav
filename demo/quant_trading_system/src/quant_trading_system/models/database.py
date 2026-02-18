"""
数据库模型定义
===========

定义SQLAlchemy ORM模型类，对应数据库表结构。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户信息模型"""
    __tablename__ = "user_info"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
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
    create_by = Column(String(64), default="system")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_by = Column(String(64))
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    api_keys = relationship("UserExchangeAPI", back_populates="user")


class Exchange(Base):
    """交易所信息模型"""
    __tablename__ = "exchange_info"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
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
    api_keys = relationship("UserExchangeAPI", back_populates="exchange")


class UserExchangeAPI(Base):
    """用户交易所API密钥模型"""
    __tablename__ = "user_exchange_api"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_info.id"), nullable=False)
    exchange_id = Column(UUID(as_uuid=True), ForeignKey("exchange_info.id"), nullable=False)
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
    user = relationship("User", back_populates="api_keys")
    exchange = relationship("Exchange", back_populates="api_keys")
