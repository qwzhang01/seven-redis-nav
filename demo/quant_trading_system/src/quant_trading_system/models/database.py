"""
数据库模型定义
===========

定义SQLAlchemy ORM模型类，对应数据库表结构。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, BigInteger, Integer
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


class Subscription(Base):
    """行情订阅配置模型"""
    __tablename__ = "subscriptions"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(50), nullable=False)
    market_type = Column(String(20), default="spot")
    data_type = Column(String(20), nullable=False)
    symbols = Column(JSON, nullable=False)
    interval = Column(String(10))
    status = Column(String(20), default="stopped")  # stopped/running/paused
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_sync_time = Column(DateTime)
    total_records = Column(BigInteger, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    config = Column(JSON)

    # 关系
    sync_tasks = relationship("SyncTask", back_populates="subscription", cascade="all, delete-orphan")


class SyncTask(Base):
    """手动同步任务模型"""
    __tablename__ = "sync_tasks"

    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed/cancelled
    progress = Column(Integer, default=0)
    total_records = Column(BigInteger, default=0)
    synced_records = Column(BigInteger, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关系
    subscription = relationship("Subscription", back_populates="sync_tasks")
