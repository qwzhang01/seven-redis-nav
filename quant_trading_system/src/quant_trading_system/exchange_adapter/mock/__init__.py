"""
Mock 模块
=========

集中管理所有交易所对接的 Mock 实现，通过配置可以自由切换是否使用 mock。
本模块提供以下 mock 功能：

- MockConnector: 模拟行情连接器（tick / kline / depth 推送）
- MockBinanceRestClient: 模拟 Binance REST API 客户端
- MockBinanceUserStreamManager: 模拟 Binance 用户数据流
- generate_mock_klines / generate_multi_timeframe_klines: 生成模拟 K线数据

使用方式：
    from quant_trading_system.exchange_adapter.mock import MockConnector, is_mock_enabled
"""

from quant_trading_system.core.config import settings
from quant_trading_system.exchange_adapter.mock.mock_binance_rest_client import (
    MockBinanceRestClient,
)
from quant_trading_system.exchange_adapter.mock.mock_binance_user_stream import (
    MockBinanceUserStreamManager,
)
from quant_trading_system.exchange_adapter.mock.mock_connector import (
    MockConnector,
    SymbolConfig,
    DEFAULT_SYMBOL_CONFIGS,
)
from quant_trading_system.exchange_adapter.mock.mock_data import (
    generate_mock_klines,
    generate_multi_timeframe_klines,
)


def is_mock_enabled() -> bool:
    """
    判断是否启用 Mock 模式。

    规则：开发环境自动启用 mock，生产环境使用真实接口。
    也可通过环境变量 USE_MOCK=true 强制启用。
    """
    return settings.is_development


__all__ = [
    "is_mock_enabled",
    # 行情连接器 Mock
    "MockConnector",
    "SymbolConfig",
    "DEFAULT_SYMBOL_CONFIGS",
    # 交易所 API Mock
    "MockBinanceRestClient",
    "MockBinanceUserStreamManager",
    # 模拟数据生成
    "generate_mock_klines",
    "generate_multi_timeframe_klines",
]
