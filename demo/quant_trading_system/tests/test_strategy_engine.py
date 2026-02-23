import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from datetime import datetime

from quant_trading_system.services import Strategy
from quant_trading_system.services.strategy.strategy_engine import StrategyEngine
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.core.events import EventEngine, EventType
from quant_trading_system.services.strategy.base import StrategyState


class TestStrategyEngine:
    """策略引擎测试"""

    @pytest.fixture
    def strategy_engine(self):
        """创建策略引擎实例"""
        event_engine = EventEngine()
        return StrategyEngine(event_engine=event_engine)

    @pytest.fixture
    def mock_strategy(self):
        """模拟策略"""
        return Strategy(
            strategy_id="test_strategy_001",
            name="Test Strategy",
            type="trend_following",
            symbols=["BTC/USDT", "ETH/USDT"],
            timeframe="1m",
            parameters={"lookback": 20, "threshold": 0.02},
            status=StrategyState.ACTIVE,
            created_time=datetime.now(),
            updated_time=datetime.now()
        )

    @pytest.fixture
    def mock_order(self):
        """模拟订单"""
        return Order(
            order_id="test_order_001",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account",
            strategy_id="test_strategy_001"
        )

    @pytest.fixture
    def mock_market_data(self):
        """模拟市场数据"""
        return {
            "symbol": "BTC/USDT",
            "timestamp": 1700000000000,
            "open": 50000.0,
            "high": 50100.0,
            "low": 49900.0,
            "close": 50050.0,
            "volume": 1000.0,
            "turnover": 50050000.0
        }

    @pytest.mark.asyncio
    async def test_start_stop(self, strategy_engine):
        """测试启动和停止"""
        # 测试启动
        await strategy_engine.start()
        assert strategy_engine.is_running

        # 测试停止
        await strategy_engine.stop()
        assert not strategy_engine.is_running

    @pytest.mark.asyncio
    async def test_add_strategy(self, strategy_engine, mock_strategy):
        """测试添加策略"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 检查策略是否添加成功
        assert mock_strategy.strategy_id in strategy_engine._strategies
        assert strategy_engine._strategies[mock_strategy.strategy_id] == mock_strategy

        # 检查策略实例是否创建
        assert mock_strategy.strategy_id in strategy_engine._strategy_instances

    @pytest.mark.asyncio
    async def test_remove_strategy(self, strategy_engine, mock_strategy):
        """测试移除策略"""
        # 先添加策略
        await strategy_engine.add_strategy(mock_strategy)
        assert mock_strategy.strategy_id in strategy_engine._strategies

        # 移除策略
        await strategy_engine.remove_strategy(mock_strategy.strategy_id)

        # 检查策略是否移除成功
        assert mock_strategy.strategy_id not in strategy_engine._strategies
        assert mock_strategy.strategy_id not in strategy_engine._strategy_instances

    @pytest.mark.asyncio
    async def test_update_strategy(self, strategy_engine, mock_strategy):
        """测试更新策略"""
        # 先添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 更新策略参数
        updated_params = {"lookback": 30, "threshold": 0.03}
        mock_strategy.parameters = updated_params

        await strategy_engine.update_strategy(mock_strategy)

        # 检查策略是否更新成功
        updated = strategy_engine._strategies[mock_strategy.strategy_id]
        assert updated.parameters == updated_params

    @pytest.mark.asyncio
    async def test_pause_resume_strategy(self, strategy_engine, mock_strategy):
        """测试暂停和恢复策略"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 暂停策略
        await strategy_engine.pause_strategy(mock_strategy.strategy_id)

        # 检查策略状态
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.PAUSED

        # 恢复策略
        await strategy_engine.resume_strategy(mock_strategy.strategy_id)

        # 检查策略状态
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.ACTIVE

    @pytest.mark.asyncio
    async def test_on_market_data(self, strategy_engine, mock_strategy, mock_market_data):
        """测试处理市场数据"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例
        mock_strategy_instance = Mock()
        mock_strategy_instance.on_market_data = AsyncMock()
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 处理市场数据
        await strategy_engine.on_market_data(mock_market_data)

        # 检查策略是否收到市场数据
        mock_strategy_instance.on_market_data.assert_called_with(mock_market_data)

    @pytest.mark.asyncio
    async def test_on_tick_data(self, strategy_engine, mock_strategy):
        """测试处理Tick数据"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例
        mock_strategy_instance = Mock()
        mock_strategy_instance.on_tick_data = AsyncMock()
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 模拟Tick数据
        tick_data = {
            "symbol": "BTC/USDT",
            "timestamp": 1700000000000,
            "last_price": 50000.0,
            "bid_price": 49999.0,
            "ask_price": 50001.0,
            "volume": 1000.0,
            "turnover": 50000000.0
        }

        # 处理Tick数据
        await strategy_engine.on_tick_data(tick_data)

        # 检查策略是否收到Tick数据
        mock_strategy_instance.on_tick_data.assert_called_with(tick_data)

    @pytest.mark.asyncio
    async def test_on_order_update(self, strategy_engine, mock_strategy, mock_order):
        """测试处理订单更新"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例
        mock_strategy_instance = Mock()
        mock_strategy_instance.on_order_update = AsyncMock()
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 模拟订单更新
        order_update = {
            "order_id": mock_order.order_id,
            "status": OrderStatus.FILLED,
            "filled_quantity": 1.0,
            "filled_price": 50000.0,
            "timestamp": datetime.now()
        }

        # 处理订单更新
        await strategy_engine.on_order_update(order_update)

        # 检查策略是否收到订单更新
        mock_strategy_instance.on_order_update.assert_called_with(order_update)

    @pytest.mark.asyncio
    async def test_submit_order(self, strategy_engine, mock_strategy, mock_order):
        """测试提交订单"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟交易引擎
        strategy_engine._trading_engine = Mock()
        strategy_engine._trading_engine.submit_order = AsyncMock(return_value=mock_order)

        # 提交订单
        result = await strategy_engine.submit_order(mock_order)

        # 检查订单是否提交成功
        assert result == mock_order
        strategy_engine._trading_engine.submit_order.assert_called_with(mock_order)

    @pytest.mark.asyncio
    async def test_cancel_order(self, strategy_engine, mock_order):
        """测试取消订单"""
        # 模拟交易引擎
        strategy_engine._trading_engine = Mock()
        strategy_engine._trading_engine.cancel_order = AsyncMock(return_value=True)

        # 取消订单
        result = await strategy_engine.cancel_order(mock_order.order_id)

        # 检查订单是否取消成功
        assert result is True
        strategy_engine._trading_engine.cancel_order.assert_called_with(mock_order.order_id)

    @pytest.mark.asyncio
    async def test_get_strategy_performance(self, strategy_engine, mock_strategy):
        """测试获取策略性能"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例
        mock_strategy_instance = Mock()
        mock_strategy_instance.get_performance = Mock(return_value={
            "total_pnl": 1000.0,
            "win_rate": 0.6,
            "sharpe_ratio": 1.5,
            "max_drawdown": -500.0
        })
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 获取策略性能
        performance = strategy_engine.get_strategy_performance(mock_strategy.strategy_id)

        # 检查性能数据
        assert performance["total_pnl"] == 1000.0
        assert performance["win_rate"] == 0.6
        assert performance["sharpe_ratio"] == 1.5
        assert performance["max_drawdown"] == -500.0

    @pytest.mark.asyncio
    async def test_get_all_strategies(self, strategy_engine, mock_strategy):
        """测试获取所有策略"""
        # 添加多个策略
        strategies = []
        for i in range(3):
            strategy = Strategy(
                strategy_id=f"test_strategy_{i:03d}",
                name=f"Test Strategy {i}",
                type="trend_following",
                symbols=["BTC/USDT"],
                timeframe="1m",
                parameters={},
                status=StrategyState.ACTIVE,
                created_time=datetime.now(),
                updated_time=datetime.now()
            )
            await strategy_engine.add_strategy(strategy)
            strategies.append(strategy)

        # 获取所有策略
        all_strategies = strategy_engine.get_all_strategies()

        # 检查策略数量
        assert len(all_strategies) == 3

        # 检查策略ID
        strategy_ids = [s.strategy_id for s in all_strategies]
        expected_ids = [f"test_strategy_{i:03d}" for i in range(3)]
        assert strategy_ids == expected_ids

    @pytest.mark.asyncio
    async def test_strategy_error_handling(self, strategy_engine, mock_strategy, mock_market_data):
        """测试策略错误处理"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例抛出异常
        mock_strategy_instance = Mock()
        mock_strategy_instance.on_market_data = AsyncMock(side_effect=Exception("Strategy error"))
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 处理市场数据（应该捕获异常）
        await strategy_engine.on_market_data(mock_market_data)

        # 检查异常是否被记录
        # 这里应该检查日志记录，但由于是测试，我们主要验证不会抛出异常
        assert True  # 如果没有抛出异常，测试通过

    @pytest.mark.asyncio
    async def test_concurrent_strategy_operations(self, strategy_engine):
        """测试并发策略操作"""
        # 并发添加多个策略
        tasks = []

        for i in range(5):
            strategy = Strategy(
                strategy_id=f"concurrent_strategy_{i:03d}",
                name=f"Concurrent Strategy {i}",
                type="trend_following",
                symbols=["BTC/USDT"],
                timeframe="1m",
                parameters={},
                status=StrategyState.ACTIVE,
                created_time=datetime.now(),
                updated_time=datetime.now()
            )

            task = asyncio.create_task(strategy_engine.add_strategy(strategy))
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        # 检查所有策略是否添加成功
        assert len(strategy_engine._strategies) == 5
        assert len(strategy_engine._strategy_instances) == 5

    @pytest.mark.asyncio
    async def test_strategy_lifecycle(self, strategy_engine, mock_strategy):
        """测试策略生命周期管理"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 检查初始状态
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.ACTIVE

        # 暂停策略
        await strategy_engine.pause_strategy(mock_strategy.strategy_id)
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.PAUSED

        # 恢复策略
        await strategy_engine.resume_strategy(mock_strategy.strategy_id)
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.ACTIVE

        # 停止策略
        await strategy_engine.stop_strategy(mock_strategy.strategy_id)
        strategy = strategy_engine._strategies[mock_strategy.strategy_id]
        assert strategy.status == StrategyState.STOPPED

        # 移除策略
        await strategy_engine.remove_strategy(mock_strategy.strategy_id)
        assert mock_strategy.strategy_id not in strategy_engine._strategies

    @pytest.mark.asyncio
    async def test_event_emission(self, strategy_engine, mock_strategy):
        """测试事件发送"""
        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # 注册事件处理器
        strategy_engine._event_engine.register(EventType.STRATEGY_ADDED, event_handler)

        # 添加策略（应该发送事件）
        await strategy_engine.add_strategy(mock_strategy)

        # 检查事件是否发送
        assert len(received_events) == 1
        assert received_events[0].type == EventType.STRATEGY_ADDED
        assert received_events[0].data == mock_strategy

    @pytest.mark.asyncio
    async def test_strategy_parameter_validation(self, strategy_engine):
        """测试策略参数验证"""
        # 测试无效参数
        invalid_strategy = Strategy(
            strategy_id="invalid_strategy",
            name="Invalid Strategy",
            type="trend_following",
            symbols=[],  # 空交易对列表
            timeframe="1m",
            parameters={},
            status=StrategyState.ACTIVE,
            created_time=datetime.now(),
            updated_time=datetime.now()
        )

        # 添加策略（应该抛出异常）
        with pytest.raises(ValueError) as exc_info:
            await strategy_engine.add_strategy(invalid_strategy)

        # 检查异常信息
        assert "symbols" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, strategy_engine, mock_strategy):
        """测试性能监控"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟策略实例
        mock_strategy_instance = Mock()
        mock_strategy_instance.on_market_data = AsyncMock()
        strategy_engine._strategy_instances[mock_strategy.strategy_id] = mock_strategy_instance

        # 测试处理市场数据的性能
        import time

        market_data_list = []
        for i in range(100):
            market_data = {
                "symbol": "BTC/USDT",
                "timestamp": 1700000000000 + i * 60000,  # 每分钟数据
                "open": 50000.0 + i * 10,
                "high": 50100.0 + i * 10,
                "low": 49900.0 + i * 10,
                "close": 50050.0 + i * 10,
                "volume": 1000.0,
                "turnover": 50050000.0
            }
            market_data_list.append(market_data)

        # 测量处理时间
        start_time = time.time()

        for data in market_data_list:
            await strategy_engine.on_market_data(data)

        end_time = time.time()
        execution_time = end_time - start_time

        # 检查性能（100次处理应该小于1秒）
        assert execution_time < 1.0

        # 计算平均处理时间
        avg_time = execution_time / 100
        print(f"Average market data processing time: {avg_time:.6f} seconds")

        # 性能要求：平均处理时间小于5毫秒
        assert avg_time < 0.005

    @pytest.mark.asyncio
    async def test_memory_usage(self, strategy_engine):
        """测试内存使用"""
        import sys

        # 记录初始内存使用
        initial_memory = sys.getsizeof(strategy_engine)

        # 添加多个策略
        num_strategies = 100
        for i in range(num_strategies):
            strategy = Strategy(
                strategy_id=f"memory_test_{i:03d}",
                name=f"Memory Test Strategy {i}",
                type="trend_following",
                symbols=["BTC/USDT"],
                timeframe="1m",
                parameters={"param1": i, "param2": f"value_{i}"},
                status=StrategyState.ACTIVE,
                created_time=datetime.now(),
                updated_time=datetime.now()
            )
            await strategy_engine.add_strategy(strategy)

        # 记录最终内存使用
        final_memory = sys.getsizeof(strategy_engine)

        # 计算内存增长
        memory_growth = final_memory - initial_memory
        memory_per_strategy = memory_growth / num_strategies

        print(f"Memory per strategy: {memory_per_strategy:.2f} bytes")

        # 内存增长应该相对较小（每个策略小于1KB）
        assert memory_per_strategy < 1024

    def test_stats_property(self, strategy_engine, mock_strategy):
        """测试统计信息属性"""
        # 设置引擎状态
        strategy_engine._running = True
        strategy_engine._strategies = {mock_strategy.strategy_id: mock_strategy}
        strategy_engine._strategy_instances = {mock_strategy.strategy_id: Mock()}

        # 获取统计信息
        stats = strategy_engine.stats

        # 检查统计信息
        assert stats["running"] is True
        assert stats["total_strategies"] == 1
        assert stats["active_strategies"] == 1
        assert stats["paused_strategies"] == 0
        assert stats["stopped_strategies"] == 0
        assert mock_strategy.strategy_id in stats["strategy_ids"]

    @pytest.mark.asyncio
    async def test_integration_with_trading_engine(self, strategy_engine, mock_strategy, mock_order):
        """测试与交易引擎的集成"""
        # 添加策略
        await strategy_engine.add_strategy(mock_strategy)

        # 模拟交易引擎
        mock_trading_engine = Mock()
        mock_trading_engine.submit_order = AsyncMock(return_value=mock_order)
        mock_trading_engine.cancel_order = AsyncMock(return_value=True)
        mock_trading_engine.get_order = Mock(return_value=mock_order)

        strategy_engine._trading_engine = mock_trading_engine

        # 测试订单提交
        submitted_order = await strategy_engine.submit_order(mock_order)
        assert submitted_order == mock_order

        # 测试订单取消
        cancel_result = await strategy_engine.cancel_order(mock_order.order_id)
        assert cancel_result is True

        # 测试订单查询
        queried_order = strategy_engine.get_order(mock_order.order_id)
        assert queried_order == mock_order
