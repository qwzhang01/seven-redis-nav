"""
通用工具模块
============

包含币安数据采集相关的共享工具函数，消除代码重复
"""

import time
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TimeUtils:
    """时间工具类"""

    @staticmethod
    def parse_time_string(time_str: str) -> int:
        """
        解析时间字符串为毫秒时间戳

        Args:
            time_str: 时间字符串，格式支持：
                     - "YYYY-MM-DD"（仅日期）
                     - "YYYY-MM-DD HH:MM:SS"（完整时间）
                     - ISO 8601格式（如："YYYY-MM-DDTHH:MM:SSZ"、"YYYY-MM-DDTHH:MM:SS+HH:MM"）

        Returns:
            毫秒时间戳
        """
        try:
            # 首先尝试解析ISO 8601格式
            if "T" in time_str:
                # 移除时区信息，因为datetime.fromisoformat()需要Python 3.7+
                # 对于简单的ISO格式，可以直接使用strptime
                if time_str.endswith("Z"):
                    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                elif "+" in time_str:
                    # 处理带时区偏移的格式，如：2026-02-24T16:55:17+08:00
                    dt_str = time_str.split("+")[0]
                    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                elif "-" in time_str[10:]:
                    # 处理带负时区偏移的格式
                    dt_str = time_str.split("-")[0]
                    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                else:
                    # 不带时区的ISO格式
                    dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
            # 尝试解析完整时间
            elif " " in time_str:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(time_str, "%Y-%m-%d")

            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.error("Failed to parse time", time_str=time_str, error=str(e))
            raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def timestamp_to_datetime(timestamp_ms: int) -> datetime:
        """
        将毫秒时间戳转换为datetime对象

        Args:
            timestamp_ms: 毫秒时间戳

        Returns:
            datetime对象
        """
        return datetime.fromtimestamp(timestamp_ms / 1000)


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

        Args:
            data: 币安深度数据

        Returns:
            统一格式的深度数据
        """
        return {
            "symbol": data.get("s", ""),
            "exchange": "binance",
            "timestamp": data.get("E", 0),
            "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
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


class RetryUtils:
    """重试工具类"""

    @staticmethod
    def execute_with_retry(
        func: callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        retry_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        带重试机制执行函数

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            retry_exceptions: 需要重试的异常类型
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        retry_count = 0

        while retry_count < max_retries:
            try:
                return func(**kwargs)
            except retry_exceptions as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(
                        "Failed after retries",
                        error=str(e),
                        retries=max_retries,
                    )
                    raise

                logger.warning(
                    "Retrying operation",
                    error=str(e),
                    retry=retry_count,
                    max_retries=max_retries,
                )
                time.sleep(base_delay * retry_count)  # 指数退避

        raise RuntimeError("Unexpected error in retry logic")


class BinanceConfig:
    """币安配置常量"""

    # REST API端点
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    # WebSocket端点
    SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
    FUTURES_WS_URL = "wss://fstream.binance.com/ws"

    # 时间周期映射
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


class OKXDataConverter:
    """OKX数据转换工具类"""

    @staticmethod
    def convert_trade_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换OKX成交数据为统一格式

        Args:
            data: OKX成交数据

        Returns:
            统一格式的成交数据
        """
        trade = data["data"][0] if data.get("data") else {}
        return {
            "symbol": data["arg"]["instId"].replace("-", "/"),
            "exchange": "okx",
            "timestamp": int(trade.get("ts", 0)),
            "last_price": float(trade.get("px", 0)),
            "volume": float(trade.get("sz", 0)),
            "is_trade": True,
            "trade_id": trade.get("tradeId", ""),
        }

    @staticmethod
    def convert_ticker_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换OKX Ticker数据为统一格式

        Args:
            data: OKX Ticker数据

        Returns:
            统一格式的Ticker数据
        """
        ticker = data["data"][0] if data.get("data") else {}
        return {
            "symbol": data["arg"]["instId"].replace("-", "/"),
            "exchange": "okx",
            "timestamp": int(ticker.get("ts", 0)),
            "last_price": float(ticker.get("last", 0)),
            "bid_price": float(ticker.get("bidPx", 0)),
            "ask_price": float(ticker.get("askPx", 0)),
            "bid_size": float(ticker.get("bidSz", 0)),
            "ask_size": float(ticker.get("askSz", 0)),
            "volume": float(ticker.get("vol24h", 0)),
            "turnover": float(ticker.get("volCcy24h", 0)),
            "is_trade": False,
        }

    @staticmethod
    def convert_depth_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        转换OKX深度数据为统一格式

        Args:
            data: OKX深度数据

        Returns:
            统一格式的深度数据
        """
        book = data["data"][0] if data.get("data") else {}
        return {
            "symbol": data["arg"]["instId"].replace("-", "/"),
            "exchange": "okx",
            "timestamp": int(book.get("ts", 0)),
            "bids": [[float(b[0]), float(b[1])] for b in book.get("bids", [])],
            "asks": [[float(a[0]), float(a[1])] for a in book.get("asks", [])],
        }

    @staticmethod
    def convert_kline_data(klines: list[list[str]]) -> list[dict[str, Any]]:
        """
        转换OKX K线数据为统一格式

        Args:
            klines: OKX K线数据列表

        Returns:
            统一格式的K线数据列表
        """
        result = []
        for kline in klines:
            # OKX K线格式: [timestamp, open, high, low, close, volume, turnover]
            result.append({
                "timestamp": int(kline[0]),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "turnover": float(kline[6]),
            })
        return result


class OKXConfig:
    """OKX配置常量"""

    # REST API端点
    BASE_URL = "https://www.okx.com"

    # WebSocket端点
    WS_URL = "wss://ws.okx.com:8443/ws/v5/public"

    # 时间周期映射
    TIMEFRAME_MAP = {
        "M1": "1m",
        "M3": "3m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1H",
        "H4": "4H",
        "D1": "1D",
        "W1": "1W",
        "MN1": "1M",
    }

    @staticmethod
    def get_base_url() -> str:
        """获取基础URL"""
        return OKXConfig.BASE_URL

    @staticmethod
    def get_ws_url() -> str:
        """获取WebSocket URL"""
        return OKXConfig.WS_URL

    @staticmethod
    def get_timeframe_interval(timeframe: str) -> str:
        """获取时间周期对应的OKX间隔"""
        return OKXConfig.TIMEFRAME_MAP.get(timeframe, timeframe)
