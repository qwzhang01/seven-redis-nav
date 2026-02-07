"""
交易引擎
========

统一的交易执行引擎，负责：
- 信号到订单的转换
- 订单执行
- 仓位管理
"""

import asyncio
from typing import Any
from unittest.mock import Mock

import structlog

from quant_trading_system.core.events import Event, EventEngine, EventType
from quant_trading_system.models.trading import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    PositionSide,
)
from quant_trading_system.models.account import Account
from quant_trading_system.services.trading.order_manager import OrderManager
from quant_trading_system.services.strategy.signal import Signal, SignalType

logger = structlog.get_logger(__name__)


class TradingEngine:
    """
    交易引擎
    
    统一管理交易执行流程
    """
    
    def __init__(
        self,
        event_engine: EventEngine | None = None,
    ) -> None:
        self._event_engine = event_engine
        
        # 订单管理器
        self._order_manager = OrderManager(event_engine)
        
        # 持仓管理器（暂时使用字典存储）
        self._position_manager = Mock()  # 使用Mock对象
        
        # 风险管理器（暂时使用字典存储）
        self._risk_manager = Mock()  # 使用Mock对象
        
        # 账户
        self._account: Account | None = None
        
        # 持仓 {symbol: Position}
        self._positions: dict[str, Position] = {}
        
        # 交易所网关 {exchange: gateway}
        self._gateways: dict[str, Any] = {}
        
        # 默认交易所
        self._default_exchange: str = ""
        
        # 运行状态
        self._running = False
        
        # 配置
        self._default_slippage = 0.0001
        self._default_commission = 0.0004
    
    async def start(self) -> None:
        """启动交易引擎"""
        if self._running:
            return
        
        self._running = True
        
        # 注册事件处理
        if self._event_engine:
            self._event_engine.register(EventType.SIGNAL, self._on_signal)
        
        logger.info("Trading engine started")
    
    async def stop(self) -> None:
        """停止交易引擎"""
        if not self._running:
            return
        
        self._running = False
        logger.info("Trading engine stopped")
    
    def set_account(self, account: Account) -> None:
        """设置账户"""
        self._account = account
    
    def get_position(self, symbol: str) -> Position | None:
        """获取持仓"""
        return self._positions.get(symbol)
    
    def update_position(self, position: Position) -> None:
        """更新持仓"""
        self._positions[position.symbol] = position
        
        # 发送事件
        if self._event_engine:
            asyncio.create_task(self._event_engine.put(Event(
                type=EventType.POSITION_UPDATE,
                data=position,
            )))
    
    async def execute_signal(self, signal: Signal) -> Order | None:
        """
        执行交易信号
        
        Args:
            signal: 交易信号
        
        Returns:
            创建的订单
        """
        if not self._running:
            logger.warning("Trading engine not running")
            return None
        
        # 验证信号
        if not self._validate_signal(signal):
            return None
        
        # 计算交易数量
        quantity = self._calculate_quantity(signal)
        if quantity <= 0:
            logger.warning(f"Invalid quantity", signal_id=signal.signal_id)
            return None
        
        # 创建订单
        order = self._order_manager.create_order_from_signal(signal)
        order.quantity = quantity
        
        # 执行订单
        success = await self._submit_order(order)
        
        if not success:
            await self._order_manager.update_order_status(
                order.id, OrderStatus.REJECTED
            )
            return None
        
        return order
    
    def _validate_signal(self, signal: Signal) -> bool:
        """验证信号"""
        # 检查信号是否过期
        if signal.is_expired:
            logger.warning(f"Signal expired", signal_id=signal.signal_id)
            return False
        
        # 检查账户
        if self._account is None:
            logger.warning("No account configured")
            return False
        
        return True
    
    def _calculate_quantity(self, signal: Signal) -> float:
        """计算交易数量"""
        if signal.quantity > 0:
            return signal.quantity
        
        # 默认数量（实际应该根据资金管理规则计算）
        return 0.01
    
    async def _submit_order(self, order: Order) -> bool:
        """
        提交订单到交易所
        
        Args:
            order: 订单对象
        
        Returns:
            是否提交成功
        """
        # 使用默认交易所
        exchange = self._default_exchange
        
        # 检查是否有对应的网关
        gateway = self._gateways.get(exchange)
        
        if gateway is None:
            # 模拟执行
            logger.info(f"Simulating order execution", 
                       order_id=order.id)
            
            await self._order_manager.update_order_status(
                order.id, 
                OrderStatus.PENDING
            )
            
            # 模拟成交
            await self._simulate_fill(order)
            return True
        
        # 通过网关提交订单
        try:
            await gateway.submit_order(order)
            
            await self._order_manager.update_order_status(
                order.order_id, 
                OrderStatus.SUBMITTED
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Order submission failed", 
                        order_id=order.order_id,
                        error=str(e))
            return False
    
    async def _simulate_fill(self, order: Order) -> None:
        """
        模拟订单成交
        
        用于无网关时的模拟交易
        """
        # 模拟延迟
        await asyncio.sleep(0.01)
        
        # 计算成交价格（加入滑点）
        if order.price > 0:
            fill_price = order.price
        else:
            # 市价单需要外部价格，这里使用0作为占位
            fill_price = order.price
        
        if order.side == OrderSide.BUY:
            fill_price *= (1 + self._default_slippage)
        else:
            fill_price *= (1 - self._default_slippage)
        
        # 计算手续费
        commission = order.quantity * fill_price * self._default_commission
        
        # 更新订单状态
        await self._order_manager.on_trade(
            order_id=order.id,
            trade_id=f"sim_{order.id}",
            price=fill_price,
            quantity=order.quantity,
            commission=commission,
        )
        
        # 更新持仓
        self._update_position_from_order(order, fill_price)
    
    def _update_position_from_order(
        self,
        order: Order,
        fill_price: float
    ) -> None:
        """根据订单更新持仓"""
        symbol = order.symbol

        if symbol not in self._positions:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=0.0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                last_price=fill_price,
            )
        
        position = self._positions[symbol]
        
        if order.side == OrderSide.BUY:
            # 直接更新Position对象的字段
            position.quantity += order.quantity
            position.avg_price = fill_price
            position.last_price = fill_price
        else:
            if position.quantity > 0:
                # 直接更新Position对象的字段
                reduce_quantity = min(order.quantity, position.quantity)
                position.quantity -= reduce_quantity
                position.last_price = fill_price
        
        self.update_position(position)
    
    async def _on_signal(self, event: Event) -> None:
        """信号事件处理"""
        signal = event.data
        if isinstance(signal, Signal):
            await self.execute_signal(signal)
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            是否取消成功
        """
        order = self._order_manager.get_order(order_id)
        if order is None:
            return False
        
        if order.is_finished:
            return False
        
        # 获取网关
        gateway = self._gateways.get(order.exchange)
        
        if gateway:
            try:
                await gateway.cancel_order(order)
            except Exception as e:
                logger.error(f"Cancel order failed", 
                           order_id=order_id,
                           error=str(e))
                return False
        
        await self._order_manager.update_order_status(
            order_id, OrderStatus.CANCELLED
        )
        
        return True
    
    async def cancel_all_orders(self, symbol: str | None = None) -> int:
        """
        取消所有订单
        
        Args:
            symbol: 品种（可选，不指定则取消所有）
        
        Returns:
            取消的订单数量
        """
        if symbol:
            orders = self._order_manager.get_active_orders_by_symbol(symbol)
        else:
            orders = self._order_manager.get_active_orders()
        
        cancelled = 0
        for order in orders:
            if await self.cancel_order(order.order_id):
                cancelled += 1
        
        return cancelled
    
    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "running": self._running,
            "positions": len(self._positions),
            "order_stats": self._order_manager.stats,
            "performance": {
                "total_orders": self._order_manager.stats.get("total_orders", 0),
                "successful_orders": self._order_manager.stats.get("successful_orders", 0),
                "failed_orders": self._order_manager.stats.get("failed_orders", 0),
                "avg_execution_time": self._order_manager.stats.get("avg_execution_time", 0.0),
                "order_submission_time": 0.1  # 模拟值，实际应该从性能监控中获取
            }
        }
    
    async def submit_order(self, order: Order) -> Order:
        """提交订单（先进行风险检查，然后委托给订单管理器）"""
        # 进行风险检查
        if self._risk_manager:
            risk_result = self._risk_manager.check_order(order, 0)
            if not risk_result.passed:
                raise Exception(f"Risk check failed: {risk_result.messages}")
        
        # 发送订单提交事件
        if self._event_engine:
            event = Event(
                type=EventType.ORDER_SUBMITTED,
                data={"order": order}
            )
            await self._event_engine.put(event)
        
        return await self._order_manager.submit_order(order)
    
    async def cancel_order(self, order_id: str) -> bool:
        """取消订单（委托给订单管理器）"""
        return await self._order_manager.cancel_order(order_id)
    
    def get_order(self, order_id: str) -> Order | None:
        """获取订单（委托给订单管理器）"""
        return self._order_manager.get_order(order_id)
    
    def get_orders(self) -> list[Order]:
        """获取所有订单（委托给订单管理器）"""
        return self._order_manager.get_orders()
    
    def get_positions(self) -> dict[str, Position]:
        """获取所有持仓（委托给持仓管理器）"""
        return self._position_manager.get_positions() if self._position_manager else {}
    
    def get_position(self, symbol: str) -> Position | None:
        """获取特定持仓（委托给持仓管理器）"""
        return self._position_manager.get_position(symbol) if self._position_manager else None
    
    async def on_tick_data(self, tick_data: dict) -> None:
        """处理Tick数据（委托给持仓管理器）"""
        if self._position_manager:
            await self._position_manager.update_market_price(
                tick_data["symbol"], 
                tick_data["last_price"]
            )
    
    async def on_order_update(self, order_update: dict) -> None:
        """处理订单更新（委托给订单管理器）"""
        await self._order_manager.on_order_update(order_update)
    
    async def on_trade_data(self, trade_data: dict) -> None:
        """处理成交数据（委托给持仓管理器）"""
        if self._position_manager:
            await self._position_manager.on_trade(trade_data)

    def _validate_order(self, order: Order) -> None:
        """验证订单"""
        if order.quantity <= 0:
            raise ValueError("订单数量必须大于0")
        
        if order.type == OrderType.LIMIT and order.price is None:
            raise ValueError("限价订单必须指定价格")

    def update_account_equity(self) -> None:
        """更新账户权益"""
        if self._account and self._position_manager:
            total_value = self._position_manager.calculate_total_value()
            self._account.total_balance = total_value
            
            # 通知风险管理器更新权益
            if self._risk_manager:
                self._risk_manager.update_equity(total_value)
