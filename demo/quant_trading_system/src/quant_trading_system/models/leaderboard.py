"""
排行榜模块数据库模型
"""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, BigInteger, Numeric

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class LeaderboardSnapshot(Base):
    """排行榜快照模型"""
    __tablename__ = "leaderboard_snapshots"

    id = Column(BigInteger, primary_key=True, default=generate_snowflake_id)
    rank_type = Column(String(32), nullable=False)
    period = Column(String(16), nullable=False)
    rank_position = Column(Integer, nullable=False)
    entity_id = Column(String(128), nullable=False)
    entity_name = Column(String(256))
    entity_type = Column(String(64))
    owner_id = Column(BigInteger)
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
