"""
历史K线数据同步器
==================

从交易所 REST API 拉取历史K线数据，通过事件总线发布给订阅器处理。

设计思路：
- 按传入的时间区间，智能分批拉取（币安 API 单次最多 1000 条）
- 根据 K线周期自动计算每批的时间窗口大小
- 拉取到数据后，模仿实时行情的事件机制，通过 MarketEventBus 发布 HISTORICAL_KLINE 事件
- 订阅了 HISTORICAL_KLINE 事件的订阅器（如 DatabaseSubscriber）自动处理存储
"""

import asyncio
import time
from typing import Any

import structlog

from quant_trading_system.core.enums import KlineInterval, DefaultTradingPair
from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
)
from quant_trading_system.exchange_adapter.utils import TimeUtils
from quant_trading_system.models.market import Bar

logger = structlog.get_logger(__name__)

# 币安 API 单次最大返回条数
BINANCE_MAX_LIMIT = 10000

# 默认批次间的请求间隔（秒），避免触发限流
DEFAULT_BATCH_DELAY = 0.3

class HistoricalKlineSyncer:
    """
    历史K线数据同步器

    核心能力：
    1. 按时间区间智能分批拉取历史K线数据
    2. 通过事件总线发布数据，与实时行情共用同一套订阅器体系
    3. 支持进度回调与统计

    工作流程：
        ┌──────────────────┐
        │  调用 sync()     │
        │  传入时间区间     │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  计算分批策略     │
        │  (每批最多1000条) │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  循环拉取每批数据  │◄──── BinanceAPI.fetch_klines()
        │                   │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  转换为 Bar 对象  │
        │  + 发布事件       │───── MarketEventBus.publish()
        └────────┬─────────┘      (HISTORICAL_KLINE 事件)
                 │
        ┌────────▼─────────┐
        │  订阅器自动处理   │
        │  DatabaseSubscriber │
        │  等处理存储/转发   │
        └──────────────────┘
    """

    def __init__(
        self,
        binance_api: Any,
        event_bus: MarketEventBus,
    ) -> None:
        """
        初始化历史K线同步器

        Args:
            binance_api: 币安 REST API 客户端
            event_bus: 行情事件总线
        """
        self._api = binance_api
        self._event_bus = event_bus
        self._batch_delay = DEFAULT_BATCH_DELAY
        self._batch_size = BINANCE_MAX_LIMIT

        # 同步统计
        self._stats: dict[str, Any] = {
            "total_synced": 0,
            "total_batches": 0,
            "total_bars": 0,
            "errors": 0,
        }

    # ─── 公开接口 ───────────────────────────────────────────────

    def close(self) -> None:
        """
        关闭同步器，释放底层 BinanceAPI 的 HTTP 客户端资源
        """
        if self._api:
            self._api.close()
            logger.info("历史K线同步器已关闭")

    async def sync_on_startup(self, start_time: str) -> None:
        """
        服务启动时自动执行的历史数据同步
        """
        from datetime import datetime, timezone

        now_utc = datetime.now(timezone.utc)
        end_time = now_utc.strftime("%Y-%m-%d %H:%M:%S")

        # 构建批量同步任务
        tasks: list[dict[str, Any]] = []
        for symbol in DefaultTradingPair.values():
            for timeframe in KlineInterval:
                tasks.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start_time": start_time,
                    "end_time": end_time,
                })

        if not tasks:
            logger.warning("启动时同步任务列表为空，跳过")
            return

        try:
            results = await self._sync_multiple(tasks, concurrency=1)
            total = sum(v for v in results.values() if v > 0)
            logger.info(
                "启动时历史数据同步完成",
                results=results,
                total_bars=total,
            )
        except Exception as e:
            logger.exception("启动时历史数据同步失败", error=str(e))

    async def sync(
        self,
        symbol: str,
        timeframe: KlineInterval,
        start_time: str,
        end_time: str | None = None,
        on_progress: Any = None,
    ) -> int:
        """
        同步指定交易对和周期的历史K线数据

        智能分批策略：
        - 根据 K线周期和 batch_size 计算每批覆盖的时间窗口
        - 自动循环拉取直到覆盖整个时间区间
        - 每批拉取后立即通过事件总线发布给订阅器

        Args:
            symbol: 交易对，如 "BTCUSDT" 或 "BTC/USDT"
            timeframe: K线周期（KlineInterval 枚举）
            start_time: 开始时间，格式 "YYYY-MM-DD" 或 "YYYY-MM-DD HH:MM:SS"
            end_time: 结束时间，格式同上；为空则同步到当前时间
            on_progress: 可选的进度回调函数，签名: (batch_index, total_bars, is_done) -> None

        Returns:
            总共同步的K线条数
        """
        # 格式化交易对
        symbol_formatted = symbol.replace("/", "").upper()
        interval_str = timeframe.value

        # 解析时间范围
        start_ms = TimeUtils.parse_time_string(start_time)
        end_ms = TimeUtils.parse_time_string(end_time) if end_time else int(time.time() * 1000)

        # 获取K线周期对应的毫秒数（用于推进时间窗口）
        interval_ms = KlineInterval.from_str(interval_str)
        if not interval_ms or interval_ms is None:
            raise ValueError(f"不支持的K线周期: {interval_str}")

        logger.info(
            "开始同步历史K线",
            symbol=symbol_formatted,
            timeframe=interval_str,
            start_time=start_time,
            end_time=end_time or "now",
            batch_size=self._batch_size,
        )

        total_bars = 0
        batch_index = 0
        current_start_ms = start_ms

        while current_start_ms < end_ms:
            batch_index += 1

            try:
                # 使用 BinanceAPI 拉取一批数据
                # 只传 start_time + 总 end_time + limit=batch_size，
                # 让 fetch_klines 内部分页逻辑自行控制（拉满 limit 条即停）
                loop = asyncio.get_running_loop()
                bar_array = await loop.run_in_executor(
                    None,
                    lambda s=current_start_ms: self._api.fetch_klines(
                        symbol=symbol_formatted,
                        timeframe=timeframe,
                        start_time=self._ms_to_time_string(s),
                        end_time=self._ms_to_time_string(end_ms),
                        limit=self._batch_size,
                    ),
                )

                batch_count = len(bar_array)

                if batch_count == 0:
                    logger.debug(
                        "批次无数据，同步结束",
                        batch=batch_index,
                        start_ms=current_start_ms,
                    )
                    break

                # 将 BarArray 转换为 Bar 对象列表，通过事件总线发布
                bars = self._bar_array_to_bars(bar_array, symbol_formatted, timeframe)

                # 通过事件总线发布 HISTORICAL_KLINE 事件
                await self._publish_bars(bars, symbol_formatted)

                total_bars += batch_count

                # 使用最后一条数据的时间戳推进起始位置
                last_bar = bars[-1]
                last_ts = int(last_bar.timestamp)

                logger.info(
                    "批次同步完成",
                    batch=batch_index,
                    batch_bars=batch_count,
                    total_bars=total_bars,
                    symbol=symbol_formatted,
                    timeframe=interval_str,
                    progress=f"{min(100, int((last_ts - start_ms) / max(1, end_ms - start_ms) * 100))}%",
                )

                # 进度回调
                if on_progress:
                    try:
                        if asyncio.iscoroutinefunction(on_progress):
                            await on_progress(batch_index, total_bars, False)
                        else:
                            on_progress(batch_index, total_bars, False)
                    except Exception as e:
                        logger.exception("进度回调异常", error=str(e))

                # 更新起始位置：最后一条时间戳 + 1 个周期，避免重复
                current_start_ms = last_ts + interval_ms.seconds

                # 如果返回条数少于请求的 batch_size，说明已到末尾
                if batch_count < self._batch_size:
                    logger.debug("返回条数少于批次大小，数据已到末尾")
                    break

            except Exception as e:
                self._stats["errors"] += 1
                logger.exception(
                    "批次同步失败",
                    batch=batch_index,
                    symbol=symbol_formatted,
                    error=str(e),
                )
                # 失败后跳过一个批次窗口继续，避免整体中断
                current_start_ms += interval_ms * self._batch_size

            # 批次间延迟，避免触发 API 限流
            if current_start_ms < end_ms:
                await asyncio.sleep(self._batch_delay)

        # 更新统计
        self._stats["total_synced"] += 1
        self._stats["total_batches"] += batch_index
        self._stats["total_bars"] += total_bars

        # 最终进度回调
        if on_progress:
            try:
                if asyncio.iscoroutinefunction(on_progress):
                    await on_progress(batch_index, total_bars, True)
                else:
                    on_progress(batch_index, total_bars, True)
            except Exception:
                pass

        logger.info(
            "历史K线同步完成",
            symbol=symbol_formatted,
            timeframe=interval_str,
            total_bars=total_bars,
            total_batches=batch_index,
        )

        return total_bars

    async def _sync_multiple(
        self,
        tasks: list[dict[str, Any]],
        concurrency: int = 1,
    ) -> dict[str, int]:
        """
        批量同步多个交易对/周期的历史K线

        Args:
            tasks: 同步任务列表，每个元素为 dict:
                {
                    "symbol": "BTCUSDT",
                    "timeframe": KlineInterval.MIN_1,
                    "start_time": "2024-01-01",
                    "end_time": "2024-01-31",  # 可选
                }
            concurrency: 并发数（默认 1，串行执行避免限流）

        Returns:
            每个交易对+周期的同步条数，如 {"BTCUSDT_1m": 1500, ...}
        """
        results: dict[str, int] = {}
        semaphore = asyncio.Semaphore(concurrency)

        async def _sync_task(task: dict[str, Any]) -> None:
            async with semaphore:
                symbol = task["symbol"]
                timeframe = task["timeframe"]
                key = f"{symbol.replace('/', '').upper()}_{timeframe.value}"

                try:
                    count = await self.sync(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_time=task["start_time"],
                        end_time=task.get("end_time"),
                    )
                    results[key] = count
                except Exception as e:
                    logger.exception("批量同步任务失败", key=key, error=str(e))
                    results[key] = -1

        await asyncio.gather(*[_sync_task(t) for t in tasks])

        logger.info("批量同步完成", results=results)
        return results

    # ─── 内部方法 ───────────────────────────────────────────────

    async def _publish_bars(
        self,
        bars: list[Bar],
        symbol: str,
    ) -> None:
        """
        将历史K线数据通过事件总线发布

        模仿实时行情的事件发布方式，使用 HISTORICAL_KLINE 事件类型，
        让订阅了该事件的 DatabaseSubscriber 等自动处理存储。

        Args:
            bars: Bar 对象列表
            symbol: 交易对
        """
        if not bars:
            return

        # 发布 HISTORICAL_KLINE 事件（批量）
        event = MarketEvent(
            type=MarketEventType.HISTORICAL_KLINE,
            data={
                "bars": bars,
                "symbol": symbol,
                "timeframe": bars[0].timeframe.value if bars else "",
                "count": len(bars),
                "start_ts": bars[0].timestamp if bars else 0,
                "end_ts": bars[-1].timestamp if bars else 0,
            },
            exchange="binance",
            symbol=symbol,
        )
        await self._event_bus.publish(event)

    @staticmethod
    def _bar_array_to_bars(
        bar_array: Any,
        symbol: str,
        timeframe: KlineInterval,
    ) -> list[Bar]:
        """
        将 BarArray 转换为 Bar 对象列表

        Args:
            bar_array: BinanceAPI 返回的 BarArray
            symbol: 交易对
            timeframe: K线周期

        Returns:
            Bar 对象列表
        """
        bars: list[Bar] = []

        for i in range(len(bar_array)):
            bar = Bar(
                timestamp=float(bar_array._timestamp_buf[i]),
                open=bar_array._open_buf[i],
                high=bar_array._high_buf[i],
                low=bar_array._low_buf[i],
                close=bar_array._close_buf[i],
                volume=bar_array._volume_buf[i],
                turnover=bar_array._turnover_buf[i] if bar_array._turnover_buf else 0.0,
                symbol=symbol,
                exchange="binance",
                timeframe=timeframe,
                is_closed=True,  # 历史数据都是已闭合的
            )
            bars.append(bar)

        return bars

    @staticmethod
    def _ms_to_time_string(ms: int) -> str:
        """
        将毫秒时间戳转换为 UTC 时间字符串

        Args:
            ms: 毫秒时间戳

        Returns:
            格式为 "YYYY-MM-DD HH:MM:SS" 的 UTC 时间字符串
        """
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def stats(self) -> dict[str, Any]:
        """获取同步统计信息"""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_synced": 0,
            "total_batches": 0,
            "total_bars": 0,
            "errors": 0,
        }
