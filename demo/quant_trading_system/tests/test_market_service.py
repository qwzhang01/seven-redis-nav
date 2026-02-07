import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from quant_trading_system.services.market.market_service import MarketService
from quant_trading_system.models.market import Bar, Tick, Depth, TimeFrame
from quant_trading_system.core.events import EventEngine, EventType


class TestMarketService:
    """市场服务测试"""
    
    @pytest.fixture
    def market_service(self):
        """创建市场服务实例"""
        event_engine = EventEngine()
        return MarketService(event_engine=event_engine)
    
    @pytest.fixture
    def mock_tick_data(self):
        """模拟Tick数据"""
        return Tick(
            symbol="BTC/USDT",
            exchange="binance",
            timestamp=1700000000000,
            last_price=50000.0,
            bid_price=49999.0,
            ask_price=50001.0,
            bid_size=1.0,
            ask_size=1.0,
            volume=1000.0,
            turnover=50000000.0,
            is_trade=True,
            trade_id="test_trade_001"
        )
    
    @pytest.fixture
    def mock_bar_data(self):
        """模拟K线数据"""
        return Bar(
            symbol="BTC/USDT",
            exchange="binance",
            timeframe=TimeFrame.M1,
            timestamp=1700000000000,
            open=50000.0,
            high=50100.0,
            low=49900.0,
            close=50050.0,
            volume=1000.0,
            turnover=50050000.0
        )
    
    @pytest.mark.asyncio
    async def test_start_stop(self, market_service):
        """测试启动和停止"""
        # 测试启动
        await market_service.start()
        assert market_service.is_running
        
        # 测试停止
        await market_service.stop()
        assert not market_service.is_running
    
    @pytest.mark.asyncio
    async def test_add_exchange(self, market_service):
        """测试添加交易所"""
        # 添加Binance交易所
        market_service.add_exchange(
            exchange="binance",
            market_type="spot",
            api_key="test_key",
            api_secret="test_secret"
        )
        
        # 检查是否添加成功
        assert "binance_spot" in market_service._collectors
    
    @pytest.mark.asyncio
    async def test_subscribe_symbols(self, market_service):
        """测试订阅交易对"""
        # 添加交易所
        market_service.add_exchange("binance", "spot")
        
        # 订阅交易对
        symbols = ["BTC/USDT", "ETH/USDT"]
        await market_service.subscribe(symbols, "binance", "spot")
        
        # 检查订阅状态
        collector = market_service._collectors["binance_spot"]
        assert collector.subscribed_symbols == symbols
    
    @pytest.mark.asyncio
    async def test_unsubscribe_symbols(self, market_service):
        """测试取消订阅"""
        # 添加交易所并订阅
        market_service.add_exchange("binance", "spot")
        symbols = ["BTC/USDT", "ETH/USDT"]
        await market_service.subscribe(symbols, "binance", "spot")
        
        # 取消订阅
        await market_service.unsubscribe(["BTC/USDT"], "binance", "spot")
        
        # 检查取消订阅状态
        collector = market_service._collectors["binance_spot"]
        assert "BTC/USDT" not in collector.subscribed_symbols
    
    @pytest.mark.asyncio
    async def test_tick_callback(self, market_service, mock_tick_data):
        """测试Tick回调"""
        received_ticks = []
        
        async def tick_callback(tick: Tick):
            received_ticks.append(tick)
        
        # 添加回调
        market_service.add_tick_callback(tick_callback)
        
        # 模拟收到Tick数据
        await market_service._on_tick_data({
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "timestamp": 1700000000000,
            "last_price": 50000.0,
            "bid_price": 49999.0,
            "ask_price": 50001.0,
            "bid_size": 1.0,
            "ask_size": 1.0,
            "volume": 1000.0,
            "turnover": 50000000.0,
            "is_trade": True,
            "trade_id": "test_trade_001"
        })
        
        # 检查回调是否被调用
        assert len(received_ticks) == 1
        assert received_ticks[0].symbol == "BTC/USDT"
    
    @pytest.mark.asyncio
    async def test_bar_callback(self, market_service, mock_bar_data):
        """测试K线回调"""
        received_bars = []
        
        async def bar_callback(bar: Bar):
            received_bars.append(bar)
        
        # 添加回调
        market_service.add_bar_callback(bar_callback, TimeFrame.M1)
        
        # 模拟K线合成（简化测试）
        market_service._kline_engine.process_bar = AsyncMock()
        
        # 模拟收到Tick数据
        await market_service._on_tick_data({
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "timestamp": 1700000000000,
            "last_price": 50000.0,
            "bid_price": 49999.0,
            "ask_price": 50001.0,
            "bid_size": 1.0,
            "ask_size": 1.0,
            "volume": 1000.0,
            "turnover": 50000000.0,
            "is_trade": True,
            "trade_id": "test_trade_001"
        })
        
        # 检查回调是否被调用
        assert market_service._kline_engine.process_bar.called
    
    @pytest.mark.asyncio
    async def test_depth_callback(self, market_service):
        """测试深度回调"""
        received_depths = []
        
        async def depth_callback(depth: Depth):
            received_depths.append(depth)
        
        # 添加回调
        market_service.add_depth_callback(depth_callback)
        
        # 模拟收到深度数据
        await market_service._on_depth_data({
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "timestamp": 1700000000000,
            "bids": [[49999.0, 1.0], [49998.0, 2.0]],
            "asks": [[50001.0, 1.0], [50002.0, 2.0]]
        })
        
        # 检查回调是否被调用
        assert len(received_depths) == 1
        assert received_depths[0].symbol == "BTC/USDT"
    
    def test_get_bars(self, market_service):
        """测试获取K线数据"""
        # 模拟K线引擎返回数据
        mock_bars = [Mock(spec=Bar) for _ in range(10)]
        market_service._kline_engine.get_bars = Mock(return_value=mock_bars)
        
        # 获取K线数据
        bars = market_service.get_bars("BTC/USDT", TimeFrame.M1, limit=10)
        
        # 检查返回结果
        assert len(bars) == 10
        market_service._kline_engine.get_bars.assert_called_with(
            "BTC/USDT", TimeFrame.M1, 10
        )
    
    def test_get_bar_array(self, market_service):
        """测试获取K线数组"""
        # 模拟K线引擎返回数据
        mock_bar_array = Mock()
        market_service._kline_engine.get_bar_array = Mock(return_value=mock_bar_array)
        
        # 获取K线数组
        bar_array = market_service.get_bar_array("BTC/USDT", TimeFrame.M1, limit=10)
        
        # 检查返回结果
        assert bar_array == mock_bar_array
        market_service._kline_engine.get_bar_array.assert_called_with(
            "BTC/USDT", TimeFrame.M1, 10
        )
    
    def test_get_current_bar(self, market_service):
        """测试获取当前K线"""
        # 模拟当前K线
        mock_current_bar = Mock(spec=Bar)
        market_service._kline_engine.get_current_bar = Mock(return_value=mock_current_bar)
        
        # 获取当前K线
        current_bar = market_service.get_current_bar("BTC/USDT", TimeFrame.M1)
        
        # 检查返回结果
        assert current_bar == mock_current_bar
        market_service._kline_engine.get_current_bar.assert_called_with(
            "BTC/USDT", TimeFrame.M1
        )
    
    def test_stats_property(self, market_service):
        """测试统计信息属性"""
        # 设置初始状态
        market_service._running = True
        market_service._tick_count = 100
        market_service._depth_count = 50
        market_service._collectors = {"binance_spot": Mock()}
        market_service._kline_engine.stats = {"bars_processed": 1000}
        
        # 获取统计信息
        stats = market_service.stats
        
        # 检查统计信息
        assert stats["running"] is True
        assert stats["tick_count"] == 100
        assert stats["depth_count"] == 50
        assert "binance_spot" in stats["collectors"]
        assert stats["kline_stats"]["bars_processed"] == 1000
    
    @pytest.mark.asyncio
    async def test_event_emission(self, market_service):
        """测试事件发送"""
        received_events = []
        
        async def event_handler(event):
            received_events.append(event)
        
        # 注册事件处理器
        market_service._event_engine.register(EventType.TICK, event_handler)
        
        # 模拟收到Tick数据
        await market_service._on_tick_data({
            "symbol": "BTC/USDT",
            "exchange": "binance",
            "timestamp": 1700000000000,
            "last_price": 50000.0,
            "bid_price": 49999.0,
            "ask_price": 50001.0,
            "bid_size": 1.0,
            "ask_size": 1.0,
            "volume": 1000.0,
            "turnover": 50000000.0,
            "is_trade": True,
            "trade_id": "test_trade_001"
        })
        
        # 检查事件是否发送
        assert len(received_events) == 1
        assert received_events[0].type == EventType.TICK
        assert received_events[0].data.symbol == "BTC/USDT"
    
    @pytest.mark.asyncio
    async def test_multiple_exchanges(self, market_service):
        """测试多交易所支持"""
        # 添加多个交易所
        market_service.add_exchange("binance", "spot")
        market_service.add_exchange("okx", "spot")
        market_service.add_exchange("binance", "futures")
        
        # 检查交易所是否添加成功
        assert "binance_spot" in market_service._collectors
        assert "okx_spot" in market_service._collectors
        assert "binance_futures" in market_service._collectors
        
        # 检查统计信息
        stats = market_service.stats
        assert len(stats["collectors"]) == 3
    
    def test_invalid_exchange(self, market_service):
        """测试无效交易所处理"""
        # 尝试添加不支持的交易所
        with pytest.raises(Exception):
            market_service.add_exchange("invalid_exchange", "spot")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, market_service):
        """测试并发操作"""
        # 启动服务
        await market_service.start()
        
        # 并发订阅多个交易对
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                market_service.subscribe([f"SYM{i}/USDT"], "binance", "spot")
            )
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 检查服务状态
        assert market_service.is_running
        
        # 停止服务
        await market_service.stop()