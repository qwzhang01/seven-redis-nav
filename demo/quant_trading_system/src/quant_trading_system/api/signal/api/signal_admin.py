"""
信号交易记录管理 Admin 端路由
====================

提供管理员对信号交易记录的查询和管理功能。

M 端接口（管理员）：
- GET  /records            : 获取信号交易记录列表
- GET  /{record_id}        : 获取单条交易记录详情
- POST /                   : 手动创建交易记录
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import SignalTradeRecord
from quant_trading_system.services.database.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id

router = APIRouter()


def _trade_record_to_dict(r: SignalTradeRecord) -> dict:
    """将 SignalTradeRecord ORM 对象转换为字典"""
    return {
        "id": str(r.id),
        "signal_id": str(r.signal_id),
        "action": r.action,
        "symbol": r.symbol,
        "price": float(r.price) if r.price is not None else None,
        "amount": float(r.amount) if r.amount is not None else None,
        "total": float(r.total) if r.total is not None else None,
        "strength": r.strength,
        "pnl": float(r.pnl) if r.pnl is not None else None,
        "traded_at": r.traded_at.isoformat() if r.traded_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/records")
async def list_trade_records(
    signal_id: Optional[int] = Query(None, description="按信号ID筛选"),
    symbol: Optional[str] = Query(None, description="按交易对筛选"),
    action: Optional[str] = Query(None, description="按操作类型筛选(buy/sell)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号交易记录列表（管理员）

    支持按信号ID、交易对、操作类型筛选。

    参数：
    - signal_id : 信号ID（可选）
    - symbol    : 交易对（可选）
    - action    : 操作类型 buy/sell（可选）
    - page      : 页码
    - page_size : 每页数量

    返回：
    - items : 交易记录列表
    - total : 总数量
    """
    query = db.query(SignalTradeRecord)
    if signal_id is not None:
        query = query.filter(SignalTradeRecord.signal_id == signal_id)
    if symbol:
        query = query.filter(SignalTradeRecord.symbol == symbol.upper())
    if action:
        query = query.filter(SignalTradeRecord.action == action.lower())

    total = query.count()
    items = query.order_by(SignalTradeRecord.traded_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_trade_record_to_dict(r) for r in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{record_id}")
async def get_trade_record(
    record_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取单条交易记录详情（管理员）

    参数：
    - record_id: 交易记录ID

    返回：
    - 交易记录详情

    异常：
    - 404: 记录不存在
    """
    record = db.query(SignalTradeRecord).filter(SignalTradeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    return {
        "success": True,
        "record": _trade_record_to_dict(record),
    }


class CreateTradeRecordRequest(BaseModel):
    """手动创建交易记录请求"""
    signal_id: int
    action: str           # buy / sell
    symbol: str
    price: float
    amount: float
    total: Optional[float] = None
    strength: Optional[str] = None   # strong / medium / weak
    pnl: Optional[float] = None
    traded_at: Optional[datetime] = None


@router.post("/")
async def create_trade_record(
    request: CreateTradeRecordRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    手动创建交易记录（管理员）

    手动向系统写入一条信号交易记录，用于测试或手动操作。

    参数：
    - 交易记录详细信息

    返回：
    - 创建的交易记录信息
    """
    record = SignalTradeRecord(
        id=generate_snowflake_id(),
        signal_id=request.signal_id,
        action=request.action.lower(),
        symbol=request.symbol.upper(),
        price=Decimal(str(request.price)),
        amount=Decimal(str(request.amount)),
        total=Decimal(str(request.total)) if request.total is not None else None,
        strength=request.strength,
        pnl=Decimal(str(request.pnl)) if request.pnl is not None else None,
        traded_at=request.traded_at or datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "record": _trade_record_to_dict(record),
        "message": "交易记录创建成功",
    }
