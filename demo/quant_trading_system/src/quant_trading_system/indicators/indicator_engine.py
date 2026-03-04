"""
指标计算引擎
============

高性能的指标计算引擎，支持：
- 批量计算
- 增量更新
- 结果缓存
- 并行计算
"""

import asyncio
import hashlib
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Union

import numpy as np
import structlog

from quant_trading_system.models.market import Bar, BarArray, BarArrayView
from quant_trading_system.indicators.base import (
    Indicator,
    IndicatorRegistry,
    IndicatorResult,
)

# 统一的 bars 输入类型
BarsInput = Union[BarArray, BarArrayView, list[Bar]]

logger = structlog.get_logger(__name__)


class IndicatorCache:
    """
    指标结果缓存（基于 OrderedDict 实现 O(1) LRU）
    """

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: OrderedDict[str, IndicatorResult] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> IndicatorResult | None:
        """获取缓存，命中时自动移到末尾（O(1)）"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def set(self, key: str, result: IndicatorResult) -> None:
        """设置缓存，超出容量时淘汰最久未访问的条目（O(1)）"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = result
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)  # 淘汰最旧
                self._cache[key] = result

    def clear(self) -> None:
        """清除缓存"""
        with self._lock:
            self._cache.clear()

    @staticmethod
    def make_key(
        symbol: str,
        indicator_name: str,
        params: dict[str, Any],
        data_hash: str,
    ) -> str:
        """生成缓存键"""
        params_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{symbol}:{indicator_name}:{params_str}:{data_hash}"


class IndicatorEngine:
    """
    指标计算引擎

    提供高性能的指标计算能力
    """

    def __init__(
        self,
        cache_size: int = 1000,
        max_workers: int = 4,
    ) -> None:
        self._cache = IndicatorCache(max_size=cache_size)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        # 指标实例缓存（线程安全）
        self._indicator_instances: dict[str, Indicator] = {}
        self._instances_lock = threading.Lock()

        # 统计（使用原子操作无需锁，但用 lock 保证准确）
        self._stats_lock = threading.Lock()
        self._calc_count = 0
        self._cache_hits = 0

    def calculate(
        self,
        indicator_name: str,
        bars: BarsInput,
        use_cache: bool = True,
        **params: Any,
    ) -> IndicatorResult:
        """
        计算指标

        Args:
            indicator_name: 指标名称
            bars: K线数据（支持 BarArray / BarArrayView / list[Bar]）
            use_cache: 是否使用缓存
            **params: 指标参数

        Returns:
            指标计算结果
        """
        # 转换 list[Bar] 为 BarArray
        if isinstance(bars, list):
            if not bars:
                raise ValueError("bars cannot be empty")
            bars = BarArray.from_bars(bars)

        # 检查缓存
        cache_key = ""
        if use_cache:
            data_hash = self._compute_data_hash(bars)
            cache_key = IndicatorCache.make_key(
                bars.symbol, indicator_name, params, data_hash
            )
            cached = self._cache.get(cache_key)
            if cached:
                with self._stats_lock:
                    self._cache_hits += 1
                return cached

        # 获取或创建指标实例（线程安全）
        instance_key = f"{indicator_name}_{hash(frozenset(params.items()))}"

        with self._instances_lock:
            if instance_key not in self._indicator_instances:
                indicator = IndicatorRegistry.create(indicator_name, **params)
                if indicator is None:
                    raise ValueError(f"Unknown indicator: {indicator_name}")
                self._indicator_instances[instance_key] = indicator
            indicator = self._indicator_instances[instance_key]

        # 计算指标
        result = indicator.calculate(
            close=bars.close,
            high=bars.high,
            low=bars.low,
            open=bars.open,
            volume=bars.volume,
        )

        with self._stats_lock:
            self._calc_count += 1

        # 缓存结果
        if use_cache:
            self._cache.set(cache_key, result)

        return result

    async def calculate_async(
        self,
        indicator_name: str,
        bars: BarsInput,
        use_cache: bool = True,
        **params: Any,
    ) -> IndicatorResult:
        """异步计算指标"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.calculate(indicator_name, bars, use_cache, **params)
        )

    def calculate_multiple(
        self,
        indicators: list[tuple[str, dict[str, Any]]],
        bars: BarsInput,
        use_cache: bool = True,
    ) -> dict[str, IndicatorResult]:
        """
        批量计算多个指标

        Args:
            indicators: [(指标名称, 参数), ...]
            bars: K线数据
            use_cache: 是否使用缓存

        Returns:
            {指标名称: 结果}
        """
        results = {}

        for name, params in indicators:
            try:
                result = self.calculate(name, bars, use_cache, **params)
                results[name] = result
            except Exception as e:
                logger.error(f"Indicator calculation failed",
                           indicator=name,
                           error=str(e))

        return results

    async def calculate_multiple_async(
        self,
        indicators: list[tuple[str, dict[str, Any]]],
        bars: BarsInput,
        use_cache: bool = True,
    ) -> dict[str, IndicatorResult]:
        """异步批量计算多个指标"""
        tasks = []
        names = []

        for name, params in indicators:
            task = self.calculate_async(name, bars, use_cache, **params)
            tasks.append(task)
            names.append(name)

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for name, result in zip(names, results_list):
            if isinstance(result, Exception):
                logger.error(f"Indicator calculation failed",
                           indicator=name,
                           error=str(result))
            else:
                results[name] = result

        return results

    def get_latest_values(
        self,
        indicator_name: str,
        bars: BarsInput,
        **params: Any,
    ) -> dict[str, float]:
        """
        获取指标最新值

        Args:
            indicator_name: 指标名称
            bars: K线数据
            **params: 指标参数

        Returns:
            {输出名: 最新值}
        """
        result = self.calculate(indicator_name, bars, **params)

        latest = {}
        for key, values in result.values.items():
            if len(values) > 0:
                latest[key] = float(values[-1]) if not np.isnan(values[-1]) else None
            else:
                latest[key] = None

        return latest

    @staticmethod
    def _compute_data_hash(bars: Union[BarArray, BarArrayView]) -> str:
        """
        计算数据哈希

        使用数据长度 + 全量 OHLCV 最后 N 条的 MD5 摘要，
        避免仅用尾部少量字段导致的缓存碰撞。
        """
        n = len(bars)
        if n == 0:
            return "empty"

        # 取最后 min(20, n) 条数据，覆盖 OHLCV 五个字段
        tail = min(20, n)
        data = np.concatenate([
            bars.open[-tail:],
            bars.high[-tail:],
            bars.low[-tail:],
            bars.close[-tail:],
            bars.volume[-tail:],
        ])
        # 将数据长度编码进哈希，防止不同长度但尾部相同的情况碰撞
        raw = f"{n}:".encode() + data.tobytes()
        return hashlib.md5(raw).hexdigest()

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.clear()
        with self._instances_lock:
            self._indicator_instances.clear()

    def list_indicators(self) -> list[str]:
        """列出可用指标"""
        return IndicatorRegistry.list_indicators()

    def get_indicator_info(self, name: str) -> dict[str, Any] | None:
        """获取指标信息"""
        return IndicatorRegistry.get_info(name)

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "calc_count": self._calc_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                self._cache_hits / (self._calc_count + self._cache_hits)
                if (self._calc_count + self._cache_hits) > 0
                else 0
            ),
            "available_indicators": self.list_indicators(),
        }

    def shutdown(self) -> None:
        """关闭引擎"""
        self._executor.shutdown(wait=False)


def get_indicator_engine() -> IndicatorEngine:
    """获取全局指标引擎（委托到 ServiceContainer）"""
    from quant_trading_system.core.container import container
    return container.indicator_engine
