"""
数据查询服务

为回测引擎提供从TimescaleDB获取数据的功能
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import structlog
import numpy as np

from quant_trading_system.models.market import BarArray, Bar
from quant_trading_system.core.enums import KlineInterval
from .database import get_database

logger = structlog.get_logger(__name__)


class DataQueryService:
    """数据查询服务"""

    def __init__(self):
        self.db = get_database()

    def get_kline_data_sync(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> BarArray:
        """
        获取K线数据（同步版本）

        内部使用同步的 psycopg2 连接，可在同步/异步上下文中安全调用。

        Args:
            symbol: 交易对符号 (如: BTC/USDT)
            timeframe: 时间框架
            start_time: 开始时间
            end_time: 结束时间
            limit: 最大数据条数

        Returns:
            BarArray: K线数据数组
        """
        try:
            # 转换时间框架格式
            if isinstance(timeframe, KlineInterval):
                tf_str = timeframe.value
            else:
                tf_str = timeframe

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # 查询K线数据
                query = """
                    SELECT timestamp, open, high, low, close, volume, turnover
                    FROM kline_data
                    WHERE symbol = %s AND timeframe = %s
                    AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                    LIMIT %s
                """

                cursor.execute(query, (symbol, tf_str, start_time, end_time, limit))

                results = cursor.fetchall()

                if not results:
                    logger.warning(
                        "No kline data found",
                        symbol=symbol,
                        timeframe=tf_str,
                        start_time=start_time,
                        end_time=end_time
                    )
                    return BarArray(symbol=symbol, exchange="unknown", timeframe=timeframe)

                # 转换为BarArray格式
                timestamps = []
                opens = []
                highs = []
                lows = []
                closes = []
                volumes = []
                turnovers = []

                for row in results:
                    timestamps.append(row[0])
                    opens.append(float(row[1]))
                    highs.append(float(row[2]))
                    lows.append(float(row[3]))
                    closes.append(float(row[4]))
                    volumes.append(float(row[5]))
                    turnovers.append(float(row[6]) if row[6] else 0.0)

                # 转换为numpy数组
                bar_array = BarArray(
                    symbol=symbol,
                    exchange="unknown",
                    timeframe=timeframe,
                    timestamp=np.array(timestamps, dtype="datetime64[ms]"),
                    open=np.array(opens, dtype=np.float64),
                    high=np.array(highs, dtype=np.float64),
                    low=np.array(lows, dtype=np.float64),
                    close=np.array(closes, dtype=np.float64),
                    volume=np.array(volumes, dtype=np.float64),
                    turnover=np.array(turnovers, dtype=np.float64)
                )

                logger.debug(
                    "Kline data retrieved",
                    symbol=symbol,
                    timeframe=tf_str,
                    count=len(results),
                    start_time=timestamps[0] if timestamps else None,
                    end_time=timestamps[-1] if timestamps else None
                )

                return bar_array

        except Exception as e:
            logger.error(
                "Failed to query kline data",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe
            )
            # 返回空的BarArray
            return BarArray(symbol=symbol, exchange="unknown", timeframe=timeframe)

    async def get_kline_data(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> BarArray:
        """
        获取K线数据（异步版本，委托给同步实现）

        Args:
            symbol: 交易对符号 (如: BTC/USDT)
            timeframe: 时间框架
            start_time: 开始时间
            end_time: 结束时间
            limit: 最大数据条数

        Returns:
            BarArray: K线数据数组
        """
        return self.get_kline_data_sync(symbol, timeframe, start_time, end_time, limit)

    async def get_multiple_kline_data(
        self,
        symbols: List[str],
        timeframes: List[Union[str, KlineInterval]],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> Dict[str, Dict[KlineInterval, BarArray]]:
        """
        获取多个品种多个周期的K线数据

        Args:
            symbols: 交易对符号列表
            timeframes: 时间框架列表
            start_time: 开始时间
            end_time: 结束时间
            limit: 每个品种的最大数据条数

        Returns:
            Dict[str, Dict[KlineInterval, BarArray]]: 多品种多周期数据
        """
        result = {}

        # 并行查询所有品种和周期
        tasks = []
        for symbol in symbols:
            result[symbol] = {}
            for timeframe in timeframes:
                task = self.get_kline_data(symbol, timeframe, start_time, end_time, limit)
                tasks.append((symbol, timeframe, task))

        # 等待所有查询完成
        for symbol, timeframe, task in tasks:
            try:
                bar_array = await task
                result[symbol][timeframe] = bar_array
            except Exception as e:
                logger.error(
                    "Failed to query kline data for symbol/timeframe",
                    error=str(e),
                    symbol=symbol,
                    timeframe=timeframe
                )
                # 创建空的BarArray
                result[symbol][timeframe] = BarArray(
                    symbol=symbol,
                    exchange="unknown",
                    timeframe=timeframe
                )

        return result

    async def get_available_symbols(self) -> List[str]:
        """获取数据库中可用的交易对列表"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT DISTINCT symbol FROM kline_data
                    ORDER BY symbol
                """

                cursor.execute(query)
                results = cursor.fetchall()

                symbols = [row[0] for row in results]

                logger.debug("Available symbols retrieved", count=len(symbols))

                return symbols

        except Exception as e:
            logger.error("Failed to query available symbols", error=str(e))
            return []

    async def get_available_timeframes(self, symbol: str = None) -> List[str]:
        """获取数据库中可用的时间框架列表"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                if symbol:
                    query = """
                        SELECT DISTINCT timeframe FROM kline_data
                        WHERE symbol = %s ORDER BY timeframe
                    """
                    cursor.execute(query, (symbol,))
                else:
                    query = """
                        SELECT DISTINCT timeframe FROM kline_data
                        ORDER BY timeframe
                    """
                    cursor.execute(query)

                results = cursor.fetchall()

                timeframes = [row[0] for row in results]

                logger.debug("Available timeframes retrieved", count=len(timeframes))

                return timeframes

        except Exception as e:
            logger.error("Failed to query available timeframes", error=str(e))
            return []

    async def get_data_time_range(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval]
    ) -> Dict[str, datetime]:
        """获取某个品种某个周期的数据时间范围"""
        try:
            if isinstance(timeframe, KlineInterval):
                tf_str = timeframe.value
            else:
                tf_str = timeframe

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # 查询最早和最晚的时间戳
                query = """
                    SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
                    FROM kline_data
                    WHERE symbol = %s AND timeframe = %s
                """

                cursor.execute(query, (symbol, tf_str))
                result = cursor.fetchone()

                if not result or result[0] is None:
                    return {
                        'start_time': None,
                        'end_time': None,
                        'count': 0
                    }

                return {
                    'start_time': result[0],
                    'end_time': result[1],
                    'count': result[2]
                }

        except Exception as e:
            logger.error(
                "Failed to query data time range",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe
            )
            return {'start_time': None, 'end_time': None, 'count': 0}

    async def get_latest_bar(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval]
    ) -> Optional[Bar]:
        """获取最新的K线数据"""
        try:
            if isinstance(timeframe, KlineInterval):
                tf_str = timeframe.value
            else:
                tf_str = timeframe

            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, open, high, low, close, volume, turnover
                    FROM kline_data
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """

                cursor.execute(query, (symbol, tf_str))
                result = cursor.fetchone()

                if not result:
                    return None

                # result[0] 是数据库返回的 datetime 对象，
                # Bar.timestamp 期望 float（毫秒时间戳），需要转换
                ts = result[0]
                if isinstance(ts, datetime):
                    ts_ms = ts.timestamp() * 1000
                else:
                    ts_ms = float(ts)

                return Bar(
                    timestamp=ts_ms,
                    open=float(result[1]),
                    high=float(result[2]),
                    low=float(result[3]),
                    close=float(result[4]),
                    volume=float(result[5]),
                    symbol=symbol,
                    exchange="unknown",
                    timeframe=timeframe,
                    is_closed=True
                )

        except Exception as e:
            logger.error(
                "Failed to query latest bar",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe
            )
            return None

    async def get_tick_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取实时行情数据"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, price, volume, bid_price, ask_price
                    FROM tick_data
                    WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                    LIMIT %s
                """

                cursor.execute(query, (symbol, start_time, end_time, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'price': float(row[1]),
                        'volume': float(row[2]),
                        'bid_price': float(row[3]) if row[3] else None,
                        'ask_price': float(row[4]) if row[4] else None
                    })

                return results

        except Exception as e:
            logger.error("Failed to query tick data", error=str(e))
            return []


# 全局数据查询实例
data_query_instance: Optional[DataQueryService] = None


def get_data_query_service() -> DataQueryService:
    """获取数据查询服务实例（单例模式）"""
    global data_query_instance
    if data_query_instance is None:
        data_query_instance = DataQueryService()
    return data_query_instance


async def init_data_query_service() -> DataQueryService:
    """初始化数据查询服务"""
    service = get_data_query_service()
    return service
