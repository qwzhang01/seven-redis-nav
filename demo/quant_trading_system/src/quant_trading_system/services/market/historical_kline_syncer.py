"""
历史K线数据同步器
==================

从交易所 REST API 拉取历史K线数据，通过事件总线发布给订阅器处理。

设计思路：
- 按传入的时间区间，智能分批拉取（币安 API 单次最多 1000 条）
- 根据 K线周期自动计算每批的时间窗口大小
- 拉取到数据后，模仿实时行情的事件机制，通过 MarketEventBus 发布 HISTORICAL_KLINE 事件
- 订阅了 HISTORICAL_KLINE 事件的订阅器（如 DatabaseSubscriber）自动处理存储

使用方式：
    syncer = HistoricalKlineSyncer(binance_api, event_bus)
    await syncer.sync(
        symbol="BTCUSDT",
        timeframe=KlineInterval.MIN_1,
        start_time="2024-01-01",
        end_time="2024-01-31",
    )
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.models.market import Bar
from quant_trading_system.exchange_adapter.binance.binance_rest_client import BinanceRestClient
from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventBus,
    MarketEventType,
)
from quant_trading_system.exchange_adapter.utils import TimeUtils

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════
# K线周期 → 毫秒 映射
# ═══════════════════════════════════════════════════════════════

INTERVAL_MS: dict[str, int] = {
    "1s": 1_000,
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_592_000_000,  # 按 30 天近似
}

# 币安 API 单次最大返回条数
BINANCE_MAX_LIMIT = 1000

# 默认批次间的请求间隔（秒），避免触发限流
DEFAULT_BATCH_DELAY = 0.3


@dataclass
class SyncerConfig:
    """
    历史K线同步器配置

    控制同步行为：是否启动时自动同步、默认同步参数等。
    """

    # 是否在服务启动时自动执行历史数据同步
    sync_on_startup: bool = False

    # 启动时自动同步的交易对列表
    startup_symbols: list[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT"])

    # 启动时自动同步的K线周期列表
    startup_timeframes: list[KlineInterval] = field(
        default_factory=lambda: [KlineInterval.HOUR_1]
    )

    # 启动时同步的天数（从当前时间往前推）
    startup_sync_days: int = 7

    # 批次间请求延迟（秒）
    batch_delay: float = DEFAULT_BATCH_DELAY

    # 每批拉取条数
    batch_size: int = BINANCE_MAX_LIMIT


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
        binance_api: BinanceRestClient,
        event_bus: MarketEventBus,
        config: SyncerConfig | None = None,
        batch_delay: float = DEFAULT_BATCH_DELAY,
        batch_size: int = BINANCE_MAX_LIMIT,
    ) -> None:
        """
        初始化历史K线同步器

        Args:
            binance_api: 币安 REST API 客户端
            event_bus: 行情事件总线
            config: 同步器配置（可选，为空则使用默认配置）
            batch_delay: 批次间请求延迟（秒），默认 0.3s
            batch_size: 每批拉取条数，最大 1000
        """
        self._api = binance_api
        self._event_bus = event_bus
        self._config = config or SyncerConfig(
            batch_delay=batch_delay,
            batch_size=batch_size,
        )
        self._batch_delay = self._config.batch_delay
        self._batch_size = min(self._config.batch_size, BINANCE_MAX_LIMIT)

        # 同步统计
        self._stats: dict[str, Any] = {
            "total_synced": 0,
            "total_batches": 0,
            "total_bars": 0,
            "errors": 0,
        }

    # ─── 公开接口 ───────────────────────────────────────────────

    @property
    def config(self) -> SyncerConfig:
        """获取同步器配置"""
        return self._config

    def close(self) -> None:
        """
        关闭同步器，释放底层 BinanceAPI 的 HTTP 客户端资源
        """
        if self._api:
            self._api.close()
            logger.info("历史K线同步器已关闭")

    async def sync_on_startup(self) -> None:
        """
        服务启动时自动执行的历史数据同步

        根据 config 中配置的交易对列表、K线周期和同步天数，
        自动拉取近期历史数据并通过事件总线发布。
        """
        logger.info(
            "开始启动时历史数据同步",
            symbols=self._config.startup_symbols,
            timeframes=[tf.value for tf in self._config.startup_timeframes],
            sync_days=self._config.startup_sync_days,
        )

        from datetime import datetime, timedelta

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_time = (
            datetime.now() - timedelta(days=self._config.startup_sync_days)
        ).strftime("%Y-%m-%d %H:%M:%S")

        # 构建批量同步任务
        tasks: list[dict[str, Any]] = []
        for symbol in self._config.startup_symbols:
            for timeframe in self._config.startup_timeframes:
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
            results = await self.sync_multiple(tasks, concurrency=1)
            total = sum(v for v in results.values() if v > 0)
            logger.info(
                "启动时历史数据同步完成",
                results=results,
                total_bars=total,
            )
        except Exception as e:
            logger.error("启动时历史数据同步失败", error=str(e))

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

        # 计算每批时间窗口
        interval_ms = INTERVAL_MS.get(interval_str)
        if not interval_ms:
            raise ValueError(f"不支持的K线周期: {interval_str}")

        batch_window_ms = interval_ms * self._batch_size  # 每批覆盖的时间范围

        # 估算总批次数
        total_time_span = end_ms - start_ms
        estimated_batches = max(1, (total_time_span + batch_window_ms - 1) // batch_window_ms)

        logger.info(
            "开始同步历史K线",
            symbol=symbol_formatted,
            timeframe=interval_str,
            start_time=start_time,
            end_time=end_time or "now",
            estimated_batches=estimated_batches,
            batch_size=self._batch_size,
        )

        total_bars = 0
        batch_index = 0
        current_start_ms = start_ms

        while current_start_ms < end_ms:
            batch_index += 1

            # 计算当前批次的结束时间
            current_end_ms = min(current_start_ms + batch_window_ms, end_ms)

            try:
                # 使用 BinanceAPI 拉取一批数据
                bar_array = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=current_start_ms, e=current_end_ms: self._api.fetch_klines(
                        symbol=symbol_formatted,
                        timeframe=timeframe,
                        start_time=self._ms_to_time_string(s),
                        end_time=self._ms_to_time_string(e),
                        limit=self._batch_size,
                    ),
                )

                batch_count = len(bar_array)

                if batch_count == 0:
                    logger.debug(
                        "批次无数据，跳过",
                        batch=batch_index,
                        start_ms=current_start_ms,
                    )
                    current_start_ms = current_end_ms + 1
                    continue

                # 将 BarArray 转换为 Bar 对象列表，通过事件总线发布
                bars = self._bar_array_to_bars(bar_array, symbol_formatted, timeframe)

                # 通过事件总线发布 HISTORICAL_KLINE 事件
                await self._publish_bars(bars, symbol_formatted)

                total_bars += batch_count

                logger.info(
                    "批次同步完成",
                    batch=batch_index,
                    batch_bars=batch_count,
                    total_bars=total_bars,
                    symbol=symbol_formatted,
                    timeframe=interval_str,
                    progress=f"{min(100, int((current_end_ms - start_ms) / (end_ms - start_ms) * 100))}%",
                )

                # 进度回调
                if on_progress:
                    try:
                        if asyncio.iscoroutinefunction(on_progress):
                            await on_progress(batch_index, total_bars, False)
                        else:
                            on_progress(batch_index, total_bars, False)
                    except Exception as e:
                        logger.warning("进度回调异常", error=str(e))

                # 更新起始位置：使用最后一条数据的时间戳 + 1 个周期
                last_ts = int(bar_array._timestamp_buf[-1]) if bar_array._timestamp_buf else 0
                if last_ts > 0:
                    current_start_ms = last_ts + interval_ms
                else:
                    current_start_ms = current_end_ms + 1

                # 如果返回条数少于请求的 batch_size，说明已到末尾
                if batch_count < self._batch_size:
                    logger.debug("返回条数少于批次大小，数据已到末尾")
                    break

            except Exception as e:
                self._stats["errors"] += 1
                logger.error(
                    "批次同步失败",
                    batch=batch_index,
                    symbol=symbol_formatted,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # 失败后继续下一批，避免整体中断
                current_start_ms = current_end_ms + 1

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

    async def sync_multiple(
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
                    logger.error("批量同步任务失败", key=key, error=str(e))
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
        将毫秒时间戳转换为时间字符串

        Args:
            ms: 毫秒时间戳

        Returns:
            格式为 "YYYY-MM-DD HH:MM:SS" 的时间字符串
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(ms / 1000)
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
