"""
实时数据采集和回测示例

展示如何：
1. 启动实时数据采集服务，将数据存储到TimescaleDB
2. 从TimescaleDB获取历史数据进行回测
"""

import asyncio
from datetime import datetime, timedelta
import structlog

from quant_trading_system.services.market.real_time_collector import (
    get_real_time_collector,
    start_real_time_collection,
    stop_real_time_collection
)
from quant_trading_system.services.backtest.backtest_engine import BacktestEngine, BacktestConfig
from quant_trading_system.services.database.data_query import get_data_query_service
from quant_trading_system.models.market import TimeFrame
from quant_trading_system.services.strategy.base import Strategy
from quant_trading_system.services.strategy.signal import Signal, SignalType

logger = structlog.get_logger(__name__)


class SimpleMovingAverageStrategy(Strategy):
    """简单移动平均线策略示例"""

    def __init__(self, name: str = "SMA Strategy"):
        super().__init__(name=name)
        self.short_window = 10
        self.long_window = 30

    async def on_bar(self, bar) -> list[Signal]:
        """K线回调"""
        if not self.context:
            return []

        # 获取历史数据
        symbol = bar.symbol
        bars = self.context.bars.get(symbol, {}).get(bar.timeframe)

        if not bars or len(bars.close) < self.long_window:
            return []

        # 计算移动平均线
        short_ma = bars.close[-self.short_window:].mean()
        long_ma = bars.close[-self.long_window:].mean()

        # 生成信号
        signals = []

        if short_ma > long_ma:
            # 金叉信号
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                price=bar.close,
                volume=1.0,
                timestamp=bar.timestamp,
                reason="SMA Golden Cross"
            ))
        elif short_ma < long_ma:
            # 死叉信号
            signals.append(Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                price=bar.close,
                volume=1.0,
                timestamp=bar.timestamp,
                reason="SMA Death Cross"
            ))

        return signals


async def start_real_time_data_collection():
    """启动实时数据采集"""
    logger.info("Starting real-time data collection...")

    # 配置要采集的交易对
    config = {
        "exchanges": {
            "binance": {
                "enabled": True,
                "market_type": "spot",
                "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
            },
            "okx": {
                "enabled": True,
                "symbols": ["BTC-USDT", "ETH-USDT", "BNB-USDT"]
            }
        }
    }

    # 启动实时采集服务
    collector = await start_real_time_collection(config)

    logger.info("Real-time data collection started successfully")

    # 显示收集器状态
    stats = collector.get_collector_stats()
    for exchange, stat in stats.items():
        logger.info(f"{exchange} collector status",
                   connected=stat['connected'],
                   subscriptions=stat['subscriptions'])

    return collector


async def run_backtest_from_database():
    """从数据库获取数据进行回测"""
    logger.info("Running backtest from database...")

    # 创建回测引擎（启用数据库模式）
    backtest_config = BacktestConfig(
        initial_capital=100000.0,
        commission_rate=0.0004,
        slippage_rate=0.0001
    )

    engine = BacktestEngine(config=backtest_config, use_database=True)

    # 创建策略
    strategy = SimpleMovingAverageStrategy("SMA Backtest")

    # 设置回测参数
    symbols = ["BTC/USDT", "ETH/USDT"]
    timeframes = [TimeFrame.M5, TimeFrame.M15]

    # 设置时间范围（最近7天）
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    # 从数据库运行回测
    result = await engine.run_from_database(
        strategy=strategy,
        symbols=symbols,
        timeframes=timeframes,
        start_time=start_time,
        end_time=end_time,
        limit=10000
    )

    # 打印回测结果
    logger.info("Backtest results",
               strategy=strategy.name,
               total_return=f"{result.total_return:.2%}",
               annual_return=f"{result.annual_return:.2%}",
               max_drawdown=f"{result.max_drawdown:.2%}",
               sharpe_ratio=f"{result.sharpe_ratio:.2f}",
               total_trades=result.total_trades,
               win_rate=f"{result.win_rate:.2%}")

    return result


async def query_database_data():
    """查询数据库中的数据"""
    logger.info("Querying database for available data...")

    # 获取数据查询服务
    query_service = get_data_query_service()

    # 查询可用的交易对
    symbols = await query_service.get_available_symbols()
    logger.info("Available symbols in database", symbols=symbols)

    # 查询可用的时间框架
    timeframes = await query_service.get_available_timeframes()
    logger.info("Available timeframes in database", timeframes=timeframes)

    # 查询BTC/USDT的数据时间范围
    if symbols:
        time_range = await query_service.get_data_time_range(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M5
        )
        logger.info("BTC/USDT data time range",
                   start_time=time_range['start_time'],
                   end_time=time_range['end_time'],
                   count=time_range['count'])


async def main():
    """主函数"""
    try:
        # 1. 查询数据库中的现有数据
        await query_database_data()

        # 2. 启动实时数据采集（可选，如果不需要实时采集可以注释掉）
        # collector = await start_real_time_data_collection()

        # 3. 从数据库运行回测
        result = await run_backtest_from_database()

        # 4. 等待一段时间（如果启动了实时采集）
        # logger.info("Real-time collection running for 60 seconds...")
        # await asyncio.sleep(60)

        # 5. 停止实时采集（如果启动了）
        # await stop_real_time_collection()
        # logger.info("Real-time collection stopped")

    except Exception as e:
        logger.error("Error in main function", error=str(e))
        raise


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
