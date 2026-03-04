"""
交易所适配器包
==============

将所有交易所对接代码汇总到此独立包中，与 services 同级。
包含：
- 通用工具：TimeUtils, RetryUtils (utils.py)
- 币安基础：BinanceConfig, BinanceDataConverter, BinanceRestBase (binance_base.py)
- REST API 统一客户端：BinanceRestClient (binance_rest_client.py)
  - 同步/异步 REST 接口（账户、订单、持仓、下单、撤单、K线拉取）
- WebSocket 客户端：WebSocketClient, ConnectionStats (ws_client.py)
- 交易所连接器：ExchangeConnector(抽象), BinanceConnector (binance_connector.py)
- 交易网关：ExchangeGateway(抽象), BinanceGateway (binance_gateway.py)
  - 委托 BinanceRestClient，提供面向 Order 对象的下单/撤单接口
- 用户数据流：BinanceUserStreamManager (binance_user_stream.py)
  - WebSocket 事件流 + 委托 BinanceRestClient 拉取历史数据
- 信号流：SignalStream, SignalStreamEngine (signal_stream.py, signal_stream_engine.py)
- 跟单引擎：CopyOrderEngine (copy_order_engine.py), FollowEngine (follow_engine.py)
"""

# 通用工具
from quant_trading_system.exchange_adapter.utils import (
    RetryUtils,
    TimeUtils,
)

# 币安基础
from quant_trading_system.exchange_adapter.binance_base import (
    BinanceConfig,
    BinanceDataConverter,
    BinanceRestBase,
)

# REST API 统一客户端
from quant_trading_system.exchange_adapter.binance_rest_client import BinanceRestClient

# WebSocket 客户端
from quant_trading_system.exchange_adapter.ws_client import (
    ConnectionStats,
    WebSocketClient,
)

# 交易所连接器
from quant_trading_system.exchange_adapter.binance_connector import (
    BinanceConnector,
    ExchangeConnector,
)

# 交易网关
from quant_trading_system.exchange_adapter.binance_gateway import (
    BinanceGateway,
    ExchangeGateway,
)

# 用户数据流
from quant_trading_system.exchange_adapter.binance_user_stream import BinanceUserStreamManager

# 信号流引擎
from quant_trading_system.exchange_adapter.signal_stream_engine import SignalStreamEngine

# 跟单引擎
from quant_trading_system.exchange_adapter.copy_order_engine import CopyOrderEngine
from quant_trading_system.exchange_adapter.follow_engine import FollowEngine

__all__ = [
    # 通用工具
    "RetryUtils",
    "TimeUtils",
    # 币安基础
    "BinanceConfig",
    "BinanceDataConverter",
    "BinanceRestBase",
    # REST API 统一客户端
    "BinanceRestClient",
    # WebSocket 客户端
    "ConnectionStats",
    "WebSocketClient",
    # 交易所连接器
    "ExchangeConnector",
    "BinanceConnector",
    # 交易网关
    "ExchangeGateway",
    "BinanceGateway",
    # 用户数据流
    "BinanceUserStreamManager",
    # 信号流引擎
    "SignalStreamEngine",
    # 跟单引擎
    "CopyOrderEngine",
    "FollowEngine",
]
