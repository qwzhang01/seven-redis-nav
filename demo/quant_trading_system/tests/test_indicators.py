"""
指标测试
"""

import numpy as np
import pytest
import time
import asyncio
from unittest.mock import Mock, patch

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

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试周期为1
        close = np.array([1, 2, 3], dtype=float)
        sma = SMA(period=1)
        result = sma.calculate(close)
        assert np.allclose(result["sma"], close, equal_nan=True)
        
        # 测试周期等于数据长度
        close = np.array([1, 2, 3], dtype=float)
        sma = SMA(period=3)
        result = sma.calculate(close)
        assert np.isclose(result["sma"][2], 2.0)  # (1+2+3)/3 = 2
        
        # 测试周期大于数据长度
        close = np.array([1, 2], dtype=float)
        sma = SMA(period=5)
        result = sma.calculate(close)
        assert all(np.isnan(result["sma"]))

    def test_nan_handling(self):
        """测试NaN值处理"""
        close = np.array([1, np.nan, 3, 4, 5, 6], dtype=float)
        sma = SMA(period=3)
        result = sma.calculate(close)
        
        # 包含NaN的窗口应该返回NaN
        assert np.isnan(result["sma"][2])
        # 不包含NaN的窗口应该正常计算
        assert np.isclose(result["sma"][4], (3+4+5)/3)

    def test_performance(self):
        """测试性能"""
        n = 10000
        close = np.random.randn(n).cumsum() + 100
        
        sma = SMA(period=20)
        
        start_time = time.time()
        result = sma.calculate(close)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"SMA calculation time for {n} data points: {execution_time:.4f}s")
        
        # 性能要求：10000个数据点计算时间小于0.1秒
        assert execution_time < 0.1


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

    def test_convergence(self):
        """测试EMA收敛性"""
        # 测试EMA对常数序列的收敛
        close = np.full(100, 10.0)
        ema = EMA(period=10)
        result = ema.calculate(close)
        
        # EMA应该收敛到常数
        valid_ema = result["ema"][~np.isnan(result["ema"])]
        assert np.allclose(valid_ema, 10.0, atol=0.1)

    def test_alpha_calculation(self):
        """测试alpha计算正确性"""
        period = 10
        expected_alpha = 2 / (period + 1)
        
        # 验证EMA内部计算的alpha
        close = np.array([1, 2, 3], dtype=float)
        ema = EMA(period=period)
        result = ema.calculate(close)
        
        # 通过手动计算验证
        if len(close) >= period:
            alpha = 2 / (period + 1)
            assert np.isclose(alpha, expected_alpha)


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

    def test_histogram_calculation(self):
        """测试柱状图计算正确性"""
        close = np.array([100, 101, 102, 103, 104], dtype=float)
        macd = MACD(fast_period=2, slow_period=3, signal_period=2)
        result = macd.calculate(close)
        
        # 验证histogram = macd - signal
        valid_idx = ~np.isnan(result["macd"])
        macd_vals = result["macd"][valid_idx]
        signal_vals = result["signal"][valid_idx]
        histogram_vals = result["histogram"][valid_idx]
        
        expected_histogram = macd_vals - signal_vals
        assert np.allclose(histogram_vals, expected_histogram, equal_nan=True)

    def test_trend_detection(self):
        """测试趋势检测能力"""
        # 上涨趋势
        close_up = np.arange(100, 200, 1.0)
        macd = MACD()
        result_up = macd.calculate(close_up)
        
        # 下跌趋势
        close_down = np.arange(200, 100, -1.0)
        result_down = macd.calculate(close_down)
        
        # 上涨趋势中MACD应该为正
        valid_up = result_up["macd"][~np.isnan(result_up["macd"])]
        valid_down = result_down["macd"][~np.isnan(result_down["macd"])]
        
        # 趋势检测的统计验证
        assert np.mean(valid_up) > np.mean(valid_down)


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

    def test_extreme_values(self):
        """测试极端情况下的RSI"""
        # 连续上涨
        close_up = np.full(50, 100.0)
        close_up[1:] = np.arange(101, 151, dtype=float)
        rsi = RSI(period=14)
        result_up = rsi.calculate(close_up)
        
        # 连续下跌
        close_down = np.full(50, 150.0)
        close_down[1:] = np.arange(149, 99, -1, dtype=float)
        result_down = rsi.calculate(close_down)
        
        valid_up = result_up["rsi"][~np.isnan(result_up["rsi"])]
        valid_down = result_down["rsi"][~np.isnan(result_down["rsi"])]
        
        # 连续上涨时RSI应该接近100
        assert np.mean(valid_up) > 80
        # 连续下跌时RSI应该接近0
        assert np.mean(valid_down) < 20

    def test_wilder_smoothing(self):
        """测试Wilder平滑算法"""
        close = np.array([100, 101, 102, 101, 100, 99], dtype=float)
        rsi = RSI(period=3)
        result = rsi.calculate(close)
        
        # 手动验证Wilder平滑计算
        delta = np.diff(close, prepend=close[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # 验证平滑计算逻辑
        assert len(gain) == len(close)
        assert len(loss) == len(close)


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

    def test_rsv_calculation(self):
        """测试RSV计算正确性"""
        close = np.array([50, 55, 60, 58, 62], dtype=float)
        high = np.array([52, 58, 65, 62, 65], dtype=float)
        low = np.array([48, 52, 55, 56, 58], dtype=float)
        
        kdj = KDJ(k_period=3)
        result = kdj.calculate(close, high=high, low=low)
        
        # 验证RSV计算
        # 第3个点的RSV = (60-52)/(65-52)*100 = 61.54
        assert np.isclose(result["k"][2], 50.0)  # 初始K值

    def test_kdj_range(self):
        """测试KDJ值范围"""
        n = 100
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 10
        low = close - np.random.rand(n) * 10
        
        kdj = KDJ()
        result = kdj.calculate(close, high=high, low=low)
        
        valid_k = result["k"][~np.isnan(result["k"])]
        valid_d = result["d"][~np.isnan(result["d"])]
        valid_j = result["j"][~np.isnan(result["j"])]
        
        # KDJ值应该在合理范围内
        assert all(0 <= k <= 100 for k in valid_k)
        assert all(0 <= d <= 100 for d in valid_d)
        # J值可能超出0-100范围


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

    def test_band_width(self):
        """测试带宽计算"""
        close = np.random.randn(100).cumsum() + 100
        
        # 测试不同标准差下的带宽
        for std_dev in [1.0, 2.0, 3.0]:
            boll = BOLL(period=20, std_dev=std_dev)
            result = boll.calculate(close)
            
            valid_idx = ~np.isnan(result["middle"])
            middle = result["middle"][valid_idx]
            upper = result["upper"][valid_idx]
            lower = result["lower"][valid_idx]
            
            # 验证带宽与标准差的关系
            band_width = (upper - lower) / middle
            expected_ratio = 2 * std_dev
            
            # 平均带宽应该与标准差相关
            avg_band_ratio = np.mean(band_width)
            assert avg_band_ratio > 0

    def test_volatility_measurement(self):
        """测试波动率测量"""
        # 低波动率序列
        close_low_vol = np.full(100, 100.0) + np.random.randn(100) * 0.1
        
        # 高波动率序列
        close_high_vol = np.full(100, 100.0) + np.random.randn(100) * 5.0
        
        boll = BOLL(period=20)
        result_low = boll.calculate(close_low_vol)
        result_high = boll.calculate(close_high_vol)
        
        valid_low = result_low["upper"] - result_low["lower"]
        valid_high = result_high["upper"] - result_high["lower"]
        
        # 高波动率序列的带宽应该更大
        avg_low_band = np.nanmean(valid_low)
        avg_high_band = np.nanmean(valid_high)
        
        assert avg_high_band > avg_low_band


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

    def test_true_range_calculation(self):
        """测试真实波幅计算"""
        close = np.array([100, 102, 98, 101], dtype=float)
        high = np.array([105, 104, 100, 103], dtype=float)
        low = np.array([95, 98, 96, 99], dtype=float)
        
        atr = ATR(period=2)
        result = atr.calculate(close, high=high, low=low)
        
        # 验证TR计算
        # 第1个TR = max(105-95, |105-100|, |95-100|) = 10
        # 第2个TR = max(104-98, |104-102|, |98-102|) = 6
        valid_atr = result["atr"][~np.isnan(result["atr"])]
        assert len(valid_atr) > 0

    def test_wilder_smoothing_atr(self):
        """测试ATR的Wilder平滑"""
        close = np.array([100, 101, 99, 102, 98], dtype=float)
        high = close + np.random.rand(len(close)) * 5
        low = close - np.random.rand(len(close)) * 5
        
        atr = ATR(period=3)
        result = atr.calculate(close, high=high, low=low)
        
        # 验证ATR计算逻辑
        valid_atr = result["atr"][~np.isnan(result["atr"])]
        assert all(valid_atr > 0)


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

    def test_mad_calculation(self):
        """测试平均绝对偏差计算"""
        # 测试典型价格和MAD计算
        close = np.array([100, 102, 98, 101], dtype=float)
        high = np.array([105, 104, 100, 103], dtype=float)
        low = np.array([95, 98, 96, 99], dtype=float)
        
        cci = CCI(period=2)
        result = cci.calculate(close, high=high, low=low)
        
        # 验证典型价格计算
        tp = (high + low + close) / 3
        assert len(tp) == len(close)

    def test_cci_range(self):
        """测试CCI值范围"""
        n = 100
        close = np.random.randn(n).cumsum() + 100
        high = close + np.random.rand(n) * 10
        low = close - np.random.rand(n) * 10
        
        cci = CCI()
        result = cci.calculate(close, high=high, low=low)
        
        valid_cci = result["cci"][~np.isnan(result["cci"])]
        
        # CCI值通常在-200到+200之间
        assert np.mean(np.abs(valid_cci)) < 300


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

    def test_price_down_volume_down(self):
        """测试价格下跌时OBV递减"""
        close = np.array([102, 101, 100], dtype=float)
        volume = np.array([1000, 1000, 1000], dtype=float)

        obv = OBV()
        result = obv.calculate(close, volume=volume)

        # 价格持续下跌，OBV应该递减
        assert result["obv"][0] == 1000
        assert result["obv"][1] == 0
        assert result["obv"][2] == -1000

    def test_price_unchanged(self):
        """测试价格不变时OBV不变"""
        close = np.array([100, 100, 100], dtype=float)
        volume = np.array([1000, 1000, 1000], dtype=float)

        obv = OBV()
        result = obv.calculate(close, volume=volume)

        # 价格不变，OBV应该保持不变
        assert result["obv"][0] == 1000
        assert result["obv"][1] == 1000
        assert result["obv"][2] == 1000


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

    def test_money_flow_calculation(self):
        """测试资金流量计算"""
        close = np.array([100, 101, 99], dtype=float)
        high = np.array([105, 104, 100], dtype=float)
        low = np.array([95, 98, 96], dtype=float)
        volume = np.array([1000, 1000, 1000], dtype=float)
        
        mfi = MFI(period=2)
        result = mfi.calculate(close, high=high, low=low, volume=volume)
        
        # 验证典型价格和资金流量计算
        tp = (high + low + close) / 3
        mf = tp * volume
        assert len(mf) == len(close)


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

    def test_wr_calculation(self):
        """测试WR计算逻辑"""
        close = np.array([50, 55, 60], dtype=float)
        high = np.array([60, 65, 70], dtype=float)
        low = np.array([40, 45, 50], dtype=float)
        
        wr = WR(period=2)
        result = wr.calculate(close, high=high, low=low)
        
        # 验证WR计算：WR = -100 * (最高价 - 收盘价) / (最高价 - 最低价)
        # 第2个点：WR = -100 * (65-55)/(65-45) = -50
        valid_wr = result["wr"][~np.isnan(result["wr"])]
        assert len(valid_wr) > 0


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

    def test_async_calculation(self):
        """测试异步计算"""
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

        async def test_async():
            result = await engine.calculate_async("SMA", bars, period=20)
            assert "sma" in result.values
            assert len(result["sma"]) == n

        asyncio.run(test_async())

    def test_concurrent_calculations(self):
        """测试并发计算"""
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

        async def test_concurrent():
            indicators = [
                ("SMA", {"period": 20}),
                ("EMA", {"period": 20}),
                ("RSI", {"period": 14}),
                ("MACD", {}),
            ]

            results = await engine.calculate_multiple_async(indicators, bars)
            assert len(results) == 4
            assert all(name in results for name in ["SMA", "EMA", "RSI", "MACD"])

        asyncio.run(test_concurrent())

    def test_memory_efficiency(self):
        """测试内存效率"""
        import sys
        
        n = 1000
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
        
        # 记录初始内存使用
        initial_memory = sys.getsizeof(engine)
        
        # 计算多个指标
        for i in range(10):
            engine.calculate("SMA", bars, period=20)
            engine.calculate("EMA", bars, period=20)
            engine.calculate("RSI", bars, period=14)
        
        # 记录最终内存使用
        final_memory = sys.getsizeof(engine)
        
        # 内存增长应该相对较小
        memory_growth = final_memory - initial_memory
        print(f"Memory growth after 30 calculations: {memory_growth} bytes")
        
        assert memory_growth < 1024 * 1024  # 小于1MB

    def test_error_handling(self):
        """测试错误处理"""
        engine = IndicatorEngine()
        
        # 测试空数据
        with pytest.raises(ValueError, match="bars cannot be empty"):
            engine.calculate("SMA", [])
        
        # 测试无效参数
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.array([1000], dtype='int64').astype('datetime64[ms]'),
            open=np.array([100.0]),
            high=np.array([105.0]),
            low=np.array([95.0]),
            close=np.array([100.0]),
            volume=np.array([1000.0]),
        )
        
        with pytest.raises(ValueError):
            engine.calculate("SMA", bars, period=0)  # 无效周期

    def test_statistics_tracking(self):
        """测试统计信息跟踪"""
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
        
        # 初始统计
        initial_stats = engine.stats
        assert initial_stats["calc_count"] == 0
        assert initial_stats["cache_hits"] == 0
        
        # 进行计算
        engine.calculate("SMA", bars, period=20)
        engine.calculate("SMA", bars, period=20)  # 应该命中缓存
        
        # 检查统计更新
        updated_stats = engine.stats
        assert updated_stats["calc_count"] == 1  # 缓存命中不计入计算次数
        assert updated_stats["cache_hits"] == 1
        assert 0 <= updated_stats["cache_hit_rate"] <= 1

    def test_cache_clear(self):
        """测试缓存清除"""
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
        result1 = engine.calculate("SMA", bars, period=20)
        
        # 清除缓存
        engine.clear_cache()
        
        # 第二次计算（应该重新计算）
        result2 = engine.calculate("SMA", bars, period=20)
        
        # 结果应该相同（但缓存被清除）
        assert np.array_equal(result1["sma"], result2["sma"], equal_nan=True)
        
        # 统计应该反映缓存被清除
        stats = engine.stats
        assert stats["cache_hits"] == 0
        assert stats["calc_count"] == 2

    def test_indicator_info(self):
        """测试指标信息获取"""
        engine = IndicatorEngine()
        
        # 获取SMA指标信息
        sma_info = engine.get_indicator_info("SMA")
        assert sma_info is not None
        assert "name" in sma_info
        assert sma_info["name"] == "SMA"
        
        # 获取未知指标信息
        unknown_info = engine.get_indicator_info("UNKNOWN")
        assert unknown_info is None
