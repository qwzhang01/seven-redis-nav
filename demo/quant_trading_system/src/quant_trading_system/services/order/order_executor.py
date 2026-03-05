"""
订单执行器
==========

定义订单执行器的抽象接口和三种模式的实现：
- BacktestExecutor: 回测模式（滑点+手续费模拟成交）
- SimulationExecutor: 模拟交易模式（延迟模拟成交）
- LiveExecutor: 实盘交易模式（通过 Gateway 提交）
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog

from quant_trading_system.core.enums import OrderSide, OrderStatus
from quant_trading_system.models.trading import Order, Trade
from quant_trading_system.core.snowflake import generate_backtest_snowflake_id

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionConfig:
    """执行配置"""

    # 手续费率
    commission_rate: float = 0.0004
    min_commission: float = 0.0

    # 滑点配置
    slippage_rate: float = 0.0001  # 滑点比例
    slippage_fixed: float = 0.0    # 固定滑点


@dataclass
class ExecutionResult:
    """执行结果"""

    success: bool = False
    order: Order | None = None
    trade: Trade | None = None
    fill_price: float = 0.0
    fill_quantity: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    message: str = ""


class OrderExecutor(ABC):
    """
    订单执行器抽象基类

    不同模式（回测/模拟/实盘）实现不同的执行逻辑
    """

    def __init__(self, config: ExecutionConfig | None = None) -> None:
        self.config = config or ExecutionConfig()

    @abstractmethod
    async def execute(self, order: Order, market_price: float) -> ExecutionResult:
        """
        执行订单

        Args:
            order: 订单对象
            market_price: 当前市场价格

        Returns:
            执行结果
        """
        pass

    def _calculate_slippage(self, price: float, side: OrderSide) -> tuple[float, float]:
        """
        计算滑点

        Args:
            price: 市场价格
            side: 订单方向

        Returns:
            (执行价格, 滑点金额)
        """
        slippage = price * self.config.slippage_rate + self.config.slippage_fixed

        if side == OrderSide.BUY:
            exec_price = price + slippage
        else:
            exec_price = price - slippage

        return exec_price, abs(slippage)

    def _calculate_commission(self, quantity: float, price: float) -> float:
        """
        计算手续费

        Args:
            quantity: 成交数量
            price: 成交价格

        Returns:
            手续费
        """
        return max(
            quantity * price * self.config.commission_rate,
            self.config.min_commission
        )


class BacktestExecutor(OrderExecutor):
    """
    回测执行器

    立即模拟成交，计算滑点和手续费
    """

    def execute_sync(self, order: Order, market_price: float) -> ExecutionResult:
        """回测模式同步执行：立即成交（无需事件循环，性能更优）"""
        return self._do_execute(order, market_price)

    async def execute(self, order: Order, market_price: float) -> ExecutionResult:
        """回测模式：立即成交（async 接口兼容）"""
        return self._do_execute(order, market_price)

    def _do_execute(self, order: Order, market_price: float) -> ExecutionResult:
        """回测执行核心逻辑"""
        result = ExecutionResult()

        if market_price <= 0:
            result.message = "无效的市场价格"
            return result

        # 计算滑点
        fill_price, slippage = self._calculate_slippage(market_price, order.side)

        # 计算手续费
        commission = self._calculate_commission(order.quantity, fill_price)

        # 创建成交记录
        trade = Trade(
            trade_id=str(generate_backtest_snowflake_id()),
            symbol=order.symbol,
            exchange="backtest",
            order_id=order.order_id,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            amount=order.quantity * fill_price,
            commission=commission,
            strategy_id=order.strategy_id,
        )

        # 更新订单状态
        order.status = OrderStatus.FILLED
        order.update_fill(order.quantity, fill_price, commission)

        result.success = True
        result.order = order
        result.trade = trade
        result.fill_price = fill_price
        result.fill_quantity = order.quantity
        result.commission = commission
        result.slippage = slippage

        logger.debug(
            "回测成交",
            side=order.side.value,
            symbol=order.symbol,
            price=f"{fill_price:.4f}",
            quantity=f"{order.quantity:.6f}",
            commission=f"{commission:.4f}",
        )

        return result


class SimulationExecutor(OrderExecutor):
    """
    模拟交易执行器

    模拟延迟成交，计算滑点和手续费
    """

    def __init__(
        self,
        config: ExecutionConfig | None = None,
        simulated_delay: float = 0.01,
    ) -> None:
        super().__init__(config)
        self._simulated_delay = simulated_delay

    async def execute(self, order: Order, market_price: float) -> ExecutionResult:
        """模拟交易模式：带延迟的模拟成交"""
        result = ExecutionResult()

        if market_price <= 0:
            result.message = "无效的市场价格"
            return result

        # 模拟延迟
        await asyncio.sleep(self._simulated_delay)

        # 计算滑点
        fill_price, slippage = self._calculate_slippage(market_price, order.side)

        # 计算手续费
        commission = self._calculate_commission(order.quantity, fill_price)

        # 创建成交记录
        trade = Trade(
            trade_id=str(generate_backtest_snowflake_id()),
            symbol=order.symbol,
            exchange="simulation",
            order_id=order.order_id,
            side=order.side,
            price=fill_price,
            quantity=order.quantity,
            amount=order.quantity * fill_price,
            commission=commission,
            strategy_id=order.strategy_id,
        )

        # 更新订单状态
        order.status = OrderStatus.FILLED
        order.update_fill(order.quantity, fill_price, commission)

        result.success = True
        result.order = order
        result.trade = trade
        result.fill_price = fill_price
        result.fill_quantity = order.quantity
        result.commission = commission
        result.slippage = slippage

        logger.info(
            "模拟成交",
            side=order.side.value,
            symbol=order.symbol,
            price=f"{fill_price:.4f}",
            quantity=f"{order.quantity:.6f}",
        )

        return result


class LiveExecutor(OrderExecutor):
    """
    实盘执行器

    通过交易所网关提交订单
    """

    def __init__(
        self,
        config: ExecutionConfig | None = None,
        gateway: Any = None,
    ) -> None:
        super().__init__(config)
        self._gateway = gateway

    def set_gateway(self, gateway: Any) -> None:
        """设置交易所网关"""
        self._gateway = gateway

    async def execute(self, order: Order, market_price: float) -> ExecutionResult:
        """实盘模式：通过网关提交订单"""
        result = ExecutionResult()

        if self._gateway is None:
            result.message = "交易所网关未配置"
            return result

        try:
            # 通过网关提交订单
            response = await self._gateway.submit_order(order)

            # 更新订单状态为已提交
            order.status = OrderStatus.SUBMITTED

            result.success = True
            result.order = order
            result.message = f"订单已提交到交易所: {response}"

            logger.info(
                "实盘订单已提交",
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side.value,
                quantity=f"{order.quantity:.6f}",
            )

        except Exception as e:
            order.status = OrderStatus.REJECTED
            result.message = f"订单提交失败: {str(e)}"
            logger.error(
                "实盘订单提交失败",
                order_id=order.order_id,
                exc_info=True,
            )

        return result
