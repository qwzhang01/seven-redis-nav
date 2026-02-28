"""
EventEngine 单元测试
====================

演示 EventEngine 的核心功能用法：
- 启动与停止
- 事件发布与订阅（异步/同步处理器）
- 事件优先级队列
- 事件过滤器
- 通用处理器（接收所有事件）
- 处理器注册与注销
- 非阻塞事件投递
- 统计信息
"""

import asyncio

import pytest

from quant_trading_system.core.events import (
    Event,
    EventEngine,
    EventPriority,
    EventType,
)


# ============================
# Fixtures
# ============================

@pytest.fixture
def engine():
    """创建一个测试用的 EventEngine 实例"""
    return EventEngine(queue_size=1000, num_workers=2, name="TestEngine")


# ============================
# 基础生命周期测试
# ============================

class TestEventEngineLifecycle:
    """测试事件引擎的启动与停止"""

    async def test_start_and_stop(self, engine: EventEngine):
        """测试基本的启动和停止流程"""
        assert not engine.is_running

        await engine.start()
        assert engine.is_running

        await engine.stop()
        assert not engine.is_running

    async def test_duplicate_start(self, engine: EventEngine):
        """测试重复启动不会报错"""
        await engine.start()
        await engine.start()  # 第二次启动应该被忽略
        assert engine.is_running

        await engine.stop()

    async def test_stop_without_start(self, engine: EventEngine):
        """测试未启动直接停止不会报错"""
        await engine.stop()  # 不应抛出异常
        assert not engine.is_running


# ============================
# 事件发布与订阅（异步处理器）
# ============================

class TestAsyncEventHandling:
    """测试异步事件处理器的注册和分发"""

    async def test_register_and_receive_event(self, engine: EventEngine):
        """
        Demo: 注册一个异步处理器，发布事件后处理器应被调用

        典型使用方式：
            engine.register(EventType.BAR, on_bar_handler)
            await engine.put(Event(type=EventType.BAR, data=bar_data))
        """
        received_events: list[Event] = []

        async def on_bar(event: Event):
            received_events.append(event)

        # 注册处理器
        engine.register(EventType.BAR, on_bar)

        await engine.start()

        # 发布 BAR 事件
        bar_data = {"symbol": "AAPL", "close": 150.0, "volume": 1000}
        await engine.put(Event(
            type=EventType.BAR,
            data=bar_data,
            source="test_market_service",
        ))

        # 等待事件被处理
        await asyncio.sleep(0.1)
        await engine.stop()

        assert len(received_events) == 1
        assert received_events[0].type == EventType.BAR
        assert received_events[0].data["symbol"] == "AAPL"
        assert received_events[0].source == "test_market_service"

    async def test_multiple_handlers_for_same_event(self, engine: EventEngine):
        """Demo: 同一事件类型可以注册多个处理器，都会被调用"""
        handler1_called = asyncio.Event()
        handler2_called = asyncio.Event()

        async def handler1(event: Event):
            handler1_called.set()

        async def handler2(event: Event):
            handler2_called.set()

        engine.register(EventType.TICK, handler1)
        engine.register(EventType.TICK, handler2)

        await engine.start()
        await engine.put(Event(type=EventType.TICK, data={"price": 100.0}))

        await asyncio.sleep(0.1)
        await engine.stop()

        assert handler1_called.is_set()
        assert handler2_called.is_set()

    async def test_handler_only_receives_registered_event_type(self, engine: EventEngine):
        """Demo: 处理器只接收注册的事件类型，其他类型不会触发"""
        received_types: list[EventType] = []

        async def on_order(event: Event):
            received_types.append(event.type)

        engine.register(EventType.ORDER, on_order)

        await engine.start()

        # 发布 BAR 事件（不应触发 on_order）
        await engine.put(Event(type=EventType.BAR, data={}))
        # 发布 ORDER 事件（应触发 on_order）
        await engine.put(Event(type=EventType.ORDER, data={"order_id": "001"}))

        await asyncio.sleep(0.1)
        await engine.stop()

        assert received_types == [EventType.ORDER]


# ============================
# 同步处理器
# ============================

class TestSyncEventHandling:
    """测试同步事件处理器"""

    async def test_sync_handler(self, engine: EventEngine):
        """
        Demo: 注册同步处理器（is_async=False）

        适用于轻量级的同步回调，如日志记录。
        """
        sync_results: list[str] = []

        def on_log(event: Event):
            sync_results.append(f"LOG: {event.data}")

        engine.register(EventType.LOG, on_log, is_async=False)

        await engine.start()
        await engine.put(Event(type=EventType.LOG, data="系统启动完成"))

        await asyncio.sleep(0.1)
        await engine.stop()

        assert len(sync_results) == 1
        assert sync_results[0] == "LOG: 系统启动完成"

    async def test_mixed_async_and_sync_handlers(self, engine: EventEngine):
        """Demo: 同一事件可以同时注册异步和同步处理器"""
        call_order: list[str] = []

        async def async_handler(event: Event):
            call_order.append("async")

        def sync_handler(event: Event):
            call_order.append("sync")

        engine.register(EventType.SIGNAL, async_handler, is_async=True)
        engine.register(EventType.SIGNAL, sync_handler, is_async=False)

        await engine.start()
        await engine.put(Event(type=EventType.SIGNAL, data={"action": "BUY"}))

        await asyncio.sleep(0.1)
        await engine.stop()

        # 异步和同步处理器都应被调用
        assert "async" in call_order
        assert "sync" in call_order


# ============================
# 事件优先级
# ============================

class TestEventPriority:
    """测试事件优先级队列"""

    async def test_priority_ordering(self, engine: EventEngine):
        """
        Demo: 高优先级事件先于低优先级事件被处理

        优先级从高到低：CRITICAL > HIGH > NORMAL > LOW
        场景：风控事件(CRITICAL)应优先于行情事件(NORMAL)被处理
        """
        processed_order: list[str] = []

        async def handler(event: Event):
            processed_order.append(event.data["label"])

        engine.register(EventType.BAR, handler)
        engine.register(EventType.RISK_ALERT, handler)
        engine.register(EventType.LOG, handler)

        await engine.start()

        # 批量投入不同优先级的事件（先投入低优先级，再投入高优先级）
        events = [
            Event(type=EventType.LOG, data={"label": "low"},
                  priority=EventPriority.LOW),
            Event(type=EventType.BAR, data={"label": "normal"},
                  priority=EventPriority.NORMAL),
            Event(type=EventType.RISK_ALERT, data={"label": "critical"},
                  priority=EventPriority.CRITICAL),
        ]

        for e in events:
            engine.put_nowait(e)

        await asyncio.sleep(0.2)
        await engine.stop()

        # 验证高优先级事件先被处理
        assert len(processed_order) == 3
        assert processed_order[0] == "critical"  # CRITICAL 最先

    async def test_event_lt_comparison(self):
        """测试 Event 的优先级比较（__lt__）"""
        critical_event = Event(
            type=EventType.RISK_BREACH,
            priority=EventPriority.CRITICAL,
        )
        normal_event = Event(
            type=EventType.BAR,
            priority=EventPriority.NORMAL,
        )
        assert critical_event < normal_event  # CRITICAL(0) < NORMAL(2)

        # 相同优先级，时间戳更早的在前
        import time
        e1 = Event(type=EventType.BAR, priority=EventPriority.NORMAL, timestamp=time.time())
        e2 = Event(type=EventType.BAR, priority=EventPriority.NORMAL, timestamp=time.time() + 1)
        assert e1 < e2


# ============================
# 通用处理器
# ============================

class TestGeneralHandler:
    """测试通用处理器（接收所有事件）"""

    async def test_general_handler_receives_all_events(self, engine: EventEngine):
        """
        Demo: 通用处理器可以接收所有类型的事件

        适用于全局日志记录、监控统计等场景。
        """
        all_events: list[Event] = []

        async def monitor(event: Event):
            all_events.append(event)

        engine.register_general(monitor)

        await engine.start()

        # SYSTEM_START 事件在 start() 时自动发送，所以先等一下
        await asyncio.sleep(0.05)

        await engine.put(Event(type=EventType.BAR, data={}))
        await engine.put(Event(type=EventType.ORDER, data={}))
        await engine.put(Event(type=EventType.SIGNAL, data={}))

        await asyncio.sleep(0.1)
        await engine.stop()

        # 通用处理器应该收到所有事件（包括 SYSTEM_START 和 SYSTEM_STOP）
        event_types = [e.type for e in all_events]
        assert EventType.SYSTEM_START in event_types
        assert EventType.BAR in event_types
        assert EventType.ORDER in event_types
        assert EventType.SIGNAL in event_types

    async def test_general_sync_handler(self, engine: EventEngine):
        """Demo: 通用同步处理器"""
        event_count = {"count": 0}

        def counter(event: Event):
            event_count["count"] += 1

        engine.register_general(counter, is_async=False)

        await engine.start()
        await engine.put(Event(type=EventType.TICK, data={}))
        await engine.put(Event(type=EventType.BAR, data={}))

        await asyncio.sleep(0.1)
        await engine.stop()

        # SYSTEM_START + TICK + BAR + SYSTEM_STOP = 至少4个
        assert event_count["count"] >= 4


# ============================
# 事件过滤器
# ============================

class TestEventFilter:
    """测试事件过滤器"""

    async def test_filter_blocks_event(self, engine: EventEngine):
        """
        Demo: 通过过滤器可以阻止特定事件被处理

        场景：只处理特定股票代码的行情事件
        """
        received_events: list[Event] = []

        async def on_bar(event: Event):
            received_events.append(event)

        engine.register(EventType.BAR, on_bar)

        # 添加过滤器：只处理 symbol == "AAPL" 的 BAR 事件
        engine.add_filter(
            EventType.BAR,
            lambda event: event.data.get("symbol") == "AAPL"
        )

        await engine.start()

        # 发布 AAPL 的行情（应通过过滤）
        await engine.put(Event(type=EventType.BAR, data={"symbol": "AAPL", "close": 150.0}))
        # 发布 GOOG 的行情（应被过滤掉）
        await engine.put(Event(type=EventType.BAR, data={"symbol": "GOOG", "close": 2800.0}))

        await asyncio.sleep(0.1)
        await engine.stop()

        assert len(received_events) == 1
        assert received_events[0].data["symbol"] == "AAPL"


# ============================
# 处理器注销
# ============================

class TestUnregister:
    """测试处理器注销"""

    async def test_unregister_handler(self, engine: EventEngine):
        """Demo: 注销处理器后，不再接收该类型事件"""
        call_count = {"count": 0}

        async def on_tick(event: Event):
            call_count["count"] += 1

        engine.register(EventType.TICK, on_tick)

        await engine.start()

        # 第一次发布，应触发处理器
        await engine.put(Event(type=EventType.TICK, data={}))
        await asyncio.sleep(0.1)
        assert call_count["count"] == 1

        # 注销处理器
        engine.unregister(EventType.TICK, on_tick)

        # 第二次发布，不应触发处理器
        await engine.put(Event(type=EventType.TICK, data={}))
        await asyncio.sleep(0.1)

        await engine.stop()
        assert call_count["count"] == 1  # 仍然是1，没有增加

    async def test_duplicate_register_ignored(self, engine: EventEngine):
        """Demo: 重复注册同一处理器会被忽略"""
        call_count = {"count": 0}

        async def handler(event: Event):
            call_count["count"] += 1

        engine.register(EventType.BAR, handler)
        engine.register(EventType.BAR, handler)  # 重复注册

        await engine.start()
        await engine.put(Event(type=EventType.BAR, data={}))
        await asyncio.sleep(0.1)
        await engine.stop()

        assert call_count["count"] == 1  # 只调用一次


# ============================
# 非阻塞投递
# ============================

class TestPutNowait:
    """测试非阻塞事件投递"""

    async def test_put_nowait_success(self, engine: EventEngine):
        """Demo: 使用 put_nowait 非阻塞投递事件"""
        received = []

        async def handler(event: Event):
            received.append(event)

        engine.register(EventType.ORDER, handler)

        await engine.start()

        result = engine.put_nowait(Event(
            type=EventType.ORDER,
            data={"order_id": "ORD001", "side": "BUY"},
        ))
        assert result is True

        await asyncio.sleep(0.1)
        await engine.stop()

        assert len(received) == 1

    async def test_put_nowait_when_not_running(self, engine: EventEngine):
        """Demo: 引擎未启动时，put_nowait 返回 False"""
        result = engine.put_nowait(Event(type=EventType.BAR, data={}))
        assert result is False


# ============================
# Event 数据类
# ============================

class TestEventDataclass:
    """测试 Event 数据类"""

    async def test_event_auto_id(self):
        """测试事件自动生成 ID"""
        event = Event(type=EventType.BAR, data={"close": 100.0})
        assert event.event_id != ""
        assert "BAR_" in event.event_id

    async def test_event_custom_id(self):
        """测试自定义事件 ID"""
        event = Event(type=EventType.ORDER, data={}, event_id="MY_ORDER_001")
        assert event.event_id == "MY_ORDER_001"

    async def test_event_default_priority(self):
        """测试事件默认优先级为 NORMAL"""
        event = Event(type=EventType.TICK, data={})
        assert event.priority == EventPriority.NORMAL

    async def test_event_timestamp(self):
        """测试事件自动生成时间戳"""
        import time
        before = time.time()
        event = Event(type=EventType.BAR, data={})
        after = time.time()
        assert before <= event.timestamp <= after


# ============================
# 统计信息
# ============================

class TestEngineStats:
    """测试引擎统计信息"""

    async def test_stats_after_events(self, engine: EventEngine):
        """
        Demo: 获取引擎运行统计信息

        可用于监控面板展示引擎运行状况。
        """
        async def noop(event: Event):
            pass

        engine.register(EventType.BAR, noop)

        await engine.start()

        for i in range(5):
            await engine.put(Event(type=EventType.BAR, data={"i": i}))

        await asyncio.sleep(0.2)

        stats = engine.stats
        assert stats["name"] == "TestEngine"
        assert stats["running"] is True
        # total_events 至少包含 SYSTEM_START + 5个BAR
        assert stats["total_events"] >= 6
        assert stats["uptime"] > 0
        assert stats["events_per_second"] > 0

        await engine.stop()

    async def test_queue_size(self, engine: EventEngine):
        """Demo: 查询当前队列中待处理事件数量"""
        assert engine.queue_size == 0  # 未启动时为0

        await engine.start()
        # start() 后队列可能有 SYSTEM_START 事件
        await asyncio.sleep(0.1)  # 等待worker消费完

        assert engine.queue_size == 0  # 已经被消费
        await engine.stop()


# ============================
# 异常处理
# ============================

class TestErrorHandling:
    """测试异常处理"""

    async def test_handler_exception_does_not_crash_engine(self, engine: EventEngine):
        """
        Demo: 处理器抛出异常不会导致引擎崩溃

        引擎会捕获异常并记录日志，继续处理后续事件。
        """
        processed = []

        async def bad_handler(event: Event):
            raise ValueError("模拟处理器异常")

        async def good_handler(event: Event):
            processed.append(event)

        engine.register(EventType.BAR, bad_handler)
        engine.register(EventType.TICK, good_handler)

        await engine.start()

        # bad_handler 会抛异常，但不应影响后续事件处理
        await engine.put(Event(type=EventType.BAR, data={}))
        await engine.put(Event(type=EventType.TICK, data={"price": 50.0}))

        await asyncio.sleep(0.1)
        await engine.stop()

        # good_handler 应正常工作
        assert len(processed) == 1
        assert processed[0].type == EventType.TICK

    async def test_put_event_when_engine_not_running(self, engine: EventEngine):
        """Demo: 引擎未启动时发送事件不会报错，事件被丢弃"""
        # 不应抛出异常
        await engine.put(Event(type=EventType.BAR, data={}))


# ============================
# 综合 Demo: 模拟量化交易事件流
# ============================

class TestTradingEventFlowDemo:
    """
    综合 Demo: 模拟一个简化的量化交易事件流

    流程：行情数据 → 策略信号 → 订单执行 → 风控检查
    """

    async def test_full_trading_event_flow(self):
        """
        模拟完整的交易事件流：

        1. 行情服务发布 BAR 事件
        2. 策略引擎接收到 BAR，生成 SIGNAL 事件
        3. 交易引擎接收到 SIGNAL，生成 ORDER 事件
        4. 风控模块通过通用处理器监控所有事件
        """
        engine = EventEngine(queue_size=1000, num_workers=2, name="TradingDemo")
        event_log: list[str] = []

        # ---- 策略引擎：接收行情，生成信号 ----
        async def strategy_on_bar(event: Event):
            bar = event.data
            event_log.append(f"策略收到行情: {bar['symbol']} 收盘价={bar['close']}")

            # 简单策略：收盘价超过 150 就发出买入信号
            if bar["close"] > 150:
                signal = Event(
                    type=EventType.SIGNAL,
                    data={"symbol": bar["symbol"], "action": "BUY", "price": bar["close"]},
                    source="demo_strategy",
                    priority=EventPriority.HIGH,
                )
                await engine.put(signal)

        # ---- 交易引擎：接收信号，生成订单 ----
        async def trading_on_signal(event: Event):
            signal = event.data
            event_log.append(f"交易引擎收到信号: {signal['action']} {signal['symbol']}")

            order = Event(
                type=EventType.ORDER,
                data={
                    "order_id": "ORD001",
                    "symbol": signal["symbol"],
                    "side": signal["action"],
                    "price": signal["price"],
                    "quantity": 100,
                },
                source="demo_trading_engine",
            )
            await engine.put(order)

        # ---- 风控模块：通用处理器监控所有事件 ----
        async def risk_monitor(event: Event):
            # 忽略系统事件
            if event.type in (EventType.SYSTEM_START, EventType.SYSTEM_STOP):
                return
            event_log.append(f"[风控监控] 事件类型={event.type.name}, 来源={event.source}")

        # 注册处理器
        engine.register(EventType.BAR, strategy_on_bar)
        engine.register(EventType.SIGNAL, trading_on_signal)
        engine.register_general(risk_monitor)

        # 启动引擎
        await engine.start()
        await asyncio.sleep(0.05)

        # ---- 模拟行情服务发布数据 ----
        bars = [
            {"symbol": "AAPL", "close": 145.0, "volume": 1000},   # 不触发信号
            {"symbol": "AAPL", "close": 160.0, "volume": 2000},   # 触发买入信号
        ]

        for bar in bars:
            await engine.put(Event(
                type=EventType.BAR,
                data=bar,
                source="demo_market_service",
            ))

        # 等待所有事件处理完毕
        await asyncio.sleep(0.3)
        await engine.stop()

        # ---- 验证事件流 ----
        # 两根K线都被策略接收
        assert any("收盘价=145.0" in log for log in event_log)
        assert any("收盘价=160.0" in log for log in event_log)

        # 只有160的K线触发了交易信号
        assert any("BUY AAPL" in log for log in event_log)

        # 风控模块监控到了事件
        assert any("[风控监控]" in log for log in event_log)

        # 打印完整事件日志（方便调试查看）
        print("\n===== 交易事件流日志 =====")
        for log in event_log:
            print(f"  {log}")
        print("==========================\n")
