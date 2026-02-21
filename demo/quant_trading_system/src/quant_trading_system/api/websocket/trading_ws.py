"""
交易事件 WebSocket 路由
=======================

提供交易事件实时推送的 WebSocket 接口（需要认证）。

支持频道：
- trading/{user_id}  : 用户私有交易事件（订单状态变化、成交通知）

消息类型（服务端 → 客户端）：
    {"type": "order_update",  "data": {...}}  # 订单状态变化
    {"type": "trade",         "data": {...}}  # 成交通知
    {"type": "position",      "data": {...}}  # 持仓变化
    {"type": "account",       "data": {...}}  # 账户余额变化
"""

import logging
from datetime import datetime

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/trading")
async def trading_websocket(
    ws: WebSocket,
    token: str = Query(..., description="JWT Token（必填）"),
):
    """
    交易事件实时推送 WebSocket（需要认证）

    连接后自动订阅当前用户的私有交易频道，接收订单、成交、持仓变化通知。

    参数：
    - token: JWT 访问令牌（必填）

    推送事件类型：
    - order_update : 订单状态变化
    - trade        : 成交通知
    - position     : 持仓变化
    - account      : 账户余额变化
    """
    # 验证 token
    user_id = None
    try:
        from quant_trading_system.config import settings
        secret_key = getattr(settings, "JWT_SECRET_KEY", "your-secret-key-change-in-production")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            await ws.close(code=4001, reason="无效的 Token")
            return
    except jwt.ExpiredSignatureError:
        await ws.close(code=4001, reason="Token 已过期")
        return
    except jwt.PyJWTError:
        await ws.close(code=4001, reason="无效的 Token")
        return

    await ws_manager.connect(ws, user_id=user_id)
    # 自动订阅用户私有频道
    private_channel = f"trading/{user_id}"
    await ws_manager.subscribe(ws, [private_channel])

    await ws_manager.send_to_connection(ws, {
        "type": "connected",
        "message": "交易 WebSocket 连接成功",
        "user_id": user_id,
        "subscribed_channels": [private_channel],
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            raw = await ws.receive_text()
            await ws_manager.handle_message(ws, raw)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("交易 WebSocket 异常: %s", e)
    finally:
        await ws_manager.disconnect(ws)


async def push_order_update(user_id: str, order_data: dict) -> None:
    """
    推送订单状态变化通知

    由交易引擎在订单状态变化时调用。

    参数：
    - user_id   : 用户 ID
    - order_data: 订单数据字典
    """
    channel = f"trading/{user_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "order_update",
        "data": order_data,
    })


async def push_trade_notification(user_id: str, trade_data: dict) -> None:
    """
    推送成交通知

    参数：
    - user_id   : 用户 ID
    - trade_data: 成交数据字典
    """
    channel = f"trading/{user_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "trade",
        "data": trade_data,
    })


async def push_position_update(user_id: str, position_data: dict) -> None:
    """
    推送持仓变化通知

    参数：
    - user_id      : 用户 ID
    - position_data: 持仓数据字典
    """
    channel = f"trading/{user_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "position",
        "data": position_data,
    })
