"""
回测路由模块
===========

提供策略回测相关的API接口，支持回测执行、结果查询、历史记录管理等功能。

主要功能：
- 执行策略回测并返回回测ID
- 查询回测结果和统计指标
- 获取回测权益曲线和交易记录
- 管理回测历史记录
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from quant_trading_system.services.backtest.backtest_engine import BacktestEngine, BacktestConfig
from quant_trading_system.services.strategy.base import get_strategy_class
from quant_trading_system.models.market import TimeFrame

# 创建回测路由实例
router = APIRouter()

# 回测实例存储（简单内存存储，生产环境应使用数据库）
_backtest_instances: dict[str, BacktestEngine] = {}
_backtest_results: dict[str, Any] = {}

# 时间周期映射表
TIMEFRAME_MAP = {
    "1m": TimeFrame.M1,
    "5m": TimeFrame.M5,
    "15m": TimeFrame.M15,
    "30m": TimeFrame.M30,
    "1h": TimeFrame.H1,
    "4h": TimeFrame.H4,
    "1d": TimeFrame.D1,
    "1w": TimeFrame.W1,
}


class BacktestRequest(BaseModel):
    """
    回测请求数据模型

    参数说明：
    - strategy_type: 策略类型名称
    - symbol: 交易标的符号
    - timeframe: K线时间周期，默认1分钟
    - start_time: 回测开始时间（ISO格式）
    - end_time: 回测结束时间（ISO格式）
    - initial_capital: 初始资金，默认100万
    - commission_rate: 手续费率，默认0.04%
    - slippage_rate: 滑点率，默认0.01%
    - params: 策略参数配置字典
    """
    strategy_type: str
    symbol: str
    timeframe: str = "1m"
    start_time: str  # ISO格式时间
    end_time: str
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0004
    slippage_rate: float = 0.0001
    params: dict[str, Any] = {}


def _create_backtest_id() -> str:
    """生成回测ID"""
    from quant_trading_system.core.snowflake import generate_snowflake_id
    return f"backtest_{generate_snowflake_id()}"


def _parse_datetime(dt_str: str) -> datetime:
    """解析ISO格式时间字符串"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {dt_str}")


@router.post("/run")
async def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    """
    运行策略回测

    执行指定策略的回测，返回回测任务ID和状态信息。

    参数：
    - request: 回测请求参数

    返回：
    - success: 操作是否成功
    - backtest_id: 回测任务唯一标识
    - message: 操作结果描述
    """
    try:
        # 验证策略类型
        strategy_class = get_strategy_class(request.strategy_type)
        if not strategy_class:
            raise HTTPException(status_code=400, detail=f"Unknown strategy type: {request.strategy_type}")

        # 验证时间周期
        timeframe = TIMEFRAME_MAP.get(request.timeframe)
        if not timeframe:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe: {request.timeframe}")

        # 解析时间
        start_dt = _parse_datetime(request.start_time)
        end_dt = _parse_datetime(request.end_time)

        if start_dt >= end_dt:
            raise HTTPException(status_code=400, detail="Start time must be before end time")

        # 创建回测配置
        config = BacktestConfig(
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
        )

        # 创建回测引擎
        backtest_id = _create_backtest_id()
        engine = BacktestEngine(config=config)

        # 创建策略实例
        strategy = strategy_class(
            strategy_id=backtest_id,
            **request.params,
        )

        # 存储回测实例
        _backtest_instances[backtest_id] = engine

        # 启动回测（异步执行）
        import asyncio
        asyncio.create_task(_execute_backtest(backtest_id, engine, strategy, request.symbol, timeframe, start_dt, end_dt))

        return {
            "success": True,
            "backtest_id": backtest_id,
            "message": "Backtest started successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


async def _execute_backtest(
    backtest_id: str,
    engine: BacktestEngine,
    strategy: Any,
    symbol: str,
    timeframe: TimeFrame,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """异步执行回测任务"""
    try:
        # 从数据库获取数据并运行回测
        result = await engine.run_from_database(
            strategy=strategy,
            symbols=[symbol],
            timeframes=[timeframe],
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        # 存储回测结果
        _backtest_results[backtest_id] = result.to_dict()

    except Exception as e:
        # 存储错误信息
        _backtest_results[backtest_id] = {
            "error": str(e),
            "status": "failed"
        }


@router.get("/{backtest_id}")
async def get_backtest_result(backtest_id: str) -> dict[str, Any]:
    """
    获取回测结果

    查询指定回测ID的详细结果和统计指标。

    参数：
    - backtest_id: 回测任务唯一标识

    返回：
    - backtest_id: 回测任务ID
    - status: 回测状态（completed/running/failed）
    - result: 回测结果统计指标
    """
    if backtest_id not in _backtest_results:
        # 检查是否正在运行
        if backtest_id in _backtest_instances:
            return {
                "backtest_id": backtest_id,
                "status": "running",
                "result": None,
                "message": "Backtest is still running"
            }
        else:
            raise HTTPException(status_code=404, detail="Backtest not found")

    result = _backtest_results[backtest_id]

    if "error" in result:
        return {
            "backtest_id": backtest_id,
            "status": "failed",
            "result": None,
            "error": result["error"]
        }

    return {
        "backtest_id": backtest_id,
        "status": "completed",
        "result": result
    }


@router.get("/{backtest_id}/equity")
async def get_backtest_equity(backtest_id: str) -> dict[str, Any]:
    """
    获取回测权益曲线

    查询回测过程中的权益变化曲线数据。

    参数：
    - backtest_id: 回测任务唯一标识

    返回：
    - backtest_id: 回测任务ID
    - equity_curve: 权益曲线数据列表
    """
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    result = _backtest_results[backtest_id]

    if "error" in result:
        raise HTTPException(status_code=400, detail=f"Backtest failed: {result['error']}")

    return {
        "backtest_id": backtest_id,
        "equity_curve": result.get("equity_curve", [])
    }


@router.get("/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    获取回测交易记录

    查询回测过程中产生的所有交易记录。

    参数：
    - backtest_id: 回测任务唯一标识
    - limit: 返回记录数量限制（1-1000）

    返回：
    - backtest_id: 回测任务ID
    - trades: 交易记录列表
    - total: 总交易记录数
    """
    if backtest_id not in _backtest_results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    result = _backtest_results[backtest_id]

    if "error" in result:
        raise HTTPException(status_code=400, detail=f"Backtest failed: {result['error']}")

    trades = result.get("trades", [])

    return {
        "backtest_id": backtest_id,
        "trades": trades[:limit],
        "total": len(trades)
    }


@router.get("/list")
async def list_backtests(
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """
    获取回测历史列表

    查询所有历史回测任务的简要信息列表。

    参数：
    - limit: 返回记录数量限制（1-100）

    返回：
    - backtests: 回测任务列表
    - total: 总回测任务数
    """
    backtests = []

    for backtest_id, result in list(_backtest_results.items())[:limit]:
        status = "completed"
        if "error" in result:
            status = "failed"

        backtests.append({
            "backtest_id": backtest_id,
            "status": status,
            "strategy_name": result.get("strategy_name", "Unknown"),
            "start_time": result.get("start_time"),
            "end_time": result.get("end_time"),
            "total_return": result.get("total_return", 0),
            "total_trades": result.get("total_trades", 0)
        })

    return {
        "backtests": backtests,
        "total": len(_backtest_results)
    }


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str) -> dict[str, Any]:
    """
    删除回测记录

    删除指定的回测任务记录。

    参数：
    - backtest_id: 回测任务唯一标识

    返回：
    - success: 操作是否成功
    - backtest_id: 被删除的回测任务ID
    - message: 操作结果描述
    """
    if backtest_id in _backtest_instances:
        del _backtest_instances[backtest_id]

    if backtest_id in _backtest_results:
        del _backtest_results[backtest_id]

    return {
        "success": True,
        "backtest_id": backtest_id,
        "message": "Backtest deleted successfully"
    }
