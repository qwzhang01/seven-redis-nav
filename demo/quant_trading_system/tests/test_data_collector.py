import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

from quant_trading_system.services.market.data_collector import (
    WebSocketClient,
    DataCollector,
    BinanceDataCollector,
    OKXDataCollector,
    ConnectionStats
)


class TestConnectionStats:
    """连接统计测试"""
    
    def test_initialization(self):
        """测试初始化"""
        stats = ConnectionStats()
        assert stats.connect_count == 0
        assert stats.disconnect_count == 0
        assert stats.reconnect_count == 0
        assert stats.message_count == 0
        assert stats.error_count == 0
        assert stats.last_message_time == 0.0
        assert stats.latency_sum == 0.0
        assert stats.latency_count == 0
    
    def test_avg_latency_with_data(self):
        """测试平均延迟计算 - 有数据"""
        stats = ConnectionStats()
        stats.latency_sum = 100.0
        stats.latency_count = 5
        assert stats.avg_latency == 20.0
    
    def test_avg_latency_no_data(self):
        """测试平均延迟计算 - 无数据"""
        stats = ConnectionStats()
        assert stats.avg_latency == 0.0


class TestWebSocketClient:
    """WebSocket客户端测试"""
    
    @pytest.fixture
    def ws_client(self):
        """创建WebSocket客户端实例"""
        return WebSocketClient(
            url="wss://test.com/ws",
            name="test-client",
            ping_interval=30.0,
            ping_timeout=10.0,
            reconnect_delay=5.0,
            max_reconnect_attempts=3
        )
    
    def test_initialization(self, ws_client):
        """测试初始化"""
        assert ws_client.url == "wss://test.com/ws"
        assert ws_client.name == "test-client"
        assert ws_client.ping_interval == 30.0
        assert ws_client.ping_timeout == 10.0
        assert ws_client.reconnect_delay == 5.0
        assert ws_client.max_reconnect_attempts == 3
        assert not ws_client.is_connected
    
    def test_set_callbacks(self, ws_client):
        """测试回调函数设置"""
        on_message = AsyncMock()
        on_connect = AsyncMock()
        on_disconnect = AsyncMock()
        
        ws_client.set_callbacks(
            on_message=on_message,
            on_connect=on_connect,
            on_disconnect=on_disconnect
        )
        
        assert ws_client._on_message == on_message
        assert ws_client._on_connect == on_connect
        assert ws_client._on_disconnect == on_disconnect
    
    @patch("websockets.connect")
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_connect, ws_client):
        """测试成功连接"""
        mock_ws = AsyncMock()
        mock_connect.return_value = mock_ws
        
        on_connect = AsyncMock()
        ws_client.set_callbacks(on_connect=on_connect)
        
        result = await ws_client.connect()
        
        assert result is True
        assert ws_client.is_connected
        assert ws_client.stats.connect_count == 1
        mock_connect.assert_called_once()
        on_connect.assert_called_once()
    
    @patch("websockets.connect")
    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_connect, ws_client):
        """测试连接失败"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = await ws_client.connect()
        
        assert result is False
        assert not ws_client.is_connected
        assert ws_client.stats.error_count == 1
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ws_client):
        """测试断开连接"""
        ws_client._connected = True
        ws_client._running = True
        ws_client._ws = AsyncMock()
        
        on_disconnect = AsyncMock()
        ws_client.set_callbacks(on_disconnect=on_disconnect)
        
        await ws_client.disconnect()
        
        assert not ws_client.is_connected
        assert not ws_client._running
        assert ws_client.stats.disconnect_count == 1
        on_disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_when_connected(self, ws_client):
        """测试发送数据 - 已连接"""
        ws_client._connected = True
        ws_client._ws = AsyncMock()
        
        data = {"method": "test", "params": ["test"]}
        result = await ws_client.send(data)
        
        assert result is True
        ws_client._ws.send.assert_called_once_with(json.dumps(data))
    
    @pytest.mark.asyncio
    async def test_send_when_disconnected(self, ws_client):
        """测试发送数据 - 未连接"""
        ws_client._connected = False
        
        data = {"method": "test", "params": ["test"]}
        result = await ws_client.send(data)
        
        assert result is False


class TestDataCollector:
    """数据采集器基类测试"""
    
    @pytest.fixture
    def data_collector(self):
        """创建数据采集器实例"""
        class TestCollector(DataCollector):
            async def start(self):
                self._running = True
            
            async def stop(self):
                self._running = False
            
            async def subscribe(self, symbols: list[str]):
                self._subscriptions.update(symbols)
            
            async def unsubscribe(self, symbols: list[str]):
                self._subscriptions.difference_update(symbols)
        
        return TestCollector(name="test-collector")
    
    def test_initialization(self, data_collector):
        """测试初始化"""
        assert data_collector.name == "test-collector"
        assert not data_collector.is_running
        assert data_collector.subscriptions == set()
    
    @pytest.mark.asyncio
    async def test_add_and_remove_callback(self, data_collector):
        """测试添加和移除回调"""
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        
        # 添加回调
        data_collector.add_callback("tick", callback1)
        data_collector.add_callback("tick", callback2)
        
        assert len(data_collector._callbacks["tick"]) == 2
        
        # 移除回调
        data_collector.remove_callback("tick", callback1)
        assert len(data_collector._callbacks["tick"]) == 1
        assert data_collector._callbacks["tick"][0] == callback2
    
    @pytest.mark.asyncio
    async def test_notify_callbacks(self, data_collector):
        """测试通知回调"""
        callback1 = AsyncMock()
        callback2 = AsyncMock()
        
        data_collector.add_callback("tick", callback1)
        data_collector.add_callback("tick", callback2)
        
        test_data = {"symbol": "BTC/USDT", "price": 50000.0}
        await data_collector._notify("tick", test_data)
        
        callback1.assert_called_once_with(test_data)
        callback2.assert_called_once_with(test_data)
    
    @pytest.mark.asyncio
    async def test_notify_no_callbacks(self, data_collector):
        """测试无回调时的通知"""
        test_data = {"symbol": "BTC/USDT", "price": 50000.0}
        
        # 应该不会抛出异常
        await data_collector._notify("tick", test_data)


class TestBinanceDataCollector:
    """币安数据采集器测试"""
    
    @pytest.fixture
    def binance_collector(self):
        """创建币安数据采集器实例"""
        return BinanceDataCollector(
            market_type="spot",
            api_key="test_key",
            api_secret="test_secret"
        )
    
    def test_initialization(self, binance_collector):
        """测试初始化"""
        assert binance_collector.name == "binance"
        assert binance_collector.market_type == "spot"
        assert binance_collector.api_key == "test_key"
        assert binance_collector._ws_client.url == "wss://stream.binance.com:9443/ws"
    
    @patch.object(BinanceDataCollector, "_ws_client")
    @pytest.mark.asyncio
    async def test_start_and_stop(self, mock_ws_client, binance_collector):
        """测试启动和停止"""
        mock_ws_client.connect = AsyncMock()
        mock_ws_client.disconnect = AsyncMock()
        
        # 测试启动
        await binance_collector.start()
        assert binance_collector.is_running
        mock_ws_client.connect.assert_called_once()
        
        # 测试停止
        await binance_collector.stop()
        assert not binance_collector.is_running
        mock_ws_client.disconnect.assert_called_once()
    
    @patch.object(BinanceDataCollector, "_ws_client")
    @pytest.mark.asyncio
    async def test_subscribe_symbols(self, mock_ws_client, binance_collector):
        """测试订阅交易对"""
        mock_ws_client.is_connected = True
        mock_ws_client.send = AsyncMock()
        
        symbols = ["BTC/USDT", "ETH/USDT"]
        await binance_collector.subscribe(symbols)
        
        assert binance_collector.subscriptions == set(symbols)
        mock_ws_client.send.assert_called_once()
        
        # 验证订阅参数
        call_args = mock_ws_client.send.call_args[0][0]
        assert call_args["method"] == "SUBSCRIBE"
        assert "btcusdt@trade" in call_args["params"]
        assert "ethusdt@ticker" in call_args["params"]
    
    @patch.object(BinanceDataCollector, "_ws_client")
    @pytest.mark.asyncio
    async def test_unsubscribe_symbols(self, mock_ws_client, binance_collector):
        """测试取消订阅"""
        mock_ws_client.is_connected = True
        mock_ws_client.send = AsyncMock()
        
        # 先订阅
        symbols = ["BTC/USDT", "ETH/USDT"]
        binance_collector._subscriptions = set(symbols)
        
        # 取消订阅
        await binance_collector.unsubscribe(["BTC/USDT"])
        
        assert binance_collector.subscriptions == {"ETH/USDT"}
        mock_ws_client.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_trade_data(self, binance_collector):
        """测试处理成交数据"""
        mock_callback = AsyncMock()
        binance_collector.add_callback("tick", mock_callback)
        
        trade_data = {
            "e": "trade",
            "s": "BTCUSDT",
            "T": 1700000000000,
            "p": "50000.0",
            "q": "1.0",
            "t": "123456"
        }
        
        await binance_collector._process_trade(trade_data)
        
        mock_callback.assert_called_once()
        callback_data = mock_callback.call_args[0][0]
        assert callback_data["symbol"] == "BTCUSDT"
        assert callback_data["last_price"] == 50000.0
        assert callback_data["is_trade"] is True
    
    @pytest.mark.asyncio
    async def test_process_ticker_data(self, binance_collector):
        """测试处理Ticker数据"""
        mock_callback = AsyncMock()
        binance_collector.add_callback("tick", mock_callback)
        
        ticker_data = {
            "e": "24hrTicker",
            "s": "BTCUSDT",
            "E": 1700000000000,
            "c": "50000.0",
            "b": "49999.0",
            "a": "50001.0",
            "B": "1.0",
            "A": "1.0",
            "v": "1000.0",
            "q": "50000000.0"
        }
        
        await binance_collector._process_ticker(ticker_data)
        
        mock_callback.assert_called_once()
        callback_data = mock_callback.call_args[0][0]
        assert callback_data["symbol"] == "BTCUSDT"
        assert callback_data["last_price"] == 50000.0
        assert callback_data["is_trade"] is False


class TestOKXDataCollector:
    """OKX数据采集器测试"""
    
    @pytest.fixture
    def okx_collector(self):
        """创建OKX数据采集器实例"""
        return OKXDataCollector(
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_passphrase"
        )
    
    def test_initialization(self, okx_collector):
        """测试初始化"""
        assert okx_collector.name == "okx"
        assert okx_collector.api_key == "test_key"
        assert okx_collector._ws_client.url == "wss://ws.okx.com:8443/ws/v5/public"
    
    @patch.object(OKXDataCollector, "_ws_client")
    @pytest.mark.asyncio
    async def test_subscribe_symbols(self, mock_ws_client, okx_collector):
        """测试订阅交易对"""
        mock_ws_client.is_connected = True
        mock_ws_client.send = AsyncMock()
        
        symbols = ["BTC/USDT", "ETH/USDT"]
        await okx_collector.subscribe(symbols)
        
        assert okx_collector.subscriptions == set(symbols)
        mock_ws_client.send.assert_called_once()
        
        # 验证订阅参数
        call_args = mock_ws_client.send.call_args[0][0]
        assert call_args["op"] == "subscribe"
        assert len(call_args["args"]) == 6  # 2个交易对 * 3个频道