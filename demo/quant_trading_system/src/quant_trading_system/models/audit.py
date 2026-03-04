"""
审计与风控模块数据库模型
=======================

- AuditLog: 审计日志
- RiskAlert: 风控告警
"""

from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, \
    BigInteger, \
    Numeric
from sqlalchemy.dialects.postgresql import JSONB

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.base import Base


class AuditLog(Base):
    """审计日志模型（时序表，联合主键）"""
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, primary_key=True, default=datetime.utcnow,
                      nullable=False)
    log_level = Column(String(16), nullable=False, default="INFO")
    log_category = Column(String(32), nullable=False)
    user_id = Column(BigInteger)
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
    alert_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default="warning")
    strategy_id = Column(String(128))
    symbol = Column(String(32))
    user_id = Column(BigInteger)
    title = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    trigger_value = Column(Numeric(20, 8))
    threshold_value = Column(Numeric(20, 8))
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(64))
    extra_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
