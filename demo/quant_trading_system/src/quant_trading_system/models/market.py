from typing import List, Optional
from pydantic import BaseModel
import numpy as np

from quant_trading_system.core.enums import KlineInterval

# 向后兼容别名（已废弃，请直接使用 KlineInterval）
TimeFrame = KlineInterval


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
    timeframe: KlineInterval
    turnover: float = 0.0
    is_closed: bool = True


class BarArray:
    """
    K线数据数组

    内部使用 list 缓冲区 + numpy 延迟转换，避免 np.append 的 O(n) 性能问题。
    支持两种构造方式：
      1. 只传 symbol/exchange/timeframe，后续通过 append() 逐条追加（实盘/流式场景）
      2. 直接传入 numpy 数组（timestamp/open/high/low/close/volume/turnover）批量初始化（回测/数据加载场景）
    """

    __slots__ = (
        "symbol", "exchange", "timeframe", "max_size",
        "_timestamp_buf", "_open_buf", "_high_buf", "_low_buf",
        "_close_buf", "_volume_buf", "_turnover_buf",
        "_np_dirty", "_ts_cache", "_open_cache", "_high_cache",
        "_low_cache", "_close_cache", "_volume_cache", "_turnover_cache",
        "_ts_ms_cache",
    )

    def __init__(
        self,
        symbol: str,
        exchange: str,
        timeframe: KlineInterval,
        timestamp: np.ndarray | None = None,
        open: np.ndarray | None = None,
        high: np.ndarray | None = None,
        low: np.ndarray | None = None,
        close: np.ndarray | None = None,
        volume: np.ndarray | None = None,
        turnover: np.ndarray | None = None,
        max_size: int = 0,
    ) -> None:
        self.symbol = symbol
        self.exchange = exchange
        self.timeframe = timeframe
        self.max_size = max_size  # 0 表示不限制（回测场景），>0 时自动裁剪（实盘场景）

        # 如果传入了 numpy 数组，则直接使用（向后兼容批量构造）
        if close is not None and len(close) > 0:
            # 将 numpy 数组转为 list 缓冲区
            ts_arr = timestamp if timestamp is not None else np.array([], dtype="datetime64[ms]")
            # timestamp 可能是 datetime64 类型，转为 int 毫秒存储
            if ts_arr.dtype.kind == 'M':  # datetime64
                self._timestamp_buf = ts_arr.astype("datetime64[ms]").astype(np.int64).tolist()
            else:
                self._timestamp_buf = [int(x) for x in ts_arr]
            self._open_buf = list(np.asarray(open, dtype=np.float64)) if open is not None else []
            self._high_buf = list(np.asarray(high, dtype=np.float64)) if high is not None else []
            self._low_buf = list(np.asarray(low, dtype=np.float64)) if low is not None else []
            self._close_buf = list(np.asarray(close, dtype=np.float64))
            self._volume_buf = list(np.asarray(volume, dtype=np.float64)) if volume is not None else []
            self._turnover_buf = list(np.asarray(turnover, dtype=np.float64)) if turnover is not None else []
        else:
            self._timestamp_buf: list = []
            self._open_buf: list = []
            self._high_buf: list = []
            self._low_buf: list = []
            self._close_buf: list = []
            self._volume_buf: list = []
            self._turnover_buf: list = []

        # numpy 数组缓存，按需重建
        self._np_dirty: bool = True
        self._ts_cache: np.ndarray = np.array([], dtype="datetime64[ms]")
        self._open_cache: np.ndarray = np.array([], dtype=np.float64)
        self._high_cache: np.ndarray = np.array([], dtype=np.float64)
        self._low_cache: np.ndarray = np.array([], dtype=np.float64)
        self._close_cache: np.ndarray = np.array([], dtype=np.float64)
        self._volume_cache: np.ndarray = np.array([], dtype=np.float64)
        self._turnover_cache: np.ndarray = np.array([], dtype=np.float64)
        self._ts_ms_cache: np.ndarray | None = None  # 时间戳毫秒数组（float64），回测用

    def _rebuild_cache(self) -> None:
        """从 list 缓冲区重建 numpy 数组缓存"""
        if not self._np_dirty:
            return
        self._ts_cache = np.array(self._timestamp_buf, dtype="datetime64[ms]")
        self._open_cache = np.array(self._open_buf, dtype=np.float64)
        self._high_cache = np.array(self._high_buf, dtype=np.float64)
        self._low_cache = np.array(self._low_buf, dtype=np.float64)
        self._close_cache = np.array(self._close_buf, dtype=np.float64)
        self._volume_cache = np.array(self._volume_buf, dtype=np.float64)
        self._turnover_cache = np.array(self._turnover_buf, dtype=np.float64)
        self._np_dirty = False

    def _trim_if_needed(self) -> None:
        """当缓冲区超过 max_size 时，裁剪旧数据"""
        if self.max_size > 0 and len(self._close_buf) > self.max_size:
            excess = len(self._close_buf) - self.max_size
            self._timestamp_buf = self._timestamp_buf[excess:]
            self._open_buf = self._open_buf[excess:]
            self._high_buf = self._high_buf[excess:]
            self._low_buf = self._low_buf[excess:]
            self._close_buf = self._close_buf[excess:]
            self._volume_buf = self._volume_buf[excess:]
            self._turnover_buf = self._turnover_buf[excess:]

    # ---- numpy 数组属性（只读，按需重建）----

    @property
    def timestamp(self) -> np.ndarray:
        self._rebuild_cache()
        return self._ts_cache

    @property
    def open(self) -> np.ndarray:
        self._rebuild_cache()
        return self._open_cache

    @property
    def high(self) -> np.ndarray:
        self._rebuild_cache()
        return self._high_cache

    @property
    def low(self) -> np.ndarray:
        self._rebuild_cache()
        return self._low_cache

    @property
    def close(self) -> np.ndarray:
        self._rebuild_cache()
        return self._close_cache

    @property
    def volume(self) -> np.ndarray:
        self._rebuild_cache()
        return self._volume_cache

    @property
    def turnover(self) -> np.ndarray:
        self._rebuild_cache()
        return self._turnover_cache

    def __len__(self):
        """返回数组长度"""
        return len(self._close_buf)

    def __repr__(self) -> str:
        return (
            f"BarArray(symbol={self.symbol!r}, exchange={self.exchange!r}, "
            f"timeframe={self.timeframe!r}, len={len(self)})"
        )

    def append(self, bar: Bar) -> None:
        """添加一个Bar对象到数组（O(1) 均摊复杂度）"""
        self._timestamp_buf.append(int(bar.timestamp))
        self._open_buf.append(bar.open)
        self._high_buf.append(bar.high)
        self._low_buf.append(bar.low)
        self._close_buf.append(bar.close)
        self._volume_buf.append(bar.volume)
        self._turnover_buf.append(bar.volume * bar.close)
        self._np_dirty = True
        self._trim_if_needed()

    def update_last(self, bar: Bar) -> None:
        """更新最后一根K线的数据（用于未关闭的K线实时更新）"""
        if len(self) == 0:
            # 如果数组为空，则直接添加
            self.append(bar)
            return
        self._timestamp_buf[-1] = int(bar.timestamp)
        self._open_buf[-1] = bar.open
        self._high_buf[-1] = bar.high
        self._low_buf[-1] = bar.low
        self._close_buf[-1] = bar.close
        self._volume_buf[-1] = bar.volume
        self._turnover_buf[-1] = bar.volume * bar.close
        self._np_dirty = True

    def truncate(self, max_count: int) -> None:
        """裁剪缓冲区，只保留最新的 max_count 条数据"""
        if len(self._close_buf) <= max_count:
            return
        excess = len(self._close_buf) - max_count
        self._timestamp_buf = self._timestamp_buf[excess:]
        self._open_buf = self._open_buf[excess:]
        self._high_buf = self._high_buf[excess:]
        self._low_buf = self._low_buf[excess:]
        self._close_buf = self._close_buf[excess:]
        self._volume_buf = self._volume_buf[excess:]
        self._turnover_buf = self._turnover_buf[excess:]
        self._np_dirty = True

    def ensure_numpy_cache(self) -> None:
        """预先构建 numpy 缓存，回测初始化时调用一次"""
        self._rebuild_cache()

    def get_timestamp_ms(self) -> np.ndarray:
        """获取时间戳毫秒数组（float64），结果会被缓存"""
        if self._ts_ms_cache is None:
            ts = self.timestamp
            if len(ts) == 0:
                self._ts_ms_cache = np.array([], dtype=np.float64)
            elif ts.dtype.kind == 'M':  # datetime64
                self._ts_ms_cache = ts.astype('datetime64[ms]').astype(np.int64).astype(np.float64)
            else:
                self._ts_ms_cache = np.asarray(ts, dtype=np.float64)
        return self._ts_ms_cache

    def get_numpy_arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """一次性获取所有 numpy 数组引用（timestamp, open, high, low, close, volume, turnover），避免多次 property 调用触发重建检查"""
        self._rebuild_cache()
        return (self._ts_cache, self._open_cache, self._high_cache,
                self._low_cache, self._close_cache, self._volume_cache, self._turnover_cache)

    @classmethod
    def from_bars(cls, bars: list["Bar"]) -> "BarArray":
        """从 Bar 列表批量构建 BarArray"""
        if not bars:
            raise ValueError("bars cannot be empty")
        first = bars[0]
        arr = cls(
            symbol=first.symbol,
            exchange=first.exchange,
            timeframe=first.timeframe,
        )
        for bar in bars:
            arr.append(bar)
        return arr


class BarArrayView:
    """
    BarArray 的轻量级只读视图（用于回测）

    通过 numpy 切片提供 O(1) 的零拷贝视图，
    避免回测中每根K线都创建新 BarArray 的 O(n) 开销。
    """

    __slots__ = (
        "symbol", "exchange", "timeframe",
        "_src_ts", "_src_open", "_src_high", "_src_low",
        "_src_close", "_src_volume", "_src_turnover",
        "_end",
    )

    def __init__(self, source: BarArray) -> None:
        self.symbol = source.symbol
        self.exchange = source.exchange
        self.timeframe = source.timeframe
        # 获取底层 numpy 数组的引用（仅一次）
        (self._src_ts, self._src_open, self._src_high,
         self._src_low, self._src_close, self._src_volume,
         self._src_turnover) = source.get_numpy_arrays()
        self._end: int = len(self._src_close)  # 可见长度

    def set_end(self, end: int) -> None:
        """设置可见数据的结束索引（不含），O(1) 操作"""
        self._end = end

    @property
    def timestamp(self) -> np.ndarray:
        return self._src_ts[:self._end]

    @property
    def open(self) -> np.ndarray:
        return self._src_open[:self._end]

    @property
    def high(self) -> np.ndarray:
        return self._src_high[:self._end]

    @property
    def low(self) -> np.ndarray:
        return self._src_low[:self._end]

    @property
    def close(self) -> np.ndarray:
        return self._src_close[:self._end]

    @property
    def volume(self) -> np.ndarray:
        return self._src_volume[:self._end]

    @property
    def turnover(self) -> np.ndarray:
        return self._src_turnover[:self._end]

    def __len__(self) -> int:
        return self._end

    def __repr__(self) -> str:
        return (
            f"BarArrayView(symbol={self.symbol!r}, exchange={self.exchange!r}, "
            f"timeframe={self.timeframe!r}, len={len(self)})"
        )


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
    timestamp: float  # 毫秒时间戳，与 Bar/Tick 保持一致
    symbol: str
    exchange: str = "unknown"
    bids: List[DepthLevel]  # 买盘深度列表（价格从高到低）
    asks: List[DepthLevel]  # 卖盘深度列表（价格从低到高）
    sequence: Optional[int] = None  # lastUpdateId (币安) 或其他序列号

    @staticmethod
    def parse_levels(raw: List[List[float]]) -> List[DepthLevel]:
        """将 [[price, volume], ...] 原始数据解析为 DepthLevel 列表"""
        return [DepthLevel(price=item[0], volume=item[1]) for item in raw]
