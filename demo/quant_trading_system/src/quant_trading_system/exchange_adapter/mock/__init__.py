"""
Mock 模块
=========

集中管理所有交易所对接的 Mock 实现，通过配置可以自由切换是否使用 mock。
本模块提供以下 mock 功能：

- MockConnector: 模拟行情连接器（tick / kline / depth 推送）
- MockBinanceCopyTradeClient: 模拟 Binance 跟单 API
- MockBinanceUserStreamManager: 模拟 Binance 用户数据流
- generate_mock_klines / generate_multi_timeframe_klines: 生成模拟 K线数据

使用方式：
    from quant_trading_system.exchange_adapter.mock import MockConnector, is_mock_enabled
"""

from quant_trading_system.core.config import settings


def is_mock_enabled() -> bool:
    """
    判断是否启用 Mock 模式。

    规则：开发环境自动启用 mock，生产环境使用真实接口。
    也可通过环境变量 USE_MOCK=true 强制启用。
    """
    return settings.is_development


# ── 延迟导入，避免循环依赖 ──

_LAZY_IMPORTS = {
    "MockConnector":                ("quant_trading_system.exchange_adapter.mock.mock_connector", "MockConnector"),
    "SymbolConfig":                 ("quant_trading_system.exchange_adapter.mock.mock_connector", "SymbolConfig"),
    "DEFAULT_SYMBOL_CONFIGS":       ("quant_trading_system.exchange_adapter.mock.mock_connector", "DEFAULT_SYMBOL_CONFIGS"),
    "MockBinanceCopyTradeClient":   ("quant_trading_system.exchange_adapter.mock.mock_binance_copy_trade", "MockBinanceCopyTradeClient"),
    "MockBinanceUserStreamManager": ("quant_trading_system.exchange_adapter.mock.mock_binance_user_stream", "MockBinanceUserStreamManager"),
    "generate_mock_klines":         ("quant_trading_system.exchange_adapter.mock.mock_data", "generate_mock_klines"),
    "generate_multi_timeframe_klines": ("quant_trading_system.exchange_adapter.mock.mock_data", "generate_multi_timeframe_klines"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "is_mock_enabled",
    # 行情连接器 Mock
    "MockConnector",
    "SymbolConfig",
    "DEFAULT_SYMBOL_CONFIGS",
    # 交易所 API Mock
    "MockBinanceCopyTradeClient",
    "MockBinanceUserStreamManager",
    # 模拟数据生成
    "generate_mock_klines",
    "generate_multi_timeframe_klines",
]
