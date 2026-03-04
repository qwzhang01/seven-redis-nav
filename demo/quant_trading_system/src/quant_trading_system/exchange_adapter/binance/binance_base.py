"""
币安基础模块
============

包含币安交易所相关的配置常量、REST API 基类和数据转换工具
"""

import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BinanceConfig:
    """币安配置常量"""

    # REST API端点
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    # WebSocket端点（使用 combined stream 端点，支持多品种深度数据识别）
    SPOT_WS_URL = "wss://stream.binance.com:9443/stream"
    FUTURES_WS_URL = "wss://fstream.binance.com/stream"

    # 时间周期映射（系统内部代号 → 币安 API 字符串）
    TIMEFRAME_MAP = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1h",
        "H4": "4h",
        "D1": "1d",
        "W1": "1w",
    }

    # 币安支持的所有 K 线周期（WebSocket 订阅等场景使用）
    ALL_KLINE_INTERVALS = [
        "1s", "1m", "3m", "5m", "15m", "30m",
        "1h", "2h", "4h", "6h", "8h", "12h",
        "1d", "3d", "1w", "1M",
    ]

    @staticmethod
    def get_base_url(market_type: str) -> str:
        """获取基础URL"""
        if market_type == "spot":
            return BinanceConfig.SPOT_BASE_URL
        else:
            return BinanceConfig.FUTURES_BASE_URL

    @staticmethod
    def get_ws_url(market_type: str) -> str:
        """获取WebSocket URL"""
        if market_type == "spot":
            return BinanceConfig.SPOT_WS_URL
        else:
            return BinanceConfig.FUTURES_WS_URL

    @staticmethod
    def get_timeframe_interval(timeframe: str) -> str:
        """获取时间周期对应的币安间隔"""
        return BinanceConfig.TIMEFRAME_MAP.get(timeframe, timeframe)


class BinanceDataConverter:
    """币安数据转换工具类"""

    # 币安K线数据格式映射
    KLINE_FIELD_MAP = {
        "timestamp": 0,
        "open": 1,
        "high": 2,
        "low": 3,
        "close": 4,
        "volume": 5,
        "close_time": 6,
        "turnover": 7,
        "trade_count": 8,
        "taker_buy_volume": 9,
        "taker_buy_turnover": 10,
    }

    @staticmethod
    def extract_kline_data(klines: list[list[Any]], fields: list[str]) -> list[Any]:
        """
        从币安K线数据中提取指定字段

        Args:
            klines: 币安K线数据列表
            fields: 要提取的字段名列表

        Returns:
            提取的数据列表
        """
        if not klines:
            return []

        result = []
        for field in fields:
            if field in BinanceDataConverter.KLINE_FIELD_MAP:
                index = BinanceDataConverter.KLINE_FIELD_MAP[field]
                result.append([float(kline[index]) for kline in klines])

        return result

    @staticmethod
    def convert_trade_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换币安成交数据为统一格式

        Args:
            data: 币安成交数据

        Returns:
            统一格式的成交数据
        """
        return {
            "symbol": data.get("s", ""),
            "exchange": "binance",
            "timestamp": data.get("T", 0),
            "last_price": float(data.get("p", 0)),
            "volume": float(data.get("q", 0)),
            "is_trade": True,
            "trade_id": str(data.get("t", "")),
        }

    @staticmethod
    def convert_ticker_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换币安Ticker数据为统一格式

        Args:
            data: 币安Ticker数据

        Returns:
            统一格式的Ticker数据
        """
        return {
            "symbol": data.get("s", ""),
            "exchange": "binance",
            "timestamp": data.get("E", 0),
            "last_price": float(data.get("c", 0)),
            "bid_price": float(data.get("b", 0)),
            "ask_price": float(data.get("a", 0)),
            "bid_size": float(data.get("B", 0)),
            "ask_size": float(data.get("A", 0)),
            "volume": float(data.get("v", 0)),
            "turnover": float(data.get("q", 0)),
            "is_trade": False,
        }

    @staticmethod
    def convert_depth_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换币安深度数据为统一格式

        兼容两种格式：
        1. 增量深度流(@depth): 有 "e", "s", "E", "b", "a" 字段
        2. 有限档深度流(@depth20@100ms): 有 "lastUpdateId", "bids", "asks" 字段（无 "e" 字段）

        Args:
            data: 币安深度数据

        Returns:
            统一格式的深度数据
        """
        if "lastUpdateId" in data:
            # 有限档深度信息流 (depth20@100ms)
            return {
                "symbol": data.get("s", ""),  # 有限档深度流通常不含 symbol，需外部补充
                "exchange": "binance",
                "timestamp": data.get("E", 0),  # 有限档深度流通常不含时间戳
                "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
                "sequence": data.get("lastUpdateId"),
            }
        else:
            # 增量深度流 (depthUpdate)
            return {
                "symbol": data.get("s", ""),
                "exchange": "binance",
                "timestamp": data.get("E", 0),
                "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
                "sequence": data.get("U"),
            }

    @staticmethod
    def convert_kline_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换币安K线数据为统一格式

        Args:
            data: 币安K线数据

        Returns:
            统一格式的K线数据
        """
        kline_info = data.get("k", {})
        return {
            "symbol": kline_info.get("s", ""),
            "exchange": "binance",
            "timestamp": kline_info.get("t", 0),
            "interval": kline_info.get("i", "1m"),
            "open": float(kline_info.get("o", 0)),
            "high": float(kline_info.get("h", 0)),
            "low": float(kline_info.get("l", 0)),
            "close": float(kline_info.get("c", 0)),
            "volume": float(kline_info.get("v", 0)),
            "is_closed": kline_info.get("x", False),
        }


class BinanceRestBase:
    """
    币安 REST API 基类

    统一封装：
    1. HMAC-SHA256 签名逻辑
    2. httpx.Client 创建与配置
    3. 带签名的 HTTP 请求方法（同步）
    4. spot/futures 路径映射

    子类继承后只需专注于业务方法，无需重复实现签名和请求逻辑。
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        market_type: str = "spot",
        testnet: bool = False,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type

        if testnet:
            if market_type == "spot":
                self.base_url = "https://testnet.binance.vision"
            else:
                self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = BinanceConfig.get_base_url(market_type)

        self._client = self._create_http_client()
        # 异步 HTTP 客户端（延迟创建，复用连接池）
        self._async_session: Any = None

    @staticmethod
    def _create_http_client():
        """
        创建标准 httpx.Client，统一超时和连接池配置。
        延迟导入 httpx，避免未安装时启动报错。
        """
        import httpx as _httpx

        return _httpx.Client(
            timeout=_httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0),
            verify=True,
            follow_redirects=True,
            limits=_httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    # ------------------------------------------------------------------
    # 签名
    # ------------------------------------------------------------------

    def _sign(self, params: dict[str, Any]) -> str:
        """
        对参数进行 HMAC-SHA256 签名

        Args:
            params: 已包含 timestamp 的请求参数

        Returns:
            签名字符串
        """
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    # ------------------------------------------------------------------
    # HTTP 请求
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> Any:
        """
        发送同步 HTTP 请求（带可选签名）

        Args:
            method: HTTP 方法（GET / POST / DELETE）
            path: API 路径，如 "/api/v3/order"
            params: 请求参数
            signed: 是否需要签名

        Returns:
            JSON 响应数据
        """
        import httpx as _httpx

        params = params or {}
        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._sign(params)

        try:
            if method.upper() == "GET":
                response = self._client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self._client.post(url, params=params, headers=headers)
            elif method.upper() == "DELETE":
                response = self._client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except _httpx.HTTPStatusError as e:
            logger.error(
                "Binance API request failed",
                status=e.response.status_code,
                body=e.response.text,
                path=path,
            )
            raise
        except _httpx.RequestError as e:
            logger.error("Binance API network error", error=str(e), path=path)
            raise

    async def _get_async_session(self):
        """
        获取或创建可复用的 aiohttp ClientSession。
        延迟创建以避免在非异步上下文中初始化。
        """
        if self._async_session is None or self._async_session.closed:
            import aiohttp
            self._async_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60, connect=30),
            )
        return self._async_session

    async def _async_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> dict[str, Any]:
        """
        发送异步 HTTP 请求（带可选签名）

        复用 aiohttp.ClientSession 连接池，避免每次请求创建新连接。

        Args:
            method: HTTP 方法（GET / POST / DELETE）
            path: API 路径
            params: 请求参数
            signed: 是否需要签名

        Returns:
            JSON 响应数据
        """
        params = params or {}
        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        session = await self._get_async_session()

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
    # 路径工具
    # ------------------------------------------------------------------

    def _get_path(self, spot_path: str, futures_path: str) -> str:
        """
        根据 market_type 自动选择 spot 或 futures 路径

        Args:
            spot_path: 现货 API 路径
            futures_path: 合约 API 路径

        Returns:
            对应的 API 路径
        """
        return spot_path if self.market_type == "spot" else futures_path

    # ------------------------------------------------------------------
    # 资源释放
    # ------------------------------------------------------------------

    def close(self) -> None:
        """关闭 HTTP 客户端"""
        if hasattr(self, "_client") and self._client:
            try:
                self._client.close()
                logger.debug("HTTP client closed")
            except Exception as e:
                logger.warning("Error closing HTTP client", error=str(e))

    async def aclose(self) -> None:
        """异步关闭：同时关闭同步和异步客户端"""
        self.close()
        if self._async_session and not self._async_session.closed:
            try:
                await self._async_session.close()
                logger.debug("Async HTTP session closed")
            except Exception as e:
                logger.warning("Error closing async session", error=str(e))
            finally:
                self._async_session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
