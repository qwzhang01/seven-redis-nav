"""调试回测脚本"""

import quant_trading_system.strategies  # noqa: F401

from quant_trading_system.models.market import TimeFrame
from quant_trading_system.services.backtest.backtest_engine import (
    BacktestConfig,
    BacktestEngine,
)
from quant_trading_system.services.market.mock_data import generate_mock_klines
from quant_trading_system.services.strategy.base import get_strategy_class

# 生成数据
print("生成模拟数据...")
bars = generate_mock_klines(
    symbol="BTCUSDT",
    timeframe=TimeFrame.M1,
    start_time="2025-01-01",
    end_time="2025-12-31",
)
print(f"生成了 {len(bars)} 根K线")
print(f"时间范围: {bars.timestamp[0]} 到 {bars.timestamp[-1]}")
print(f"价格范围: {bars.close.min():.2f} - {bars.close.max():.2f}")
print()

# 获取策略
print("加载策略...")
strategy_class = get_strategy_class("macd_cross")
if not strategy_class:
    print("错误：找不到策略 macd_cross")
    exit(1)

strategy = strategy_class()
print(f"策略: {strategy.name}")
print(f"参数: {strategy.params}")
print()

# 配置回测
config = BacktestConfig(
    initial_capital=100000.0,
    commission_rate=0.001,
    slippage_rate=0.0005,
)

# 运行回测
print("开始回测...")
engine = BacktestEngine(config=config)

# 添加调试：检查策略的on_bar是否被调用
original_on_bar = strategy.on_bar
call_count = 0
signal_count = 0

def debug_on_bar(bar):
    global call_count, signal_count
    call_count += 1
    result = original_on_bar(bar)
    if result:
        signal_count += 1
        print(f"[Bar {call_count}] 生成信号: {result}")
    if call_count % 1000 == 0:
        print(f"已处理 {call_count} 根K线...")
    return result

strategy.on_bar = debug_on_bar

result = engine.run(strategy, bars)

print()
print(f"on_bar 调用次数: {call_count}")
print(f"信号生成次数: {signal_count}")
print()

# 显示结果
print("=" * 60)
print("回测结果")
print("=" * 60)
print()
print(f"策略名称: {result.strategy_name}")
print(f"回测周期: {result.duration_days:.1f} 天")
print()
print(f"初始资金: {result.initial_capital:,.2f}")
print(f"最终资金: {result.final_capital:,.2f}")
print(f"总收益率: {result.total_return:.2%}")
print(f"年化收益率: {result.annual_return:.2%}")
print()
print(f"总交易次数: {result.total_trades}")
print(f"盈利次数: {result.winning_trades}")
print(f"亏损次数: {result.losing_trades}")
print(f"胜率: {result.win_rate:.2%}")
print()
print(f"最大回撤: {result.max_drawdown:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
