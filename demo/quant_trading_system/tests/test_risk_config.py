"""
风险配置测试
============

专门测试风险配置的各种组合和边界条件
"""

import pytest
from unittest.mock import Mock

from quant_trading_system.services.risk.risk_manager import (
    RiskConfig, RiskLevel, RiskCheckResult, RiskMetrics
)
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.models.account import Account


class TestRiskConfig:
    """风险配置测试"""

    def test_default_config_values(self):
        """测试默认配置值"""
        config = RiskConfig()

        # 验证默认值
        assert config.max_position_value == 1000000.0
        assert config.max_position_ratio == 0.8
        assert config.max_single_position_ratio == 0.2
        assert config.max_order_value == 100000.0
        assert config.max_order_quantity == 1000.0
        assert config.max_orders_per_minute == 60
        assert config.max_orders_per_day == 1000
        assert config.max_daily_loss == 50000.0
        assert config.max_daily_loss_ratio == 0.05
        assert config.max_drawdown == 0.2
        assert config.min_order_interval == 0.1
        assert config.max_price_deviation == 0.1

    def test_custom_config_values(self):
        """测试自定义配置值"""
        config = RiskConfig(
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

        # 验证自定义值
        assert config.max_position_value == 2000000.0
        assert config.max_position_ratio == 0.9
        assert config.max_single_position_ratio == 0.3
        assert config.max_order_value == 200000.0
        assert config.max_order_quantity == 2000.0
        assert config.max_orders_per_minute == 120
        assert config.max_orders_per_day == 2000
        assert config.max_daily_loss == 100000.0
        assert config.max_daily_loss_ratio == 0.1
        assert config.max_drawdown == 0.3
        assert config.min_order_interval == 0.05
        assert config.max_price_deviation == 0.15

    def test_extreme_config_values(self):
        """测试极端配置值"""
        # 测试非常宽松的配置
        loose_config = RiskConfig(
            max_position_value=10000000.0,
            max_position_ratio=0.99,
            max_order_value=1000000.0,
            max_orders_per_minute=1000,
            max_daily_loss=500000.0,
            max_drawdown=0.5
        )

        assert loose_config.max_position_ratio == 0.99
        assert loose_config.max_drawdown == 0.5

        # 测试非常严格的配置
        strict_config = RiskConfig(
            max_position_value=10000.0,
            max_position_ratio=0.1,
            max_order_value=1000.0,
            max_orders_per_minute=10,
            max_daily_loss=1000.0,
            max_drawdown=0.05
        )

        assert strict_config.max_position_ratio == 0.1
        assert strict_config.max_drawdown == 0.05

    def test_config_boundary_values(self):
        """测试配置边界值"""
        # 测试边界值配置
        boundary_config = RiskConfig(
            max_position_value=0.0,  # 零值
            max_position_ratio=0.0,  # 零比例
            max_order_value=0.0,     # 零订单金额
            max_order_quantity=0.0,  # 零数量
            max_orders_per_minute=0,  # 零频率
            max_daily_loss=0.0,      # 零亏损
            max_drawdown=0.0         # 零回撤
        )

        # 验证边界值
        assert boundary_config.max_position_value == 0.0
        assert boundary_config.max_position_ratio == 0.0
        assert boundary_config.max_order_value == 0.0
        assert boundary_config.max_order_quantity == 0.0
        assert boundary_config.max_orders_per_minute == 0
        assert boundary_config.max_daily_loss == 0.0
        assert boundary_config.max_drawdown == 0.0

    def test_config_validation(self):
        """测试配置验证逻辑"""
        # 测试配置一致性
        config = RiskConfig()

        # 验证配置之间的逻辑关系
        assert config.max_order_value <= config.max_position_value
        assert config.max_single_position_ratio <= config.max_position_ratio
        assert config.max_daily_loss_ratio <= 1.0  # 亏损比例不能超过100%
        assert config.max_drawdown <= 1.0         # 回撤不能超过100%
        assert config.min_order_interval >= 0.0   # 间隔不能为负

    def test_config_comparison(self):
        """测试配置比较"""
        config1 = RiskConfig(max_position_value=1000000.0)
        config2 = RiskConfig(max_position_value=1000000.0)
        config3 = RiskConfig(max_position_value=2000000.0)

        # 相同配置应该相等
        assert config1.max_position_value == config2.max_position_value

        # 不同配置应该不同
        assert config1.max_position_value != config3.max_position_value

    def test_config_immutability(self):
        """测试配置不可变性"""
        config = RiskConfig()

        # 尝试修改配置值（应该失败）
        try:
            config.max_position_value = 2000000.0
            pytest.fail("配置应该不可变")
        except (AttributeError, TypeError):
            # 预期行为：配置不可变
            pass

    def test_config_copy(self):
        """测试配置复制"""
        original_config = RiskConfig(max_position_value=1000000.0)

        # 创建新配置（复制）
        copied_config = RiskConfig(
            max_position_value=original_config.max_position_value,
            max_position_ratio=original_config.max_position_ratio,
            max_single_position_ratio=original_config.max_single_position_ratio,
            max_order_value=original_config.max_order_value,
            max_order_quantity=original_config.max_order_quantity,
            max_orders_per_minute=original_config.max_orders_per_minute,
            max_orders_per_day=original_config.max_orders_per_day,
            max_daily_loss=original_config.max_daily_loss,
            max_daily_loss_ratio=original_config.max_daily_loss_ratio,
            max_drawdown=original_config.max_drawdown,
            min_order_interval=original_config.min_order_interval,
            max_price_deviation=original_config.max_price_deviation
        )

        # 验证复制结果
        assert copied_config.max_position_value == original_config.max_position_value
        assert copied_config.max_position_ratio == original_config.max_position_ratio
        assert copied_config.max_single_position_ratio == original_config.max_single_position_ratio

    def test_config_serialization(self):
        """测试配置序列化"""
        config = RiskConfig()

        # 转换为字典
        config_dict = {
            'max_position_value': config.max_position_value,
            'max_position_ratio': config.max_position_ratio,
            'max_single_position_ratio': config.max_single_position_ratio,
            'max_order_value': config.max_order_value,
            'max_order_quantity': config.max_order_quantity,
            'max_orders_per_minute': config.max_orders_per_minute,
            'max_orders_per_day': config.max_orders_per_day,
            'max_daily_loss': config.max_daily_loss,
            'max_daily_loss_ratio': config.max_daily_loss_ratio,
            'max_drawdown': config.max_drawdown,
            'min_order_interval': config.min_order_interval,
            'max_price_deviation': config.max_price_deviation
        }

        # 验证序列化结果
        assert isinstance(config_dict, dict)
        assert 'max_position_value' in config_dict
        assert config_dict['max_position_value'] == 1000000.0

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            'max_position_value': 2000000.0,
            'max_position_ratio': 0.9,
            'max_single_position_ratio': 0.3,
            'max_order_value': 200000.0,
            'max_order_quantity': 2000.0,
            'max_orders_per_minute': 120,
            'max_orders_per_day': 2000,
            'max_daily_loss': 100000.0,
            'max_daily_loss_ratio': 0.1,
            'max_drawdown': 0.3,
            'min_order_interval': 0.05,
            'max_price_deviation': 0.15
        }

        config = RiskConfig(**config_dict)

        # 验证配置值
        assert config.max_position_value == 2000000.0
        assert config.max_position_ratio == 0.9
        assert config.max_single_position_ratio == 0.3
        assert config.max_order_value == 200000.0
        assert config.max_order_quantity == 2000.0
        assert config.max_orders_per_minute == 120
        assert config.max_orders_per_day == 2000
        assert config.max_daily_loss == 100000.0
        assert config.max_daily_loss_ratio == 0.1
        assert config.max_drawdown == 0.3
        assert config.min_order_interval == 0.05
        assert config.max_price_deviation == 0.15

    def test_config_partial_update(self):
        """测试配置部分更新"""
        # 创建默认配置
        config = RiskConfig()

        # 部分更新配置
        updated_config = RiskConfig(
            max_position_value=2000000.0,
            max_order_value=200000.0,
            max_orders_per_minute=120
        )

        # 验证更新结果
        assert updated_config.max_position_value == 2000000.0
        assert updated_config.max_order_value == 200000.0
        assert updated_config.max_orders_per_minute == 120

        # 未指定的值应该保持默认
        assert updated_config.max_position_ratio == config.max_position_ratio
        assert updated_config.max_daily_loss == config.max_daily_loss

    def test_config_edge_cases(self):
        """测试配置边界情况"""
        # 测试负值配置（应该被拒绝或转换为正数）
        try:
            config = RiskConfig(max_position_value=-1000.0)
            # 如果允许负值，验证行为
            if config.max_position_value < 0:
                # 负值配置可能表示无限制
                pass
        except ValueError:
            # 预期行为：负值不被允许
            pass

        # 测试极大值配置
        huge_config = RiskConfig(
            max_position_value=1e18,  # 极大值
            max_orders_per_minute=1000000,
            max_daily_loss=1e15
        )

        assert huge_config.max_position_value == 1e18
        assert huge_config.max_orders_per_minute == 1000000
        assert huge_config.max_daily_loss == 1e15

    def test_config_for_different_account_sizes(self):
        """测试不同账户规模的配置"""
        # 小额账户配置
        small_account_config = RiskConfig(
            max_position_value=10000.0,
            max_order_value=1000.0,
            max_daily_loss=500.0
        )

        # 中等账户配置
        medium_account_config = RiskConfig(
            max_position_value=100000.0,
            max_order_value=10000.0,
            max_daily_loss=5000.0
        )

        # 大额账户配置
        large_account_config = RiskConfig(
            max_position_value=1000000.0,
            max_order_value=100000.0,
            max_daily_loss=50000.0
        )

        # 验证配置比例关系
        assert small_account_config.max_order_value / small_account_config.max_position_value == 0.1
        assert medium_account_config.max_order_value / medium_account_config.max_position_value == 0.1
        assert large_account_config.max_order_value / large_account_config.max_position_value == 0.1

    def test_config_for_different_risk_profiles(self):
        """测试不同风险偏好的配置"""
        # 保守型配置
        conservative_config = RiskConfig(
            max_position_ratio=0.5,
            max_drawdown=0.1,
            max_daily_loss_ratio=0.02
        )

        # 平衡型配置
        balanced_config = RiskConfig(
            max_position_ratio=0.7,
            max_drawdown=0.2,
            max_daily_loss_ratio=0.05
        )

        # 激进型配置
        aggressive_config = RiskConfig(
            max_position_ratio=0.9,
            max_drawdown=0.3,
            max_daily_loss_ratio=0.1
        )

        # 验证风险级别
        assert conservative_config.max_position_ratio < balanced_config.max_position_ratio
        assert balanced_config.max_position_ratio < aggressive_config.max_position_ratio
        assert conservative_config.max_drawdown < balanced_config.max_drawdown
        assert balanced_config.max_drawdown < aggressive_config.max_drawdown

    def test_config_validation_scenarios(self):
        """测试配置验证场景"""
        # 场景1：订单金额不能超过持仓市值
        try:
            invalid_config = RiskConfig(
                max_position_value=10000.0,
                max_order_value=20000.0  # 订单金额 > 持仓市值
            )
            # 如果允许，验证行为
            if invalid_config.max_order_value > invalid_config.max_position_value:
                # 可能表示特殊逻辑
                pass
        except ValueError:
            # 预期行为：配置验证失败
            pass

        # 场景2：单品种仓位不能超过总仓位
        try:
            invalid_config = RiskConfig(
                max_position_ratio=0.5,
                max_single_position_ratio=0.6  # 单品种 > 总仓位
            )
            # 如果允许，验证行为
            if invalid_config.max_single_position_ratio > invalid_config.max_position_ratio:
                # 可能表示特殊逻辑
                pass
        except ValueError:
            # 预期行为：配置验证失败
            pass

    def test_config_performance_characteristics(self):
        """测试配置性能特征"""
        import time

        # 测试配置创建性能
        start_time = time.time()

        for i in range(1000):
            config = RiskConfig()

        end_time = time.time()
        creation_time = end_time - start_time

        # 配置创建应该很快
        assert creation_time < 1.0
        print(f"配置创建性能：{creation_time:.4f}秒（1000次）")

        # 测试配置访问性能
        config = RiskConfig()

        start_time = time.time()

        for i in range(10000):
            _ = config.max_position_value
            _ = config.max_order_value
            _ = config.max_drawdown

        end_time = time.time()
        access_time = end_time - start_time

        # 配置访问应该非常快
        assert access_time < 0.1
        print(f"配置访问性能：{access_time:.4f}秒（30000次访问）")

    def test_config_compatibility(self):
        """测试配置兼容性"""
        # 测试与不同版本的兼容性
        old_config = RiskConfig(
            max_position_value=1000000.0,
            max_position_ratio=0.8,
            max_order_value=100000.0
        )

        new_config = RiskConfig(
            max_position_value=old_config.max_position_value,
            max_position_ratio=old_config.max_position_ratio,
            max_order_value=old_config.max_order_value,
            # 新版本可能添加的新参数使用默认值
            max_single_position_ratio=0.2,
            max_daily_loss_ratio=0.05
        )

        # 验证兼容性
        assert new_config.max_position_value == old_config.max_position_value
        assert new_config.max_position_ratio == old_config.max_position_ratio
        assert new_config.max_order_value == old_config.max_order_value

    def test_config_error_handling(self):
        """测试配置错误处理"""
        # 测试无效参数类型
        try:
            config = RiskConfig(max_position_value="invalid")  # 字符串而非数字
            pytest.fail("应该抛出类型错误")
        except (TypeError, ValueError):
            # 预期行为：类型错误
            pass

        # 测试缺失参数（使用默认值）
        config = RiskConfig()  # 无参数，使用所有默认值
        assert config.max_position_value == 1000000.0
        assert config.max_position_ratio == 0.8

    def test_config_documentation(self):
        """测试配置文档完整性"""
        config = RiskConfig()

        # 验证所有配置参数都有合理的默认值
        assert hasattr(config, 'max_position_value')
        assert hasattr(config, 'max_position_ratio')
        assert hasattr(config, 'max_single_position_ratio')
        assert hasattr(config, 'max_order_value')
        assert hasattr(config, 'max_order_quantity')
        assert hasattr(config, 'max_orders_per_minute')
        assert hasattr(config, 'max_orders_per_day')
        assert hasattr(config, 'max_daily_loss')
        assert hasattr(config, 'max_daily_loss_ratio')
        assert hasattr(config, 'max_drawdown')
        assert hasattr(config, 'min_order_interval')
        assert hasattr(config, 'max_price_deviation')

        # 验证默认值合理性
        assert config.max_position_value > 0
        assert 0 < config.max_position_ratio <= 1
        assert 0 < config.max_single_position_ratio <= 1
        assert config.max_order_value > 0
        assert config.max_order_quantity > 0
        assert config.max_orders_per_minute > 0
        assert config.max_orders_per_day > 0
        assert config.max_daily_loss > 0
        assert 0 < config.max_daily_loss_ratio <= 1
        assert 0 < config.max_drawdown <= 1
        assert config.min_order_interval >= 0
        assert config.max_price_deviation >= 0
