"""
手动同步任务管理路由
====================

提供手动同步任务的创建、查询和取消接口。

接口列表：
- POST  /admin/sync-tasks              创建同步任务
- GET   /admin/sync-tasks              获取同步任务列表（支持筛选分页）
- GET   /admin/sync-tasks/{id}         获取同步任务详情
- POST  /admin/sync-tasks/{id}/cancel  取消同步任务
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import Subscription, SyncTask, User
from quant_trading_system.services.database.database import get_db

router = APIRouter()


def _require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    校验当前请求用户是否为管理员。
    AuthMiddleware 已将 username 写入 request.state.username。
    """
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    user = db.query(User).filter(User.username == username, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.user_type != "admin":
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可操作")
    return user


# ── Pydantic 请求/响应模型 ────────────────────────────────────────────────────

class SyncTaskCreate(BaseModel):
    """创建同步任务请求体"""
    subscription_id: str
    start_time: datetime
    end_time: datetime


def _to_dict(task: SyncTask, sub: Optional[Subscription] = None) -> dict[str, Any]:
    """将 ORM 对象转换为响应字典"""
    return {
        "id": task.id,
        "subscription_id": task.subscription_id,
        "subscription_name": sub.name if sub else None,
        "exchange": sub.exchange if sub else None,
        "symbols": sub.symbols if sub else None,
        "data_type": sub.data_type if sub else None,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "status": task.status,
        "progress": task.progress,
        "total_records": task.total_records,
        "synced_records": task.synced_records,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


# ── 接口实现 ──────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sync_task(
    body: SyncTaskCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    创建同步任务

    为指定订阅创建一个手动历史数据同步任务，任务初始状态为 pending。
    """
    sub = db.query(Subscription).filter(Subscription.id == body.subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    if body.end_time <= body.start_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

    task = SyncTask(
        id=str(uuid.uuid4()),
        subscription_id=body.subscription_id,
        start_time=body.start_time,
        end_time=body.end_time,
        status="pending",
        progress=0,
        total_records=0,
        synced_records=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "message": "同步任务已创建", "data": _to_dict(task, sub)}


@router.get("")
async def list_sync_tasks(
    subscription_id: Optional[str] = Query(None, description="按订阅ID筛选"),
    task_status: Optional[str] = Query(None, alias="status", description="按状态筛选：pending/running/completed/failed/cancelled"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取同步任务列表

    支持按订阅 ID 和状态筛选，结果按创建时间倒序分页返回。
    """
    query = db.query(SyncTask)
    if subscription_id:
        query = query.filter(SyncTask.subscription_id == subscription_id)
    if task_status:
        query = query.filter(SyncTask.status == task_status)

    query = query.order_by(SyncTask.created_at.desc())
    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    # 批量查询关联订阅
    sub_ids = list({t.subscription_id for t in tasks})
    subs = {s.id: s for s in db.query(Subscription).filter(Subscription.id.in_(sub_ids)).all()}

    return {
        "success": True,
        "data": {
            "items": [_to_dict(t, subs.get(t.subscription_id)) for t in tasks],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{task_id}")
async def get_sync_task(
    task_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取同步任务详情

    根据任务 ID 返回完整的同步任务信息。
    """
    task = db.query(SyncTask).filter(SyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="同步任务不存在")

    sub = db.query(Subscription).filter(Subscription.id == task.subscription_id).first()
    return {"success": True, "data": _to_dict(task, sub)}


@router.post("/{task_id}/cancel")
async def cancel_sync_task(
    task_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    取消同步任务

    取消处于 pending 或 running 状态的同步任务。
    """
    task = db.query(SyncTask).filter(SyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="同步任务不存在")

    if task.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 '{task.status}' 不允许取消，只有 pending/running 状态可取消",
        )

    task.status = "cancelled"
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {
        "success": True,
        "message": "同步任务已取消",
        "data": {"id": task.id, "status": task.status, "updated_at": task.updated_at.isoformat()},
    }
