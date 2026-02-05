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
    
    # 对于日线及以上周期，按天生成
    if timeframe in [TimeFrame.D1, TimeFrame.W1]:
        while current_dt <= end_dt:
            timestamps.append(int(current_dt.timestamp() * 1000))
            if timeframe == TimeFrame.D1:
                current_dt += timedelta(days=1)
            else:  # W1
                current_dt += timedelta(weeks=1)
    else:
        # 对于日内周期，生成完整的天数数据
        total_days = (end_dt - start_dt).days + 1
        
        # 计算每个周期在一天内的K线数量
        if timeframe == TimeFrame.M1:
            bars_per_day = 1440
        elif timeframe == TimeFrame.M5:
            bars_per_day = 288
        elif timeframe == TimeFrame.M15:
            bars_per_day = 96
        elif timeframe == TimeFrame.M30:
            bars_per_day = 48
        elif timeframe == TimeFrame.H1:
            bars_per_day = 24
        elif timeframe == TimeFrame.H4:
            bars_per_day = 6
        else:
            bars_per_day = 24  # 默认
        
        n = total_days * bars_per_day
        
        # 生成时间戳序列
        for day in range(total_days):
            day_start = start_dt + timedelta(days=day)
            for bar_index in range(bars_per_day):
                bar_time = day_start + timedelta(seconds=bar_index * interval_seconds)
                timestamps.append(int(bar_time.timestamp() * 1000))

    n = len(timestamps)

    # 生成价格数据（使用几何布朗运动）
    # 移除固定随机种子，使用时间戳作为种子，确保每次生成不同的数据
    seed = int(datetime.now().timestamp())
    np.random.seed(seed)

    # 生成收益率，增加更大的波动率以确保产生MA交叉
    returns = np.random.normal(0, volatility * 2, n)

    # 添加更明显的趋势（先上涨后下跌，确保产生交叉）
    trend = np.zeros(n)
    mid_point = n // 2
    
    # 前半部分：上涨趋势
    trend[:mid_point] = np.linspace(0, 0.2, mid_point)  # 20%上涨
    # 后半部分：下跌趋势
    trend[mid_point:] = np.linspace(0.2, -0.1, n - mid_point)  # 下跌到-10%
    
    returns += trend / n
    
    # 添加周期性波动，确保产生更多的交叉信号
    periodic_wave = np.sin(np.linspace(0, 10 * np.pi, n)) * volatility * 0.5
    returns += periodic_wave

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
