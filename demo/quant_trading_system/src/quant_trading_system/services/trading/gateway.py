"""
交易所网关接口
==============

定义交易所网关的抽象接口和 Binance 实现。
"""

import asyncio
import hashlib
import hmac
import time
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


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


class BinanceGateway(ExchangeGateway):
    """
    币安交易所网关

    通过 REST API 实现下单/撤单/查单/查账户。
    需要提供 api_key 和 api_secret。

    支持 spot 和 futures。
    """

    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        market_type: str = "spot",
    ) -> None:
        super().__init__(name=f"binance-{market_type}")
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type

        if market_type == "futures":
            self.base_url = self.FUTURES_BASE_URL
        else:
            self.base_url = self.SPOT_BASE_URL

    # ------------------------------------------------------------------
    # 签名 & 请求
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, Any]) -> dict[str, Any]:
        """对参数进行 HMAC-SHA256 签名"""
        params["timestamp"] = int(time.time() * 1000)
        query = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """发送 HTTP 请求"""
        import aiohttp  # 延迟导入，避免未安装时启动报错

        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key}
        params = params or {}

        if signed:
            params = self._sign(params)

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params, headers=headers) as resp:
                    data = await resp.json()
            elif method == "POST":
                async with session.post(url, params=params, headers=headers) as resp:
                    data = await resp.json()
            elif method == "DELETE":
                async with session.delete(url, params=params, headers=headers) as resp:
                    data = await resp.json()
            else:
                raise ValueError(f"Unsupported method: {method}")

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            logger.error("Binance API error", path=path, response=data)

        return data

    # ------------------------------------------------------------------
    # 交易接口
    # ------------------------------------------------------------------

    async def submit_order(self, order: Any) -> dict[str, Any]:
        """提交订单到币安"""
        side = "BUY" if order.side.value == "BUY" else "SELL"
        order_type = order.type.value if hasattr(order.type, "value") else str(order.type)

        params: dict[str, Any] = {
            "symbol": order.symbol.replace("/", ""),
            "side": side,
            "type": order_type,
            "quantity": f"{order.quantity:.8f}",
        }

        # 限价单需要价格和 timeInForce
        if order_type == "LIMIT" and order.price:
            params["price"] = f"{order.price:.8f}"
            params["timeInForce"] = "GTC"

        if order_type in ("STOP", "STOP_LIMIT") and order.stop_price:
            params["stopPrice"] = f"{order.stop_price:.8f}"

        # 客户端订单ID
        if hasattr(order, "order_id"):
            params["newClientOrderId"] = order.order_id

        path = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"

        logger.info("Submitting order to Binance", params=params)
        return await self._request("POST", path, params)

    async def cancel_order(self, order: Any) -> dict[str, Any]:
        """取消订单"""
        symbol = order.symbol.replace("/", "")
        params: dict[str, Any] = {"symbol": symbol}

        if hasattr(order, "exchange_order_id") and order.exchange_order_id:
            params["orderId"] = order.exchange_order_id
        elif hasattr(order, "order_id"):
            params["origClientOrderId"] = order.order_id

        path = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"

        logger.info("Cancelling order on Binance", params=params)
        return await self._request("DELETE", path, params)

    async def query_order(self, symbol: str, order_id: str) -> dict[str, Any]:
        """查询订单状态"""
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", ""),
            "origClientOrderId": order_id,
        }

        path = "/api/v3/order" if self.market_type == "spot" else "/fapi/v1/order"
        return await self._request("GET", path, params)

    async def get_account(self) -> dict[str, Any]:
        """查询账户信息"""
        path = "/api/v3/account" if self.market_type == "spot" else "/fapi/v2/account"
        return await self._request("GET", path)
