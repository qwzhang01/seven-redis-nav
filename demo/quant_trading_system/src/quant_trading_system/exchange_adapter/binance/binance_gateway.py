"""
币安交易所网关
==============

BinanceGateway 委托 BinanceRestClient 执行实际的 REST 请求，避免重复实现。
"""

from typing import Any

import structlog

from quant_trading_system.exchange_adapter.base import ExchangeGateway
from quant_trading_system.exchange_adapter.binance.binance_rest_client import BinanceRestClient

logger = structlog.get_logger(__name__)


class BinanceGateway(ExchangeGateway):
    """
    币安交易所网关

    通过委托 BinanceRestClient 实现下单/撤单/查单/查账户。
    需要提供 api_key 和 api_secret。

    支持 spot 和 futures。
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        market_type: str = "spot",
    ) -> None:
        super().__init__(name=f"binance-{market_type}")
        self._client = BinanceRestClient(
            api_key=api_key,
            api_secret=api_secret,
            market_type=market_type,
        )

    # ------------------------------------------------------------------
    # 交易接口（委托 BinanceRestClient 的异步方法）
    # ------------------------------------------------------------------

    async def submit_order(self, order: Any) -> dict[str, Any]:
        """提交订单到币安"""
        side = "BUY" if order.side.value == "BUY" else "SELL"
        order_type = order.type.value if hasattr(order.type, "value") else str(order.type)

        logger.info(
            "Submitting order to Binance",
            symbol=order.symbol,
            side=side,
            type=order_type,
            quantity=order.quantity,
        )

        return await self._client.async_place_order(
            symbol=order.symbol,
            side=side,
            order_type=order_type,
            quantity=order.quantity,
            price=order.price if hasattr(order, "price") else None,
            stop_price=order.stop_price if hasattr(order, "stop_price") and order.stop_price else None,
            client_order_id=order.order_id if hasattr(order, "order_id") else None,
        )

    async def cancel_order(self, order: Any) -> dict[str, Any]:
        """取消订单"""
        symbol = order.symbol.replace("/", "")

        order_id = None
        client_order_id = None
        if hasattr(order, "exchange_order_id") and order.exchange_order_id:
            order_id = int(order.exchange_order_id)
        elif hasattr(order, "order_id"):
            client_order_id = order.order_id

        logger.info("Cancelling order on Binance", symbol=symbol)

        return await self._client.async_cancel_order(
            symbol=symbol,
            order_id=order_id,
            client_order_id=client_order_id,
        )

    async def query_order(self, symbol: str, order_id: str) -> dict[str, Any]:
        """查询订单状态"""
        return await self._client.async_query_order(
            symbol=symbol,
            client_order_id=order_id,
        )

    async def get_account(self) -> dict[str, Any]:
        """查询账户信息"""
        return await self._client.async_get_account_info()

    def close(self) -> None:
        """关闭底层 REST 客户端"""
        self._client.close()
