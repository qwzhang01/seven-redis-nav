"""
风险场景测试
============

包含各种风险场景的测试用例，覆盖边界条件、异常情况和复杂场景
"""

import pytest
from unittest.mock import Mock, patch
import time
from datetime import datetime, timedelta

from quant_trading_system.services.risk.risk_manager import (
    RiskManager, RiskConfig, RiskLevel, RiskCheckResult, RiskMetrics
)
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.models.account import Account


class TestRiskScenarios:
    """风险场景测试"""

    @pytest.fixture
    def aggressive_config(self):
        """激进交易配置（高风险）"""
        return RiskConfig(
            max_position_value=2000000.0,
            max_position_ratio=0.9,
            max_single_position_ratio=0.3,
            max_order_value=200000.0,
            max_order_quantity=2000.0,
            max_orders_per_minute=120,
            max_orders_per_day=2000,
            max_daily_loss=100000.0,
            max_daily_loss_ratio=0.1,
            max_drawdown=0.3,
            min_order_interval=0.05,
            max_price_deviation=0.15
        )

    @pytest.fixture
    def conservative_config(self):
        """保守交易配置（低风险）"""
        return RiskConfig(
            max_position_value=500000.0,
            max_position_ratio=0.5,
            max_single_position_ratio=0.1,
            max_order_value=50000.0,
            max_order_quantity=500.0,
            max_orders_per_minute=30,
            max_orders_per_day=500,
            max_daily_loss=25000.0,
            max_daily_loss_ratio=0.025,
            max_drawdown=0.1,
            min_order_interval=0.2,
            max_price_deviation=0.05
        )

    @pytest.fixture
    def large_account(self):
        """大额账户"""
        return Account(
            account_id="large_account",
            total_equity=5000000.0,  # 500万
            available_cash=4000000.0,
            margin=1000000.0,
            leverage=5.0,
            currency="USDT"
        )

    @pytest.fixture
    def small_account(self):
        """小额账户"""
        return Account(
            account_id="small_account",
            total_equity=10000.0,  # 1万
            available_cash=8000.0,
            margin=2000.0,
            leverage=10.0,
            currency="USDT"
        )

    def test_high_frequency_trading_scenario(self, aggressive_config, large_account):
        """测试高频交易场景"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 模拟高频订单流
        orders = []
        for i in range(100):
            order = Order(
                order_id=f"hf_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=0.1,
                price=50000.0,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="large_account"
            )
            orders.append(order)

        # 快速提交订单（模拟高频交易）
        passed_count = 0
        rejected_count = 0

        for i, order in enumerate(orders):
            # 模拟时间间隔（高频：0.1秒间隔）
            if i > 0:
                time.sleep(0.1)

            result = risk_manager.check_order(order, current_price=50000.0)

            if result.passed:
                passed_count += 1
                risk_manager.on_order_submitted(order)
            else:
                rejected_count += 1

        # 检查高频交易限制
        assert passed_count <= aggressive_config.max_orders_per_minute
        print(f"高频交易：通过 {passed_count}，拒绝 {rejected_count}")

    def test_market_crash_scenario(self, conservative_config, large_account):
        """测试市场崩盘场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(large_account)

        # 初始状态：正常交易
        order = Order(
            order_id="normal_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        # 正常检查通过
        result = risk_manager.check_order(order, current_price=50000.0)
        assert result.passed is True

        # 模拟市场崩盘：价格暴跌50%
        risk_manager.update_equity(2500000.0)  # 权益减半

        # 检查回撤和熔断
        assert risk_manager._metrics.current_drawdown > 0.4

        # 触发熔断检查
        risk_manager._check_circuit_breaker()

        # 应该触发熔断，禁用交易
        assert risk_manager._trading_enabled is False
        assert risk_manager._risk_level == RiskLevel.EMERGENCY

        # 尝试新订单应该被拒绝
        new_order = Order(
            order_id="crash_order",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            quantity=5.0,
            price=25000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        result = risk_manager.check_order(new_order, current_price=25000.0)
        assert result.passed is False

    def test_portfolio_concentration_scenario(self, aggressive_config, large_account):
        """测试投资组合集中度风险"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 模拟多个持仓
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT"]

        for i, symbol in enumerate(symbols):
            # 创建大额订单（接近单品种限制）
            order = Order(
                order_id=f"concentration_order_{i}",
                symbol=symbol,
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=10.0 if i == 0 else 5.0,  # BTC仓位更大
                price=50000.0 if i == 0 else 3000.0,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="large_account"
            )

            result = risk_manager.check_order(order, current_price=50000.0 if i == 0 else 3000.0)

            if result.passed:
                # 模拟持仓更新
                mock_position = Mock()
                mock_position.symbol = symbol
                mock_position.notional_value = order.quantity * order.price
                risk_manager.update_position(mock_position)
                risk_manager.on_order_submitted(order)

        # 检查总仓位比例
        assert risk_manager._metrics.position_ratio <= aggressive_config.max_position_ratio

        # 检查单品种集中度
        btc_position_value = risk_manager._positions.get("BTC/USDT", Mock(notional_value=0.0)).notional_value
        if btc_position_value > 0:
            btc_ratio = btc_position_value / large_account.total_equity
            assert btc_ratio <= aggressive_config.max_single_position_ratio

    def test_liquidity_crisis_scenario(self, conservative_config, small_account):
        """测试流动性危机场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(small_account)

        # 模拟流动性枯竭：价格大幅偏离
        orders = []
        for i in range(10):
            order = Order(
                order_id=f"liquidity_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=0.1,
                price=75000.0 if i % 2 == 0 else 25000.0,  # 大幅偏离
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="small_account"
            )
            orders.append(order)

        warning_count = 0
        for order in orders:
            result = risk_manager.check_order(order, current_price=50000.0)

            # 检查价格偏离警告
            if any("Price deviation" in msg for msg in result.messages):
                warning_count += 1

            if result.passed:
                risk_manager.on_order_submitted(order)

        # 应该产生大量价格偏离警告
        assert warning_count > 0
        print(f"流动性危机场景：价格偏离警告 {warning_count} 次")

    def test_margin_call_scenario(self, aggressive_config, large_account):
        """测试保证金追缴场景"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 初始高仓位
        risk_manager._metrics.total_position_value = 4500000.0  # 90%仓位
        risk_manager._metrics.position_ratio = 0.9

        # 模拟价格下跌触发保证金追缴
        risk_manager.update_equity(3500000.0)  # 权益下降

        # 检查风险级别升级
        risk_manager._update_risk_level()
        assert risk_manager._risk_level.value >= RiskLevel.WARNING.value

        # 尝试减仓订单
        sell_order = Order(
            order_id="margin_call_sell",
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            quantity=2.0,
            price=45000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        result = risk_manager.check_order(sell_order, current_price=45000.0)

        # 减仓订单应该通过（即使在高风险下）
        assert result.passed is True

    def test_flash_crash_recovery_scenario(self, conservative_config, large_account):
        """测试闪崩恢复场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(large_account)

        # 初始状态
        risk_manager.update_equity(5000000.0)

        # 模拟闪崩：价格瞬间暴跌
        risk_manager.update_equity(3000000.0)  # 40%下跌

        # 触发熔断
        risk_manager._check_circuit_breaker()
        assert risk_manager._trading_enabled is False

        # 模拟价格恢复
        risk_manager.update_equity(4500000.0)  # 部分恢复

        # 重置每日统计（模拟新交易日）
        risk_manager.reset_daily()

        # 检查交易是否重新启用
        assert risk_manager._trading_enabled is True

        # 尝试新订单
        recovery_order = Order(
            order_id="recovery_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=0.5,
            price=48000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        result = risk_manager.check_order(recovery_order, current_price=48000.0)
        assert result.passed is True

    def test_volatility_spike_scenario(self, aggressive_config, large_account):
        """测试波动率飙升场景"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 模拟高波动环境
        price_variations = [45000.0, 55000.0, 42000.0, 58000.0, 40000.0, 60000.0]

        warning_count = 0
        for i, price in enumerate(price_variations):
            order = Order(
                order_id=f"volatility_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                type=OrderType.LIMIT,
                quantity=1.0,
                price=price,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="large_account"
            )

            # 使用平均价格作为当前价格
            current_price = 50000.0
            result = risk_manager.check_order(order, current_price=current_price)

            # 统计价格偏离警告
            if any("Price deviation" in msg for msg in result.messages):
                warning_count += 1

            if result.passed:
                risk_manager.on_order_submitted(order)

        # 高波动环境下应该产生大量价格偏离警告
        assert warning_count >= len(price_variations) // 2
        print(f"波动率飙升场景：价格偏离警告 {warning_count} 次")

    def test_overnight_risk_scenario(self, conservative_config, large_account):
        """测试隔夜风险场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(large_account)

        # 模拟交易日结束时的持仓
        risk_manager._metrics.total_position_value = 2000000.0  # 40%仓位
        risk_manager._metrics.position_ratio = 0.4

        # 模拟隔夜价格波动
        # 假设夜间价格下跌20%
        overnight_equity = 4000000.0  # 权益下降20%
        risk_manager.update_equity(overnight_equity)

        # 检查隔夜风险指标
        assert risk_manager._metrics.daily_pnl == -1000000.0
        assert risk_manager._metrics.daily_pnl_ratio == -0.2

        # 新交易日开始，重置统计
        risk_manager.reset_daily()

        # 检查重置后的状态
        assert risk_manager._metrics.daily_pnl == 0.0
        assert risk_manager._daily_order_count == 0
        assert risk_manager._trading_enabled is True

    def test_correlation_breakdown_scenario(self, aggressive_config, large_account):
        """测试相关性破裂场景"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 模拟相关性破裂：不同资产价格走势分化
        assets = [
            ("BTC/USDT", 50000.0, 0.1),   # 主流资产
            ("ETH/USDT", 3000.0, 0.08),   # 主流资产
            ("ADA/USDT", 1.0, 0.5),      # 高风险资产
            ("DOT/USDT", 20.0, 0.3),     # 中风险资产
        ]

        total_risk_warnings = 0

        for symbol, price, volatility in assets:
            # 模拟该资产的价格波动
            for i in range(5):
                current_price = price * (1 + volatility * (i - 2) / 10)  # ±波动率

                order = Order(
                    order_id=f"correlation_order_{symbol}_{i}",
                    symbol=symbol,
                    side=OrderSide.BUY,
                    type=OrderType.LIMIT,
                    quantity=10.0 if "BTC" in symbol else 100.0,
                    price=current_price,
                    status=OrderStatus.PENDING,
                    created_time=datetime.now(),
                    account_id="large_account"
                )

                result = risk_manager.check_order(order, current_price=price)

                # 高风险资产可能产生更多警告
                if volatility > 0.2 and any("warning" in msg.lower() for msg in result.messages):
                    total_risk_warnings += 1

                if result.passed:
                    risk_manager.on_order_submitted(order)

        # 高风险资产应该产生更多风险警告
        assert total_risk_warnings > 0
        print(f"相关性破裂场景：风险警告 {total_risk_warnings} 次")

    def test_regulatory_impact_scenario(self, conservative_config, large_account):
        """测试监管影响场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(large_account)

        # 模拟监管收紧：降低风险限制
        conservative_config.max_position_ratio = 0.3  # 从0.5降到0.3
        conservative_config.max_order_value = 20000.0  # 从50000降到20000

        # 现有持仓可能超过新限制
        risk_manager._metrics.total_position_value = 2000000.0  # 40%仓位 > 新限制30%
        risk_manager._metrics.position_ratio = 0.4

        # 检查风险级别
        risk_manager._update_risk_level()
        assert risk_manager._risk_level.value >= RiskLevel.WARNING.value

        # 尝试新订单（应该被更严格的限制拒绝）
        order = Order(
            order_id="regulatory_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=25000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="large_account"
        )

        result = risk_manager.check_order(order, current_price=25000.0)

        # 可能因为仓位超限或订单金额超限被拒绝
        if not result.passed:
            assert any(keyword in result.messages[0] for keyword in ["exceeds", "limit"])

    def test_stress_test_comprehensive(self, aggressive_config, large_account):
        """综合压力测试"""
        risk_manager = RiskManager(config=aggressive_config)
        risk_manager.set_account(large_account)

        # 模拟极端市场条件
        scenarios = [
            # (权益变化, 价格变化, 订单数量)
            (0.8, 0.7, 50),   # 熊市：权益-20%，价格-30%，中等订单量
            (1.2, 1.3, 80),   # 牛市：权益+20%，价格+30%，高订单量
            (0.6, 0.5, 20),   # 崩盘：权益-40%，价格-50%，低订单量
            (1.0, 1.0, 100),  # 横盘：权益不变，价格不变，极高订单量
        ]

        total_orders = 0
        passed_orders = 0
        rejected_orders = 0
        warnings_issued = 0

        for equity_multiplier, price_multiplier, order_count in scenarios:
            # 更新权益
            new_equity = large_account.total_equity * equity_multiplier
            risk_manager.update_equity(new_equity)

            # 生成订单
            base_price = 50000.0 * price_multiplier

            for i in range(order_count):
                order = Order(
                    order_id=f"stress_order_{total_orders}",
                    symbol="BTC/USDT",
                    side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                    type=OrderType.LIMIT,
                    quantity=0.5 + (i % 5) * 0.1,
                    price=base_price * (0.95 + (i % 10) * 0.01),
                    status=OrderStatus.PENDING,
                    created_time=datetime.now(),
                    account_id="large_account"
                )

                result = risk_manager.check_order(order, current_price=base_price)
                total_orders += 1

                if result.passed:
                    passed_orders += 1
                    risk_manager.on_order_submitted(order)
                else:
                    rejected_orders += 1

                warnings_issued += len([msg for msg in result.messages if "warning" in msg.lower()])

                # 小延迟模拟真实交易间隔
                time.sleep(0.01)

        # 输出压力测试结果
        print(f"综合压力测试结果：")
        print(f"总订单数: {total_orders}")
        print(f"通过订单: {passed_orders}")
        print(f"拒绝订单: {rejected_orders}")
        print(f"警告次数: {warnings_issued}")
        print(f"通过率: {passed_orders/total_orders*100:.1f}%")

        # 验证风险控制有效性
        assert passed_orders <= aggressive_config.max_orders_per_day
        assert risk_manager._risk_level != RiskLevel.EMERGENCY or not risk_manager._trading_enabled

    def test_risk_level_transition_scenario(self, conservative_config, large_account):
        """测试风险级别转换场景"""
        risk_manager = RiskManager(config=conservative_config)
        risk_manager.set_account(large_account)

        # 初始状态：正常
        assert risk_manager._risk_level == RiskLevel.NORMAL

        # 逐步增加风险，观察级别转换
        risk_levels = []

        # 阶段1：轻微风险（警告）
        risk_manager._metrics.position_ratio = 0.45  # 接近50%限制
        risk_manager._update_risk_level()
        risk_levels.append(risk_manager._risk_level)

        # 阶段2：中等风险（告警）
        risk_manager._metrics.position_ratio = 0.55  # 超过50%限制
        risk_manager._metrics.daily_pnl_ratio = -0.03  # 接近-2.5%限制
        risk_manager._update_risk_level()
        risk_levels.append(risk_manager._risk_level)

        # 阶段3：高风险（危险）
        risk_manager._metrics.current_drawdown = 0.12  # 超过10%限制
        risk_manager._update_risk_level()
        risk_levels.append(risk_manager._risk_level)

        # 阶段4：极端风险（紧急）
        risk_manager._metrics.current_drawdown = 0.25  # 严重超过限制
        risk_manager._check_circuit_breaker()
        risk_levels.append(risk_manager._risk_level)

        # 验证风险级别逐步升级
        assert risk_levels[0].value <= risk_levels[1].value
        assert risk_levels[1].value <= risk_levels[2].value
        assert risk_levels[2].value <= risk_levels[3].value

        # 最终应该触发熔断
        assert risk_manager._trading_enabled is False
        assert risk_manager._risk_level == RiskLevel.EMERGENCY
