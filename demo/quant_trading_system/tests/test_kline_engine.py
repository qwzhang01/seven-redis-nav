import pytest
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from quant_trading_system.services.market.kline_engine import (
    KLineBuffer,
    KLineEngine,
    KLineAggregator
)
from quant_trading_system.models.market import Bar, BarArray, Tick, TimeFrame


class TestKLineBuffer:
    """K线缓冲区测试"""
    
    @pytest.fixture
    def kline_buffer(self):
        """创建K线缓冲区实例"""
        return KLineBuffer(
            symbol="BTC/USDT",
            exchange="binance",
            timeframe=TimeFrame.M1,
            max_size=100
        )
    
    @pytest.fixture
    def sample_bar(self):
        """创建示例K线数据"""
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
    
    def test_initialization(self, kline_buffer):
        """测试初始化"""
        assert kline_buffer.symbol == "BTC/USDT"
        assert kline_buffer.exchange == "binance"
        assert kline_buffer.timeframe == TimeFrame.M1
        assert kline_buffer.max_size == 100
        assert kline_buffer.count == 0
        assert kline_buffer.is_empty
    
    def test_append_bar(self, kline_buffer, sample_bar):
        """测试添加K线"""
        kline_buffer.append(sample_bar)
        
        assert kline_buffer.count == 1
        assert not kline_buffer.is_empty
        
        # 验证数据存储
        last_bars = kline_buffer.get_last(1)
        assert len(last_bars) == 1
        assert last_bars[0].timestamp == sample_bar.timestamp
        assert last_bars[0].open == sample_bar.open
    
    def test_append_multiple_bars(self, kline_buffer, sample_bar):
        """测试添加多个K线"""
        for i in range(5):
            bar = Bar(
                symbol="BTC/USDT",
                exchange="binance",
                timeframe=TimeFrame.M1,
                timestamp=1700000000000 + i * 60000,
                open=50000.0 + i * 100,
                high=50100.0 + i * 100,
                low=49900.0 + i * 100,
                close=50050.0 + i * 100,
                volume=1000.0 + i * 100,
                turnover=50050000.0 + i * 50000
            )
            kline_buffer.append(bar)
        
        assert kline_buffer.count == 5
        
        # 获取最后3根K线
        last_3 = kline_buffer.get_last(3)
        assert len(last_3) == 3
        assert last_3[0].timestamp == 1700000000000 + 2 * 60000
        assert last_3[2].timestamp == 1700000000000 + 4 * 60000
    
    def test_buffer_wraparound(self, kline_buffer, sample_bar):
        """测试缓冲区循环覆盖"""
        # 添加超过缓冲区大小的K线
        for i in range(kline_buffer.max_size + 10):
            bar = Bar(
                symbol="BTC/USDT",
                exchange="binance",
                timeframe=TimeFrame.M1,
                timestamp=1700000000000 + i * 60000,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=1000.0,
                turnover=50050000.0
            )
            kline_buffer.append(bar)
        
        # 缓冲区应该保持最大大小
        assert kline_buffer.count == kline_buffer.max_size
        
        # 获取所有K线
        all_bars = kline_buffer.get_last(kline_buffer.max_size)
        assert len(all_bars) == kline_buffer.max_size
        
        # 验证时间戳顺序
        timestamps = [bar.timestamp for bar in all_bars]
        assert all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))
    
    def test_update_last_bar(self, kline_buffer, sample_bar):
        """测试更新最后一根K线"""
        # 先添加一根K线
        kline_buffer.append(sample_bar)
        
        # 更新最后一根K线
        updated_bar = Bar(
            symbol="BTC/USDT",
            exchange="binance",
            timeframe=TimeFrame.M1,
            timestamp=1700000000000,
            open=50000.0,
            high=50200.0,  # 更新最高价
            low=49800.0,   # 更新最低价
            close=50100.0,  # 更新收盘价
            volume=1500.0, # 更新成交量
            turnover=75150000.0
        )
        kline_buffer.update_last(updated_bar)
        
        # 验证更新
        last_bar = kline_buffer.get_last(1)[0]
        assert last_bar.high == 50200.0
        assert last_bar.low == 49800.0
        assert last_bar.close == 50100.0
        assert last_bar.volume == 1500.0
    
    def test_get_bar_array(self, kline_buffer, sample_bar):
        """测试获取K线数组"""
        # 添加多根K线
        for i in range(5):
            bar = Bar(
                symbol="BTC/USDT",
                exchange="binance",
                timeframe=TimeFrame.M1,
                timestamp=1700000000000 + i * 60000,
                open=50000.0 + i * 100,
                high=50100.0 + i * 100,
                low=49900.0 + i * 100,
                close=50050.0 + i * 100,
                volume=1000.0 + i * 100,
                turnover=50050000.0 + i * 50000
            )
            kline_buffer.append(bar)
        
        bar_array = kline_buffer.get_array()
        
        assert isinstance(bar_array, BarArray)
        assert len(bar_array) == 5
        assert bar_array.symbol == "BTC/USDT"
        assert bar_array.exchange == "binance"
        assert bar_array.timeframe == TimeFrame.M1
        
        # 验证数据正确性
        assert bar_array.open[0] == 50000.0
        assert bar_array.high[4] == 50100.0 + 4 * 100
        assert bar_array.low[2] == 49900.0 + 2 * 100
        assert bar_array.close[3] == 50050.0 + 3 * 100
    
    def test_get_empty_array(self, kline_buffer):
        """测试获取空数组"""
        bar_array = kline_buffer.get_array()
        
        assert isinstance(bar_array, BarArray)
        assert len(bar_array) == 0
        assert bar_array.symbol == "BTC/USDT"
        assert bar_array.exchange == "binance"
        assert bar_array.timeframe == TimeFrame.M1


class TestKLineEngine:
    """K线合成引擎测试"""
    
    @pytest.fixture
    def kline_engine(self):
        """创建K线合成引擎实例"""
        return KLineEngine(buffer_size=100)
    
    @pytest.fixture
    def sample_tick(self):
        """创建示例Tick数据"""
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
    
    def test_initialization(self, kline_engine):
        """测试初始化"""
        assert kline_engine.buffer_size == 100
        assert len(kline_engine._timeframes) > 0
        assert kline_engine._tick_count == 0
        assert kline_engine._bar_count == 0
    
    def test_add_timeframe(self, kline_engine):
        """测试添加时间周期"""
        new_timeframe = TimeFrame.M3  # 假设3分钟周期
        
        kline_engine.add_timeframe(new_timeframe)
        
        assert new_timeframe in kline_engine._timeframes
    
    def test_add_and_remove_callback(self, kline_engine):
        """测试添加和移除回调函数"""
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        
        # 添加回调
        kline_engine.add_callback(callback1, TimeFrame.M1)
        kline_engine.add_callback(callback2, TimeFrame.M1)
        kline_engine.add_callback(callback1)  # 通用回调
        
        assert len(kline_engine._callbacks[TimeFrame.M1]) == 2
        assert len(kline_engine._general_callbacks) == 1
        
        # 移除回调
        kline_engine.remove_callback(callback1, TimeFrame.M1)
        kline_engine.remove_callback(callback1)  # 通用回调
        
        assert len(kline_engine._callbacks[TimeFrame.M1]) == 1
        assert len(kline_engine._general_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_process_tick_new_bar(self, kline_engine, sample_tick):
        """测试处理Tick数据 - 新K线"""
        # 设置回调函数
        callback = AsyncMock()
        kline_engine.add_callback(callback, TimeFrame.M1)
        
        await kline_engine.process_tick(sample_tick)
        
        # 验证统计信息
        assert kline_engine._tick_count == 1
        
        # 验证当前K线
        current_bar = kline_engine.get_current_bar("BTC/USDT", TimeFrame.M1)
        assert current_bar is not None
        assert current_bar.open == 50000.0
        assert current_bar.high == 50000.0
        assert current_bar.low == 50000.0
        assert current_bar.close == 50000.0
        assert not current_bar.is_closed
        
        # 回调应该还没有被调用（K线未完成）
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_tick_update_bar(self, kline_engine, sample_tick):
        """测试处理Tick数据 - 更新K线"""
        # 先处理一个Tick
        await kline_engine.process_tick(sample_tick)
        
        # 处理第二个Tick（相同K线周期）
        tick2 = Tick(
            symbol="BTC/USDT",
            exchange="binance",
            timestamp=1700000005000,  # 同一分钟内的不同时间
            last_price=50100.0,      # 更高价格
            bid_price=50099.0,
            ask_price=50101.0,
            bid_size=1.0,
            ask_size=1.0,
            volume=1500.0,
            turnover=75150000.0,
            is_trade=True,
            trade_id="test_trade_002"
        )
        
        await kline_engine.process_tick(tick2)
        
        # 验证K线更新
        current_bar = kline_engine.get_current_bar("BTC/USDT", TimeFrame.M1)
        assert current_bar.high == 50100.0  # 更新最高价
        assert current_bar.low == 50000.0   # 最低价不变
        assert current_bar.close == 50100.0  # 更新收盘价
        assert current_bar.volume == 2500.0  # 累计成交量
    
    @pytest.mark.asyncio
    async def test_process_tick_new_timeframe(self, kline_engine, sample_tick):
        """测试处理Tick数据 - 新时间周期"""
        # 处理一个Tick
        await kline_engine.process_tick(sample_tick)
        
        # 处理下一个周期的Tick
        tick2 = Tick(
            symbol="BTC/USDT",
            exchange="binance",
            timestamp=1700000600000,  # 下一分钟
            last_price=50200.0,
            bid_price=50199.0,
            ask_price=50201.0,
            bid_size=1.0,
            ask_size=1.0,
            volume=500.0,
            turnover=25100000.0,
            is_trade=True,
            trade_id="test_trade_003"
        )
        
        callback = AsyncMock()
        kline_engine.add_callback(callback, TimeFrame.M1)
        
        await kline_engine.process_tick(tick2)
        
        # 验证K线数量
        bars = kline_engine.get_bars("BTC/USDT", TimeFrame.M1, limit=10)
        assert len(bars) == 1  # 第一根K线已完成
        
        # 验证回调被调用
        callback.assert_called_once()
        
        # 验证当前K线
        current_bar = kline_engine.get_current_bar("BTC/USDT", TimeFrame.M1)
        assert current_bar.open == 50200.0
        assert current_bar.timestamp == 1700000600000
    
    def test_get_bar_start_time(self, kline_engine):
        """测试计算K线开始时间"""
        # 测试1分钟周期
        timestamp = 1700000000123  # 2023-11-14 08:53:20.123
        start_time = kline_engine._get_bar_start_time(timestamp, TimeFrame.M1)
        assert start_time == 1700000000000  # 2023-11-14 08:53:00.000
        
        # 测试5分钟周期
        start_time = kline_engine._get_bar_start_time(timestamp, TimeFrame.M5)
        assert start_time == 1699999800000  # 2023-11-14 08:50:00.000
        
        # 测试1小时周期
        start_time = kline_engine._get_bar_start_time(timestamp, TimeFrame.H1)
        assert start_time == 1699999200000  # 2023-11-14 08:00:00.000
    
    def test_get_bars_empty(self, kline_engine):
        """测试获取空K线列表"""
        bars = kline_engine.get_bars("BTC/USDT", TimeFrame.M1, limit=10)
        assert len(bars) == 0
    
    def test_get_bar_array_empty(self, kline_engine):
        """测试获取空K线数组"""
        bar_array = kline_engine.get_bar_array("BTC/USDT", TimeFrame.M1, limit=10)
        assert isinstance(bar_array, BarArray)
        assert len(bar_array) == 0
    
    def test_stats_property(self, kline_engine):
        """测试统计信息属性"""
        stats = kline_engine.stats
        
        assert "tick_count" in stats
        assert "bar_count" in stats
        assert "symbols" in stats
        assert "timeframes" in stats
        
        assert stats["tick_count"] == 0
        assert stats["bar_count"] == 0
        assert stats["symbols"] == []
    
    def test_clear_data(self, kline_engine, sample_tick):
        """测试清除数据"""
        # 添加一些数据
        asyncio.run(kline_engine.process_tick(sample_tick))
        
        # 清除数据
        kline_engine.clear()
        
        # 验证数据被清除
        assert kline_engine._tick_count == 0
        assert kline_engine._bar_count == 0
        assert len(kline_engine._buffers) == 0
        assert len(kline_engine._current_bars) == 0


class TestKLineAggregator:
    """K线聚合器测试"""
    
    @pytest.fixture
    def aggregator(self):
        """创建聚合器实例"""
        return KLineAggregator()
    
    @pytest.fixture
    def sample_bars(self):
        """创建示例K线列表"""
        bars = []
        for i in range(4):
            bar = Bar(
                symbol="BTC/USDT",
                exchange="binance",
                timeframe=TimeFrame.M15,
                timestamp=1700000000000 + i * 900000,  # 15分钟间隔
                open=50000.0 + i * 100,
                high=50100.0 + i * 100,
                low=49900.0 + i * 100,
                close=50050.0 + i * 100,
                volume=1000.0 + i * 100,
                turnover=50050000.0 + i * 50000
            )
            bars.append(bar)
        return bars
    
    def test_aggregate_15m_to_1h(self, aggregator, sample_bars):
        """测试15分钟K线聚合为1小时K线"""
        aggregated = aggregator.aggregate(sample_bars, TimeFrame.H1)
        
        assert len(aggregated) == 1  # 4根15分钟K线 = 1根1小时K线
        
        result_bar = aggregated[0]
        assert result_bar.timeframe == TimeFrame.H1
        assert result_bar.open == 50000.0  # 第一根K线的开盘价
        assert result_bar.high == 50300.0  # 最高价
        assert result_bar.low == 49900.0   # 最低价
        assert result_bar.close == 50350.0 # 最后一根K线的收盘价
        assert result_bar.volume == 4600.0  # 总成交量
    
    def test_aggregate_smaller_timeframe(self, aggregator, sample_bars):
        """测试小周期K线聚合"""
        # 从15分钟聚合到30分钟
        aggregated = aggregator.aggregate(sample_bars, TimeFrame.M30)
        
        assert len(aggregated) == 2  # 4根15分钟K线 = 2根30分钟K线
        
        # 验证第一根聚合K线
        bar1 = aggregated[0]
        assert bar1.timeframe == TimeFrame.M30
        assert bar1.open == 50000.0
        assert bar1.high == 50200.0
        assert bar1.low == 49900.0
        assert bar1.close == 50150.0
        assert bar1.volume == 2100.0
        
        # 验证第二根聚合K线
        bar2 = aggregated[1]
        assert bar2.open == 50200.0
        assert bar2.high == 50300.0
        assert bar2.low == 50100.0
        assert bar2.close == 50350.0
        assert bar2.volume == 2500.0
    
    def test_aggregate_empty_list(self, aggregator):
        """测试空列表聚合"""
        aggregated = aggregator.aggregate([], TimeFrame.H1)
        assert len(aggregated) == 0
    
    def test_aggregate_same_timeframe(self, aggregator, sample_bars):
        """测试相同时间周期聚合"""
        # 从15分钟聚合到15分钟（无需聚合）
        aggregated = aggregator.aggregate(sample_bars, TimeFrame.M15)
        
        assert len(aggregated) == len(sample_bars)
        assert aggregated == sample_bars
    
    def test_aggregate_irregular_bars(self, aggregator):
        """测试不规则K线聚合"""
        # 创建不规则时间间隔的K线
        bars = []
        timestamps = [1700000000000, 1700000900000, 1700001800000]  # 不规则间隔
        
        for i, ts in enumerate(timestamps):
            bar = Bar(
                symbol="BTC/USDT",
                exchange="binance",
                timeframe=TimeFrame.M15,
                timestamp=ts,
                open=50000.0 + i * 100,
                high=50100.0 + i * 100,
                low=49900.0 + i * 100,
                close=50050.0 + i * 100,
                volume=1000.0 + i * 100,
                turnover=50050000.0 + i * 50000
            )
            bars.append(bar)
        
        # 聚合到1小时
        aggregated = aggregator.aggregate(bars, TimeFrame.H1)
        
        # 应该只有一根K线（所有K线都在同一小时内）
        assert len(aggregated) == 1
        assert aggregated[0].timeframe == TimeFrame.H1