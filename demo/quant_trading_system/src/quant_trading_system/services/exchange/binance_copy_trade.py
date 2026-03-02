"""
币安交易所跟单数据对接服务
===========================

提供对接币安交易所的订单、账户历史/实时数据接口，
用于实现交易所跟单功能（跟踪指定账户的交易操作）。

主要功能：
1. 获取目标账户的历史订单
2. 实时轮询新订单（增量同步）
3. 获取账户持仓信息
4. 获取账户资产余额
5. 将目标账户的交易操作转化为跟单信号
"""

import hashlib
import hmac
import logging
import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


class BinanceCopyTradeClient:
    """
    币安跟单数据客户端

    对接币安REST API，获取指定账户的订单和持仓数据。
    支持现货(spot)和合约(futures)两种账户类型。
    """

    # 币安API基础URL
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        account_type: str = "spot",
        testnet: bool = False,
    ):
        """
        初始化币安跟单客户端

        Args:
            api_key: 币安API Key
            api_secret: 币安API Secret
            account_type: 账户类型 spot/futures
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_type = account_type

        if testnet:
            self.base_url = "https://testnet.binance.vision" if account_type == "spot" else "https://testnet.binancefuture.com"
        else:
            self.base_url = self.SPOT_BASE_URL if account_type == "spot" else self.FUTURES_BASE_URL

        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0),
            verify=True,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    def _sign(self, params: dict) -> str:
        """生成HMAC SHA256签名"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, params: Optional[dict] = None, signed: bool = True) -> Any:
        """
        发送API请求

        Args:
            method: HTTP方法
            path: API路径
            params: 请求参数
            signed: 是否需要签名

        Returns:
            API响应数据
        """
        params = params or {}
        url = f"{self.base_url}{path}"

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._sign(params)

        headers = self._get_headers()

        try:
            if method.upper() == "GET":
                response = self._client.get(url, params=params, headers=headers)
            else:
                response = self._client.post(url, params=params, headers=headers)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"币安API请求失败: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"币安API网络错误: {e}")
            raise

    # ── 现货API ───────────────────────────────────────────────

    def get_account_info(self) -> dict[str, Any]:
        """
        获取账户信息（现货）

        返回账户余额、持仓等信息。

        Returns:
            {
                "makerCommission": 10,
                "takerCommission": 10,
                "balances": [
                    {"asset": "BTC", "free": "0.001", "locked": "0.0"},
                    {"asset": "USDT", "free": "1000.0", "locked": "0.0"}
                ]
            }
        """
        if self.account_type == "spot":
            return self._request("GET", "/api/v3/account")
        else:
            return self._request("GET", "/fapi/v2/account")

    def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        order_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        获取所有历史订单（现货）

        Args:
            symbol: 交易对，如 "BTCUSDT"
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 返回数量（最大1000）
            order_id: 从此订单ID开始查询（增量同步用）

        Returns:
            订单列表 [{orderId, symbol, side, type, price, origQty, status, time, ...}]
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "limit": min(limit, 1000),
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if order_id:
            params["orderId"] = order_id

        if self.account_type == "spot":
            return self._request("GET", "/api/v3/allOrders", params)
        else:
            return self._request("GET", "/fapi/v1/allOrders", params)

    def get_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        """
        获取当前挂单（现货）

        Args:
            symbol: 交易对（可选，不传返回所有）

        Returns:
            挂单列表
        """
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol.replace("/", "").upper()

        if self.account_type == "spot":
            return self._request("GET", "/api/v3/openOrders", params)
        else:
            return self._request("GET", "/fapi/v1/openOrders", params)

    def get_my_trades(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        from_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        获取历史成交记录

        Args:
            symbol: 交易对
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 返回数量
            from_id: 从此trade ID开始查询

        Returns:
            成交记录列表 [{id, symbol, price, qty, commission, time, isBuyer, ...}]
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "limit": min(limit, 1000),
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if from_id:
            params["fromId"] = from_id

        if self.account_type == "spot":
            return self._request("GET", "/api/v3/myTrades", params)
        else:
            return self._request("GET", "/fapi/v1/userTrades", params)

    # ── 合约API ───────────────────────────────────────────────

    def get_futures_positions(self) -> list[dict[str, Any]]:
        """
        获取合约持仓信息

        Returns:
            持仓列表 [{symbol, positionAmt, entryPrice, markPrice, unRealizedProfit, ...}]
        """
        if self.account_type != "futures":
            raise ValueError("此方法仅适用于合约账户")
        return self._request("GET", "/fapi/v2/positionRisk")

    def get_futures_income(
        self,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        获取合约账户收益流水

        Args:
            income_type: 收入类型（TRANSFER, WELCOME_BONUS, REALIZED_PNL, FUNDING_FEE, COMMISSION, INSURANCE_CLEAR 等）
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 返回数量

        Returns:
            收益流水列表
        """
        if self.account_type != "futures":
            raise ValueError("此方法仅适用于合约账户")

        params: dict[str, Any] = {"limit": min(limit, 1000)}
        if income_type:
            params["incomeType"] = income_type
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._request("GET", "/fapi/v1/income", params)

    # ── 下单接口（跟单执行用） ─────────────────────────────────

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "MARKET",
        quantity: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        price: Optional[float] = None,
        time_in_force: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        下单（跟单执行）

        Args:
            symbol: 交易对
            side: BUY/SELL
            order_type: MARKET/LIMIT
            quantity: 数量
            quote_order_qty: 报价资产数量（按金额买入）
            price: 价格（限价单必填）
            time_in_force: 有效期（限价单必填，GTC/IOC/FOK）

        Returns:
            订单信息
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "side": side.upper(),
            "type": order_type.upper(),
        }
        if quantity:
            params["quantity"] = str(quantity)
        if quote_order_qty:
            params["quoteOrderQty"] = str(quote_order_qty)
        if price and order_type.upper() == "LIMIT":
            params["price"] = str(price)
            params["timeInForce"] = time_in_force or "GTC"

        if self.account_type == "spot":
            return self._request("POST", "/api/v3/order", params)
        else:
            return self._request("POST", "/fapi/v1/order", params)

    # ── 跟单逻辑工具方法 ─────────────────────────────────────

    def sync_new_orders(
        self,
        symbol: str,
        last_order_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        增量同步新订单（跟单核心）

        从last_order_id之后拉取新订单，用于跟单同步。

        Args:
            symbol: 交易对
            last_order_id: 上次同步的最后一个订单ID

        Returns:
            新订单列表（已成交的）
        """
        order_id = int(last_order_id) if last_order_id else None
        all_orders = self.get_all_orders(symbol, order_id=order_id, limit=100)

        # 过滤已成交的订单
        filled_orders = [
            o for o in all_orders
            if o.get("status") == "FILLED" and str(o.get("orderId", "")) != str(last_order_id)
        ]

        return filled_orders

    def convert_order_to_signal(self, order: dict[str, Any]) -> dict[str, Any]:
        """
        将币安订单转化为跟单信号

        Args:
            order: 币安订单数据

        Returns:
            标准化的信号数据 {
                symbol, side, price, quantity, order_type, time, original_order_id
            }
        """
        # 提取价格：市价单使用cummulativeQuoteQty/executedQty，限价单使用price
        price = 0.0
        executed_qty = float(order.get("executedQty", 0))
        cum_quote = float(order.get("cummulativeQuoteQty", 0))

        if executed_qty > 0 and cum_quote > 0:
            price = cum_quote / executed_qty
        elif float(order.get("price", 0)) > 0:
            price = float(order["price"])

        return {
            "symbol": order.get("symbol", ""),
            "side": order.get("side", "").lower(),
            "price": price,
            "quantity": executed_qty,
            "order_type": order.get("type", "MARKET"),
            "time": datetime.fromtimestamp(order.get("time", 0) / 1000).isoformat() if order.get("time") else None,
            "original_order_id": str(order.get("orderId", "")),
            "status": order.get("status", ""),
        }

    def get_balance(self, asset: str = "USDT") -> dict[str, Any]:
        """
        获取指定资产余额

        Args:
            asset: 资产名称

        Returns:
            {free, locked, total}
        """
        account = self.get_account_info()

        if self.account_type == "spot":
            for b in account.get("balances", []):
                if b["asset"] == asset.upper():
                    free = float(b.get("free", 0))
                    locked = float(b.get("locked", 0))
                    return {"free": free, "locked": locked, "total": free + locked}
            return {"free": 0, "locked": 0, "total": 0}
        else:
            # 合约账户余额
            for a in account.get("assets", []):
                if a["asset"] == asset.upper():
                    balance = float(a.get("walletBalance", 0))
                    available = float(a.get("availableBalance", 0))
                    return {
                        "free": available,
                        "locked": balance - available,
                        "total": balance,
                    }
            return {"free": 0, "locked": 0, "total": 0}

    def get_current_price(self, symbol: str) -> float:
        """
        获取当前价格

        Args:
            symbol: 交易对

        Returns:
            当前价格
        """
        params = {"symbol": symbol.replace("/", "").upper()}
        if self.account_type == "spot":
            result = self._request("GET", "/api/v3/ticker/price", params, signed=False)
        else:
            result = self._request("GET", "/fapi/v1/ticker/price", params, signed=False)
        return float(result.get("price", 0))

    def close(self) -> None:
        """关闭HTTP客户端"""
        if hasattr(self, "_client") and self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"关闭HTTP客户端失败: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



