"""
行情路由
========

行情数据API接口 — 接入 MarketService 实例
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from quant_trading_system.models.market import TimeFrame

router = APIRouter()


def _get_engines():
    """获取编排器"""
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


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


class SubscribeRequest(BaseModel):
    """订阅请求"""
    symbols: list[str]
    exchange: str = "binance"
    market_type: str = "spot"


@router.post("/subscribe")
async def subscribe_market(request: SubscribeRequest) -> dict[str, Any]:
    """订阅行情"""
    orch = _get_engines()
    await orch.market_service.subscribe(
        symbols=request.symbols,
        exchange=request.exchange,
        market_type=request.market_type,
    )
    return {
        "success": True,
        "message": f"Subscribed to {len(request.symbols)} symbols",
        "symbols": request.symbols,
    }


@router.post("/unsubscribe")
async def unsubscribe_market(request: SubscribeRequest) -> dict[str, Any]:
    """取消订阅"""
    orch = _get_engines()
    await orch.market_service.unsubscribe(
        symbols=request.symbols,
        exchange=request.exchange,
        market_type=request.market_type,
    )
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
    orch = _get_engines()
    tf = TIMEFRAME_MAP.get(timeframe)
    if not tf:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe: {timeframe}")

    bars = orch.market_service.get_bars(symbol, tf, limit=limit)
    data = [
        {
            "timestamp": b.timestamp,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in bars
    ]
    return {"symbol": symbol, "timeframe": timeframe, "data": data, "count": len(data)}


@router.get("/tick/{symbol}")
async def get_latest_tick(symbol: str) -> dict[str, Any]:
    """获取最新Tick"""
    orch = _get_engines()
    tick = orch.strategy_engine._latest_ticks.get(symbol)
    if not tick:
        return {
            "symbol": symbol,
            "last_price": 0,
            "bid_price": 0,
            "ask_price": 0,
            "volume": 0,
            "timestamp": 0,
        }
    return {
        "symbol": symbol,
        "last_price": tick.last_price,
        "bid_price": tick.bid_price,
        "ask_price": tick.ask_price,
        "volume": tick.volume,
        "timestamp": tick.timestamp,
    }


@router.get("/depth/{symbol}")
async def get_depth(
    symbol: str,
    limit: int = Query(20, description="深度档位"),
) -> dict[str, Any]:
    """获取市场深度"""
    orch = _get_engines()
    depth = orch.strategy_engine._latest_depths.get(symbol)
    if not depth:
        return {"symbol": symbol, "bids": [], "asks": [], "timestamp": 0}
    return {
        "symbol": symbol,
        "bids": [{"price": d.price, "size": d.size} for d in depth.bids[:limit]],
        "asks": [{"price": d.price, "size": d.size} for d in depth.asks[:limit]],
        "timestamp": depth.timestamp,
    }


@router.get("/symbols")
async def get_symbols(
    exchange: str = Query("binance", description="交易所"),
    market_type: str = Query("spot", description="市场类型"),
) -> dict[str, Any]:
    """获取已订阅的交易对列表"""
    orch = _get_engines()
    collector_key = f"{exchange}_{market_type}"
    collector = orch.market_service._collectors.get(collector_key)
    symbols = list(collector.subscriptions) if collector else []
    return {"exchange": exchange, "market_type": market_type, "symbols": symbols}


@router.get("/stats")
async def get_market_stats() -> dict[str, Any]:
    """获取行情服务统计"""
    orch = _get_engines()
    return orch.market_service.stats
