"""
信号跟单管理路由模块
=======================

提供信号跟单的完整管理 API 接口：

C 端接口（需登录）：
- GET  /list                     : 获取用户所有跟单记录
- POST /                         : 创建跟单
- GET  /{follow_id}              : 获取跟单详情
- GET  /{follow_id}/comparison   : 获取跟单收益对比数据
- GET  /{follow_id}/trades       : 获取跟单交易记录
- GET  /{follow_id}/events       : 获取事件日志
- GET  /{follow_id}/positions    : 获取仓位分布
- PUT  /{follow_id}/config       : 更新跟单配置
- POST /{follow_id}/stop         : 停止跟单
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.models.user import User
from quant_trading_system.core.database import get_db
from quant_trading_system.api.signal.services.follow_service import FollowService
from quant_trading_system.api.deps import get_follow_engine_dep

logger = logging.getLogger(__name__)
router = APIRouter()


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


# ── 请求模型 ──────────────────────────────────────────────────────────────────

class UpdateFollowConfigRequest(BaseModel):
    """更新跟单配置请求"""
    followRatio: Optional[float] = Field(None, description="跟单比例")
    stopLoss: Optional[float] = Field(None, ge=1, le=50, description="止损百分比")
    followAmount: Optional[float] = Field(None, gt=0, description="跟单资金(USDT)")


class CreateFollowRequest(BaseModel):
    """创建跟单请求"""
    signalId: str = Field(..., description="要跟单的信号ID")
    signalName: str = Field(..., description="信号/策略名称")
    exchange: str = Field("binance", description="交易所")
    followAmount: float = Field(..., gt=0, description="跟单资金(USDT)")
    followRatio: float = Field(1.0, gt=0, le=1, description="跟单比例(0~1)")
    stopLoss: Optional[float] = Field(None, gt=0, lt=1, description="止损比例(0~1)")


class StopFollowRequest(BaseModel):
    """停止跟单请求"""
    closePositions: bool = Field(True, description="是否同时平仓所有持仓")
    reason: Optional[str] = Field(None, max_length=200, description="停止原因")


# ── 跟单管理接口 ──────────────────────────────────────────────────────────────

@router.post("")
async def create_follow(
    body: CreateFollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    创建跟单

    为当前用户创建一条新的信号跟单记录。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.create_follow(
            s,
            user_id=current_user.id,
            username=current_user.username,
            signal_id=body.signalId,
            signal_name=body.signalName,
            exchange=body.exchange,
            follow_amount=body.followAmount,
            follow_ratio=body.followRatio,
            stop_loss=body.stopLoss,
        ))
        return {"code": 0, "message": "跟单创建成功", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
async def get_user_follows(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤: following/stopped/paused"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取用户所有的信号跟单记录

    返回当前用户的全部跟单记录列表，支持分页和状态过滤。
    """
    result = await db.run_sync(lambda s: FollowService.get_user_follows(
        s, current_user.id,
        page=page, page_size=page_size, status=status,
    ))
    return {"code": 0, "message": "success", "data": result}


@router.get("/{follow_id}")
async def get_follow_detail(
    follow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取跟单详情

    获取跟单的完整详情，包括配置、收益、持仓、绩效统计。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.get_follow_detail(s, follow_id, current_user.id))
        if not result:
            raise HTTPException(status_code=404, detail="跟单记录不存在")
        return {"code": 0, "message": "success", "data": result}
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")


@router.get("/{follow_id}/comparison")
async def get_follow_comparison(
    follow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取跟单收益对比数据

    获取跟单收益曲线与信号源收益曲线的对比数据，
    包含收益差异、平均滑点、跟单复制率等统计指标。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.get_comparison(s, follow_id, current_user.id))
        return {"code": 0, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")


@router.get("/{follow_id}/trades")
async def get_follow_trades(
    follow_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    side: Optional[str] = Query(None, description="过滤方向: buy/sell"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取跟单交易记录

    查询跟单的历史成交记录，支持按方向过滤和分页。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.get_trades(
            s, follow_id, current_user.id,
            page=page, page_size=page_size, side=side,
        ))
        return {"code": 0, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")


@router.get("/{follow_id}/events")
async def get_follow_events(
    follow_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: Optional[str] = Query(None, alias="type", description="过滤类型: trade/risk/success/error/system"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取事件日志

    查询跟单操作的完整事件日志，包括交易、风控、异常、系统事件。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.get_events(
            s, follow_id, current_user.id,
            page=page, page_size=page_size, event_type=type,
        ))
        return {"code": 0, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")


@router.get("/{follow_id}/positions")
async def get_follow_positions(
    follow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    获取仓位分布

    获取跟单的当前持仓分布，包括各交易对占比、资金使用率等。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.get_positions(s, follow_id, current_user.id))
        return {"code": 0, "message": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权访问此跟单记录")


@router.put("/{follow_id}/config")
async def update_follow_config(
    follow_id: int,
    body: UpdateFollowConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    更新跟单配置

    修改跟单的比例、止损和资金设置。仅允许修改进行中的跟单。
    """
    try:
        result = await db.run_sync(lambda s: FollowService.update_config(
            s, follow_id, current_user.id,
            follow_ratio=body.followRatio,
            stop_loss=body.stopLoss,
            follow_amount=body.followAmount,
        ))
        return {"code": 0, "message": "配置更新成功", "data": result}
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        if "已停止" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权操作此跟单记录")


@router.post("/{follow_id}/stop")
async def stop_follow(
    follow_id: int,
    body: StopFollowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    signal_engine=Depends(get_follow_engine_dep),
) -> dict[str, Any]:
    """
    停止跟单

    将跟单设为停止状态，可选择是否同时平仓。
    同时自动从跟单引擎内存中移除该跟单。
    """
    try:
        # 从跟单引擎内存中移除
        await signal_engine.remove_follow(follow_id)
        logger.info(f"已从跟单引擎移除: follow_id={follow_id}")

        result = await db.run_sync(lambda s: FollowService.stop_follow(
            s, follow_id, current_user.id,
            close_positions=body.closePositions,
            reason=body.reason,
        ))
        return {"code": 0, "message": "跟单已停止", "data": result}
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权操作此跟单记录")
