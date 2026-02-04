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

from quant_trading_system.models.market import Bar, BarArray, TimeFrame

logger = structlog.get_logger(__name__)


class BinanceAPI:
    """
    币安REST API客户端

    用于获取历史K线数据
    """

    # API端点
    SPOT_BASE_URL = "https://api.binance.com"
    FUTURES_BASE_URL = "https://fapi.binance.com"

    # 时间周期映射
    TIMEFRAME_MAP = {
        TimeFrame.M1: "1m",
        TimeFrame.M5: "5m",
        TimeFrame.M15: "15m",
        TimeFrame.M30: "30m",
        TimeFrame.H1: "1h",
        TimeFrame.H4: "4h",
        TimeFrame.D1: "1d",
        TimeFrame.W1: "1w",
    }

    def __init__(
        self,
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
    ) -> None:
        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret

        # 选择基础URL
        if market_type == "spot":
            self.base_url = self.SPOT_BASE_URL
        else:
            self.base_url = self.FUTURES_BASE_URL

        # HTTP客户端
        self._client = httpx.Client(
            timeout=30.0,
            verify=True,  # SSL验证
            follow_redirects=True,
        )

    def fetch_klines(
        self,
        symbol: str,
        timeframe: TimeFrame,
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

        # 转换时间周期
        interval = self.TIMEFRAME_MAP.get(timeframe)
        if not interval:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # 转换时间戳
        start_ts = self._parse_time(start_time) if start_time else None
        end_ts = self._parse_time(end_time) if end_time else None

        logger.info(
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

            # 发送请求
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    response = self._client.get(
                        f"{self.base_url}/api/v3/klines",
                        params=params,
                    )
                    response.raise_for_status()
                    klines = response.json()
                    break  # 成功，跳出重试循环

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(
                            "Failed to fetch klines after retries",
                            error=str(e),
                            symbol=symbol_formatted,
                            retries=max_retries,
                        )
                        raise

                    logger.warning(
                        "Retrying request",
                        error=str(e),
                        retry=retry_count,
                        max_retries=max_retries,
                    )
                    time.sleep(1 * retry_count)  # 指数退避
                    continue

                except Exception as e:
                    logger.error(
                        "Failed to fetch klines",
                        error=str(e),
                        symbol=symbol_formatted,
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

            # 避免请求过快
            time.sleep(0.1)

        logger.info(
            "Fetched klines",
            symbol=symbol_formatted,
            count=len(all_klines),
        )

        # 转换为BarArray
        return self._convert_to_bar_array(
            symbol,
            timeframe,
            all_klines,
        )

    def _parse_time(self, time_str: str) -> int:
        """
        解析时间字符串为毫秒时间戳

        Args:
            time_str: 时间字符串，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS"

        Returns:
            毫秒时间戳
        """
        try:
            # 尝试解析完整时间
            if " " in time_str:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(time_str, "%Y-%m-%d")

            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.error("Failed to parse time", time_str=time_str, error=str(e))
            raise ValueError(f"Invalid time format: {time_str}")

    def _convert_to_bar_array(
        self,
        symbol: str,
        timeframe: TimeFrame,
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

        # 提取数据
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

    def close(self) -> None:
        """关闭HTTP客户端"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
