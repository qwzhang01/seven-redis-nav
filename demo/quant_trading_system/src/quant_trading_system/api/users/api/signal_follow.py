"""
信号跟单管理 API
================

提供用户信号跟单的完整管理功能：

C 端接口（普通用户）：
- GET  /                        : 获取我的跟单列表
- POST /                        : 创建跟单
- GET  /{follow_id}             : 获取跟单详情
- PUT  /{follow_id}/config      : 更新跟单配置
- POST /{follow_id}/stop        : 停止跟单
- GET  /{follow_id}/positions   : 获取当前持仓
- GET  /{follow_id}/trades      : 获取交易记录
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.models.database import (
    User,
    SignalFollowOrder,
    SignalFollowPosition,
    SignalFollowTrade,
)
from quant_trading_system.services.database.database import get_db

router = APIRouter()


# ── 权限校验 ──────────────────────────────────────────────────────────────────

def _require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    校验当前请求用户是否已登录。
    AuthMiddleware 已将 username 写入 request.state.username。
    """
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    user = db.query(User).filter(User.username == username, User.enable_flag == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ── 请求/响应模型 ─────────────────────────────────────────────────────────────

class CreateFollowRequest(BaseModel):
    """创建跟单请求体"""
    strategy_id: str
    signal_name: str
    exchange: str = "binance"
    follow_amount: float                    # 跟单资金（USDT）
    follow_ratio: float = 1.0              # 跟单比例（0~1）
    stop_loss: Optional[float] = None      # 止损比例（0~1），可选


class UpdateFollowConfigRequest(BaseModel):
    """更新跟单配置请求体"""
    follow_amount: Optional[float] = None
    follow_ratio: Optional[float] = None
    stop_loss: Optional[float] = None


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _follow_order_to_dict(order: SignalFollowOrder) -> dict[str, Any]:
    """将 SignalFollowOrder ORM 对象转换为响应字典"""
    start_time = order.start_time
    follow_days = 0
    if start_time:
        follow_days = (datetime.utcnow() - start_time).days

    return {
        "id": str(order.id),
        "user_id": str(order.user_id),
        "strategy_id": order.strategy_id,
        "signal_name": order.signal_name,
        "exchange": order.exchange,
        "follow_amount": float(order.follow_amount) if order.follow_amount is not None else None,
        "current_value": float(order.current_value) if order.current_value is not None else None,
        "follow_ratio": float(order.follow_ratio) if order.follow_ratio is not None else None,
        "stop_loss": float(order.stop_loss) if order.stop_loss is not None else None,
        "total_return": float(order.total_return) if order.total_return is not None else None,
        "max_drawdown": float(order.max_drawdown) if order.max_drawdown is not None else None,
        "current_drawdown": float(order.current_drawdown) if order.current_drawdown is not None else None,
        "today_return": float(order.today_return) if order.today_return is not None else None,
        "win_rate": float(order.win_rate) if order.win_rate is not None else None,
        "total_trades": order.total_trades,
        "win_trades": order.win_trades,
        "loss_trades": order.loss_trades,
        "avg_win": float(order.avg_win) if order.avg_win is not None else None,
        "avg_loss": float(order.avg_loss) if order.avg_loss is not None else None,
        "profit_factor": float(order.profit_factor) if order.profit_factor is not None else None,
        "risk_level": order.risk_level,
        "status": order.status,
        "follow_days": follow_days,
        "start_time": order.start_time.isoformat() if order.start_time else None,
        "stop_time": order.stop_time.isoformat() if order.stop_time else None,
        "return_curve": order.return_curve,
        "return_curve_labels": order.return_curve_labels,
        "create_time": order.create_time.isoformat() if order.create_time else None,
        "update_time": order.update_time.isoformat() if order.update_time else None,
    }


def _position_to_dict(pos: SignalFollowPosition) -> dict[str, Any]:
    """将 SignalFollowPosition ORM 对象转换为响应字典"""
    return {
        "id": str(pos.id),
        "follow_order_id": str(pos.follow_order_id),
        "symbol": pos.symbol,
        "side": pos.side,
        "amount": float(pos.amount) if pos.amount is not None else None,
        "entry_price": float(pos.entry_price) if pos.entry_price is not None else None,
        "current_price": float(pos.current_price) if pos.current_price is not None else None,
        "pnl": float(pos.pnl) if pos.pnl is not None else None,
        "pnl_percent": float(pos.pnl_percent) if pos.pnl_percent is not None else None,
        "status": pos.status,
        "open_time": pos.open_time.isoformat() if pos.open_time else None,
        "close_time": pos.close_time.isoformat() if pos.close_time else None,
    }


def _trade_to_dict(trade: SignalFollowTrade) -> dict[str, Any]:
    """将 SignalFollowTrade ORM 对象转换为响应字典"""
    return {
        "id": str(trade.id),
        "follow_order_id": str(trade.follow_order_id),
        "position_id": str(trade.position_id) if trade.position_id else None,
        "symbol": trade.symbol,
        "side": trade.side,
        "price": float(trade.price) if trade.price is not None else None,
        "amount": float(trade.amount) if trade.amount is not None else None,
        "total": float(trade.total) if trade.total is not None else None,
        "pnl": float(trade.pnl) if trade.pnl is not None else None,
        "fee": float(trade.fee) if trade.fee is not None else None,
        "signal_record_id": str(trade.signal_record_id) if trade.signal_record_id else None,
        "trade_time": trade.trade_time.isoformat() if trade.trade_time else None,
    }


# ── 接口实现 ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_my_follows(
    status: Optional[str] = Query(None, description="状态筛选: following/stopped/paused"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    获取我的跟单列表

    查询当前用户的所有跟单记录，支持按状态筛选和分页。

    参数：
    - status   : 状态筛选（following/stopped/paused），不传则返回全部
    - page     : 页码（默认1）
    - page_size: 每页数量（默认20，最大100）

    返回：
    - items: 跟单列表
    - total: 总数量
    - page : 当前页码
    - pages: 总页数
    """
    query = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.user_id == current_user.id,
        SignalFollowOrder.enable_flag == True,
    )
    if status:
        query = query.filter(SignalFollowOrder.status == status)

    total = query.count()
    items = (
        query.order_by(SignalFollowOrder.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "success": True,
        "data": {
            "items": [_follow_order_to_dict(o) for o in items],
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size,
        },
    }


@router.post("")
async def create_follow(
    body: CreateFollowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    创建跟单

    为当前用户创建一条新的信号跟单记录。

    参数：
    - strategy_id  : 要跟单的策略ID
    - signal_name  : 信号/策略名称
    - exchange     : 交易所（默认 binance）
    - follow_amount: 跟单资金（USDT）
    - follow_ratio : 跟单比例（0~1，默认1.0）
    - stop_loss    : 止损比例（0~1，可选）

    返回：
    - 创建的跟单信息

    异常：
    - 400: 参数校验失败（如已存在相同策略的活跃跟单）
    """
    # 校验参数
    if body.follow_amount <= 0:
        raise HTTPException(status_code=400, detail="跟单资金必须大于0")
    if not (0 < body.follow_ratio <= 1):
        raise HTTPException(status_code=400, detail="跟单比例必须在 0~1 之间")
    if body.stop_loss is not None and not (0 < body.stop_loss < 1):
        raise HTTPException(status_code=400, detail="止损比例必须在 0~1 之间")

    # 检查是否已存在相同策略的活跃跟单
    existing = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.user_id == current_user.id,
        SignalFollowOrder.strategy_id == body.strategy_id,
        SignalFollowOrder.status == "following",
        SignalFollowOrder.enable_flag == True,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已存在该策略的活跃跟单，请先停止后再创建")

    now = datetime.utcnow()
    order = SignalFollowOrder(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        strategy_id=body.strategy_id,
        signal_name=body.signal_name,
        exchange=body.exchange,
        follow_amount=body.follow_amount,
        current_value=body.follow_amount,   # 初始净值等于跟单资金
        follow_ratio=body.follow_ratio,
        stop_loss=body.stop_loss,
        total_return=0,
        max_drawdown=0,
        current_drawdown=0,
        today_return=0,
        win_rate=0,
        total_trades=0,
        win_trades=0,
        loss_trades=0,
        avg_win=0,
        avg_loss=0,
        profit_factor=0,
        risk_level="low",
        status="following",
        start_time=now,
        return_curve=[],
        return_curve_labels=[],
        create_by=current_user.username,
        create_time=now,
        update_time=now,
        enable_flag=True,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "data": _follow_order_to_dict(order),
        "message": "跟单创建成功",
    }


@router.get("/{follow_id}")
async def get_follow_detail(
    follow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    获取跟单详情

    根据跟单ID查询完整的跟单详情，包含绩效统计、收益曲线、配置信息等。

    参数：
    - follow_id: 跟单ID

    返回：
    - 跟单详细信息

    异常：
    - 404: 跟单不存在
    - 403: 无权访问
    """
    order = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.id == follow_id,
        SignalFollowOrder.enable_flag == True,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")

    return {"success": True, "data": _follow_order_to_dict(order)}


@router.put("/{follow_id}/config")
async def update_follow_config(
    follow_id: str,
    body: UpdateFollowConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    更新跟单配置

    修改跟单的资金、比例或止损设置。仅允许修改状态为 following 的跟单。

    参数：
    - follow_id   : 跟单ID
    - follow_amount: 跟单资金（USDT，可选）
    - follow_ratio : 跟单比例（0~1，可选）
    - stop_loss   : 止损比例（0~1，可选）

    返回：
    - 更新后的跟单信息

    异常：
    - 404: 跟单不存在
    - 403: 无权操作
    - 400: 跟单已停止，无法修改
    """
    order = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.id == follow_id,
        SignalFollowOrder.enable_flag == True,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权操作此跟单记录")
    if order.status == "stopped":
        raise HTTPException(status_code=400, detail="跟单已停止，无法修改配置")

    if body.follow_amount is not None:
        if body.follow_amount <= 0:
            raise HTTPException(status_code=400, detail="跟单资金必须大于0")
        order.follow_amount = body.follow_amount
    if body.follow_ratio is not None:
        if not (0 < body.follow_ratio <= 1):
            raise HTTPException(status_code=400, detail="跟单比例必须在 0~1 之间")
        order.follow_ratio = body.follow_ratio
    if body.stop_loss is not None:
        if not (0 < body.stop_loss < 1):
            raise HTTPException(status_code=400, detail="止损比例必须在 0~1 之间")
        order.stop_loss = body.stop_loss

    order.update_time = datetime.utcnow()
    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "data": _follow_order_to_dict(order),
        "message": "跟单配置更新成功",
    }


@router.post("/{follow_id}/stop")
async def stop_follow(
    follow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    停止跟单

    将指定跟单的状态设置为 stopped，同时关闭所有未平仓持仓。

    参数：
    - follow_id: 跟单ID

    返回：
    - 操作结果

    异常：
    - 404: 跟单不存在
    - 403: 无权操作
    - 400: 跟单已停止
    """
    order = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.id == follow_id,
        SignalFollowOrder.enable_flag == True,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权操作此跟单记录")
    if order.status == "stopped":
        raise HTTPException(status_code=400, detail="跟单已停止")

    now = datetime.utcnow()
    order.status = "stopped"
    order.stop_time = now
    order.update_time = now

    # 将所有未平仓持仓标记为已关闭
    db.query(SignalFollowPosition).filter(
        SignalFollowPosition.follow_order_id == follow_id,
        SignalFollowPosition.status == "open",
    ).update({"status": "closed", "close_time": now, "update_time": now})

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "data": _follow_order_to_dict(order),
        "message": "跟单已停止",
    }


@router.get("/{follow_id}/positions")
async def get_follow_positions(
    follow_id: str,
    position_status: Optional[str] = Query(None, alias="status", description="持仓状态: open/closed"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    获取跟单持仓列表

    查询指定跟单的持仓记录，默认返回当前未平仓持仓。

    参数：
    - follow_id: 跟单ID
    - status   : 持仓状态筛选（open/closed），不传则返回全部
    - page     : 页码
    - page_size: 每页数量

    返回：
    - items: 持仓列表
    - total: 总数量

    异常：
    - 404: 跟单不存在
    - 403: 无权访问
    """
    order = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.id == follow_id,
        SignalFollowOrder.enable_flag == True,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")

    query = db.query(SignalFollowPosition).filter(
        SignalFollowPosition.follow_order_id == follow_id,
    )
    if position_status:
        query = query.filter(SignalFollowPosition.status == position_status)

    total = query.count()
    items = (
        query.order_by(SignalFollowPosition.open_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "success": True,
        "data": {
            "items": [_position_to_dict(p) for p in items],
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/{follow_id}/trades")
async def get_follow_trades(
    follow_id: str,
    symbol: Optional[str] = Query(None, description="交易对过滤"),
    side: Optional[str] = Query(None, description="方向过滤: buy/sell"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_user),
) -> dict[str, Any]:
    """
    获取跟单交易记录

    查询指定跟单的历史成交记录，支持按交易对和方向筛选。

    参数：
    - follow_id: 跟单ID
    - symbol   : 交易对过滤（可选）
    - side     : 方向过滤（buy/sell，可选）
    - page     : 页码
    - page_size: 每页数量

    返回：
    - items: 交易记录列表
    - total: 总数量

    异常：
    - 404: 跟单不存在
    - 403: 无权访问
    """
    order = db.query(SignalFollowOrder).filter(
        SignalFollowOrder.id == follow_id,
        SignalFollowOrder.enable_flag == True,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")

    query = db.query(SignalFollowTrade).filter(
        SignalFollowTrade.follow_order_id == follow_id,
    )
    if symbol:
        query = query.filter(SignalFollowTrade.symbol == symbol.upper())
    if side:
        query = query.filter(SignalFollowTrade.side == side.lower())

    total = query.count()
    items = (
        query.order_by(SignalFollowTrade.trade_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "success": True,
        "data": {
            "items": [_trade_to_dict(t) for t in items],
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size,
        },
    }
