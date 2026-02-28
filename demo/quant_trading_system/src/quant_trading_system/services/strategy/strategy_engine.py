"""
策略引擎
========

管理策略的生命周期和执行
"""

import asyncio
import time
from collections import defaultdict
from typing import Any, Callable, Coroutine, Type

import structlog

from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.market import Bar, Depth, Tick, BarArray
from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.models.trading import Order, Position
from quant_trading_system.models.account import Account
from quant_trading_system.services.strategy.base import (
    Strategy,
    StrategyContext,
)
from quant_trading_system.core.enums import StrategyState
from quant_trading_system.services.strategy.signal import Signal
from quant_trading_system.services.indicators.indicator_engine import (
    IndicatorEngine,
    get_indicator_engine,
)

logger = structlog.get_logger(__name__)


# 信号回调类型
SignalCallback = Callable[[Signal], Coroutine[Any, Any, None]]


class StrategyEngine:
    """
    策略引擎

    负责：
    - 策略生命周期管理
    - 数据分发
    - 信号处理
    """

    def __init__(
        self,
        event_engine: EventEngine | None = None,
        indicator_engine: IndicatorEngine | None = None,
    ) -> None:
        self._event_engine = event_engine
        self._indicator_engine = indicator_engine or get_indicator_engine()

        # 策略实例 {strategy_id: Strategy}
        self._strategies: dict[str, Strategy] = {}

        # 策略订阅 {symbol: [strategy_id]}
        self._symbol_subscriptions: dict[str, list[str]] = defaultdict(list)

        # K线数据缓存 {symbol: {timeframe: BarArray}}
        self._bar_cache: dict[str, dict[KlineInterval, BarArray]] = defaultdict(dict)

        # K线缓存最大长度，超过时自动裁剪旧数据
        self._max_bar_count: int = 1000

        # 最新数据
        self._latest_ticks: dict[str, Tick] = {}
        self._latest_depths: dict[str, Depth] = {}

        # 账户和持仓
        self._account: Account | None = None
        # 持仓缓存 {(symbol, strategy_id): Position}
        self._positions: dict[tuple[str, str], Position] = {}
        # 全局持仓（按symbol，用于不带strategy_id的场景）
        self._global_positions: dict[str, Position] = {}

        # 信号回调
        self._signal_callbacks: list[SignalCallback] = []

        # 运行状态
        self._running = False

        # 统计
        self._bar_count = 0
        self._tick_count = 0
        self._signal_count = 0

    async def start(self) -> None:
        """启动策略引擎"""
        if self._running:
            return

        self._running = True

        # 注册事件处理器
        if self._event_engine:
            self._event_engine.register(EventType.BAR, self._on_bar_event)
            self._event_engine.register(EventType.TICK, self._on_tick_event)
            self._event_engine.register(EventType.DEPTH, self._on_depth_event)
            self._event_engine.register(EventType.ORDER, self._on_order_event)
            self._event_engine.register(EventType.POSITION, self._on_position_event)

        logger.info("Strategy engine started")

    async def stop(self) -> None:
        """停止策略引擎"""
        if not self._running:
            return

        # 停止所有策略
        for strategy_id in list(self._strategies.keys()):
            await self.stop_strategy(strategy_id)

        # 注销事件处理器，防止引擎停止后仍收到事件
        if self._event_engine:
            self._event_engine.unregister(EventType.BAR, self._on_bar_event)
            self._event_engine.unregister(EventType.TICK, self._on_tick_event)
            self._event_engine.unregister(EventType.DEPTH, self._on_depth_event)
            self._event_engine.unregister(EventType.ORDER, self._on_order_event)
            self._event_engine.unregister(EventType.POSITION, self._on_position_event)

        self._running = False
        logger.info("Strategy engine stopped")

    def add_strategy(
        self,
        strategy: Strategy | Type[Strategy],
        **params: Any,
    ) -> str:
        """
        添加策略

        Args:
            strategy: 策略实例或策略类
            **params: 策略参数（当传入策略类时使用）

        Returns:
            策略ID
        """
        # 如果传入的是类，创建实例
        if isinstance(strategy, type):
            strategy = strategy(**params)

        strategy_id = strategy.strategy_id

        if strategy_id in self._strategies:
            raise ValueError(f"Strategy {strategy_id} already exists")

        # 创建上下文
        context = StrategyContext(
            strategy_id=strategy_id,
            symbols=strategy.symbols,
            timeframes=strategy.timeframes,
            indicator_engine=self._indicator_engine,
            account=self._account,
            positions=self._positions,
            bars=self._bar_cache,
            latest_ticks=self._latest_ticks,
            latest_depths=self._latest_depths,
            params=strategy.params,
        )
        strategy.set_context(context)

        # 注册订阅
        for symbol in strategy.symbols:
            if strategy_id not in self._symbol_subscriptions[symbol]:
                self._symbol_subscriptions[symbol].append(strategy_id)

        self._strategies[strategy_id] = strategy

        logger.info(f"Strategy added",
                   strategy_id=strategy_id,
                   name=strategy.name)

        return strategy_id

    async def remove_strategy(self, strategy_id: str) -> None:
        """移除策略"""
        if strategy_id not in self._strategies:
            return

        strategy = self._strategies[strategy_id]

        # 如果策略正在运行，先等待停止完成
        if strategy.state in (StrategyState.RUNNING, StrategyState.PAUSED):
            await self.stop_strategy(strategy_id)

        # 移除订阅
        for symbol in strategy.symbols:
            if strategy_id in self._symbol_subscriptions[symbol]:
                self._symbol_subscriptions[symbol].remove(strategy_id)

        del self._strategies[strategy_id]

        logger.info(f"Strategy removed", strategy_id=strategy_id)

    async def start_strategy(self, strategy_id: str) -> None:
        """启动策略"""
        if strategy_id not in self._strategies:
            raise ValueError(f"Strategy {strategy_id} not found")

        strategy = self._strategies[strategy_id]

        if strategy.state == StrategyState.RUNNING:
            return

        try:
            # 初始化
            strategy.state = StrategyState.INITIALIZING
            strategy.on_init()

            # 启动
            strategy.state = StrategyState.RUNNING
            strategy.started_at = time.time()
            strategy.on_start()

            logger.info(f"Strategy started",
                       strategy_id=strategy_id,
                       name=strategy.name)

        except Exception as e:
            strategy.state = StrategyState.ERROR
            logger.exception(f"Strategy start failed",
                           strategy_id=strategy_id,
                           error=str(e))
            raise

    async def stop_strategy(self, strategy_id: str) -> None:
        """停止策略"""
        if strategy_id not in self._strategies:
            return

        strategy = self._strategies[strategy_id]

        if strategy.state == StrategyState.STOPPED:
            return

        try:
            strategy.state = StrategyState.STOPPING
            strategy.on_stop()

            strategy.state = StrategyState.STOPPED
            strategy.stopped_at = time.time()

            logger.info(f"Strategy stopped", strategy_id=strategy_id)

        except Exception as e:
            strategy.state = StrategyState.ERROR
            logger.exception(f"Strategy stop error",
                           strategy_id=strategy_id,
                           error=str(e))

    async def pause_strategy(self, strategy_id: str) -> None:
        """暂停策略"""
        if strategy_id not in self._strategies:
            return

        strategy = self._strategies[strategy_id]

        if strategy.state != StrategyState.RUNNING:
            return

        strategy.state = StrategyState.PAUSED
        strategy.on_pause()

        logger.info(f"Strategy paused", strategy_id=strategy_id)

    async def resume_strategy(self, strategy_id: str) -> None:
        """恢复策略"""
        if strategy_id not in self._strategies:
            return

        strategy = self._strategies[strategy_id]

        if strategy.state != StrategyState.PAUSED:
            return

        strategy.state = StrategyState.RUNNING
        strategy.on_resume()

        logger.info(f"Strategy resumed", strategy_id=strategy_id)

    def add_signal_callback(self, callback: SignalCallback) -> None:
        """添加信号回调"""
        self._signal_callbacks.append(callback)

    async def on_bar(self, bar: Bar) -> None:
        """处理K线数据"""
        self._bar_count += 1
        symbol = bar.symbol

        # 更新缓存
        if bar.timeframe not in self._bar_cache[symbol]:
            self._bar_cache[symbol][bar.timeframe] = BarArray(
                symbol=symbol,
                exchange=bar.exchange,
                timeframe=bar.timeframe,
            )

        bar_array = self._bar_cache[symbol][bar.timeframe]

        if bar.is_closed:
            bar_array.append(bar)
            # 裁剪超出最大长度的旧数据，避免内存无限增长
            if len(bar_array) > self._max_bar_count:
                bar_array.truncate(self._max_bar_count)
        else:
            bar_array.update_last(bar)

        # 分发给订阅的策略
        strategy_ids = self._symbol_subscriptions.get(symbol, [])

        for strategy_id in strategy_ids:
            strategy = self._strategies.get(strategy_id)
            if strategy and strategy.state == StrategyState.RUNNING:
                if bar.timeframe in strategy.timeframes:
                    await self._dispatch_bar(strategy, bar)

    async def on_tick(self, tick: Tick) -> None:
        """处理Tick数据"""
        self._tick_count += 1
        symbol = tick.symbol

        # 更新缓存
        self._latest_ticks[symbol] = tick

        # 分发给订阅的策略
        strategy_ids = self._symbol_subscriptions.get(symbol, [])

        for strategy_id in strategy_ids:
            strategy = self._strategies.get(strategy_id)
            if strategy and strategy.state == StrategyState.RUNNING:
                await self._dispatch_tick(strategy, tick)

    async def on_depth(self, depth: Depth) -> None:
        """处理深度数据"""
        symbol = depth.symbol

        # 更新缓存
        self._latest_depths[symbol] = depth

        # 分发给订阅的策略
        strategy_ids = self._symbol_subscriptions.get(symbol, [])

        for strategy_id in strategy_ids:
            strategy = self._strategies.get(strategy_id)
            if strategy and strategy.state == StrategyState.RUNNING:
                await self._dispatch_depth(strategy, depth)

    async def _dispatch_bar(self, strategy: Strategy, bar: Bar) -> None:
        """分发K线给策略（在线程池中执行，避免阻塞事件循环）"""
        try:
            loop = asyncio.get_running_loop()
            signals = await loop.run_in_executor(None, strategy.on_bar, bar)
            await self._process_signals(signals)
        except Exception as e:
            logger.exception(f"Strategy on_bar error",
                           strategy_id=strategy.strategy_id,
                           error=str(e))

    async def _dispatch_tick(self, strategy: Strategy, tick: Tick) -> None:
        """分发Tick给策略（在线程池中执行，避免阻塞事件循环）"""
        try:
            loop = asyncio.get_running_loop()
            signals = await loop.run_in_executor(None, strategy.on_tick, tick)
            await self._process_signals(signals)
        except Exception as e:
            logger.exception(f"Strategy on_tick error",
                           strategy_id=strategy.strategy_id,
                           error=str(e))

    async def _dispatch_depth(self, strategy: Strategy, depth: Depth) -> None:
        """分发深度给策略（在线程池中执行，避免阻塞事件循环）"""
        try:
            loop = asyncio.get_running_loop()
            signals = await loop.run_in_executor(None, strategy.on_depth, depth)
            await self._process_signals(signals)
        except Exception as e:
            logger.exception(f"Strategy on_depth error",
                           strategy_id=strategy.strategy_id,
                           error=str(e))

    async def _process_signals(
        self,
        signals: Signal | list[Signal] | None
    ) -> None:
        """处理策略产生的信号"""
        if signals is None:
            return

        if isinstance(signals, Signal):
            signals = [signals]

        for signal in signals:
            self._signal_count += 1

            # 发送事件
            if self._event_engine:
                await self._event_engine.put(Event(
                    type=EventType.SIGNAL,
                    data=signal,
                ))

            # 调用回调
            if self._signal_callbacks:
                tasks = [cb(signal) for cb in self._signal_callbacks]
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _on_bar_event(self, event: Event) -> None:
        """K线事件处理器"""
        bar = event.data
        if isinstance(bar, Bar):
            await self.on_bar(bar)

    async def _on_tick_event(self, event: Event) -> None:
        """Tick事件处理器"""
        tick = event.data
        if isinstance(tick, Tick):
            await self.on_tick(tick)

    async def _on_depth_event(self, event: Event) -> None:
        """深度事件处理器"""
        depth = event.data
        if isinstance(depth, Depth):
            await self.on_depth(depth)

    async def _on_order_event(self, event: Event) -> None:
        """订单事件处理器"""
        order = event.data
        if isinstance(order, Order):
            strategy = self._strategies.get(order.strategy_id)
            if strategy:
                strategy.on_order(order)

    async def _on_position_event(self, event: Event) -> None:
        """持仓事件处理器"""
        position = event.data
        if isinstance(position, Position):
            # 更新全局持仓缓存（按symbol）
            self._global_positions[position.symbol] = position

            # 更新策略级持仓缓存（按(symbol, strategy_id)），避免多策略同品种覆盖
            strategy_id = getattr(position, 'strategy_id', '')
            if strategy_id:
                self._positions[(position.symbol, strategy_id)] = position
                # 通知对应策略
                strategy = self._strategies.get(strategy_id)
                if strategy:
                    strategy.on_position(position)
            else:
                # 没有strategy_id时，通知所有订阅该symbol的策略
                strategy_ids = self._symbol_subscriptions.get(position.symbol, [])
                for sid in strategy_ids:
                    strategy = self._strategies.get(sid)
                    if strategy:
                        strategy.on_position(position)

    def set_account(self, account: Account) -> None:
        """设置账户"""
        self._account = account

        # 更新所有策略的上下文
        for strategy in self._strategies.values():
            if strategy._context:
                strategy._context.account = account

    def update_position(self, position: Position) -> None:
        """更新持仓"""
        self._global_positions[position.symbol] = position
        strategy_id = getattr(position, 'strategy_id', '')
        if strategy_id:
            self._positions[(position.symbol, strategy_id)] = position

    def get_strategy(self, strategy_id: str) -> Strategy | None:
        """获取策略"""
        return self._strategies.get(strategy_id)

    def list_strategies(self) -> list[str]:
        """列出所有策略ID"""
        return list(self._strategies.keys())

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        strategy_stats = {}
        for sid, strategy in self._strategies.items():
            strategy_stats[sid] = {
                "name": strategy.name,
                "state": strategy.state.value,
                "signal_count": strategy._signal_count,
            }

        return {
            "running": self._running,
            "strategy_count": len(self._strategies),
            "bar_count": self._bar_count,
            "tick_count": self._tick_count,
            "signal_count": self._signal_count,
            "strategies": strategy_stats,
        }
