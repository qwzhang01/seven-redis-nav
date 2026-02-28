"""
事件引擎模块
============

实现高性能的事件驱动架构，支持：
- 异步事件处理
- 事件优先级队列
- 事件过滤和路由
- 事件持久化
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)

def get_event_engine(
    queue_size: int = 100000,
    num_workers: int = 4,
    name: str = "MainEventEngine"
) -> "EventEngine":
    """
    获取EventEngine单例实例

    委托到 ServiceContainer 统一管理。

    Args:
        queue_size: 事件队列大小
        num_workers: 工作协程数量
        name: 事件引擎名称

    Returns:
        EventEngine实例
    """
    from quant_trading_system.core.container import container

    if container._event_engine is None:
        container.event_engine = EventEngine(
            queue_size=queue_size,
            num_workers=num_workers,
            name=name,
        )

    return container.event_engine


class EventType(Enum):
    """事件类型枚举"""

    # 系统事件
    SYSTEM_START = auto()
    SYSTEM_STOP = auto()
    SYSTEM_ERROR = auto()
    SYSTEM_HEARTBEAT = auto()

    # 行情事件
    TICK = auto()
    BAR = auto()
    DEPTH = auto()
    TRADE_TICK = auto()

    # 交易事件
    ORDER = auto()
    ORDER_SUBMITTED = auto()
    ORDER_ACCEPTED = auto()
    ORDER_REJECTED = auto()
    ORDER_CANCELLED = auto()
    ORDER_FILLED = auto()
    ORDER_PARTIAL_FILLED = auto()

    # 持仓事件
    POSITION = auto()
    POSITION_UPDATE = auto()

    # 账户事件
    ACCOUNT = auto()
    ACCOUNT_UPDATE = auto()

    # 策略事件
    STRATEGY_START = auto()
    STRATEGY_STOP = auto()
    STRATEGY_PAUSE = auto()
    STRATEGY_RESUME = auto()
    SIGNAL = auto()

    # 风控事件
    RISK_WARNING = auto()
    RISK_ALERT = auto()
    RISK_BREACH = auto()

    # 日志事件
    LOG = auto()

    # 定时事件
    TIMER = auto()


class EventPriority(Enum):
    """事件优先级"""

    CRITICAL = 0  # 最高优先级（风控、系统错误）
    HIGH = 1      # 高优先级（订单执行）
    NORMAL = 2    # 普通优先级（行情数据）
    LOW = 3       # 低优先级（日志、统计）


@dataclass
class Event:
    """事件基类"""

    type: EventType
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    priority: EventPriority = EventPriority.NORMAL
    event_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = f"{self.type.name}_{self.timestamp}_{id(self)}"

    def __lt__(self, other: "Event") -> bool:
        """用于优先级队列比较"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.timestamp < other.timestamp


# 事件处理器类型
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]
SyncEventHandler = Callable[[Event], None]


class EventEngine:
    """
    异步事件引擎

    特性：
    - 支持异步和同步事件处理器
    - 支持事件优先级队列
    - 支持事件过滤
    - 支持事件广播
    - 线程安全
    """

    def __init__(
        self,
        queue_size: int = 100000,
        num_workers: int = 4,
        name: str = "EventEngine",
    ) -> None:
        self.name = name
        self._queue_size = queue_size
        self.num_workers = num_workers

        # 事件队列（优先级队列）
        self._queue: asyncio.PriorityQueue[tuple[int, float, Event]] | None = None

        # 事件处理器映射
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._sync_handlers: dict[EventType, list[SyncEventHandler]] = defaultdict(list)

        # 通用处理器（接收所有事件）
        self._general_handlers: list[EventHandler] = []
        self._general_sync_handlers: list[SyncEventHandler] = []

        # 工作协程
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

        # 统计信息
        self._event_count: dict[EventType, int] = defaultdict(int)
        self._total_events = 0
        self._processed_events = 0
        self._start_time: float = 0

        # 事件过滤器
        self._filters: dict[EventType, list[Callable[[Event], bool]]] = defaultdict(list)

        logger.info(f"EventEngine {name} initialized",
                   queue_size=queue_size,
                   num_workers=num_workers)

    async def start(self) -> None:
        """启动事件引擎"""
        if self._running:
            logger.warning(f"EventEngine {self.name} already running")
            return

        self._running = True
        self._start_time = time.time()
        self._queue = asyncio.PriorityQueue(maxsize=self._queue_size)

        # 启动工作协程
        for i in range(self.num_workers):
            worker = asyncio.create_task(
                self._worker(f"worker-{i}"),
                name=f"{self.name}-worker-{i}"
            )
            self._workers.append(worker)

        logger.info(f"EventEngine {self.name} started", workers=self.num_workers)

        # 发送系统启动事件
        await self.put(Event(type=EventType.SYSTEM_START, source=self.name))

    async def stop(self) -> None:
        """停止事件引擎"""
        if not self._running:
            return

        logger.info(f"Stopping EventEngine {self.name}")

        # 发送系统停止事件
        await self.put(Event(
            type=EventType.SYSTEM_STOP,
            source=self.name,
            priority=EventPriority.CRITICAL
        ))

        # 等待队列清空
        if self._queue:
            await self._queue.join()

        self._running = False

        # 取消所有工作协程
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info(
            f"EventEngine {self.name} stopped",
            total_events=self._total_events,
            processed_events=self._processed_events,
            uptime=time.time() - self._start_time
        )

    async def _worker(self, worker_name: str) -> None:
        """事件处理工作协程"""
        logger.debug(f"Worker {worker_name} started")

        while self._running:
            try:
                if self._queue is None:
                    await asyncio.sleep(0.01)
                    continue

                # 从队列获取事件
                _, _, event = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )

                try:
                    await self._process_event(event)
                    self._processed_events += 1
                finally:
                    self._queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Worker {worker_name} error", error=str(e))

        logger.debug(f"Worker {worker_name} stopped")

    async def _process_event(self, event: Event) -> None:
        """处理单个事件"""
        event_type = event.type

        # 应用过滤器
        filters = self._filters.get(event_type, [])
        for filter_func in filters:
            try:
                if not filter_func(event):
                    logger.debug(f"Event filtered out", event_type=event_type.name)
                    return
            except Exception as e:
                logger.error(f"Filter error", error=str(e), event_type=event_type.name)

        # 处理特定类型的处理器
        handlers = self._handlers.get(event_type, [])
        sync_handlers = self._sync_handlers.get(event_type, [])

        # 异步处理器并发执行
        if handlers:
            tasks = [self._safe_call_handler(h, event) for h in handlers]
            await asyncio.gather(*tasks)

        # 同步处理器顺序执行
        for handler in sync_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception(f"Sync handler error",
                               error=str(e),
                               event_type=event_type.name)

        # 处理通用处理器
        if self._general_handlers:
            tasks = [self._safe_call_handler(h, event) for h in self._general_handlers]
            await asyncio.gather(*tasks)

        for handler in self._general_sync_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.exception(f"General sync handler error", error=str(e))

    async def _safe_call_handler(
        self,
        handler: EventHandler,
        event: Event
    ) -> None:
        """安全调用异步处理器"""
        try:
            await handler(event)
        except Exception as e:
            logger.exception(
                f"Handler error",
                error=str(e),
                handler=handler.__name__,
                event_type=event.type.name
            )

    async def put(self, event: Event) -> None:
        """添加事件到队列"""
        if not self._running or self._queue is None:
            logger.warning(f"EventEngine not running, event dropped",
                          event_type=event.type.name)
            return

        try:
            # 使用优先级和时间戳排序
            priority_tuple = (event.priority.value, event.timestamp, event)
            await self._queue.put(priority_tuple)

            self._total_events += 1
            self._event_count[event.type] += 1

        except asyncio.QueueFull:
            logger.error(f"Event queue full, event dropped",
                        event_type=event.type.name)

    def put_nowait(self, event: Event) -> bool:
        """非阻塞添加事件"""
        if not self._running or self._queue is None:
            return False

        try:
            priority_tuple = (event.priority.value, event.timestamp, event)
            self._queue.put_nowait(priority_tuple)

            self._total_events += 1
            self._event_count[event.type] += 1
            return True

        except asyncio.QueueFull:
            logger.error(f"Event queue full", event_type=event.type.name)
            return False

    def register(
        self,
        event_type: EventType,
        handler: EventHandler | SyncEventHandler,
        is_async: bool = True
    ) -> None:
        """注册事件处理器"""
        if is_async:
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)  # type: ignore
                logger.debug(f"Registered async handler",
                           event_type=event_type.name,
                           handler=handler.__name__)
        else:
            if handler not in self._sync_handlers[event_type]:
                self._sync_handlers[event_type].append(handler)  # type: ignore
                logger.debug(f"Registered sync handler",
                           event_type=event_type.name,
                           handler=handler.__name__)

    def unregister(
        self,
        event_type: EventType,
        handler: EventHandler | SyncEventHandler
    ) -> None:
        """注销事件处理器"""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)  # type: ignore
        if handler in self._sync_handlers[event_type]:
            self._sync_handlers[event_type].remove(handler)  # type: ignore

    def register_general(
        self,
        handler: EventHandler | SyncEventHandler,
        is_async: bool = True
    ) -> None:
        """注册通用处理器（接收所有事件）"""
        if is_async:
            if handler not in self._general_handlers:
                self._general_handlers.append(handler)  # type: ignore
        else:
            if handler not in self._general_sync_handlers:
                self._general_sync_handlers.append(handler)  # type: ignore

    def add_filter(
        self,
        event_type: EventType,
        filter_func: Callable[[Event], bool]
    ) -> None:
        """添加事件过滤器"""
        self._filters[event_type].append(filter_func)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        if self._queue is None:
            return 0
        return self._queue.qsize()

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "name": self.name,
            "running": self._running,
            "total_events": self._total_events,
            "processed_events": self._processed_events,
            "pending_events": self.queue_size,
            "uptime": uptime,
            "events_per_second": self._total_events / uptime if uptime > 0 else 0,
            "event_counts": dict(self._event_count),
        }
