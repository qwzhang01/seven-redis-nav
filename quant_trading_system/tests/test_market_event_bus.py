"""
MarketEventBus 单元测试
====================

测试行情事件总线的核心功能：
- 订阅器注册与注销
- 事件发布与分发
- 多事件类型订阅
- 异常处理
- 统计信息
- 订阅器生命周期管理
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
    MarketSubscriber,
)


# ============================
# 测试订阅器实现
# ============================

class TestSubscriber(MarketSubscriber):
    """用于测试的订阅器实现"""

    def __init__(self, name: str = "TestSubscriber"):
        self._name = name
        self.received_events: list[MarketEvent] = []
        self.start_called = False
        self.stop_called = False

    @property
    def name(self) -> str:
        return self._name

    async def on_event(self, event: MarketEvent) -> None:
        self.received_events.append(event)

    async def start(self) -> None:
        self.start_called = True

    async def stop(self) -> None:
        self.stop_called = True


# ============================
# Fixtures
# ============================

@pytest.fixture
def bus():
    """创建一个测试用的 MarketEventBus 实例"""
    return MarketEventBus()


@pytest.fixture
def tick_event():
    """创建一个 TICK 事件"""
    return MarketEvent(
        type=MarketEventType.TICK,
        data={"price": 150.0, "volume": 1000},
        exchange="binance",
        symbol="BTCUSDT",
    )


@pytest.fixture
def kline_event():
    """创建一个 KLINE 事件"""
    return MarketEvent(
        type=MarketEventType.KLINE,
        data={"open": 148.0, "high": 152.0, "low": 147.0, "close": 151.0},
        exchange="okx",
        symbol="ETHUSDT",
    )


# ============================
# 订阅器注册与注销测试
# ============================

class TestSubscriptionManagement:
    """测试订阅器的注册和注销功能"""

    def test_subscribe_single_event_type(self, bus: MarketEventBus):
        """测试订阅单个事件类型"""
        subscriber = TestSubscriber()

        bus.subscribe(MarketEventType.TICK, subscriber)

        subscribers = bus.get_subscribers(MarketEventType.TICK)
        assert subscriber in subscribers
        assert len(subscribers) == 1

    def test_subscribe_multiple_event_types(self, bus: MarketEventBus):
        """测试订阅多个事件类型"""
        subscriber = TestSubscriber()

        bus.subscribe_many([MarketEventType.TICK, MarketEventType.KLINE], subscriber)

        tick_subscribers = bus.get_subscribers(MarketEventType.TICK)
        kline_subscribers = bus.get_subscribers(MarketEventType.KLINE)

        assert subscriber in tick_subscribers
        assert subscriber in kline_subscribers

    def test_unsubscribe_single_event_type(self, bus: MarketEventBus):
        """测试注销单个事件类型的订阅"""
        subscriber = TestSubscriber()

        bus.subscribe(MarketEventType.TICK, subscriber)
        bus.unsubscribe(MarketEventType.TICK, subscriber)

        subscribers = bus.get_subscribers(MarketEventType.TICK)
        assert subscriber not in subscribers
        assert len(subscribers) == 0

    def test_unsubscribe_all_event_types(self, bus: MarketEventBus):
        """测试注销所有事件类型的订阅"""
        subscriber = TestSubscriber()

        bus.subscribe(MarketEventType.TICK, subscriber)
        bus.subscribe(MarketEventType.KLINE, subscriber)
        bus.unsubscribe_all(subscriber)

        tick_subscribers = bus.get_subscribers(MarketEventType.TICK)
        kline_subscribers = bus.get_subscribers(MarketEventType.KLINE)

        assert subscriber not in tick_subscribers
        assert subscriber not in kline_subscribers

    def test_duplicate_subscription_ignored(self, bus: MarketEventBus):
        """测试重复订阅同一事件类型会被忽略"""
        subscriber = TestSubscriber()

        bus.subscribe(MarketEventType.TICK, subscriber)
        bus.subscribe(MarketEventType.TICK, subscriber)  # 重复订阅

        subscribers = bus.get_subscribers(MarketEventType.TICK)
        assert len(subscribers) == 1  # 只注册一次

    def test_multiple_subscribers_same_event_type(self, bus: MarketEventBus):
        """测试同一事件类型可以有多个订阅器"""
        subscriber1 = TestSubscriber("Subscriber1")
        subscriber2 = TestSubscriber("Subscriber2")

        bus.subscribe(MarketEventType.TICK, subscriber1)
        bus.subscribe(MarketEventType.TICK, subscriber2)

        subscribers = bus.get_subscribers(MarketEventType.TICK)
        assert len(subscribers) == 2
        assert subscriber1 in subscribers
        assert subscriber2 in subscribers


# ============================
# 事件发布与分发测试
# ============================

class TestEventPublishing:
    """测试事件发布和分发功能"""

    async def test_publish_to_single_subscriber(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试发布事件到单个订阅器"""
        subscriber = TestSubscriber()
        bus.subscribe(MarketEventType.TICK, subscriber)

        await bus.publish(tick_event)

        assert len(subscriber.received_events) == 1
        assert subscriber.received_events[0] == tick_event

    async def test_publish_to_multiple_subscribers(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试发布事件到多个订阅器"""
        subscriber1 = TestSubscriber("Subscriber1")
        subscriber2 = TestSubscriber("Subscriber2")

        bus.subscribe(MarketEventType.TICK, subscriber1)
        bus.subscribe(MarketEventType.TICK, subscriber2)

        await bus.publish(tick_event)

        assert len(subscriber1.received_events) == 1
        assert len(subscriber2.received_events) == 1
        assert subscriber1.received_events[0] == tick_event
        assert subscriber2.received_events[0] == tick_event

    async def test_publish_event_with_no_subscribers(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试发布事件时没有订阅器（不应报错）"""
        # 没有订阅 TICK 事件的订阅器
        await bus.publish(tick_event)

        # 不应抛出异常
        assert True

    async def test_subscriber_only_receives_subscribed_events(self, bus: MarketEventBus, tick_event: MarketEvent, kline_event: MarketEvent):
        """测试订阅器只接收订阅的事件类型"""
        tick_subscriber = TestSubscriber("TickSubscriber")
        kline_subscriber = TestSubscriber("KlineSubscriber")

        bus.subscribe(MarketEventType.TICK, tick_subscriber)
        bus.subscribe(MarketEventType.KLINE, kline_subscriber)

        # 发布两个不同类型的事件
        await bus.publish(tick_event)
        await bus.publish(kline_event)

        # 每个订阅器只应收到自己订阅的事件
        assert len(tick_subscriber.received_events) == 1
        assert len(kline_subscriber.received_events) == 1
        assert tick_subscriber.received_events[0].type == MarketEventType.TICK
        assert kline_subscriber.received_events[0].type == MarketEventType.KLINE

    async def test_concurrent_event_publishing(self, bus: MarketEventBus):
        """测试并发事件发布"""
        subscriber = TestSubscriber()
        bus.subscribe(MarketEventType.TICK, subscriber)

        # 创建多个事件
        events = [
            MarketEvent(
                type=MarketEventType.TICK,
                data={"price": 150 + i, "volume": 1000 + i},
                exchange="binance",
                symbol="BTCUSDT",
            )
            for i in range(10)
        ]

        # 并发发布所有事件
        tasks = [bus.publish(event) for event in events]
        await asyncio.gather(*tasks)

        assert len(subscriber.received_events) == 10

        # 验证所有事件都被接收
        received_prices = [event.data["price"] for event in subscriber.received_events]
        expected_prices = list(range(150, 160))
        assert sorted(received_prices) == expected_prices


# ============================
# 异常处理测试
# ============================

class TestErrorHandling:
    """测试异常处理机制"""

    async def test_subscriber_exception_does_not_affect_others(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试订阅器异常不影响其他订阅器"""
        good_subscriber = TestSubscriber("GoodSubscriber")
        bad_subscriber = Mock(spec=MarketSubscriber)
        bad_subscriber.name = "BadSubscriber"
        bad_subscriber.on_event = AsyncMock(side_effect=Exception("模拟异常"))

        bus.subscribe(MarketEventType.TICK, good_subscriber)
        bus.subscribe(MarketEventType.TICK, bad_subscriber)

        # 发布事件，bad_subscriber 会抛出异常
        await bus.publish(tick_event)

        # good_subscriber 应正常接收事件
        assert len(good_subscriber.received_events) == 1
        assert good_subscriber.received_events[0] == tick_event

        # bad_subscriber 的 on_event 应被调用
        bad_subscriber.on_event.assert_called_once()

    async def test_subscriber_start_stop_exception_handling(self, bus: MarketEventBus):
        """测试订阅器启动/停止异常处理"""
        normal_subscriber = TestSubscriber("NormalSubscriber")

        bad_subscriber = Mock(spec=MarketSubscriber)
        bad_subscriber.name = "BadSubscriber"
        bad_subscriber.start = AsyncMock(side_effect=Exception("启动失败"))
        bad_subscriber.stop = AsyncMock(side_effect=Exception("停止失败"))

        bus.subscribe(MarketEventType.TICK, normal_subscriber)
        bus.subscribe(MarketEventType.TICK, bad_subscriber)

        # 启动所有订阅器
        await bus.start_all_subscribers()

        # 正常订阅器应被启动
        assert normal_subscriber.start_called

        # 停止所有订阅器
        await bus.stop_all_subscribers()

        # 正常订阅器应被停止
        assert normal_subscriber.stop_called


# ============================
# 订阅器生命周期测试
# ============================

class TestSubscriberLifecycle:
    """测试订阅器生命周期管理"""

    async def test_start_all_subscribers(self, bus: MarketEventBus):
        """测试启动所有订阅器"""
        subscriber1 = TestSubscriber("Subscriber1")
        subscriber2 = TestSubscriber("Subscriber2")

        bus.subscribe(MarketEventType.TICK, subscriber1)
        bus.subscribe(MarketEventType.KLINE, subscriber2)

        await bus.start_all_subscribers()

        assert subscriber1.start_called
        assert subscriber2.start_called

    async def test_stop_all_subscribers(self, bus: MarketEventBus):
        """测试停止所有订阅器"""
        subscriber1 = TestSubscriber("Subscriber1")
        subscriber2 = TestSubscriber("Subscriber2")

        bus.subscribe(MarketEventType.TICK, subscriber1)
        bus.subscribe(MarketEventType.KLINE, subscriber2)

        await bus.stop_all_subscribers()

        assert subscriber1.stop_called
        assert subscriber2.stop_called

    async def test_subscriber_lifecycle_with_events(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试完整的订阅器生命周期"""
        subscriber = TestSubscriber()
        bus.subscribe(MarketEventType.TICK, subscriber)

        # 启动订阅器
        await bus.start_all_subscribers()
        assert subscriber.start_called

        # 发布事件
        await bus.publish(tick_event)
        assert len(subscriber.received_events) == 1

        # 停止订阅器
        await bus.stop_all_subscribers()
        assert subscriber.stop_called


# ============================
# 统计信息测试
# ============================

class TestStatistics:
    """测试统计信息功能"""

    async def test_stats_after_publishing(self, bus: MarketEventBus, tick_event: MarketEvent, kline_event: MarketEvent):
        """测试发布事件后的统计信息"""
        subscriber1 = TestSubscriber("Subscriber1")
        subscriber2 = TestSubscriber("Subscriber2")

        bus.subscribe(MarketEventType.TICK, subscriber1)
        bus.subscribe(MarketEventType.KLINE, subscriber2)

        # 发布多个事件
        await bus.publish(tick_event)
        await bus.publish(kline_event)
        await bus.publish(tick_event)  # 再次发布 TICK

        stats = bus.stats

        assert stats["total_published"] == 3
        assert stats["event_counts"]["TICK"] == 2
        assert stats["event_counts"]["KLINE"] == 1
        assert stats["subscriber_count"] == 2
        assert "Subscriber1" in stats["subscribers"]
        assert "Subscriber2" in stats["subscribers"]

    async def test_error_count_statistics(self, bus: MarketEventBus, tick_event: MarketEvent):
        """测试错误计数统计"""
        bad_subscriber = Mock(spec=MarketSubscriber)
        bad_subscriber.name = "BadSubscriber"
        bad_subscriber.on_event = AsyncMock(side_effect=Exception("错误"))

        bus.subscribe(MarketEventType.TICK, bad_subscriber)

        # 发布事件，会触发异常
        await bus.publish(tick_event)

        stats = bus.stats
        assert stats["error_count"] == 1


# ============================
# MarketEvent 数据类测试
# ============================

class TestMarketEvent:
    """测试 MarketEvent 数据类"""

    def test_event_creation(self):
        """测试事件创建"""
        event = MarketEvent(
            type=MarketEventType.TICK,
            data={"price": 150.0, "volume": 1000},
            exchange="binance",
            symbol="BTCUSDT",
        )

        assert event.type == MarketEventType.TICK
        assert event.data["price"] == 150.0
        assert event.exchange == "binance"
        assert event.symbol == "BTCUSDT"
        assert event.timestamp > 0

    def test_event_repr(self):
        """测试事件字符串表示"""
        event = MarketEvent(
            type=MarketEventType.KLINE,
            data={"open": 148.0, "close": 151.0},
            exchange="okx",
            symbol="ETHUSDT",
        )

        repr_str = repr(event)
        assert "MarketEvent" in repr_str
        assert "KLINE" in repr_str
        assert "okx" in repr_str
        assert "ETHUSDT" in repr_str


# ============================
# 综合场景测试
# ============================

class TestIntegrationScenarios:
    """综合场景测试"""

    async def test_real_time_market_data_flow(self, bus: MarketEventBus):
        """
        模拟实时行情数据流：
        交易所连接 → 接收行情 → 分发给策略引擎
        """
        # 模拟策略引擎订阅器
        strategy_subscriber = TestSubscriber("StrategyEngine")

        # 模拟风控订阅器
        risk_subscriber = TestSubscriber("RiskEngine")

        # 策略订阅 TICK 和 KLINE
        bus.subscribe_many([MarketEventType.TICK, MarketEventType.KLINE], strategy_subscriber)

        # 风控订阅所有事件
        bus.subscribe_many(list(MarketEventType), risk_subscriber)

        # 启动所有订阅器
        await bus.start_all_subscribers()

        # 模拟交易所连接成功
        connected_event = MarketEvent(
            type=MarketEventType.CONNECTED,
            data={"exchange": "binance", "timestamp": 1234567890},
            exchange="binance",
        )
        await bus.publish(connected_event)

        # 模拟实时行情数据
        tick_event = MarketEvent(
            type=MarketEventType.TICK,
            data={"price": 50000.0, "volume": 1.5},
            exchange="binance",
            symbol="BTCUSDT",
        )
        await bus.publish(tick_event)

        kline_event = MarketEvent(
            type=MarketEventType.KLINE,
            data={"open": 49800.0, "high": 50200.0, "low": 49700.0, "close": 50100.0},
            exchange="binance",
            symbol="BTCUSDT",
        )
        await bus.publish(kline_event)

        # 停止所有订阅器
        await bus.stop_all_subscribers()

        # 验证结果
        # 策略引擎应收到 TICK 和 KLINE
        strategy_events = [e.type for e in strategy_subscriber.received_events]
        assert MarketEventType.TICK in strategy_events
        assert MarketEventType.KLINE in strategy_events

        # 风控引擎应收到所有事件
        risk_events = [e.type for e in risk_subscriber.received_events]
        assert MarketEventType.CONNECTED in risk_events
        assert MarketEventType.TICK in risk_events
        assert MarketEventType.KLINE in risk_events

        # 验证订阅器生命周期
        assert strategy_subscriber.start_called
        assert strategy_subscriber.stop_called
        assert risk_subscriber.start_called
        assert risk_subscriber.stop_called
