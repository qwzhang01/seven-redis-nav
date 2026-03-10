"""
信号管理路由模块（完整实现）
============================

提供信号详情页的全部 API 接口：

C 端接口（普通用户）：
- GET  /list                           : 获取公开信号列表（信号广场）
- GET  /{signal_id}                    : 获取信号详情
- GET  /{signal_id}/history            : 获取信号历史记录
- GET  /{signal_id}/provider           : 获取信号提供者信息
- GET  /{signal_id}/monthly-returns    : 获取月度收益分布
- GET  /{signal_id}/drawdown           : 获取回撤分析数据
- GET  /{signal_id}/reviews            : 获取用户评价列表
- POST /{signal_id}/reviews            : 提交用户评价
- POST /{signal_id}/reviews/{review_id}/like : 评价点赞
- POST /{signal_id}/follow             : 创建跟单
- GET  /strategy/{strategy_id}/history : 获取策略历史信号
- GET  /subscriptions                  : 获取我的订阅列表
- POST /subscribe                      : 订阅信号通知
- DELETE /subscriptions/{id}           : 取消订阅
"""

import structlog
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.models.signal import (
    Signal,
    SignalTradeRecord,
    SignalSubscription,
)
from quant_trading_system.models.user import User
from quant_trading_system.core.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.api.signal.services.signal_service import SignalService

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)


# ── 权限校验 ──────────────────────────────────────────────────────────────────

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> (
    User):
    """从拦截器验证后的request.state中获取当前用户"""
    username = getattr(request.state, 'username', None)
    if not username:
        raise HTTPException(status_code=401, detail="未认证的用户")
    user = await db.run_sync(lambda s: s.query(User).filter(User.username == username, User.enable_flag == True).first())
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> (
    Optional)[User]:
    """可选获取当前用户（未登录返回None）"""
    username = getattr(request.state, 'username', None)
    if not username:
        return None
    return await db.run_sync(lambda s: s.query(User).filter(User.username == username, User.enable_flag == True).first())


# ── 请求模型 ──────────────────────────────────────────────────────────────────

class SubmitReviewRequest(BaseModel):
    """提交评价请求"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    content: str = Field(..., min_length=10, max_length=500, description="评价内容 10-500字")


class CreateFollowRequest(BaseModel):
    """创建跟单请求"""
    amount: float = Field(..., ge=100, description="跟单资金(USDT)，最小100")
    ratio: float = Field(1.0, description="跟单比例: 0.25/0.5/1.0/2.0")
    stopLoss: float = Field(..., ge=1, le=50, description="止损百分比 1-50")


class SubscribeSignalRequest(BaseModel):
    """订阅信号请求"""
    strategy_id: str
    notify_type: str = "realtime"


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _trade_record_to_dict(s: SignalTradeRecord) -> dict:
    """将 SignalTradeRecord ORM 对象转换为字典"""
    return {
        "id": s.id,
        "signal_id": s.signal_id,
        "action": s.action,
        "symbol": s.symbol,
        "price": float(s.price) if s.price is not None else None,
        "amount": float(s.amount) if s.amount is not None else None,
        "total": float(s.total) if s.total is not None else None,
        "strength": s.strength,
        "pnl": float(s.pnl) if s.pnl is not None else None,
        "traded_at": s.traded_at.isoformat() if s.traded_at else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ── 信号广场接口 ──────────────────────────────────────────────────────────────

@router.get("/list")
async def list_signals(
    platform: Optional[str] = Query(None, description="来源平台筛选"),
    type: Optional[str] = Query(None, alias="type", description="信号类型: live / simulated"),
    min_days: Optional[int] = Query(None, ge=0, description="最小运行天数"),
    search: Optional[str] = Query(None, description="关键词搜索（模糊匹配信号名称）"),
    sort_by: str = Query("return_desc", description="排序: return_desc/return_asc/drawdown_asc/followers"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(9, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号列表（信号广场）

    支持按平台、类型、运行天数筛选，支持关键词搜索和多种排序方式。
    """
    result = await db.run_sync(lambda s: SignalService.list_signals(
        s, platform=platform, signal_type=type,
        min_days=min_days, search=search,
        sort_by=sort_by, page=page, page_size=page_size,
    ))
    return {"code": 0, "message": "success", "data": result}


@router.get("/platforms")
async def get_platforms(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取平台列表（筛选项）

    返回当前系统中所有信号源的平台名称列表。
    """
    platforms = await db.run_sync(lambda s: SignalService.get_platforms(s))
    return {"code": 0, "message": "success", "data": platforms}


# ── 信号详情页接口 ────────────────────────────────────────────────────────────


@router.get("/subscriptions")
async def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取我的信号订阅列表"""
    subs = await db.run_sync(lambda s: s.query(SignalSubscription).filter(
        SignalSubscription.user_id == current_user.id,
        SignalSubscription.is_active == True,
    ).all())

    items = [
        {
            "id": s.id,
            "strategy_id": s.strategy_id,
            "notify_type": s.notify_type,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subs
    ]
    return {"code": 0, "message": "success", "data": {"items": items, "total": len(items)}}


@router.get("/strategy/{strategy_id}/history")
async def get_strategy_signal_history(
    strategy_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取策略历史信号"""
    # 通过 signal 表找到该策略关联的 signal_id
    signal = await db.run_sync(lambda s: s.query(Signal).filter(Signal.strategy_id == strategy_id, Signal.enable_flag == True).first())
    if not signal:
        return {
            "code": 0,
            "message": "success",
            "data": {"strategy_id": strategy_id, "items": [], "total": 0, "page": page, "pages": 0},
        }

    def _get_records(s):
        query = s.query(SignalTradeRecord).filter(SignalTradeRecord.signal_id == signal.id)
        total = query.count()
        items = query.order_by(SignalTradeRecord.traded_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return items, total

    items, total = await db.run_sync(lambda s: _get_records(s))

    return {
        "code": 0,
        "message": "success",
        "data": {
            "strategy_id": strategy_id,
            "items": [_trade_record_to_dict(s) for s in items],
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/{signal_id}")
async def get_signal_detail(
    signal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> dict[str, Any]:
    """
    获取信号详情

    获取信号的完整详情信息，包括基本信息、风险参数、绩效指标、持仓等。
    """
    user_id = current_user.id if current_user else None
    result = await db.run_sync(lambda s: SignalService.get_signal_detail_v2(s, signal_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="信号不存在")
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/return-curve")
async def get_signal_return_curve(
    signal_id: int,
    period: str = Query("all", description="时间范围: 7d/30d/90d/180d/all"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号收益曲线

    返回信号的每日累计收益率和回撤曲线数据，支持时间范围筛选。
    """
    result = await db.run_sync(lambda s: SignalService.get_signal_return_curve(s, signal_id, period))
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/history")
async def get_signal_history(
    signal_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号历史记录

    获取信号发出的交易信号历史列表，支持分页。
    """
    signal = await db.run_sync(lambda s: s.query(Signal).filter(Signal.id == signal_id, Signal.enable_flag == True).first())
    if not signal:
        raise HTTPException(status_code=404, detail="信号不存在")

    result = await db.run_sync(lambda s: SignalService.get_signal_history(s, signal_id, page, page_size))
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/provider")
async def get_signal_provider(
    signal_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取信号提供者信息

    获取信号创建者/提供者的详细资料。
    """
    result = await db.run_sync(lambda s: SignalService.get_signal_provider(s, signal_id))
    if not result:
        raise HTTPException(status_code=404, detail="信号不存在")
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/monthly-returns")
async def get_monthly_returns(
    signal_id: int,
    months: int = Query(12, ge=1, le=60, description="返回月份数"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取月度收益分布

    按月汇总信号的收益分布数据。优先从signal_monthly_return表获取。
    """
    result = await db.run_sync(lambda s: SignalService.get_signal_monthly_returns(s, signal_id, months))
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/drawdown")
async def get_drawdown_analysis(
    signal_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取回撤分析数据

    获取信号的回撤曲线和统计信息。优先从signal_return_curve时序表获取。
    """
    result = await db.run_sync(lambda s: SignalService.get_signal_drawdown(s, signal_id))
    return {"code": 0, "message": "success", "data": result}


@router.get("/{signal_id}/reviews")
async def get_reviews(
    signal_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    sort: str = Query("latest", description="排序: latest/highest/lowest/most_liked"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> dict[str, Any]:
    """
    获取用户评价列表

    获取信号的用户评价，包括评分分布和评价详情。
    """
    signal = await db.run_sync(lambda s: s.query(Signal).filter(Signal.id == signal_id, Signal.enable_flag == True).first())
    if not signal:
        raise HTTPException(status_code=404, detail="信号不存在")

    user_id = current_user.id if current_user else None
    result = await db.run_sync(lambda s: SignalService.get_reviews(s, signal_id, page, page_size, sort, user_id))
    return {"code": 0, "message": "success", "data": result}


@router.post("/{signal_id}/reviews")
async def submit_review(
    signal_id: int,
    body: SubmitReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    提交用户评价

    为信号提交评价和评分，每个用户只能评价一次。
    """
    try:
        result = await db.run_sync(lambda s: SignalService.submit_review(
            s, signal_id, current_user.id, body.rating, body.content
        ))
        return {"code": 0, "message": "评价提交成功", "data": result}
    except ValueError as e:
        error_msg = str(e)
        code = 3001  # 默认评价错误码
        if "已评价" in error_msg:
            code = 3002
        elif "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail={"code": code, "message": error_msg})


@router.post("/{signal_id}/reviews/{review_id}/like")
async def toggle_review_like(
    signal_id: int,
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    评价点赞/取消点赞

    对评价进行点赞，重复点赞则取消。
    """
    try:
        result = await db.run_sync(lambda s: SignalService.toggle_review_like(s, signal_id, review_id, current_user.id))
        return {"code": 0, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{signal_id}/follow")
async def create_follow(
    signal_id: int,
    body: CreateFollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    创建跟单

    为当前用户创建信号跟单，设置跟单资金、比例和止损。
    """
    try:
        result = await db.run_sync(lambda s: SignalService.create_follow(
            s, signal_id, current_user.id,
            body.amount, body.ratio, body.stopLoss,
        ))
        return {"code": 0, "message": "跟单创建成功", "data": result}
    except ValueError as e:
        error_msg = str(e)
        code_map = {
            "信号不存在": 2001,
            "信号已停止": 2003,
            "余额不足": 2004,
            "已跟单": 2005,
            "低于最低限额": 2006,
            "止损比例超出": 2007,
        }
        error_code = 400
        for key, code in code_map.items():
            if key in error_msg:
                error_code = 400
                break
        raise HTTPException(status_code=error_code, detail=error_msg)


# ── 订阅管理接口 ──────────────────────────────────────────────────────────────

@router.post("/subscribe")
async def subscribe_signal(
    request: SubscribeSignalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """订阅策略信号通知"""
    def _subscribe(s):
        existing = s.query(SignalSubscription).filter(
            SignalSubscription.user_id == current_user.id,
            SignalSubscription.strategy_id == request.strategy_id,
        ).first()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.notify_type = request.notify_type
                existing.updated_at = datetime.utcnow()
                s.commit()
            return {
                "id": existing.id,
                "strategy_id": existing.strategy_id,
                "notify_type": existing.notify_type,
                "is_active": existing.is_active,
                "is_update": True,
            }

        sub = SignalSubscription(
            id=generate_snowflake_id(),
            user_id=current_user.id,
            strategy_id=request.strategy_id,
            notify_type=request.notify_type,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        s.add(sub)

        s.query(Signal).filter(
            Signal.strategy_id == request.strategy_id,
            Signal.enable_flag == True,
        ).update({"followers_count": Signal.followers_count + 1})

        s.commit()
        s.refresh(sub)

        return {
            "id": sub.id,
            "strategy_id": sub.strategy_id,
            "notify_type": sub.notify_type,
            "is_active": sub.is_active,
            "is_update": False,
        }

    result = await db.run_sync(_subscribe)

    return {
        "code": 0,
        "message": "已更新订阅" if result.get("is_update") else "订阅成功",
        "data": {
            "id": result["id"],
            "strategy_id": result["strategy_id"],
            "notify_type": result["notify_type"],
            "is_active": result["is_active"],
        },
    }


@router.delete("/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """取消信号订阅"""
    def _cancel(s):
        sub = s.query(SignalSubscription).filter(SignalSubscription.id == subscription_id).first()
        if not sub:
            return {"error": 404, "detail": "订阅不存在"}
        if sub.user_id != current_user.id:
            return {"error": 403, "detail": "无权操作此订阅"}
        sub.is_active = False
        sub.updated_at = datetime.utcnow()
        s.commit()
        return {"success": True}

    result = await db.run_sync(_cancel)

    if "error" in result:
        raise HTTPException(status_code=result["error"], detail=result["detail"])

    return {"code": 0, "message": "已取消订阅", "data": {"success": True}}
