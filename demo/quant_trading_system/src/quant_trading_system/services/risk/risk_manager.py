"""
风险管理器
==========

多层次风险控制系统，包括：
- 事前风控：订单验证
- 事中风控：实时监控
- 事后风控：风险分析
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.trading import Order, OrderSide, Position
from quant_trading_system.models.account import Account

logger = structlog.get_logger(__name__)


class RiskLevel(Enum):
    """风险级别"""

    NORMAL = "normal"       # 正常
    WARNING = "warning"     # 警告
    ALERT = "alert"         # 告警
    CRITICAL = "critical"   # 危险
    EMERGENCY = "emergency" # 紧急


@dataclass
class RiskConfig:
    """风险配置"""

    # 仓位限制
    max_position_value: float = 1000000.0    # 最大持仓市值
    max_position_ratio: float = 0.8          # 最大仓位比例
    max_single_position_ratio: float = 0.2   # 单品种最大仓位比例

    # 订单限制
    max_order_value: float = 100000.0        # 单笔订单最大金额
    max_order_quantity: float = 1000.0       # 单笔订单最大数量
    max_orders_per_minute: int = 60          # 每分钟最大订单数
    max_orders_per_day: int = 1000           # 每日最大订单数

    # 亏损限制
    max_daily_loss: float = 50000.0          # 每日最大亏损
    max_daily_loss_ratio: float = 0.05       # 每日最大亏损比例
    max_drawdown: float = 0.2                # 最大回撤

    # 频率限制
    min_order_interval: float = 0.1          # 最小订单间隔（秒）

    # 价格限制
    max_price_deviation: float = 0.1         # 最大价格偏离


@dataclass
class RiskMetrics:
    """风险指标"""

    # 仓位指标
    total_position_value: float = 0.0
    position_ratio: float = 0.0

    # 盈亏指标
    daily_pnl: float = 0.0
    daily_pnl_ratio: float = 0.0
    current_drawdown: float = 0.0

    # 订单指标
    orders_today: int = 0
    orders_this_minute: int = 0

    # 风险级别
    risk_level: RiskLevel = RiskLevel.NORMAL

    # 时间
    update_time: float = 0.0


@dataclass
class RiskCheckResult:
    """风险检查结果"""

    passed: bool = True
    risk_level: RiskLevel = RiskLevel.NORMAL
    messages: list[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        self.messages.append(f"[WARNING] {message}")
        if self.risk_level.value < RiskLevel.WARNING.value:
            self.risk_level = RiskLevel.WARNING

    def add_alert(self, message: str) -> None:
        self.messages.append(f"[ALERT] {message}")
        self.risk_level = RiskLevel.ALERT

    def reject(self, message: str) -> None:
        self.passed = False
        self.messages.append(f"[REJECT] {message}")
        self.risk_level = RiskLevel.CRITICAL


class RiskManager:
    """
    风险管理器

    提供多层次的风险控制
    """

    def __init__(
        self,
        config: RiskConfig | None = None,
        event_engine: EventEngine | None = None,
    ) -> None:
        self.config = config or RiskConfig()
        self._event_engine = event_engine

        # 账户
        self._account: Account | None = None

        # 持仓
        self._positions: dict[str, Position] = {}

        # 风险指标
        self._metrics = RiskMetrics()

        # 订单记录（用于频率限制）
        self._order_times: list[float] = []
        self._daily_order_count = 0
        self._last_order_time = 0.0

        # 盈亏记录
        self._initial_equity = 0.0
        self._peak_equity = 0.0
        self._daily_start_equity = 0.0

        # 风险状态
        self._risk_level = RiskLevel.NORMAL
        self._trading_enabled = True

    def set_account(self, account: Account) -> None:
        """设置账户"""
        self._account = account

        # 初始化权益记录
        if self._initial_equity == 0:
            self._initial_equity = account.total_balance
            self._peak_equity = account.total_balance
            self._daily_start_equity = account.total_balance

    def update_position(self, position: Position) -> None:
        """更新持仓"""
        self._positions[position.symbol] = position
        self._update_metrics()

    def check_order(self, order: Order, current_price: float = 0) -> RiskCheckResult:
        """
        事前风控：检查订单

        Args:
            order: 订单对象
            current_price: 当前市场价格

        Returns:
            检查结果
        """
        result = RiskCheckResult()

        # 检查交易是否启用
        if not self._trading_enabled:
            result.reject("Trading is disabled due to risk limit")
            return result

        # 检查订单金额
        order_value = order.quantity * (order.price or current_price)
        if order_value > self.config.max_order_value:
            result.reject(
                f"Order value {order_value:.2f} exceeds limit "
                f"{self.config.max_order_value:.2f}"
            )
            return result

        # 检查订单数量
        if order.quantity > self.config.max_order_quantity:
            result.reject(
                f"Order quantity {order.quantity:.4f} exceeds limit "
                f"{self.config.max_order_quantity:.4f}"
            )
            return result

        # 检查订单频率
        current_time = time.time()

        # 最小间隔检查
        if current_time - self._last_order_time < self.config.min_order_interval:
            result.reject(
                f"Order interval too short, minimum: "
                f"{self.config.min_order_interval}s"
            )
            return result

        # 每分钟订单数检查
        one_minute_ago = current_time - 60
        recent_orders = sum(1 for t in self._order_times if t > one_minute_ago)
        if recent_orders >= self.config.max_orders_per_minute:
            result.reject(
                f"Orders per minute ({recent_orders}) exceeds limit "
                f"({self.config.max_orders_per_minute})"
            )
            return result

        # 每日订单数检查
        if self._daily_order_count >= self.config.max_orders_per_day:
            result.reject(
                f"Daily orders ({self._daily_order_count}) exceeds limit "
                f"({self.config.max_orders_per_day})"
            )
            return result

        # 检查仓位限制（买入订单）
        if order.side == OrderSide.BUY:
            new_position_value = (
                self._metrics.total_position_value + order_value
            )

            if self._account:
                new_ratio = new_position_value / self._account.total_balance
                if new_ratio > self.config.max_position_ratio:
                    result.reject(
                        f"Position ratio {new_ratio:.2%} would exceed limit "
                        f"{self.config.max_position_ratio:.2%}"
                    )
                    return result

        # 检查价格偏离
        if current_price > 0 and order.price > 0:
            deviation = abs(order.price - current_price) / current_price
            if deviation > self.config.max_price_deviation:
                result.add_warning(
                    f"Price deviation {deviation:.2%} exceeds threshold "
                    f"{self.config.max_price_deviation:.2%}"
                )

        # 检查当日亏损
        if self._metrics.daily_pnl < -self.config.max_daily_loss:
            result.add_alert(
                f"Daily loss {-self._metrics.daily_pnl:.2f} exceeds limit"
            )

        # 检查回撤
        if self._metrics.current_drawdown > self.config.max_drawdown * 0.8:
            result.add_warning(
                f"Drawdown {self._metrics.current_drawdown:.2%} approaching limit"
            )

        return result

    def on_order_submitted(self, order: Order) -> None:
        """订单提交后更新"""
        current_time = time.time()

        self._order_times.append(current_time)
        self._last_order_time = current_time
        self._daily_order_count += 1

        # 清理旧的订单时间记录
        one_minute_ago = current_time - 60
        self._order_times = [t for t in self._order_times if t > one_minute_ago]

    def update_equity(self, equity: float) -> None:
        """更新权益"""
        # 更新峰值
        if equity > self._peak_equity:
            self._peak_equity = equity

        # 计算回撤
        if self._peak_equity > 0:
            self._metrics.current_drawdown = (
                (self._peak_equity - equity) / self._peak_equity
            )

        # 计算当日盈亏
        self._metrics.daily_pnl = equity - self._daily_start_equity
        if self._daily_start_equity > 0:
            self._metrics.daily_pnl_ratio = (
                self._metrics.daily_pnl / self._daily_start_equity
            )

        # 检查是否触发熔断
        self._check_circuit_breaker()

    def _update_metrics(self) -> None:
        """更新风险指标"""
        # 计算总持仓市值
        total_value = 0.0
        for position in self._positions.values():
            total_value += position.notional_value

        self._metrics.total_position_value = total_value

        # 计算仓位比例
        if self._account and self._account.total_balance > 0:
            self._metrics.position_ratio = (
                total_value / self._account.total_balance
            )

        self._metrics.update_time = time.time() * 1000

        # 更新风险级别
        self._update_risk_level()

    def _update_risk_level(self) -> None:
        """更新风险级别"""
        level = RiskLevel.NORMAL

        # 检查仓位
        if self._metrics.position_ratio > self.config.max_position_ratio * 0.9:
            level = RiskLevel.WARNING
        if self._metrics.position_ratio > self.config.max_position_ratio:
            level = RiskLevel.ALERT

        # 检查亏损
        if self._metrics.daily_pnl_ratio < -self.config.max_daily_loss_ratio * 0.8:
            level = max(level, RiskLevel.WARNING, key=lambda x: x.value)
        if self._metrics.daily_pnl_ratio < -self.config.max_daily_loss_ratio:
            level = max(level, RiskLevel.ALERT, key=lambda x: x.value)

        # 检查回撤
        if self._metrics.current_drawdown > self.config.max_drawdown * 0.8:
            level = max(level, RiskLevel.WARNING, key=lambda x: x.value)
        if self._metrics.current_drawdown > self.config.max_drawdown:
            level = max(level, RiskLevel.CRITICAL, key=lambda x: x.value)

        self._metrics.risk_level = level
        self._risk_level = level

    def _check_circuit_breaker(self) -> None:
        """检查熔断条件"""
        should_disable = False
        reason = ""

        # 检查回撤熔断
        if self._metrics.current_drawdown > self.config.max_drawdown:
            should_disable = True
            reason = f"Max drawdown exceeded: {self._metrics.current_drawdown:.2%}"

        # 检查每日亏损熔断
        if self._metrics.daily_pnl < -self.config.max_daily_loss:
            should_disable = True
            reason = f"Max daily loss exceeded: {-self._metrics.daily_pnl:.2f}"

        if should_disable and self._trading_enabled:
            self._trading_enabled = False
            self._risk_level = RiskLevel.EMERGENCY

            logger.critical(f"Circuit breaker triggered", reason=reason)

            # 发送风险事件
            if self._event_engine:
                import asyncio
                asyncio.create_task(self._event_engine.put(Event(
                    type=EventType.RISK_BREACH,
                    data={"reason": reason, "level": RiskLevel.EMERGENCY},
                )))

    def reset_daily(self) -> None:
        """重置每日统计"""
        if self._account:
            self._daily_start_equity = self._account.total_balance

        self._daily_order_count = 0
        self._metrics.daily_pnl = 0
        self._metrics.daily_pnl_ratio = 0

        # 重新启用交易（如果是每日熔断）
        if self._metrics.current_drawdown <= self.config.max_drawdown:
            self._trading_enabled = True

    def enable_trading(self) -> None:
        """启用交易"""
        self._trading_enabled = True
        logger.info("Trading enabled")

    def disable_trading(self, reason: str = "") -> None:
        """禁用交易"""
        self._trading_enabled = False
        logger.warning(f"Trading disabled", reason=reason)

    @property
    def is_trading_enabled(self) -> bool:
        return self._trading_enabled

    @property
    def risk_level(self) -> RiskLevel:
        return self._risk_level

    @property
    def metrics(self) -> RiskMetrics:
        return self._metrics

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "trading_enabled": self._trading_enabled,
            "risk_level": self._risk_level.value,
            "total_position_value": self._metrics.total_position_value,
            "position_ratio": self._metrics.position_ratio,
            "daily_pnl": self._metrics.daily_pnl,
            "daily_pnl_ratio": self._metrics.daily_pnl_ratio,
            "current_drawdown": self._metrics.current_drawdown,
            "orders_today": self._daily_order_count,
        }
