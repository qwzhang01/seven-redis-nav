"""
M 端策略管理路由（基于数据库）
==============================

面向管理员的策略管理接口，挂载在 /api/v1/m/strategy/ 下。

主要功能：
- 系统预设策略 CRUD 管理
- 策略上架/下架
- 策略启停控制
- 策略表现和信号查询
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from quant_trading_system.services.database.database import get_db
from quant_trading_system.api.strategies.services import PresetStrategyService
from quant_trading_system.core.enums import StrategyType

# 创建 M 端策略路由实例
router = APIRouter()


# ========== 请求模型 ==========

class CreatePresetStrategyRequest(BaseModel):
    """创建预设策略请求"""
    name: str
    description: Optional[str] = None
    detail: Optional[str] = None
    strategy_type: str
    market_type: str = "spot"
    risk_level: str = "medium"
    exchange: str = "binance"
    symbols: Optional[list[str]] = None
    timeframe: str = "1h"
    logic_description: Optional[str] = None
    params_schema: Optional[dict[str, Any]] = None
    default_params: Optional[dict[str, Any]] = None
    risk_params: Optional[dict[str, Any]] = None
    advanced_params: Optional[dict[str, Any]] = None
    risk_warning: Optional[str] = None
    is_featured: bool = False
    sort_order: int = 0


class UpdatePresetStrategyRequest(BaseModel):
    """更新预设策略请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    detail: Optional[str] = None
    strategy_type: Optional[str] = None
    market_type: Optional[str] = None
    risk_level: Optional[str] = None
    exchange: Optional[str] = None
    symbols: Optional[list[str]] = None
    timeframe: Optional[str] = None
    logic_description: Optional[str] = None
    params_schema: Optional[dict[str, Any]] = None
    default_params: Optional[dict[str, Any]] = None
    risk_params: Optional[dict[str, Any]] = None
    advanced_params: Optional[dict[str, Any]] = None
    risk_warning: Optional[str] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    running_days: Optional[int] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None


# ========== 预设策略管理接口 ==========

@router.get("/list")
async def list_strategies(
    keyword: Optional[str] = Query(None, description="按策略名称搜索"),
    market_type: Optional[str] = Query(None, description="市场类型"),
    strategy_type: Optional[str] = Query(None, description="策略类型"),
    risk_level: Optional[str] = Query(None, description="风险等级: low/medium/high"),
    status: Optional[str] = Query(None, description="策略状态"),
    is_published: Optional[bool] = Query(None, description="是否已上架"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略列表（管理端）

    支持按关键词、市场类型、策略类型、风险等级、状态和上架状态筛选。
    """
    return PresetStrategyService.list_strategies(
        db,
        keyword=keyword,
        market_type=market_type,
        strategy_type=strategy_type,
        risk_level=risk_level,
        status=status,
        is_published=is_published,
        page=page,
        page_size=page_size,
    )


@router.get("/types")
async def get_strategy_types() -> dict[str, Any]:
    """
    获取可用的策略类型

    返回所有策略类型枚举信息。
    """
    return {"types": StrategyType.to_list()}


@router.post("/create")
async def create_strategy(
    body: CreatePresetStrategyRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    新增预设策略

    管理员创建系统预设策略模板。
    """
    data = body.model_dump()
    result = PresetStrategyService.create(db, data, operator="admin")
    return {
        "success": True,
        "strategy_id": result["id"],
        "message": "策略创建成功",
    }


@router.get("/{strategy_id}")
async def get_strategy_detail(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略详情

    管理端查看预设策略完整信息。
    """
    detail = PresetStrategyService.get_detail(db, strategy_id)
    if not detail:
        raise HTTPException(status_code=404, detail="策略不存在")
    return detail


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    body: UpdatePresetStrategyRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    编辑策略

    更新预设策略的基本信息和配置。
    """
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = PresetStrategyService.update(db, strategy_id, data, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略更新成功"}


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    删除策略

    逻辑删除预设策略。
    """
    success = PresetStrategyService.delete(db, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": str(strategy_id), "message": "策略删除成功"}


@router.post("/{strategy_id}/publish")
async def publish_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    上架策略

    将策略设为已发布状态，对 C 端用户可见。
    """
    result = PresetStrategyService.publish(db, strategy_id, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略上架成功"}


@router.post("/{strategy_id}/unpublish")
async def unpublish_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    下架策略

    将策略设为未发布状态，从 C 端隐藏。
    """
    result = PresetStrategyService.unpublish(db, strategy_id, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略下架成功"}


@router.post("/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    启动策略（管理端）

    管理员启动预设策略的运行。
    """
    result = PresetStrategyService.update(db, strategy_id, {"status": "running"}, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略启动成功"}


@router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    停止策略（管理端）

    管理员停止预设策略的运行。
    """
    result = PresetStrategyService.update(db, strategy_id, {"status": "stopped"}, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略停止成功"}


@router.post("/{strategy_id}/pause")
async def pause_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    暂停策略（管理端）
    """
    result = PresetStrategyService.update(db, strategy_id, {"status": "paused"}, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略暂停成功"}


@router.post("/{strategy_id}/resume")
async def resume_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    恢复策略（管理端）
    """
    result = PresetStrategyService.update(db, strategy_id, {"status": "running"}, operator="admin")
    if not result:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {"success": True, "strategy_id": result["id"], "message": "策略恢复成功"}


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(
    strategy_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略表现（管理端）
    """
    detail = PresetStrategyService.get_detail(db, strategy_id)
    if not detail:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {
        "strategy_id": detail["id"],
        "performance": {
            "total_return": detail.get("total_return"),
            "max_drawdown": detail.get("max_drawdown"),
            "sharpe_ratio": detail.get("sharpe_ratio"),
            "win_rate": detail.get("win_rate"),
            "running_days": detail.get("running_days"),
        },
    }


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略信号历史（管理端）
    """
    detail = PresetStrategyService.get_detail(db, strategy_id)
    if not detail:
        raise HTTPException(status_code=404, detail="策略不存在")
    return {
        "strategy_id": detail["id"],
        "signals": [],  # TODO: 实现信号历史存储
        "total": 0,
    }
