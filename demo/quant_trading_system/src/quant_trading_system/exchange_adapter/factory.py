"""
交易所工厂
==========

提供 create_connector / create_gateway 工厂函数，
根据交易所名称自动创建对应的 Connector / Gateway 实例。

新增交易所只需在 _CONNECTOR_REGISTRY / _GATEWAY_REGISTRY 中注册即可，
调用方零改动。
"""

from __future__ import annotations

from typing import Any, Callable

import structlog

from quant_trading_system.exchange_adapter.base import ExchangeConnector, ExchangeGateway
from quant_trading_system.engines.market_event_bus import MarketEventBus

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 类型别名
# ═══════════════════════════════════════════════════════════════

# Connector 工厂签名: (event_bus, **kwargs) -> ExchangeConnector
ConnectorFactory = Callable[..., ExchangeConnector]
# Gateway 工厂签名: (**kwargs) -> ExchangeGateway
GatewayFactory = Callable[..., ExchangeGateway]
# RestClient 工厂签名: (**kwargs) -> Any
RestClientFactory = Callable[..., Any]
# UserStream 工厂签名: (**kwargs) -> Any
UserStreamFactory = Callable[..., Any]


# ═══════════════════════════════════════════════════════════════
# 注册表（延迟导入，避免循环依赖）
# ═══════════════════════════════════════════════════════════════

def _create_binance_connector(event_bus: MarketEventBus, **kwargs: Any) -> ExchangeConnector:
    """创建币安行情连接器"""
    from quant_trading_system.exchange_adapter.binance.binance_connector import BinanceConnector
    return BinanceConnector(
        event_bus=event_bus,
        market_type=kwargs.get("market_type", "spot"),
        api_key=kwargs.get("api_key", ""),
        api_secret=kwargs.get("api_secret", ""),
        proxy_url=kwargs.get("proxy_url"),
    )


def _create_mock_connector(event_bus: MarketEventBus, **kwargs: Any) -> ExchangeConnector:
    """创建模拟行情连接器"""
    from quant_trading_system.exchange_adapter.mock.mock_connector import MockConnector
    return MockConnector(
        event_bus=event_bus,
        tick_interval=kwargs.get("tick_interval", 0.5),
        depth_interval=kwargs.get("depth_interval", 1.0),
        kline_intervals=kwargs.get("kline_intervals", ["1m", "5m", "15m", "1h"]),
    )


def _create_binance_gateway(**kwargs: Any) -> ExchangeGateway:
    """创建币安交易网关"""
    from quant_trading_system.exchange_adapter.binance.binance_gateway import BinanceGateway
    return BinanceGateway(
        api_key=kwargs["api_key"],
        api_secret=kwargs["api_secret"],
        market_type=kwargs.get("market_type", "spot"),
        proxy_url=kwargs.get("proxy_url"),
    )


def _create_binance_rest_client(**kwargs: Any) -> Any:
    """创建币安 REST API 客户端"""
    from quant_trading_system.exchange_adapter.binance.binance_rest_client import BinanceRestClient
    return BinanceRestClient(
        api_key=kwargs.get("api_key", ""),
        api_secret=kwargs.get("api_secret", ""),
        market_type=kwargs.get("market_type", "spot"),
        testnet=kwargs.get("testnet", False),
        proxy_url=kwargs.get("proxy_url"),
    )


def _create_mock_rest_client(**kwargs: Any) -> Any:
    """创建模拟 REST API 客户端（开发环境）"""
    from quant_trading_system.exchange_adapter.mock.mock_binance_rest_client import MockBinanceRestClient
    return MockBinanceRestClient(
        api_key=kwargs.get("api_key", "mock_key"),
        api_secret=kwargs.get("api_secret", "mock_secret"),
        account_type=kwargs.get("market_type", "spot"),
        testnet=kwargs.get("testnet", False),
    )


def _create_binance_user_stream(**kwargs: Any) -> Any:
    """创建币安 User Data Stream 管理器"""
    from quant_trading_system.exchange_adapter.binance.binance_user_stream import BinanceUserStreamManager
    return BinanceUserStreamManager(
        api_key=kwargs.get("api_key", ""),
        api_secret=kwargs.get("api_secret", ""),
        account_type=kwargs.get("account_type", "spot"),
        testnet=kwargs.get("testnet", False),
        proxy_url=kwargs.get("proxy_url"),
    )


def _create_mock_user_stream(**kwargs: Any) -> Any:
    """创建模拟 User Data Stream 管理器（开发环境）"""
    from quant_trading_system.exchange_adapter.mock.mock_binance_user_stream import MockBinanceUserStreamManager
    return MockBinanceUserStreamManager(
        api_key=kwargs.get("api_key", "mock_key"),
        api_secret=kwargs.get("api_secret", "mock_secret"),
        account_type=kwargs.get("account_type", "spot"),
        testnet=kwargs.get("testnet", False),
    )


# ── Connector 注册表 ──
_CONNECTOR_REGISTRY: dict[str, ConnectorFactory] = {
    "binance": _create_binance_connector,
    "mock": _create_mock_connector,
}

# ── Gateway 注册表 ──
_GATEWAY_REGISTRY: dict[str, GatewayFactory] = {
    "binance": _create_binance_gateway,
}

# ── RestClient 注册表 ──
_REST_CLIENT_REGISTRY: dict[str, RestClientFactory] = {
    "binance": _create_binance_rest_client,
    "mock": _create_mock_rest_client,
}

# ── UserStream 注册表 ──
_USER_STREAM_REGISTRY: dict[str, UserStreamFactory] = {
    "binance": _create_binance_user_stream,
    "mock": _create_mock_user_stream,
}


# ═══════════════════════════════════════════════════════════════
# 公共 API
# ═══════════════════════════════════════════════════════════════

def create_connector(
    exchange: str,
    event_bus: MarketEventBus,
    **kwargs: Any,
) -> ExchangeConnector:
    """
    根据交易所名称创建行情连接器

    Args:
        exchange: 交易所名称（如 "binance", "mock"）
        event_bus: 行情事件总线
        **kwargs: 交易所特定参数（market_type, api_key, api_secret 等）

    Returns:
        对应的 ExchangeConnector 实例

    Raises:
        ValueError: 不支持的交易所
    """
    factory = _CONNECTOR_REGISTRY.get(exchange)
    if factory is None:
        supported = ", ".join(sorted(_CONNECTOR_REGISTRY.keys()))
        raise ValueError(
            f"不支持的交易所: {exchange!r}，当前支持: {supported}"
        )
    return factory(event_bus, **kwargs)


def create_gateway(
    exchange: str,
    **kwargs: Any,
) -> ExchangeGateway:
    """
    根据交易所名称创建交易网关

    Args:
        exchange: 交易所名称（如 "binance"）
        **kwargs: 交易所特定参数（api_key, api_secret, market_type 等）

    Returns:
        对应的 ExchangeGateway 实例

    Raises:
        ValueError: 不支持的交易所
    """
    factory = _GATEWAY_REGISTRY.get(exchange)
    if factory is None:
        supported = ", ".join(sorted(_GATEWAY_REGISTRY.keys()))
        raise ValueError(
            f"不支持的交易所: {exchange!r}，当前支持: {supported}"
        )
    return factory(**kwargs)


def create_rest_client(
    exchange: str,
    **kwargs: Any,
) -> Any:
    """
    根据交易所名称创建 REST API 客户端

    自动处理：
    - proxy_url 注入（从 settings 读取，也可通过 kwargs 覆盖）
    - Mock 自动切换（开发环境自动使用 mock 实现）

    Args:
        exchange: 交易所名称（如 "binance"）
        **kwargs: 交易所特定参数（api_key, api_secret, market_type, testnet 等）

    Returns:
        对应的 REST API 客户端实例

    Raises:
        ValueError: 不支持的交易所
    """
    # 自动注入 proxy_url（如果调用方未显式传入）
    if "proxy_url" not in kwargs:
        from quant_trading_system.core.config import settings
        kwargs["proxy_url"] = settings.exchange.proxy_url

    # 开发环境自动切换到 mock
    resolved_exchange = exchange
    if exchange != "mock":
        from quant_trading_system.core.config import settings as _settings
        if _settings.is_development:
            resolved_exchange = "mock"
            logger.debug("开发环境，REST 客户端自动切换为 mock", original=exchange)

    factory = _REST_CLIENT_REGISTRY.get(resolved_exchange)
    if factory is None:
        supported = ", ".join(sorted(_REST_CLIENT_REGISTRY.keys()))
        raise ValueError(
            f"不支持的交易所: {exchange!r}，当前支持: {supported}"
        )
    return factory(**kwargs)


def create_user_stream(
    exchange: str,
    **kwargs: Any,
) -> Any:
    """
    根据交易所名称创建 User Data Stream 管理器

    自动处理：
    - proxy_url 注入（从 settings 读取，也可通过 kwargs 覆盖）
    - Mock 自动切换（开发环境自动使用 mock 实现）

    Args:
        exchange: 交易所名称（如 "binance"）
        **kwargs: 交易所特定参数（api_key, api_secret, account_type, testnet 等）

    Returns:
        对应的 UserStream 管理器实例

    Raises:
        ValueError: 不支持的交易所
    """
    # 自动注入 proxy_url（如果调用方未显式传入）
    if "proxy_url" not in kwargs:
        from quant_trading_system.core.config import settings
        kwargs["proxy_url"] = settings.exchange.proxy_url

    # 开发环境自动切换到 mock
    resolved_exchange = exchange
    if exchange != "mock":
        from quant_trading_system.core.config import settings as _settings
        if _settings.is_development:
            resolved_exchange = "mock"
            logger.debug("开发环境，UserStream 自动切换为 mock", original=exchange)

    factory = _USER_STREAM_REGISTRY.get(resolved_exchange)
    if factory is None:
        supported = ", ".join(sorted(_USER_STREAM_REGISTRY.keys()))
        raise ValueError(
            f"不支持的交易所: {exchange!r}，当前支持: {supported}"
        )
    return factory(**kwargs)


def register_connector(exchange: str, factory: ConnectorFactory) -> None:
    """
    注册自定义 Connector 工厂（供扩展使用）

    Args:
        exchange: 交易所名称
        factory: 工厂函数，签名 (event_bus, **kwargs) -> ExchangeConnector
    """
    _CONNECTOR_REGISTRY[exchange] = factory
    logger.info("已注册 Connector 工厂", exchange=exchange)


def register_gateway(exchange: str, factory: GatewayFactory) -> None:
    """
    注册自定义 Gateway 工厂（供扩展使用）

    Args:
        exchange: 交易所名称
        factory: 工厂函数，签名 (**kwargs) -> ExchangeGateway
    """
    _GATEWAY_REGISTRY[exchange] = factory
    logger.info("已注册 Gateway 工厂", exchange=exchange)


def register_rest_client(exchange: str, factory: RestClientFactory) -> None:
    """
    注册自定义 RestClient 工厂（供扩展使用）

    Args:
        exchange: 交易所名称
        factory: 工厂函数，签名 (**kwargs) -> RestClient
    """
    _REST_CLIENT_REGISTRY[exchange] = factory
    logger.info("已注册 RestClient 工厂", exchange=exchange)


def register_user_stream(exchange: str, factory: UserStreamFactory) -> None:
    """
    注册自定义 UserStream 工厂（供扩展使用）

    Args:
        exchange: 交易所名称
        factory: 工厂函数，签名 (**kwargs) -> UserStreamManager
    """
    _USER_STREAM_REGISTRY[exchange] = factory
    logger.info("已注册 UserStream 工厂", exchange=exchange)


def supported_connectors() -> list[str]:
    """返回当前支持的 Connector 交易所列表"""
    return sorted(_CONNECTOR_REGISTRY.keys())


def supported_gateways() -> list[str]:
    """返回当前支持的 Gateway 交易所列表"""
    return sorted(_GATEWAY_REGISTRY.keys())


def supported_rest_clients() -> list[str]:
    """返回当前支持的 RestClient 交易所列表"""
    return sorted(_REST_CLIENT_REGISTRY.keys())


def supported_user_streams() -> list[str]:
    """返回当前支持的 UserStream 交易所列表"""
    return sorted(_USER_STREAM_REGISTRY.keys())
