"""
行情路由
========

行情数据API接口
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from quant_trading_system.models.market import TimeFrame

router = APIRouter()


class SubscribeRequest(BaseModel):
    """订阅请求"""
    symbols: list[str]
    exchange: str = "binance"
    market_type: str = "spot"


@router.post("/subscribe")
async def subscribe_market(request: SubscribeRequest) -> dict[str, Any]:
    """订阅行情"""
    return {
        "success": True,
        "message": f"Subscribed to {len(request.symbols)} symbols",
        "symbols": request.symbols,
    }


@router.post("/unsubscribe")
async def unsubscribe_market(request: SubscribeRequest) -> dict[str, Any]:
    """取消订阅"""
    return {
        "success": True,
        "message": f"Unsubscribed from {len(request.symbols)} symbols",
    }


@router.get("/kline/{symbol}")
async def get_kline(
    symbol: str,
    timeframe: str = Query("1m", description="时间周期"),
    limit: int = Query(100, description="数量限制", ge=1, le=1000),
) -> dict[str, Any]:
    """获取K线数据"""
    # 实际应从市场服务获取数据
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": [],
        "count": 0,
    }


@router.get("/tick/{symbol}")
async def get_latest_tick(symbol: str) -> dict[str, Any]:
    """获取最新Tick"""
    return {
        "symbol": symbol,
        "last_price": 0,
        "bid_price": 0,
        "ask_price": 0,
        "volume": 0,
        "timestamp": 0,
    }


@router.get("/depth/{symbol}")
async def get_depth(
    symbol: str,
    limit: int = Query(20, description="深度档位"),
) -> dict[str, Any]:
    """获取市场深度"""
    return {
        "symbol": symbol,
        "bids": [],
        "asks": [],
        "timestamp": 0,
    }


@router.get("/symbols")
async def get_symbols(
    exchange: str = Query("binance", description="交易所"),
    market_type: str = Query("spot", description="市场类型"),
) -> dict[str, Any]:
    """获取交易对列表"""
    return {
        "exchange": exchange,
        "market_type": market_type,
        "symbols": [],
    }
