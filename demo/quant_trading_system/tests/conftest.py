"""
测试配置文件
============

为风险管理系统测试提供必要的fixture和配置
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from quant_trading_system.services.risk.risk_manager import (
    RiskManager, RiskConfig, RiskLevel, RiskCheckResult, RiskMetrics
)
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.models.account import Account, AccountType, Balance
from quant_trading_system.core.events import EventEngine, EventType, Event


@pytest.fixture
def risk_config():
    """默认风险配置"""
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
def aggressive_config():
    """激进风险配置"""
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
def conservative_config():
    """保守风险配置"""
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
def mock_account():
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
def large_account():
    """大额账户"""
    return Account(
        id="large_account",
        type=AccountType.SPOT,
        balances={"USDT": Balance(asset="USDT", free=4000000.0, locked=1000000.0, total=5000000.0)},
        total_balance=5000000.0,
        available_balance=4000000.0,
        margin_balance=1000000.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        updated_at=datetime.now()
    )


@pytest.fixture
def small_account():
    """小额账户"""
    return Account(
        id="small_account",
        type=AccountType.SPOT,
        balances={"USDT": Balance(asset="USDT", free=8000.0, locked=2000.0, total=10000.0)},
        total_balance=10000.0,
        available_balance=8000.0,
        margin_balance=2000.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        updated_at=datetime.now()
    )


@pytest.fixture
def zero_equity_account():
    """零权益账户"""
    return Account(
        id="zero_account",
        type=AccountType.SPOT,
        balances={"USDT": Balance(asset="USDT", free=0.0, locked=0.0, total=0.0)},
        total_balance=0.0,
        available_balance=0.0,
        margin_balance=0.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        updated_at=datetime.now()
    )


@pytest.fixture
def mock_order():
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


@pytest.fixture
def sell_order():
    """卖出订单"""
    return Order(
        id="sell_order_001",
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        type=OrderType.LIMIT,
        quantity=0.5,
        price=51000.0,
        status=OrderStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def market_order():
    """市价订单"""
    return Order(
        id="market_order_001",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        quantity=0.1,
        price=None,
        status=OrderStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def large_order():
    """大额订单"""
    return Order(
        id="large_order_001",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        quantity=10.0,
        price=50000.0,
        status=OrderStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def small_order():
    """小额订单"""
    return Order(
        id="small_order_001",
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        quantity=0.001,
        price=50000.0,
        status=OrderStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def risk_manager(risk_config):
    """风险管理器实例"""
    event_engine = Mock(spec=EventEngine)
    return RiskManager(config=risk_config, event_engine=event_engine)


@pytest.fixture
def risk_manager_without_event_engine(risk_config):
    """无事件引擎的风险管理器"""
    return RiskManager(config=risk_config, event_engine=None)


@pytest.fixture
def mock_position():
    """模拟持仓"""
    position = Mock()
    position.symbol = "BTC/USDT"
    position.notional_value = 300000.0
    position.quantity = 6.0
    position.average_price = 50000.0
    position.unrealized_pnl = 0.0
    position.realized_pnl = 0.0
    return position


@pytest.fixture
def multiple_positions():
    """多个模拟持仓"""
    positions = []

    symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT"]
    values = [300000.0, 200000.0, 100000.0, 80000.0, 50000.0]

    for symbol, value in zip(symbols, values):
        position = Mock()
        position.symbol = symbol
        position.notional_value = value
        positions.append(position)

    return positions


@pytest.fixture
def event_engine():
    """模拟事件引擎"""
    engine = Mock(spec=EventEngine)
    engine.put = Mock()
    return engine


@pytest.fixture
def risk_check_result():
    """风险检查结果"""
    return RiskCheckResult()


@pytest.fixture
def risk_metrics():
    """风险指标"""
    return RiskMetrics()


@pytest.fixture
def all_risk_levels():
    """所有风险级别"""
    return list(RiskLevel)


@pytest.fixture
def high_frequency_orders():
    """高频交易订单列表"""
    orders = []
    for i in range(100):
        order = Order(
            id=f"hf_order_{i:03d}",
            symbol="BTC/USDT",
            side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=0.1 + (i % 10) * 0.01,
            price=50000.0 + (i % 100) * 10,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orders.append(order)
    return orders


@pytest.fixture
def stress_test_orders():
    """压力测试订单列表"""
    orders = []
    for i in range(1000):
        order = Order(
            id=f"stress_order_{i:04d}",
            symbol="BTC/USDT",
            side=OrderSide.BUY if i % 3 == 0 else OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=0.5 + (i % 20) * 0.1,
            price=50000.0 + (i % 200) * 50,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orders.append(order)
    return orders


@pytest.fixture
def performance_test_orders():
    """性能测试订单列表"""
    orders = []
    for i in range(10000):
        order = Order(
            id=f"perf_order_{i:05d}",
            symbol="BTC/USDT",
            side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
            type=OrderType.LIMIT,
            quantity=0.1 + (i % 100) * 0.01,
            price=50000.0 + (i % 1000) * 1,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        orders.append(order)
    return orders


@pytest.fixture
def risk_scenario_data():
    """风险场景测试数据"""
    return {
        'market_crash': {
            'equity_change': -0.4,  # 权益下降40%
            'price_change': -0.5,    # 价格下跌50%
            'order_count': 50
        },
        'bull_market': {
            'equity_change': 0.3,   # 权益增长30%
            'price_change': 0.4,    # 价格上涨40%
            'order_count': 100
        },
        'volatility_spike': {
            'equity_change': -0.1,  # 权益下降10%
            'price_change': 0.2,    # 价格波动20%
            'order_count': 200
        }
    }


@pytest.fixture
def datetime_now():
    """当前时间"""
    return datetime.now()


@pytest.fixture
def time_mock():
    """时间模拟"""
    return Mock()


# 钩子函数
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试报告钩子"""
    outcome = yield
    report = outcome.get_result()

    # 在测试失败时记录额外信息
    if report.failed:
        # 可以在这里添加失败时的日志记录
        pass


# 自定义标记
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line(
        "markers", "performance: 标记为性能测试"
    )
    config.addinivalue_line(
        "markers", "stress: 标记为压力测试"
    )
    config.addinivalue_line(
        "markers", "scenario: 标记为场景测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )


# 测试跳过条件
@pytest.fixture(autouse=True)
def skip_slow_tests(request):
    """自动跳过慢速测试（除非明确指定）"""
    if request.node.get_closest_marker('slow') and not request.config.getoption('--run-slow'):
        pytest.skip('跳过慢速测试（使用--run-slow运行）')


# 命令行选项
@pytest.fixture
def run_slow_tests(request):
    """是否运行慢速测试"""
    return request.config.getoption('--run-slow')


# 添加命令行选项
@pytest.fixture
def performance_threshold(request):
    """性能测试阈值"""
    return request.config.getoption('--performance-threshold')


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        '--run-slow',
        action='store_true',
        default=False,
        help='运行慢速测试'
    )
    parser.addoption(
        '--performance-threshold',
        action='store',
        default='1000',
        help='性能测试吞吐量阈值（次/秒）'
    )
    parser.addoption(
        '--stress-test-scale',
        action='store',
        default='1000',
        help='压力测试规模（订单数量）'
    )
