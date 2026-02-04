"""
模拟数据生成器
==============

用于生成模拟的K线数据，用于测试和演示
"""

from datetime import datetime, timedelta

import numpy as np

from quant_trading_system.models.market import BarArray, TimeFrame


def generate_mock_klines(
    symbol: str,
    timeframe: TimeFrame,
    start_time: str,
    end_time: str,
    initial_price: float = 40000.0,
    volatility: float = 0.02,
) -> BarArray:
    """
    生成模拟K线数据

    Args:
        symbol: 交易对
        timeframe: 时间周期
        start_time: 开始时间 "YYYY-MM-DD"
        end_time: 结束时间 "YYYY-MM-DD"
        initial_price: 初始价格
        volatility: 波动率

    Returns:
        K线数组
    """
    # 解析时间
    start_dt = datetime.strptime(start_time, "%Y-%m-%d")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d")

    # TimeFrame到秒数的映射
    timeframe_seconds = {
        TimeFrame.M1: 60,
        TimeFrame.M5: 300,
        TimeFrame.M15: 900,
        TimeFrame.M30: 1800,
        TimeFrame.H1: 3600,
        TimeFrame.H4: 14400,
        TimeFrame.D1: 86400,
        TimeFrame.W1: 604800,
    }

    # 计算时间间隔（秒）
    interval_seconds = timeframe_seconds.get(timeframe, 3600)

    # 生成时间序列
    timestamps = []
    current_dt = start_dt
    while current_dt <= end_dt:
        timestamps.append(int(current_dt.timestamp() * 1000))
        current_dt += timedelta(seconds=interval_seconds)

    n = len(timestamps)

    # 生成价格数据（使用几何布朗运动）
    np.random.seed(42)  # 固定随机种子以便复现

    # 生成收益率
    returns = np.random.normal(0, volatility, n)

    # 添加趋势
    trend = np.linspace(0, 0.1, n)  # 10%的上涨趋势
    returns += trend / n

    # 计算价格
    prices = initial_price * np.exp(np.cumsum(returns))

    # 生成OHLC
    opens = prices.copy()
    closes = prices * (1 + np.random.normal(0, volatility/2, n))

    # 生成高低价
    highs = np.maximum(opens, closes) * (1 + np.abs(np.random.normal(0, volatility/4, n)))
    lows = np.minimum(opens, closes) * (1 - np.abs(np.random.normal(0, volatility/4, n)))

    # 生成成交量
    base_volume = 100.0
    volumes = base_volume * (1 + np.random.normal(0, 0.5, n))
    volumes = np.abs(volumes)

    # 计算成交额
    turnovers = volumes * closes

    return BarArray(
        symbol=symbol,
        exchange="mock",
        timeframe=timeframe,
        timestamp=np.array(timestamps, dtype="datetime64[ms]"),
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        volume=volumes,
        turnover=turnovers,
    )
