"""
交易所适配器 — 公共抽象基类
============================

定义交易所对接层的两个核心抽象：
- ExchangeGateway: 交易网关（下单/撤单/查询等 REST 操作）
- ExchangeConnector: 行情连接器（WebSocket 实时数据流）

每个具体交易所（如 Binance）在自己的子包中继承并实现这些基类。
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
)

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# 交易所网关抽象基类
# ═══════════════════════════════════════════════════════════════


class ExchangeGateway(ABC):
    """
    交易所网关抽象基类

    封装交易所下单/撤单等交易相关 REST API。
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def submit_order(self, order: Any) -> dict[str, Any]:
        """提交订单到交易所，返回交易所侧的响应"""

    @abstractmethod
    async def cancel_order(self, order: Any) -> dict[str, Any]:
        """取消订单，返回交易所侧的响应"""

    @abstractmethod
    async def query_order(self, symbol: str, order_id: str) -> dict[str, Any]:
        """查询订单状态"""

    @abstractmethod
    async def get_account(self) -> dict[str, Any]:
        """查询账户信息"""


# ═══════════════════════════════════════════════════════════════
# 交易所连接器抽象基类
# ═══════════════════════════════════════════════════════════════


class ExchangeConnector(ABC):
    """
    交易所连接器抽象基类（适配器模式 + 模板方法模式）

    职责：
    1. 管理与交易所的 WebSocket 连接
    2. 接收交易所推送的原始数据
    3. 将数据转换为统一格式
    4. 通过 MarketEventBus 发布事件

    不负责：
    - 数据存储（由 DatabaseSubscriber 处理）
    - WebSocket 前端推送（由 WebSocketSubscriber 处理）
    - 交易信号计算（由 TradingEngineSubscriber 处理）
    """

    def __init__(self, name: str, event_bus: MarketEventBus) -> None:
        self._name = name
        self._event_bus = event_bus
        self._running = False
        self._subscriptions: set[str] = set()

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def start(self) -> None:
        """启动连接器"""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """停止连接器"""
        ...

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """订阅交易对"""
        ...

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        ...

    async def _publish(
        self,
        event_type: MarketEventType,
        data: dict[str, Any],
        exchange: str = "",
        symbol: str = "",
    ) -> None:
        """便捷方法：发布事件到事件总线"""
        event = MarketEvent(
            type=event_type,
            data=data,
            exchange=exchange or self._name,
            symbol=symbol,
        )
        await self._event_bus.publish(event)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def subscriptions(self) -> set[str]:
        return self._subscriptions.copy()
