"""
信号管理 Admin 端路由
====================

提供管理员对信号的审核和管理功能。

M 端接口（管理员）：
- GET  /pending           : 获取待审核信号列表
- PUT  /{signal_id}/approve: 审核信号（设置是否公开）
- POST /                  : 手动创建信号记录
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import SignalRecord
from quant_trading_system.services.database.database import get_db
from .signal import _signal_to_dict

router = APIRouter()


@router.get("/pending")
async def list_pending_signals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取待审核信号列表（管理员）

    查询所有尚未设置公开状态的信号记录，供管理员审核。

    参数：
    - page     : 页码
    - page_size: 每页数量

    返回：
    - items : 信号列表
    - total : 总数量
    """
    query = db.query(SignalRecord).filter(SignalRecord.is_public == False)
    total = query.count()
    items = query.order_by(SignalRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_signal_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


class ApproveSignalRequest(BaseModel):
    """审核信号请求"""
    is_public: bool
    reason: Optional[str] = None


@router.put("/{signal_id}/approve")
async def approve_signal(
    signal_id: str,
    request: ApproveSignalRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    审核信号（管理员）

    设置信号是否在信号广场公开展示。

    参数：
    - signal_id: 信号ID
    - is_public: 是否公开
    - reason   : 审核原因（可选）

    返回：
    - 更新后的信号信息

    异常：
    - 404: 信号不存在
    """
    signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="信号不存在")

    signal.is_public = request.is_public
    if request.reason:
        signal.reason = request.reason
    signal.updated_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "signal": _signal_to_dict(signal),
        "message": "审核完成",
    }


class CreateSignalRequest(BaseModel):
    """手动创建信号请求"""
    strategy_id: str
    strategy_name: Optional[str] = None
    symbol: str
    exchange: str = "binance"
    signal_type: str  # buy/sell/close
    price: float
    quantity: Optional[float] = None
    confidence: Optional[float] = None
    timeframe: Optional[str] = None
    reason: Optional[str] = None
    indicators: Optional[dict] = None
    is_public: bool = False


@router.post("/")
async def create_signal(
    request: CreateSignalRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    手动创建信号记录（管理员）

    手动向系统写入一条信号记录，用于测试或手动操作。

    参数：
    - 信号详细信息

    返回：
    - 创建的信号信息
    """
    signal = SignalRecord(
        id=str(uuid.uuid4()),
        strategy_id=request.strategy_id,
        strategy_name=request.strategy_name,
        symbol=request.symbol.upper(),
        exchange=request.exchange,
        signal_type=request.signal_type.lower(),
        price=request.price,
        quantity=request.quantity,
        confidence=request.confidence,
        timeframe=request.timeframe,
        reason=request.reason,
        indicators=request.indicators,
        status="pending",
        is_public=request.is_public,
        subscriber_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    return {
        "success": True,
        "signal": _signal_to_dict(signal),
        "message": "信号创建成功",
    }
