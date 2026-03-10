"""
跟单模块数据库模型
=================

包含信号跟单相关的所有 ORM 模型：
- SignalFollowOrder: 信号跟单订单主表
- SignalFollowPosition: 信号跟单持仓
- SignalFollowTrade: 信号跟单交易记录
- SignalFollowEvent: 信号跟单事件日志
- SignalFollowReturnCurve: 跟单收益曲线
- ExchangeCopyAccount: 交易所跟单账户
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, \
    BigInteger, \
    Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class SignalFollowOrder(Base):
    """信号跟单订单主表模型"""
    __tablename__ = "signal_follow_orders"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False)
    strategy_id = Column(String(128), nullable=False)
    signal_name = Column(String(256), nullable=False)
    exchange = Column(String(32), nullable=False, default="binance")
    follow_amount = Column(Numeric(20, 2), nullable=False)
    current_value = Column(Numeric(20, 2))
    follow_ratio = Column(Numeric(5, 4), default=1.0)
    stop_loss = Column(Numeric(5, 4))
    total_return = Column(Numeric(10, 6), default=0)
    max_drawdown = Column(Numeric(10, 6), default=0)
    current_drawdown = Column(Numeric(10, 6), default=0)
    today_return = Column(Numeric(10, 6), default=0)
    win_rate = Column(Numeric(10, 6), default=0)
    total_trades = Column(Integer, default=0)
    win_trades = Column(Integer, default=0)
    loss_trades = Column(Integer, default=0)
    avg_win = Column(Numeric(20, 8), default=0)
    avg_loss = Column(Numeric(20, 8), default=0)
    profit_factor = Column(Numeric(10, 4), default=0)
    risk_level = Column(String(16), default="low")
    status = Column(String(16), default="following")
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    stop_time = Column(DateTime(timezone=True))
    return_curve = Column(JSONB)
    return_curve_labels = Column(JSONB)
    create_by = Column(String(64))
    create_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    update_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    enable_flag = Column(Boolean, default=True)

    # 关系
    positions = relationship("SignalFollowPosition", back_populates="follow_order",
                             cascade="all, delete-orphan",
                             foreign_keys="[SignalFollowPosition.follow_order_id]",
                             primaryjoin="SignalFollowOrder.id == SignalFollowPosition.follow_order_id")
    trades = relationship("SignalFollowTrade", back_populates="follow_order",
                          cascade="all, delete-orphan",
                          foreign_keys="[SignalFollowTrade.follow_order_id]",
                          primaryjoin="SignalFollowOrder.id == SignalFollowTrade.follow_order_id")


class SignalFollowPosition(Base):
    """信号跟单持仓模型"""
    __tablename__ = "signal_follow_positions"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    follow_order_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(20, 8), nullable=False)
    current_price = Column(Numeric(20, 8))
    pnl = Column(Numeric(20, 8), default=0)
    pnl_percent = Column(Numeric(10, 6), default=0)
    status = Column(String(16), default="open")
    open_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    close_time = Column(DateTime(timezone=True))
    create_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    update_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # 关系
    follow_order = relationship("SignalFollowOrder", back_populates="positions",
                                foreign_keys=[follow_order_id],
                                primaryjoin="SignalFollowPosition.follow_order_id == SignalFollowOrder.id")


class SignalFollowTrade(Base):
    """信号跟单交易记录模型"""
    __tablename__ = "signal_follow_trades"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    follow_order_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    position_id = Column(BigInteger)
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)
    price = Column(Numeric(20, 8), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    total = Column(Numeric(20, 8), nullable=False)
    pnl = Column(Numeric(20, 8))
    fee = Column(Numeric(20, 8), default=0)
    signal_record_id = Column(BigInteger)
    signal_time = Column(DateTime(timezone=True))
    slippage = Column(Numeric(10, 6), default=0)
    trade_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    create_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # 关系
    follow_order = relationship("SignalFollowOrder", back_populates="trades",
                                foreign_keys=[follow_order_id],
                                primaryjoin="SignalFollowTrade.follow_order_id == SignalFollowOrder.id")


class SignalFollowEvent(Base):
    """信号跟单事件日志模型"""
    __tablename__ = "signal_follow_events"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    follow_order_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    event_type = Column(String(16), nullable=False)
    type_label = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    event_meta = Column(JSONB)
    event_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    create_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SignalFollowReturnCurve(Base):
    """跟单收益曲线模型（时序表）"""
    __tablename__ = "signal_follow_return_curve"

    follow_id = Column(BigInteger, primary_key=True)
    time = Column(DateTime(timezone=True), primary_key=True)
    return_value = Column(Numeric(12, 4), nullable=False)
    signal_return = Column(Numeric(12, 4))


class ExchangeCopyAccount(Base):
    """交易所跟单账户模型"""
    __tablename__ = "exchange_copy_accounts"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False)
    exchange = Column(String(32), nullable=False, default="binance")
    account_type = Column(String(16), nullable=False, default="spot")
    target_account_id = Column(String(256), nullable=False)
    target_account_name = Column(String(256))
    api_key_id = Column(BigInteger)
    follow_order_id = Column(BigInteger)
    sync_interval = Column(Integer, default=5)
    last_sync_time = Column(DateTime(timezone=True))
    last_sync_order_id = Column(String(256))
    status = Column(String(16), default="active")
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    config = Column(JSONB, default={})
    create_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    update_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    enable_flag = Column(Boolean, default=True)

    # 关系
    user = relationship("User", foreign_keys=[user_id],
                        primaryjoin="ExchangeCopyAccount.user_id == User.id")
    api_key = relationship("UserExchangeAPI", foreign_keys=[api_key_id],
                           primaryjoin="ExchangeCopyAccount.api_key_id == UserExchangeAPI.id")
    follow_order = relationship("SignalFollowOrder", foreign_keys=[follow_order_id],
                                primaryjoin="ExchangeCopyAccount.follow_order_id == SignalFollowOrder.id")
