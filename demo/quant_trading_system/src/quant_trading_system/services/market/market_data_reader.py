"""
行情数据读取服务

从 TimescaleDB 查询行情数据（K线、Tick等）。
基于 AsyncTimescaleDB（SQLAlchemy 异步引擎 + asyncpg），全部使用异步查询。
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import structlog
import numpy as np

from quant_trading_system.models.market import BarArray, Bar
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.core.database import get_async_database

logger = structlog.get_logger(__name__)


class MarketDataReader:
    """行情数据读取服务（异步版本）"""

    def __init__(self):
        self.db = get_async_database()

    async def get_kline_data(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> BarArray:
        """
        获取K线数据（异步版本）

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
            if isinstance(timeframe, KlineInterval):
                tf_str = timeframe.value
            else:
                tf_str = timeframe

            rows = await self.db.execute_raw(
                """
                SELECT timestamp, open, high, low, close, volume, turnover
                FROM kline_data
                WHERE symbol = %s AND timeframe = %s
                AND timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp ASC
                LIMIT %s
                """,
                (symbol, tf_str, start_time, end_time, limit),
            )

            if not rows:
                logger.warning(
                    "No kline data found",
                    symbol=symbol,
                    timeframe=tf_str,
                    start_time=start_time,
                    end_time=end_time,
                )
                return BarArray(symbol=symbol, exchange="unknown", timeframe=timeframe)

            timestamps = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            turnovers = []

            for row in rows:
                timestamps.append(row[0])
                opens.append(float(row[1]))
                highs.append(float(row[2]))
                lows.append(float(row[3]))
                closes.append(float(row[4]))
                volumes.append(float(row[5]))
                turnovers.append(float(row[6]) if row[6] else 0.0)

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
                turnover=np.array(turnovers, dtype=np.float64),
            )

            logger.debug(
                "Kline data retrieved",
                symbol=symbol,
                timeframe=tf_str,
                count=len(rows),
                start_time=timestamps[0] if timestamps else None,
                end_time=timestamps[-1] if timestamps else None,
            )

            return bar_array

        except Exception as e:
            logger.error(
                "Failed to query kline data",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe,
            )
            return BarArray(symbol=symbol, exchange="unknown", timeframe=timeframe)

    def get_kline_data_sync(
        self,
        symbol: str,
        timeframe: Union[str, KlineInterval],
        start_time: datetime,
        end_time: datetime,
        limit: int = 10000
    ) -> BarArray:
        """
        获取K线数据（同步兼容版本）

        通过 asyncio 事件循环运行异步查询。
        适用于在同步上下文中调用的场景（如回测引擎）。
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 已在事件循环中，创建 Future 来运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(
                    asyncio.run,
                    self.get_kline_data(symbol, timeframe, start_time, end_time, limit)
                ).result()
                return result
        else:
            return asyncio.run(
                self.get_kline_data(symbol, timeframe, start_time, end_time, limit)
            )

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
        import asyncio

        result = {}
        tasks = []
        task_keys = []

        for symbol in symbols:
            result[symbol] = {}
            for timeframe in timeframes:
                task = self.get_kline_data(symbol, timeframe, start_time, end_time, limit)
                tasks.append(task)
                task_keys.append((symbol, timeframe))

        # 并行执行所有查询
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (symbol, timeframe), task_result in zip(task_keys, results):
            if isinstance(task_result, Exception):
                logger.error(
                    "Failed to query kline data for symbol/timeframe",
                    error=str(task_result),
                    symbol=symbol,
                    timeframe=timeframe,
                )
                result[symbol][timeframe] = BarArray(
                    symbol=symbol, exchange="unknown", timeframe=timeframe
                )
            else:
                result[symbol][timeframe] = task_result

        return result

    async def get_available_symbols(self) -> List[str]:
        """获取数据库中可用的交易对列表"""
        try:
            rows = await self.db.execute_raw(
                "SELECT DISTINCT symbol FROM kline_data ORDER BY symbol"
            )
            symbols = [row[0] for row in rows]
            logger.debug("Available symbols retrieved", count=len(symbols))
            return symbols
        except Exception as e:
            logger.error("Failed to query available symbols", error=str(e))
            return []

    async def get_available_timeframes(self, symbol: str = None) -> List[str]:
        """获取数据库中可用的时间框架列表"""
        try:
            if symbol:
                rows = await self.db.execute_raw(
                    "SELECT DISTINCT timeframe FROM kline_data WHERE symbol = %s ORDER BY timeframe",
                    (symbol,),
                )
            else:
                rows = await self.db.execute_raw(
                    "SELECT DISTINCT timeframe FROM kline_data ORDER BY timeframe"
                )
            timeframes = [row[0] for row in rows]
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

            rows = await self.db.execute_raw(
                """
                SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
                FROM kline_data
                WHERE symbol = %s AND timeframe = %s
                """,
                (symbol, tf_str),
            )

            if not rows or rows[0][0] is None:
                return {'start_time': None, 'end_time': None, 'count': 0}

            result = rows[0]
            return {
                'start_time': result[0],
                'end_time': result[1],
                'count': result[2],
            }

        except Exception as e:
            logger.error(
                "Failed to query data time range",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe,
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

            rows = await self.db.execute_raw(
                """
                SELECT timestamp, open, high, low, close, volume, turnover
                FROM kline_data
                WHERE symbol = %s AND timeframe = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (symbol, tf_str),
            )

            if not rows:
                return None

            result = rows[0]
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
                is_closed=True,
            )

        except Exception as e:
            logger.error(
                "Failed to query latest bar",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe,
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
            rows = await self.db.execute_raw(
                """
                SELECT timestamp, price, volume, bid_price, ask_price
                FROM tick_data
                WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp ASC
                LIMIT %s
                """,
                (symbol, start_time, end_time, limit),
            )

            results = []
            for row in rows:
                results.append({
                    'timestamp': row[0],
                    'price': float(row[1]),
                    'volume': float(row[2]),
                    'bid_price': float(row[3]) if row[3] else None,
                    'ask_price': float(row[4]) if row[4] else None,
                })
            return results

        except Exception as e:
            logger.error("Failed to query tick data", error=str(e))
            return []


# 全局读取服务实例
_reader_instance: Optional[MarketDataReader] = None


def get_market_data_reader() -> MarketDataReader:
    """获取行情数据读取服务实例（单例模式）"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = MarketDataReader()
    return _reader_instance


async def init_market_data_reader() -> MarketDataReader:
    """初始化行情数据读取服务"""
    service = get_market_data_reader()
    return service
