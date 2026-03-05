"""
币安 REST API 统一客户端
========================

合并原 BinanceAPI（历史K线拉取）和 BinanceCopyTradeClient（账户/订单/持仓/下单），
以及 BinanceUserStreamManager 中的 REST 数据拉取方法，
提供完整的币安 REST API 调用入口。

同时提供同步和异步两种接口：
- 同步方法（如 get_account_info）：使用 httpx 同步客户端
- 异步方法（如 async_get_account_info）：使用 aiohttp 异步客户端

支持 spot（现货）和 futures（合约）两种账户类型。
"""

import logging
import time
from datetime import datetime
from typing import Any, Optional

import httpx
import numpy as np

from quant_trading_system.models.market import BarArray
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.exchange_adapter.binance.binance_base import (
    BinanceConfig,
    BinanceRestBase,
)
from quant_trading_system.exchange_adapter.utils import (
    TimeUtils,
    RetryUtils,
)

logger = logging.getLogger(__name__)


class BinanceRestClient(BinanceRestBase):
    """
    币安 REST API 统一客户端

    合并了历史K线拉取、账户查询、订单管理、持仓管理、下单等功能。
    继承 BinanceRestBase，复用签名、请求、httpx Client 等公共逻辑。

    支持 spot（现货）和 futures（合约）两种账户类型。
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        market_type: str = "spot",
        testnet: bool = False,
        proxy_url: str | None = None,
    ):
        """
        初始化币安 REST 客户端

        Args:
            api_key: 币安 API Key
            api_secret: 币安 API Secret
            market_type: 市场类型 spot/futures
            testnet: 是否使用测试网
            proxy_url: 代理地址（如 socks5://127.0.0.1:7891）
        """
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            market_type=market_type,
            testnet=testnet,
            proxy_url=proxy_url,
        )
        # 保留 account_type 别名，兼容外部调用
        self.account_type = market_type

    # ══════════════════════════════════════════════════════════
    # 历史K线数据（原 BinanceAPI）
    # ══════════════════════════════════════════════════════════

    def fetch_klines(
        self,
        symbol: str,
        timeframe: KlineInterval,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 1000,
    ) -> BarArray:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 "BTCUSDT"
            timeframe: 时间周期
            start_time: 开始时间，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS"
            end_time: 结束时间，格式同上
            limit: 每次请求的数量限制（最大1000）

        Returns:
            K线数组
        """
        # 转换交易对格式
        symbol_formatted = symbol.replace("/", "").upper()

        # 使用共享配置获取时间间隔
        interval = BinanceConfig.get_timeframe_interval(timeframe.value)
        if not interval:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # 使用共享工具解析时间戳
        start_ts = TimeUtils.parse_time_string(start_time) if start_time else None
        end_ts = TimeUtils.parse_time_string(end_time) if end_time else None

        logger.debug(
            "Fetching klines from Binance: "
            f"symbol={symbol_formatted}, timeframe={interval}, "
            f"start={start_time}, end={end_time}"
        )

        # 获取所有K线数据
        all_klines = []
        current_start = start_ts

        while True:
            # 构建请求参数
            params: dict[str, Any] = {
                "symbol": symbol_formatted,
                "interval": interval,
                "limit": min(limit, 1000),
            }

            if current_start:
                params["startTime"] = current_start

            if end_ts:
                params["endTime"] = end_ts

            # 使用共享重试工具发送请求
            def _fetch_request():
                try:
                    response = self._client.get(
                        f"{self.base_url}/api/v3/klines",
                        params=params,
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.RequestError as e:
                    logger.warning(
                        "Network request failed: "
                        f"error_type={type(e).__name__}, error={e}, "
                        f"url={self.base_url}/api/v3/klines"
                    )
                    raise

            try:
                klines = RetryUtils.execute_with_retry(
                    _fetch_request,
                    max_retries=3,
                    base_delay=2.0,
                    retry_exceptions=(
                        httpx.ConnectError,
                        httpx.TimeoutException,
                        httpx.ReadError,
                        httpx.WriteError,
                        httpx.ProxyError,
                        httpx.NetworkError
                    )
                )
            except Exception as e:
                logger.error(
                    f"Failed to fetch klines after retries: "
                    f"error={e}, symbol={symbol_formatted}"
                )
                raise

            if not klines:
                break

            all_klines.extend(klines)

            if len(klines) < limit:
                break

            if end_ts and klines[-1][0] >= end_ts:
                break

            current_start = klines[-1][0] + 1
            time.sleep(0.2)

        logger.info(f"Fetched klines: symbol={symbol_formatted}, count={len(all_klines)}")

        return self._convert_to_bar_array(symbol, timeframe, all_klines)

    def _convert_to_bar_array(
        self,
        symbol: str,
        timeframe: KlineInterval,
        klines: list[list[Any]],
    ) -> BarArray:
        """将币安K线数据转换为BarArray"""
        if not klines:
            return BarArray(
                symbol=symbol,
                exchange="binance",
                timeframe=timeframe,
                timestamp=np.array([], dtype="datetime64[ms]"),
                open=np.array([], dtype=np.float64),
                high=np.array([], dtype=np.float64),
                low=np.array([], dtype=np.float64),
                close=np.array([], dtype=np.float64),
                volume=np.array([], dtype=np.float64),
                turnover=np.array([], dtype=np.float64),
            )

        try:
            timestamps = [k[0] for k in klines]
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            turnovers = [float(k[7]) for k in klines]

            return BarArray(
                symbol=symbol,
                exchange="binance",
                timeframe=timeframe,
                timestamp=np.array(timestamps, dtype="datetime64[ms]"),
                open=np.array(opens, dtype=np.float64),
                high=np.array(highs, dtype=np.float64),
                low=np.array(lows, dtype=np.float64),
                close=np.array(closes, dtype=np.float64),
                volume=np.array(volumes, dtype=np.float64),
                turnover=np.array(turnovers, dtype=np.float64),
            )
        except (ValueError, IndexError, TypeError) as e:
            logger.error(
                f"Failed to convert kline data: error={e}, "
                f"symbol={symbol}, klines_count={len(klines)}"
            )
            raise ValueError(f"Invalid kline data format: {e}")

    # ══════════════════════════════════════════════════════════
    # 账户信息（同步）
    # ══════════════════════════════════════════════════════════

    def get_account_info(self) -> dict[str, Any]:
        """获取账户信息（现货/合约）"""
        path = self._get_path("/api/v3/account", "/fapi/v2/account")
        return self._request("GET", path)

    def get_balance(self, asset: str = "USDT") -> dict[str, Any]:
        """
        获取指定资产余额

        Args:
            asset: 资产名称

        Returns:
            {free, locked, total}
        """
        account = self.get_account_info()

        if self.market_type == "spot":
            for b in account.get("balances", []):
                if b["asset"] == asset.upper():
                    free = float(b.get("free", 0))
                    locked = float(b.get("locked", 0))
                    return {"free": free, "locked": locked, "total": free + locked}
            return {"free": 0, "locked": 0, "total": 0}
        else:
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

    # ══════════════════════════════════════════════════════════
    # 订单查询（同步）
    # ══════════════════════════════════════════════════════════

    def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        order_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """获取所有历史订单"""
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

        path = self._get_path("/api/v3/allOrders", "/fapi/v1/allOrders")
        return self._request("GET", path, params)

    def get_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        """获取当前挂单"""
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol.replace("/", "").upper()

        path = self._get_path("/api/v3/openOrders", "/fapi/v1/openOrders")
        return self._request("GET", path, params)

    def get_my_trades(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        from_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """获取历史成交记录"""
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

        path = self._get_path("/api/v3/myTrades", "/fapi/v1/userTrades")
        return self._request("GET", path, params)

    # ══════════════════════════════════════════════════════════
    # 合约专用（同步）
    # ══════════════════════════════════════════════════════════

    def get_futures_positions(self) -> list[dict[str, Any]]:
        """获取合约持仓信息"""
        if self.market_type != "futures":
            raise ValueError("此方法仅适用于合约账户")
        return self._request("GET", "/fapi/v2/positionRisk")

    def get_futures_income(
        self,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取合约账户收益流水"""
        if self.market_type != "futures":
            raise ValueError("此方法仅适用于合约账户")

        params: dict[str, Any] = {"limit": min(limit, 1000)}
        if income_type:
            params["incomeType"] = income_type
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        return self._request("GET", "/fapi/v1/income", params)

    # ══════════════════════════════════════════════════════════
    # 下单接口（同步）
    # ══════════════════════════════════════════════════════════

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
        下单

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

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return self._request("POST", path, params)

    # ══════════════════════════════════════════════════════════
    # 撤单接口（同步）
    # ══════════════════════════════════════════════════════════

    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        撤销订单

        Args:
            symbol: 交易对
            order_id: 交易所订单ID（与 client_order_id 二选一）
            client_order_id: 客户端订单ID

        Returns:
            撤单结果
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
        }
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("必须提供 order_id 或 client_order_id")

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return self._request("DELETE", path, params)

    def query_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        查询单个订单状态

        Args:
            symbol: 交易对
            order_id: 交易所订单ID（与 client_order_id 二选一）
            client_order_id: 客户端订单ID

        Returns:
            订单信息
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
        }
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return self._request("GET", path, params)

    # ══════════════════════════════════════════════════════════
    # 价格查询（同步）
    # ══════════════════════════════════════════════════════════

    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        params = {"symbol": symbol.replace("/", "").upper()}
        path = self._get_path("/api/v3/ticker/price", "/fapi/v1/ticker/price")
        result = self._request("GET", path, params, signed=False)
        return float(result.get("price", 0))

    # ══════════════════════════════════════════════════════════
    # 跟单逻辑工具方法（同步）
    # ══════════════════════════════════════════════════════════

    def sync_new_orders(
        self,
        symbol: str,
        last_order_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        增量同步新订单（跟单核心）

        从last_order_id之后拉取新订单，用于跟单同步。
        """
        order_id = int(last_order_id) if last_order_id else None
        all_orders = self.get_all_orders(symbol, order_id=order_id, limit=100)

        filled_orders = [
            o for o in all_orders
            if o.get("status") == "FILLED" and str(o.get("orderId", "")) != str(last_order_id)
        ]

        return filled_orders

    def convert_order_to_signal(self, order: dict[str, Any]) -> dict[str, Any]:
        """将币安订单转化为跟单信号"""
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

    # ══════════════════════════════════════════════════════════
    # 异步撤单/查单接口
    # ══════════════════════════════════════════════════════════

    async def async_cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """异步撤销订单"""
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
        }
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("必须提供 order_id 或 client_order_id")

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return await self._async_request("DELETE", path, params)

    async def async_query_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """异步查询单个订单状态"""
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
        }
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return await self._async_request("GET", path, params)

    async def async_place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "MARKET",
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        time_in_force: Optional[str] = None,
        stop_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        异步下单

        Args:
            symbol: 交易对
            side: BUY/SELL
            order_type: MARKET/LIMIT/STOP/STOP_LIMIT
            quantity: 数量
            price: 价格（限价单必填）
            time_in_force: 有效期
            stop_price: 触发价格
            client_order_id: 客户端自定义订单ID

        Returns:
            订单信息
        """
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "side": side.upper(),
            "type": order_type.upper(),
        }
        if quantity:
            params["quantity"] = f"{quantity:.8f}"
        if price and order_type.upper() in ("LIMIT", "STOP_LIMIT"):
            params["price"] = f"{price:.8f}"
            params["timeInForce"] = time_in_force or "GTC"
        if stop_price and order_type.upper() in ("STOP", "STOP_LIMIT"):
            params["stopPrice"] = f"{stop_price:.8f}"
        if client_order_id:
            params["newClientOrderId"] = client_order_id

        path = self._get_path("/api/v3/order", "/fapi/v1/order")
        return await self._async_request("POST", path, params)

    # ══════════════════════════════════════════════════════════
    # 异步 REST 查询方法
    # ══════════════════════════════════════════════════════════

    async def async_get_account_info(self) -> dict[str, Any]:
        """异步获取账户信息"""
        path = self._get_path("/api/v3/account", "/fapi/v2/account")
        return await self._async_request("GET", path)

    async def async_get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """异步获取当前挂单"""
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol.replace("/", "").upper()
        path = self._get_path("/api/v3/openOrders", "/fapi/v1/openOrders")
        return await self._async_request("GET", path, params)

    async def async_get_all_orders(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取历史订单"""
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "limit": min(limit, 1000),
        }
        path = self._get_path("/api/v3/allOrders", "/fapi/v1/allOrders")
        return await self._async_request("GET", path, params)

    async def async_get_my_trades(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取成交记录"""
        params: dict[str, Any] = {
            "symbol": symbol.replace("/", "").upper(),
            "limit": min(limit, 1000),
        }
        path = self._get_path("/api/v3/myTrades", "/fapi/v1/userTrades")
        return await self._async_request("GET", path, params)

    async def async_get_positions(self) -> list[dict[str, Any]]:
        """
        异步获取持仓信息

        - 现货：从账户信息中提取非零余额的资产
        - 合约：直接查询持仓信息
        """
        if self.market_type == "spot":
            account = await self.async_get_account_info()
            return [
                balance for balance in account.get("balances", [])
                if float(balance.get("free", 0)) > 0 or float(balance.get("locked", 0)) > 0
            ]
        else:
            result = await self._async_request("GET", "/fapi/v2/positionRisk")
            return [
                pos for pos in result
                if float(pos.get("positionAmt", 0)) != 0
            ]
