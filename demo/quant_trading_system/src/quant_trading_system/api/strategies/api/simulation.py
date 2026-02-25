"""
C 端模拟交易专用接口
====================

提供模拟交易的 K 线数据、指标数据、交易点标记、持仓、交易记录和运行日志等接口。
挂载在 /api/v1/c/simulation/ 下。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from quant_trading_system.services.database.database import get_db
from quant_trading_system.api.strategies.services import (
    UserStrategyService,
    SimulationService,
)

router = APIRouter()


def _get_current_user_id(request: Request) -> int:
    """从请求中获取当前用户ID"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        username = getattr(request.state, "username", None)
        if not username:
            raise HTTPException(status_code=401, detail="未提供认证凭据")
        user_id = hash(username) & 0x7FFFFFFFFFFFFFFF
    return int(user_id)


def _check_strategy_access(db: Session, strategy_id: int, user_id: int):
    """检查策略访问权限"""
    strategy = UserStrategyService.get_detail(db, strategy_id, user_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在或无权访问")
    return strategy


@router.get("/{strategy_id}/klines")
async def get_simulation_klines(
    strategy_id: int,
    request: Request,
    timeframe: Optional[str] = Query(None, description="K线周期，默认与策略配置一致"),
    start_time: Optional[int] = Query(None, description="开始时间戳(ms)"),
    end_time: Optional[int] = Query(None, description="结束时间戳(ms)"),
    limit: int = Query(500, ge=1, le=2000, description="返回条数"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取模拟交易的K线历史数据

    支持分页加载，前端拖动图表时可传入 end_time 获取更早数据。
    返回数据按时间升序排列，time 为 Unix 秒级时间戳。
    """
    user_id = _get_current_user_id(request)
    strategy = _check_strategy_access(db, strategy_id, user_id)

    # 使用策略配置的交易对和交易所查询K线数据
    symbol = (strategy.get("symbols") or ["BTC/USDT"])[0]
    exchange = strategy.get("exchange", "binance")
    tf = timeframe or strategy.get("timeframe", "1h")

    # TODO: 从 kline_data 表查询实际K线数据
    # 此处返回占位数据格式
    return {
        "strategy_id": str(strategy_id),
        "symbol": symbol,
        "timeframe": tf,
        "data": [],  # TODO: 查询 kline_data 表
    }


@router.get("/{strategy_id}/indicators")
async def get_simulation_indicators(
    strategy_id: int,
    request: Request,
    start_time: Optional[int] = Query(None, description="开始时间戳(ms)"),
    end_time: Optional[int] = Query(None, description="结束时间戳(ms)"),
    limit: int = Query(500, ge=1, le=2000, description="返回条数"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取策略指标历史数据

    返回策略使用的技术指标数据，包含指标类型、颜色、面板和数据。

    - pane 字段指示指标显示在主图(main)还是副图(sub/sub2)
    - type 字段指示绘制类型：line(线图)、histogram(柱状图)、area(面积图)
    """
    user_id = _get_current_user_id(request)
    _check_strategy_access(db, strategy_id, user_id)

    # TODO: 查询策略指标数据
    return {
        "strategy_id": str(strategy_id),
        "indicators": [],  # TODO: 接入实际指标数据
    }


@router.get("/{strategy_id}/trade-marks")
async def get_simulation_trade_marks(
    strategy_id: int,
    request: Request,
    start_time: Optional[int] = Query(None, description="开始时间戳(ms)"),
    end_time: Optional[int] = Query(None, description="结束时间戳(ms)"),
    limit: int = Query(100, ge=1, le=500, description="返回条数"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取交易买卖点标记

    返回策略运行中的买卖交易点，用于在K线图上标注。
    买入标记使用绿色位于K线下方，卖出标记使用红色位于K线上方。
    """
    user_id = _get_current_user_id(request)
    _check_strategy_access(db, strategy_id, user_id)

    return SimulationService.get_trade_marks(
        db, strategy_id, start_time=start_time, end_time=end_time, limit=limit,
    )


@router.get("/{strategy_id}/positions")
async def get_simulation_positions(
    strategy_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取当前模拟持仓

    返回策略当前持仓列表和汇总信息。
    """
    user_id = _get_current_user_id(request)
    _check_strategy_access(db, strategy_id, user_id)

    return SimulationService.get_positions(db, strategy_id)


@router.get("/{strategy_id}/trades")
async def get_simulation_trades(
    strategy_id: int,
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取模拟交易记录

    分页查询策略的模拟交易历史记录。
    """
    user_id = _get_current_user_id(request)
    _check_strategy_access(db, strategy_id, user_id)

    return SimulationService.get_trades(db, strategy_id, page=page, page_size=page_size)


@router.get("/{strategy_id}/logs")
async def get_simulation_logs(
    strategy_id: int,
    request: Request,
    level: Optional[str] = Query(None, description="日志级别: info/warn/error/trade"),
    limit: int = Query(50, ge=1, le=200, description="返回条数"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取模拟运行日志

    查询策略模拟运行产生的日志记录。
    """
    user_id = _get_current_user_id(request)
    _check_strategy_access(db, strategy_id, user_id)

    return SimulationService.get_logs(db, strategy_id, level=level, limit=limit)
