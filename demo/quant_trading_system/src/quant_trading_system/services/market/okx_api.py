"""
OKX API客户端
=============

提供OKX REST API接口，用于获取历史数据
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
    OKXDataConverter,
    RetryUtils,
    OKXConfig
)

logger = structlog.get_logger(__name__)


class OKXAPI:
    """
    OKX REST API客户端

    用于获取历史K线数据
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = "",
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase

        # 使用共享配置获取基础URL
        self.base_url = OKXConfig.get_base_url()

        # HTTP客户端
        self._client = httpx.Client(
            timeout=30.0,
            verify=True,  # SSL验证
            follow_redirects=True,
        )

    def fetch_klines(
        self,
        symbol: str,
        timeframe: KlineInterval,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> BarArray:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 "BTC-USDT"
            timeframe: 时间周期
            start_time: 开始时间，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS"
            end_time: 结束时间，格式同上
            limit: 每次请求的数量限制（最大100）

        Returns:
            K线数组
        """
        # 转换交易对格式
        symbol_formatted = symbol.replace("/", "-").upper()

        # 使用共享配置获取时间间隔
        interval = OKXConfig.get_timeframe_interval(timeframe.value)
        if not interval:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # 使用共享工具解析时间戳
        start_ts = TimeUtils.parse_time_string(start_time) if start_time else None
        end_ts = TimeUtils.parse_time_string(end_time) if end_time else None

        logger.info(
            "Fetching klines from OKX",
            symbol=symbol_formatted,
            timeframe=interval,
            start=start_time,
            end=end_time,
        )

        # 获取所有K线数据
        all_klines = []
        current_end = end_ts

        while True:
            # 构建请求参数
            params: dict[str, Any] = {
                "instId": symbol_formatted,
                "bar": interval,
                "limit": min(limit, 100),
            }

            if current_end:
                params["after"] = current_end

            # 使用共享重试工具发送请求
            def _fetch_request():
                response = self._client.get(
                    f"{self.base_url}/api/v5/market/candles",
                    params=params,
                )
                response.raise_for_status()
                return response.json()

            try:
                result = RetryUtils.execute_with_retry(
                    _fetch_request,
                    max_retries=3,
                    base_delay=1.0,
                    retry_exceptions=(httpx.ConnectError, httpx.TimeoutException)
                )
            except Exception as e:
                logger.error(
                    "Failed to fetch klines",
                    error=str(e),
                    symbol=symbol_formatted,
                )
                raise

            # 检查是否有数据
            if not result.get("data"):
                break

            klines = result["data"]
            all_klines.extend(klines)

            # 检查是否需要继续获取
            if len(klines) < limit:
                break

            # 如果指定了开始时间且已经到达，停止
            if start_ts and int(klines[-1][0]) <= start_ts:
                break

            # 更新结束时间为第一根K线的时间-1ms（OKX是反向分页）
            current_end = int(klines[0][0]) - 1

            # 避免请求过快
            time.sleep(0.1)

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
        klines: list[list[str]],
    ) -> BarArray:
        """
        将OKX K线数据转换为BarArray

        OKX K线格式:
        [
            [
                "1597026383085",  // 开盘时间
                "3.721",          // 开盘价
                "3.743",          // 最高价
                "3.677",          // 最低价
                "3.708",          // 收盘价
                "5593.59",        // 成交量
                "20575.76"        // 成交额
            ]
        ]
        """
        if not klines:
            return BarArray(
                symbol=symbol,
                exchange="okx",
                timeframe=timeframe,
                timestamp=np.array([], dtype="datetime64[ms]"),
                open=np.array([], dtype=np.float64),
                high=np.array([], dtype=np.float64),
                low=np.array([], dtype=np.float64),
                close=np.array([], dtype=np.float64),
                volume=np.array([], dtype=np.float64),
                turnover=np.array([], dtype=np.float64),
            )

        # 使用共享工具提取数据
        converted_data = OKXDataConverter.convert_kline_data(klines)

        # 转换为numpy数组
        timestamps = [data["timestamp"] for data in converted_data]
        opens = [data["open"] for data in converted_data]
        highs = [data["high"] for data in converted_data]
        lows = [data["low"] for data in converted_data]
        closes = [data["close"] for data in converted_data]
        volumes = [data["volume"] for data in converted_data]
        turnovers = [data["turnover"] for data in converted_data]

        return BarArray(
            symbol=symbol,
            exchange="okx",
            timeframe=timeframe,
            timestamp=np.array(timestamps, dtype="datetime64[ms]"),
            open=np.array(opens, dtype=np.float64),
            high=np.array(highs, dtype=np.float64),
            low=np.array(lows, dtype=np.float64),
            close=np.array(closes, dtype=np.float64),
            volume=np.array(volumes, dtype=np.float64),
            turnover=np.array(turnovers, dtype=np.float64),
        )

    def close(self) -> None:
        """关闭HTTP客户端"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
