"""
策略路由
========

策略管理API接口 — 接入 StrategyEngine 实例
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _get_engines():
    """获取编排器中的引擎实例"""
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


class CreateStrategyRequest(BaseModel):
    """创建策略请求"""
    name: str
    strategy_type: str
    symbols: list[str]
    params: dict[str, Any] = {}


class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    params: dict[str, Any] = {}


@router.get("/list")
async def list_strategies() -> dict[str, Any]:
    """获取策略列表"""
    orch = _get_engines()
    se = orch.strategy_engine
    strategies = []
    for sid in se.list_strategies():
        s = se.get_strategy(sid)
        if s:
            strategies.append({
                "strategy_id": sid,
                "name": s.name,
                "state": s.state.value,
                "symbols": s.symbols,
                "timeframes": [tf.value for tf in s.timeframes],
            })
    return {"strategies": strategies, "total": len(strategies)}


@router.get("/types")
async def get_strategy_types() -> dict[str, Any]:
    """获取可用的策略类型"""
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import (
        list_strategies as list_registered,
        get_strategy_class,
    )

    types = []
    for name in list_registered():
        cls = get_strategy_class(name)
        if cls:
            types.append({
                "name": name,
                "description": cls.description,
                "params": cls.params_def,
                "timeframes": [tf.value for tf in cls.timeframes],
            })
    return {"types": types}


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str) -> dict[str, Any]:
    """获取策略详情"""
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": strategy_id,
        "name": s.name,
        "state": s.state.value,
        "params": s.params,
        "symbols": s.symbols,
        "timeframes": [tf.value for tf in s.timeframes],
        "stats": {
            "signal_count": s._signal_count,
        },
    }


@router.post("/create")
async def create_strategy(request: CreateStrategyRequest) -> dict[str, Any]:
    """创建策略"""
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import get_strategy_class

    orch = _get_engines()
    cls = get_strategy_class(request.strategy_type)
    if not cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy type: {request.strategy_type}",
        )

    strategy_id = orch.add_strategy(
        cls, symbols=request.symbols, **request.params
    )
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy created",
    }


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    request: UpdateStrategyRequest,
) -> dict[str, Any]:
    """更新策略参数"""
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # 更新参数
    s.params.update(request.params)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy updated",
    }


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str) -> dict[str, Any]:
    """删除策略"""
    orch = _get_engines()
    orch.strategy_engine.remove_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy deleted",
    }


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: str) -> dict[str, Any]:
    """启动策略"""
    orch = _get_engines()
    try:
        await orch.strategy_engine.start_strategy(strategy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy started",
    }


@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: str) -> dict[str, Any]:
    """停止策略"""
    orch = _get_engines()
    await orch.strategy_engine.stop_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy stopped",
    }


@router.post("/{strategy_id}/pause")
async def pause_strategy(strategy_id: str) -> dict[str, Any]:
    """暂停策略"""
    orch = _get_engines()
    await orch.strategy_engine.pause_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy paused",
    }


@router.post("/{strategy_id}/resume")
async def resume_strategy(strategy_id: str) -> dict[str, Any]:
    """恢复策略"""
    orch = _get_engines()
    await orch.strategy_engine.resume_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy resumed",
    }


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """获取策略信号历史"""
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": strategy_id,
        "signals": [],  # TODO: 实现信号历史存储
        "total": 0,
    }
