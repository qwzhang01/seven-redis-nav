"""
指标测试
"""

import numpy as np
import pytest

from quant_trading_system.services.indicators import (
    SMA, EMA, MACD, RSI, KDJ, BOLL, ATR,
    IndicatorEngine,
)


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


class TestEMA:
    """EMA测试"""
    
    def test_calculate(self):
        close = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
        
        ema = EMA(period=5)
        result = ema.calculate(close)
        
        assert "ema" in result.values
        assert len(result["ema"]) == len(close)


class TestMACD:
    """MACD测试"""
    
    def test_calculate(self):
        close = np.random.randn(100).cumsum() + 100
        
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
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


class TestIndicatorEngine:
    """指标引擎测试"""
    
    def test_calculate_indicator(self):
        from quant_trading_system.models.market import BarArray, TimeFrame
        
        n = 100
        bars = BarArray(
            symbol="TEST",
            exchange="test",
            timeframe=TimeFrame.M1,
            timestamp=np.arange(n, dtype=float),
            open=np.random.rand(n) * 100,
            high=np.random.rand(n) * 100 + 50,
            low=np.random.rand(n) * 100 - 50,
            close=np.random.rand(n) * 100,
            volume=np.random.rand(n) * 1000,
        )
        
        engine = IndicatorEngine()
        
        result = engine.calculate("SMA", bars, period=20)
        assert result is not None
        
    def test_list_indicators(self):
        engine = IndicatorEngine()
        indicators = engine.list_indicators()
        
        assert "SMA" in indicators
        assert "EMA" in indicators
        assert "MACD" in indicators
        assert "RSI" in indicators
