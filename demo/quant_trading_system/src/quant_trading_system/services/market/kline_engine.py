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

from quant_trading_system.models.market import Bar, BarArray, Tick, TimeFrame

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
    timeframe: TimeFrame
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
        self._buffers: dict[str, dict[TimeFrame, KLineBuffer]] = defaultdict(dict)
        
        # 当前K线: {symbol: {timeframe: Bar}}
        self._current_bars: dict[str, dict[TimeFrame, Bar]] = defaultdict(dict)
        
        # 回调: {timeframe: [callbacks]}
        self._callbacks: dict[TimeFrame, list[BarCallback]] = defaultdict(list)
        
        # 通用回调（所有周期）
        self._general_callbacks: list[BarCallback] = []
        
        # 支持的周期
        self._timeframes: list[TimeFrame] = [
            TimeFrame.M1,
            TimeFrame.M5,
            TimeFrame.M15,
            TimeFrame.M30,
            TimeFrame.H1,
            TimeFrame.H4,
            TimeFrame.D1,
        ]
        
        # 统计
        self._tick_count = 0
        self._bar_count = 0
    
    def add_timeframe(self, timeframe: TimeFrame) -> None:
        """添加支持的周期"""
        if timeframe not in self._timeframes:
            self._timeframes.append(timeframe)
    
    def add_callback(
        self, 
        callback: BarCallback,
        timeframe: TimeFrame | None = None,
    ) -> None:
        """添加K线回调"""
        if timeframe:
            self._callbacks[timeframe].append(callback)
        else:
            self._general_callbacks.append(callback)
    
    def remove_callback(
        self, 
        callback: BarCallback,
        timeframe: TimeFrame | None = None,
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
        symbol = tick.symbol
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
        timeframe: TimeFrame,
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
    
    def _get_bar_start_time(self, timestamp: float, timeframe: TimeFrame) -> float:
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
    
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame,
        limit: int | None = None,
    ) -> list[Bar]:
        """获取K线列表"""
        if symbol not in self._buffers:
            return []
        
        if timeframe not in self._buffers[symbol]:
            return []
        
        buffer = self._buffers[symbol][timeframe]
        return buffer.get_last(limit or buffer.count)
    
    def get_bar_array(
        self,
        symbol: str,
        timeframe: TimeFrame,
        limit: int | None = None,
    ) -> BarArray:
        """获取K线数组"""
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
        timeframe: TimeFrame,
    ) -> Bar | None:
        """获取当前未完成的K线"""
        return self._current_bars.get(symbol, {}).get(timeframe)
    
    def get_last_bar(
        self,
        symbol: str,
        timeframe: TimeFrame,
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


class KLineAggregator:
    """
    K线聚合器
    
    从小周期K线合成大周期K线
    """
    
    def __init__(self) -> None:
        self._buffers: dict[str, dict[TimeFrame, list[Bar]]] = defaultdict(dict)
    
    def aggregate(
        self,
        bars: list[Bar],
        target_timeframe: TimeFrame,
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
