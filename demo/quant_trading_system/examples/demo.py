"""
使用示例
========

展示如何使用量化交易系统
"""

import asyncio
import numpy as np
from datetime import datetime

from quant_trading_system.models.market import Bar, BarArray, TimeFrame
from quant_trading_system.services.indicators import IndicatorEngine
from quant_trading_system.services.backtest import BacktestEngine, BacktestConfig
from quant_trading_system.services.backtest.performance import PerformanceAnalyzer
from quant_trading_system.strategies.examples import DualMAStrategy


def generate_sample_data(n: int = 100) -> BarArray:
    """生成示例数据"""
    np.random.seed(42)

    # 生成随机价格序列
    returns = np.random.randn(n) * 0.02  # 2%的日波动率
    price = 10000 * np.exp(np.cumsum(returns))

    # 生成OHLCV数据
    timestamps = np.arange(n) * 60000 + 1609459200000  # 从2021-01-01开始

    # 创建Bar对象列表
    bar_list = []
    for i in range(n):
        bar = Bar(
            timestamp=datetime.fromtimestamp(timestamps[i] / 1000),
            open=price[i] * (1 - np.random.rand() * 0.01),
            high=price[i] * (1 + np.random.rand() * 0.02),
            low=price[i] * (1 - np.random.rand() * 0.02),
            close=price[i],
            volume=np.random.rand() * 1000,
            symbol="BTC/USDT",
            timeframe=TimeFrame.M15
        )
        bar_list.append(bar)

    bars = BarArray(
        bars=bar_list,
        symbol="BTC/USDT",
        timeframe=TimeFrame.M15
    )

    return bars


def example_indicator_calculation():
    """指标计算示例"""
    print("=" * 50)
    print("指标计算示例")
    print("=" * 50)

    # 生成数据
    bars = generate_sample_data(200)

    # 创建指标引擎
    engine = IndicatorEngine()

    # 计算各种指标
    print("\n计算技术指标:")

    # SMA
    sma_result = engine.calculate("SMA", bars, period=20)
    print(f"SMA(20) 最新值: {sma_result['sma'][-1]:.2f}")

    # EMA
    ema_result = engine.calculate("EMA", bars, period=20)
    print(f"EMA(20) 最新值: {ema_result['ema'][-1]:.2f}")

    # MACD
    macd_result = engine.calculate("MACD", bars)
    print(f"MACD: {macd_result['macd'][-1]:.4f}")
    print(f"Signal: {macd_result['signal'][-1]:.4f}")
    print(f"Histogram: {macd_result['histogram'][-1]:.4f}")

    # RSI
    rsi_result = engine.calculate("RSI", bars, period=14)
    print(f"RSI(14): {rsi_result['rsi'][-1]:.2f}")

    # 布林带
    boll_result = engine.calculate("BOLL", bars, period=20, std_dev=2)
    print(f"BOLL Upper: {boll_result['upper'][-1]:.2f}")
    print(f"BOLL Middle: {boll_result['middle'][-1]:.2f}")
    print(f"BOLL Lower: {boll_result['lower'][-1]:.2f}")

    print(f"\n引擎统计: {engine.stats}")


def example_backtest():
    """回测示例"""
    print("\n" + "=" * 50)
    print("策略回测示例")
    print("=" * 50)

    # 生成数据
    bars = generate_sample_data(1000)

    # 创建策略
    strategy = DualMAStrategy(
        fast_period=5,
        slow_period=20,
    )
    strategy.symbols = ["BTC/USDT"]

    # 创建回测配置
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.0004,
        slippage_rate=0.0001,
    )

    # 运行回测
    engine = BacktestEngine(config)
    result = engine.run(strategy, bars)

    # 输出结果
    print(f"\n回测结果:")
    print(f"  初始资金: {result.initial_capital:,.2f}")
    print(f"  最终资金: {result.final_capital:,.2f}")
    print(f"  总收益率: {result.total_return:.2%}")
    print(f"  年化收益: {result.annual_return:.2%}")
    print(f"  最大回撤: {result.max_drawdown:.2%}")
    print(f"  夏普比率: {result.sharpe_ratio:.2f}")
    print(f"  总交易次数: {result.total_trades}")
    print(f"  胜率: {result.win_rate:.2%}")
    print(f"  盈亏比: {result.profit_factor:.2f}")

    # 绩效分析
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result)

    print(f"\n详细绩效报告:")
    for category, metrics in report.items():
        print(f"\n  {category}:")
        for key, value in metrics.items():
            print(f"    {key}: {value}")


async def example_event_engine():
    """事件引擎示例"""
    print("\n" + "=" * 50)
    print("事件引擎示例")
    print("=" * 50)

    from quant_trading_system.core.events import Event, EventEngine, EventType

    # 创建事件引擎
    engine = EventEngine(num_workers=2)

    # 定义事件处理器
    tick_count = 0

    async def on_tick(event: Event):
        nonlocal tick_count
        tick_count += 1
        print(f"收到Tick事件: {event.data}")

    # 注册处理器
    engine.register(EventType.TICK, on_tick)

    # 启动引擎
    await engine.start()

    # 发送一些事件
    for i in range(5):
        await engine.put(Event(
            type=EventType.TICK,
            data={"price": 10000 + i * 100},
        ))

    # 等待处理完成
    await asyncio.sleep(0.5)

    # 停止引擎
    await engine.stop()

    print(f"\n处理了 {tick_count} 个Tick事件")
    print(f"引擎统计: {engine.stats}")


def main():
    """运行所有示例"""
    print("=" * 60)
    print("量化交易系统 - 使用示例")
    print("=" * 60)

    # 指标计算示例
    example_indicator_calculation()

    # 回测示例
    example_backtest()

    # 事件引擎示例
    asyncio.run(example_event_engine())

    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
