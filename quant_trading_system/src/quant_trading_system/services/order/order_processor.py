"""
订单处理器
==========

统一的订单处理管道，适用于回测/模拟/实盘三种模式。
负责：
- 信号 → 订单转换
- Position Sizing（仓位大小计算）
- 风控检查（委托 RiskManager）
- 订单执行（委托 OrderExecutor）
- 仓位更新（委托 PositionManager）
- 账户更新（委托 AccountManager）
- 事件发布

数据流：Signal → OrderProcessor → OrderExecutor → PositionManager + AccountManager → 事件
"""

from typing import Any, TYPE_CHECKING

import structlog

from quant_trading_system.core.enums import OrderSide, OrderType, SignalType
from quant_trading_system.engines.event_engine import Event, EventEngine, EventType
from quant_trading_system.core.snowflake import generate_backtest_snowflake_id
from quant_trading_system.models.trading import Order, Trade
from quant_trading_system.services.order.order_executor import (
    OrderExecutor,
    ExecutionResult,
)
from quant_trading_system.services.order.position_manager import PositionManager
from quant_trading_system.services.order.account_manager import AccountManager
from quant_trading_system.strategy import StrategySignal

if TYPE_CHECKING:
    from quant_trading_system.services.risk.risk_manager import RiskManager

logger = structlog.get_logger(__name__)


class OrderProcessorConfig:
    """订单处理器配置"""

    def __init__(
        self,
        position_sizing: str = "fixed",  # fixed, percent, kelly
        fixed_quantity: float = 1.0,
        percent_risk: float = 0.02,
    ) -> None:
        self.position_sizing = position_sizing
        self.fixed_quantity = fixed_quantity
        self.percent_risk = percent_risk


class OrderProcessor:
    """
    统一订单处理器

    接收策略信号，经过完整的处理管道：
    1. 信号验证
    2. 仓位大小计算（Position Sizing）
    3. 创建订单
    4. 风控检查（事前风控）
    5. 订单执行
    6. 仓位更新
    7. 账户更新
    8. 发布事件
    """

    def __init__(
        self,
        executor: OrderExecutor,
        position_manager: PositionManager,
        account_manager: AccountManager,
        event_engine: EventEngine | None = None,
        risk_manager: "RiskManager | None" = None,
        config: OrderProcessorConfig | None = None,
    ) -> None:
        self._executor = executor
        self._position_manager = position_manager
        self._account_manager = account_manager
        self._event_engine = event_engine
        self._risk_manager = risk_manager
        self._config = config or OrderProcessorConfig()

        # 订单和成交记录
        self._orders: list[Order] = []
        self._trades: list[Trade] = []

        # 统计
        self._total_commission: float = 0.0
        self._total_slippage: float = 0.0
        self._signal_count: int = 0
        self._order_count: int = 0

    async def process_signal(self, signal: StrategySignal, market_price: float) -> ExecutionResult | None:
        """
        处理交易信号（完整管道）

        Args:
            signal: 交易信号
            market_price: 当前市场价格

        Returns:
            执行结果，如果信号被过滤则返回 None
        """
        self._signal_count += 1

        # 1. 信号验证
        if not self._validate_signal(signal, market_price):
            return None

        # 2. 计算交易数量
        quantity = self._calculate_quantity(signal, market_price)
        if quantity <= 0:
            logger.debug("信号被过滤：计算数量为0", timestamp=signal.timestamp)
            return None

        # 3. 创建订单
        order = self._create_order(signal, quantity, market_price)
        self._orders.append(order)
        self._order_count += 1

        # 4. 风控检查（事前风控）
        if self._risk_manager:
            risk_result = self._risk_manager.check_order(order, market_price)
            if not risk_result.passed:
                logger.warning(
                    "订单被风控拒绝",
                    order_id=order.order_id,
                    reasons=risk_result.messages,
                )
                return None
            # 通知风控订单已提交
            self._risk_manager.on_order_submitted(order)

        # 5. 执行订单
        result = await self._executor.execute(order, market_price)

        if not result.success:
            logger.warning(
                "订单执行失败",
                order_id=order.order_id,
                message=result.message,
            )
            return result

        # 6. 记录成交
        if result.trade:
            self._trades.append(result.trade)
            self._total_commission += result.commission
            self._total_slippage += result.slippage

            # 7. 更新仓位
            position = self._position_manager.update_from_trade(result.trade)

            # 8. 更新账户
            self._account_manager.update_from_trade(result.trade)

            # 9. 发布事件
            await self._publish_events(result, position)

        return result

    def process_signal_sync(self, signal: StrategySignal, market_price: float) -> ExecutionResult | None:
        """
        同步处理交易信号（用于回测模式，无需 async）

        Args:
            signal: 交易信号
            market_price: 当前市场价格

        Returns:
            执行结果
        """
        self._signal_count += 1

        # 1. 信号验证
        if not self._validate_signal(signal, market_price):
            return None

        # 2. 计算交易数量
        quantity = self._calculate_quantity(signal, market_price)
        if quantity <= 0:
            return None

        # 3. 创建订单
        order = self._create_order(signal, quantity, market_price)
        self._orders.append(order)
        self._order_count += 1

        # 4. 风控检查
        if self._risk_manager:
            risk_result = self._risk_manager.check_order(order, market_price)
            if not risk_result.passed:
                logger.warning(
                    "订单被风控拒绝",
                    order_id=order.order_id,
                    reasons=risk_result.messages,
                )
                return None
            self._risk_manager.on_order_submitted(order)

        # 5. 同步执行（回测模式下直接调用同步方法，避免每次创建事件循环）
        if hasattr(self._executor, 'execute_sync'):
            result = self._executor.execute_sync(order, market_price)
        else:
            # 兜底：非 BacktestExecutor 时仍走事件循环
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(self._executor.execute(order, market_price))
            finally:
                loop.close()

        if not result.success:
            return result

        # 6. 记录成交
        if result.trade:
            self._trades.append(result.trade)
            self._total_commission += result.commission
            self._total_slippage += result.slippage

            # 7. 更新仓位
            self._position_manager.update_from_trade(result.trade)

            # 8. 更新账户
            self._account_manager.update_from_trade(result.trade)

        return result

    def _validate_signal(self, signal: StrategySignal, market_price: float) -> bool:
        """验证信号有效性"""
        if market_price <= 0:
            logger.warning("无效的市场价格", timestamp=signal.timestamp)
            return False

        if signal.is_expired:
            logger.warning("信号已过期", timestamp=signal.timestamp)
            return False

        # 卖出时检查是否有持仓
        if signal.is_sell:
            position = self._position_manager.get_position(signal.symbol)
            if position is None or position.quantity <= 0:
                logger.debug("无持仓，跳过卖出信号", symbol=signal.symbol)
                return False

        return True

    def _calculate_quantity(self, signal: StrategySignal, price: float) -> float:
        """
        计算交易数量（Position Sizing）

        Args:
            signal: 交易信号
            price: 市场价格

        Returns:
            交易数量
        """
        # 如果信号指定了数量，直接使用
        if signal.quantity > 0:
            # 卖出时限制不超过持仓量
            if signal.is_sell:
                position = self._position_manager.get_position(signal.symbol)
                if position:
                    return min(signal.quantity, position.quantity)
            return signal.quantity

        if self._config.position_sizing == "fixed":
            quantity = self._config.fixed_quantity
        elif self._config.position_sizing == "percent":
            # 按风险百分比计算
            total_position_value = self._position_manager.get_total_position_value()
            equity = self._account_manager.calculate_equity(total_position_value)
            risk_amount = equity * self._config.percent_risk
            quantity = risk_amount / price if price > 0 else 0
        else:
            quantity = self._config.fixed_quantity

        # 卖出时限制不超过持仓量
        if signal.is_sell:
            position = self._position_manager.get_position(signal.symbol)
            if position:
                quantity = min(quantity, position.quantity)
            else:
                quantity = 0

        return quantity

    def _create_order(self, signal: StrategySignal, quantity: float, market_price: float) -> Order:
        """
        从信号创建订单

        Args:
            signal: 交易信号
            quantity: 交易数量
            market_price: 市场价格

        Returns:
            订单对象
        """
        # 确定订单方向
        if signal.signal_type in (SignalType.BUY, SignalType.OPEN_LONG, SignalType.CLOSE_SHORT):
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL

        # 确定订单类型和价格
        if signal.price > 0:
            order_type = OrderType.LIMIT
            price = signal.price
        else:
            order_type = OrderType.MARKET
            price = market_price

        return Order(
            order_id=str(generate_backtest_snowflake_id()),
            symbol=signal.symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            strategy_id=signal.strategy_id,
        )

    async def _publish_events(self, result: ExecutionResult, position: Any) -> None:
        """发布订单和持仓事件"""
        if self._event_engine is None:
            return

        # 发布订单成交事件
        if result.trade:
            await self._event_engine.put(Event(
                type=EventType.ORDER_FILLED,
                data=result.trade,
            ))

        # 发布持仓更新事件
        if position:
            await self._event_engine.put(Event(
                type=EventType.POSITION_UPDATE,
                data=position,
            ))

    def set_executor(self, executor: OrderExecutor) -> None:
        """切换执行器"""
        self._executor = executor

    def set_risk_manager(self, risk_manager: "RiskManager") -> None:
        """设置风控管理器"""
        self._risk_manager = risk_manager

    def set_config(self, config: OrderProcessorConfig) -> None:
        """设置配置"""
        self._config = config

    @property
    def orders(self) -> list[Order]:
        """获取所有订单"""
        return self._orders

    @property
    def trades(self) -> list[Trade]:
        """获取所有成交记录"""
        return self._trades

    @property
    def total_commission(self) -> float:
        """获取总手续费"""
        return self._total_commission

    @property
    def total_slippage(self) -> float:
        """获取总滑点"""
        return self._total_slippage

    @property
    def position_manager(self) -> PositionManager:
        """获取仓位管理器"""
        return self._position_manager

    @property
    def account_manager(self) -> AccountManager:
        """获取账户管理器"""
        return self._account_manager

    def reset(self) -> None:
        """重置状态（用于回测重新运行）"""
        self._orders.clear()
        self._trades.clear()
        self._total_commission = 0.0
        self._total_slippage = 0.0
        self._signal_count = 0
        self._order_count = 0
        self._position_manager.reset()
        self._account_manager.reset()

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "signal_count": self._signal_count,
            "order_count": self._order_count,
            "trade_count": len(self._trades),
            "total_commission": self._total_commission,
            "total_slippage": self._total_slippage,
            "position_stats": self._position_manager.stats,
            "account_stats": self._account_manager.stats,
        }
