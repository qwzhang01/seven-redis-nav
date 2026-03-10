#!/usr/bin/env python3
"""
SignalEventBus 测试用例

测试信号事件总线的核心功能：
- 事件发布和订阅机制
- 全局订阅和信号级订阅
- 错误处理和统计功能
- 并发事件分发
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
from typing import Any

from src.quant_trading_system.engines.signal_event_bus import (
    SignalEventBus,
    SignalEvent,
    SignalEventType,
    SignalSubscriber,
    OrderFilledData,
)


# ── 测试订阅器实现 ──────────────────────────────────────────────


class TestSubscriber(SignalSubscriber):
    """测试用订阅器"""

    def __init__(self, name: str = "test_subscriber"):
        self._name = name
        self.received_events: list[SignalEvent] = []
        self.error_count = 0

    @property
    def name(self) -> str:
        return self._name

    async def on_signal_event(self, event: SignalEvent) -> None:
        """记录接收到的事件"""
        self.received_events.append(event)


class ErrorSubscriber(SignalSubscriber):
    """会抛出异常的测试订阅器"""

    def __init__(self, name: str = "error_subscriber"):
        self._name = name
        self.received_events: list[SignalEvent] = []

    @property
    def name(self) -> str:
        return self._name

    async def on_signal_event(self, event: SignalEvent) -> None:
        """总是抛出异常"""
        self.received_events.append(event)
        raise RuntimeError("模拟订阅器异常")


class SlowSubscriber(SignalSubscriber):
    """处理速度较慢的测试订阅器"""

    def __init__(self, name: str = "slow_subscriber", delay: float = 0.1):
        self._name = name
        self.delay = delay
        self.received_events: list[SignalEvent] = []

    @property
    def name(self) -> str:
        return self._name

    async def on_signal_event(self, event: SignalEvent) -> None:
        """模拟慢速处理"""
        await asyncio.sleep(self.delay)
        self.received_events.append(event)


# ── 测试用例类 ──────────────────────────────────────────────────


class TestSignalEventBus:
    """SignalEventBus 核心功能测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.bus = SignalEventBus()
        self.test_subscriber = TestSubscriber()
        self.error_subscriber = ErrorSubscriber()
        self.slow_subscriber = SlowSubscriber()

    def test_initial_state(self):
        """测试初始状态"""
        stats = self.bus.stats
        assert stats["total_published"] == 0
        assert stats["error_count"] == 0
        assert stats["subscriber_count"] == 0
        assert stats["subscribers"] == []

    def test_subscribe_global(self):
        """测试全局订阅"""
        # 订阅单个事件类型
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)

        # 验证订阅状态
        stats = self.bus.stats
        assert stats["subscriber_count"] == 1
        assert self.test_subscriber.name in stats["subscribers"]

    def test_subscribe_signal_level(self):
        """测试信号级订阅"""
        # 订阅特定信号ID的事件
        signal_id = 123
        self.bus.subscribe(
            SignalEventType.ORDER_FILLED,
            self.test_subscriber,
            signal_id=signal_id
        )

        # 验证订阅状态
        stats = self.bus.stats
        assert stats["subscriber_count"] == 1
        assert signal_id in stats["signal_subscriptions"]
        assert stats["signal_subscriptions"][signal_id] == 1

    def test_subscribe_many(self):
        """测试批量订阅"""
        event_types = [
            SignalEventType.ORDER_FILLED,
            SignalEventType.ORDER_NEW,
            SignalEventType.ACCOUNT_UPDATE,
        ]

        self.bus.subscribe_many(event_types, self.test_subscriber)

        # 验证所有事件类型都已订阅
        stats = self.bus.stats
        assert stats["subscriber_count"] == 1

    async def test_publish_to_global_subscriber(self):
        """测试发布事件到全局订阅器"""
        # 设置订阅
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)

        # 创建并发布事件
        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=456,
            data={"test": "data"},
            symbol="BTCUSDT",
        )

        await self.bus.publish(event)

        # 验证事件被接收
        assert len(self.test_subscriber.received_events) == 1
        assert self.test_subscriber.received_events[0] == event

        # 验证统计信息
        stats = self.bus.stats
        assert stats["total_published"] == 1
        assert stats["event_counts"]["ORDER_FILLED"] == 1

    async def test_publish_to_signal_level_subscriber(self):
        """测试发布事件到信号级订阅器"""
        signal_id = 789

        # 设置信号级订阅
        self.bus.subscribe(
            SignalEventType.ORDER_FILLED,
            self.test_subscriber,
            signal_id=signal_id
        )

        # 发布匹配信号ID的事件
        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=signal_id,
            data={"test": "data"},
        )

        await self.bus.publish(event)

        # 验证事件被接收
        assert len(self.test_subscriber.received_events) == 1
        assert self.test_subscriber.received_events[0].signal_id == signal_id

    async def test_publish_to_both_subscribers(self):
        """测试同时有全局和信号级订阅器的情况"""
        signal_id = 999

        # 创建两个订阅器
        global_subscriber = TestSubscriber("global")
        signal_subscriber = TestSubscriber("signal")

        # 设置订阅
        self.bus.subscribe(SignalEventType.ORDER_FILLED, global_subscriber)
        self.bus.subscribe(
            SignalEventType.ORDER_FILLED,
            signal_subscriber,
            signal_id=signal_id
        )

        # 发布事件
        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=signal_id,
            data={"test": "data"},
        )

        await self.bus.publish(event)

        # 验证两个订阅器都收到了事件
        assert len(global_subscriber.received_events) == 1
        assert len(signal_subscriber.received_events) == 1

    async def test_publish_with_order_filled_data(self):
        """测试使用OrderFilledData发布事件"""
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)

        # 创建订单成交数据
        order_data = OrderFilledData(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.1,
            price=50000.0,
            quote_quantity=5000.0,
            original_order_id="order_123",
            trade_time=1640995200000,
            commission=5.0,
            commission_asset="USDT",
        )

        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=456,
            data=order_data.to_dict(),
            symbol="BTCUSDT",
        )

        await self.bus.publish(event)

        # 验证数据正确传递
        received_event = self.test_subscriber.received_events[0]
        assert received_event.data["symbol"] == "BTCUSDT"
        assert received_event.data["side"] == "BUY"
        assert received_event.data["quantity"] == 0.1

    async def test_error_handling(self):
        """测试错误处理机制"""
        # 设置会抛出异常的订阅器
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.error_subscriber)

        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=456,
            data={"test": "data"},
        )

        # 发布事件，应该不会抛出异常
        await self.bus.publish(event)

        # 验证错误统计
        stats = self.bus.stats
        assert stats["error_count"] == 1
        assert len(self.error_subscriber.received_events) == 1

    async def test_concurrent_event_processing(self):
        """测试并发事件处理"""
        # 设置多个慢速订阅器
        subscribers = [SlowSubscriber(f"sub_{i}") for i in range(3)]
        for subscriber in subscribers:
            self.bus.subscribe(SignalEventType.ORDER_FILLED, subscriber)

        # 并发发布多个事件
        events = [
            SignalEvent(
                type=SignalEventType.ORDER_FILLED,
                signal_id=i,
                data={"event_id": i},
            )
            for i in range(5)
        ]

        # 并发发布所有事件
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[self.bus.publish(event) for event in events])
        end_time = asyncio.get_event_loop().time()

        # 验证并发执行（总时间应小于串行时间）
        serial_time = len(events) * 0.1 * len(subscribers)
        assert end_time - start_time < serial_time

        # 验证所有订阅器都收到了所有事件
        for subscriber in subscribers:
            assert len(subscriber.received_events) == len(events)

    def test_unsubscribe_global(self):
        """测试取消全局订阅"""
        # 先订阅
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)
        assert self.bus.stats["subscriber_count"] == 1

        # 再取消订阅
        self.bus.unsubscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)
        assert self.bus.stats["subscriber_count"] == 0

    def test_unsubscribe_signal_level(self):
        """测试取消信号级订阅"""
        signal_id = 123

        # 先订阅
        self.bus.subscribe(
            SignalEventType.ORDER_FILLED,
            self.test_subscriber,
            signal_id=signal_id
        )
        assert self.bus.stats["signal_subscriptions"][signal_id] == 1

        # 再取消订阅
        self.bus.unsubscribe(
            SignalEventType.ORDER_FILLED,
            self.test_subscriber,
            signal_id=signal_id
        )
        # 取消订阅后，该 signal_id 的订阅数应为 0（key 可能仍存在但 count=0）
        assert self.bus.stats["signal_subscriptions"].get(signal_id, 0) == 0

    def test_unsubscribe_all(self):
        """测试取消所有订阅"""
        # 订阅多个事件类型
        event_types = [
            SignalEventType.ORDER_FILLED,
            SignalEventType.ORDER_NEW,
            SignalEventType.ACCOUNT_UPDATE,
        ]

        for event_type in event_types:
            self.bus.subscribe(event_type, self.test_subscriber)

        assert self.bus.stats["subscriber_count"] == 1

        # 取消所有订阅
        self.bus.unsubscribe_all(self.test_subscriber)
        assert self.bus.stats["subscriber_count"] == 0

    def test_unsubscribe_signal(self):
        """测试取消特定信号的所有订阅"""
        signal_id = 456

        # 为同一信号ID订阅多个事件类型
        event_types = [
            SignalEventType.ORDER_FILLED,
            SignalEventType.ORDER_NEW,
        ]

        for event_type in event_types:
            self.bus.subscribe(event_type, self.test_subscriber, signal_id=signal_id)

        assert self.bus.stats["signal_subscriptions"][signal_id] == 2

        # 取消该信号的所有订阅
        self.bus.unsubscribe_signal(signal_id)
        assert signal_id not in self.bus.stats["signal_subscriptions"]

    async def test_no_subscribers(self):
        """测试没有订阅器时发布事件"""
        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=456,
            data={"test": "data"},
        )

        # 应该不会抛出异常
        await self.bus.publish(event)

        # 验证统计信息
        stats = self.bus.stats
        assert stats["total_published"] == 1
        assert stats["event_counts"]["ORDER_FILLED"] == 1

    async def test_duplicate_subscriber_handling(self):
        """测试重复订阅器处理"""
        # 多次订阅同一事件类型
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)
        self.bus.subscribe(SignalEventType.ORDER_FILLED, self.test_subscriber)

        # 应该只注册一次
        assert self.bus.stats["subscriber_count"] == 1

        # 发布事件
        event = SignalEvent(
            type=SignalEventType.ORDER_FILLED,
            signal_id=456,
            data={"test": "data"},
        )

        await self.bus.publish(event)

        # 应该只收到一次事件
        assert len(self.test_subscriber.received_events) == 1


# ── 集成测试 ──────────────────────────────────────────────────


class TestSignalEventBusIntegration:
    """SignalEventBus 集成测试"""

    async def test_realistic_workflow(self):
        """测试真实工作流程"""
        bus = SignalEventBus()

        # 创建多个不同类型的订阅器
        record_subscriber = TestSubscriber("record_subscriber")
        follow_subscriber = TestSubscriber("follow_subscriber")
        monitor_subscriber = TestSubscriber("monitor_subscriber")

        # 设置订阅关系
        # 记录订阅器订阅所有订单事件
        bus.subscribe_many(
            [
                SignalEventType.ORDER_FILLED,
                SignalEventType.ORDER_NEW,
                SignalEventType.ORDER_CANCELED,
            ],
            record_subscriber,
        )

        # 跟单订阅器只关注特定信号源的成交事件
        target_signal_id = 1001
        bus.subscribe(
            SignalEventType.ORDER_FILLED,
            follow_subscriber,
            signal_id=target_signal_id
        )

        # 监控订阅器关注所有账户更新事件
        bus.subscribe(SignalEventType.ACCOUNT_UPDATE, monitor_subscriber)

        # 模拟真实事件流
        events = [
            # 目标信号源的成交事件
            SignalEvent(
                type=SignalEventType.ORDER_FILLED,
                signal_id=target_signal_id,
                data=OrderFilledData(
                    symbol="BTCUSDT",
                    side="BUY",
                    order_type="MARKET",
                    quantity=0.5,
                    price=52000.0,
                    quote_quantity=26000.0,
                    original_order_id="order_1001",
                    trade_time=1640995200000,
                ).to_dict(),
                symbol="BTCUSDT",
            ),
            # 其他信号源的成交事件
            SignalEvent(
                type=SignalEventType.ORDER_FILLED,
                signal_id=1002,
                data=OrderFilledData(
                    symbol="ETHUSDT",
                    side="SELL",
                    order_type="LIMIT",
                    quantity=2.0,
                    price=3500.0,
                    quote_quantity=7000.0,
                    original_order_id="order_1002",
                    trade_time=1640995201000,
                ).to_dict(),
                symbol="ETHUSDT",
            ),
            # 账户更新事件
            SignalEvent(
                type=SignalEventType.ACCOUNT_UPDATE,
                signal_id=1001,
                data={
                    "total_balance": 100000.0,
                    "available_balance": 80000.0,
                    "positions": {"BTC": 0.5, "ETH": 10.0},
                },
            ),
        ]

        # 发布所有事件
        for event in events:
            await bus.publish(event)

        # 验证事件分发正确性
        # 记录订阅器订阅了 ORDER_FILLED/ORDER_NEW/ORDER_CANCELED，共收到 2 个成交事件
        # （未订阅 ACCOUNT_UPDATE，所以不会收到账户更新事件）
        assert len(record_subscriber.received_events) == 2

        # 跟单订阅器只收到目标信号源的成交事件
        assert len(follow_subscriber.received_events) == 1
        assert follow_subscriber.received_events[0].signal_id == target_signal_id

        # 监控订阅器只收到账户更新事件
        assert len(monitor_subscriber.received_events) == 1
        assert monitor_subscriber.received_events[0].type == SignalEventType.ACCOUNT_UPDATE

        # 验证统计信息
        stats = bus.stats
        assert stats["total_published"] == 3
        assert stats["event_counts"]["ORDER_FILLED"] == 2
        assert stats["event_counts"]["ACCOUNT_UPDATE"] == 1
        assert stats["subscriber_count"] == 3


# ── 性能测试 ──────────────────────────────────────────────────


class TestSignalEventBusPerformance:
    """SignalEventBus 性能测试"""

    async def test_high_frequency_events(self):
        """测试高频事件处理性能"""
        bus = SignalEventBus()

        # 创建多个订阅器
        subscribers = [TestSubscriber(f"sub_{i}") for i in range(10)]
        for subscriber in subscribers:
            bus.subscribe(SignalEventType.ORDER_FILLED, subscriber)

        # 发布大量事件
        event_count = 100
        events = [
            SignalEvent(
                type=SignalEventType.ORDER_FILLED,
                signal_id=i % 5,  # 5个不同的信号源
                data={"event_id": i},
            )
            for i in range(event_count)
        ]

        # 批量发布
        start_time = asyncio.get_event_loop().time()
        await asyncio.gather(*[bus.publish(event) for event in events])
        end_time = asyncio.get_event_loop().time()

        # 验证所有事件都被处理
        total_received = sum(len(sub.received_events) for sub in subscribers)
        assert total_received == event_count * len(subscribers)

        # 验证性能（应该在合理时间内完成）
        processing_time = end_time - start_time
        assert processing_time < 5.0  # 100个事件应该在5秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
