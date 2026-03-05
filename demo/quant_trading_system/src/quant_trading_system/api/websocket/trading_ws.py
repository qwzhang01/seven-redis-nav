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

import structlog
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from .manager import ws_manager
from quant_trading_system.core.jwt_utils import JWTUtils

logger = structlog.get_logger(__name__)

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
        jwt_utils = JWTUtils()
        payload = jwt_utils.verify_token(token)
        user_id = payload.get("user_id") or payload.get("sub")
        if not user_id:
            await ws.close(code=4001, reason="无效的 Token")
            return
    except Exception as e:
        await ws.close(code=4001, reason=str(e))
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


async def push_copy_trade_signal(signal_id: int, event_type: str, trade_data: dict) -> None:
    """
    推送跟单信号的订单事件到 WebSocket 前端

    由信号记录订阅器在收到实时订单事件后调用，向订阅了 signal/{signal_id} 频道的
    前端客户端推送跟单信号的订单变化（创建、成交、取消等）。

    前端通过策略 WebSocket 订阅 signal/{signal_id} 频道即可接收。

    参数：
    - signal_id : 信号源 ID（signal 表的 id）
    - event_type: 事件类型，如 ORDER_NEW / ORDER_FILLED / ORDER_PARTIALLY_FILLED / ORDER_CANCELED
    - trade_data: 订单数据字典，包含 symbol / side / price / quantity 等
    """
    channel = f"signal/{signal_id}"
    await ws_manager.broadcast_to_channel(channel, {
        "type": "copy_trade_signal",
        "channel": channel,
        "event_type": event_type,
        "data": trade_data,
    })
