"""
行情 WebSocket 路由
==================

提供行情实时推送的 WebSocket 接口。

支持频道：
- ticker/{symbol}            : 实时 Ticker（最新价、涨跌幅、成交量）
- kline/{symbol}/{timeframe} : K 线数据（实时更新）
- depth/{symbol}             : 市场深度（买卖盘）
- indicator/{symbol}/{timeframe}/{indicator_name} : 技术指标实时数据

消息协议（客户端 → 服务端）：
    {"action": "subscribe",   "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]}
    {"action": "unsubscribe", "channels": ["ticker/BTCUSDT"]}
    {"action": "ping"}

消息协议（服务端 → 客户端）：
    {"type": "ticker",    "channel": "ticker/BTCUSDT",       "data": {...}, "timestamp": "..."}
    {"type": "kline",     "channel": "kline/BTCUSDT/1m",     "data": {...}, "timestamp": "..."}
    {"type": "depth",     "channel": "depth/BTCUSDT",        "data": {...}, "timestamp": "..."}
    {"type": "indicator", "channel": "indicator/BTCUSDT/1m/MACD", "data": {...}, "timestamp": "..."}
    {"type": "pong"}
    {"type": "error",     "message": "..."}
"""

import structlog
import re
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import ws_manager
from quant_trading_system.core.jwt_utils import JWTUtils

logger = structlog.get_logger(__name__)

router = APIRouter()

# ---- 频道名称校验 ----
VALID_CHANNEL_PATTERNS = [
    re.compile(r"^ticker/[A-Za-z0-9_]+$"),
    re.compile(r"^kline/[A-Za-z0-9_]+/(1m|5m|15m|30m|1h|4h|1d|1w)$"),
    re.compile(r"^depth/[A-Za-z0-9_]+$"),
    re.compile(r"^indicator/[A-Za-z0-9_]+/(1m|5m|15m|30m|1h|4h|1d|1w)/[A-Za-z0-9_]+$"),
]


def is_valid_channel(channel: str) -> bool:
    """校验频道名称是否合法"""
    return any(p.match(channel) for p in VALID_CHANNEL_PATTERNS)


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
    - indicator/{symbol}/{timeframe}/{indicator_name} : 技术指标

    示例订阅：
        {"action": "subscribe", "channels": ["ticker/BTCUSDT", "kline/BTCUSDT/1m"]}
    """
    # 解析可选 token 获取 user_id
    user_id = None
    if token:
        try:
            jwt_utils = JWTUtils()
            payload = jwt_utils.verify_token(token)
            user_id = payload.get("user_id") or payload.get("sub")
        except Exception:
            pass

    # 连接管理器可能因为连接数上限而拒绝
    accepted = await ws_manager.connect(ws, user_id=user_id)
    if not accepted:
        return

    # 发送欢迎消息
    await ws_manager.send_to_connection(ws, {
        "type": "connected",
        "message": "行情 WebSocket 连接成功",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    try:
        while True:
            raw = await ws.receive_text()
            # 更新最后活跃时间（用于心跳超时检测）
            ws_manager.update_last_active(ws)
            await ws_manager.handle_message(ws, raw, channel_validator=is_valid_channel)
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
    - symbol: 交易对符号（如 BTCUSDT）
    - data  : Ticker 数据字典
    """
    channel = f"ticker/{symbol}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "ticker",
        "channel": channel,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def push_kline(symbol: str, timeframe: str, data: dict) -> None:
    """
    推送 K 线数据到订阅该频道的所有客户端

    由行情服务在 K 线更新时调用。

    参数：
    - symbol   : 交易对符号（如 BTCUSDT）
    - timeframe: 时间周期（1m/5m/15m/1h/4h/1d）
    - data     : K 线数据字典
    """
    channel = f"kline/{symbol}/{timeframe}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "kline",
        "channel": channel,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def push_depth(symbol: str, data: dict) -> None:
    """
    推送市场深度到订阅该频道的所有客户端

    参数：
    - symbol: 交易对符号（如 BTCUSDT）
    - data  : 深度数据字典（bids/asks）
    """
    channel = f"depth/{symbol}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "depth",
        "channel": channel,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def push_indicator(
    symbol: str,
    timeframe: str,
    indicator_name: str,
    data: dict,
) -> None:
    """
    推送技术指标数据到订阅该频道的所有客户端

    当K线闭合后，由行情订阅器计算指标最新值并推送。

    参数：
    - symbol        : 交易对符号（如 BTCUSDT）
    - timeframe     : 时间周期（1m/5m/15m/1h/4h/1d）
    - indicator_name : 指标名称（MACD/RSI/BOLL/EMA/SMA 等）
    - data          : 指标数据字典，包含各输出字段的最新值
    """
    channel = f"indicator/{symbol}/{timeframe}/{indicator_name}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "indicator",
        "channel": channel,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def get_indicator_channels() -> list[str]:
    """
    获取当前被订阅的所有 indicator 频道

    返回：
        频道名称列表，格式为 indicator/{symbol}/{timeframe}/{indicator_name}
    """
    return [
        ch for ch in ws_manager.channel_stats.keys()
        if ch.startswith("indicator/")
    ]
