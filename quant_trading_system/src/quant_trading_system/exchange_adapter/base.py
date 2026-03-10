"""
交易所适配器 — 公共抽象基类
============================

定义交易所对接层的核心抽象：
- ExchangeGateway: 交易网关（下单/撤单/查询等 REST 操作）
- ExchangeConnector: 行情连接器（WebSocket 实时数据流）
- ExchangeRestClient: REST API 客户端（账户/订单/持仓等查询）
- ExchangeUserStream: 用户数据流管理器（实时订单/账户事件）

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
- 交易信号计算（由 MarketDataDispatcher 处理）
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


# ═══════════════════════════════════════════════════════════════
# REST API 客户端抽象基类
# ═══════════════════════════════════════════════════════════════


class ExchangeRestClient(ABC):
    """
    交易所 REST API 客户端抽象基类

    定义统一的同步和异步 REST API 接口，包括：
    - 账户信息查询
    - 订单管理（下单/撤单/查单）
    - 成交记录查询
    - 持仓查询
    - 价格查询

    每个具体交易所实现此基类，Mock 版本也需遵循此接口。
    """

    # ── 账户信息（同步） ──

    @abstractmethod
    def get_account_info(self) -> dict[str, Any]:
        """获取账户信息"""

    @abstractmethod
    def get_balance(self, asset: str = "USDT") -> dict[str, Any]:
        """获取指定资产余额，返回 {free, locked, total}"""

    # ── 订单管理（同步） ──

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "MARKET",
        quantity: float | None = None,
        quote_order_qty: float | None = None,
        price: float | None = None,
        time_in_force: str | None = None,
    ) -> dict[str, Any]:
        """下单"""

    @abstractmethod
    def cancel_order(
        self,
        symbol: str,
        order_id: int | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """撤单"""

    @abstractmethod
    def query_order(
        self,
        symbol: str,
        order_id: int | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """查询单个订单状态"""

    @abstractmethod
    def get_all_orders(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
        order_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """获取历史订单"""

    @abstractmethod
    def get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """获取当前挂单"""

    @abstractmethod
    def get_my_trades(
        self,
        symbol: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
        from_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """获取成交记录"""

    # ── 价格查询 ──

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""

    # ── 异步接口 ──

    @abstractmethod
    async def async_place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "MARKET",
        quantity: float | None = None,
        price: float | None = None,
        time_in_force: str | None = None,
        stop_price: float | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """异步下单"""

    @abstractmethod
    async def async_cancel_order(
        self,
        symbol: str,
        order_id: int | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """异步撤单"""

    @abstractmethod
    async def async_query_order(
        self,
        symbol: str,
        order_id: int | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """异步查询订单"""

    @abstractmethod
    async def async_get_account_info(self) -> dict[str, Any]:
        """异步获取账户信息"""

    @abstractmethod
    async def async_get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """异步获取挂单"""

    @abstractmethod
    async def async_get_all_orders(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取历史订单"""

    @abstractmethod
    async def async_get_my_trades(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取成交记录"""

    @abstractmethod
    async def async_get_positions(self) -> list[dict[str, Any]]:
        """异步获取持仓"""

    # ── 资源释放 ──

    @abstractmethod
    def close(self) -> None:
        """关闭同步客户端"""

    @abstractmethod
    async def aclose(self) -> None:
        """异步关闭客户端"""


# ═══════════════════════════════════════════════════════════════
# 用户数据流管理器抽象基类
# ═══════════════════════════════════════════════════════════════


class ExchangeUserStream(ABC):
    """
    交易所用户数据流管理器抽象基类

    定义统一的用户数据流接口，包括：
    - 启动/停止 WebSocket 监听
    - 事件回调注册（订单更新、账户更新、余额更新）
    - 初始快照拉取
    - 状态查询

    每个具体交易所实现此基类，Mock 版本也需遵循此接口。
    """

    @abstractmethod
    async def start(self) -> None:
        """启动用户数据流监听"""

    @abstractmethod
    async def stop(self) -> None:
        """停止用户数据流监听"""

    @abstractmethod
    async def fetch_initial_snapshot(self) -> dict[str, Any]:
        """
        拉取初始快照

        Returns:
            快照数据字典:
            {
                "open_orders": [...],
                "positions": [...],
                "account": {...},
            }
        """

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """是否正在运行"""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """WebSocket 是否已连接"""

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """获取当前状态摘要"""
