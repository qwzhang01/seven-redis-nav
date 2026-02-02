"""
回测路由
========

回测API接口
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_type: str
    symbol: str
    timeframe: str = "1m"
    start_time: str  # ISO格式时间
    end_time: str
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0004
    slippage_rate: float = 0.0001
    params: dict[str, Any] = {}


@router.post("/run")
async def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    """运行回测"""
    return {
        "success": True,
        "backtest_id": "new_backtest_id",
        "message": "Backtest started",
    }


@router.get("/{backtest_id}")
async def get_backtest_result(backtest_id: str) -> dict[str, Any]:
    """获取回测结果"""
    return {
        "backtest_id": backtest_id,
        "status": "completed",
        "result": {
            "total_return": 0,
            "annual_return": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "total_trades": 0,
            "win_rate": 0,
        }
    }


@router.get("/{backtest_id}/equity")
async def get_backtest_equity(backtest_id: str) -> dict[str, Any]:
    """获取回测权益曲线"""
    return {
        "backtest_id": backtest_id,
        "equity_curve": [],
    }


@router.get("/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """获取回测交易记录"""
    return {
        "backtest_id": backtest_id,
        "trades": [],
        "total": 0,
    }


@router.get("/list")
async def list_backtests(
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """获取回测历史列表"""
    return {
        "backtests": [],
        "total": 0,
    }


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str) -> dict[str, Any]:
    """删除回测记录"""
    return {
        "success": True,
        "backtest_id": backtest_id,
        "message": "Backtest deleted",
    }
