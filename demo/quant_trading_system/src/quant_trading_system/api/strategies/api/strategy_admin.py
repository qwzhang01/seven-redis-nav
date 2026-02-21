"""
策略路由模块
===========

提供策略管理相关的API接口，接入StrategyEngine实例，支持策略的完整生命周期管理。

主要功能：
- 策略创建、更新、删除管理
- 策略启动、停止、暂停、恢复控制
- 策略列表和详情查询
- 策略信号历史记录查询
- 可用策略类型查询
- 策略性能指标查询
- 策略发布/下架管理
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 创建策略路由实例
router = APIRouter()


def _get_engines():
    """
    获取编排器中的引擎实例

    返回当前系统的编排器实例，用于访问策略引擎和其他组件。

    异常：
    - HTTPException: 当交易系统未启动时返回503错误
    """
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


class CreateStrategyRequest(BaseModel):
    """
    创建策略请求数据模型

    参数说明：
    - name: 策略名称（用户自定义）
    - strategy_type: 策略类型名称（系统注册的策略类型）
    - symbols: 策略监控的交易对列表
    - params: 策略参数配置字典
    """
    name: str
    strategy_type: str
    symbols: list[str]
    params: dict[str, Any] = {}


class UpdateStrategyRequest(BaseModel):
    """
    更新策略请求数据模型

    参数说明：
    - params: 要更新的策略参数字典
    """
    params: dict[str, Any] = {}


@router.get("/list")
async def list_strategies(
    keyword: Optional[str] = Query(None, description="按策略名称关键词搜索"),
    state: Optional[str] = Query(None, description="按状态筛选：running / stopped / paused"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict[str, Any]:
    """
    获取策略列表

    查询系统中所有已创建的策略基本信息列表，支持关键词搜索、状态筛选和分页。

    参数：
    - keyword: 策略名称关键词（模糊匹配）
    - state: 策略状态筛选（running/stopped/paused）
    - page: 页码（从1开始）
    - page_size: 每页数量（1-100）

    返回：
    - strategies: 策略信息列表
    - total: 符合条件的策略总数
    - page: 当前页码
    - page_size: 每页数量

    策略信息包含：
    - strategy_id: 策略唯一标识
    - name: 策略名称
    - state: 策略状态（running/stopped/paused）
    - symbols: 监控的交易对列表
    - timeframes: 使用的时间周期列表
    """
    orch = _get_engines()
    se = orch.strategy_engine
    strategies = []
    for sid in se.list_strategies():
        s = se.get_strategy(sid)
        if not s:
            continue
        # 关键词过滤
        if keyword and keyword.lower() not in s.name.lower():
            continue
        # 状态过滤
        if state and s.state.value != state:
            continue
        strategies.append({
            "strategy_id": sid,
            "name": s.name,
            "state": s.state.value,
            "symbols": s.symbols,
            "timeframes": [tf.value for tf in s.timeframes],
        })

    total = len(strategies)
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "strategies": strategies[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/types")
async def get_strategy_types() -> dict[str, Any]:
    """
    获取可用的策略类型

    查询系统中所有已注册的策略类型及其配置信息。

    返回：
    - types: 策略类型信息列表

    策略类型信息包含：
    - name: 策略类型名称
    - description: 策略描述
    - params: 策略参数定义
    - timeframes: 支持的时间周期列表
    """
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import (
        list_strategies as list_registered,
        get_strategy_class,
    )

    def _serialize_params_def(params_def: dict) -> dict:
        """将 params_def 中的 type 字段（Python 类对象）转换为字符串"""
        result = {}
        for key, definition in params_def.items():
            serialized = {}
            for k, v in definition.items():
                if k == "type" and isinstance(v, type):
                    serialized[k] = v.__name__
                else:
                    serialized[k] = v
            result[key] = serialized
        return result

    types = []
    for name in list_registered():
        cls = get_strategy_class(name)
        if cls:
            types.append({
                "name": name,
                "description": cls.description,
                "params": _serialize_params_def(cls.params_def),
                "timeframes": [tf.value for tf in cls.timeframes],
            })
    return {"types": types}


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str) -> dict[str, Any]:
    """
    获取策略性能指标

    查询指定策略的运行性能统计数据，包括收益率、最大回撤、夏普比率等核心指标。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - strategy_id: 策略ID
    - performance: 性能指标字典，包含：
        - signal_count: 累计信号数
        - trade_count: 累计交易次数
        - running_seconds: 运行时长（秒）
        - total_return: 累计收益率（占位，待接入实际数据）
        - max_drawdown: 最大回撤（占位）
        - sharpe_ratio: 夏普比率（占位）
        - win_rate: 胜率（占位）

    异常：
    - HTTPException 404: 当策略不存在时
    """
    import time as _time
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")

    running_seconds = 0.0
    if s.started_at:
        stopped = s.stopped_at if s.stopped_at else _time.time()
        running_seconds = stopped - s.started_at

    return {
        "strategy_id": strategy_id,
        "performance": {
            "signal_count": s._signal_count,
            "trade_count": s._trade_count,
            "running_seconds": round(running_seconds, 2),
            # 以下指标需接入回测/实盘数据后实现
            "total_return": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "win_rate": None,
        },
    }


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str) -> dict[str, Any]:
    """
    获取策略详情

    查询指定策略的详细信息和运行状态。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - strategy_id: 策略ID
    - name: 策略名称
    - state: 策略状态
    - params: 策略参数配置
    - symbols: 监控的交易对列表
    - timeframes: 使用的时间周期列表
    - stats: 策略统计信息

    异常：
    - HTTPException: 当策略不存在时返回404错误
    """
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
            "trade_count": s._trade_count,
        },
    }


@router.post("/create")
async def create_strategy(request: CreateStrategyRequest) -> dict[str, Any]:
    """
    创建策略

    根据指定的策略类型和参数创建新的策略实例。

    参数：
    - request: 创建策略请求参数

    返回：
    - success: 操作是否成功
    - strategy_id: 新创建的策略ID
    - message: 操作结果描述

    异常：
    - HTTPException: 当策略类型不存在时返回400错误
    """
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
    """
    更新策略参数

    更新指定策略的参数配置。

    参数：
    - strategy_id: 策略唯一标识
    - request: 更新策略请求参数

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException: 当策略不存在时返回404错误
    """
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
    """
    删除策略

    从系统中删除指定的策略实例。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 被删除的策略ID
    - message: 操作结果描述
    """
    orch = _get_engines()
    orch.strategy_engine.remove_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy deleted",
    }


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: str) -> dict[str, Any]:
    """
    启动策略

    启动指定的策略实例，开始接收行情数据并生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException: 当策略不存在时返回404错误
    """
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
    """
    停止策略

    停止指定的策略实例，不再接收行情数据和生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述
    """
    orch = _get_engines()
    await orch.strategy_engine.stop_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy stopped",
    }


@router.post("/{strategy_id}/pause")
async def pause_strategy(strategy_id: str) -> dict[str, Any]:
    """
    暂停策略

    暂停指定的策略实例，暂时停止生成交易信号但保持订阅行情数据。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述
    """
    orch = _get_engines()
    await orch.strategy_engine.pause_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy paused",
    }


@router.post("/{strategy_id}/resume")
async def resume_strategy(strategy_id: str) -> dict[str, Any]:
    """
    恢复策略

    恢复之前暂停的策略实例，重新开始生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述
    """
    orch = _get_engines()
    await orch.strategy_engine.resume_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy resumed",
    }


@router.post("/{strategy_id}/publish")
async def publish_strategy(strategy_id: str) -> dict[str, Any]:
    """
    发布策略

    将指定策略设为已发布状态，使其对 C 端用户可见。
    发布后用户可在策略广场中浏览和订阅该策略。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # 在策略参数中标记发布状态
    s.params["published"] = True
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy published",
    }


@router.post("/{strategy_id}/unpublish")
async def unpublish_strategy(strategy_id: str) -> dict[str, Any]:
    """
    下架策略

    将指定策略设为未发布状态，从 C 端策略广场中隐藏。
    下架后用户无法在策略广场中看到该策略，但已订阅的用户不受影响。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # 在策略参数中标记下架状态
    s.params["published"] = False
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy unpublished",
    }


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    获取策略信号历史

    查询指定策略生成的交易信号历史记录。

    参数：
    - strategy_id: 策略唯一标识
    - limit: 返回信号数量限制（1-1000）

    返回：
    - strategy_id: 策略ID
    - signals: 信号历史记录列表
    - total: 总信号数量

    异常：
    - HTTPException: 当策略不存在时返回404错误
    """
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": strategy_id,
        "signals": [],  # TODO: 实现信号历史存储
        "total": 0,
    }
