"""
策略基类
========

定义策略的抽象接口和生命周期管理
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Type

import structlog

from quant_trading_system.models.market import Bar, BarArray, Depth, Tick, TimeFrame
from quant_trading_system.models.trading import Order, Position, Trade
from quant_trading_system.models.account import Account
from quant_trading_system.services.strategy.signal import Signal, SignalType
from quant_trading_system.services.indicators.indicator_engine import IndicatorEngine
from quant_trading_system.core.snowflake import generate_snowflake_id

logger = structlog.get_logger(__name__)


class StrategyState(Enum):
    """策略状态"""

    CREATED = "created"         # 已创建
    INITIALIZING = "initializing"  # 初始化中
    READY = "ready"             # 就绪
    RUNNING = "running"         # 运行中
    PAUSED = "paused"           # 已暂停
    STOPPING = "stopping"       # 停止中
    STOPPED = "stopped"         # 已停止
    ERROR = "error"             # 错误


@dataclass
class StrategyContext:
    """
    策略上下文

    提供策略运行时所需的数据和服务
    """

    # 策略ID
    strategy_id: str

    # 交易品种
    symbols: list[str] = field(default_factory=list)

    # 时间周期
    timeframes: list[TimeFrame] = field(default_factory=list)

    # 账户信息
    account: Account | None = None

    # 持仓信息 {symbol: Position}
    positions: dict[str, Position] = field(default_factory=dict)

    # 活跃订单 {order_id: Order}
    active_orders: dict[str, Order] = field(default_factory=dict)

    # 指标引擎
    indicator_engine: IndicatorEngine | None = None

    # K线数据 {symbol: {timeframe: BarArray}}
    bars: dict[str, dict[TimeFrame, BarArray]] = field(default_factory=dict)

    # 最新Tick {symbol: Tick}
    latest_ticks: dict[str, Tick] = field(default_factory=dict)

    # 最新深度 {symbol: Depth}
    latest_depths: dict[str, Depth] = field(default_factory=dict)

    # 策略参数
    params: dict[str, Any] = field(default_factory=dict)

    # 运行模式
    is_backtest: bool = False

    # 当前时间（回测时使用）
    current_time: float = 0.0

    def get_position(self, symbol: str) -> Position | None:
        """获取持仓"""
        return self.positions.get(symbol)

    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame
    ) -> BarArray | None:
        """获取K线数据"""
        return self.bars.get(symbol, {}).get(timeframe)

    def get_latest_price(self, symbol: str) -> float:
        """获取最新价格"""
        tick = self.latest_ticks.get(symbol)
        if tick:
            return tick.last_price

        # 从K线获取
        for tf in [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15]:
            bars = self.get_bars(symbol, tf)
            if bars and len(bars) > 0:
                return float(bars.close[-1])

        return 0.0


@dataclass
class StrategyInfo:
    """策略信息"""

    strategy_id: str
    name: str
    description: str
    version: str
    author: str
    params: dict[str, Any]
    state: StrategyState
    created_at: float
    started_at: float = 0.0
    stopped_at: float = 0.0


class Strategy(ABC):
    """
    策略抽象基类

    所有策略都应继承此类并实现相应的方法
    """

    # 策略元信息
    name: ClassVar[str] = "strategy"
    description: ClassVar[str] = ""
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = ""

    # 参数定义
    params_def: ClassVar[dict[str, dict[str, Any]]] = {}

    # 订阅的数据
    symbols: ClassVar[list[str]] = []
    timeframes: ClassVar[list[TimeFrame]] = [TimeFrame.M1]

    def __init__(
        self,
        strategy_id: str | None = None,
        **params: Any,
    ) -> None:
        """
        初始化策略

        Args:
            strategy_id: 策略ID
            **params: 策略参数
        """
        self.strategy_id = strategy_id or str(generate_snowflake_id())
        self.params = self._validate_params(params)
        self.state = StrategyState.CREATED

        # 上下文
        self._context: StrategyContext | None = None

        # 统计
        self._signal_count = 0
        self._trade_count = 0

        # 时间戳
        self.created_at = time.time()
        self.started_at: float = 0
        self.stopped_at: float = 0

        logger.info(f"Strategy created",
                   strategy_id=self.strategy_id,
                   name=self.name)

    def _validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """验证并填充默认参数"""
        validated = {}

        for name, definition in self.params_def.items():
            if name in params:
                validated[name] = params[name]
            elif "default" in definition:
                validated[name] = definition["default"]
            elif definition.get("required", False):
                raise ValueError(f"Required parameter {name} not provided")

        return validated

    def set_context(self, context: StrategyContext) -> None:
        """设置策略上下文"""
        self._context = context

    @property
    def context(self) -> StrategyContext:
        """获取策略上下文"""
        if self._context is None:
            raise RuntimeError("Strategy context not set")
        return self._context

    # ========== 生命周期方法 ==========

    def on_init(self) -> None:
        """
        策略初始化

        在策略启动前调用，用于初始化资源
        """
        pass

    def on_start(self) -> None:
        """
        策略启动

        在策略开始运行时调用
        """
        pass

    def on_stop(self) -> None:
        """
        策略停止

        在策略停止时调用，用于清理资源
        """
        pass

    def on_pause(self) -> None:
        """
        策略暂停
        """
        pass

    def on_resume(self) -> None:
        """
        策略恢复
        """
        pass

    # ========== 数据事件方法 ==========

    @abstractmethod
    def on_bar(self, bar: Bar) -> Signal | list[Signal] | None:
        """
        K线数据回调

        当新的K线数据到达时调用

        Args:
            bar: K线数据

        Returns:
            交易信号或信号列表
        """
        pass

    def on_tick(self, tick: Tick) -> Signal | list[Signal] | None:
        """
        Tick数据回调

        当新的Tick数据到达时调用

        Args:
            tick: Tick数据

        Returns:
            交易信号或信号列表
        """
        return None

    def on_depth(self, depth: Depth) -> Signal | list[Signal] | None:
        """
        深度数据回调

        Args:
            depth: 深度数据

        Returns:
            交易信号或信号列表
        """
        return None

    # ========== 交易事件方法 ==========

    def on_order(self, order: Order) -> None:
        """
        订单状态更新回调

        Args:
            order: 订单对象
        """
        pass

    def on_trade(self, trade: Trade) -> None:
        """
        成交回调

        Args:
            trade: 成交记录
        """
        self._trade_count += 1

    def on_position(self, position: Position) -> None:
        """
        持仓更新回调

        Args:
            position: 持仓对象
        """
        pass

    # ========== 辅助方法 ==========

    def buy(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        stop_loss: float = 0,
        take_profit: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建买入信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
        )

    def sell(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建卖出信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            reason=reason,
        )

    def open_long(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        stop_loss: float = 0,
        take_profit: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建开多信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.OPEN_LONG,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
        )

    def open_short(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        stop_loss: float = 0,
        take_profit: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建开空信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.OPEN_SHORT,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reason=reason,
        )

    def close_long(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建平多信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.CLOSE_LONG,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            reason=reason,
        )

    def close_short(
        self,
        symbol: str,
        quantity: float = 0,
        price: float = 0,
        reason: str = "",
    ) -> Signal:
        """创建平空信号"""
        self._signal_count += 1
        return Signal(
            symbol=symbol,
            signal_type=SignalType.CLOSE_SHORT,
            strategy_id=self.strategy_id,
            strategy_name=self.name,
            quantity=quantity,
            price=price,
            reason=reason,
        )

    def calculate_indicator(
        self,
        indicator_name: str,
        symbol: str | None = None,
        timeframe: TimeFrame | None = None,
        **params: Any,
    ):
        """计算技术指标"""
        if self._context is None or self._context.indicator_engine is None:
            raise RuntimeError("Indicator engine not available")

        # 获取K线数据
        sym = symbol or (self.symbols[0] if self.symbols else None)
        tf = timeframe or (self.timeframes[0] if self.timeframes else TimeFrame.M1)

        if sym is None:
            raise ValueError("Symbol not specified")

        bars = self.context.get_bars(sym, tf)
        if bars is None or len(bars) == 0:
            raise ValueError(f"No bar data for {sym} {tf.value}")

        return self._context.indicator_engine.calculate(
            indicator_name, bars, **params
        )

    def get_position(self, symbol: str | None = None) -> Position | None:
        """获取持仓"""
        sym = symbol or (self.symbols[0] if self.symbols else None)
        if sym is None:
            return None
        return self.context.get_position(sym)

    def get_latest_price(self, symbol: str | None = None) -> float:
        """获取最新价格"""
        sym = symbol or (self.symbols[0] if self.symbols else None)
        if sym is None:
            return 0.0
        return self.context.get_latest_price(sym)

    @property
    def info(self) -> StrategyInfo:
        """获取策略信息"""
        return StrategyInfo(
            strategy_id=self.strategy_id,
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            params=self.params,
            state=self.state,
            created_at=self.created_at,
            started_at=self.started_at,
            stopped_at=self.stopped_at,
        )

    @property
    def stats(self) -> dict[str, Any]:
        """获取策略统计"""
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "state": self.state.value,
            "signal_count": self._signal_count,
            "trade_count": self._trade_count,
        }


# 策略注册表
_strategy_registry: dict[str, Type[Strategy]] = {}


def register_strategy(cls: Type[Strategy]) -> Type[Strategy]:
    """策略注册装饰器"""
    _strategy_registry[cls.name] = cls
    logger.debug(f"Strategy registered", name=cls.name)
    return cls


def get_strategy_class(name: str) -> Type[Strategy] | None:
    """获取策略类"""
    return _strategy_registry.get(name)


def list_strategies() -> list[str]:
    """列出所有注册的策略"""
    return list(_strategy_registry.keys())
