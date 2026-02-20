"""
订阅配置管理路由
================

提供行情订阅配置的 CRUD 操作及状态控制接口。

接口列表：
- POST   /admin/subscriptions              创建订阅配置
- GET    /admin/subscriptions              获取订阅列表（支持筛选分页）
- GET    /admin/subscriptions/statistics   获取订阅统计信息
- GET    /admin/subscriptions/{id}         获取订阅详情
- PUT    /admin/subscriptions/{id}         更新订阅配置
- DELETE /admin/subscriptions/{id}         删除订阅
- POST   /admin/subscriptions/{id}/start   启动订阅
- POST   /admin/subscriptions/{id}/pause   暂停订阅
- POST   /admin/subscriptions/{id}/stop    停止订阅
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import Subscription
from quant_trading_system.services.database.database import get_db

router = APIRouter()


# ── Pydantic 请求/响应模型 ────────────────────────────────────────────────────

class SubscriptionConfig(BaseModel):
    """订阅高级配置"""
    auto_restart: bool = True
    max_retries: int = 3
    batch_size: int = 1000
    sync_interval: int = 60


class SubscriptionCreate(BaseModel):
    """创建订阅请求体"""
    name: str
    exchange: str
    market_type: str = "spot"
    data_type: str
    symbols: list[str]
    interval: Optional[str] = None
    config: Optional[SubscriptionConfig] = None


class SubscriptionUpdate(BaseModel):
    """更新订阅请求体（所有字段可选）"""
    name: Optional[str] = None
    symbols: Optional[list[str]] = None
    interval: Optional[str] = None
    config: Optional[SubscriptionConfig] = None


def _to_dict(sub: Subscription) -> dict[str, Any]:
    """将 ORM 对象转换为响应字典"""
    return {
        "id": sub.id,
        "name": sub.name,
        "exchange": sub.exchange,
        "market_type": sub.market_type,
        "data_type": sub.data_type,
        "symbols": sub.symbols,
        "interval": sub.interval,
        "status": sub.status,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        "last_sync_time": sub.last_sync_time.isoformat() if sub.last_sync_time else None,
        "total_records": sub.total_records,
        "error_count": sub.error_count,
        "last_error": sub.last_error,
        "config": sub.config,
    }


# ── 接口实现 ──────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: SubscriptionCreate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    创建订阅配置

    创建新的数据订阅配置并持久化保存，初始状态为 stopped。
    """
    sub = Subscription(
        id=str(uuid.uuid4()),
        name=body.name,
        exchange=body.exchange,
        market_type=body.market_type,
        data_type=body.data_type,
        symbols=body.symbols,
        interval=body.interval,
        status="stopped",
        config=body.config.model_dump() if body.config else {
            "auto_restart": True,
            "max_retries": 3,
            "batch_size": 1000,
            "sync_interval": 60,
        },
        total_records=0,
        error_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"success": True, "message": "订阅创建成功", "data": _to_dict(sub)}


@router.get("/statistics")
async def get_subscription_statistics(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取订阅统计信息

    返回各状态订阅数量、总记录数、错误数以及按交易所/数据类型的分布。
    """
    subs = db.query(Subscription).all()

    total = len(subs)
    running = sum(1 for s in subs if s.status == "running")
    paused = sum(1 for s in subs if s.status == "paused")
    stopped = sum(1 for s in subs if s.status == "stopped")
    total_records = sum(s.total_records or 0 for s in subs)
    total_errors = sum(s.error_count or 0 for s in subs)

    by_exchange: dict[str, int] = {}
    by_data_type: dict[str, int] = {}
    for s in subs:
        by_exchange[s.exchange] = by_exchange.get(s.exchange, 0) + 1
        by_data_type[s.data_type] = by_data_type.get(s.data_type, 0) + 1

    return {
        "success": True,
        "data": {
            "total_subscriptions": total,
            "running_subscriptions": running,
            "paused_subscriptions": paused,
            "stopped_subscriptions": stopped,
            "total_records": total_records,
            "total_errors": total_errors,
            "by_exchange": by_exchange,
            "by_data_type": by_data_type,
        },
    }


@router.get("")
async def list_subscriptions(
    exchange: Optional[str] = Query(None, description="按交易所筛选"),
    data_type: Optional[str] = Query(None, description="按数据类型筛选"),
    sub_status: Optional[str] = Query(None, alias="status", description="按状态筛选：running/paused/stopped"),
    search: Optional[str] = Query(None, description="按名称模糊搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取订阅列表

    支持按交易所、数据类型、状态筛选，以及按名称模糊搜索，结果分页返回。
    """
    query = db.query(Subscription)
    if exchange:
        query = query.filter(Subscription.exchange == exchange)
    if data_type:
        query = query.filter(Subscription.data_type == data_type)
    if sub_status:
        query = query.filter(Subscription.status == sub_status)
    if search:
        query = query.filter(Subscription.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "items": [_to_dict(s) for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取订阅详情

    根据订阅 ID 返回完整的订阅配置信息。
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    return {"success": True, "data": _to_dict(sub)}


@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    body: SubscriptionUpdate,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    更新订阅配置

    支持更新名称、交易对列表、K线周期和高级配置。
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    if body.name is not None:
        sub.name = body.name
    if body.symbols is not None:
        sub.symbols = body.symbols
    if body.interval is not None:
        sub.interval = body.interval
    if body.config is not None:
        # 合并更新配置，保留未传字段的原值
        existing = sub.config or {}
        existing.update(body.config.model_dump(exclude_none=True))
        sub.config = existing

    sub.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sub)
    return {"success": True, "message": "订阅更新成功", "data": _to_dict(sub)}


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    删除订阅

    删除指定订阅配置，同时级联删除关联的同步任务。
    """
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    db.delete(sub)
    db.commit()
    return {"success": True, "message": "订阅已删除"}


# ── 状态控制 ──────────────────────────────────────────────────────────────────

def _change_status(
    subscription_id: str,
    target_status: str,
    allowed_from: list[str],
    message: str,
    db: Session,
) -> dict[str, Any]:
    """通用状态变更辅助函数"""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if sub.status not in allowed_from:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 '{sub.status}' 不允许执行此操作，允许的状态：{allowed_from}",
        )
    sub.status = target_status
    sub.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sub)
    return {
        "success": True,
        "message": message,
        "data": {"id": sub.id, "status": sub.status, "updated_at": sub.updated_at.isoformat()},
    }


@router.post("/{subscription_id}/start")
async def start_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    启动订阅

    将 stopped 或 paused 状态的订阅切换为 running。
    """
    return _change_status(
        subscription_id, "running", ["stopped", "paused"], "订阅已启动", db
    )


@router.post("/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    暂停订阅

    将 running 状态的订阅切换为 paused，保留配置和数据。
    """
    return _change_status(
        subscription_id, "paused", ["running"], "订阅已暂停", db
    )


@router.post("/{subscription_id}/stop")
async def stop_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    停止订阅

    将 running 或 paused 状态的订阅切换为 stopped。
    """
    return _change_status(
        subscription_id, "stopped", ["running", "paused"], "订阅已停止", db
    )
