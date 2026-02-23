"""
历史数据同步路由模块
====================

提供独立的历史数据同步任务管理接口，不依赖现有订阅配置。

接口列表：
- POST /admin/historical-sync             创建历史数据同步任务
- GET  /admin/historical-sync              获取历史同步任务列表
- GET  /admin/historical-sync/{id}         获取任务详情
- POST /admin/historical-sync/{id}/cancel  取消同步任务
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from quant_trading_system.models.database import HistoricalSyncTask, User
from quant_trading_system.services.database.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id

router = APIRouter()

# 合法枚举值
VALID_EXCHANGES = {"Binance", "OKX", "Bybit", "Bitget", "binance", "okx", "bybit", "bitget"}
VALID_DATA_TYPES = {"kline", "ticker", "depth", "trade", "orderbook"}
VALID_INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d"}


def _require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """校验当前请求用户是否为管理员"""
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

class HistoricalSyncCreate(BaseModel):
    """创建历史数据同步任务请求体"""
    name: str
    exchange: str
    data_type: str
    symbols: list[str]
    interval: Optional[str] = None
    start_time: datetime
    end_time: datetime
    batch_size: int = 1000

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        if v not in VALID_EXCHANGES:
            raise ValueError(f"不支持的交易所 '{v}'，合法值：{sorted(VALID_EXCHANGES)}")
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str) -> str:
        if v not in VALID_DATA_TYPES:
            raise ValueError(f"不支持的数据类型 '{v}'，合法值：{sorted(VALID_DATA_TYPES)}")
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_INTERVALS:
            raise ValueError(f"不支持的K线周期 '{v}'，合法值：{sorted(VALID_INTERVALS)}")
        return v

    @field_validator("symbols")
    @classmethod
    def validate_symbols(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("交易对列表不能为空")
        return v

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        if v < 1 or v > 5000:
            raise ValueError("批次大小必须在1-5000之间")
        return v

    def model_post_init(self, __context: Any) -> None:
        """跨字段校验：kline 类型必须提供 interval"""
        if self.data_type == "kline" and not self.interval:
            raise ValueError("data_type 为 kline 时，interval 为必填项")
        if self.end_time <= self.start_time:
            raise ValueError("结束时间必须晚于开始时间")


def _to_dict(task: HistoricalSyncTask) -> dict[str, Any]:
    """将 ORM 对象转换为响应字典"""
    return {
        "id": task.id,
        "name": task.name,
        "exchange": task.exchange,
        "data_type": task.data_type,
        "symbols": task.symbols,
        "interval": task.interval,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "batch_size": task.batch_size,
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
async def create_historical_sync(
    body: HistoricalSyncCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    创建历史数据同步任务

    创建独立的历史数据同步任务，不依赖现有订阅配置。
    """
    task = HistoricalSyncTask(
        id=str(generate_snowflake_id()),
        name=body.name,
        exchange=body.exchange,
        data_type=body.data_type,
        symbols=body.symbols,
        interval=body.interval,
        start_time=body.start_time,
        end_time=body.end_time,
        batch_size=body.batch_size,
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
    return {"success": True, "message": "历史数据同步任务已创建", "data": _to_dict(task)}


@router.get("")
async def list_historical_sync_tasks(
    exchange: Optional[str] = Query(None, description="按交易所筛选"),
    data_type: Optional[str] = Query(None, description="按数据类型筛选"),
    task_status: Optional[str] = Query(None, alias="status", description="按状态筛选：pending/running/completed/failed/cancelled"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取历史数据同步任务列表

    支持按交易所、数据类型、状态筛选，结果按创建时间倒序分页返回。
    """
    query = db.query(HistoricalSyncTask)
    if exchange:
        query = query.filter(HistoricalSyncTask.exchange == exchange)
    if data_type:
        query = query.filter(HistoricalSyncTask.data_type == data_type)
    if task_status:
        query = query.filter(HistoricalSyncTask.status == task_status)

    query = query.order_by(HistoricalSyncTask.created_at.desc())
    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "data": {
            "items": [_to_dict(t) for t in tasks],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/{task_id}")
async def get_historical_sync_task(
    task_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取历史数据同步任务详情

    根据任务 ID 返回完整的历史数据同步任务信息。
    """
    task = db.query(HistoricalSyncTask).filter(HistoricalSyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="历史数据同步任务不存在")
    return {"success": True, "data": _to_dict(task)}


@router.post("/{task_id}/cancel")
async def cancel_historical_sync_task(
    task_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    取消历史数据同步任务

    取消处于 pending 或 running 状态的历史数据同步任务。
    """
    task = db.query(HistoricalSyncTask).filter(HistoricalSyncTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="历史数据同步任务不存在")

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
        "message": "历史数据同步任务已取消",
        "data": {"id": task.id, "status": task.status, "updated_at": task.updated_at.isoformat()},
    }


@router.get("/status/executor")
async def get_historical_sync_executor_status(
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    获取历史数据同步执行器状态

    返回执行器的运行状态、活跃任务数量等信息。
    """
    try:
        from quant_trading_system.services.market.historical_sync_executor import \
            get_historical_sync_executor

        executor = get_historical_sync_executor()
        stats = executor.stats

        return {
            "success": True,
            "data": {
                "executor_running": executor.is_running,
                "active_tasks": stats["active_tasks"],
                "task_ids": stats["task_ids"],
                "max_concurrent_tasks": executor.max_concurrent_tasks,
                "check_interval": executor.check_interval,
                "max_retries": executor.max_retries
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取执行器状态失败: {str(e)}"
        }


@router.post("/executor/start")
async def start_historical_sync_executor(
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    启动历史数据同步执行器

    手动启动历史数据同步任务执行器。
    """
    try:
        from quant_trading_system.services.market.historical_sync_executor import \
            get_historical_sync_executor

        executor = get_historical_sync_executor()
        if executor.is_running:
            return {
                "success": True,
                "message": "历史数据同步执行器已在运行中"
            }

        await executor.start()
        return {
            "success": True,
            "message": "历史数据同步执行器已启动"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"启动执行器失败: {str(e)}"
        }


@router.post("/executor/stop")
async def stop_historical_sync_executor(
    _admin: User = Depends(_require_admin),
) -> dict[str, Any]:
    """
    停止历史数据同步执行器

    手动停止历史数据同步任务执行器。
    """
    try:
        from quant_trading_system.services.market.historical_sync_executor import \
            get_historical_sync_executor

        executor = get_historical_sync_executor()
        if not executor.is_running:
            return {
                "success": True,
                "message": "历史数据同步执行器已停止"
            }

        await executor.stop()
        return {
            "success": True,
            "message": "历史数据同步执行器已停止"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"停止执行器失败: {str(e)}"
        }
