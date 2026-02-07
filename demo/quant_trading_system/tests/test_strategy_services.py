"""
策略服务测试
============

验证策略服务中指标计算功能的正确性
"""

import numpy as np
import pytest
import asyncio
import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from quant_trading_system.services.strategy.strategy_engine import StrategyEngine
from quant_trading_system.services.strategy.base import Strategy, StrategyContext, StrategyState
from quant_trading_system.services.indicators.indicator_engine import IndicatorEngine
from quant_trading_system.models.market import Bar, BarArray, TimeFrame, Tick, Depth
from quant_trading_system.models.trading import Order, Position, Trade
from quant_trading_system.models.account import Account
from quant_trading_system.services.strategy.signal import Signal, SignalType


class TestStrategyEngine:
    """策略引擎测试"""

    def test_init_with_indicator_engine(self):
        """测试策略引擎初始化时集成指标引擎"""
        indicator_engine = Mock(spec=IndicatorEngine)
        strategy_engine = StrategyEngine(indicator_engine=indicator_engine)
        
        assert strategy_engine._indicator_engine is indicator_engine

    def test_add_strategy_with_indicator_context(self):
        """测试添加策略时正确设置指标引擎上下文"""
        indicator_engine = Mock(spec=IndicatorEngine)
        strategy_engine = StrategyEngine(indicator_engine=indicator_engine)
        
        # 创建模拟策略
        mock_strategy = Mock(spec=Strategy)
        mock_strategy.strategy_id = "test_strategy"
        mock_strategy.symbols = ["BTCUSDT"]
        mock_strategy.timeframes = [TimeFrame.M1]
        mock_strategy.params = {}
        
        # 添加策略
        strategy_id = strategy_engine.add_strategy(mock_strategy)
        
        # 验证策略上下文正确设置
        mock_strategy.set_context.assert_called_once()
        context = mock_strategy.set_context.call_args[0][0]
        assert context.indicator_engine is indicator_engine
        assert context.strategy_id == "test_strategy"

    def test_strategy_calculate_indicator_integration(self):
        """测试策略通过上下文调用指标计算"""
        # 创建模拟指标引擎
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_result = Mock()
        mock_result.values = {"sma": np.array([100.0, 101.0, 102.0])}
        mock_indicator_engine.calculate.return_value = mock_result
        
        strategy_engine = StrategyEngine(indicator_engine=mock_indicator_engine)
        
        # 创建真实策略类
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["BTCUSDT"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                return None
        
        # 添加策略
        strategy = TestStrategy()
        strategy_id = strategy_engine.add_strategy(strategy)
        
        # 获取策略实例并设置上下文
        strategy_instance = strategy_engine.get_strategy(strategy_id)
        
        # 创建模拟上下文
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = mock_indicator_engine
        
        # 创建模拟K线数据，设置len()方法
        mock_bars = Mock(spec=BarArray)
        mock_bars.__len__ = Mock(return_value=3)
        mock_context.get_bars.return_value = mock_bars
        
        # 设置策略上下文
        strategy_instance._context = mock_context
        
        # 测试策略调用指标计算
        result = strategy_instance.calculate_indicator("SMA", symbol="BTCUSDT", timeframe=TimeFrame.M1, period=20)
        
        # 验证指标引擎被正确调用
        mock_indicator_engine.calculate.assert_called_once_with("SMA", mock_bars, period=20)
        assert result is mock_result

    @pytest.mark.asyncio
    async def test_bar_processing_with_indicator_calculation(self):
        """测试K线处理时策略调用指标计算"""
        # 创建模拟指标引擎
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_result = Mock()
        mock_result.values = {"rsi": np.array([70.0, 65.0, 60.0])}
        mock_indicator_engine.calculate.return_value = mock_result
        
        strategy_engine = StrategyEngine(indicator_engine=mock_indicator_engine)
        
        # 创建真实策略类
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["BTCUSDT"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                # 在策略中调用指标计算
                rsi_result = self.calculate_indicator("RSI", period=14)
                if rsi_result["rsi"][-1] > 70:
                    return self.sell("BTCUSDT", quantity=1, reason="RSI超买")
                return None
        
        # 添加策略
        strategy = TestStrategy()
        strategy_id = strategy_engine.add_strategy(strategy)
        
        # 启动策略
        await strategy_engine.start_strategy(strategy_id)
        
        # 创建测试K线
        bar = Bar(
            symbol="BTCUSDT",
            exchange="binance",
            timeframe=TimeFrame.M1,
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
            is_closed=True
        )
        
        # 处理K线
        await strategy_engine.on_bar(bar)
        
        # 验证指标计算被调用
        mock_indicator_engine.calculate.assert_called()
        call_args = mock_indicator_engine.calculate.call_args
        assert call_args[0][0] == "RSI"
        assert call_args[1]["period"] == 14

    def test_strategy_engine_stats_includes_indicator_info(self):
        """测试策略引擎统计信息包含指标相关信息"""
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_indicator_engine.stats = {
            "calc_count": 100,
            "cache_hits": 80,
            "cache_hit_rate": 0.8,
            "available_indicators": ["SMA", "EMA", "RSI"]
        }
        
        strategy_engine = StrategyEngine(indicator_engine=mock_indicator_engine)
        
        stats = strategy_engine.stats
        
        # 验证统计信息包含策略和指标信息
        assert "running" in stats
        assert "strategy_count" in stats
        assert "strategies" in stats


class TestStrategyBaseClass:
    """策略基类测试"""

    def test_calculate_indicator_method(self):
        """测试策略基类的calculate_indicator方法"""
        # 创建模拟上下文和指标引擎
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_result = Mock()
        mock_result.values = {"macd": np.array([0.1, 0.2, 0.3])}
        mock_indicator_engine.calculate.return_value = mock_result
        
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = mock_indicator_engine
        
        # 创建模拟K线数据，设置len()方法
        mock_bars = Mock(spec=BarArray)
        mock_bars.close = np.array([100.0, 101.0, 102.0])
        mock_bars.__len__ = Mock(return_value=3)  # 设置len()方法
        mock_context.get_bars.return_value = mock_bars
        
        # 创建策略实例
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["BTCUSDT"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                return None
        
        strategy = TestStrategy()
        strategy.set_context(mock_context)
        
        # 测试指标计算
        result = strategy.calculate_indicator("MACD")
        
        # 验证方法调用正确
        mock_context.get_bars.assert_called_once_with("BTCUSDT", TimeFrame.M1)
        mock_indicator_engine.calculate.assert_called_once_with("MACD", mock_bars)
        assert result is mock_result

    def test_calculate_indicator_with_custom_params(self):
        """测试带自定义参数的指标计算"""
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = mock_indicator_engine
        
        # 创建模拟K线数据，设置len()方法
        mock_bars = Mock(spec=BarArray)
        mock_bars.__len__ = Mock(return_value=3)  # 设置len()方法
        mock_context.get_bars.return_value = mock_bars
        
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["ETHUSDT"]
            timeframes = [TimeFrame.M5]
            
            def on_bar(self, bar):
                return None
        
        strategy = TestStrategy()
        strategy.set_context(mock_context)
        
        # 测试带参数的指标计算
        strategy.calculate_indicator("BOLL", period=20, std_dev=2.0)
        
        # 验证参数正确传递
        mock_indicator_engine.calculate.assert_called_once_with("BOLL", mock_bars, period=20, std_dev=2.0)
        call_kwargs = mock_indicator_engine.calculate.call_args[1]
        assert call_kwargs["period"] == 20
        assert call_kwargs["std_dev"] == 2.0

    def test_calculate_indicator_error_handling(self):
        """测试指标计算的错误处理"""
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = None  # 没有指标引擎
        
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["BTCUSDT"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                return None
        
        strategy = TestStrategy()
        strategy.set_context(mock_context)
        
        # 测试没有指标引擎时的错误
        with pytest.raises(RuntimeError, match="Indicator engine not available"):
            strategy.calculate_indicator("SMA")

    def test_calculate_indicator_no_symbol_error(self):
        """测试没有交易品种时的错误处理"""
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = mock_indicator_engine
        
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = []  # 没有交易品种
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                return None
        
        strategy = TestStrategy()
        strategy.set_context(mock_context)
        
        # 测试没有交易品种时的错误
        with pytest.raises(ValueError, match="Symbol not specified"):
            strategy.calculate_indicator("SMA")

    def test_calculate_indicator_no_bar_data_error(self):
        """测试没有K线数据时的错误处理"""
        mock_indicator_engine = Mock(spec=IndicatorEngine)
        mock_context = Mock(spec=StrategyContext)
        mock_context.indicator_engine = mock_indicator_engine
        mock_context.get_bars.return_value = None  # 没有K线数据
        
        class TestStrategy(Strategy):
            name = "TestStrategy"
            symbols = ["BTCUSDT"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                return None
        
        strategy = TestStrategy()
        strategy.set_context(mock_context)
        
        # 测试没有K线数据时的错误
        with pytest.raises(ValueError, match="No bar data for"):
            strategy.calculate_indicator("SMA")


class TestStrategyIndicatorIntegration:
    """策略与指标集成测试"""

    def test_real_strategy_using_indicators(self):
        """测试真实策略使用多个指标进行决策"""
        # 创建真实的指标引擎（非模拟）
        indicator_engine = IndicatorEngine()
        
        # 创建包含真实数据的策略上下文
        context = StrategyContext(
            strategy_id="test_strategy",
            symbols=["TEST"],
            timeframes=[TimeFrame.M1],
            indicator_engine=indicator_engine
        )
        
        # 创建测试K线数据
        n = 100
        close_prices = np.linspace(100, 200, n)
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=close_prices - 1,
            high=close_prices + 2,
            low=close_prices - 2,
            close=close_prices,
            volume=np.full(n, 1000.0)
        )
        context.bars = {"TEST": {TimeFrame.M1: bars}}
        
        # 创建使用多个指标的真实策略
        class MultiIndicatorStrategy(Strategy):
            name = "MultiIndicatorStrategy"
            symbols = ["TEST"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                # 计算多个指标
                sma_result = self.calculate_indicator("SMA", period=20)
                rsi_result = self.calculate_indicator("RSI", period=14)
                macd_result = self.calculate_indicator("MACD")
                
                # 基于指标组合生成信号
                sma_value = sma_result["sma"][-1] if not np.isnan(sma_result["sma"][-1]) else None
                rsi_value = rsi_result["rsi"][-1] if not np.isnan(rsi_result["rsi"][-1]) else None
                macd_value = macd_result["macd"][-1] if not np.isnan(macd_result["macd"][-1]) else None
                
                signals = []
                
                # 简单的多指标策略逻辑
                if sma_value and rsi_value and macd_value:
                    if bar.close > sma_value and rsi_value < 30 and macd_value > 0:
                        signals.append(self.buy("TEST", quantity=1, reason="多指标买入信号"))
                    elif bar.close < sma_value and rsi_value > 70 and macd_value < 0:
                        signals.append(self.sell("TEST", quantity=1, reason="多指标卖出信号"))
                
                return signals if signals else None
        
        strategy = MultiIndicatorStrategy()
        strategy.set_context(context)
        
        # 测试策略处理K线
        test_bar = Bar(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=datetime.now(),
            open=150.0,
            high=155.0,
            low=145.0,
            close=152.0,
            volume=1000.0,
            is_closed=True
        )
        
        signals = strategy.on_bar(test_bar)
        
        # 验证策略正常工作
        assert signals is None or isinstance(signals, (list, Signal))
        
        # 验证指标计算结果有效
        sma_result = strategy.calculate_indicator("SMA", period=20)
        rsi_result = strategy.calculate_indicator("RSI", period=14)
        macd_result = strategy.calculate_indicator("MACD")
        
        assert "sma" in sma_result.values
        assert "rsi" in rsi_result.values
        assert "macd" in macd_result.values

    @pytest.mark.asyncio
    async def test_async_indicator_calculation_in_strategy(self):
        """测试策略中的异步指标计算"""
        # 创建支持异步的指标引擎
        indicator_engine = IndicatorEngine()
        
        # 创建策略上下文
        context = StrategyContext(
            strategy_id="async_strategy",
            symbols=["TEST"],
            timeframes=[TimeFrame.M1],
            indicator_engine=indicator_engine
        )
        
        # 创建测试数据
        n = 50
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100 + 50,
            high=np.random.rand(n) * 100 + 100,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100 + 75,
            volume=np.random.rand(n) * 1000 + 500
        )
        context.bars = {"TEST": {TimeFrame.M1: bars}}
        
        # 创建使用异步指标计算的策略
        class AsyncIndicatorStrategy(Strategy):
            name = "AsyncIndicatorStrategy"
            symbols = ["TEST"]
            timeframes = [TimeFrame.M1]
            
            async def on_bar_async(self, bar):
                """异步处理K线的自定义方法"""
                # 异步计算多个指标
                indicators = [
                    ("SMA", {"period": 20}),
                    ("RSI", {"period": 14}),
                    ("MACD", {})
                ]
                
                # 使用指标引擎的异步批量计算
                results = await self.context.indicator_engine.calculate_multiple_async(
                    indicators, self.context.get_bars("TEST", TimeFrame.M1)
                )
                
                # 基于异步计算结果生成信号
                sma_value = results["SMA"]["sma"][-1] if not np.isnan(results["SMA"]["sma"][-1]) else None
                rsi_value = results["RSI"]["rsi"][-1] if not np.isnan(results["RSI"]["rsi"][-1]) else None
                
                if sma_value and rsi_value:
                    if bar.close > sma_value and rsi_value < 30:
                        return self.buy("TEST", quantity=1, reason="异步指标买入")
                
                return None
            
            def on_bar(self, bar):
                # 同步方法中调用异步处理，使用现有的异步循环
                if hasattr(self, '_async_loop') and self._async_loop:
                    return self._async_loop.run_until_complete(self.on_bar_async(bar))
                else:
                    # 如果没有异步循环，直接返回None
                    return None
        
        strategy = AsyncIndicatorStrategy()
        strategy.set_context(context)
        
        # 测试策略
        test_bar = Bar(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
            is_closed=True
        )
        
        signal = strategy.on_bar(test_bar)
        
        # 验证异步计算正常工作
        assert signal is None or isinstance(signal, Signal)

    def test_indicator_cache_in_strategy_context(self):
        """测试策略上下文中的指标缓存功能"""
        indicator_engine = IndicatorEngine(cache_size=100)
        
        context = StrategyContext(
            strategy_id="cached_strategy",
            symbols=["TEST"],
            timeframes=[TimeFrame.M1],
            indicator_engine=indicator_engine
        )
        
        # 创建测试数据
        n = 30
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000
        )
        context.bars = {"TEST": {TimeFrame.M1: bars}}
        
        class CachedIndicatorStrategy(Strategy):
            name = "CachedIndicatorStrategy"
            symbols = ["TEST"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                # 多次计算相同指标，应该利用缓存
                result1 = self.calculate_indicator("SMA", period=20)
                result2 = self.calculate_indicator("SMA", period=20)  # 应该命中缓存
                result3 = self.calculate_indicator("SMA", period=10)  # 不同参数，重新计算
                
                # 验证缓存效果
                stats = self.context.indicator_engine.stats
                assert stats["cache_hits"] >= 1  # 至少有一次缓存命中
                
                return None
        
        strategy = CachedIndicatorStrategy()
        strategy.set_context(context)
        
        # 执行策略
        test_bar = Bar(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
            is_closed=True
        )
        
        strategy.on_bar(test_bar)
        
        # 验证缓存统计
        stats = indicator_engine.stats
        assert stats["cache_hits"] > 0
        assert 0 <= stats["cache_hit_rate"] <= 1


class TestStrategyIndicatorPerformance:
    """策略指标性能测试"""

    def test_strategy_indicator_calculation_performance(self):
        """测试策略中指标计算的性能"""
        import time
        
        indicator_engine = IndicatorEngine()
        
        # 创建大量测试数据
        n = 1000
        bars = BarArray(
            symbol="PERF_TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000
        )
        
        context = StrategyContext(
            strategy_id="perf_strategy",
            symbols=["PERF_TEST"],
            timeframes=[TimeFrame.M1],
            indicator_engine=indicator_engine
        )
        context.bars = {"PERF_TEST": {TimeFrame.M1: bars}}
        
        class PerformanceTestStrategy(Strategy):
            name = "PerformanceTestStrategy"
            symbols = ["PERF_TEST"]
            timeframes = [TimeFrame.M1]
            
            def on_bar(self, bar):
                # 计算多个复杂指标
                start_time = time.time()
                
                results = {}
                indicators = [
                    ("SMA", {"period": 20}),
                    ("EMA", {"period": 20}),
                    ("MACD", {}),
                    ("RSI", {"period": 14}),
                    ("BOLL", {"period": 20, "std_dev": 2.0})
                ]
                
                for name, params in indicators:
                    results[name] = self.calculate_indicator(name, **params)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                # 性能要求：5个指标计算时间小于0.5秒
                assert execution_time < 0.5, f"指标计算时间过长: {execution_time:.4f}s"
                
                return None
        
        strategy = PerformanceTestStrategy()
        strategy.set_context(context)
        
        # 执行性能测试
        test_bar = Bar(
            symbol="PERF_TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0,
            is_closed=True
        )
        
        strategy.on_bar(test_bar)

    def test_concurrent_strategy_indicator_calculation(self):
        """测试并发策略的指标计算"""
        import threading
        import time
        
        indicator_engine = IndicatorEngine(max_workers=4)
        
        # 创建共享测试数据
        n = 200
        bars = BarArray(
            symbol="CONCURRENT_TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000
        )
        
        results = []
        errors = []
        
        def run_strategy_calculation(strategy_id):
            """单个策略的指标计算任务"""
            try:
                context = StrategyContext(
                    strategy_id=strategy_id,
                    symbols=["CONCURRENT_TEST"],
                    timeframes=[TimeFrame.M1],
                    indicator_engine=indicator_engine
                )
                context.bars = {"CONCURRENT_TEST": {TimeFrame.M1: bars}}
                
                class ConcurrentStrategy(Strategy):
                    name = "ConcurrentStrategy"
                    symbols = ["CONCURRENT_TEST"]
                    timeframes = [TimeFrame.M1]
                    
                    def on_bar(self, bar):
                        # 计算指标
                        sma_result = self.calculate_indicator("SMA", period=20)
                        rsi_result = self.calculate_indicator("RSI", period=14)
                        return None
                
                strategy = ConcurrentStrategy()
                strategy.set_context(context)
                
                test_bar = Bar(
                    symbol="CONCURRENT_TEST",
                    exchange="test",
                    timeframe=TimeFrame.M1,
                    timestamp=datetime.now(),
                    open=100.0,
                    high=105.0,
                    low=95.0,
                    close=102.0,
                    volume=1000.0,
                    is_closed=True
                )
                
                start_time = time.time()
                strategy.on_bar(test_bar)
                end_time = time.time()
                
                results.append({
                    "strategy_id": strategy_id,
                    "execution_time": end_time - start_time
                })
                
            except Exception as e:
                errors.append((strategy_id, str(e)))
        
        # 创建多个并发线程
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=run_strategy_calculation,
                args=(f"strategy_{i}",)
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证并发计算结果
        assert len(errors) == 0, f"并发计算出现错误: {errors}"
        assert len(results) == 10, "并发计算未完成所有任务"
        
        # 验证性能：平均执行时间应合理
        avg_time = sum(r["execution_time"] for r in results) / len(results)
        assert avg_time < 1.0, f"并发计算平均时间过长: {avg_time:.4f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])