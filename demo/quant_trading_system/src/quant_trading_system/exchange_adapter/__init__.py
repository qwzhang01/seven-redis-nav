"""
交易所适配器包
==============

将所有交易所对接代码汇总到此独立包中。
包含：

公共模块（exchange_adapter 根目录）：
- base.py: ExchangeGateway / ExchangeConnector 抽象基类
- utils.py: TimeUtils / RetryUtils 通用工具
- ws_client.py: WebSocketClient 通用 WebSocket 客户端

binance 子包：
- BinanceConfig / BinanceDataConverter / BinanceRestBase
- BinanceRestClient: REST API 统一客户端
- BinanceConnector: 行情 WebSocket 连接器
- BinanceGateway: 交易网关
- BinanceUserStreamManager: 用户数据流管理器

mock 子包：
- MockConnector / MockBinanceCopyTradeClient / MockBinanceUserStreamManager
- generate_mock_klines / generate_multi_timeframe_klines
"""

# ── 公共抽象基类 ──
from quant_trading_system.exchange_adapter.base import (
    ExchangeConnector,
    ExchangeGateway,
)

# ── 通用工具 ──
from quant_trading_system.exchange_adapter.utils import (
    RetryUtils,
    TimeUtils,
)

# ── 通用 WebSocket 客户端 ──
from quant_trading_system.exchange_adapter.ws_client import (
    ConnectionStats,
    WebSocketClient,
)

# ── 工厂函数 ──
from quant_trading_system.exchange_adapter.factory import (
    create_connector,
    create_gateway,
    register_connector,
    register_gateway,
    supported_connectors,
    supported_gateways,
)

# ── 币安对接 ──
from quant_trading_system.exchange_adapter.binance.binance_base import (
    BinanceConfig,
    BinanceDataConverter,
    BinanceRestBase,
)
from quant_trading_system.exchange_adapter.binance.binance_rest_client import BinanceRestClient
from quant_trading_system.exchange_adapter.binance.binance_connector import BinanceConnector
from quant_trading_system.exchange_adapter.binance.binance_gateway import BinanceGateway
from quant_trading_system.exchange_adapter.binance.binance_user_stream import BinanceUserStreamManager

__all__ = [
    # 公共抽象基类
    "ExchangeGateway",
    "ExchangeConnector",
    # 通用工具
    "RetryUtils",
    "TimeUtils",
    # 通用 WebSocket 客户端
    "ConnectionStats",
    "WebSocketClient",
    # 工厂函数
    "create_connector",
    "create_gateway",
    "register_connector",
    "register_gateway",
    "supported_connectors",
    "supported_gateways",
    # 币安对接
    "BinanceConfig",
    "BinanceDataConverter",
    "BinanceRestBase",
    "BinanceRestClient",
    "BinanceConnector",
    "BinanceGateway",
    "BinanceUserStreamManager",
]
