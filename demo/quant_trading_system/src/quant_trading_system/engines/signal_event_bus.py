"""
信号事件总线
============

实现发布/订阅（Pub/Sub）模式的信号事件分发机制。

核心职责：
- 定义统一的信号事件类型和数据结构
- 管理订阅器的注册和注销
- 将信号事件异步分发给所有订阅器

事件流：
    WebSocket 收到仓位操作
        ↓
    SignalStreamEngine 解析事件
        ↓
    SignalEventBus.publish()
        ├── SignalRecordSubscriber  → 存储到 signal_trade_record
        └── FollowEngine           → 触发跟单引擎处理

使用方式：
    bus = SignalEventBus()
    bus.subscribe(SignalEventType.ORDER_FILLED, my_subscriber)
    await bus.publish(SignalEvent(type=SignalEventType.ORDER_FILLED, ...))
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 事件类型定义
# ═══════════════════════════════════════════════════════════════


class SignalEventType(Enum):
    """
    信号事件类型枚举

    分为三大类：
    1. 订单事件 —— 目标账户的订单状态变化
    2. 账户事件 —— 目标账户的持仓/余额变化
    3. 系统事件 —— 连接状态变化
    """

    # ── 订单事件（核心） ──
    ORDER_FILLED = auto()         # 订单完全成交（触发跟单的核心事件）
    ORDER_PARTIALLY_FILLED = auto()  # 订单部分成交
    ORDER_NEW = auto()            # 新订单创建
    ORDER_CANCELED = auto()       # 订单取消

    # ── 账户事件 ──
    ACCOUNT_UPDATE = auto()       # 账户持仓变化
    BALANCE_UPDATE = auto()       # 余额变化

    # ── 历史快照事件 ──
    SNAPSHOT_OPEN_ORDERS = auto()   # 当前挂单快照（启动时拉取）
    SNAPSHOT_POSITIONS = auto()     # 当前持仓快照（启动时拉取）
    SNAPSHOT_ACCOUNT = auto()       # 账户信息快照（启动时拉取）
    SNAPSHOT_TRADE_HISTORY = auto() # 最近成交历史快照（启动时拉取）

    # ── 系统事件 ──
    STREAM_CONNECTED = auto()     # 信号流已连接
    STREAM_DISCONNECTED = auto()  # 信号流已断开
    STREAM_ERROR = auto()         # 信号流错误


# ═══════════════════════════════════════════════════════════════
# 事件数据结构
# ═══════════════════════════════════════════════════════════════


@dataclass
class SignalEvent:
    """
    信号事件

    所有通过事件总线传递的信号数据统一封装为此对象。

    Attributes:
        type: 事件类型
        signal_id: 信号源ID（signal 表的 id）
        data: 事件数据（标准化后的订单/账户信息）
        exchange: 来源交易所
        symbol: 交易对
        timestamp: 事件时间戳（毫秒）
        raw_event: 原始 WebSocket 事件数据（调试用）
    """

    type: SignalEventType
    signal_id: int                              # 信号源ID（signal 表的 id）
    data: dict[str, Any]                        # 标准化的事件数据
    exchange: str = "binance"
    symbol: str = ""
    timestamp: float = field(default_factory=lambda: time.time() * 1000)
    raw_event: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"SignalEvent(type={self.type.name}, signal_id={self.signal_id}, "
            f"symbol={self.symbol}, data_keys={list(self.data.keys())})"
        )


@dataclass
class OrderFilledData:
    """
    订单成交事件的标准化数据

    从各交易所的不同格式统一转换为此结构。
    """

    symbol: str                  # 交易对，如 BTCUSDT
    side: str                    # BUY / SELL
    order_type: str              # MARKET / LIMIT
    quantity: float              # 成交数量
    price: float                 # 成交均价
    quote_quantity: float        # 成交金额（USDT）
    original_order_id: str       # 原始订单ID
    trade_time: int              # 成交时间戳（毫秒）
    commission: float = 0.0      # 手续费
    commission_asset: str = ""   # 手续费资产

    def to_dict(self) -> dict[str, Any]:
        """转为字典"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "quote_quantity": self.quote_quantity,
            "original_order_id": self.original_order_id,
            "trade_time": self.trade_time,
            "commission": self.commission,
            "commission_asset": self.commission_asset,
        }


# ═══════════════════════════════════════════════════════════════
# 订阅器抽象基类
# ═══════════════════════════════════════════════════════════════


class SignalSubscriber(ABC):
    """
    信号订阅器抽象基类

    所有希望接收信号事件的组件都必须实现此接口。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """订阅器名称，用于日志标识"""
        ...

    @abstractmethod
    async def on_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件

        Args:
            event: 信号事件对象
        """
        ...

    async def start(self) -> None:
        """启动订阅器（可选覆写，用于初始化资源）"""
        pass

    async def stop(self) -> None:
        """停止订阅器（可选覆写，用于释放资源）"""
        pass


# ═══════════════════════════════════════════════════════════════
# 事件总线核心
# ═══════════════════════════════════════════════════════════════


class SignalEventBus:
    """
    信号事件总线（Pub/Sub 中心）

    核心职责：
    1. 管理订阅器的注册 / 注销
    2. 将事件异步广播给所有已注册的订阅器
    3. 支持按信号ID过滤（订阅器可选择只关注特定信号源）

    设计特点：
    - 同一订阅器可以订阅多种事件类型
    - 同一事件类型可以有多个订阅器
    - 支持全局订阅（所有信号）和指定信号ID订阅
    - 事件分发采用 asyncio.gather 并发执行，互不阻塞
    - 单个订阅器异常不影响其他订阅器
    """

    def __init__(self) -> None:
        # 全局订阅映射：事件类型 → 订阅器列表（接收所有信号源的事件）
        self._global_subscribers: dict[SignalEventType, list[SignalSubscriber]] = defaultdict(list)

        # 信号级订阅映射：(事件类型, 信号ID) → 订阅器列表（只接收指定信号源的事件）
        self._signal_subscribers: dict[tuple[SignalEventType, int], list[SignalSubscriber]] = defaultdict(list)

        # 统计计数
        self._event_count: dict[SignalEventType, int] = defaultdict(int)
        self._error_count: int = 0
        self._total_published: int = 0

    # ── 订阅管理 ──────────────────────────────────────────────

    def subscribe(
        self,
        event_type: SignalEventType,
        subscriber: SignalSubscriber,
        signal_id: int | None = None,
    ) -> None:
        """
        注册订阅器

        Args:
            event_type: 要订阅的事件类型
            subscriber: 订阅器实例
            signal_id: 信号源ID（为 None 则订阅所有信号源的该类型事件）
        """
        if signal_id is None:
            if subscriber not in self._global_subscribers[event_type]:
                self._global_subscribers[event_type].append(subscriber)
                logger.info(
                    f"订阅器已注册(全局): {subscriber.name} → {event_type.name}"
                )
        else:
            key = (event_type, signal_id)
            if subscriber not in self._signal_subscribers[key]:
                self._signal_subscribers[key].append(subscriber)
                logger.info(
                    f"订阅器已注册(信号级): {subscriber.name} → {event_type.name} signal_id={signal_id}"
                )

    def subscribe_many(
        self,
        event_types: list[SignalEventType],
        subscriber: SignalSubscriber,
        signal_id: int | None = None,
    ) -> None:
        """批量注册订阅器到多个事件类型"""
        for event_type in event_types:
            self.subscribe(event_type, subscriber, signal_id)

    def unsubscribe(
        self,
        event_type: SignalEventType,
        subscriber: SignalSubscriber,
        signal_id: int | None = None,
    ) -> None:
        """注销订阅器"""
        if signal_id is None:
            if subscriber in self._global_subscribers[event_type]:
                self._global_subscribers[event_type].remove(subscriber)
                logger.info(f"订阅器已注销(全局): {subscriber.name} ← {event_type.name}")
        else:
            key = (event_type, signal_id)
            if subscriber in self._signal_subscribers[key]:
                self._signal_subscribers[key].remove(subscriber)
                logger.info(
                    f"订阅器已注销(信号级): {subscriber.name} ← {event_type.name} signal_id={signal_id}"
                )

    def unsubscribe_all(self, subscriber: SignalSubscriber) -> None:
        """从所有事件类型中注销指定订阅器"""
        for event_type in list(self._global_subscribers.keys()):
            if subscriber in self._global_subscribers[event_type]:
                self._global_subscribers[event_type].remove(subscriber)

        for key in list(self._signal_subscribers.keys()):
            if subscriber in self._signal_subscribers[key]:
                self._signal_subscribers[key].remove(subscriber)

        logger.info(f"订阅器已从所有事件注销: {subscriber.name}")

    def unsubscribe_signal(self, signal_id: int) -> None:
        """注销指定信号源的所有订阅"""
        keys_to_remove = [key for key in self._signal_subscribers if key[1] == signal_id]
        for key in keys_to_remove:
            subscribers = self._signal_subscribers.pop(key, [])
            for s in subscribers:
                logger.info(
                    f"订阅器已注销(信号移除): {s.name} ← {key[0].name} signal_id={signal_id}"
                )

    # ── 事件发布 ──────────────────────────────────────────────

    async def publish(self, event: SignalEvent) -> None:
        """
        发布信号事件

        将事件异步分发给：
        1. 所有全局订阅了该事件类型的订阅器
        2. 所有订阅了该事件类型 + 该信号ID 的订阅器

        Args:
            event: 信号事件
        """
        self._total_published += 1
        self._event_count[event.type] += 1

        # 收集所有目标订阅器
        targets: list[SignalSubscriber] = []

        # 全局订阅器
        targets.extend(self._global_subscribers.get(event.type, []))

        # 信号级订阅器
        key = (event.type, event.signal_id)
        targets.extend(self._signal_subscribers.get(key, []))

        if not targets:
            return

        # 去重（同一订阅器可能同时是全局和信号级）
        seen: set[str] = set()
        unique_targets: list[SignalSubscriber] = []
        for t in targets:
            if t.name not in seen:
                seen.add(t.name)
                unique_targets.append(t)

        # 并发分发给所有订阅器
        results = await asyncio.gather(
            *[self._safe_dispatch(subscriber, event) for subscriber in unique_targets],
            return_exceptions=True,
        )

        # 统计错误
        for result in results:
            if isinstance(result, Exception):
                self._error_count += 1

    async def _safe_dispatch(
        self,
        subscriber: SignalSubscriber,
        event: SignalEvent,
    ) -> None:
        """安全地将事件分发给单个订阅器"""
        try:
            await subscriber.on_signal_event(event)
        except Exception as e:
            logger.error(
                f"订阅器处理事件失败: subscriber={subscriber.name}, "
                f"event_type={event.type.name}, signal_id={event.signal_id}, "
                f"error={e}",
                exc_info=True,
            )
            raise

    # ── 状态查询 ──────────────────────────────────────────────

    @property
    def stats(self) -> dict[str, Any]:
        """获取事件总线统计信息"""
        subscriber_names: set[str] = set()
        for subscribers in self._global_subscribers.values():
            for subscriber in subscribers:
                subscriber_names.add(subscriber.name)
        for subscribers in self._signal_subscribers.values():
            for subscriber in subscribers:
                subscriber_names.add(subscriber.name)

        # 统计每个信号源的订阅数
        signal_subscriptions: dict[int, int] = defaultdict(int)
        for (_, signal_id), subscribers in self._signal_subscribers.items():
            signal_subscriptions[signal_id] += len(subscribers)

        return {
            "total_published": self._total_published,
            "event_counts": {
                event_type.name: count
                for event_type, count in self._event_count.items()
            },
            "error_count": self._error_count,
            "subscriber_count": len(subscriber_names),
            "subscribers": sorted(subscriber_names),
            "signal_subscriptions": dict(signal_subscriptions),
        }


