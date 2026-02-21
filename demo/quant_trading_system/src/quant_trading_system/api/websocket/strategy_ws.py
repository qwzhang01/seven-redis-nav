"""
策略信号 WebSocket 路由
=======================

提供策略信号实时推送的 WebSocket 接口。

支持频道：
- strategy/{strategy_id} : 策略信号推送（买入/卖出/平仓信号）

消息类型（服务端 → 客户端）：
    {"type": "signal", "channel": "strategy/xxx", "data": {...}}
    {"type": "strategy_status", "data": {...}}  # 策略状态变化
"""

import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import ws_manager
from quant_trading_system.core.jwt_utils import JWTUtils

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/strategy")
async def strategy_websocket(
    ws: WebSocket,
    token: str = Query(None, description="可选 JWT Token"),
):
    """
    策略信号实时推送 WebSocket

    连接后订阅指定策略频道，实时接收策略产生的交易信号。

    支持频道：
    - strategy/{strategy_id} : 指定策略的信号推送

    示例订阅：
        {"action": "subscribe", "channels": ["strategy/strategy_abc123"]}
    """
    user_id = None
    if token:
        try:
            jwt_utils = JWTUtils()
            payload = jwt_utils.verify_token(token)
            user_id = payload.get("user_id") or payload.get("sub")
        except Exception:
            pass

    await ws_manager.connect(ws, user_id=user_id)
    await ws_manager.send_to_connection(ws, {
        "type": "connected",
        "message": "策略 WebSocket 连接成功",
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            raw = await ws.receive_text()
            await ws_manager.handle_message(ws, raw)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("策略 WebSocket 异常: %s", e)
    finally:
        await ws_manager.disconnect(ws)


async def push_signal(strategy_id: str, signal_data: dict) -> None:
    """
    推送策略信号到订阅该策略频道的所有客户端

    由策略引擎在产生信号时调用。

    参数：
    - strategy_id: 策略 ID
    - signal_data: 信号数据字典
    """
    channel = f"strategy/{strategy_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "signal",
        "channel": channel,
        "data": signal_data,
    })


async def push_strategy_status(strategy_id: str, status_data: dict) -> None:
    """
    推送策略状态变化通知

    参数：
    - strategy_id: 策略 ID
    - status_data: 状态数据字典
    """
    channel = f"strategy/{strategy_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "strategy_status",
        "channel": channel,
        "data": status_data,
    })
