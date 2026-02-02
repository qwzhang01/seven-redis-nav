"""
回测测试
"""

import numpy as np
import pytest

from quant_trading_system.models.market import Bar, BarArray, TimeFrame
from quant_trading_system.services.backtest import BacktestEngine, BacktestConfig
from quant_trading_system.services.strategy.base import Strategy, register_strategy
from quant_trading_system.services.strategy.signal import Signal, SignalType


class SimpleTestStrategy(Strategy):
    """简单测试策略"""
    
    name = "test_strategy"
    
    def __init__(self, **params):
        super().__init__(**params)
        self._bar_count = 0
    
    def on_bar(self, bar: Bar):
        self._bar_count += 1
        
        # 每10根K线交易一次
        if self._bar_count % 10 == 5:
            return self.buy(bar.symbol, quantity=0.1)
        elif self._bar_count % 10 == 0:
            position = self.get_position(bar.symbol)
            if position and position.quantity > 0:
                return self.sell(bar.symbol, quantity=position.quantity)
        
        return None


def generate_test_bars(n: int = 200) -> BarArray:
    """生成测试K线数据"""
    np.random.seed(42)
    
    price = 10000 + np.cumsum(np.random.randn(n) * 100)
    
    return BarArray(
        symbol="TEST/USDT",
        exchange="test",
        timeframe=TimeFrame.M15,
        timestamp=np.arange(n, dtype=float) * 60000,
        open=price - np.random.rand(n) * 10,
        high=price + np.random.rand(n) * 20,
        low=price - np.random.rand(n) * 20,
        close=price,
        volume=np.random.rand(n) * 100,
    )


class TestBacktestEngine:
    """回测引擎测试"""
    
    def test_run_backtest(self):
        bars = generate_test_bars(200)
        strategy = SimpleTestStrategy()
        strategy.symbols = ["TEST/USDT"]
        strategy.timeframes = [TimeFrame.M15]
        
        config = BacktestConfig(
            initial_capital=100000,
            commission_rate=0.0004,
        )
        
        engine = BacktestEngine(config)
        result = engine.run(strategy, bars)
        
        assert result is not None
        assert result.initial_capital == 100000
        assert result.total_trades >= 0
    
    def test_backtest_result_metrics(self):
        bars = generate_test_bars(500)
        strategy = SimpleTestStrategy()
        strategy.symbols = ["TEST/USDT"]
        strategy.timeframes = [TimeFrame.M15]
        
        engine = BacktestEngine()
        result = engine.run(strategy, bars)
        
        # 检查结果包含所有必要字段
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'max_drawdown')
        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'win_rate')
