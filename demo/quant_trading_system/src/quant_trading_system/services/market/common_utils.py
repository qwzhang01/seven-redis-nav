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

        while retry_count <= max_retries:
            try:
                return func(**kwargs)
            except retry_exceptions as e:
                retry_count += 1

                if retry_count > max_retries:
                    logger.error(
                        "Failed after all retries",
                        error=str(e),
                        error_type=type(e).__name__,
                        retries=max_retries,
                    )
                    raise

                # 根据异常类型调整延迟时间
                delay = RetryUtils._calculate_delay(retry_count, base_delay, e)

                logger.warning(
                    "Operation failed, retrying",
                    error=str(e),
                    error_type=type(e).__name__,
                    retry_count=retry_count,
                    max_retries=max_retries,
                    delay=delay,
                )

                time.sleep(delay)

        raise RuntimeError("Unexpected error in retry logic")

    @staticmethod
    def _calculate_delay(retry_count: int, base_delay: float, exception: Exception) -> float:
        """
        根据异常类型和重试次数计算延迟时间

        Args:
            retry_count: 当前重试次数
            base_delay: 基础延迟
            exception: 发生的异常

        Returns:
            计算后的延迟时间
        """
        # 指数退避基础延迟
        delay = base_delay * (2 ** (retry_count - 1))

        # 根据异常类型调整延迟
        exception_name = type(exception).__name__

        # 连接相关错误使用较短延迟
        if "Connect" in exception_name:
            delay = min(delay, 5.0)  # 连接错误最大延迟5秒
        # 超时相关错误使用中等延迟
        elif "Timeout" in exception_name:
            delay = min(delay, 10.0)  # 超时错误最大延迟10秒
        # 网络相关错误使用较长延迟
        elif any(keyword in exception_name for keyword in ["Network", "Read", "Write", "Proxy"]):
            delay = min(delay, 15.0)  # 网络错误最大延迟15秒
        # 其他错误使用标准延迟
        else:
            delay = min(delay, 30.0)  # 其他错误最大延迟30秒

        # 添加随机抖动避免同步重试
        jitter = delay * 0.1  # 10%的随机抖动
        delay += jitter * (2 * time.time() % 1 - 0.5)

        return max(0.5, delay)  # 最小延迟0.5秒

    @staticmethod
    def execute_with_progressive_retry(
        func: callable,
        max_retries: int = 5,
        base_delay: float = 1.0,
        **kwargs
    ) -> Any:
        """
        使用渐进式重试策略执行函数

        针对网络请求的智能重试策略，根据异常类型和重试次数动态调整

        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            **kwargs: 函数参数

        Returns:
            函数执行结果
        """
        # 定义网络相关的重试异常
        network_exceptions = [
            ConnectionError,
            TimeoutError,
            OSError,
            IOError,
        ]

        # 如果httpx可用，添加httpx相关的异常
        try:
            import httpx
            network_exceptions.extend([
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.ReadError,
                httpx.WriteError,
                httpx.ProxyError,
                httpx.NetworkError,
                httpx.RemoteProtocolError,
                httpx.ProtocolError,
            ])
        except ImportError:
            logger.debug("httpx not available, using standard exceptions only")

        return RetryUtils.execute_with_retry(
            func=func,
            max_retries=max_retries,
            base_delay=base_delay,
            retry_exceptions=tuple(network_exceptions),
            **kwargs
        )


class BinanceConfig:
    """币安配置常量"""

    # REST API端点
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    # WebSocket端点（使用 combined stream 端点，支持多品种深度数据识别）
    SPOT_WS_URL = "wss://stream.binance.com:9443/stream"
    FUTURES_WS_URL = "wss://fstream.binance.com/stream"

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

    @staticmethod
    def convert_ws_kline_data(data: dict[str, Any]) -> dict[str, Any] | None:
        """
        转换OKX WebSocket推送的K线数据为统一格式

        OKX WebSocket K线推送格式:
        {
            "arg": {"channel": "candle1m", "instId": "BTC-USDT"},
            "data": [
                ["1697026860000", "27500.1", "27510.5", "27495.0", "27505.3", "12.5", "343816.25", "343816.25", "1"]
            ]
        }
        data数组: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
        confirm: "0" 表示未完结, "1" 表示已完结

        Args:
            data: OKX WebSocket K线数据

        Returns:
            统一格式的K线数据，如果数据无效返回 None
        """
        try:
            channel = data.get("arg", {}).get("channel", "")
            inst_id = data.get("arg", {}).get("instId", "")
            kline_list = data.get("data", [])

            if not kline_list or not inst_id:
                return None

            kline = kline_list[0]

            # 从 channel 名称解析时间周期
            # OKX channel: candle1m, candle5m, candle15m, candle1H, candle4H, candle1D 等
            interval_str = channel.replace("candle", "")
            # 转换为统一格式: 1m, 5m, 15m, 1h, 4h, 1d
            interval_map = {
                "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "1M": "1M",
            }
            interval = interval_map.get(interval_str, interval_str.lower())

            return {
                "symbol": inst_id.replace("-", "/"),
                "exchange": "okx",
                "timestamp": int(kline[0]),
                "interval": interval,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "turnover": float(kline[6]) if len(kline) > 6 else 0.0,
                "is_closed": kline[8] == "1" if len(kline) > 8 else False,
            }
        except (IndexError, ValueError, KeyError) as e:
            logger.error(f"Failed to convert OKX WebSocket kline data",
                        error=str(e), data=data)
            return None


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
