import pytest
from unittest.mock import Mock, patch
import httpx
import numpy as np

from quant_trading_system.services.market.binance_api import BinanceAPI
from quant_trading_system.models.market import BarArray, TimeFrame


class TestBinanceAPI:
    """币安API测试"""
    
    @pytest.fixture
    def binance_api(self):
        """创建币安API实例"""
        return BinanceAPI(market_type="spot")
    
    @pytest.fixture
    def mock_klines_response(self):
        """模拟K线API响应"""
        return [
            [
                1700000000000,  # 时间戳
                "50000.0",      # 开盘价
                "50100.0",      # 最高价
                "49900.0",      # 最低价
                "50050.0",      # 收盘价
                "1000.0",       # 成交量
                1700003599999,  # 收盘时间
                "50050000.0",   # 成交额
                100,            # 成交笔数
                "500.0",        # 主动买入成交量
                "25000000.0",   # 主动买入成交额
                "ignore"        # 忽略字段
            ],
            [
                1700003600000,
                "50050.0",
                "50200.0",
                "50000.0",
                "50100.0",
                "1200.0",
                1700007199999,
                "60120000.0",
                120,
                "600.0",
                "30060000.0",
                "ignore"
            ]
        ]
    
    def test_init(self):
        """测试初始化"""
        api = BinanceAPI(market_type="spot")
        assert api.market_type == "spot"
        assert api.base_url == "https://api.binance.com"
        
        api = BinanceAPI(market_type="futures")
        assert api.market_type == "futures"
        assert api.base_url == "https://fapi.binance.com"
    
    def test_timeframe_mapping(self, binance_api):
        """测试时间周期映射"""
        assert binance_api.TIMEFRAME_MAP[TimeFrame.M1] == "1m"
        assert binance_api.TIMEFRAME_MAP[TimeFrame.M5] == "5m"
        assert binance_api.TIMEFRAME_MAP[TimeFrame.H1] == "1h"
        assert binance_api.TIMEFRAME_MAP[TimeFrame.D1] == "1d"
    
    def test_parse_time_valid_formats(self, binance_api):
        """测试时间解析 - 有效格式"""
        # 日期格式
        timestamp = binance_api._parse_time("2024-01-01")
        assert timestamp == 1704067200000
        
        # 日期时间格式
        timestamp = binance_api._parse_time("2024-01-01 00:00:00")
        assert timestamp == 1704067200000
    
    def test_parse_time_invalid_format(self, binance_api):
        """测试时间解析 - 无效格式"""
        with pytest.raises(ValueError):
            binance_api._parse_time("invalid-date")
    
    def test_convert_to_bar_array(self, binance_api, mock_klines_response):
        """测试K线数据转换"""
        bar_array = binance_api._convert_to_bar_array(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M1,
            klines=mock_klines_response
        )
        
        assert isinstance(bar_array, BarArray)
        assert bar_array.symbol == "BTC/USDT"
        assert bar_array.exchange == "binance"
        assert bar_array.timeframe == TimeFrame.M1
        assert len(bar_array) == 2
        
        # 检查数据正确性
        assert bar_array.open[0] == 50000.0
        assert bar_array.high[0] == 50100.0
        assert bar_array.low[0] == 49900.0
        assert bar_array.close[0] == 50050.0
        assert bar_array.volume[0] == 1000.0
        assert bar_array.turnover[0] == 50050000.0
    
    def test_convert_to_bar_array_empty(self, binance_api):
        """测试空K线数据转换"""
        bar_array = binance_api._convert_to_bar_array(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M1,
            klines=[]
        )
        
        assert isinstance(bar_array, BarArray)
        assert len(bar_array) == 0
        assert bar_array.symbol == "BTC/USDT"
    
    @patch("httpx.Client.get")
    def test_fetch_klines_success(self, mock_get, binance_api, mock_klines_response):
        """测试成功获取K线数据"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_klines_response
        mock_get.return_value = mock_response
        
        bar_array = binance_api.fetch_klines(
            symbol="BTC/USDT",
            timeframe=TimeFrame.M1,
            start_time="2024-01-01",
            end_time="2024-01-02",
            limit=100
        )
        
        assert isinstance(bar_array, BarArray)
        assert len(bar_array) == 2
        
        # 验证API调用参数
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "api/v3/klines" in call_args[0][0]
        assert call_args[1]["params"]["symbol"] == "BTCUSDT"
        assert call_args[1]["params"]["interval"] == "1m"
    
    @patch("httpx.Client.get")
    def test_fetch_klines_retry_on_connection_error(self, mock_get, binance_api):
        """测试连接错误重试"""
        # 模拟连接错误
        mock_get.side_effect = httpx.ConnectError("Connection failed")
        
        with pytest.raises(httpx.ConnectError):
            binance_api.fetch_klines(
                symbol="BTC/USDT",
                timeframe=TimeFrame.M1
            )
        
        # 验证重试次数
        assert mock_get.call_count == 3
    
    @patch("httpx.Client.get")
    def test_fetch_klines_http_error(self, mock_get, binance_api):
        """测试HTTP错误"""
        # 模拟HTTP错误
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response
        
        with pytest.raises(httpx.HTTPStatusError):
            binance_api.fetch_klines(
                symbol="BTC/USDT",
                timeframe=TimeFrame.M1
            )
    
    def test_fetch_klines_unsupported_timeframe(self, binance_api):
        """测试不支持的时间周期"""
        with pytest.raises(ValueError):
            binance_api.fetch_klines(
                symbol="BTC/USDT",
                timeframe=TimeFrame.W1  # 假设W1不在映射中
            )
    
    def test_symbol_formatting(self, binance_api):
        """测试交易对格式化"""
        # 测试fetch_klines中的符号格式化
        with patch.object(binance_api, '_client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_client.get.return_value = mock_response
            
            binance_api.fetch_klines(
                symbol="BTC/USDT",
                timeframe=TimeFrame.M1
            )
            
            # 验证符号被正确格式化
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["symbol"] == "BTCUSDT"
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with BinanceAPI(market_type="spot") as api:
            assert api._client is not None
        
        # 客户端应该被关闭
        assert api._client.is_closed
    
    def test_close_method(self, binance_api):
        """测试关闭方法"""
        binance_api.close()
        assert binance_api._client.is_closed