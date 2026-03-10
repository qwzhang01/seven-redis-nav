"""
行情路由模块
===========

提供市场行情数据相关的API接口，接入MarketService实例，支持行情订阅、K线数据、市场深度等功能。

主要功能：
- 行情订阅和取消订阅管理
- K线数据查询和获取
- 实时Tick数据查询
- 市场深度数据查询
- 交易对列表管理
- 市场服务统计信息
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Depends

from quant_trading_system.core.enums import KlineInterval, DefaultTradingPair

from quant_trading_system.api.deps import get_orchestrator_dep

# 创建行情路由实例
router = APIRouter()



# 合法枚举值
VALID_EXCHANGES = {"binance", "bybit", "bitget"}
VALID_MARKET_TYPES = {"spot", "futures", "margin"}


@router.get("/kline/{symbol}")
async def get_kline(
    symbol: str,
    timeframe: str = Query("1m", description="时间周期"),
    limit: int = Query(100, description="数量限制", ge=1, le=1000),
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    获取K线数据

    查询指定交易对和时间周期的历史K线数据。

    参数：
    - symbol: 交易对符号（使用 `-` 分隔，如 ETH-USDT，会自动转为 ETH/USDT）
    - timeframe: K线时间周期（1m,5m,15m,30m,1h,4h,1d,1w）
    - limit: 返回K线数量限制（1-1000）

    返回：
    - symbol: 交易对符号
    - timeframe: 时间周期
    - data: K线数据列表
    - count: 返回的K线数量
    """
    # 将 URL 安全的 `-` 分隔符还原为 `/`（如 ETH-USDT -> ETH/USDT）
    symbol = symbol.replace("-", "/")

    tf = KlineInterval.from_str(timeframe)
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
async def get_latest_tick(
    symbol: str,
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    获取最新Tick数据

    查询指定交易对的最新Tick行情数据。

    参数：
    - symbol: 交易对符号（使用 `-` 分隔，如 ETH-USDT，会自动转为 ETH/USDT）

    返回：
    - symbol: 交易对符号
    - last_price: 最新成交价
    - bid_price: 买一价
    - ask_price: 卖一价
    - volume: 成交量
    - timestamp: 时间戳
    """
    # 将 URL 安全的 `-` 分隔符还原为 `/`（如 ETH-USDT -> ETH/USDT）
    symbol = symbol.replace("-", "/")

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
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    获取市场深度数据

    查询指定交易对的买卖盘深度数据。

    参数：
    - symbol: 交易对符号（使用 `-` 分隔，如 ETH-USDT，会自动转为 ETH/USDT）
    - limit: 深度档位数量限制

    返回：
    - symbol: 交易对符号
    - bids: 买盘深度列表（价格从高到低）
    - asks: 卖盘深度列表（价格从低到高）
    - timestamp: 时间戳
    """
    # 将 URL 安全的 `-` 分隔符还原为 `/`（如 ETH-USDT -> ETH/USDT）
    symbol = symbol.replace("-", "/")

    depth = orch.strategy_engine._latest_depths.get(symbol)
    if not depth:
        return {"symbol": symbol, "bids": [], "asks": [], "timestamp": 0}
    # Depth.timestamp 已经是 float 毫秒时间戳，直接使用
    return {
        "symbol": symbol,
        "bids": [{"price": d.price, "volume": d.volume} for d in depth.bids[:limit]],
        "asks": [{"price": d.price, "volume": d.volume} for d in depth.asks[:limit]],
        "timestamp": depth.timestamp,
    }


@router.get("/symbols")
async def get_symbols(
    exchange: str = Query("binance", description="交易所"),
    market_type: str = Query("spot", description="市场类型"),
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    获取已订阅的交易对列表

    查询指定交易所和市场类型下已订阅的交易对列表。

    参数：
    - exchange: 交易所名称
    - market_type: 市场类型

    返回：
    - exchange: 交易所名称
    - market_type: 市场类型
    - symbols: 已订阅的交易对列表
    """
    collector_key = f"{exchange}_{market_type}"
    collector = orch.market_service._collectors.get(collector_key)
    symbols = list(collector.subscriptions) if collector else []
    return {"exchange": exchange, "market_type": market_type, "symbols": symbols}


@router.get("/stats")
async def get_market_stats(
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    获取行情服务统计信息

    查询市场服务的运行统计数据和性能指标。

    返回：
    - 市场服务的统计信息字典
    """
    return orch.market_service.stats


@router.post("/load-history")
async def load_history(
    limit: int = Query(500, description="每个周期拉取的K线数量", ge=1, le=1000),
    orch=Depends(get_orchestrator_dep),
) -> dict[str, Any]:
    """
    手动拉取历史K线数据

    从交易所 REST API 拉取历史K线数据并预加载到内存缓冲区。
    交易对从系统默认配置（DefaultTradingPair）中读取。

    参数：
    - limit: 每个交易对每个周期拉取的K线数量（1-1000），默认500

    返回：
    - success: 操作是否成功
    - message: 操作结果描述
    - symbols: 使用的交易对列表
    - stats: 各交易对加载的K线数量统计
    """
    # 从 DefaultTradingPair 枚举获取交易对列表
    symbols = DefaultTradingPair.values()

    stats = await orch.market_service.load_history(
        symbols=symbols,
        limit=limit,
        exchange=orch.exchange,
    )

    total = sum(stats.values())
    return {
        "success": True,
        "message": f"已为 {len(symbols)} 个交易对加载历史K线数据，共 {total} 条",
        "symbols": symbols,
        "stats": stats,
    }


@router.get("/default-symbols")
async def get_default_symbols() -> dict[str, Any]:
    """
    获取系统默认交易对配置

    返回 DefaultTradingPair 枚举中定义的所有默认交易对。

    返回：
    - symbols: 默认交易对列表
    - details: 交易对详细信息（包含 label 和 description）
    """
    return {
        "symbols": DefaultTradingPair.values(),
        "details": DefaultTradingPair.to_list(),
    }
