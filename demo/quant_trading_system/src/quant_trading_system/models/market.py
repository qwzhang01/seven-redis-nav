from enum import Enum
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel
import numpy as np


class TimeFrame(str, Enum):
    """时间框架枚举"""
    S1 = "1s"
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H8 = "8h"
    H12 = "12h"
    D1 = "1d"
    D3 = "3d"
    W1 = "1w"
    MN1 = "1M"


class Bar(BaseModel):
    """K线数据"""
    timestamp: float  # 毫秒时间戳
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str
    timeframe: TimeFrame
    turnover: float = 0.0
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
        self.timestamp = np.append(self.timestamp, np.datetime64(int(bar.timestamp), "ms"))
        self.open = np.append(self.open, bar.open)
        self.high = np.append(self.high, bar.high)
        self.low = np.append(self.low, bar.low)
        self.close = np.append(self.close, bar.close)
        self.volume = np.append(self.volume, bar.volume)
        self.turnover = np.append(self.turnover, bar.volume * bar.close)

    def update_last(self, bar: Bar) -> None:
        """更新最后一根K线的数据（用于未关闭的K线实时更新）"""
        if len(self) == 0:
            # 如果数组为空，则直接添加
            self.append(bar)
            return
        self.timestamp[-1] = np.datetime64(int(bar.timestamp), "ms")
        self.open[-1] = bar.open
        self.high[-1] = bar.high
        self.low[-1] = bar.low
        self.close[-1] = bar.close
        self.volume[-1] = bar.volume
        self.turnover[-1] = bar.volume * bar.close


class Tick(BaseModel):
    """实时行情数据"""
    timestamp: float  # 毫秒时间戳
    symbol: str
    exchange: str = "unknown"
    last_price: float = 0.0
    price: float = 0.0  # 兼容旧字段
    volume: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    turnover: float = 0.0
    is_trade: bool = False
    trade_id: str = ""


class DepthLevel(BaseModel):
    """深度级别"""
    price: float
    volume: float

    @property
    def size(self) -> float:
        """volume的别名，向后兼容"""
        return self.volume

    def to_list(self) -> List[float]:
        """转为 [price, volume] 列表格式（兼容旧序列化）"""
        return [self.price, self.volume]


class Depth(BaseModel):
    """深度数据"""
    timestamp: datetime
    symbol: str
    exchange: str = "unknown"
    bids: List[DepthLevel]  # 买盘深度列表（价格从高到低）
    asks: List[DepthLevel]  # 卖盘深度列表（价格从低到高）
    sequence: Optional[int] = None  # lastUpdateId (币安) 或其他序列号

    @staticmethod
    def parse_levels(raw: List[List[float]]) -> List[DepthLevel]:
        """将 [[price, volume], ...] 原始数据解析为 DepthLevel 列表"""
        return [DepthLevel(price=item[0], volume=item[1]) for item in raw]
