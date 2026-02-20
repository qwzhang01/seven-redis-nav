"""
数据库模型定义
===========

定义SQLAlchemy ORM模型类，对应数据库表结构。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, BigInteger, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
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


class SignalRecord(Base):
    """策略信号记录模型"""
    __tablename__ = "signal_records"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    strategy_id = Column(String(128), nullable=False)
    strategy_name = Column(String(128))
    symbol = Column(String(32), nullable=False)
    exchange = Column(String(32), default="binance")
    signal_type = Column(String(16), nullable=False)   # buy/sell/close
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8))
    confidence = Column(Numeric(5, 4))
    timeframe = Column(String(8))
    reason = Column(Text)
    indicators = Column(JSONB)
    status = Column(String(16), default="pending")     # pending/executed/ignored/expired
    executed_order_id = Column(String(128))
    executed_price = Column(Numeric(20, 8))
    executed_at = Column(DateTime)
    is_public = Column(Boolean, default=False)
    subscriber_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class SignalSubscription(Base):
    """用户订阅信号模型"""
    __tablename__ = "signal_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(String(128), nullable=False)
    notify_type = Column(String(32), default="realtime")  # realtime/daily/weekly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class LeaderboardSnapshot(Base):
    """排行榜快照模型"""
    __tablename__ = "leaderboard_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    rank_type = Column(String(32), nullable=False)     # strategy/signal/user
    period = Column(String(16), nullable=False)        # daily/weekly/monthly/all_time
    rank_position = Column(Integer, nullable=False)
    entity_id = Column(String(128), nullable=False)
    entity_name = Column(String(256))
    entity_type = Column(String(64))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user_info.id"))
    owner_name = Column(String(128))
    total_return = Column(Numeric(10, 6))
    annual_return = Column(Numeric(10, 6))
    max_drawdown = Column(Numeric(10, 6))
    sharpe_ratio = Column(Numeric(10, 6))
    win_rate = Column(Numeric(10, 6))
    total_trades = Column(Integer, default=0)
    profit_factor = Column(Numeric(10, 4))
    stat_start_time = Column(DateTime)
    stat_end_time = Column(DateTime)
    snapshot_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """审计日志模型（时序表，联合主键）"""
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, primary_key=True, default=datetime.utcnow, nullable=False)
    log_level = Column(String(16), nullable=False, default="INFO")
    log_category = Column(String(32), nullable=False)  # system/trading/strategy/user/risk/market
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_info.id"))
    username = Column(String(64))
    action = Column(String(128), nullable=False)
    resource_type = Column(String(64))
    resource_id = Column(String(128))
    request_ip = Column(String(64))
    request_path = Column(String(512))
    request_method = Column(String(16))
    request_body = Column(JSONB)
    response_status = Column(Integer)
    duration_ms = Column(Integer)
    message = Column(Text)
    extra_data = Column(JSONB)


class RiskAlert(Base):
    """风控告警模型"""
    __tablename__ = "risk_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    alert_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    alert_type = Column(String(32), nullable=False)    # drawdown/position_limit/loss_limit/volatility
    severity = Column(String(16), nullable=False, default="warning")  # info/warning/critical
    strategy_id = Column(String(128))
    symbol = Column(String(32))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_info.id"))
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    trigger_value = Column(Numeric(20, 8))
    threshold_value = Column(Numeric(20, 8))
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    extra_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
