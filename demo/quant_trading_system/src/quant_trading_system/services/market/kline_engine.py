"""
K线合成引擎
===========

实现高性能的K线合成，支持：
- 多周期K线合成
- 增量更新
- 环形缓冲区存储
- 实时推送
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, BarArray, Tick
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.core.enums import DefaultTradingPair

logger = structlog.get_logger(__name__)


# K线回调类型
BarCallback = Callable[[Bar], Coroutine[Any, Any, None]]


@dataclass
class KLineBuffer:
    """
    K线环形缓冲区

    高效存储最近的K线数据
    """

    symbol: str
    exchange: str
    timeframe: KlineInterval
    max_size: int = 1000

    # 数据存储（使用预分配的数组）
    _data: np.ndarray = field(init=False)
    _index: int = field(default=0, init=False)
    _count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        # 预分配数组: [timestamp, open, high, low, close, volume, turnover]
        self._data = np.zeros((self.max_size, 7), dtype=np.float64)

    def append(self, bar: Bar) -> None:
        """添加K线"""
        self._data[self._index] = [
            bar.timestamp,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.turnover,
        ]

        self._index = (self._index + 1) % self.max_size
        self._count = min(self._count + 1, self.max_size)

    def update_last(self, bar: Bar) -> None:
        """更新最后一根K线"""
        if self._count == 0:
            self.append(bar)
            return

        # 获取最后一根K线的索引
        last_index = (self._index - 1) % self.max_size
        self._data[last_index] = [
            bar.timestamp,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.turnover,
        ]

    def get_last(self, n: int = 1) -> list[Bar]:
        """获取最后N根K线"""
        if self._count == 0:
            return []

        n = min(n, self._count)
        bars = []

        for i in range(n):
            idx = (self._index - 1 - i) % self.max_size
            row = self._data[idx]
            bars.append(Bar(
                symbol=self.symbol,
                exchange=self.exchange,
                timeframe=self.timeframe,
                timestamp=row[0],
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
                turnover=row[6],
            ))

        bars.reverse()
        return bars

    def get_array(self, n: int | None = None) -> BarArray:
        """获取K线数组"""
        if n is None:
            n = self._count

        n = min(n, self._count)

        if n == 0:
            return BarArray(
                symbol=self.symbol,
                exchange=self.exchange,
                timeframe=self.timeframe,
            )

        # 收集数据
        indices = [(self._index - 1 - i) % self.max_size for i in range(n)]
        indices.reverse()

        data = self._data[indices]

        return BarArray(
            symbol=self.symbol,
            exchange=self.exchange,
            timeframe=self.timeframe,
            timestamp=data[:, 0],
            open=data[:, 1],
            high=data[:, 2],
            low=data[:, 3],
            close=data[:, 4],
            volume=data[:, 5],
        )

    @property
    def count(self) -> int:
        return self._count

    @property
    def is_empty(self) -> bool:
        return self._count == 0


class KLineEngine:
    """
    K线合成引擎

    功能：
    - 从Tick数据合成多周期K线
    - 支持实时更新和历史补全
    - 高性能增量计算
    """

    def __init__(
        self,
        buffer_size: int = 1000,
    ) -> None:
        self.buffer_size = buffer_size

        # K线缓冲区: {symbol: {timeframe: KLineBuffer}}
        self._buffers: dict[str, dict[KlineInterval, KLineBuffer]] = defaultdict(dict)

        # 当前K线: {symbol: {timeframe: Bar}}
        self._current_bars: dict[str, dict[KlineInterval, Bar]] = defaultdict(dict)

        # 回调: {timeframe: [callbacks]}
        self._callbacks: dict[KlineInterval, list[BarCallback]] = defaultdict(list)

        # 通用回调（所有周期）
        self._general_callbacks: list[BarCallback] = []

        # 支持的周期
        self._timeframes: list[KlineInterval] = [
            KlineInterval.MIN_1,
            KlineInterval.MIN_5,
            KlineInterval.MIN_15,
            KlineInterval.MIN_30,
            KlineInterval.HOUR_1,
            KlineInterval.HOUR_4,
            KlineInterval.DAY_1,
        ]

        # 统计
        self._tick_count = 0
        self._bar_count = 0

        # 为默认交易对预创建缓冲区（确保 get_bars 在尚无 tick 时也能返回结构）
        self._init_default_buffers()

    def _init_default_buffers(self) -> None:
        """
        为 DefaultTradingPair 枚举中的交易对预创建缓冲区

        确保系统启动后 _buffers 就包含默认交易对的结构，
        即使尚未收到任何 tick 数据，get_bars 也能正确返回空列表而非找不到 key。
        """
        default_symbols = DefaultTradingPair.values()

        for symbol in default_symbols:
            # 与 process_tick / get_bars 一致的 key 格式：去掉 "/" 和 "-"
            buffer_key = symbol.replace("/", "").replace("-", "")

            for tf in self._timeframes:
                if tf not in self._buffers[buffer_key]:
                    self._buffers[buffer_key][tf] = KLineBuffer(
                        symbol=buffer_key,
                        exchange="binance",
                        timeframe=tf,
                        max_size=self.buffer_size,
                    )

        logger.info(
            "Initialized default trading pair buffers",
            symbols=default_symbols,
            timeframes=[tf.value for tf in self._timeframes],
        )

    def add_timeframe(self, timeframe: KlineInterval) -> None:
        """添加支持的周期"""
        if timeframe not in self._timeframes:
            self._timeframes.append(timeframe)

    def add_callback(
        self,
        callback: BarCallback,
        timeframe: KlineInterval | None = None,
    ) -> None:
        """添加K线回调"""
        if timeframe:
            self._callbacks[timeframe].append(callback)
        else:
            self._general_callbacks.append(callback)

    def remove_callback(
        self,
        callback: BarCallback,
        timeframe: KlineInterval | None = None,
    ) -> None:
        """移除K线回调"""
        if timeframe:
            if callback in self._callbacks[timeframe]:
                self._callbacks[timeframe].remove(callback)
        else:
            if callback in self._general_callbacks:
                self._general_callbacks.remove(callback)

    async def process_tick(self, tick: Tick) -> None:
        """
        处理Tick数据

        根据Tick数据更新所有周期的K线
        """
        self._tick_count += 1
        symbol = tick.symbol.replace("/", "").replace("-", "")
        exchange = tick.exchange
        timestamp = tick.timestamp
        price = tick.last_price
        volume = tick.volume

        # 更新每个周期的K线
        for timeframe in self._timeframes:
            await self._update_bar(
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                timestamp=timestamp,
                price=price,
                volume=volume,
            )

    async def _update_bar(
        self,
        symbol: str,
        exchange: str,
        timeframe: KlineInterval,
        timestamp: float,
        price: float,
        volume: float,
    ) -> None:
        """更新单个周期的K线"""

        # 计算K线开始时间
        bar_start = self._get_bar_start_time(timestamp, timeframe)

        # 获取或创建缓冲区
        if timeframe not in self._buffers[symbol]:
            self._buffers[symbol][timeframe] = KLineBuffer(
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                max_size=self.buffer_size,
            )

        buffer = self._buffers[symbol][timeframe]

        # 获取当前K线
        current_bar = self._current_bars[symbol].get(timeframe)

        if current_bar is None or current_bar.timestamp != bar_start:
            # 新的K线周期

            # 保存旧K线
            if current_bar is not None:
                current_bar.is_closed = True
                buffer.append(current_bar)
                self._bar_count += 1
                await self._notify_bar(current_bar)

            # 创建新K线
            new_bar = Bar(
                symbol=symbol,
                exchange=exchange,
                timeframe=timeframe,
                timestamp=bar_start,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume,
                is_closed=False,
            )
            self._current_bars[symbol][timeframe] = new_bar

        else:
            # 更新当前K线
            current_bar.high = max(current_bar.high, price)
            current_bar.low = min(current_bar.low, price)
            current_bar.close = price
            current_bar.volume += volume

    def _get_bar_start_time(self, timestamp: float, timeframe: KlineInterval) -> float:
        """计算K线开始时间"""
        seconds = timeframe.seconds
        if seconds == 0:
            return timestamp

        # 转换为秒
        ts_seconds = timestamp / 1000

        # 计算周期开始时间
        bar_start_seconds = (int(ts_seconds) // seconds) * seconds

        return bar_start_seconds * 1000

    async def _notify_bar(self, bar: Bar) -> None:
        """通知K线回调"""
        # 特定周期回调
        callbacks = self._callbacks.get(bar.timeframe, [])
        if callbacks:
            tasks = [cb(bar) for cb in callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

        # 通用回调
        if self._general_callbacks:
            tasks = [cb(bar) for cb in self._general_callbacks]
            await asyncio.gather(*tasks, return_exceptions=True)

    def update_bar_from_ws(self, symbol: str, bar: Bar) -> None:
        """
        使用交易所WebSocket推送的K线数据直接更新缓冲区

        与 process_tick 合成K线不同，这里直接使用交易所推送的完整K线数据，
        精度更高（交易所已经在服务端完成了聚合计算）。

        Args:
            symbol: 交易对（已去除 / 和 - 的格式）
            bar: 交易所推送的K线数据
        """
        timeframe = bar.timeframe

        # 确保缓冲区存在
        if timeframe not in self._buffers[symbol]:
            self._buffers[symbol][timeframe] = KLineBuffer(
                symbol=symbol,
                exchange=bar.exchange,
                timeframe=timeframe,
                max_size=self.buffer_size,
            )

        buffer = self._buffers[symbol][timeframe]

        if bar.is_closed:
            # K线已关闭：写入缓冲区并清除 current_bar
            buffer.append(bar)
            self._bar_count += 1

            # 清除 current_bar（如果是同一根K线）
            current = self._current_bars.get(symbol, {}).get(timeframe)
            if current is not None and current.timestamp == bar.timestamp:
                del self._current_bars[symbol][timeframe]
        else:
            # K线未关闭：更新 current_bar
            self._current_bars[symbol][timeframe] = bar

    def get_bars(
        self,
        symbol: str,
        timeframe: KlineInterval,
        limit: int | None = None,
    ) -> list[Bar]:
        """获取K线列表（包含已关闭K线 + 当前未完成K线）"""

        symbol = symbol.replace("/", "").replace("-", "")

        bars: list[Bar] = []

        # 1. 从缓冲区获取已关闭的K线
        if symbol in self._buffers and timeframe in self._buffers[symbol]:
            buffer = self._buffers[symbol][timeframe]
            bars = buffer.get_last(limit or buffer.count)

        # 2. 追加当前未完成的K线（如果存在）
        current_bar = self._current_bars.get(symbol, {}).get(timeframe)
        if current_bar is not None:
            bars.append(current_bar)

        # 3. 如果指定了 limit，截取最后 limit 条
        if limit and len(bars) > limit:
            bars = bars[-limit:]

        return bars

    def get_bar_array(
        self,
        symbol: str,
        timeframe: KlineInterval,
        limit: int | None = None,
    ) -> BarArray:
        """获取K线数组"""
        symbol = symbol.replace("/", "").replace("-", "")

        if symbol not in self._buffers:
            return BarArray(
                symbol=symbol,
                exchange="",
                timeframe=timeframe,
            )

        if timeframe not in self._buffers[symbol]:
            return BarArray(
                symbol=symbol,
                exchange="",
                timeframe=timeframe,
            )

        return self._buffers[symbol][timeframe].get_array(limit)

    def get_current_bar(
        self,
        symbol: str,
        timeframe: KlineInterval,
    ) -> Bar | None:
        """获取当前未完成的K线"""
        return self._current_bars.get(symbol, {}).get(timeframe)

    def get_last_bar(
        self,
        symbol: str,
        timeframe: KlineInterval,
    ) -> Bar | None:
        """获取最后一根已完成的K线"""
        bars = self.get_bars(symbol, timeframe, limit=1)
        return bars[0] if bars else None

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "tick_count": self._tick_count,
            "bar_count": self._bar_count,
            "symbols": list(self._buffers.keys()),
            "timeframes": [tf.value for tf in self._timeframes],
        }

    def clear(self) -> None:
        """清除所有数据"""
        self._buffers.clear()
        self._current_bars.clear()
        self._tick_count = 0
        self._bar_count = 0

    async def load_history(
        self,
        symbols: list[str] | None = None,
        timeframes: list[KlineInterval] | None = None,
        limit: int = 500,
        exchange: str = "binance",
        source: str = "exchange",
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        拉取历史K线数据，预加载到 _buffers 中。

        支持两种数据源：
        - exchange: 从交易所 REST API 拉取（生产环境）
        - database: 从数据库加载（开发环境）

        Args:
            symbols: 交易对列表，为 None 则使用 DefaultTradingPair 配置
            timeframes: 时间周期列表，为 None 则使用 [M1, M5, M15, H1]
            limit: 每个周期拉取的K线数量
            exchange: 交易所名称
            source: 数据源，"exchange" 从交易所拉取，"database" 从数据库加载
            save_to_db: 从交易所拉取后是否同时保存到数据库（用于补充发版期间的数据缺口）

        Returns:
            各交易对加载的K线数量统计
        """
        if symbols is None:
            symbols = DefaultTradingPair.values()

        if timeframes is None:
            timeframes = ([KlineInterval.SEC_1,
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
                          KlineInterval.MONTH_1])

        stats: dict[str, int] = {}

        if source == "database":
            stats = await self._load_history_from_database(
                symbols=symbols,
                timeframes=timeframes,
                limit=limit,
                exchange=exchange,
            )
        else:
            stats = await self._load_history_from_exchange(
                symbols=symbols,
                timeframes=timeframes,
                limit=limit,
                exchange=exchange,
                save_to_db=save_to_db,
            )

        logger.info("Historical kline data loaded", stats=stats, source=source)
        return stats

    async def _load_history_from_database(
        self,
        symbols: list[str],
        timeframes: list[KlineInterval],
        limit: int,
        exchange: str,
    ) -> dict[str, int]:
        """
        从数据库加载历史K线数据到内存缓冲区（开发环境使用）。

        Args:
            symbols: 交易对列表
            timeframes: 时间周期列表
            limit: 每个周期最多加载的K线数量
            exchange: 交易所名称

        Returns:
            各交易对加载的K线数量统计
        """
        from datetime import datetime, timedelta
        from quant_trading_system.services.database.data_query import get_data_query_service

        stats: dict[str, int] = {}
        query_service = get_data_query_service()

        # 查询时间范围：从当前时间往前推足够的时间窗口
        end_time = datetime.utcnow()
        # 根据最大周期和limit估算需要的时间范围（以1小时周期 * limit 为上限）
        start_time = end_time - timedelta(hours=limit)

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
                    if tf not in self._buffers[buffer_key]:
                        self._buffers[buffer_key][tf] = KLineBuffer(
                            symbol=buffer_key,
                            exchange=exchange,
                            timeframe=tf,
                            max_size=self.buffer_size,
                        )

                    buffer = self._buffers[buffer_key][tf]

                    # 将数据库中的K线逐条写入缓冲区
                    # 预先将 datetime64[ms] 数组转为毫秒级整数时间戳，避免逐条 float() 转换报错
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
                        self._bar_count += 1
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
                        error=str(e),
                    )
                    continue

            stats[symbol] = symbol_count

        return stats

    async def _load_history_from_exchange(
        self,
        symbols: list[str],
        timeframes: list[KlineInterval],
        limit: int,
        exchange: str,
        save_to_db: bool = False,
    ) -> dict[str, int]:
        """
        从交易所 REST API 拉取历史K线数据到内存缓冲区。
        生产环境下同时保存到数据库，以补充发版期间实时行情同步暂停的数据缺口。

        Args:
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

        # 如果需要保存到数据库，获取数据存储服务
        data_store = None
        if save_to_db:
            try:
                from quant_trading_system.services.database.data_store import get_data_store
                data_store = get_data_store()
                logger.info("Will save fetched kline data to database for gap filling")
            except Exception as e:
                logger.warning(
                    "Failed to get data store, skipping save to database",
                    error=str(e),
                )

        loop = asyncio.get_event_loop()

        with create_rest_client(exchange, market_type="spot") as api:
            for symbol in symbols:
                symbol_count = 0
                # 去掉 "/" 和 "-" 得到 _buffers 的 key（与 process_tick 一致）
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
                        if tf not in self._buffers[buffer_key]:
                            self._buffers[buffer_key][tf] = KLineBuffer(
                                symbol=buffer_key,
                                exchange=exchange,
                                timeframe=tf,
                                max_size=self.buffer_size,
                            )

                        buffer = self._buffers[buffer_key][tf]

                        # 将历史 K 线逐条写入缓冲区，并可选保存到数据库
                        # 预先将 datetime64[ms] 数组转为毫秒级整数时间戳，避免逐条 float() 转换报错
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
                            self._bar_count += 1
                            symbol_count += 1

                            # 生产环境：同时保存到数据库，补充发版期间的数据缺口
                            if data_store is not None:
                                try:
                                    await data_store.store_kline(bar)
                                except Exception as store_err:
                                    logger.warning(
                                        "Failed to save kline to database",
                                        symbol=buffer_key,
                                        timeframe=tf.value,
                                        error=str(store_err),
                                    )

                        logger.debug(
                            "Loaded historical klines from exchange",
                            symbol=symbol,
                            timeframe=tf.value,
                            count=len(bar_array),
                            saved_to_db=data_store is not None,
                        )

                    except Exception as e:
                        logger.error(
                            "Failed to load historical klines",
                            symbol=symbol,
                            timeframe=tf.value,
                            error=str(e),
                        )
                        continue

                stats[symbol] = symbol_count

        # 如果保存了数据到数据库，确保缓冲区刷新
        if data_store is not None:
            try:
                await data_store.flush_all()
                logger.info("Flushed kline data to database after history loading")
            except Exception as e:
                logger.warning("Failed to flush kline data to database", error=str(e))

        return stats


class KLineAggregator:
    """
    K线聚合器

    从小周期K线合成大周期K线
    """

    def __init__(self) -> None:
        self._buffers: dict[str, dict[KlineInterval, list[Bar]]] = defaultdict(dict)

    def aggregate(
        self,
        bars: list[Bar],
        target_timeframe: KlineInterval,
    ) -> list[Bar]:
        """
        聚合K线

        Args:
            bars: 源K线列表
            target_timeframe: 目标周期

        Returns:
            聚合后的K线列表
        """
        if not bars:
            return []

        source_tf = bars[0].timeframe
        target_seconds = target_timeframe.seconds

        if target_seconds <= source_tf.seconds:
            return bars  # 无需聚合

        # 按目标周期分组
        grouped: dict[float, list[Bar]] = defaultdict(list)

        for bar in bars:
            # 计算目标周期开始时间
            bar_start = (int(bar.timestamp / 1000) // target_seconds) * target_seconds * 1000
            grouped[bar_start].append(bar)

        # 合成K线
        result = []
        for bar_start, group_bars in sorted(grouped.items()):
            if not group_bars:
                continue

            agg_bar = Bar(
                symbol=group_bars[0].symbol,
                exchange=group_bars[0].exchange,
                timeframe=target_timeframe,
                timestamp=bar_start,
                open=group_bars[0].open,
                high=max(b.high for b in group_bars),
                low=min(b.low for b in group_bars),
                close=group_bars[-1].close,
                volume=sum(b.volume for b in group_bars),
                turnover=sum(b.turnover for b in group_bars),
                is_closed=True,
            )
            result.append(agg_bar)

        return result
