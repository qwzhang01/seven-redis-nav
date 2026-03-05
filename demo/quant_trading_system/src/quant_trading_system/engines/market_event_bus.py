"""
行情事件总线
============

实现发布/订阅（Pub/Sub）模式的行情事件分发机制。

设计模式：
- 观察者模式（Observer Pattern）：订阅器订阅感兴趣的事件类型
- 中介者模式（Mediator Pattern）：事件总线作为中介，解耦数据生产者和消费者
- 策略模式（Strategy Pattern）：不同订阅器以不同策略处理相同事件

核心职责：
- 定义统一的行情事件类型和数据结构
- 管理订阅器的注册和注销
- 将行情事件异步分发给所有订阅器
- 事件生产者（交易所连接层）只需发布事件，不关心消费逻辑

使用方式：
    bus = MarketEventBus()
    bus.subscribe(MarketEventType.KLINE, my_subscriber)
    await bus.publish(MarketEvent(type=MarketEventType.KLINE, data={...}))
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 事件类型定义
# ═══════════════════════════════════════════════════════════════

class MarketEventType(Enum):
    """
    行情事件类型枚举

    分为两大类：
    1. 实时行情事件 —— 来自交易所 WebSocket 推送
    2. 历史数据事件 —— 来自 REST API 拉取的历史数据
    """

    # ── 实时行情事件 ──
    TICK = auto()           # 逐笔成交 / Ticker
    KLINE = auto()          # K线数据（含实时未闭合和已闭合）
    DEPTH = auto()          # 买卖盘深度数据

    # ── 历史数据事件 ──
    HISTORICAL_KLINE = auto()   # 历史K线数据批次（由历史同步器发布）

    # ── 系统事件 ──
    CONNECTED = auto()      # 交易所连接成功
    DISCONNECTED = auto()   # 交易所断开连接
    ERROR = auto()          # 错误事件


# ═══════════════════════════════════════════════════════════════
# 事件数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class MarketEvent:
    """
    行情事件

    所有通过事件总线传递的行情数据统一封装为此对象。
    """

    type: MarketEventType           # 事件类型
    data: dict[str, Any]            # 事件数据（统一为 dict 格式）
    exchange: str = ""              # 来源交易所
    symbol: str = ""                # 交易对
    timestamp: float = field(default_factory=lambda: time.time() * 1000)  # 事件时间戳（毫秒）

    def __repr__(self) -> str:
        return (
            f"MarketEvent(type={self.type.name}, exchange={self.exchange}, "
            f"symbol={self.symbol}, data_keys={list(self.data.keys())})"
        )


# ═══════════════════════════════════════════════════════════════
# 订阅器抽象基类
# ═══════════════════════════════════════════════════════════════

class MarketSubscriber(ABC):
    """
    行情订阅器抽象基类

    所有希望接收行情事件的组件都必须实现此接口。
    每个订阅器通过 `on_event` 方法异步处理事件，
    具体处理逻辑由各子类自行实现（策略模式）。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """订阅器名称，用于日志标识"""
        ...

    @abstractmethod
    async def on_event(self, event: MarketEvent) -> None:
        """
        处理行情事件

        Args:
            event: 行情事件对象
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

class MarketEventBus:
    """
    行情事件总线（Pub/Sub 中心）

    核心职责：
    1. 管理订阅器的注册 / 注销
    2. 将事件异步广播给所有已注册的订阅器
    3. 提供事件统计信息

    设计特点：
    - 同一订阅器可以订阅多种事件类型
    - 同一事件类型可以有多个订阅器
    - 事件分发采用 asyncio.gather 并发执行，互不阻塞
    - 单个订阅器异常不影响其他订阅器
    """

    def __init__(self) -> None:
        # 订阅映射：事件类型 → 订阅器列表
        self._subscribers: dict[MarketEventType, list[MarketSubscriber]] = defaultdict(list)

        # 统计计数
        self._event_count: dict[MarketEventType, int] = defaultdict(int)
        self._error_count: int = 0
        self._total_published: int = 0

    def subscribe(
        self,
        event_type: MarketEventType,
        subscriber: MarketSubscriber,
    ) -> None:
        """
        注册订阅器

        Args:
            event_type: 要订阅的事件类型
            subscriber: 订阅器实例
        """
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)
            logger.info(
                "订阅器已注册",
                subscriber=subscriber.name,
                event_type=event_type.name,
            )

    def subscribe_many(
        self,
        event_types: list[MarketEventType],
        subscriber: MarketSubscriber,
    ) -> None:
        """
        批量注册订阅器到多个事件类型

        Args:
            event_types: 要订阅的事件类型列表
            subscriber: 订阅器实例
        """
        for event_type in event_types:
            self.subscribe(event_type, subscriber)

    def unsubscribe(
        self,
        event_type: MarketEventType,
        subscriber: MarketSubscriber,
    ) -> None:
        """
        注销订阅器

        Args:
            event_type: 事件类型
            subscriber: 订阅器实例
        """
        if subscriber in self._subscribers[event_type]:
            self._subscribers[event_type].remove(subscriber)
            logger.info(
                "订阅器已注销",
                subscriber=subscriber.name,
                event_type=event_type.name,
            )

    def unsubscribe_all(self, subscriber: MarketSubscriber) -> None:
        """
        从所有事件类型中注销指定订阅器

        Args:
            subscriber: 订阅器实例
        """
        for event_type in list(self._subscribers.keys()):
            if subscriber in self._subscribers[event_type]:
                self._subscribers[event_type].remove(subscriber)

        logger.info("订阅器已从所有事件注销", subscriber=subscriber.name)

    async def publish(self, event: MarketEvent) -> None:
        """
        发布行情事件

        将事件异步分发给所有订阅了该事件类型的订阅器。
        单个订阅器处理失败不影响其他订阅器。

        Args:
            event: 行情事件
        """
        self._total_published += 1
        self._event_count[event.type] += 1

        subscribers = self._subscribers.get(event.type, [])
        if not subscribers:
            return

        # 并发分发给所有订阅器
        results = await asyncio.gather(
            *[self._safe_dispatch(subscriber, event) for subscriber in subscribers],
            return_exceptions=True,
        )

        # 统计错误
        for result in results:
            if isinstance(result, Exception):
                self._error_count += 1

    async def _safe_dispatch(
        self,
        subscriber: MarketSubscriber,
        event: MarketEvent,
    ) -> None:
        """
        安全地将事件分发给单个订阅器

        捕获并记录异常，不让单个订阅器的错误影响整体分发。
        """
        try:
            await subscriber.on_event(event)
        except Exception as e:
            logger.error(
                "订阅器处理事件失败",
                subscriber=subscriber.name,
                event_type=event.type.name,
                symbol=event.symbol,
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

    async def start_all_subscribers(self) -> None:
        """启动所有已注册的订阅器"""
        seen: set[str] = set()
        for subscribers in self._subscribers.values():
            for subscriber in subscribers:
                if subscriber.name not in seen:
                    seen.add(subscriber.name)
                    try:
                        await subscriber.start()
                        logger.info("订阅器已启动", subscriber=subscriber.name)
                    except Exception as e:
                        logger.error(
                            "订阅器启动失败",
                            subscriber=subscriber.name,
                            exc_info=True,
                        )

    async def stop_all_subscribers(self) -> None:
        """停止所有已注册的订阅器"""
        seen: set[str] = set()
        for subscribers in self._subscribers.values():
            for subscriber in subscribers:
                if subscriber.name not in seen:
                    seen.add(subscriber.name)
                    try:
                        await subscriber.stop()
                        logger.info("订阅器已停止", subscriber=subscriber.name)
                    except Exception as e:
                        logger.error(
                            "订阅器停止失败",
                            subscriber=subscriber.name,
                            exc_info=True,
                        )

    def get_subscribers(self, event_type: MarketEventType) -> list[MarketSubscriber]:
        """获取指定事件类型的所有订阅器"""
        return list(self._subscribers.get(event_type, []))

    @property
    def stats(self) -> dict[str, Any]:
        """获取事件总线统计信息"""
        subscriber_names: set[str] = set()
        for subscribers in self._subscribers.values():
            for subscriber in subscribers:
                subscriber_names.add(subscriber.name)

        return {
            "total_published": self._total_published,
            "event_counts": {
                event_type.name: count
                for event_type, count in self._event_count.items()
            },
            "error_count": self._error_count,
            "subscriber_count": len(subscriber_names),
            "subscribers": list(subscriber_names),
            "subscriptions": {
                event_type.name: [s.name for s in subscribers]
                for event_type, subscribers in self._subscribers.items()
                if subscribers
            },
        }
