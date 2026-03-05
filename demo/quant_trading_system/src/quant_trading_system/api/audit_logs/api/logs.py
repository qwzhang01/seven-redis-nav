"""
日志审计路由模块（Admin 端）
============================

提供系统日志、交易日志、风控日志和审计日志的查询接口。

M 端接口（管理员）：
- GET /system          : 系统操作日志
- GET /trading         : 交易日志
- GET /risk            : 风控日志
- GET /audit           : 审计日志（全量）
- GET /risk/alerts     : 风控告警列表
- PUT /risk/alerts/{id}/resolve : 标记告警已处理
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, func

from quant_trading_system.models.audit import AuditLog, RiskAlert
from quant_trading_system.core.database import get_db

router = APIRouter()


def _audit_to_dict(log: AuditLog) -> dict:
    """将 AuditLog ORM 对象转换为字典"""
    return {
        "id": log.id,
        "log_time": log.log_time.isoformat() if log.log_time else None,
        "log_level": log.log_level,
        "log_category": log.log_category,
        "user_id": str(log.user_id) if log.user_id else None,
        "username": log.username,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "request_ip": log.request_ip,
        "request_path": log.request_path,
        "request_method": log.request_method,
        "response_status": log.response_status,
        "duration_ms": log.duration_ms,
        "message": log.message,
        "extra_data": log.extra_data,
    }


def _alert_to_dict(alert: RiskAlert) -> dict:
    """将 RiskAlert ORM 对象转换为字典"""
    return {
        "id": alert.id,
        "alert_time": alert.alert_time.isoformat() if alert.alert_time else None,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "strategy_id": alert.strategy_id,
        "symbol": alert.symbol,
        "user_id": str(alert.user_id) if alert.user_id else None,
        "title": alert.title,
        "message": alert.message,
        "trigger_value": float(alert.trigger_value) if alert.trigger_value is not None else None,
        "threshold_value": float(alert.threshold_value) if alert.threshold_value is not None else None,
        "is_resolved": alert.is_resolved,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolved_by": alert.resolved_by,
        "extra_data": alert.extra_data,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


async def _query_audit_logs(
    db: AsyncSession,
    category: Optional[str],
    level: Optional[str],
    username: Optional[str],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    page: int,
    page_size: int,
) -> tuple[list, int]:
    """通用审计日志查询"""
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    if category:
        stmt = stmt.where(AuditLog.log_category == category)
        count_stmt = count_stmt.where(AuditLog.log_category == category)
    if level:
        stmt = stmt.where(AuditLog.log_level == level.upper())
        count_stmt = count_stmt.where(AuditLog.log_level == level.upper())
    if username:
        stmt = stmt.where(AuditLog.username == username)
        count_stmt = count_stmt.where(AuditLog.username == username)
    if start_time:
        stmt = stmt.where(AuditLog.log_time >= start_time)
        count_stmt = count_stmt.where(AuditLog.log_time >= start_time)
    if end_time:
        stmt = stmt.where(AuditLog.log_time <= end_time)
        count_stmt = count_stmt.where(AuditLog.log_time <= end_time)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(
        stmt.order_by(desc(AuditLog.log_time)).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()
    return items, total


@router.get("/system")
async def get_system_logs(
    level: Optional[str] = Query(None, description="日志级别: DEBUG/INFO/WARNING/ERROR/CRITICAL"),
    username: Optional[str] = Query(None, description="用户名过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    系统操作日志

    查询系统级别的操作日志记录。

    参数：
    - level     : 日志级别过滤
    - username  : 用户名过滤
    - start_time: 开始时间
    - end_time  : 结束时间
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 日志列表
    - total : 总数量
    """
    items, total = await _query_audit_logs(
        db, category="system", level=level, username=username,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return {
        "items": [_audit_to_dict(log) for log in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/trading")
async def get_trading_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    username: Optional[str] = Query(None, description="用户名过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    交易日志

    查询交易相关的操作日志记录。

    参数：
    - level     : 日志级别过滤
    - username  : 用户名过滤
    - start_time: 开始时间
    - end_time  : 结束时间
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 日志列表
    - total : 总数量
    """
    items, total = await _query_audit_logs(
        db, category="trading", level=level, username=username,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return {
        "items": [_audit_to_dict(log) for log in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/risk")
async def get_risk_logs(
    level: Optional[str] = Query(None, description="日志级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    风控日志

    查询风控相关的操作日志记录。

    参数：
    - level     : 日志级别过滤
    - start_time: 开始时间
    - end_time  : 结束时间
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 日志列表
    - total : 总数量
    """
    items, total = await _query_audit_logs(
        db, category="risk", level=level, username=None,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return {
        "items": [_audit_to_dict(log) for log in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/audit")
async def get_audit_logs(
    category: Optional[str] = Query(None, description="日志分类: system/trading/strategy/user/risk/market"),
    level: Optional[str] = Query(None, description="日志级别"),
    username: Optional[str] = Query(None, description="用户名过滤"),
    action: Optional[str] = Query(None, description="操作关键词"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    审计日志（全量）

    查询所有类别的审计日志，支持多维度过滤。

    参数：
    - category  : 日志分类过滤
    - level     : 日志级别过滤
    - username  : 用户名过滤
    - action    : 操作关键词过滤
    - start_time: 开始时间
    - end_time  : 结束时间
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 日志列表
    - total : 总数量
    """
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    if category:
        stmt = stmt.where(AuditLog.log_category == category)
        count_stmt = count_stmt.where(AuditLog.log_category == category)
    if level:
        stmt = stmt.where(AuditLog.log_level == level.upper())
        count_stmt = count_stmt.where(AuditLog.log_level == level.upper())
    if username:
        stmt = stmt.where(AuditLog.username == username)
        count_stmt = count_stmt.where(AuditLog.username == username)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
        count_stmt = count_stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if start_time:
        stmt = stmt.where(AuditLog.log_time >= start_time)
        count_stmt = count_stmt.where(AuditLog.log_time >= start_time)
    if end_time:
        stmt = stmt.where(AuditLog.log_time <= end_time)
        count_stmt = count_stmt.where(AuditLog.log_time <= end_time)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(
        stmt.order_by(desc(AuditLog.log_time)).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [_audit_to_dict(log) for log in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


# ─────────────────────────────────────────────
# 风控告警接口
# ─────────────────────────────────────────────

@router.get("/risk/alerts")
async def get_risk_alerts(
    severity: Optional[str] = Query(None, description="严重程度: info/warning/critical"),
    alert_type: Optional[str] = Query(None, description="告警类型: drawdown/position_limit/loss_limit/volatility"),
    is_resolved: Optional[bool] = Query(None, description="是否已处理"),
    strategy_id: Optional[str] = Query(None, description="策略ID过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    风控告警列表

    查询风控告警记录，支持按严重程度、类型、处理状态过滤。

    参数：
    - severity  : 严重程度过滤（info/warning/critical）
    - alert_type: 告警类型过滤
    - is_resolved: 是否已处理过滤
    - strategy_id: 策略ID过滤
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 告警列表
    - total : 总数量
    """
    stmt = select(RiskAlert)
    count_stmt = select(func.count()).select_from(RiskAlert)

    if severity:
        stmt = stmt.where(RiskAlert.severity == severity.lower())
        count_stmt = count_stmt.where(RiskAlert.severity == severity.lower())
    if alert_type:
        stmt = stmt.where(RiskAlert.alert_type == alert_type.lower())
        count_stmt = count_stmt.where(RiskAlert.alert_type == alert_type.lower())
    if is_resolved is not None:
        stmt = stmt.where(RiskAlert.is_resolved == is_resolved)
        count_stmt = count_stmt.where(RiskAlert.is_resolved == is_resolved)
    if strategy_id:
        stmt = stmt.where(RiskAlert.strategy_id == strategy_id)
        count_stmt = count_stmt.where(RiskAlert.strategy_id == strategy_id)

    total = (await db.execute(count_stmt)).scalar() or 0
    result = await db.execute(
        stmt.order_by(desc(RiskAlert.alert_time)).offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()

    return {
        "items": [_alert_to_dict(a) for a in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


class ResolveAlertRequest(BaseModel):
    """标记告警已处理请求"""
    resolved_by: str = "admin"
    note: Optional[str] = None


@router.put("/risk/alerts/{alert_id}/resolve")
async def resolve_risk_alert(
    alert_id: int,
    request: ResolveAlertRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    标记风控告警已处理

    将指定的风控告警标记为已处理状态。

    参数：
    - alert_id   : 告警ID
    - resolved_by: 处理人
    - note       : 处理备注（可选）

    返回：
    - 更新后的告警信息

    异常：
    - 404: 告警不存在
    - 400: 告警已处理
    """
    result = await db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    if alert.is_resolved:
        raise HTTPException(status_code=400, detail="告警已处理")

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = request.resolved_by
    if request.note:
        alert.extra_data = {**(alert.extra_data or {}), "resolve_note": request.note}
    await db.commit()

    return {
        "success": True,
        "alert": _alert_to_dict(alert),
        "message": "告警已标记为处理",
    }
