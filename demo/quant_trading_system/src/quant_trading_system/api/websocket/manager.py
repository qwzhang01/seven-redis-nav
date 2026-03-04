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
- signal/{signal_id}        : 跟单信号订单事件（实时推送信号源的订单变化）
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# ---- 资源限制常量 ----
MAX_CONNECTIONS = 1000              # 最大连接数
MAX_CHANNELS_PER_CONNECTION = 50    # 每连接最大订阅频道数
HEARTBEAT_INTERVAL = 60             # 心跳检查间隔（秒）
HEARTBEAT_TIMEOUT = 120             # 心跳超时时间（秒），超过此时间无活动则断开


class WebSocketManager:
    """
    WebSocket 连接管理器

    职责：
    1. 管理所有活跃的 WebSocket 连接
    2. 维护频道订阅关系（channel -> Set[WebSocket]）
    3. 向指定频道广播消息
    4. 处理连接断开和心跳检测
    5. 连接数 / 订阅数限制
    """

    def __init__(self):
        # 活跃连接集合
        self._connections: Set[WebSocket] = set()
        # 频道订阅映射: channel_name -> Set[WebSocket]
        self._channel_subscribers: Dict[str, Set[WebSocket]] = defaultdict(set)
        # 连接元数据: WebSocket -> {user_id, subscribed_channels, connected_at, last_active}
        self._connection_meta: Dict[WebSocket, dict] = {}
        # 心跳检测任务
        self._heartbeat_task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    #  连接生命周期
    # ------------------------------------------------------------------ #

    async def connect(self, ws: WebSocket, user_id: Optional[str] = None) -> bool:
        """
        接受新连接

        Returns:
            True  - 连接成功
            False - 连接被拒绝（超出上限）
        """
        if len(self._connections) >= MAX_CONNECTIONS:
            await ws.accept()
            await ws.close(code=1013, reason="服务器连接数已满")
            logger.warning("连接被拒绝: 超出最大连接数 %d", MAX_CONNECTIONS)
            return False

        await ws.accept()
        now = datetime.now(timezone.utc)
        self._connections.add(ws)
        self._connection_meta[ws] = {
            "user_id": user_id,
            "subscribed_channels": set(),
            "connected_at": now,
            "last_active": now,
        }
        logger.info("WebSocket 连接建立 user_id=%s 当前连接数=%d", user_id, len(self._connections))
        return True

    async def disconnect(self, ws: WebSocket) -> None:
        """断开连接，清理所有订阅"""
        self._connections.discard(ws)
        meta = self._connection_meta.pop(ws, {})
        # 从所有频道中移除该连接
        for channel in meta.get("subscribed_channels", set()):
            self._channel_subscribers[channel].discard(ws)
            if not self._channel_subscribers[channel]:
                del self._channel_subscribers[channel]
        # 安全关闭
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("WebSocket 连接断开 user_id=%s 当前连接数=%d", meta.get("user_id"), len(self._connections))

    def update_last_active(self, ws: WebSocket) -> None:
        """更新连接的最后活跃时间"""
        meta = self._connection_meta.get(ws)
        if meta:
            meta["last_active"] = datetime.now(timezone.utc)

    # ------------------------------------------------------------------ #
    #  订阅管理
    # ------------------------------------------------------------------ #

    async def subscribe(self, ws: WebSocket, channels: list[str]) -> None:
        """订阅频道列表"""
        meta = self._connection_meta.get(ws)
        if meta is None:
            return

        current_count = len(meta["subscribed_channels"])
        new_channels = [ch for ch in channels if ch not in meta["subscribed_channels"]]

        if current_count + len(new_channels) > MAX_CHANNELS_PER_CONNECTION:
            await self.send_to_connection(ws, {
                "type": "error",
                "message": f"订阅频道数超限，当前 {current_count} 个，最多 {MAX_CHANNELS_PER_CONNECTION} 个",
            })
            return

        for channel in new_channels:
            self._channel_subscribers[channel].add(ws)
            meta["subscribed_channels"].add(channel)
        logger.debug("订阅频道 channels=%s", new_channels)

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

    # ------------------------------------------------------------------ #
    #  消息广播 / 发送
    # ------------------------------------------------------------------ #

    async def broadcast_to_channel(self, channel: str, message: dict) -> None:
        """向频道内所有订阅者并行广播消息"""
        subscribers = self._channel_subscribers.get(channel)
        if not subscribers:
            return
        data = json.dumps(message, default=str, ensure_ascii=False)

        async def _safe_send(ws: WebSocket) -> WebSocket | None:
            try:
                await ws.send_text(data)
                return None
            except Exception:
                return ws

        results = await asyncio.gather(*[_safe_send(ws) for ws in list(subscribers)])
        # 清理已断开的连接
        for ws in results:
            if ws is not None:
                await self.disconnect(ws)

    async def send_to_connection(self, ws: WebSocket, message: dict) -> None:
        """向单个连接发送消息"""
        try:
            await ws.send_text(json.dumps(message, default=str, ensure_ascii=False))
        except Exception as e:
            logger.warning("发送消息失败: %s", e)
            await self.disconnect(ws)

    # ------------------------------------------------------------------ #
    #  客户端消息处理
    # ------------------------------------------------------------------ #

    async def handle_message(
        self,
        ws: WebSocket,
        raw_message: str,
        channel_validator: Callable[[str], bool] | None = None,
    ) -> None:
        """
        处理客户端消息

        支持的 action：
        - subscribe   : 订阅频道
        - unsubscribe : 取消订阅
        - ping        : 心跳

        Args:
            ws: WebSocket 连接
            raw_message: 原始消息文本
            channel_validator: 可选的频道名称校验函数
        """
        try:
            msg = json.loads(raw_message)
        except json.JSONDecodeError:
            await self.send_to_connection(ws, {"type": "error", "message": "无效的 JSON 格式"})
            return

        action = msg.get("action")
        if action == "subscribe":
            channels = msg.get("channels", [])
            # 频道名称校验
            if channel_validator:
                invalid = [ch for ch in channels if not channel_validator(ch)]
                if invalid:
                    await self.send_to_connection(ws, {
                        "type": "error",
                        "message": f"无效的频道名称: {', '.join(invalid)}",
                    })
                    return
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

    # ------------------------------------------------------------------ #
    #  心跳超时检测
    # ------------------------------------------------------------------ #

    async def start_heartbeat(self) -> None:
        """启动后台心跳超时检测任务"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_checker())
            logger.info("心跳检测任务已启动 (间隔=%ds, 超时=%ds)", HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT)

    async def stop_heartbeat(self) -> None:
        """停止心跳检测任务"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("心跳检测任务已停止")

    async def _heartbeat_checker(self) -> None:
        """后台任务：定期检查并关闭超时未活跃的连接"""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            now = datetime.now(timezone.utc)
            dead_connections: list[WebSocket] = []
            for ws in list(self._connections):
                meta = self._connection_meta.get(ws)
                if meta is None:
                    dead_connections.append(ws)
                    continue
                last_active: datetime = meta.get("last_active", now)
                if (now - last_active).total_seconds() > HEARTBEAT_TIMEOUT:
                    logger.info(
                        "心跳超时, 断开连接 user_id=%s last_active=%s",
                        meta.get("user_id"),
                        last_active.isoformat(),
                    )
                    dead_connections.append(ws)
            for ws in dead_connections:
                await self.disconnect(ws)

    # ------------------------------------------------------------------ #
    #  统计信息
    # ------------------------------------------------------------------ #

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
