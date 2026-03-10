"""
K线历史数据加载器
==================

从交易所或数据库加载历史K线数据到内存缓冲区。
从 KLineEngine 中剥离，职责单一。
"""

import asyncio
from typing import Any

import numpy as np
import structlog

from quant_trading_system.models.market import Bar
from quant_trading_system.core.enums import KlineInterval, DefaultTradingPair
from quant_trading_system.services.market.kline_engine import KLineBuffer

logger = structlog.get_logger(__name__)


class KLineHistoryLoader:
    """
    K线历史数据加载器

    负责从交易所或数据库加载历史K线数据到指定的缓冲区中。
    与 KLineEngine 解耦，由 MarketService 协调调用。
    """

    def __init__(self, buffer_size: int = 1000) -> None:
        self.buffer_size = buffer_size

    async def load_history(
        self,
        buffers: dict[str, dict[KlineInterval, KLineBuffer]],
        symbols: list[str] | None = None,
        timeframes: list[KlineInterval] | None = None,
        limit: int = 500,
        exchange: str = "binance",
        source: str = "exchange",
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        拉取历史K线数据，预加载到指定的 buffers 中。

        支持两种数据源：
        - exchange: 从交易所 REST API 拉取（生产环境）
        - database: 从数据库加载（开发环境）

        Args:
            buffers: KLineEngine 的缓冲区引用，由外部传入
            symbols: 交易对列表，为 None 则使用 DefaultTradingPair 配置
            timeframes: 时间周期列表
            limit: 每个周期拉取的K线数量
            exchange: 交易所名称
            source: 数据源，"exchange" 从交易所拉取，"database" 从数据库加载
            save_to_db: 从交易所拉取后是否同时保存到数据库

        Returns:
            各交易对加载的K线数量统计
        """
        if symbols is None:
            symbols = DefaultTradingPair.values()

        if timeframes is None:
            timeframes = [
                KlineInterval.SEC_1,
                KlineInterval.MIN_1,
                KlineInterval.MIN_3,
                KlineInterval.MIN_5,
                KlineInterval.MIN_15,
                KlineInterval.MIN_30,
                KlineInterval.HOUR_1,
                KlineInterval.HOUR_2,
                KlineInterval.HOUR_4,
                KlineInterval.HOUR_6,
                KlineInterval.HOUR_8,
                KlineInterval.HOUR_12,
                KlineInterval.DAY_1,
                KlineInterval.DAY_3,
                KlineInterval.WEEK_1,
                KlineInterval.MONTH_1,
            ]

        if source == "database":
            stats = await self._load_from_database(
                buffers=buffers,
                symbols=symbols,
                timeframes=timeframes,
                limit=limit,
                exchange=exchange,
            )
        else:
            stats = await self._load_from_exchange(
                buffers=buffers,
                symbols=symbols,
                timeframes=timeframes,
                limit=limit,
                exchange=exchange,
                save_to_db=save_to_db,
            )

        logger.info("Historical kline data loaded", stats=stats, source=source)
        return stats

    async def _load_from_database(
        self,
        buffers: dict[str, dict[KlineInterval, KLineBuffer]],
        symbols: list[str],
        timeframes: list[KlineInterval],
        limit: int,
        exchange: str,
    ) -> dict[str, int]:
        """
        从数据库加载历史K线数据到内存缓冲区（开发环境使用）。

        Args:
            buffers: 缓冲区字典引用
            symbols: 交易对列表
            timeframes: 时间周期列表
            limit: 每个周期最多加载的K线数量
            exchange: 交易所名称

        Returns:
            各交易对加载的K线数量统计
        """
        from datetime import datetime, timedelta
        from quant_trading_system.services.market.market_data_reader import get_market_data_reader

        stats: dict[str, int] = {}
        query_service = get_market_data_reader()

        # 查询时间范围：根据周期的秒数 × limit 计算需要的时间窗口
        end_time = datetime.utcnow()
        max_tf_seconds = max(tf.seconds for tf in timeframes) if timeframes else 3600
        window_seconds = max_tf_seconds * limit
        start_time = end_time - timedelta(seconds=window_seconds)

        bar_count = 0

        for symbol in symbols:
            symbol_count = 0
            buffer_key = symbol.replace("/", "").replace("-", "")

            for tf in timeframes:
                try:
                    bar_array = await query_service.get_kline_data(
                        symbol=buffer_key,
                        timeframe=tf,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit,
                    )

                    if bar_array is None or len(bar_array) == 0:
                        logger.warning(
                            "No kline data in database",
                            symbol=symbol,
                            timeframe=tf.value,
                        )
                        continue

                    # 确保缓冲区存在
                    if tf not in buffers[buffer_key]:
                        buffers[buffer_key][tf] = KLineBuffer(
                            symbol=buffer_key,
                            exchange=exchange,
                            timeframe=tf,
                            max_size=self.buffer_size,
                        )

                    buffer = buffers[buffer_key][tf]

                    # 将数据库中的K线逐条写入缓冲区
                    ts_ms = bar_array.timestamp.astype("datetime64[ms]").astype(np.int64)
                    for i in range(len(bar_array)):
                        bar = Bar(
                            symbol=buffer_key,
                            exchange=exchange,
                            timeframe=tf,
                            timestamp=float(ts_ms[i]),
                            open=float(bar_array.open[i]),
                            high=float(bar_array.high[i]),
                            low=float(bar_array.low[i]),
                            close=float(bar_array.close[i]),
                            volume=float(bar_array.volume[i]),
                            is_closed=True,
                        )
                        buffer.append(bar)
                        bar_count += 1
                        symbol_count += 1

                    logger.debug(
                        "Loaded historical klines from database",
                        symbol=symbol,
                        timeframe=tf.value,
                        count=len(bar_array),
                    )

                except Exception as e:
                    logger.error(
                        "Failed to load historical klines from database",
                        symbol=symbol,
                        timeframe=tf.value,
                        exc_info=True,
                    )
                    continue

            stats[symbol] = symbol_count

        return stats

    async def _load_from_exchange(
        self,
        buffers: dict[str, dict[KlineInterval, KLineBuffer]],
        symbols: list[str],
        timeframes: list[KlineInterval],
        limit: int,
        exchange: str,
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        从交易所 REST API 拉取历史K线数据到内存缓冲区。

        Args:
            buffers: 缓冲区字典引用
            symbols: 交易对列表
            timeframes: 时间周期列表
            limit: 每个周期拉取的K线数量
            exchange: 交易所名称
            save_to_db: 是否同时保存到数据库

        Returns:
            各交易对加载的K线数量统计
        """
        stats: dict[str, int] = {}

        # 根据交易所选择 API 客户端
        if exchange == "binance":
            from quant_trading_system.exchange_adapter.factory import create_rest_client
        else:
            logger.error(f"Unsupported exchange for history loading: {exchange}")
            return stats

        # 如果需要保存到数据库，获取数据写入服务
        data_writer = None
        if save_to_db:
            try:
                from quant_trading_system.services.market.market_data_writer import get_market_data_writer
                data_writer = get_market_data_writer()
                logger.info("Will save fetched kline data to database for gap filling")
            except Exception as e:
                logger.warning(
                    "Failed to get data writer, skipping save to database",
                    exc_info=True,
                )

        loop = asyncio.get_event_loop()
        bar_count = 0

        with create_rest_client(exchange, market_type="spot") as api:
            for symbol in symbols:
                symbol_count = 0
                buffer_key = symbol.replace("/", "").replace("-", "")

                for tf in timeframes:
                    try:
                        # 在线程池中执行同步 API 调用
                        bar_array = await loop.run_in_executor(
                            None,
                            lambda s=symbol, t=tf: api.fetch_klines(
                                symbol=s,
                                timeframe=t,
                                limit=limit,
                            ),
                        )

                        if bar_array is None or len(bar_array) == 0:
                            continue

                        # 确保缓冲区存在
                        if tf not in buffers[buffer_key]:
                            buffers[buffer_key][tf] = KLineBuffer(
                                symbol=buffer_key,
                                exchange=exchange,
                                timeframe=tf,
                                max_size=self.buffer_size,
                            )

                        buffer = buffers[buffer_key][tf]

                        # 将历史 K 线逐条写入缓冲区
                        ts_ms = bar_array.timestamp.astype("datetime64[ms]").astype(np.int64)
                        for i in range(len(bar_array)):
                            bar = Bar(
                                symbol=buffer_key,
                                exchange=exchange,
                                timeframe=tf,
                                timestamp=float(ts_ms[i]),
                                open=float(bar_array.open[i]),
                                high=float(bar_array.high[i]),
                                low=float(bar_array.low[i]),
                                close=float(bar_array.close[i]),
                                volume=float(bar_array.volume[i]),
                                is_closed=True,
                            )
                            buffer.append(bar)
                            bar_count += 1
                            symbol_count += 1

                            # 生产环境：同时保存到数据库
                            if data_writer is not None:
                                try:
                                    await data_writer.store_kline(bar)
                                except Exception as store_err:
                                    logger.warning(
                                        "Failed to save kline to database",
                                        symbol=buffer_key,
                                        timeframe=tf.value,
                                        exc_info=True,
                                    )

                        logger.debug(
                            "Loaded historical klines from exchange",
                            symbol=symbol,
                            timeframe=tf.value,
                            count=len(bar_array),
                            saved_to_db=data_writer is not None,
                        )

                    except Exception as e:
                        logger.error(
                            "Failed to load historical klines",
                            symbol=symbol,
                            timeframe=tf.value,
                            exc_info=True,
                        )
                        continue

                stats[symbol] = symbol_count

        # 如果保存了数据到数据库，确保缓冲区刷新
        if data_writer is not None:
            try:
                await data_writer.flush_all()
                logger.info("Flushed kline data to database after history loading")
            except Exception as e:
                logger.warning("Failed to flush kline data to database", exc_info=True)

        return stats
