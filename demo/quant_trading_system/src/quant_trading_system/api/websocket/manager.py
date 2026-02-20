"""
WebSocket 连接管理器
===================

负责管理所有活跃的 WebSocket 连接，维护频道订阅关系，
并向指定频道广播消息。

支持的频道格式：
- ticker/{symbol}           : 实时 Ticker 行情
- kline/{symbol}/{timeframe}: K 线数据
- depth/{symbol}            : 市场深度
- strategy/{strategy_id}    : 策略信号
- trading/{user_id}         : 交易事件（私有）
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket 连接管理器

    职责：
    1. 管理所有活跃的 WebSocket 连接
    2. 维护频道订阅关系（channel -> Set[WebSocket]）
    3. 向指定频道广播消息
    4. 处理连接断开和心跳检测
    """

    def __init__(self):
        # 活跃连接集合
        self._connections: Set[WebSocket] = set()
        # 频道订阅映射: channel_name -> Set[WebSocket]
        self._channel_subscribers: Dict[str, Set[WebSocket]] = defaultdict(set)
        # 连接元数据: WebSocket -> {user_id, subscribed_channels, connected_at}
        self._connection_meta: Dict[WebSocket, dict] = {}

    async def connect(self, ws: WebSocket, user_id: Optional[str] = None) -> None:
        """接受新连接"""
        await ws.accept()
        self._connections.add(ws)
        self._connection_meta[ws] = {
            "user_id": user_id,
            "subscribed_channels": set(),
        }
        logger.info("WebSocket 连接建立 user_id=%s 当前连接数=%d", user_id, len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        """断开连接，清理所有订阅"""
        self._connections.discard(ws)
        meta = self._connection_meta.pop(ws, {})
        # 从所有频道中移除该连接
        for channel in meta.get("subscribed_channels", set()):
            self._channel_subscribers[channel].discard(ws)
            if not self._channel_subscribers[channel]:
                del self._channel_subscribers[channel]
        logger.info("WebSocket 连接断开 user_id=%s 当前连接数=%d", meta.get("user_id"), len(self._connections))

    async def subscribe(self, ws: WebSocket, channels: list[str]) -> None:
        """订阅频道列表"""
        meta = self._connection_meta.get(ws)
        if meta is None:
            return
        for channel in channels:
            self._channel_subscribers[channel].add(ws)
            meta["subscribed_channels"].add(channel)
        logger.debug("订阅频道 channels=%s", channels)

    async def unsubscribe(self, ws: WebSocket, channels: list[str]) -> None:
        """取消订阅频道列表"""
        meta = self._connection_meta.get(ws)
        if meta is None:
            return
        for channel in channels:
            self._channel_subscribers[channel].discard(ws)
            meta["subscribed_channels"].discard(channel)
            if not self._channel_subscribers[channel]:
                self._channel_subscribers.pop(channel, None)

    async def broadcast_to_channel(self, channel: str, message: dict) -> None:
        """向频道内所有订阅者广播消息"""
        subscribers = self._channel_subscribers.get(channel)
        if not subscribers:
            return
        data = json.dumps(message, default=str, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(subscribers):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        # 清理已断开的连接
        for ws in dead:
            await self.disconnect(ws)

    async def send_to_connection(self, ws: WebSocket, message: dict) -> None:
        """向单个连接发送消息"""
        try:
            await ws.send_text(json.dumps(message, default=str, ensure_ascii=False))
        except Exception as e:
            logger.warning("发送消息失败: %s", e)
            await self.disconnect(ws)

    async def handle_message(self, ws: WebSocket, raw_message: str) -> None:
        """
        处理客户端消息

        支持的 action：
        - subscribe   : 订阅频道
        - unsubscribe : 取消订阅
        - ping        : 心跳
        """
        try:
            msg = json.loads(raw_message)
        except json.JSONDecodeError:
            await self.send_to_connection(ws, {"type": "error", "message": "无效的 JSON 格式"})
            return

        action = msg.get("action")
        if action == "subscribe":
            channels = msg.get("channels", [])
            await self.subscribe(ws, channels)
            await self.send_to_connection(ws, {
                "type": "subscribed",
                "channels": channels,
            })
        elif action == "unsubscribe":
            channels = msg.get("channels", [])
            await self.unsubscribe(ws, channels)
            await self.send_to_connection(ws, {
                "type": "unsubscribed",
                "channels": channels,
            })
        elif action == "ping":
            await self.send_to_connection(ws, {"type": "pong"})
        else:
            await self.send_to_connection(ws, {"type": "error", "message": f"未知 action: {action}"})

    @property
    def connection_count(self) -> int:
        """当前活跃连接数"""
        return len(self._connections)

    @property
    def channel_stats(self) -> dict:
        """各频道订阅人数统计"""
        return {ch: len(subs) for ch, subs in self._channel_subscribers.items() if subs}


# 全局单例
ws_manager = WebSocketManager()
