import pytest
from unittest.mock import Mock, patch
import time
from datetime import datetime

from quant_trading_system.services.risk.risk_manager import (
    RiskManager, RiskConfig, RiskLevel, RiskCheckResult, RiskMetrics
)
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.models.account import Account, AccountType, Balance
from quant_trading_system.core.events import EventEngine, EventType


class TestRiskManager:
    """风控管理器测试"""

    @pytest.fixture
    def risk_config(self):
        """风控配置"""
        return RiskConfig(
            max_position_value=1000000.0,
            max_position_ratio=0.8,
            max_single_position_ratio=0.2,
            max_order_value=100000.0,
            max_order_quantity=1000.0,
            max_orders_per_minute=60,
            max_orders_per_day=1000,
            max_daily_loss=50000.0,
            max_daily_loss_ratio=0.05,
            max_drawdown=0.2,
            min_order_interval=0.1,
            max_price_deviation=0.1
        )

    @pytest.fixture
    def risk_manager(self, risk_config):
        """风控管理器实例"""
        event_engine = EventEngine()
        return RiskManager(config=risk_config, event_engine=event_engine)

    @pytest.fixture
    def mock_account(self):
        """模拟账户"""
        return Account(
            id="test_account",
            type=AccountType.SPOT,
            balances={"USDT": Balance(asset="USDT", free=800000.0, locked=200000.0, total=1000000.0)},
            total_balance=1000000.0,
            available_balance=800000.0,
            margin_balance=200000.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            updated_at=datetime.now()
        )

    @pytest.fixture
    def mock_order(self):
        """模拟订单"""
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

    def test_initialization(self, risk_manager, risk_config):
        """测试初始化"""
        assert risk_manager.config == risk_config
        assert risk_manager._trading_enabled is True
        assert risk_manager._risk_level == RiskLevel.NORMAL
        assert risk_manager._daily_order_count == 0
        assert risk_manager._initial_equity == 0.0

    def test_set_account(self, risk_manager, mock_account):
        """测试设置账户"""
        risk_manager.set_account(mock_account)

        assert risk_manager._account == mock_account
        assert risk_manager._initial_equity == mock_account.total_balance
        assert risk_manager._peak_equity == mock_account.total_balance
        assert risk_manager._daily_start_equity == mock_account.total_balance

    def test_check_order_basic_validation(self, risk_manager, mock_account, mock_order):
        """测试订单基本验证"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 测试正常订单
        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is True
        assert result.risk_level == RiskLevel.NORMAL

    def test_check_order_value_limit(self, risk_manager, mock_account, mock_order):
        """测试订单金额限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 创建超过金额限制的订单
        large_order = Order(
            id="large_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=3.0,  # 3 * 50000 = 150000 > 100000
            price=50000.0,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = risk_manager.check_order(large_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "exceeds limit" in result.messages[0]

    def test_check_order_quantity_limit(self, risk_manager, mock_account, mock_order):
        """测试订单数量限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 创建超过数量限制的订单
        large_quantity_order = Order(
            id="large_quantity_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=2000.0,  # > 1000.0
            price=50.0,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = risk_manager.check_order(large_quantity_order, current_price=50.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "exceeds limit" in result.messages[0]

    def test_check_order_frequency_limit(self, risk_manager, mock_account, mock_order):
        """测试订单频率限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟高频订单
        risk_manager._order_times = [time.time() - 0.05] * 100  # 100个最近订单

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Orders per minute" in result.messages[0]

    def test_check_order_interval_limit(self, risk_manager, mock_account, mock_order):
        """测试订单间隔限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 设置最近订单时间
        risk_manager._last_order_time = time.time() - 0.05  # 0.05秒前

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Order interval too short" in result.messages[0]

    def test_check_position_ratio_limit(self, risk_manager, mock_account, mock_order):
        """测试仓位比例限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟已有持仓
        risk_manager._metrics.total_position_value = 700000.0  # 70%仓位
        risk_manager._metrics.position_ratio = 0.7

        # 创建新订单（会超过80%限制）
        new_order = Order(
            order_id="new_order",
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=2.0,
            price=50000.0,  # 100000价值
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )

        result = risk_manager.check_order(new_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Position ratio" in result.messages[0]

    def test_check_price_deviation(self, risk_manager, mock_account, mock_order):
        """测试价格偏离检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 创建价格偏离较大的订单
        deviated_order = Order(
            order_id="deviated_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=60000.0,  # 偏离20%
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )

        result = risk_manager.check_order(deviated_order, current_price=50000.0)
        assert result.passed is True  # 偏离检查只是警告，不拒绝
        assert result.risk_level == RiskLevel.WARNING
        assert "Price deviation" in result.messages[0]

    def test_check_daily_loss_limit(self, risk_manager, mock_account, mock_order):
        """测试每日亏损限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟当日亏损
        risk_manager._metrics.daily_pnl = -60000.0  # 超过50000限制
        risk_manager._metrics.daily_pnl_ratio = -0.06

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is True  # 亏损检查只是警告，不拒绝
        assert result.risk_level == RiskLevel.ALERT
        assert "Daily loss" in result.messages[0]

    def test_check_drawdown_limit(self, risk_manager, mock_account, mock_order):
        """测试回撤限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟较大回撤
        risk_manager._metrics.current_drawdown = 0.25  # 超过20%限制

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is True  # 回撤检查只是警告，不拒绝
        assert result.risk_level == RiskLevel.WARNING
        assert "Drawdown" in result.messages[0]

    def test_on_order_submitted(self, risk_manager, mock_order):
        """测试订单提交后更新"""
        # 初始状态
        initial_count = risk_manager._daily_order_count
        initial_times_count = len(risk_manager._order_times)

        # 订单提交
        risk_manager.on_order_submitted(mock_order)

        # 检查更新
        assert risk_manager._daily_order_count == initial_count + 1
        assert len(risk_manager._order_times) == initial_times_count + 1
        assert risk_manager._last_order_time > 0

    def test_check_daily_order_limit(self, risk_manager, mock_account, mock_order):
        """测试每日订单数量限制"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟达到每日订单限制
        risk_manager._daily_order_count = risk_manager.config.max_orders_per_day

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Daily orders" in result.messages[0]

    def test_check_order_without_account(self, risk_manager, mock_order):
        """测试无账户时的订单检查"""
        # 不设置账户
        result = risk_manager.check_order(mock_order, current_price=50000.0)

        # 应该通过基本检查
        assert result.passed is True
        assert result.risk_level == RiskLevel.NORMAL

    def test_check_sell_order_position_validation(self, risk_manager, mock_account):
        """测试卖出订单的仓位验证（应该比买入更宽松）"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 创建卖出订单
        sell_order = Order(
            order_id="sell_order",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=2.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )

        # 设置高仓位比例
        risk_manager._metrics.total_position_value = 900000.0
        risk_manager._metrics.position_ratio = 0.9

        result = risk_manager.check_order(sell_order, current_price=50000.0)

        # 卖出订单不应该受仓位比例限制
        assert result.passed is True

    def test_check_order_with_zero_price(self, risk_manager, mock_account, mock_order):
        """测试价格为0时的订单检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 使用0价格
        result = risk_manager.check_order(mock_order, current_price=0)

        # 应该通过基本检查，但跳过价格偏离检查
        assert result.passed is True

    def test_check_order_with_none_price(self, risk_manager, mock_account, mock_order):
        """测试价格为空时的订单检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 使用None价格
        result = risk_manager.check_order(mock_order, current_price=None)

        # 应该通过基本检查，但跳过价格偏离检查
        assert result.passed is True

    def test_check_order_trading_disabled(self, risk_manager, mock_account, mock_order):
        """测试交易禁用时的订单检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 禁用交易
        risk_manager._trading_enabled = False

        result = risk_manager.check_order(mock_order, current_price=50000.0)
        assert result.passed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Trading is disabled" in result.messages[0]

    def test_risk_check_result_warning_escalation(self):
        """测试风险检查结果的警告升级机制"""
        result = RiskCheckResult()

        # 添加警告
        result.add_warning("Test warning")
        assert result.risk_level == RiskLevel.WARNING

        # 添加告警（应该升级到ALERT）
        result.add_alert("Test alert")
        assert result.risk_level == RiskLevel.ALERT

        # 拒绝（应该升级到CRITICAL）
        result.reject("Test reject")
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.passed is False

    def test_update_position_and_metrics(self, risk_manager, mock_account):
        """测试更新持仓和指标计算"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟持仓
        mock_position = Mock()
        mock_position.symbol = "BTC/USDT"
        mock_position.notional_value = 300000.0

        # 更新持仓
        risk_manager.update_position(mock_position)

        # 检查持仓更新
        assert "BTC/USDT" in risk_manager._positions
        assert risk_manager._positions["BTC/USDT"] == mock_position

        # 检查指标更新
        assert risk_manager._metrics.total_position_value == 300000.0
        assert risk_manager._metrics.position_ratio == 0.3

    def test_multiple_positions_metrics_calculation(self, risk_manager, mock_account):
        """测试多持仓的指标计算"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟多个持仓
        position1 = Mock()
        position1.symbol = "BTC/USDT"
        position1.notional_value = 400000.0

        position2 = Mock()
        position2.symbol = "ETH/USDT"
        position2.notional_value = 200000.0

        position3 = Mock()
        position3.symbol = "ADA/USDT"
        position3.notional_value = 100000.0

        # 更新持仓
        risk_manager.update_position(position1)
        risk_manager.update_position(position2)
        risk_manager.update_position(position3)

        # 检查总持仓价值
        assert risk_manager._metrics.total_position_value == 700000.0
        assert risk_manager._metrics.position_ratio == 0.7

    def test_peak_equity_tracking(self, risk_manager, mock_account):
        """测试峰值权益跟踪"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 初始峰值应该等于初始权益
        assert risk_manager._peak_equity == mock_account.total_equity

        # 更新权益到更高值
        risk_manager.update_equity(1100000.0)
        assert risk_manager._peak_equity == 1100000.0

        # 更新权益到更低值（峰值应该保持不变）
        risk_manager.update_equity(900000.0)
        assert risk_manager._peak_equity == 1100000.0

    def test_drawdown_calculation(self, risk_manager, mock_account):
        """测试回撤计算"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 设置峰值权益
        risk_manager._peak_equity = 1000000.0

        # 计算回撤
        risk_manager.update_equity(800000.0)
        assert risk_manager._metrics.current_drawdown == 0.2

        # 权益回升，回撤减小
        risk_manager.update_equity(900000.0)
        assert risk_manager._metrics.current_drawdown == 0.1

        # 权益超过峰值，回撤为0
        risk_manager.update_equity(1100000.0)
        assert risk_manager._metrics.current_drawdown == 0.0

    def test_daily_pnl_calculation(self, risk_manager, mock_account):
        """测试当日盈亏计算"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 初始当日盈亏为0
        assert risk_manager._metrics.daily_pnl == 0.0
        assert risk_manager._metrics.daily_pnl_ratio == 0.0

        # 更新权益（盈利）
        risk_manager.update_equity(1050000.0)
        assert risk_manager._metrics.daily_pnl == 50000.0
        assert risk_manager._metrics.daily_pnl_ratio == 0.05

        # 更新权益（亏损）
        risk_manager.update_equity(950000.0)
        assert risk_manager._metrics.daily_pnl == -50000.0
        assert risk_manager._metrics.daily_pnl_ratio == -0.05

    def test_circuit_breaker_multiple_conditions(self, risk_manager, mock_account):
        """测试多重熔断条件"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟事件引擎
        mock_event_engine = Mock()
        risk_manager._event_engine = mock_event_engine

        # 设置严重回撤（触发熔断）
        risk_manager._metrics.current_drawdown = 0.25
        risk_manager._check_circuit_breaker()

        assert risk_manager._trading_enabled is False
        assert risk_manager._risk_level == RiskLevel.EMERGENCY

        # 重置交易状态
        risk_manager._trading_enabled = True
        risk_manager._risk_level = RiskLevel.NORMAL

        # 设置严重亏损（触发熔断）
        risk_manager._metrics.daily_pnl = -60000.0  # 超过50000限制
        risk_manager._check_circuit_breaker()

        assert risk_manager._trading_enabled is False
        assert risk_manager._risk_level == RiskLevel.EMERGENCY

    def test_reset_daily_without_account(self, risk_manager):
        """测试无账户时的每日重置"""
        # 不设置账户
        risk_manager._daily_order_count = 100
        risk_manager._metrics.daily_pnl = -10000.0
        risk_manager._trading_enabled = False

        # 重置每日统计
        risk_manager.reset_daily()

        # 检查重置结果
        assert risk_manager._daily_order_count == 0
        assert risk_manager._metrics.daily_pnl == 0.0
        assert risk_manager._trading_enabled is True

    def test_edge_case_zero_equity_account(self, risk_manager):
        """测试零权益账户的边界情况"""
        # 创建零权益账户
        zero_equity_account = Account(
            account_id="zero_account",
            total_equity=0.0,
            available_cash=0.0,
            margin=0.0,
            leverage=10.0,
            currency="USDT"
        )

        # 设置账户
        risk_manager.set_account(zero_equity_account)

        # 创建小额订单
        small_order = Order(
            order_id="small_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.001,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="zero_account"
        )

        # 检查订单（应该通过，因为订单金额很小）
        result = risk_manager.check_order(small_order, current_price=50000.0)
        assert result.passed is True

        # 检查仓位比例计算（应该是0，因为分母为0）
        risk_manager._update_metrics()
        assert risk_manager._metrics.position_ratio == 0.0

    def test_negative_values_handling(self, risk_manager, mock_account):
        """测试负值处理"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 测试负价格（应该跳过价格偏离检查）
        negative_price_order = Order(
            order_id="negative_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=-100.0,  # 负价格
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )

        result = risk_manager.check_order(negative_price_order, current_price=50000.0)
        # 应该通过基本检查，但跳过价格偏离检查
        assert result.passed is True

    def test_large_numbers_handling(self, risk_manager, mock_account):
        """测试大数值处理"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 创建大额账户
        large_account = Account(
            account_id="large_account",
            total_equity=1000000000.0,  # 10亿
            available_cash=800000000.0,
            margin=200000000.0,
            leverage=10.0,
            currency="USDT"
        )

        risk_manager.set_account(large_account)

        # 创建大额订单
        large_order = Order(
            order_id="large_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=10000.0,
            price=50000.0,  # 5亿订单
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        # 调整配置以适应大额订单
        risk_manager.config.max_order_value = 100000000.0  # 1亿

        result = risk_manager.check_order(large_order, current_price=50000.0)
        # 订单金额5亿 > 限制1亿，应该被拒绝
        assert result.passed is False

    def test_concurrent_order_checks(self, risk_manager, mock_account, mock_order):
        """测试并发订单检查"""
        import threading
        import time

        # 设置账户
        risk_manager.set_account(mock_account)

        results = []

        def check_order_thread():
            result = risk_manager.check_order(mock_order, current_price=50000.0)
            results.append(result.passed)

        # 创建多个线程同时检查订单
        threads = []
        for i in range(10):
            thread = threading.Thread(target=check_order_thread)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 所有检查都应该通过
        assert all(results)
        assert len(results) == 10

    def test_risk_config_default_values(self):
        """测试风险配置的默认值"""
        # 使用默认配置
        config = RiskConfig()

        # 检查默认值
        assert config.max_position_value == 1000000.0
        assert config.max_position_ratio == 0.8
        assert config.max_order_value == 100000.0
        assert config.max_orders_per_minute == 60
        assert config.max_orders_per_day == 1000
        assert config.max_daily_loss == 50000.0
        assert config.max_drawdown == 0.2
        assert config.min_order_interval == 0.1

    def test_risk_metrics_default_values(self):
        """测试风险指标的默认值"""
        metrics = RiskMetrics()

        # 检查默认值
        assert metrics.total_position_value == 0.0
        assert metrics.position_ratio == 0.0
        assert metrics.daily_pnl == 0.0
        assert metrics.daily_pnl_ratio == 0.0
        assert metrics.current_drawdown == 0.0
        assert metrics.risk_level == RiskLevel.NORMAL
        assert metrics.update_time == 0.0

    def test_risk_check_result_default_values(self):
        """测试风险检查结果的默认值"""
        result = RiskCheckResult()

        # 检查默认值
        assert result.passed is True
        assert result.risk_level == RiskLevel.NORMAL
        assert result.messages == []

    def test_error_handling_invalid_inputs(self, risk_manager):
        """测试无效输入的异常处理"""
        # 测试None订单
        try:
            result = risk_manager.check_order(None, current_price=50000.0)
            # 应该处理None输入而不崩溃
            assert result is not None
        except Exception:
            pytest.fail("check_order should handle None input gracefully")

        # 测试无效价格
        try:
            result = risk_manager.check_order(Mock(), current_price="invalid")
            # 应该处理无效价格而不崩溃
            assert result is not None
        except Exception:
            pytest.fail("check_order should handle invalid price gracefully")

    def test_update_equity(self, risk_manager, mock_account):
        """测试更新权益"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 更新权益
        new_equity = 950000.0  # 从1000000亏损到950000
        risk_manager.update_equity(new_equity)

        # 检查权益更新
        assert risk_manager._metrics.daily_pnl == -50000.0
        assert risk_manager._metrics.daily_pnl_ratio == -0.05
        assert risk_manager._metrics.current_drawdown == 0.05

    def test_update_metrics(self, risk_manager, mock_account):
        """测试更新风险指标"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟持仓
        risk_manager._positions = {
            "BTC/USDT": Mock(notional_value=300000.0),
            "ETH/USDT": Mock(notional_value=200000.0)
        }

        # 更新指标
        risk_manager._update_metrics()

        # 检查指标计算
        assert risk_manager._metrics.total_position_value == 500000.0
        assert risk_manager._metrics.position_ratio == 0.5
        assert risk_manager._metrics.update_time > 0

    def test_update_risk_level_normal(self, risk_manager, mock_account):
        """测试风险级别更新（正常情况）"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 正常风险指标
        risk_manager._metrics.position_ratio = 0.5
        risk_manager._metrics.daily_pnl_ratio = 0.01
        risk_manager._metrics.current_drawdown = 0.05

        # 更新风险级别
        risk_manager._update_risk_level()

        assert risk_manager._risk_level == RiskLevel.NORMAL

    def test_update_risk_level_warning(self, risk_manager, mock_account):
        """测试风险级别更新（警告情况）"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 接近限制的风险指标
        risk_manager._metrics.position_ratio = 0.75  # 接近80%
        risk_manager._metrics.daily_pnl_ratio = -0.04  # 接近-5%
        risk_manager._metrics.current_drawdown = 0.16  # 接近20%

        # 更新风险级别
        risk_manager._update_risk_level()

        assert risk_manager._risk_level == RiskLevel.WARNING

    def test_update_risk_level_alert(self, risk_manager, mock_account):
        """测试风险级别更新（告警情况）"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 超过限制的风险指标
        risk_manager._metrics.position_ratio = 0.85  # 超过80%
        risk_manager._metrics.daily_pnl_ratio = -0.06  # 超过-5%

        # 更新风险级别
        risk_manager._update_risk_level()

        assert risk_manager._risk_level == RiskLevel.ALERT

    def test_update_risk_level_critical(self, risk_manager, mock_account):
        """测试风险级别更新（危险情况）"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 严重风险指标
        risk_manager._metrics.current_drawdown = 0.25  # 超过20%

        # 更新风险级别
        risk_manager._update_risk_level()

        assert risk_manager._risk_level == RiskLevel.CRITICAL

    def test_check_circuit_breaker(self, risk_manager, mock_account):
        """测试熔断检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟严重回撤（触发熔断）
        risk_manager._metrics.current_drawdown = 0.25  # 超过20%限制

        # 检查熔断
        risk_manager._check_circuit_breaker()

        # 检查是否触发熔断
        assert risk_manager._trading_enabled is False
        assert risk_manager._risk_level == RiskLevel.EMERGENCY

    def test_reset_daily(self, risk_manager, mock_account):
        """测试重置每日统计"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 设置一些统计数据
        risk_manager._daily_order_count = 100
        risk_manager._metrics.daily_pnl = -10000.0
        risk_manager._metrics.daily_pnl_ratio = -0.01
        risk_manager._trading_enabled = False  # 模拟熔断状态

        # 重置每日统计
        risk_manager.reset_daily()

        # 检查重置结果
        assert risk_manager._daily_order_count == 0
        assert risk_manager._metrics.daily_pnl == 0.0
        assert risk_manager._metrics.daily_pnl_ratio == 0.0
        assert risk_manager._trading_enabled is True  # 应该重新启用交易

    def test_enable_disable_trading(self, risk_manager):
        """测试启用/禁用交易"""
        # 初始状态
        assert risk_manager._trading_enabled is True

        # 禁用交易
        risk_manager.disable_trading("Test reason")
        assert risk_manager._trading_enabled is False

        # 启用交易
        risk_manager.enable_trading()
        assert risk_manager._trading_enabled is True

    def test_is_trading_enabled_property(self, risk_manager):
        """测试交易启用属性"""
        # 初始状态
        assert risk_manager.is_trading_enabled is True

        # 禁用交易
        risk_manager._trading_enabled = False
        assert risk_manager.is_trading_enabled is False

    def test_risk_level_property(self, risk_manager):
        """测试风险级别属性"""
        # 设置风险级别
        risk_manager._risk_level = RiskLevel.WARNING
        assert risk_manager.risk_level == RiskLevel.WARNING

    def test_metrics_property(self, risk_manager):
        """测试风险指标属性"""
        # 设置指标
        risk_manager._metrics.total_position_value = 500000.0
        risk_manager._metrics.position_ratio = 0.5

        # 检查属性
        metrics = risk_manager.metrics
        assert metrics.total_position_value == 500000.0
        assert metrics.position_ratio == 0.5

    def test_stats_property(self, risk_manager, mock_account):
        """测试统计信息属性"""
        # 设置账户和状态
        risk_manager.set_account(mock_account)
        risk_manager._trading_enabled = True
        risk_manager._risk_level = RiskLevel.NORMAL
        risk_manager._metrics.total_position_value = 500000.0
        risk_manager._metrics.position_ratio = 0.5
        risk_manager._metrics.daily_pnl = 10000.0
        risk_manager._metrics.daily_pnl_ratio = 0.01
        risk_manager._metrics.current_drawdown = 0.05
        risk_manager._daily_order_count = 50

        # 获取统计信息
        stats = risk_manager.stats

        # 检查统计信息
        assert stats["trading_enabled"] is True
        assert stats["risk_level"] == "normal"
        assert stats["total_position_value"] == 500000.0
        assert stats["position_ratio"] == 0.5
        assert stats["daily_pnl"] == 10000.0
        assert stats["daily_pnl_ratio"] == 0.01
        assert stats["current_drawdown"] == 0.05
        assert stats["orders_today"] == 50

    def test_event_emission_on_circuit_breaker(self, risk_manager, mock_account):
        """测试熔断时的事件发送"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 模拟事件引擎
        mock_event_engine = Mock()
        risk_manager._event_engine = mock_event_engine

        # 模拟严重回撤（触发熔断）
        risk_manager._metrics.current_drawdown = 0.25

        # 检查熔断
        risk_manager._check_circuit_breaker()

        # 检查是否发送了风险事件
        mock_event_engine.put.assert_called_once()
        event = mock_event_engine.put.call_args[0][0]
        assert event.type == EventType.RISK_BREACH
        assert event.data["level"] == RiskLevel.EMERGENCY

    def test_comprehensive_risk_check(self, risk_manager, mock_account, mock_order):
        """测试综合风险检查"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 设置多重风险条件
        risk_manager._metrics.total_position_value = 700000.0
        risk_manager._metrics.position_ratio = 0.7
        risk_manager._metrics.daily_pnl = -40000.0
        risk_manager._metrics.daily_pnl_ratio = -0.04
        risk_manager._metrics.current_drawdown = 0.15
        risk_manager._order_times = [time.time() - 0.05] * 50  # 50个最近订单

        # 创建订单
        test_order = Order(
            order_id="test_order",
            symbol="ETH/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.5,
            price=60000.0,  # 偏离当前价格
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="test_account"
        )

        # 执行风险检查
        result = risk_manager.check_order(test_order, current_price=50000.0)

        # 检查结果（应该通过，但有多重警告）
        assert result.passed is True
        assert result.risk_level == RiskLevel.WARNING
        assert len(result.messages) >= 2  # 至少应该有价格偏离和频率警告

    def test_edge_cases(self, risk_manager, mock_account):
        """测试边界情况"""
        # 设置账户
        risk_manager.set_account(mock_account)

        # 测试零权益账户
        zero_equity_account = Account(
            account_id="zero_account",
            total_equity=0.0,
            available_cash=0.0,
            margin=0.0,
            leverage=10.0,
            currency="USDT"
        )

        risk_manager.set_account(zero_equity_account)

        # 创建订单
        order = Order(
            order_id="edge_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.001,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="zero_account"
        )

        # 检查（应该通过，因为订单金额很小）
        result = risk_manager.check_order(order, current_price=50000.0)
        assert result.passed is True

    def test_performance_benchmark(self, risk_manager, mock_account, mock_order):
        """测试性能基准"""
        # 设置账户
        risk_manager.set_account(mock_account)

        import time

        # 测试100次风险检查的性能
        start_time = time.time()

        for i in range(100):
            result = risk_manager.check_order(mock_order, current_price=50000.0)
            assert result.passed is True

        end_time = time.time()
        execution_time = end_time - start_time

        # 检查性能（100次检查应该小于1秒）
        assert execution_time < 1.0

        # 计算平均时间
        avg_time = execution_time / 100
        print(f"Average risk check time: {avg_time:.6f} seconds")

        # 性能要求：平均检查时间小于10毫秒
        assert avg_time < 0.01
