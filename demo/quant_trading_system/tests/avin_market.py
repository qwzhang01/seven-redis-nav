from quant_trading_system.services.market.data_collector import BinanceDataCollector

from quant_trading_system.services.market.binance_api import BinanceAPI
from quant_trading_system.models.market import TimeFrame

import numpy as np
from quant_trading_system.services.market.binance_api import BinanceAPI
from quant_trading_system.models.market import TimeFrame

# 创建币安API实例（现货市场）
with BinanceAPI(market_type="spot") as api:
    # 获取BTC/USDT的1分钟K线数据
    bars = api.fetch_klines(
        symbol="BTC/USDT",           # 交易对
        timeframe=TimeFrame.M1,      # 时间周期
        start_time="2024-01-01",     # 开始时间
        end_time="2024-01-02",       # 结束时间
        limit=1000                   # 每次请求数量（最大1000）
    )
    
    print(f"获取到 {len(bars)} 根K线")
    print(f"第一根K线: 开盘={bars.open[0]}, 收盘={bars.close[0]}")

def fetch_and_analyze_binance_data():
    """获取并分析币安数据"""
    
    # 1. 创建API实例
    with BinanceAPI(market_type="spot") as api:
        
        # 2. 获取K线数据
        bars = api.fetch_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01 00:00:00",
            end_time="2024-01-02 00:00:00",
            limit=1000
        )
        
        # 3. 数据分析
        print(f"数据统计:")
        print(f"  时间段: {bars.timestamp[0]} 到 {bars.timestamp[-1]}")
        print(f"  K线数量: {len(bars)}")
        print(f"  价格范围: {bars.low.min():.2f} - {bars.high.max():.2f}")
        print(f"  平均成交量: {bars.volume.mean():.2f}")
        print(f"  总成交额: {bars.turnover.sum():.2f}")
        
        # 4. 计算简单指标
        returns = np.diff(bars.close) / bars.close[:-1]
        volatility = returns.std() * np.sqrt(24 * 365)  # 年化波动率
        
        print(f"  年化波动率: {volatility:.2%}")
        
        return bars



# 创建实时数据采集器
collector = BinanceDataCollector(
    market_type="spot",
    api_key="your_api_key",      # 可选
    api_secret="your_secret"     # 可选
)

# 启动采集
# await collector.start()

# 运行示例
if __name__ == "__main__":
    data = fetch_and_analyze_binance_data()