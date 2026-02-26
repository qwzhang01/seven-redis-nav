from enum import Enum
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel
import numpy as np


class TimeFrame(str, Enum):
    """时间框架枚举"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1M"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class Bar(BaseModel):
    """K线数据"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str
    timeframe: TimeFrame
    is_closed: bool = True


@dataclass
class BarArray:
    """K线数据数组（使用numpy数组存储）"""
    symbol: str
    exchange: str
    timeframe: TimeFrame
    timestamp: np.ndarray = field(default_factory=lambda: np.array([], dtype="datetime64[ms]"))
    open: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    high: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    low: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    close: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    volume: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    turnover: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))

    def __len__(self):
        """返回数组长度"""
        return len(self.close)

    def append(self, bar: Bar) -> None:
        """添加一个Bar对象到数组"""
        self.timestamp = np.append(self.timestamp, np.datetime64(bar.timestamp))
        self.open = np.append(self.open, bar.open)
        self.high = np.append(self.high, bar.high)
        self.low = np.append(self.low, bar.low)
        self.close = np.append(self.close, bar.close)
        self.volume = np.append(self.volume, bar.volume)
        self.turnover = np.append(self.turnover, bar.volume * bar.close)


class Tick(BaseModel):
    """实时行情数据"""
    timestamp: datetime
    symbol: str
    exchange: str = "unknown"
    price: float
    volume: float
    bid: float
    ask: float


class Depth(BaseModel):
    """深度数据"""
    timestamp: datetime
    symbol: str
    exchange: str = "unknown"
    bids: List[List[float]]  # [price, volume]
    asks: List[List[float]]  # [price, volume]
    sequence: Optional[int] = None  # lastUpdateId (币安) 或其他序列号


class DepthLevel(BaseModel):
    """深度级别"""
    price: float
    volume: float
