"""
数据存储服务

提供实时行情数据存储到TimescaleDB的功能
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from quant_trading_system.models.market import Bar, Tick, Depth
from .database import get_database
from quant_trading_system.core.snowflake import generate_snowflake_id  # 新增导入

logger = structlog.get_logger(__name__)


class DataStore:
    """数据存储服务"""

    def __init__(self, batch_size: int = 1000, flush_interval: float = 5.0):
        self.db = get_database()
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # 批量缓存
        self._kline_buffer: List[Bar] = []
        self._tick_buffer: List[Tick] = []
        self._depth_buffer: List[Depth] = []

        # 后台任务
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """启动数据存储服务"""
        if self._running:
            return

        self._running = True

        # 启动定时刷新任务
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info("Data store service started")

    async def stop(self) -> None:
        """停止数据存储服务"""
        if not self._running:
            return

        self._running = False

        # 停止后台任务
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # 刷新剩余数据
        await self.flush_all()

        logger.info("Data store service stopped")

    async def store_kline(self, bar: Bar) -> None:
        """存储K线数据"""
        self._kline_buffer.append(bar)

        # 如果达到批量大小，立即刷新
        if len(self._kline_buffer) >= self.batch_size:
            await self._flush_kline()

    async def store_tick(self, tick: Tick) -> None:
        """存储实时行情数据"""
        self._tick_buffer.append(tick)

        # 如果达到批量大小，立即刷新
        if len(self._tick_buffer) >= self.batch_size:
            await self._flush_tick()

    async def store_depth(self, depth: Depth) -> None:
        """存储深度数据"""
        self._depth_buffer.append(depth)

        # 如果达到批量大小，立即刷新
        if len(self._depth_buffer) >= self.batch_size:
            await self._flush_depth()

    async def flush_all(self) -> None:
        """刷新所有缓存数据到数据库"""
        tasks = []

        if self._kline_buffer:
            tasks.append(self._flush_kline())

        if self._tick_buffer:
            tasks.append(self._flush_tick())

        if self._depth_buffer:
            tasks.append(self._flush_depth())

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _flush_kline(self) -> None:
        """刷新K线数据到数据库"""
        if not self._kline_buffer:
            return

        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # 批量插入K线数据
                query = """
                    INSERT INTO kline_data
                    (id, symbol, exchange, timeframe, timestamp, open, high, low, close, volume, turnover, is_closed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = []
                for bar in self._kline_buffer:
                    turnover = bar.volume * bar.close if bar.volume and bar.close else 0.0
                    values.append((
                        generate_snowflake_id(),  # 为每条记录生成唯一雪花ID
                        bar.symbol,
                        bar.exchange,
                        bar.timeframe.value,
                        bar.timestamp,
                        float(bar.open),
                        float(bar.high),
                        float(bar.low),
                        float(bar.close),
                        float(bar.volume),
                        float(turnover),
                        bar.is_closed
                    ))

                cursor.executemany(query, values)
                conn.commit()

                count = len(self._kline_buffer)
                logger.debug("Kline data flushed to database", count=count)

                # 清空缓存
                self._kline_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush kline data", error=str(e))
            # 保留数据以便重试

    async def _flush_tick(self) -> None:
        """刷新实时行情数据到数据库"""
        if not self._tick_buffer:
            return

        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # 批量插入实时行情数据
                query = """
                    INSERT INTO tick_data
                    (id, symbol, exchange, timestamp, price, volume, bid_price, ask_price, bid_size, ask_size)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = []
                for tick in self._tick_buffer:
                    values.append((
                        generate_snowflake_id(),  # 为每条记录生成唯一雪花ID
                        tick.symbol,
                        "unknown",  # 交易所信息需要从tick对象中获取
                        tick.timestamp,
                        float(tick.price),
                        float(tick.volume),
                        float(tick.bid) if tick.bid else None,
                        float(tick.ask) if tick.ask else None,
                        None,  # bid_size 需要从tick对象中获取
                        None   # ask_size 需要从tick对象中获取
                    ))

                cursor.executemany(query, values)
                conn.commit()

                count = len(self._tick_buffer)
                logger.debug("Tick data flushed to database", count=count)

                # 清空缓存
                self._tick_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush tick data", error=str(e))
            # 保留数据以便重试

    async def _flush_depth(self) -> None:
        """刷新深度数据到数据库"""
        if not self._depth_buffer:
            return

        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                # 批量插入深度数据
                query = """
                    INSERT INTO depth_data
                    (id, symbol, exchange, timestamp, bids, asks)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                values = []
                for depth in self._depth_buffer:
                    values.append((
                        generate_snowflake_id(),  # 为每条记录生成唯一雪花ID
                        depth.symbol,
                        "unknown",  # 交易所信息需要从depth对象中获取
                        depth.timestamp,
                        json.dumps(depth.bids),
                        json.dumps(depth.asks)
                    ))

                cursor.executemany(query, values)
                conn.commit()

                count = len(self._depth_buffer)
                logger.debug("Depth data flushed to database", count=count)

                # 清空缓存
                self._depth_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush depth data", error=str(e))
            # 保留数据以便重试

    async def _flush_loop(self) -> None:
        """定时刷新循环"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in flush loop", error=str(e))

    # 数据查询方法
    async def get_kline_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询K线数据"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, open, high, low, close, volume, turnover
                    FROM kline_data
                    WHERE symbol = %s AND timeframe = %s
                    AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp ASC
                    LIMIT %s
                """

                cursor.execute(query, (symbol, timeframe, start_time, end_time, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'open': float(row[1]),
                        'high': float(row[2]),
                        'low': float(row[3]),
                        'close': float(row[4]),
                        'volume': float(row[5]),
                        'turnover': float(row[6]) if row[6] else None
                    })

                return results

        except Exception as e:
            logger.error("Failed to query kline data", error=str(e))
            return []

    async def get_latest_kline(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """获取最新的K线数据"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT timestamp, open, high, low, close, volume, turnover
                    FROM kline_data
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """

                cursor.execute(query, (symbol, timeframe, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'open': float(row[1]),
                        'high': float(row[2]),
                        'low': float(row[3]),
                        'close': float(row[4]),
                        'volume': float(row[5]),
                        'turnover': float(row[6]) if row[6] else None
                    })

                return results

        except Exception as e:
            logger.error("Failed to query latest kline data", error=str(e))
            return []


# 全局数据存储实例
data_store_instance: Optional[DataStore] = None


def get_data_store() -> DataStore:
    """获取数据存储实例（单例模式）"""
    global data_store_instance
    if data_store_instance is None:
        data_store_instance = DataStore()
    return data_store_instance


async def init_data_store() -> DataStore:
    """初始化数据存储服务"""
    store = get_data_store()
    await store.start()
    return store


async def close_data_store() -> None:
    """关闭数据存储服务"""
    global data_store_instance
    if data_store_instance:
        await data_store_instance.stop()
        data_store_instance = None
