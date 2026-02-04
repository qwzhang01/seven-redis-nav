"""
指标测试
"""

import numpy as np
import pytest

from quant_trading_system.services.indicators import (
    SMA, EMA, MACD, RSI, KDJ, BOLL, ATR, CCI, OBV, MFI, WR,
    IndicatorEngine,
)
from quant_trading_system.models.market import BarArray, TimeFrame


class TestSMA:
    """SMA测试"""

    def test_calculate(self):
        close = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)

        sma = SMA(period=5)
        result = sma.calculate(close)

        assert "sma" in result.values
        assert len(result["sma"]) == len(close)
        # SMA(5) 的第5个值应该是 (1+2+3+4+5)/5 = 3
        assert np.isclose(result["sma"][4], 3.0)
        # SMA(5) 的第6个值应该是 (2+3+4+5+6)/5 = 4
        assert np.isclose(result["sma"][5], 4.0)

    def test_short_data(self):
        """测试数据长度小于周期的情况"""
        close = np.array([1, 2, 3], dtype=float)
        sma = SMA(period=5)
        result = sma.calculate(close)

        assert all(np.isnan(result["sma"]))


class TestEMA:
    """EMA测试"""

    def test_calculate(self):
        close = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)

        ema = EMA(period=5)
        result = ema.calculate(close)

        assert "ema" in result.values
        assert len(result["ema"]) == len(close)
        # 前4个值应该是NaN
        assert all(np.isnan(result["ema"][:4]))
        # 第5个值应该是SMA
        assert np.isclose(result["ema"][4], 3.0)

    def test_short_data(self):
        """测试数据长度小于周期的情况"""
        close = np.array([1, 2, 3], dtype=float)
        ema = EMA(period=5)
        result = ema.calculate(close)

        assert all(np.isnan(result["ema"]))


class TestMACD:
    """MACD测试"""

    def test_calculate(self):
        close = np.random.randn(100).cumsum() + 100

        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        result = macd.calculate(close)

        assert "macd" in result.values
        assert "signal" in result.values
        assert "histogram" in result.values
        assert len(result["macd"]) == len(close)
        assert len(result["signal"]) == len(close)
        assert len(result["histogram"]) == len(close)

    def test_custom_params(self):
        """测试自定义参数"""
        close = np.random.randn(100).cumsum() + 100

        macd = MACD(fast_period=5, slow_period=10, signal_period=3)
        result = macd.calculate(close)

        assert "macd" in result.values
        assert "signal" in result.values
        assert "histogram" in result.values


class TestRSI:
    """RSI测试"""

    def test_calculate(self):
        close = np.random.randn(100).cumsum() + 100

        rsi = RSI(period=14)
        result = rsi.calculate(close)

        assert "rsi" in result.values
        # RSI值应该在0-100之间
        valid_rsi = result["rsi"][~np.isnan(result["rsi"])]
        assert all(0 <= v <= 100 for v in valid_rsi)

    def test_trending_up(self):
        """测试上涨趋势中的RSI"""
        close = np.arange(1, 51, dtype=float)  # 持续上涨
        rsi = RSI(period=14)
        result = rsi.calculate(close)

        # 持续上涨时RSI应该较高
        valid_rsi = result["rsi"][~np.isnan(result["rsi"])]
        assert np.mean(valid_rsi) > 50

    def test_trending_down(self):
        """测试下跌趋势中的RSI"""
        close = np.arange(50, 0, -1, dtype=float)  # 持续下跌
        rsi = RSI(period=14)
        result = rsi.calculate(close)

        # 持续下跌时RSI应该较低
        valid_rsi = result["rsi"][~np.isnan(result["rsi"])]
        assert np.mean(valid_rsi) < 50


class TestKDJ:
    """KDJ测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 5
        low = close - np.random.rand(n) * 5

        kdj = KDJ(k_period=9, d_period=3, j_period=3)
        result = kdj.calculate(close, high=high, low=low)

        assert "k" in result.values
        assert "d" in result.values
        assert "j" in result.values
        assert len(result["k"]) == n

    def test_requires_high_low(self):
        """测试必须提供high和low"""
        close = np.random.randn(50).cumsum() + 100
        kdj = KDJ()

        with pytest.raises(ValueError, match="KDJ requires high and low prices"):
            kdj.calculate(close)


class TestBOLL:
    """布林带测试"""

    def test_calculate(self):
        close = np.random.randn(100).cumsum() + 100

        boll = BOLL(period=20, std_dev=2.0)
        result = boll.calculate(close)

        assert "middle" in result.values
        assert "upper" in result.values
        assert "lower" in result.values

        # 检查上轨 > 中轨 > 下轨
        valid_idx = ~np.isnan(result["middle"])
        assert all(result["upper"][valid_idx] >= result["middle"][valid_idx])
        assert all(result["middle"][valid_idx] >= result["lower"][valid_idx])

    def test_custom_std_dev(self):
        """测试自定义标准差"""
        close = np.random.randn(100).cumsum() + 100

        boll = BOLL(period=20, std_dev=3.0)
        result = boll.calculate(close)

        assert "upper" in result.values
        assert "lower" in result.values


class TestATR:
    """ATR测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 5
        low = close - np.random.rand(n) * 5

        atr = ATR(period=14)
        result = atr.calculate(close, high=high, low=low)

        assert "atr" in result.values
        assert len(result["atr"]) == n

        # ATR应该是正数
        valid_atr = result["atr"][~np.isnan(result["atr"])]
        assert all(valid_atr > 0)

    def test_requires_high_low(self):
        """测试必须提供high和low"""
        close = np.random.randn(50).cumsum() + 100
        atr = ATR()

        with pytest.raises(ValueError, match="ATR requires high and low prices"):
            atr.calculate(close)


class TestCCI:
    """CCI测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 5
        low = close - np.random.rand(n) * 5

        cci = CCI(period=20)
        result = cci.calculate(close, high=high, low=low)

        assert "cci" in result.values
        assert len(result["cci"]) == n

    def test_requires_high_low(self):
        """测试必须提供high和low"""
        close = np.random.randn(50).cumsum() + 100
        cci = CCI()

        with pytest.raises(ValueError, match="CCI requires high and low prices"):
            cci.calculate(close)


class TestOBV:
    """OBV测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        volume = np.random.rand(n) * 1000 + 100

        obv = OBV()
        result = obv.calculate(close, volume=volume)

        assert "obv" in result.values
        assert len(result["obv"]) == n
        # 第一个值应该等于第一个成交量
        assert result["obv"][0] == volume[0]

    def test_requires_volume(self):
        """测试必须提供volume"""
        close = np.random.randn(50).cumsum() + 100
        obv = OBV()

        with pytest.raises(ValueError, match="OBV requires volume data"):
            obv.calculate(close)

    def test_price_up_volume_up(self):
        """测试价格上涨时OBV累加"""
        close = np.array([100, 101, 102], dtype=float)
        volume = np.array([1000, 1000, 1000], dtype=float)

        obv = OBV()
        result = obv.calculate(close, volume=volume)

        # 价格持续上涨，OBV应该累加
        assert result["obv"][0] == 1000
        assert result["obv"][1] == 2000
        assert result["obv"][2] == 3000


class TestMFI:
    """MFI测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 5
        low = close - np.random.rand(n) * 5
        volume = np.random.rand(n) * 1000 + 100

        mfi = MFI(period=14)
        result = mfi.calculate(close, high=high, low=low, volume=volume)

        assert "mfi" in result.values
        assert len(result["mfi"]) == n

        # MFI值应该在0-100之间
        valid_mfi = result["mfi"][~np.isnan(result["mfi"])]
        assert all(0 <= v <= 100 for v in valid_mfi)

    def test_requires_high_low_volume(self):
        """测试必须提供high, low和volume"""
        close = np.random.randn(50).cumsum() + 100
        mfi = MFI()

        with pytest.raises(ValueError, match="MFI requires high, low and volume data"):
            mfi.calculate(close)


class TestWR:
    """威廉指标测试"""

    def test_calculate(self):
        n = 50
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 5
        low = close - np.random.rand(n) * 5

        wr = WR(period=14)
        result = wr.calculate(close, high=high, low=low)

        assert "wr" in result.values
        assert len(result["wr"]) == n

        # WR值应该在-100到0之间
        valid_wr = result["wr"][~np.isnan(result["wr"])]
        assert all(-100 <= v <= 0 for v in valid_wr)

    def test_requires_high_low(self):
        """测试必须提供high和low"""
        close = np.random.randn(50).cumsum() + 100
        wr = WR()

        with pytest.raises(ValueError, match="WR requires high and low prices"):
            wr.calculate(close)


class TestIndicatorEngine:
    """指标引擎测试"""

    def test_calculate_indicator(self):
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )

        engine = IndicatorEngine()

        result = engine.calculate("SMA", bars, period=20)
        assert result is not None
        assert "sma" in result.values

    def test_list_indicators(self):
        engine = IndicatorEngine()
        indicators = engine.list_indicators()

        assert "SMA" in indicators
        assert "EMA" in indicators
        assert "MACD" in indicators
        assert "RSI" in indicators
        assert "KDJ" in indicators
        assert "BOLL" in indicators
        assert "ATR" in indicators
        assert "CCI" in indicators
        assert "OBV" in indicators
        assert "MFI" in indicators
        assert "WR" in indicators

    def test_cache(self):
        """测试缓存功能"""
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )

        engine = IndicatorEngine()

        # 第一次计算
        result1 = engine.calculate("SMA", bars, use_cache=True, period=20)

        # 第二次计算应该使用缓存
        result2 = engine.calculate("SMA", bars, use_cache=True, period=20)

        # 结果应该相同
        assert np.array_equal(result1["sma"], result2["sma"], equal_nan=True)

        # 检查缓存命中
        stats = engine.stats
        assert stats["cache_hits"] > 0

    def test_calculate_multiple(self):
        """测试批量计算多个指标"""
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )

        engine = IndicatorEngine()

        indicators = [
            ("SMA", {"period": 20}),
            ("EMA", {"period": 20}),
            ("RSI", {"period": 14}),
        ]

        results = engine.calculate_multiple(indicators, bars)

        assert len(results) == 3
        assert "SMA" in results
        assert "EMA" in results
        assert "RSI" in results

    def test_get_latest_values(self):
        """测试获取最新值"""
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )

        engine = IndicatorEngine()

        latest = engine.get_latest_values("SMA", bars, period=20)

        assert "sma" in latest
        assert isinstance(latest["sma"], (float, type(None)))

    def test_unknown_indicator(self):
        """测试未知指标"""
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n * 60000, dtype='int64').astype('datetime64[ms]'),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )

        engine = IndicatorEngine()

        with pytest.raises(ValueError, match="Unknown indicator"):
            engine.calculate("UNKNOWN", bars)
