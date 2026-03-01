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
from .database import get_async_database
from quant_trading_system.core.snowflake import generate_snowflake_id

logger = structlog.get_logger(__name__)


class DataStore:
    """数据存储服务 - 异步版本"""

    def __init__(self, batch_size: int = 1000, flush_interval: float = 5.0):
        self.db = get_async_database()
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

        # 确保数据库已连接
        if not self.db.is_connected:
            logger.info("Database not connected, connecting now...")
            await self.db.connect()

        self._running = True

        # 启动定时刷新任务
        self._flush_task = asyncio.create_task(self._flush_loop())

        logger.info("Async data store service started")

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

        logger.info("Async data store service stopped")

    async def store_kline(self, bar: Bar) -> None:
        """存储K线数据 - 异步版本"""
        self._kline_buffer.append(bar)

        # 如果达到批量大小，立即刷新
        if len(self._kline_buffer) >= self.batch_size:
            await self._flush_kline()

    async def store_tick(self, tick: Tick) -> None:
        """存储实时行情数据 - 异步版本"""
        self._tick_buffer.append(tick)

        # 如果达到批量大小，立即刷新
        if len(self._tick_buffer) >= self.batch_size:
            await self._flush_tick()

    async def store_depth(self, depth: Depth) -> None:
        """存储深度数据 - 异步版本"""
        self._depth_buffer.append(depth)

        # 如果达到批量大小，立即刷新
        if len(self._depth_buffer) >= self.batch_size:
            await self._flush_depth()

    async def flush_all(self) -> None:
        """刷新所有缓存数据到数据库 - 异步版本"""
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
        """刷新K线数据到数据库 - 异步版本"""
        if not self._kline_buffer:
            return

        try:
            # 准备批量插入数据
            values = []
            for bar in self._kline_buffer:
                turnover = bar.volume * bar.close if bar.volume and bar.close else 0.0
                # 将毫秒时间戳转换为datetime对象，数据库timestamp列需要datetime类型
                bar_datetime = datetime.fromtimestamp(bar.timestamp / 1000)
                values.append({
                    "id": generate_snowflake_id(),
                    "symbol": bar.symbol,
                    "exchange": bar.exchange,
                    "timeframe": bar.timeframe.value,
                    "timestamp": bar_datetime,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume),
                    "turnover": float(turnover),
                    "is_closed": bar.is_closed
                })

            # 执行异步批量插入
            query = """
                INSERT INTO kline_data
                (id, symbol, exchange, timeframe, timestamp, open, high, low, close, volume, turnover, is_closed)
                VALUES (:id, :symbol, :exchange, :timeframe, :timestamp, :open, :high, :low, :close, :volume, :turnover, :is_closed)
                ON CONFLICT (symbol, exchange, timeframe, timestamp) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume,
                    turnover = EXCLUDED.turnover,
                    is_closed = EXCLUDED.is_closed,
                    created_at = EXCLUDED.created_at
            """

            rowcount = await self.db.execute_many(query, values)

            if rowcount > 0:
                logger.debug("Kline data processed (inserted or updated)", count=rowcount)
            else:
                logger.debug("No kline data processed (all were duplicates with no changes)")

            # 清空缓存
            self._kline_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush kline data", error=str(e))
            # 保留数据以便重试

    async def _flush_tick(self) -> None:
        """刷新实时行情数据到数据库 - 异步版本"""
        if not self._tick_buffer:
            return

        try:
            values = []
            for tick in self._tick_buffer:
                # 将毫秒时间戳转换为datetime对象，数据库timestamp列需要datetime类型
                tick_datetime = datetime.fromtimestamp(tick.timestamp / 1000)
                values.append({
                    "id": generate_snowflake_id(),
                    "symbol": tick.symbol,
                    "exchange": tick.exchange,
                    "timestamp": tick_datetime,
                    "price": float(tick.price),
                    "volume": float(tick.volume),
                    "bid_price": float(tick.bid) if tick.bid else None,
                    "ask_price": float(tick.ask) if tick.ask else None,
                    "bid_size": None,
                    "ask_size": None
                })

            query = """
                INSERT INTO tick_data
                (id, symbol, exchange, timestamp, price, volume, bid_price, ask_price, bid_size, ask_size)
                VALUES (:id, :symbol, :exchange, :timestamp, :price, :volume, :bid_price, :ask_price, :bid_size, :ask_size)
                ON CONFLICT (symbol, exchange, timestamp) DO UPDATE SET
                    price = EXCLUDED.price,
                    volume = EXCLUDED.volume,
                    bid_price = EXCLUDED.bid_price,
                    ask_price = EXCLUDED.ask_price,
                    bid_size = EXCLUDED.bid_size,
                    ask_size = EXCLUDED.ask_size,
                    created_at = EXCLUDED.created_at
            """

            rowcount = await self.db.execute_many(query, values)

            if rowcount > 0:
                logger.debug("Tick data processed (inserted or updated)", count=rowcount)
            else:
                logger.debug("No tick data processed (all were duplicates with no changes)")

            self._tick_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush tick data", error=str(e))

    async def _flush_depth(self) -> None:
        """刷新深度数据到数据库 - 异步版本"""
        if not self._depth_buffer:
            return

        try:
            values = []
            for depth in self._depth_buffer:
                # Depth.timestamp 已经是 datetime 类型，直接使用
                values.append({
                    "id": generate_snowflake_id(),
                    "symbol": depth.symbol,
                    "exchange": depth.exchange,
                    "timestamp": depth.timestamp,
                    "bids": json.dumps([d.to_list() for d in depth.bids]) if depth.bids else None,
                    "asks": json.dumps([d.to_list() for d in depth.asks]) if depth.asks else None,
                    "sequence": depth.sequence
                })

            query = """
                INSERT INTO depth_data
                (id, symbol, exchange, timestamp, bids, asks, sequence)
                VALUES (:id, :symbol, :exchange, :timestamp, :bids, :asks, :sequence)
                ON CONFLICT (symbol, exchange, timestamp) DO UPDATE SET
                    bids = EXCLUDED.bids,
                    asks = EXCLUDED.asks,
                    sequence = EXCLUDED.sequence,
                    created_at = EXCLUDED.created_at
            """

            rowcount = await self.db.execute_many(query, values)

            if rowcount > 0:
                logger.debug("Depth data processed (inserted or updated)", count=rowcount)
            else:
                logger.debug("No depth data processed (all were duplicates with no changes)")

            self._depth_buffer.clear()

        except Exception as e:
            logger.error("Failed to flush depth data", error=str(e))

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

    # 数据查询方法 - 异步版本
    async def get_kline_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """查询K线数据 - 异步版本"""
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume, turnover
                FROM kline_data
                WHERE symbol = $1 AND timeframe = $2
                AND timestamp >= $3 AND timestamp <= $4
                ORDER BY timestamp ASC
                LIMIT $5
            """

            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_time': start_time,
                'end_time': end_time,
                'limit': limit
            }

            results = await self.db.execute_query(query, params)
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
        """获取最新的K线数据 - 异步版本"""
        try:
            query = """
                SELECT timestamp, open, high, low, close, volume, turnover
                FROM kline_data
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC
                LIMIT $3
            """

            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'limit': limit
            }

            results = await self.db.execute_query(query, params)
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
