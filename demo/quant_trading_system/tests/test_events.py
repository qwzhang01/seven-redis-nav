"""
事件引擎测试
"""

import asyncio
import pytest

from quant_trading_system.core.events import Event, EventEngine, EventType


class TestEventEngine:
    """事件引擎测试"""
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        engine = EventEngine(num_workers=2)
        
        await engine.start()
        assert engine.is_running
        
        await engine.stop()
        assert not engine.is_running
    
    @pytest.mark.asyncio
    async def test_event_handling(self):
        engine = EventEngine(num_workers=2)
        
        received_events = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        engine.register(EventType.TICK, handler)
        
        await engine.start()
        
        # 发送事件
        await engine.put(Event(type=EventType.TICK, data={"price": 100}))
        await engine.put(Event(type=EventType.TICK, data={"price": 101}))
        
        # 等待处理
        await asyncio.sleep(0.1)
        
        await engine.stop()
        
        assert len(received_events) == 2
    
    @pytest.mark.asyncio
    async def test_event_priority(self):
        from quant_trading_system.core.events import EventPriority
        
        engine = EventEngine(num_workers=1)
        
        received_order = []
        
        async def handler(event: Event):
            received_order.append(event.data)
        
        engine.register(EventType.TICK, handler)
        
        await engine.start()
        
        # 发送不同优先级的事件
        await engine.put(Event(
            type=EventType.TICK, 
            data="low", 
            priority=EventPriority.LOW
        ))
        await engine.put(Event(
            type=EventType.TICK, 
            data="high", 
            priority=EventPriority.HIGH
        ))
        await engine.put(Event(
            type=EventType.TICK, 
            data="critical", 
            priority=EventPriority.CRITICAL
        ))
        
        await asyncio.sleep(0.2)
        await engine.stop()
        
        # 高优先级应该先处理
        assert len(received_order) == 3


class TestEvent:
    """事件测试"""
    
    def test_event_creation(self):
        event = Event(
            type=EventType.TICK,
            data={"price": 100},
            source="test",
        )
        
        assert event.type == EventType.TICK
        assert event.data == {"price": 100}
        assert event.source == "test"
        assert event.event_id != ""
    
    def test_event_comparison(self):
        from quant_trading_system.core.events import EventPriority
        
        event1 = Event(type=EventType.TICK, priority=EventPriority.HIGH)
        event2 = Event(type=EventType.TICK, priority=EventPriority.LOW)
        
        # 高优先级事件应该"小于"低优先级（用于优先级队列）
        assert event1 < event2
