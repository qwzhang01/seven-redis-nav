"""
消息总线模块
============

基于 Redis Streams 和 Kafka 的消息总线实现，支持：
- 发布/订阅模式
- 消息持久化
- 消息回放
- 分布式消息传递
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)


class MessageType(Enum):
    """消息类型"""
    
    # 行情消息
    TICK = "tick"
    BAR = "bar"
    DEPTH = "depth"
    
    # 交易消息
    ORDER = "order"
    TRADE = "trade"
    POSITION = "position"
    
    # 策略消息
    SIGNAL = "signal"
    
    # 系统消息
    HEARTBEAT = "heartbeat"
    COMMAND = "command"


@dataclass
class Message:
    """消息基类"""
    
    topic: str
    type: MessageType
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: str = ""
    source: str = ""
    
    def __post_init__(self) -> None:
        if not self.message_id:
            self.message_id = f"{self.topic}_{self.timestamp}_{id(self)}"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "source": self.source,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            topic=data["topic"],
            type=MessageType(data["type"]),
            data=data["data"],
            timestamp=data.get("timestamp", time.time()),
            message_id=data.get("message_id", ""),
            source=data.get("source", ""),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        return cls.from_dict(json.loads(json_str))


# 消息处理器类型
MessageHandler = Callable[[Message], Coroutine[Any, Any, None]]


class MessageBusBackend(ABC):
    """消息总线后端抽象基类"""
    
    @abstractmethod
    async def connect(self) -> None:
        """连接到消息中间件"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def publish(self, topic: str, message: Message) -> None:
        """发布消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """订阅主题"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """取消订阅"""
        pass


class InMemoryBackend(MessageBusBackend):
    """
    内存消息总线后端
    
    用于开发和测试环境
    """
    
    def __init__(self) -> None:
        self._subscribers: dict[str, list[MessageHandler]] = {}
        self._connected = False
        self._message_history: dict[str, list[Message]] = {}
        self._max_history_size = 10000
    
    async def connect(self) -> None:
        self._connected = True
        logger.info("InMemory message bus connected")
    
    async def disconnect(self) -> None:
        self._connected = False
        self._subscribers.clear()
        logger.info("InMemory message bus disconnected")
    
    async def publish(self, topic: str, message: Message) -> None:
        if not self._connected:
            raise RuntimeError("Message bus not connected")
        
        # 保存消息历史
        if topic not in self._message_history:
            self._message_history[topic] = []
        
        history = self._message_history[topic]
        history.append(message)
        
        # 限制历史大小
        if len(history) > self._max_history_size:
            self._message_history[topic] = history[-self._max_history_size:]
        
        # 分发消息
        handlers = self._subscribers.get(topic, [])
        if handlers:
            tasks = [self._safe_call(h, message) for h in handlers]
            await asyncio.gather(*tasks)
    
    async def _safe_call(self, handler: MessageHandler, message: Message) -> None:
        try:
            await handler(message)
        except Exception as e:
            logger.exception("Handler error", error=str(e), topic=message.topic)
    
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        if handler not in self._subscribers[topic]:
            self._subscribers[topic].append(handler)
            logger.debug(f"Subscribed to topic", topic=topic)
    
    async def unsubscribe(self, topic: str) -> None:
        if topic in self._subscribers:
            del self._subscribers[topic]
            logger.debug(f"Unsubscribed from topic", topic=topic)
    
    def get_history(self, topic: str, limit: int = 100) -> list[Message]:
        """获取消息历史"""
        history = self._message_history.get(topic, [])
        return history[-limit:]


class RedisStreamsBackend(MessageBusBackend):
    """
    Redis Streams 消息总线后端
    
    特性：
    - 消息持久化
    - 消费者组
    - 消息确认
    - 消息回放
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "",
        db: int = 0,
        consumer_group: str = "quant-trading",
        consumer_name: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name or f"consumer-{id(self)}"
        
        self._redis: Any = None
        self._connected = False
        self._subscribers: dict[str, MessageHandler] = {}
        self._consumer_tasks: dict[str, asyncio.Task[None]] = {}
        self._running = False
    
    async def connect(self) -> None:
        try:
            import redis.asyncio as redis
            
            self._redis = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password or None,
                db=self.db,
                decode_responses=True,
            )
            
            await self._redis.ping()
            self._connected = True
            self._running = True
            
            logger.info("Redis Streams message bus connected", 
                       host=self.host, 
                       port=self.port)
            
        except Exception as e:
            logger.error("Failed to connect Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        self._running = False
        
        # 取消所有消费者任务
        for task in self._consumer_tasks.values():
            task.cancel()
        
        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks.values(), return_exceptions=True)
        
        self._consumer_tasks.clear()
        
        if self._redis:
            await self._redis.close()
        
        self._connected = False
        logger.info("Redis Streams message bus disconnected")
    
    async def publish(self, topic: str, message: Message) -> None:
        if not self._connected:
            raise RuntimeError("Message bus not connected")
        
        stream_key = f"stream:{topic}"
        
        try:
            await self._redis.xadd(
                stream_key,
                {"data": message.to_json()},
                maxlen=100000,  # 限制 stream 长度
            )
        except Exception as e:
            logger.error("Failed to publish message", 
                        error=str(e), 
                        topic=topic)
            raise
    
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        if topic in self._subscribers:
            logger.warning(f"Already subscribed to topic", topic=topic)
            return
        
        self._subscribers[topic] = handler
        stream_key = f"stream:{topic}"
        
        # 创建消费者组
        try:
            await self._redis.xgroup_create(
                stream_key,
                self.consumer_group,
                id="0",
                mkstream=True,
            )
        except Exception as e:
            # 消费者组可能已存在
            if "BUSYGROUP" not in str(e):
                logger.error("Failed to create consumer group", error=str(e))
        
        # 启动消费者任务
        task = asyncio.create_task(
            self._consume_loop(topic, stream_key, handler),
            name=f"consumer-{topic}"
        )
        self._consumer_tasks[topic] = task
        
        logger.debug(f"Subscribed to topic", topic=topic)
    
    async def _consume_loop(
        self, 
        topic: str, 
        stream_key: str, 
        handler: MessageHandler
    ) -> None:
        """消费者循环"""
        while self._running:
            try:
                # 读取消息
                messages = await self._redis.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {stream_key: ">"},
                    count=100,
                    block=1000,
                )
                
                if not messages:
                    continue
                
                for stream, entries in messages:
                    for entry_id, entry_data in entries:
                        try:
                            msg_json = entry_data.get("data", "{}")
                            message = Message.from_json(msg_json)
                            await handler(message)
                            
                            # 确认消息
                            await self._redis.xack(
                                stream_key,
                                self.consumer_group,
                                entry_id,
                            )
                            
                        except Exception as e:
                            logger.exception("Message handling error", 
                                           error=str(e),
                                           topic=topic)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Consumer loop error", error=str(e), topic=topic)
                await asyncio.sleep(1)
    
    async def unsubscribe(self, topic: str) -> None:
        if topic in self._consumer_tasks:
            self._consumer_tasks[topic].cancel()
            try:
                await self._consumer_tasks[topic]
            except asyncio.CancelledError:
                pass
            del self._consumer_tasks[topic]
        
        if topic in self._subscribers:
            del self._subscribers[topic]
        
        logger.debug(f"Unsubscribed from topic", topic=topic)


class KafkaBackend(MessageBusBackend):
    """
    Kafka 消息总线后端
    
    特性：
    - 高吞吐量
    - 消息持久化
    - 分区和副本
    - 消费者组
    """
    
    def __init__(
        self,
        bootstrap_servers: list[str],
        client_id: str = "quant-trading",
        group_id: str = "quant-trading-group",
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.group_id = group_id
        
        self._producer: Any = None
        self._consumers: dict[str, Any] = {}
        self._connected = False
        self._consumer_tasks: dict[str, asyncio.Task[None]] = {}
        self._running = False
    
    async def connect(self) -> None:
        try:
            from aiokafka import AIOKafkaProducer
            
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                acks="all",
                compression_type="gzip",
            )
            
            await self._producer.start()
            self._connected = True
            self._running = True
            
            logger.info("Kafka message bus connected", 
                       servers=self.bootstrap_servers)
            
        except Exception as e:
            logger.error("Failed to connect Kafka", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        self._running = False
        
        # 停止所有消费者任务
        for task in self._consumer_tasks.values():
            task.cancel()
        
        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks.values(), return_exceptions=True)
        
        self._consumer_tasks.clear()
        
        # 停止消费者
        for consumer in self._consumers.values():
            await consumer.stop()
        
        self._consumers.clear()
        
        # 停止生产者
        if self._producer:
            await self._producer.stop()
        
        self._connected = False
        logger.info("Kafka message bus disconnected")
    
    async def publish(self, topic: str, message: Message) -> None:
        if not self._connected:
            raise RuntimeError("Message bus not connected")
        
        try:
            await self._producer.send_and_wait(
                topic,
                message.to_json().encode("utf-8"),
                key=message.source.encode("utf-8") if message.source else None,
            )
        except Exception as e:
            logger.error("Failed to publish message", 
                        error=str(e), 
                        topic=topic)
            raise
    
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        if topic in self._consumers:
            logger.warning(f"Already subscribed to topic", topic=topic)
            return
        
        try:
            from aiokafka import AIOKafkaConsumer
            
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="latest",
                enable_auto_commit=False,
            )
            
            await consumer.start()
            self._consumers[topic] = consumer
            
            # 启动消费者任务
            task = asyncio.create_task(
                self._consume_loop(topic, consumer, handler),
                name=f"kafka-consumer-{topic}"
            )
            self._consumer_tasks[topic] = task
            
            logger.debug(f"Subscribed to Kafka topic", topic=topic)
            
        except Exception as e:
            logger.error("Failed to subscribe", error=str(e), topic=topic)
            raise
    
    async def _consume_loop(
        self, 
        topic: str, 
        consumer: Any, 
        handler: MessageHandler
    ) -> None:
        """Kafka 消费者循环"""
        while self._running:
            try:
                async for msg in consumer:
                    try:
                        message = Message.from_json(msg.value.decode("utf-8"))
                        await handler(message)
                        await consumer.commit()
                    except Exception as e:
                        logger.exception("Message handling error",
                                        error=str(e),
                                        topic=topic)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Kafka consumer error", error=str(e), topic=topic)
                await asyncio.sleep(1)
    
    async def unsubscribe(self, topic: str) -> None:
        if topic in self._consumer_tasks:
            self._consumer_tasks[topic].cancel()
            try:
                await self._consumer_tasks[topic]
            except asyncio.CancelledError:
                pass
            del self._consumer_tasks[topic]
        
        if topic in self._consumers:
            await self._consumers[topic].stop()
            del self._consumers[topic]
        
        logger.debug(f"Unsubscribed from Kafka topic", topic=topic)


class MessageBus:
    """
    消息总线
    
    统一的消息总线接口，支持多种后端
    """
    
    def __init__(
        self,
        backend: MessageBusBackend | None = None,
    ) -> None:
        self._backend = backend or InMemoryBackend()
        self._connected = False
    
    async def connect(self) -> None:
        """连接到消息总线"""
        await self._backend.connect()
        self._connected = True
    
    async def disconnect(self) -> None:
        """断开连接"""
        await self._backend.disconnect()
        self._connected = False
    
    async def publish(
        self, 
        topic: str, 
        data: dict[str, Any],
        msg_type: MessageType = MessageType.COMMAND,
        source: str = "",
    ) -> None:
        """发布消息"""
        message = Message(
            topic=topic,
            type=msg_type,
            data=data,
            source=source,
        )
        await self._backend.publish(topic, message)
    
    async def publish_message(self, message: Message) -> None:
        """发布消息对象"""
        await self._backend.publish(message.topic, message)
    
    async def subscribe(self, topic: str, handler: MessageHandler) -> None:
        """订阅主题"""
        await self._backend.subscribe(topic, handler)
    
    async def unsubscribe(self, topic: str) -> None:
        """取消订阅"""
        await self._backend.unsubscribe(topic)
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @classmethod
    def create_redis_bus(
        cls,
        host: str = "localhost",
        port: int = 6379,
        password: str = "",
        consumer_group: str = "quant-trading",
    ) -> "MessageBus":
        """创建 Redis Streams 消息总线"""
        backend = RedisStreamsBackend(
            host=host,
            port=port,
            password=password,
            consumer_group=consumer_group,
        )
        return cls(backend=backend)
    
    @classmethod
    def create_kafka_bus(
        cls,
        bootstrap_servers: list[str],
        client_id: str = "quant-trading",
        group_id: str = "quant-trading-group",
    ) -> "MessageBus":
        """创建 Kafka 消息总线"""
        backend = KafkaBackend(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            group_id=group_id,
        )
        return cls(backend=backend)
