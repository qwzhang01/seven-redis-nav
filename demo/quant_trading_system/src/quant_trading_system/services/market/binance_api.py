#!/usr/bin/env python3
"""
币安API客户端
============

提供币安REST API接口，用于获取历史数据
"""

import time
from datetime import datetime
from typing import Any

import httpx
import numpy as np
import structlog

from quant_trading_system.models.market import BarArray
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.services.market.common_utils import (
    TimeUtils,
    BinanceDataConverter,
    RetryUtils,
    BinanceConfig
)

logger = structlog.get_logger(__name__)


class BinanceAPI:
    """
    币安REST API客户端

    用于获取历史K线数据
    """

    def __init__(
        self,
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
    ) -> None:
        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret

        # 使用共享配置获取基础URL
        self.base_url = BinanceConfig.get_base_url(market_type)

        # HTTP客户端 - 增加超时和重试配置
        self._client = httpx.Client(
            timeout=httpx.Timeout(connect=30.0, read=60.0, write=30.0, pool=30.0),
            verify=True,  # SSL验证
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

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
            "Fetching klines from Binance",
            symbol=symbol_formatted,
            timeframe=interval,
            start=start_time,
            end=end_time,
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

            # 使用共享重试工具发送请求，增加更多网络异常类型
            def _fetch_request():
                try:
                    response = self._client.get(
                        f"{self.base_url}/api/v3/klines",
                        params=params,
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.RequestError as e:
                    # 记录详细的网络错误信息
                    logger.warning(
                        "Network request failed",
                        error_type=type(e).__name__,
                        error=str(e),
                        url=f"{self.base_url}/api/v3/klines",
                        params=params
                    )
                    raise

            try:
                klines = RetryUtils.execute_with_retry(
                    _fetch_request,
                    max_retries=3,
                    base_delay=2.0,  # 增加基础延迟
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
                    "Failed to fetch klines after retries",
                    error=str(e),
                    error_type=type(e).__name__,
                    symbol=symbol_formatted,
                    retries=3
                )
                raise

            # 检查是否有数据
            if not klines:
                break

            all_klines.extend(klines)

            # 检查是否需要继续获取
            if len(klines) < limit:
                break

            # 如果指定了结束时间且已经到达，停止
            if end_ts and klines[-1][0] >= end_ts:
                break

            # 更新起始时间为最后一根K线的时间+1ms
            current_start = klines[-1][0] + 1

            # 增加请求间隔，避免触发API限制
            time.sleep(0.2)

        logger.info(
            "Fetched klines",
            symbol=symbol_formatted,
            count=len(all_klines),
        )

        # 使用共享工具转换为BarArray
        return self._convert_to_bar_array(
            symbol,
            timeframe,
            all_klines,
        )

    def _convert_to_bar_array(
        self,
        symbol: str,
        timeframe: KlineInterval,
        klines: list[list[Any]],
    ) -> BarArray:
        """
        将币安K线数据转换为BarArray

        币安K线格式:
        [
            [
                1499040000000,      // 开盘时间
                "0.01634790",       // 开盘价
                "0.80000000",       // 最高价
                "0.01575800",       // 最低价
                "0.01577100",       // 收盘价
                "148976.11427815",  // 成交量
                1499644799999,      // 收盘时间
                "2434.19055334",    // 成交额
                308,                // 成交笔数
                "1756.87402397",    // 主动买入成交量
                "28.46694368",      // 主动买入成交额
                "17928899.62484339" // 忽略
            ]
        ]
        """
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
            # 使用共享工具提取数据
            timestamps = [k[0] for k in klines]
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            turnovers = [float(k[7]) for k in klines]

            # 转换为numpy数组
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
                "Failed to convert kline data",
                error=str(e),
                symbol=symbol,
                klines_count=len(klines),
                first_kline=klines[0] if klines else None
            )
            raise ValueError(f"Invalid kline data format: {e}")

    def close(self) -> None:
        """关闭HTTP客户端"""
        if hasattr(self, '_client') and self._client:
            try:
                self._client.close()
                logger.debug("HTTP client closed")
            except Exception as e:
                logger.warning("Error closing HTTP client", error=str(e))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
