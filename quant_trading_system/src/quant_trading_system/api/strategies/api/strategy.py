"""
C 端策略管理路由（基于数据库）
==============================

面向普通用户（customer）的策略管理接口，挂载在 /api/v1/c/strategy/ 下。

主要功能：
- 浏览系统预设策略（列表、详情、推荐）
- 创建实盘/模拟策略实例
- 策略启停控制
- 策略表现和信号查询
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.core.database import get_db
from quant_trading_system.api.strategies.services import (
    PresetStrategyService,
    UserStrategyService,
)

# 创建 C 端策略路由实例
router = APIRouter()


def _get_current_user_id(request: Request) -> int:
    """
    从请求状态中获取当前登录用户ID。

    AuthMiddleware 已将 JWT 中的 user_id 写入 request.state.user_id。

    异常：
    - HTTPException: 当用户未认证时返回401错误
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # 兼容 username 方式
        username = getattr(request.state, "username", None)
        if not username:
            raise HTTPException(status_code=401, detail="未提供认证凭据")
        # 如果没有 user_id，使用 username 的 hash 作为临时 ID
        user_id = hash(username) & 0x7FFFFFFFFFFFFFFF
    return int(user_id)


# ========== 请求模型 ==========

class CreateLiveStrategyRequest(BaseModel):
    """创建实盘策略请求"""
    preset_strategy_id: str
    name: str
    exchange: str = "binance"
    symbols: list[str] = []
    timeframe: str = "1h"
    leverage: int = 1
    initial_capital: float = 10000.0
    params: dict[str, Any] = {}
    # 仓位控制
    trade_mode: str = "both"
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    stop_mode: str = "both"
    max_positions: int = 10
    max_orders: int = 50


class CreateSimulateStrategyRequest(BaseModel):
    """创建模拟策略请求"""
    preset_strategy_id: str
    name: str = ""
    exchange: str = "binance"
    symbols: list[str] = []
    timeframe: str = "1h"
    leverage: int = 1
    initial_capital: float = 10000.0
    params: dict[str, Any] = {}
    trade_mode: str = "both"
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    stop_mode: str = "both"


class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    params: dict[str, Any] = {}
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    stop_mode: Optional[str] = None
    max_positions: Optional[int] = None
    max_orders: Optional[int] = None


# ========== 预设策略接口（浏览）==========

@router.get("/featured")
async def get_featured_strategies(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取首页推荐策略

    返回系统推荐的优质预设策略列表，用于首页展示。
    """
    strategies = await PresetStrategyService.get_featured(db, limit)
    return {"strategies": strategies, "total": len(strategies)}

@router.get("/list")
async def list_preset_strategies(
    keyword: Optional[str] = Query(None, description="按策略名称搜索"),
    market_type: Optional[str] = Query(None, description="市场类型: spot/futures/margin"),
    strategy_type: Optional[str] = Query(None, description="策略类型"),
    risk_level: Optional[str] = Query(None, description="风险等级: low/medium/high"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取系统预设策略列表（C端只看已上架的）

    支持按市场类型、策略类型、风险等级筛选，支持关键词搜索和分页。
    """
    return await PresetStrategyService.list_strategies(
        db,
        keyword=keyword,
        market_type=market_type,
        strategy_type=strategy_type,
        risk_level=risk_level,
        is_published=True,
        page=page,
        page_size=page_size,
    )


@router.get("/preset/{strategy_id}")
async def get_preset_strategy_detail(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取系统预设策略详情

    包含策略介绍、逻辑说明、参数配置、风险提示等完整信息。
    """
    detail = await PresetStrategyService.get_detail(db, strategy_id)
    if not detail:
        raise HTTPException(status_code=404, detail="策略不存在")
    if not detail.get("is_published"):
        raise HTTPException(status_code=404, detail="策略未上架")
    return detail


# ========== 用户策略接口 ==========

@router.get("/my")
async def list_my_strategies(
    request: Request,
    mode: Optional[str] = Query(None, description="运行模式: live/simulate"),
    status: Optional[str] = Query(None, description="策略状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取当前用户的策略实例列表

    支持按运行模式和状态筛选。
    """
    user_id = _get_current_user_id(request)
    return await UserStrategyService.list_strategies(
        db, user_id, mode=mode, status=status, page=page, page_size=page_size,
    )


@router.post("/create")
async def create_live_strategy(
    request: Request,
    body: CreateLiveStrategyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    创建实盘策略

    根据系统预设策略创建实盘交易策略实例。
    """
    user_id = _get_current_user_id(request)
    data = body.model_dump()
    data["preset_strategy_id"] = int(data["preset_strategy_id"])
    result = await UserStrategyService.create_live(db, user_id, data)
    return {
        "success": True,
        "strategy_id": result["id"],
        "mode": "live",
        "message": "实盘策略创建成功",
    }


@router.post("/simulate")
async def create_simulate_strategy(
    request: Request,
    body: CreateSimulateStrategyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    创建模拟策略

    根据系统预设策略创建模拟交易策略实例，使用虚拟资金。
    """
    user_id = _get_current_user_id(request)
    data = body.model_dump()
    data["preset_strategy_id"] = int(data["preset_strategy_id"])
    if not data.get("name"):
        data["name"] = f"模拟策略_{data['preset_strategy_id']}"
    result = await UserStrategyService.create_simulation(db, user_id, data)
    return {
        "success": True,
        "strategy_id": result["id"],
        "mode": "simulate",
        "initial_capital": result.get("initial_capital"),
        "message": "模拟策略创建成功",
    }


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略性能指标

    返回策略运行的各项性能统计指标。
    """
    user_id = _get_current_user_id(request)
    result = await UserStrategyService.get_performance(db, strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权访问")
    return result


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: int,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略信号历史

    查询指定策略生成的交易信号历史记录。
    """
    user_id = _get_current_user_id(request)
    strategy = await UserStrategyService.get_detail(db, strategy_id, user_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在或无权访问")
    return {
        "strategy_id": str(strategy_id),
        "signals": [],  # TODO: 实现信号历史存储
        "total": 0,
    }


@router.get("/{strategy_id}")
async def get_strategy_detail(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    获取用户策略实例详情

    包含策略配置、运行状态和统计信息。
    """
    user_id = _get_current_user_id(request)
    detail = await UserStrategyService.get_detail(db, strategy_id, user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="策略不存在或无权访问")
    return detail


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    request: Request,
    body: UpdateStrategyRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    更新策略参数
    """
    user_id = _get_current_user_id(request)
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await UserStrategyService.update(db, strategy_id, user_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": result["id"], "message": "策略更新成功"}


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    删除策略
    """
    user_id = _get_current_user_id(request)
    success = await UserStrategyService.delete(db, strategy_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": str(strategy_id), "message": "策略删除成功"}


@router.post("/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    启动策略
    """
    user_id = _get_current_user_id(request)
    result = await UserStrategyService.start(db, strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": result["id"], "message": "策略启动成功"}


@router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    停止策略
    """
    user_id = _get_current_user_id(request)
    result = await UserStrategyService.stop(db, strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": result["id"], "message": "策略停止成功"}


@router.post("/{strategy_id}/pause")
async def pause_strategy(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    暂停策略
    """
    user_id = _get_current_user_id(request)
    result = await UserStrategyService.pause(db, strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": result["id"], "message": "策略暂停成功"}


@router.post("/{strategy_id}/resume")
async def resume_strategy(
    strategy_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    恢复策略
    """
    user_id = _get_current_user_id(request)
    result = await UserStrategyService.resume(db, strategy_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在或无权操作")
    return {"success": True, "strategy_id": result["id"], "message": "策略恢复成功"}
