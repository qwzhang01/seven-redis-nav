"""
行情 WebSocket 路由
==================

提供行情实时推送的 WebSocket 接口。

支持频道：
- ticker/{symbol}            : 实时 Ticker（最新价、涨跌幅、成交量）
- kline/{symbol}/{timeframe} : K 线数据（实时更新）
- depth/{symbol}             : 市场深度（买卖盘）

消息协议（客户端 → 服务端）：
    {"action": "subscribe",   "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]}
    {"action": "unsubscribe", "channels": ["ticker/BTCUSDT"]}
    {"action": "ping"}

消息协议（服务端 → 客户端）：
    {"type": "ticker",  "channel": "ticker/BTCUSDT",       "data": {...}}
    {"type": "kline",   "channel": "kline/BTCUSDT/1m",     "data": {...}}
    {"type": "depth",   "channel": "depth/BTCUSDT",        "data": {...}}
    {"type": "pong"}
    {"type": "error",   "message": "..."}
"""

import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/market")
async def market_websocket(
    ws: WebSocket,
    token: str = Query(None, description="可选 JWT Token，用于身份识别"),
):
    """
    行情实时推送 WebSocket

    连接后发送订阅消息即可接收实时行情数据。

    支持频道：
    - ticker/{symbol}            : 实时 Ticker
    - kline/{symbol}/{timeframe} : K 线数据
    - depth/{symbol}             : 市场深度

    示例订阅：
        {"action": "subscribe", "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]}
    """
    # 解析可选 token 获取 user_id
    user_id = None
    if token:
        try:
            import jwt
            from quant_trading_system.config import settings
            secret_key = getattr(settings, "JWT_SECRET_KEY", "your-secret-key-change-in-production")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload.get("user_id") or payload.get("sub")
        except Exception:
            pass

    await ws_manager.connect(ws, user_id=user_id)
    # 发送欢迎消息
    await ws_manager.send_to_connection(ws, {
        "type": "connected",
        "message": "行情 WebSocket 连接成功",
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            raw = await ws.receive_text()
            await ws_manager.handle_message(ws, raw)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("行情 WebSocket 异常: %s", e)
    finally:
        await ws_manager.disconnect(ws)


async def push_ticker(symbol: str, data: dict) -> None:
    """
    推送 Ticker 行情到订阅该频道的所有客户端

    由行情服务（MarketService）在收到新 Tick 时调用。

    参数：
    - symbol: 交易对符号
    - data  : Ticker 数据字典
    """
    channel = f"ticker/{symbol}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "ticker",
        "channel": channel,
        "data": data,
    })


async def push_kline(symbol: str, timeframe: str, data: dict) -> None:
    """
    推送 K 线数据到订阅该频道的所有客户端

    由行情服务在 K 线更新时调用。

    参数：
    - symbol   : 交易对符号
    - timeframe: 时间周期（1m/5m/15m/1h/4h/1d）
    - data     : K 线数据字典
    """
    channel = f"kline/{symbol}/{timeframe}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "kline",
        "channel": channel,
        "data": data,
    })


async def push_depth(symbol: str, data: dict) -> None:
    """
    推送市场深度到订阅该频道的所有客户端

    参数：
    - symbol: 交易对符号
    - data  : 深度数据字典（bids/asks）
    """
    channel = f"depth/{symbol}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "depth",
        "channel": channel,
        "data": data,
    })
