"""
模拟行情数据采集器
==================

在开发环境中替代真实交易所 WebSocket 连接，
生成逼真的实时 tick / kline / depth 模拟数据流。

数据通过 DataCollector._notify 分发，
完全兼容 MarketService 的回调管道（_on_tick_data / _on_kline_data / _on_depth_data）。

用法：
    MarketService.add_exchange("mock") 即可在开发环境启用。
"""

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any

import structlog

from quant_trading_system.services.market.data_collector import DataCollector

logger = structlog.get_logger(__name__)


# ── 交易对默认配置 ──────────────────────────────────────────────

@dataclass
class SymbolConfig:
    """单个交易对的模拟参数"""
    base_price: float          # 基准价格
    volatility: float = 0.002  # 单次波动率（±0.2%）
    base_volume: float = 1.0   # 基准成交量
    depth_levels: int = 10     # 深度档位数
    spread_pct: float = 0.0005 # 买卖价差百分比


# 预置主流币种的合理基准价格
DEFAULT_SYMBOL_CONFIGS: dict[str, SymbolConfig] = {
    "BTCUSDT":  SymbolConfig(base_price=95000.0, volatility=0.0015, base_volume=0.5),
    "ETHUSDT":  SymbolConfig(base_price=2600.0,  volatility=0.002,  base_volume=5.0),
    "SOLUSDT":  SymbolConfig(base_price=180.0,   volatility=0.003,  base_volume=20.0),
    "BNBUSDT":  SymbolConfig(base_price=620.0,   volatility=0.002,  base_volume=3.0),
    "XRPUSDT":  SymbolConfig(base_price=2.3,     volatility=0.003,  base_volume=500.0),
    "ADAUSDT":  SymbolConfig(base_price=0.75,    volatility=0.003,  base_volume=1000.0),
    "DOGEUSDT": SymbolConfig(base_price=0.22,    volatility=0.004,  base_volume=5000.0),
    "DOTUSDT":  SymbolConfig(base_price=7.5,     volatility=0.003,  base_volume=50.0),
}


@dataclass
class _SymbolState:
    """运行时：单个交易对的实时状态"""
    last_price: float
    bid_price: float = 0.0
    ask_price: float = 0.0
    # 当前 1m K 线缓存
    kline_open: float = 0.0
    kline_high: float = 0.0
    kline_low: float = 0.0
    kline_close: float = 0.0
    kline_volume: float = 0.0
    kline_start_ts: float = 0.0  # 毫秒时间戳
    # 趋势状态（模拟微趋势）
    trend: float = 0.0
    trend_remaining: int = 0


class MockDataCollector(DataCollector):
    """
    模拟行情数据采集器

    功能：
    - 模拟 ticker（逐笔行情）   ：默认每 500ms 推送一次
    - 模拟 kline（1m K线）       ：每秒推送实时更新，每 60s 推送 is_closed=True
    - 模拟 depth（买卖深度）     ：默认每 1s 推送一次
    - 价格采用带微趋势的随机游走，视觉上更真实
    - 可通过 subscribe / unsubscribe 动态增减交易对

    参数：
    - tick_interval   : tick 推送间隔（秒），默认 0.5
    - depth_interval  : depth 推送间隔（秒），默认 1.0
    - kline_intervals : 需要推送的 K 线周期列表，默认 ["1m", "5m", "15m", "1h"]
    """

    def __init__(
        self,
        tick_interval: float = 0.5,
        depth_interval: float = 1.0,
        kline_intervals: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name="mock", enable_storage=False)

        self.tick_interval = tick_interval
        self.depth_interval = depth_interval
        self.kline_intervals = kline_intervals or ["1m", "5m", "15m", "1h"]

        # 运行时状态：symbol_key → _SymbolState
        self._states: dict[str, _SymbolState] = {}

        # 后台任务
        self._tick_task: asyncio.Task | None = None
        self._depth_task: asyncio.Task | None = None
        self._kline_task: asyncio.Task | None = None

    # ── 生命周期 ────────────────────────────────────────────────

    async def start(self) -> None:
        """启动模拟采集器"""
        if self._running:
            return

        self._running = True
        logger.info("🎭 MockDataCollector 启动",
                     tick_interval=self.tick_interval,
                     depth_interval=self.depth_interval,
                     kline_intervals=self.kline_intervals)

        # 启动后台推送任务
        self._tick_task = asyncio.create_task(self._tick_loop(), name="mock-tick")
        self._depth_task = asyncio.create_task(self._depth_loop(), name="mock-depth")
        self._kline_task = asyncio.create_task(self._kline_loop(), name="mock-kline")

    async def stop(self) -> None:
        """停止模拟采集器"""
        self._running = False

        for task in [self._tick_task, self._depth_task, self._kline_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._tick_task = None
        self._depth_task = None
        self._kline_task = None

        logger.info("🎭 MockDataCollector 已停止")

    # ── 订阅管理 ────────────────────────────────────────────────

    async def subscribe(self, symbols: list[str]) -> None:
        """
        订阅交易对

        symbols 格式与真实采集器一致，如 ["BTC/USDT", "ETH/USDT"]
        内部自动转换为 BTCUSDT 格式。
        """
        for raw_symbol in symbols:
            symbol_key = raw_symbol.replace("/", "").replace("-", "").upper()

            if symbol_key in self._states:
                continue

            # 获取预置配置或使用默认值
            cfg = DEFAULT_SYMBOL_CONFIGS.get(
                symbol_key,
                SymbolConfig(base_price=100.0, volatility=0.003, base_volume=10.0),
            )

            # 初始化运行时状态
            now_ms = time.time() * 1000
            # K 线开始时间对齐到分钟
            kline_start = (int(now_ms) // 60000) * 60000

            state = _SymbolState(
                last_price=cfg.base_price,
                bid_price=cfg.base_price * (1 - cfg.spread_pct),
                ask_price=cfg.base_price * (1 + cfg.spread_pct),
                kline_open=cfg.base_price,
                kline_high=cfg.base_price,
                kline_low=cfg.base_price,
                kline_close=cfg.base_price,
                kline_volume=0.0,
                kline_start_ts=float(kline_start),
            )
            self._states[symbol_key] = state
            self._subscriptions.add(raw_symbol)

        logger.info("🎭 Mock 订阅", symbols=symbols,
                     active_symbols=list(self._states.keys()))

    async def unsubscribe(self, symbols: list[str]) -> None:
        """取消订阅"""
        for raw_symbol in symbols:
            symbol_key = raw_symbol.replace("/", "").replace("-", "").upper()
            self._states.pop(symbol_key, None)
            self._subscriptions.discard(raw_symbol)

        logger.info("🎭 Mock 取消订阅", symbols=symbols)

    # ── 价格模拟引擎 ────────────────────────────────────────────

    def _next_price(self, symbol_key: str) -> float:
        """
        生成下一个价格（带微趋势的随机游走）

        模拟效果：
        - 70% 时间在小幅波动
        - 偶尔出现一段持续的微趋势（连续涨/跌 5~20 个 tick）
        - 偶尔出现短暂的大波动（模拟成交异动）
        """
        state = self._states[symbol_key]
        cfg = DEFAULT_SYMBOL_CONFIGS.get(
            symbol_key,
            SymbolConfig(base_price=state.last_price),
        )

        # 微趋势切换
        if state.trend_remaining <= 0:
            if random.random() < 0.3:
                # 30% 概率进入一段趋势
                state.trend = random.choice([-1, 1]) * cfg.volatility * random.uniform(0.3, 1.0)
                state.trend_remaining = random.randint(5, 20)
            else:
                state.trend = 0.0
                state.trend_remaining = random.randint(3, 10)

        state.trend_remaining -= 1

        # 基础随机波动
        noise = random.gauss(0, cfg.volatility)

        # 偶尔大波动（2% 概率）
        if random.random() < 0.02:
            noise *= random.uniform(2.0, 4.0)

        # 叠加趋势
        change_pct = noise + state.trend * 0.3

        new_price = state.last_price * (1 + change_pct)

        # 价格不能为负
        new_price = max(new_price, state.last_price * 0.9)

        state.last_price = new_price

        # 更新买卖价
        spread = new_price * cfg.spread_pct
        state.bid_price = new_price - spread / 2
        state.ask_price = new_price + spread / 2

        return new_price

    # ── Tick 推送循环 ───────────────────────────────────────────

    async def _tick_loop(self) -> None:
        """定时生成并推送 tick 数据"""
        while self._running:
            try:
                await asyncio.sleep(self.tick_interval)

                for symbol_key, state in list(self._states.items()):
                    cfg = DEFAULT_SYMBOL_CONFIGS.get(
                        symbol_key,
                        SymbolConfig(base_price=state.last_price),
                    )

                    price = self._next_price(symbol_key)
                    now_ms = time.time() * 1000

                    # 模拟成交量
                    volume = cfg.base_volume * random.uniform(0.1, 3.0)

                    tick_data = {
                        "symbol": symbol_key,
                        "exchange": "mock",
                        "timestamp": now_ms,
                        "last_price": round(price, self._price_decimals(price)),
                        "bid_price": round(state.bid_price, self._price_decimals(price)),
                        "ask_price": round(state.ask_price, self._price_decimals(price)),
                        "bid_size": round(cfg.base_volume * random.uniform(0.5, 5.0), 4),
                        "ask_size": round(cfg.base_volume * random.uniform(0.5, 5.0), 4),
                        "volume": round(volume, 4),
                        "turnover": round(volume * price, 2),
                        "is_trade": True,
                        "trade_id": f"mock_{int(now_ms)}_{random.randint(1000, 9999)}",
                    }

                    # 更新 1m K 线缓存
                    self._update_kline_state(symbol_key, price, volume, now_ms)

                    await self._notify("tick", tick_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockDataCollector tick 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── Kline 推送循环 ──────────────────────────────────────────

    async def _kline_loop(self) -> None:
        """定时推送 K 线数据（每秒检查一次是否需要推送关闭的 K 线）"""
        while self._running:
            try:
                await asyncio.sleep(1.0)
                now_ms = time.time() * 1000

                for symbol_key, state in list(self._states.items()):
                    # 推送所有配置的 K 线周期
                    for interval in self.kline_intervals:
                        interval_ms = self._interval_to_ms(interval)
                        current_kline_start = (int(now_ms) // interval_ms) * interval_ms

                        # 判断当前 K 线是否已关闭
                        is_closed = False
                        if interval == "1m":
                            # 1m 由内部状态精确维护
                            if state.kline_start_ts < current_kline_start:
                                is_closed = True
                        else:
                            # 其他周期：在新周期开始的前 2 秒内推送上一个周期的关闭
                            time_in_period = now_ms - current_kline_start
                            if time_in_period < 2000:
                                is_closed = True

                        kline_data = {
                            "symbol": symbol_key,
                            "exchange": "mock",
                            "timestamp": state.kline_start_ts if interval == "1m" else float(current_kline_start),
                            "interval": interval,
                            "open": round(state.kline_open, self._price_decimals(state.kline_open)),
                            "high": round(state.kline_high, self._price_decimals(state.kline_high)),
                            "low": round(state.kline_low, self._price_decimals(state.kline_low)),
                            "close": round(state.kline_close, self._price_decimals(state.kline_close)),
                            "volume": round(state.kline_volume, 4),
                            "is_closed": is_closed,
                        }

                        await self._notify("kline", kline_data)

                    # 如果 1m K 线已关闭，重置状态
                    current_minute_start = (int(now_ms) // 60000) * 60000
                    if state.kline_start_ts < current_minute_start:
                        state.kline_open = state.last_price
                        state.kline_high = state.last_price
                        state.kline_low = state.last_price
                        state.kline_close = state.last_price
                        state.kline_volume = 0.0
                        state.kline_start_ts = float(current_minute_start)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockDataCollector kline 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── Depth 推送循环 ──────────────────────────────────────────

    async def _depth_loop(self) -> None:
        """定时生成并推送 depth 数据"""
        while self._running:
            try:
                await asyncio.sleep(self.depth_interval)

                for symbol_key, state in list(self._states.items()):
                    cfg = DEFAULT_SYMBOL_CONFIGS.get(
                        symbol_key,
                        SymbolConfig(base_price=state.last_price),
                    )

                    now_ms = time.time() * 1000
                    decimals = self._price_decimals(state.last_price)

                    # 生成买盘（由高到低）
                    bids = []
                    for i in range(cfg.depth_levels):
                        price = state.bid_price * (1 - i * cfg.spread_pct * 0.5)
                        size = cfg.base_volume * random.uniform(0.5, 10.0)
                        bids.append([round(price, decimals), round(size, 4)])

                    # 生成卖盘（由低到高）
                    asks = []
                    for i in range(cfg.depth_levels):
                        price = state.ask_price * (1 + i * cfg.spread_pct * 0.5)
                        size = cfg.base_volume * random.uniform(0.5, 10.0)
                        asks.append([round(price, decimals), round(size, 4)])

                    depth_data = {
                        "symbol": symbol_key,
                        "exchange": "mock",
                        "timestamp": now_ms,
                        "bids": bids,
                        "asks": asks,
                    }

                    await self._notify("depth", depth_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MockDataCollector depth 推送异常", error=str(e))
                await asyncio.sleep(1)

    # ── 工具方法 ────────────────────────────────────────────────

    def _update_kline_state(
        self, symbol_key: str, price: float, volume: float, now_ms: float,
    ) -> None:
        """更新 1m K 线内存状态"""
        state = self._states.get(symbol_key)
        if not state:
            return

        current_minute_start = (int(now_ms) // 60000) * 60000

        # 如果进入了新的一分钟，先重置
        if state.kline_start_ts < current_minute_start:
            state.kline_open = price
            state.kline_high = price
            state.kline_low = price
            state.kline_close = price
            state.kline_volume = volume
            state.kline_start_ts = float(current_minute_start)
        else:
            state.kline_high = max(state.kline_high, price)
            state.kline_low = min(state.kline_low, price)
            state.kline_close = price
            state.kline_volume += volume

    @staticmethod
    def _price_decimals(price: float) -> int:
        """根据价格量级决定小数位数"""
        if price >= 10000:
            return 2
        elif price >= 100:
            return 3
        elif price >= 1:
            return 4
        elif price >= 0.01:
            return 5
        else:
            return 8

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        """将 K 线周期字符串转为毫秒"""
        mapping = {
            "1m": 60_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "4h": 14_400_000,
            "1d": 86_400_000,
            "1w": 604_800_000,
        }
        return mapping.get(interval, 60_000)
