"""
行情订阅 & 同步任务 ORM 模型
============================

Subscription / SyncTask / HistoricalSyncTask
"""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, JSON, BigInteger, Integer
from sqlalchemy.orm import relationship

from quant_trading_system.models.base import Base


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
    status = Column(String(20), default="stopped")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_sync_time = Column(DateTime)
    total_records = Column(BigInteger, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    config = Column(JSON)

    # 关系
    sync_tasks = relationship("SyncTask", back_populates="subscription",
                              cascade="all, delete-orphan",
                              foreign_keys="[SyncTask.subscription_id]",
                              primaryjoin="Subscription.id == SyncTask.subscription_id")


class HistoricalSyncTask(Base):
    """历史数据同步任务模型（独立于订阅）"""
    __tablename__ = "historical_sync_tasks"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(50), nullable=False)
    data_type = Column(String(20), nullable=False)
    symbols = Column(JSON, nullable=False)
    interval = Column(String(10))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    batch_size = Column(Integer, default=1000)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    total_records = Column(BigInteger, default=0)
    synced_records = Column(BigInteger, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class SyncTask(Base):
    """手动同步任务模型"""
    __tablename__ = "sync_tasks"

    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    total_records = Column(BigInteger, default=0)
    synced_records = Column(BigInteger, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # 关系
    subscription = relationship("Subscription", back_populates="sync_tasks",
                                foreign_keys=[subscription_id],
                                primaryjoin="SyncTask.subscription_id == Subscription.id")
