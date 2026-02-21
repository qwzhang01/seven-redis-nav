"""
信号管理路由模块
===============

提供策略信号的查询、订阅和管理功能。

C 端接口（普通用户）：
- GET  /list              : 获取公开信号列表（信号广场）
- GET  /{signal_id}       : 获取信号详情
- GET  /strategy/{id}/history : 获取策略历史信号
- POST /subscribe         : 订阅信号通知
- GET  /subscriptions     : 获取我的订阅列表
- DELETE /subscriptions/{id}: 取消订阅

M 端接口（管理员）：
- GET  /pending           : 获取待审核信号
- PUT  /{signal_id}/approve: 审核信号（设置是否公开）
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt

from quant_trading_system.models.database import SignalRecord, SignalSubscription, User
from quant_trading_system.services.database.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
security = HTTPBearer(auto_error=False)

# JWT 配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"


def _require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从 JWT Token 中获取当前用户（必须认证）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
        user = db.query(User).filter(User.username == username, User.enable_flag == True).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")


def _signal_to_dict(s: SignalRecord) -> dict:
    """将 SignalRecord ORM 对象转换为字典"""
    return {
        "id": str(s.id),
        "strategy_id": s.strategy_id,
        "strategy_name": s.strategy_name,
        "symbol": s.symbol,
        "exchange": s.exchange,
        "signal_type": s.signal_type,
        "price": float(s.price) if s.price is not None else None,
        "quantity": float(s.quantity) if s.quantity is not None else None,
        "confidence": float(s.confidence) if s.confidence is not None else None,
        "timeframe": s.timeframe,
        "reason": s.reason,
        "indicators": s.indicators,
        "status": s.status,
        "executed_order_id": s.executed_order_id,
        "executed_price": float(s.executed_price) if s.executed_price is not None else None,
        "executed_at": s.executed_at.isoformat() if s.executed_at else None,
        "is_public": s.is_public,
        "subscriber_count": s.subscriber_count,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


# ─────────────────────────────────────────────
# C 端接口
# ─────────────────────────────────────────────

@router.get("/list")
async def list_public_signals(
    symbol: Optional[str] = Query(None, description="交易对过滤"),
    signal_type: Optional[str] = Query(None, description="信号类型: buy/sell/close"),
    strategy_id: Optional[str] = Query(None, description="策略ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取公开信号列表（信号广场）

    查询所有公开展示的策略信号，支持按交易对、信号类型、策略过滤。

    参数：
    - symbol     : 交易对过滤（可选）
    - signal_type: 信号类型过滤（buy/sell/close）
    - strategy_id: 策略ID过滤（可选）
    - page       : 页码（默认1）
    - page_size  : 每页数量（默认20，最大100）

    返回：
    - items : 信号列表
    - total : 总数量
    - page  : 当前页码
    - pages : 总页数
    """
    query = db.query(SignalRecord).filter(SignalRecord.is_public == True)
    if symbol:
        query = query.filter(SignalRecord.symbol == symbol.upper())
    if signal_type:
        query = query.filter(SignalRecord.signal_type == signal_type.lower())
    if strategy_id:
        query = query.filter(SignalRecord.strategy_id == strategy_id)

    total = query.count()
    items = query.order_by(SignalRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_signal_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/subscriptions")
async def get_my_subscriptions(
    current_user: User = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取我的信号订阅列表

    查询当前用户订阅的所有策略信号。

    返回：
    - items : 订阅列表
    - total : 总数量
    """
    subs = db.query(SignalSubscription).filter(
        SignalSubscription.user_id == current_user.id,
        SignalSubscription.is_active == True,
    ).all()

    items = [
        {
            "id": str(s.id),
            "strategy_id": s.strategy_id,
            "notify_type": s.notify_type,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subs
    ]
    return {"items": items, "total": len(items)}


@router.get("/strategy/{strategy_id}/history")
async def get_strategy_signal_history(
    strategy_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略历史信号

    查询指定策略产生的所有历史信号记录。

    参数：
    - strategy_id: 策略ID
    - page       : 页码
    - page_size  : 每页数量

    返回：
    - items : 信号列表
    - total : 总数量
    """
    query = db.query(SignalRecord).filter(SignalRecord.strategy_id == strategy_id)
    total = query.count()
    items = query.order_by(SignalRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "strategy_id": strategy_id,
        "items": [_signal_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/{signal_id}")
async def get_signal_detail(
    signal_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号详情

    根据信号ID查询详细信息。

    参数：
    - signal_id: 信号ID

    返回：
    - 信号详细信息

    异常：
    - 404: 信号不存在
    """
    signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="信号不存在")
    return _signal_to_dict(signal)


class SubscribeSignalRequest(BaseModel):
    """订阅信号请求"""
    strategy_id: str
    notify_type: str = "realtime"  # realtime/daily/weekly


@router.post("/subscribe")
async def subscribe_signal(
    request: SubscribeSignalRequest,
    current_user: User = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    订阅策略信号通知

    订阅指定策略的信号推送，支持实时/每日/每周通知。

    参数：
    - strategy_id: 要订阅的策略ID
    - notify_type: 通知方式（realtime/daily/weekly）

    返回：
    - 订阅信息
    """
    # 检查是否已订阅
    existing = db.query(SignalSubscription).filter(
        SignalSubscription.user_id == current_user.id,
        SignalSubscription.strategy_id == request.strategy_id,
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.notify_type = request.notify_type
            existing.updated_at = datetime.utcnow()
            db.commit()
        return {
            "id": str(existing.id),
            "strategy_id": existing.strategy_id,
            "notify_type": existing.notify_type,
            "is_active": existing.is_active,
            "message": "已更新订阅",
        }

    sub = SignalSubscription(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        strategy_id=request.strategy_id,
        notify_type=request.notify_type,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(sub)

    # 更新信号记录中的订阅人数
    db.query(SignalRecord).filter(
        SignalRecord.strategy_id == request.strategy_id
    ).update({"subscriber_count": SignalRecord.subscriber_count + 1})

    db.commit()
    db.refresh(sub)

    return {
        "id": str(sub.id),
        "strategy_id": sub.strategy_id,
        "notify_type": sub.notify_type,
        "is_active": sub.is_active,
        "message": "订阅成功",
    }


@router.delete("/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(_require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    取消信号订阅

    取消对指定策略信号的订阅。

    参数：
    - subscription_id: 订阅ID

    返回：
    - 操作结果

    异常：
    - 404: 订阅不存在
    - 403: 无权操作
    """
    sub = db.query(SignalSubscription).filter(SignalSubscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    if str(sub.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权操作此订阅")

    sub.is_active = False
    sub.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "已取消订阅"}
