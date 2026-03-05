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


# ── Connector 注册表 ──
_CONNECTOR_REGISTRY: dict[str, ConnectorFactory] = {
    "binance": _create_binance_connector,
    "mock": _create_mock_connector,
}

# ── Gateway 注册表 ──
_GATEWAY_REGISTRY: dict[str, GatewayFactory] = {
    "binance": _create_binance_gateway,
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


def supported_connectors() -> list[str]:
    """返回当前支持的 Connector 交易所列表"""
    return sorted(_CONNECTOR_REGISTRY.keys())


def supported_gateways() -> list[str]:
    """返回当前支持的 Gateway 交易所列表"""
    return sorted(_GATEWAY_REGISTRY.keys())
