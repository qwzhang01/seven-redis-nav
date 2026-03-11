"""
Mock 币安 REST API 客户端（开发环境专用）
=========================================

与 BinanceRestClient 完全兼容的接口，
不连接真实 Binance REST API，返回模拟的下单结果和查询数据。

用于开发环境联调和前端对接。
"""

import random
import time
from datetime import datetime
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)

# 模拟交易对价格范围
MOCK_PRICES = {
    "BTCUSDT": 95000.0,
    "ETHUSDT": 2100.0,
    "SOLUSDT": 160.0,
    "BNBUSDT": 620.0,
}


def _get_mock_price(symbol: str) -> float:
    """获取模拟当前价格（带小幅随机波动）"""
    base = MOCK_PRICES.get(symbol.upper(), 100.0)
    # ±1% 波动
    return round(base * random.uniform(0.99, 1.01), 2)


class MockBinanceRestClient:
    """
    Mock 币安 REST API 客户端

    完全兼容 BinanceRestClient 的同步和异步接口，
    不发起真实 HTTP 请求，返回模拟数据。

    模拟特性：
    - place_order / async_place_order: 返回成功的下单结果（含模拟订单ID、成交价格、滑点）
    - get_account_info / async_get_account_info: 返回模拟账户余额
    - get_all_orders / async_get_all_orders: 返回模拟历史订单
    - get_current_price: 返回模拟价格（带随机波动）
    - cancel_order / async_cancel_order: 返回模拟撤单结果
    """

    def __init__(
        self,
        api_key: str = "mock_key",
        api_secret: str = "mock_secret",
        account_type: str = "spot",
        testnet: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_type = account_type
        self.market_type = account_type  # 兼容 BinanceRestClient 的 market_type 属性
        self.base_url = "mock://binance"

        logger.info(
            f"🎭 [Mock] 币安 REST 客户端已创建 "
            f"(account_type={account_type}, api_key={api_key[:8]}...)"
        )

    # ── 下单接口 ──────────────────────────────────────────────

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
        模拟下单

        返回与真实 Binance API 格式一致的下单结果。
        市价单：使用模拟价格计算成交金额。
        """
        symbol_upper = symbol.replace("/", "").upper()
        mock_price = price or _get_mock_price(symbol_upper)
        qty = quantity or (quote_order_qty / mock_price if quote_order_qty else 0.001)
        cum_quote = round(mock_price * qty, 4)
        order_id = random.randint(10**9, 10**10 - 1)
        now_ms = int(time.time() * 1000)

        result = {
            "symbol": symbol_upper,
            "orderId": order_id,
            "orderListId": -1,
            "clientOrderId": f"mock_{order_id}",
            "transactTime": now_ms,
            "price": "0.00000000" if order_type.upper() == "MARKET" else str(mock_price),
            "origQty": str(round(qty, 8)),
            "executedQty": str(round(qty, 8)),
            "cummulativeQuoteQty": str(cum_quote),
            "status": "FILLED",
            "timeInForce": time_in_force or "GTC",
            "type": order_type.upper(),
            "side": side.upper(),
            "fills": [
                {
                    "price": str(mock_price),
                    "qty": str(round(qty, 8)),
                    "commission": str(round(cum_quote * 0.001, 8)),
                    "commissionAsset": "USDT",
                    "tradeId": random.randint(10**8, 10**9),
                }
            ],
        }

        logger.info(
            f"🎭 [Mock] 模拟下单成功: {symbol_upper} {side.upper()} "
            f"qty={qty:.6f} price={mock_price:.2f} total={cum_quote:.4f} "
            f"orderId={order_id}"
        )

        return result

    # ── 撤单接口 ──────────────────────────────────────────────

    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """模拟撤单"""
        symbol_upper = symbol.replace("/", "").upper()
        oid = order_id or random.randint(10**9, 10**10 - 1)
        now_ms = int(time.time() * 1000)

        result = {
            "symbol": symbol_upper,
            "origClientOrderId": client_order_id or f"mock_{oid}",
            "orderId": oid,
            "orderListId": -1,
            "clientOrderId": f"cancel_{oid}",
            "price": "0.00000000",
            "origQty": "0.01000000",
            "executedQty": "0.00000000",
            "cummulativeQuoteQty": "0.00000000",
            "status": "CANCELED",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
        }

        logger.info(
            f"🎭 [Mock] 模拟撤单成功: {symbol_upper} orderId={oid}"
        )
        return result

    def query_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """模拟查询单个订单状态"""
        symbol_upper = symbol.replace("/", "").upper()
        oid = order_id or random.randint(10**9, 10**10 - 1)
        p = _get_mock_price(symbol_upper)
        q = round(random.uniform(0.001, 0.1), 6)

        return {
            "symbol": symbol_upper,
            "orderId": oid,
            "clientOrderId": client_order_id or f"mock_{oid}",
            "price": str(p),
            "origQty": str(q),
            "executedQty": str(q),
            "cummulativeQuoteQty": str(round(p * q, 4)),
            "status": "FILLED",
            "type": "MARKET",
            "side": random.choice(["BUY", "SELL"]),
            "time": int(time.time() * 1000),
        }

    # ── 账户查询 ──────────────────────────────────────────────

    def get_account_info(self) -> dict[str, Any]:
        """返回模拟账户信息"""
        return {
            "makerCommission": 10,
            "takerCommission": 10,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": int(time.time() * 1000),
            "accountType": "SPOT",
            "balances": [
                {"asset": "USDT", "free": "50000.00", "locked": "5000.00"},
                {"asset": "BTC", "free": "0.5", "locked": "0.0"},
                {"asset": "ETH", "free": "5.0", "locked": "1.0"},
                {"asset": "SOL", "free": "100.0", "locked": "0.0"},
                {"asset": "BNB", "free": "10.0", "locked": "0.0"},
            ],
        }

    def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        order_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """返回模拟历史订单"""
        orders = []
        now_ms = int(time.time() * 1000)
        symbol_upper = symbol.replace("/", "").upper()

        for i in range(min(limit, random.randint(5, 15))):
            p = _get_mock_price(symbol_upper)
            q = round(random.uniform(0.001, 0.1), 6)
            orders.append({
                "orderId": random.randint(10**9, 10**10 - 1),
                "symbol": symbol_upper,
                "side": random.choice(["BUY", "SELL"]),
                "type": "MARKET",
                "price": str(p),
                "origQty": str(q),
                "executedQty": str(q),
                "cummulativeQuoteQty": str(round(p * q, 4)),
                "status": "FILLED",
                "time": now_ms - random.randint(0, 86400000 * 7),
            })

        return orders

    def get_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        """返回模拟挂单（随机 0~2 个）"""
        orders = []
        symbols = [symbol] if symbol else list(MOCK_PRICES.keys())
        for sym in symbols:
            if random.random() < 0.2:
                p = _get_mock_price(sym)
                orders.append({
                    "orderId": random.randint(10**9, 10**10 - 1),
                    "symbol": sym.replace("/", "").upper(),
                    "side": random.choice(["BUY", "SELL"]),
                    "type": "LIMIT",
                    "price": str(round(p * random.uniform(0.95, 1.05), 2)),
                    "origQty": str(round(random.uniform(0.001, 0.1), 6)),
                    "executedQty": "0.0",
                    "status": "NEW",
                    "time": int(time.time() * 1000),
                })
        return orders

    def get_my_trades(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        from_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """返回模拟成交记录"""
        trades = []
        now_ms = int(time.time() * 1000)
        symbol_upper = symbol.replace("/", "").upper()

        for i in range(min(limit, random.randint(3, 10))):
            p = _get_mock_price(symbol_upper)
            q = round(random.uniform(0.001, 0.1), 6)
            trades.append({
                "id": random.randint(10**8, 10**9),
                "orderId": random.randint(10**9, 10**10 - 1),
                "symbol": symbol_upper,
                "price": str(p),
                "qty": str(q),
                "quoteQty": str(round(p * q, 4)),
                "commission": str(round(p * q * 0.001, 8)),
                "commissionAsset": "USDT",
                "time": now_ms - random.randint(0, 86400000 * 3),
                "isBuyer": random.choice([True, False]),
                "isMaker": random.choice([True, False]),
            })

        return trades

    def get_futures_positions(self) -> list[dict[str, Any]]:
        """返回模拟合约持仓"""
        return [
            {
                "symbol": "BTCUSDT",
                "positionAmt": "0.01",
                "entryPrice": "92000.00",
                "markPrice": str(_get_mock_price("BTCUSDT")),
                "unRealizedProfit": str(round(random.uniform(-500, 500), 2)),
                "leverage": "10",
            },
        ]

    def get_futures_income(
        self,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """返回模拟合约收益流水"""
        return []

    def sync_new_orders(
        self,
        symbol: str,
        last_order_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """模拟增量同步新订单"""
        # 随机返回 0~3 个新成交订单
        orders = []
        for _ in range(random.randint(0, 3)):
            p = _get_mock_price(symbol)
            q = round(random.uniform(0.001, 0.05), 6)
            orders.append({
                "orderId": random.randint(10**9, 10**10 - 1),
                "symbol": symbol.replace("/", "").upper(),
                "side": random.choice(["BUY", "SELL"]),
                "type": "MARKET",
                "price": str(p),
                "origQty": str(q),
                "executedQty": str(q),
                "cummulativeQuoteQty": str(round(p * q, 4)),
                "status": "FILLED",
                "time": int(time.time() * 1000),
            })
        return orders

    def convert_order_to_signal(self, order: dict[str, Any]) -> dict[str, Any]:
        """将模拟订单转化为信号数据"""
        executed_qty = float(order.get("executedQty", 0))
        cum_quote = float(order.get("cummulativeQuoteQty", 0))
        price = cum_quote / executed_qty if executed_qty > 0 else 0

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
        """返回模拟资产余额"""
        mock_balances = {
            "USDT": {"free": 50000.0, "locked": 5000.0},
            "BTC": {"free": 0.5, "locked": 0.0},
            "ETH": {"free": 5.0, "locked": 1.0},
        }
        bal = mock_balances.get(asset.upper(), {"free": 0, "locked": 0})
        return {
            "free": bal["free"],
            "locked": bal["locked"],
            "total": bal["free"] + bal["locked"],
        }

    def get_current_price(self, symbol: str) -> float:
        """返回模拟当前价格"""
        return _get_mock_price(symbol)

    def get_depth_data(self, symbol: str, limit: int = 20) -> dict[str, Any]:
        """获取深度数据

        Args:
            symbol: 交易对符号，如 "BTCUSDT"
            limit: 深度档位数，可选值：5, 10, 20, 50, 100, 500, 1000，默认20

        Returns:
            dict: 包含深度数据的字典，格式为：
            {
                "lastUpdateId": int,  # 最后更新ID
                "bids": list,        # 买单深度 [[价格, 数量], ...]
                "asks": list         # 卖单深度 [[价格, 数量], ...]
            }
        """
        symbol_upper = symbol.replace("/", "").upper()
        base_price = _get_mock_price(symbol_upper)

        # 生成买单深度（价格从高到低）
        bids = []
        for i in range(min(limit, 20)):
            price = round(base_price * (1 - (i + 1) * 0.001), 2)
            volume = round(random.uniform(0.1, 5.0), 6)
            bids.append([str(price), str(volume)])

        # 生成卖单深度（价格从低到高）
        asks = []
        for i in range(min(limit, 20)):
            price = round(base_price * (1 + (i + 1) * 0.001), 2)
            volume = round(random.uniform(0.1, 5.0), 6)
            asks.append([str(price), str(volume)])

        return {
            "lastUpdateId": int(time.time() * 1000),
            "bids": bids,
            "asks": asks
        }

    def close(self) -> None:
        """关闭客户端（Mock 无需清理）"""
        logger.debug("🎭 [Mock] 币安 REST 客户端已关闭")

    async def aclose(self) -> None:
        """异步关闭客户端（Mock 无需清理，与 BinanceRestBase.aclose 对称）"""
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ══════════════════════════════════════════════════════════
    # 异步方法（与 BinanceRestClient 的 async_* 接口对称）
    # ══════════════════════════════════════════════════════════

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
        """异步模拟下单（委托同步方法）"""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
        )

    async def async_cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """异步模拟撤单（委托同步方法）"""
        return self.cancel_order(
            symbol=symbol,
            order_id=order_id,
            client_order_id=client_order_id,
        )

    async def async_query_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """异步模拟查询订单（委托同步方法）"""
        return self.query_order(
            symbol=symbol,
            order_id=order_id,
            client_order_id=client_order_id,
        )

    async def async_get_account_info(self) -> dict[str, Any]:
        """异步获取模拟账户信息（委托同步方法）"""
        return self.get_account_info()

    async def async_get_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """异步获取模拟挂单（委托同步方法）"""
        return self.get_open_orders(symbol=symbol)

    async def async_get_all_orders(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取模拟历史订单（委托同步方法）"""
        return self.get_all_orders(symbol=symbol, limit=limit)

    async def async_get_my_trades(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """异步获取模拟成交记录（委托同步方法）"""
        return self.get_my_trades(symbol=symbol, limit=limit)

    async def async_get_positions(self) -> list[dict[str, Any]]:
        """
        异步获取模拟持仓信息

        与 BinanceRestClient.async_get_positions 对称：
        - 现货：从账户信息中提取非零余额的资产
        - 合约：返回模拟合约持仓
        """
        if self.account_type == "spot":
            account = self.get_account_info()
            return [
                balance for balance in account.get("balances", [])
                if float(balance.get("free", 0)) > 0 or float(balance.get("locked", 0)) > 0
            ]
        else:
            return self.get_futures_positions()


# 向后兼容别名（已废弃，将在未来版本移除）
MockBinanceCopyTradeClient = MockBinanceRestClient
