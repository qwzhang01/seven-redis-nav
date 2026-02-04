"""
Mock数据生成器测试
"""

import numpy as np
import pytest
from datetime import datetime

from quant_trading_system.services.market.mock_data import generate_mock_klines
from quant_trading_system.models.market import BarArray, TimeFrame


class TestGenerateMockKlines:
    """测试mock K线数据生成"""

    def test_basic_generation(self):
        """测试基本数据生成"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M15,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        assert isinstance(bars, BarArray)
        assert bars.symbol == "BTC/USDT"
        assert bars.timeframe == TimeFrame.M15
        assert len(bars) > 0

    def test_timeframe_m1(self):
        """测试1分钟时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M1,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 1天应该有1440个1分钟K线
        assert len(bars) == 1440

    def test_timeframe_m5(self):
        """测试5分钟时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M5,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 1天应该有288个5分钟K线
        assert len(bars) == 288

    def test_timeframe_m15(self):
        """测试15分钟时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M15,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 1天应该有96个15分钟K线
        assert len(bars) == 96

    def test_timeframe_m30(self):
        """测试30分钟时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M30,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 1天应该有48个30分钟K线
        assert len(bars) == 48

    def test_timeframe_h1(self):
        """测试1小时时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 1天应该有24个1小时K线
        assert len(bars) == 24

    def test_timeframe_h4(self):
        """测试4小时时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H4,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 2天应该有12个4小时K线
        assert len(bars) == 12

    def test_timeframe_d1(self):
        """测试日线时间周期"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.D1,
            start_time="2024-01-01",
            end_time="2024-01-10",
        )

        # 10天应该有10个日K线
        assert len(bars) == 10

    def test_ohlc_relationship(self):
        """测试OHLC关系"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 检查每根K线的OHLC关系
        for i in range(len(bars)):
            high = bars.high[i]
            low = bars.low[i]
            open_price = bars.open[i]
            close = bars.close[i]

            # 最高价应该 >= 开盘价和收盘价
            assert high >= open_price, f"Bar {i}: high < open"
            assert high >= close, f"Bar {i}: high < close"

            # 最低价应该 <= 开盘价和收盘价
            assert low <= open_price, f"Bar {i}: low > open"
            assert low <= close, f"Bar {i}: low > close"

    def test_volume_positive(self):
        """测试成交量为正"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 所有成交量应该为正
        assert all(bars.volume > 0)

    def test_custom_initial_price(self):
        """测试自定义初始价格"""
        initial_price = 50000.0
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
            initial_price=initial_price,
        )

        # 第一根K线的开盘价应该接近初始价格
        assert abs(bars.open[0] - initial_price) < initial_price * 0.1

    def test_custom_volatility(self):
        """测试自定义波动率"""
        # 低波动率
        bars_low = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
            volatility=0.001,
        )

        # 高波动率
        bars_high = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
            volatility=0.05,
        )

        # 高波动率的价格变化应该更大
        low_volatility = np.std(np.diff(bars_low.close))
        high_volatility = np.std(np.diff(bars_high.close))

        assert high_volatility > low_volatility

    def test_timestamp_sequence(self):
        """测试时间戳序列"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 时间戳应该是递增的
        timestamps = bars.timestamp.astype('int64')
        assert all(timestamps[i] < timestamps[i+1] for i in range(len(timestamps)-1))

    def test_timestamp_interval(self):
        """测试时间戳间隔"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )
    
        # 计算时间间隔（毫秒）
        timestamps = bars.timestamp.astype('int64')  # 已经是毫秒
        intervals = np.diff(timestamps)
    
        # 1小时 = 3600000毫秒
        expected_interval = 3600000
    
        # 所有间隔应该等于预期间隔
        assert all(intervals == expected_interval)

    def test_multiple_days(self):
        """测试多天数据生成"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-10",
        )

        # 10天，每天24小时，应该有240根K线
        assert len(bars) == 240

    def test_exchange_field(self):
        """测试交易所字段"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 交易所应该是mock
        assert bars.exchange == "mock"

    def test_turnover_calculation(self):
        """测试成交额计算"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 成交额应该大于0
        assert all(bars.turnover > 0)

        # 成交额应该接近 volume * close
        for i in range(len(bars)):
            expected_turnover = bars.volume[i] * bars.close[i]
            # 允许一定误差
            assert abs(bars.turnover[i] - expected_turnover) < expected_turnover * 0.01

    def test_reproducibility(self):
        """测试数据可重现性"""
        # 生成两次相同参数的数据
        bars1 = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        bars2 = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 两次生成的数据应该相同（因为使用了固定的随机种子）
        assert np.array_equal(bars1.close, bars2.close)
        assert np.array_equal(bars1.open, bars2.open)
        assert np.array_equal(bars1.high, bars2.high)
        assert np.array_equal(bars1.low, bars2.low)

    def test_price_trend(self):
        """测试价格趋势"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-10",
        )

        # 由于添加了上涨趋势，最后的价格应该高于初始价格
        assert bars.close[-1] > bars.close[0]

    def test_different_symbols(self):
        """测试不同交易对"""
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]

        for symbol in symbols:
            bars = generate_mock_klines(
                symbol=symbol,
                timeframe=TimeFrame.H1,
                start_time="2024-01-01",
                end_time="2024-01-02",
            )

            assert bars.symbol == symbol
            assert len(bars) > 0

    def test_edge_case_same_day(self):
        """测试边界情况：开始和结束是同一天"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.D1,
            start_time="2024-01-01",
            end_time="2024-01-01",
        )

        # 应该有1根日K线
        assert len(bars) == 1

    def test_bar_array_properties(self):
        """测试BarArray属性"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 检查所有必需的属性
        assert hasattr(bars, "symbol")
        assert hasattr(bars, "exchange")
        assert hasattr(bars, "timeframe")
        assert hasattr(bars, "timestamp")
        assert hasattr(bars, "open")
        assert hasattr(bars, "high")
        assert hasattr(bars, "low")
        assert hasattr(bars, "close")
        assert hasattr(bars, "volume")
        assert hasattr(bars, "turnover")

    def test_data_types(self):
        """测试数据类型"""
        bars = generate_mock_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.H1,
            start_time="2024-01-01",
            end_time="2024-01-02",
        )

        # 检查数据类型
        assert isinstance(bars.open, np.ndarray)
        assert isinstance(bars.high, np.ndarray)
        assert isinstance(bars.low, np.ndarray)
        assert isinstance(bars.close, np.ndarray)
        assert isinstance(bars.volume, np.ndarray)
        assert isinstance(bars.turnover, np.ndarray)
