import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from datetime import datetime

from quant_trading_system.services.trading.trading_engine import TradingEngine
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus, Position
from quant_trading_system.models.account import Account
from quant_trading_system.core.events import EventEngine, EventType


class TestTradingEngine:
    """交易引擎测试"""
    
    @pytest.fixture
    def trading_engine(self):
        """创建交易引擎实例"""
        event_engine = EventEngine()
        return TradingEngine(event_engine=event_engine)
    
    @pytest.fixture
    def mock_account(self):
        """模拟账户"""
        from datetime import datetime
        return Account(
            id="test_account",
            type="SPOT",
            balances={"USDT": {"asset": "USDT", "free": 80000.0, "locked": 0.0, "total": 80000.0}},
            total_balance=100000.0,
            available_balance=80000.0,
            margin_balance=20000.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_order(self):
        """模拟订单"""
        from datetime import datetime
        return Order(
            id="test_order_001",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_position(self):
        """模拟持仓"""
        return Position(
            symbol="BTC/USDT",
            quantity=1.0,
            avg_price=50000.0,
            last_price=51000.0,
            unrealized_pnl=1000.0,
            realized_pnl=0.0
        )
    
    @pytest.mark.asyncio
    async def test_start_stop(self, trading_engine):
        """测试启动和停止"""
        # 测试启动
        await trading_engine.start()
        assert trading_engine.is_running
        
        # 测试停止
        await trading_engine.stop()
        assert not trading_engine.is_running
    
    @pytest.mark.asyncio
    async def test_set_account(self, trading_engine, mock_account):
        """测试设置账户"""
        # 设置账户
        trading_engine.set_account(mock_account)
    
        # 检查账户是否设置成功
        assert trading_engine._account == mock_account
    
    @pytest.mark.asyncio
    async def test_execute_signal(self, trading_engine, mock_account):
        """测试执行交易信号"""
        from quant_trading_system.services.strategy.signal import Signal, SignalType
        
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 启动交易引擎
        await trading_engine.start()
        
        # 创建测试信号
        signal = Signal(
            signal_id="test_signal_001",
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            price=50000.0,
            timestamp=datetime.now(),
            strategy_id="test_strategy"
        )
        
        # 模拟订单管理器
        mock_order = Mock()
        trading_engine._order_manager.create_order_from_signal = Mock(return_value=mock_order)
        trading_engine._order_manager.update_order_status = AsyncMock()
        
        # 执行信号
        result = await trading_engine.execute_signal(signal)
        
        # 检查返回结果
        assert result == mock_order
        trading_engine._order_manager.create_order_from_signal.assert_called_with(signal)
        
        # 停止交易引擎
        await trading_engine.stop()
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, trading_engine, mock_order):
        """测试取消订单"""
        # 模拟订单管理器
        trading_engine._order_manager.cancel_order = AsyncMock(return_value=True)
        
        # 取消订单
        result = await trading_engine.cancel_order("test_order_001")
        
        # 检查返回结果
        assert result is True
        trading_engine._order_manager.cancel_order.assert_called_with("test_order_001")
    
    @pytest.mark.asyncio
    async def test_get_order(self, trading_engine, mock_order):
        """测试获取订单"""
        # 模拟订单管理器
        trading_engine._order_manager.get_order = Mock(return_value=mock_order)
        
        # 获取订单
        result = trading_engine.get_order("test_order_001")
        
        # 检查返回结果
        assert result == mock_order
        trading_engine._order_manager.get_order.assert_called_with("test_order_001")
    
    @pytest.mark.asyncio
    async def test_get_orders(self, trading_engine, mock_order):
        """测试获取订单列表"""
        # 模拟订单管理器
        orders = [mock_order]
        trading_engine._order_manager.get_orders = Mock(return_value=orders)
        
        # 获取订单列表
        result = trading_engine.get_orders()
        
        # 检查返回结果
        assert result == orders
        trading_engine._order_manager.get_orders.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_positions(self, trading_engine, mock_position):
        """测试获取持仓列表"""
        # 模拟持仓管理器
        positions = {"BTC/USDT": mock_position}
        trading_engine._position_manager.get_positions = Mock(return_value=positions)
        
        # 获取持仓列表
        result = trading_engine.get_positions()
        
        # 检查返回结果
        assert result == positions
        trading_engine._position_manager.get_positions.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_position(self, trading_engine, mock_position):
        """测试获取特定持仓"""
        # 模拟持仓管理器
        trading_engine._position_manager.get_position = Mock(return_value=mock_position)
        
        # 获取持仓
        result = trading_engine.get_position("BTC/USDT")
        
        # 检查返回结果
        assert result == mock_position
        trading_engine._position_manager.get_position.assert_called_with("BTC/USDT")
    
    @pytest.mark.asyncio
    async def test_on_tick_data(self, trading_engine, mock_account):
        """测试处理Tick数据"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 模拟持仓管理器
        trading_engine._position_manager.update_market_price = AsyncMock()
        
        # 模拟Tick数据
        tick_data = {
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
        }
        
        # 处理Tick数据
        await trading_engine.on_tick_data(tick_data)
        
        # 检查是否调用了更新市场价格的函数
        trading_engine._position_manager.update_market_price.assert_called_with(
            "BTC/USDT", 50000.0
        )
    
    @pytest.mark.asyncio
    async def test_on_order_update(self, trading_engine, mock_order):
        """测试处理订单更新"""
        # 模拟订单管理器
        trading_engine._order_manager.on_order_update = AsyncMock()
        
        # 模拟订单更新数据
        order_update = {
            "order_id": "test_order_001",
            "status": OrderStatus.FILLED,
            "filled_quantity": 1.0,
            "filled_price": 50000.0,
            "timestamp": datetime.now()
        }
        
        # 处理订单更新
        await trading_engine.on_order_update(order_update)
        
        # 检查是否调用了订单更新函数
        trading_engine._order_manager.on_order_update.assert_called_with(order_update)
    
    @pytest.mark.asyncio
    async def test_on_trade_data(self, trading_engine, mock_account):
        """测试处理成交数据"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 模拟持仓管理器
        trading_engine._position_manager.on_trade = AsyncMock()
        
        # 模拟成交数据
        trade_data = {
            "trade_id": "test_trade_001",
            "order_id": "test_order_001",
            "symbol": "BTC/USDT",
            "side": OrderSide.BUY,
            "price": 50000.0,
            "quantity": 1.0,
            "timestamp": datetime.now(),
            "fee": 10.0,
            "fee_currency": "USDT"
        }
        
        # 处理成交数据
        await trading_engine.on_trade_data(trade_data)
        
        # 检查是否调用了成交处理函数
        trading_engine._position_manager.on_trade.assert_called_with(trade_data)
    
    @pytest.mark.asyncio
    async def test_risk_check(self, trading_engine, mock_account, mock_order):
        """测试风险检查"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 模拟风险检查通过
        trading_engine._risk_manager.check_order = Mock()
        trading_engine._risk_manager.check_order.return_value.passed = True
        
        # 提交订单（会触发风险检查）
        trading_engine._order_manager.submit_order = AsyncMock(return_value=mock_order)
        result = await trading_engine.submit_order(mock_order)
        
        # 检查风险检查是否被调用
        trading_engine._risk_manager.check_order.assert_called_with(mock_order, 0)
        assert result == mock_order
    
    @pytest.mark.asyncio
    async def test_risk_check_reject(self, trading_engine, mock_account, mock_order):
        """测试风险检查拒绝"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 模拟风险检查拒绝
        risk_result = Mock()
        risk_result.passed = False
        risk_result.messages = ["Risk check failed"]
        trading_engine._risk_manager.check_order = Mock(return_value=risk_result)
        
        # 提交订单（应该被拒绝）
        with pytest.raises(Exception) as exc_info:
            await trading_engine.submit_order(mock_order)
        
        # 检查异常信息
        assert "Risk check failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_account_equity(self, trading_engine, mock_account):
        """测试更新账户权益"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 模拟持仓管理器
        trading_engine._position_manager.calculate_total_value = Mock(return_value=51000.0)
        
        # 更新账户权益
        trading_engine.update_account_equity()
        
        # 检查账户权益是否更新
        assert trading_engine.account.total_equity == 51000.0
        
        # 检查风险管理器是否收到权益更新
        trading_engine._risk_manager.update_equity.assert_called_with(51000.0)
    
    @pytest.mark.asyncio
    async def test_event_emission(self, trading_engine, mock_order):
        """测试事件发送"""
        received_events = []
        
        async def event_handler(event):
            received_events.append(event)
        
        # 注册事件处理器
        trading_engine._event_engine.register(EventType.ORDER_SUBMITTED, event_handler)
        
        # 模拟订单提交
        trading_engine._order_manager.submit_order = AsyncMock(return_value=mock_order)
        await trading_engine.submit_order(mock_order)
        
        # 检查事件是否发送
        assert len(received_events) == 1
        assert received_events[0].type == EventType.ORDER_SUBMITTED
        assert received_events[0].data == mock_order
    
    @pytest.mark.asyncio
    async def test_stats_property(self, trading_engine, mock_account):
        """测试统计信息属性"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 设置引擎状态
        trading_engine._running = True
        trading_engine._order_manager.stats = {"total_orders": 10, "active_orders": 2}
        trading_engine._position_manager.stats = {"total_positions": 1, "total_value": 51000.0}
        trading_engine._risk_manager.stats = {"risk_level": "normal", "trading_enabled": True}
        
        # 获取统计信息
        stats = trading_engine.stats
        
        # 检查统计信息
        assert stats["running"] is True
        assert stats["account_id"] == "test_account"
        assert stats["order_stats"]["total_orders"] == 10
        assert stats["position_stats"]["total_positions"] == 1
        assert stats["risk_stats"]["risk_level"] == "normal"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, trading_engine, mock_account, mock_order):
        """测试并发操作"""
        # 设置账户
        trading_engine.set_account(mock_account)
        
        # 启动引擎
        await trading_engine.start()
        
        # 并发提交多个订单
        tasks = []
        for i in range(5):
            order = Order(
                order_id=f"test_order_{i:03d}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="test_account"
            )
            
            # 模拟订单管理器
            trading_engine._order_manager.submit_order = AsyncMock(return_value=order)
            
            task = asyncio.create_task(trading_engine.submit_order(order))
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 检查所有订单都成功提交
        assert len(results) == 5
        assert all(isinstance(result, Order) for result in results)
        
        # 停止引擎
        await trading_engine.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, trading_engine, mock_order):
        """测试错误处理"""
        # 模拟订单管理器抛出异常
        trading_engine._order_manager.submit_order = AsyncMock(side_effect=Exception("Order submission failed"))
        
        # 提交订单（应该抛出异常）
        with pytest.raises(Exception) as exc_info:
            await trading_engine.submit_order(mock_order)
        
        # 检查异常信息
        assert "Order submission failed" in str(exc_info.value)
    
    def test_validation_checks(self, trading_engine, mock_order):
        """测试验证检查"""
        # 测试无效订单（数量为0）
        invalid_order = Order(
            order_id="invalid_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.0,  # 无效数量
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )
        
        # 应该抛出验证错误
        with pytest.raises(ValueError):
            trading_engine._validate_order(invalid_order)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, trading_engine, mock_order):
        """测试性能监控"""
        # 设置账户
        trading_engine.set_account(Mock(spec=Account))
        
        # 模拟订单管理器
        trading_engine._order_manager.submit_order = AsyncMock(return_value=mock_order)
        
        # 记录开始时间
        start_time = asyncio.get_event_loop().time()
        
        # 提交订单
        await trading_engine.submit_order(mock_order)
        
        # 记录结束时间
        end_time = asyncio.get_event_loop().time()
        
        # 检查执行时间（应该小于1秒）
        execution_time = end_time - start_time
        assert execution_time < 1.0
        
        # 检查性能统计
        stats = trading_engine.stats
        assert "performance" in stats
        assert stats["performance"]["order_submission_time"] < 1.0