"""
信号模块数据库模型
=================

包含信号广场相关的所有 ORM 模型：
- Signal: 信号广场主表
- SignalProvider: 信号提供者
- SignalReview / SignalReviewLike: 用户评价
- SignalRiskParameters: 信号风险参数
- SignalPerformanceMetrics: 信号绩效指标
- SignalNotificationSettings: 信号通知设置
- SignalPosition: 信号当前持仓
- SignalTradeRecord: 信号交易记录
- SignalMonthlyReturn: 信号月度收益
- SignalReturnCurve: 信号收益曲线
- SignalSubscription: 用户订阅信号
"""

from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, \
    BigInteger, \
    Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class Signal(Base):
    """
    信号广场主表模型 — 信号源的核心元数据

    信号来源分为两类：
    - strategy: 交易所跟单信号（由系统策略产生）
    - subscribe: 订阅大佬账户（通过 API 授权监听目标账户仓位变化）
    """
    __tablename__ = "signal"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    name = Column(String(128), nullable=False)
    platform = Column(String(64), nullable=False, default="Binance")
    type = Column(String(16), nullable=False, default="live")  # live / simulated
    signal_source = Column(String(16), nullable=False,
                           default="strategy")  # strategy / subscribe
    status = Column(String(16), nullable=False,
                    default="running")  # running / paused / stopped
    exchange = Column(String(64))
    account_type = Column(String(16), default="spot")  # spot / futures
    trading_pair = Column(String(32))
    timeframe = Column(String(16))
    signal_frequency = Column(String(16))  # high / medium / low
    description = Column(Text)
    provider_id = Column(BigInteger)  # 软关联 -> signal_providers.id
    strategy_id = Column(String(128))

    # ── 订阅大佬账户时的 API 授权信息（signal_source='subscribe' 时必填）──
    target_api_key = Column(String(512))
    target_api_secret = Column(String(512))
    target_passphrase = Column(String(512))
    target_account_name = Column(String(256))
    testnet = Column(Boolean, default=False)

    # ── WebSocket 监听配置 ──
    auto_start_stream = Column(Boolean, default=True)
    watch_symbols = Column(JSONB)
    sync_history = Column(Boolean, default=False)

    # ── 统计字段 ──
    followers_count = Column(Integer, nullable=False, default=0)
    run_days = Column(Integer, nullable=False, default=0)
    cumulative_return = Column(Numeric(12, 4), nullable=False, default=0)
    max_drawdown = Column(Numeric(12, 4), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    provider = relationship("SignalProvider", backref="signals",
                            foreign_keys=[provider_id],
                            primaryjoin="Signal.provider_id == SignalProvider.id")
    risk_parameters = relationship("SignalRiskParameters", uselist=False,
                                   back_populates="signal",
                                   cascade="all, delete-orphan",
                                   foreign_keys="[SignalRiskParameters.signal_id]",
                                   primaryjoin="Signal.id == SignalRiskParameters.signal_id")
    performance_metrics = relationship("SignalPerformanceMetrics", uselist=False,
                                       back_populates="signal",
                                       cascade="all, delete-orphan",
                                       foreign_keys="[SignalPerformanceMetrics.signal_id]",
                                       primaryjoin="Signal.id == SignalPerformanceMetrics.signal_id")
    notification_settings = relationship("SignalNotificationSettings", uselist=False,
                                         back_populates="signal",
                                         cascade="all, delete-orphan",
                                         foreign_keys="[SignalNotificationSettings.signal_id]",
                                         primaryjoin="Signal.id == SignalNotificationSettings.signal_id")
    positions = relationship("SignalPosition", back_populates="signal",
                             cascade="all, delete-orphan",
                             foreign_keys="[SignalPosition.signal_id]",
                             primaryjoin="Signal.id == SignalPosition.signal_id")
    trade_records = relationship("SignalTradeRecord", back_populates="signal",
                                 cascade="all, delete-orphan",
                                 foreign_keys="[SignalTradeRecord.signal_id]",
                                 primaryjoin="Signal.id == SignalTradeRecord.signal_id")


class SignalProvider(Base):
    """信号提供者模型"""
    __tablename__ = "signal_providers"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String(128), nullable=False)
    avatar = Column(String(512))
    verified = Column(Boolean, default=False)
    bio = Column(Text)
    total_signals = Column(Integer, default=0)
    avg_return = Column(Numeric(10, 6), default=0)
    total_followers = Column(Integer, default=0)
    rating = Column(Numeric(3, 2), default=0)
    experience = Column(String(64))
    badges = Column(JSONB, default=[])
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)
    enable_flag = Column(Boolean, default=True)

    # 关系
    user = relationship("User", foreign_keys=[user_id],
                        primaryjoin="SignalProvider.user_id == User.id")


class SignalReview(Base):
    """用户评价模型"""
    __tablename__ = "signal_reviews"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    rating = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    status = Column(String(16), default="active")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", foreign_keys=[user_id],
                        primaryjoin="SignalReview.user_id == User.id")


class SignalReviewLike(Base):
    """评价点赞模型"""
    __tablename__ = "signal_review_likes"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    review_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)


class SignalRiskParameters(Base):
    """信号风险参数模型"""
    __tablename__ = "signal_risk_parameters"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False, unique=True)
    max_position_size = Column(Numeric(8, 2))
    stop_loss_percentage = Column(Numeric(8, 2))
    take_profit_percentage = Column(Numeric(8, 2))
    risk_reward_ratio = Column(Numeric(8, 2))
    volatility_filter = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    signal = relationship("Signal", back_populates="risk_parameters",
                          foreign_keys=[signal_id],
                          primaryjoin="SignalRiskParameters.signal_id == Signal.id")


class SignalPerformanceMetrics(Base):
    """信号绩效指标模型"""
    __tablename__ = "signal_performance_metrics"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False, unique=True)
    sharpe_ratio = Column(Numeric(8, 4))
    win_rate = Column(Numeric(8, 4))
    profit_factor = Column(Numeric(8, 4))
    average_holding_period = Column(Numeric(8, 2))
    max_consecutive_losses = Column(Integer)
    total_trades = Column(Integer, default=0)
    win_trades = Column(Integer, default=0)
    loss_trades = Column(Integer, default=0)
    avg_win = Column(Numeric(14, 4))
    avg_loss = Column(Numeric(14, 4))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    signal = relationship("Signal", back_populates="performance_metrics",
                          foreign_keys=[signal_id],
                          primaryjoin="SignalPerformanceMetrics.signal_id == Signal.id")


class SignalNotificationSettings(Base):
    """信号通知设置模型"""
    __tablename__ = "signal_notification_settings"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False, unique=True)
    email_alerts = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    telegram_bot = Column(Boolean, default=False)
    discord_webhook = Column(Boolean, default=False)
    alert_threshold = Column(Numeric(8, 2))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    signal = relationship("Signal", back_populates="notification_settings",
                          foreign_keys=[signal_id],
                          primaryjoin="SignalNotificationSettings.signal_id == Signal.id")


class SignalPosition(Base):
    """信号当前持仓模型"""
    __tablename__ = "signal_position"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False)
    symbol = Column(String(32), nullable=False)
    side = Column(String(8), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    entry_price = Column(Numeric(18, 8), nullable=False)
    current_price = Column(Numeric(18, 8))
    pnl = Column(Numeric(14, 4))
    pnl_percent = Column(Numeric(10, 4))
    status = Column(String(16), nullable=False, default="open")
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    signal = relationship("Signal", back_populates="positions",
                          foreign_keys=[signal_id],
                          primaryjoin="SignalPosition.signal_id == Signal.id")


class SignalTradeRecord(Base):
    """信号交易记录模型"""
    __tablename__ = "signal_trade_record"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    signal_id = Column(BigInteger, nullable=False)
    original_order_id = Column(String(64), nullable=True, index=True)
    order_status = Column(String(24), nullable=True)
    action = Column(String(8), nullable=False)
    symbol = Column(String(32), nullable=False)
    price = Column(Numeric(18, 8), nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    total = Column(Numeric(18, 4))
    strength = Column(String(8))
    pnl = Column(Numeric(14, 4))
    open_trade_id = Column(BigInteger, nullable=True)
    traded_at = Column(DateTime, nullable=False, timezone=True)
    created_at = Column(DateTime, nullable=False, timezone=True, default=datetime.utcnow)

    signal = relationship("Signal", back_populates="trade_records",
                          foreign_keys=[signal_id],
                          primaryjoin="SignalTradeRecord.signal_id == Signal.id")
    open_trade = relationship("SignalTradeRecord", remote_side=[id],
                              foreign_keys=[open_trade_id],
                              primaryjoin="SignalTradeRecord.open_trade_id == SignalTradeRecord.id")


class SignalMonthlyReturn(Base):
    """信号月度收益模型"""
    __tablename__ = "signal_monthly_return"

    signal_id = Column(BigInteger, primary_key=True)
    month = Column(DateTime, primary_key=True)
    return_value = Column(Numeric(12, 4), nullable=False)


class SignalReturnCurve(Base):
    """信号收益曲线模型（时序表）"""
    __tablename__ = "signal_return_curve"

    signal_id = Column(BigInteger, primary_key=True)
    time = Column(DateTime, primary_key=True)
    return_value = Column(Numeric(12, 4), nullable=False)
    drawdown = Column(Numeric(12, 4))


class SignalSubscription(Base):
    """用户订阅信号模型"""
    __tablename__ = "signal_subscriptions"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    user_id = Column(BigInteger, nullable=False)
    strategy_id = Column(String(128), nullable=False)
    notify_type = Column(String(32), default="realtime")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
