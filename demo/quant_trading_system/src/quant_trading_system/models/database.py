"""
数据库模型定义
===========

定义SQLAlchemy ORM模型类，对应数据库表结构。
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, BigInteger, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from quant_trading_system.core.snowflake import generate_snowflake_id

Base = declarative_base()


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
    api_keys = relationship("UserExchangeAPI", back_populates="exchange")


class UserExchangeAPI(Base):
    """用户交易所API密钥模型"""
    __tablename__ = "user_exchange_api"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, ForeignKey("user_info.id"), nullable=False)
    exchange_id = Column(BigInteger, ForeignKey("exchange_info.id"), nullable=False)
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

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
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

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(String(128), nullable=False)
    notify_type = Column(String(32), default="realtime")  # realtime/daily/weekly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class LeaderboardSnapshot(Base):
    """排行榜快照模型"""
    __tablename__ = "leaderboard_snapshots"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    rank_type = Column(String(32), nullable=False)     # strategy/signal/user
    period = Column(String(16), nullable=False)        # daily/weekly/monthly/all_time
    rank_position = Column(Integer, nullable=False)
    entity_id = Column(String(128), nullable=False)
    entity_name = Column(String(256))
    entity_type = Column(String(64))
    owner_id = Column(BigInteger, ForeignKey("user_info.id"))
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
    user_id = Column(BigInteger, ForeignKey("user_info.id"))
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

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    alert_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    alert_type = Column(String(32), nullable=False)    # drawdown/position_limit/loss_limit/volatility
    severity = Column(String(16), nullable=False, default="warning")  # info/warning/critical
    strategy_id = Column(String(128))
    symbol = Column(String(32))
    user_id = Column(BigInteger, ForeignKey("user_info.id"))
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    trigger_value = Column(Numeric(20, 8))
    threshold_value = Column(Numeric(20, 8))
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    extra_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignalFollowOrder(Base):
    """信号跟单订单主表模型"""
    __tablename__ = "signal_follow_orders"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(String(128), nullable=False)
    signal_name = Column(String(256), nullable=False)
    exchange = Column(String(32), nullable=False, default="binance")
    follow_amount = Column(Numeric(20, 2), nullable=False)       # 跟单资金（USDT）
    current_value = Column(Numeric(20, 2))                       # 当前净值（USDT）
    follow_ratio = Column(Numeric(5, 4), default=1.0)            # 跟单比例
    stop_loss = Column(Numeric(5, 4))                            # 止损比例
    total_return = Column(Numeric(10, 6), default=0)             # 总收益率
    max_drawdown = Column(Numeric(10, 6), default=0)             # 最大回撤
    current_drawdown = Column(Numeric(10, 6), default=0)         # 当前回撤
    today_return = Column(Numeric(10, 6), default=0)             # 今日收益率
    win_rate = Column(Numeric(10, 6), default=0)                 # 胜率
    total_trades = Column(Integer, default=0)                    # 总交易次数
    win_trades = Column(Integer, default=0)                      # 盈利次数
    loss_trades = Column(Integer, default=0)                     # 亏损次数
    avg_win = Column(Numeric(20, 8), default=0)                  # 平均盈利（USDT）
    avg_loss = Column(Numeric(20, 8), default=0)                 # 平均亏损（USDT）
    profit_factor = Column(Numeric(10, 4), default=0)            # 盈亏比
    risk_level = Column(String(16), default="low")               # low/medium/high
    status = Column(String(16), default="following")             # following/stopped/paused
    start_time = Column(DateTime, default=datetime.utcnow)
    stop_time = Column(DateTime)
    return_curve = Column(JSONB)                                 # 收益曲线数据
    return_curve_labels = Column(JSONB)                          # 收益曲线时间标签
    create_by = Column(String(64))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    positions = relationship("SignalFollowPosition", back_populates="follow_order", cascade="all, delete-orphan")
    trades = relationship("SignalFollowTrade", back_populates="follow_order", cascade="all, delete-orphan")


class SignalFollowPosition(Base):
    """信号跟单持仓模型"""
    __tablename__ = "signal_follow_positions"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    follow_order_id = Column(BigInteger, ForeignKey("signal_follow_orders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)                     # long/short
    amount = Column(Numeric(20, 8), nullable=False)              # 持仓数量
    entry_price = Column(Numeric(20, 8), nullable=False)         # 开仓价格
    current_price = Column(Numeric(20, 8))                       # 当前价格
    pnl = Column(Numeric(20, 8), default=0)                      # 盈亏金额（USDT）
    pnl_percent = Column(Numeric(10, 6), default=0)              # 盈亏率
    status = Column(String(16), default="open")                  # open/closed
    open_time = Column(DateTime, default=datetime.utcnow)
    close_time = Column(DateTime)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

    # 关系
    follow_order = relationship("SignalFollowOrder", back_populates="positions")


class SignalFollowTrade(Base):
    """信号跟单交易记录模型"""
    __tablename__ = "signal_follow_trades"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    follow_order_id = Column(BigInteger, ForeignKey("signal_follow_orders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False)
    position_id = Column(BigInteger, ForeignKey("signal_follow_positions.id"))
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)                     # buy/sell
    price = Column(Numeric(20, 8), nullable=False)               # 成交价格
    amount = Column(Numeric(20, 8), nullable=False)              # 成交数量
    total = Column(Numeric(20, 8), nullable=False)               # 成交额（USDT）
    pnl = Column(Numeric(20, 8))                                 # 盈亏金额（已平仓时有值）
    fee = Column(Numeric(20, 8), default=0)                      # 手续费
    signal_record_id = Column(BigInteger, ForeignKey("signal_records.id"))
    trade_time = Column(DateTime, default=datetime.utcnow)
    create_time = Column(DateTime, default=datetime.utcnow)

    # 关系
    follow_order = relationship("SignalFollowOrder", back_populates="trades")
