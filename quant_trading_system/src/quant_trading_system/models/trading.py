import time
from typing import Optional, Any

from pydantic import BaseModel, Field

from quant_trading_system.core.enums import (
    OrderSide,
    PositionSide,
    OrderType,
    OrderStatus,
)
from quant_trading_system.core.snowflake import generate_backtest_snowflake_id


class Order(BaseModel):
    """订单模型"""
    # 订单ID（本地生成）
    order_id: str = Field(default_factory=lambda: str(generate_backtest_snowflake_id()))
    # 交易所订单ID
    exchange_order_id: str = ""
    # 交易对
    symbol: str
    # 交易所
    exchange: str = ""
    # 买卖方向
    side: OrderSide
    # 订单类型（使用别名避免与Python内置type冲突）
    order_type: OrderType = OrderType.MARKET
    # 数量
    quantity: float = 0.0
    # 价格（限价单）
    price: Optional[float] = None
    # 触发价格（止损单）
    stop_price: Optional[float] = None
    # 订单状态
    status: OrderStatus = OrderStatus.PENDING
    # 已成交数量
    filled_quantity: float = 0.0
    # 平均成交价格
    avg_filled_price: float = 0.0
    # 手续费
    commission: float = 0.0
    # 手续费币种
    commission_asset: str = ""
    # 策略ID
    strategy_id: str = ""
    # 信号ID
    signal_id: str = ""
    # 创建时间（毫秒时间戳）
    create_time: float = Field(default_factory=lambda: time.time() * 1000)
    # 更新时间（毫秒时间戳）
    update_time: float = Field(default_factory=lambda: time.time() * 1000)

    @property
    def id(self) -> str:
        """向后兼容：order_id 的别名"""
        return self.order_id

    @property
    def is_finished(self) -> bool:
        """订单是否已完成（成交、取消、拒绝）"""
        return self.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        )

    def update_fill(
        self,
        filled_qty: float,
        filled_price: float,
        commission: float = 0.0,
        commission_asset: str = "",
    ) -> None:
        """更新成交信息"""
        # 计算新的平均成交价
        old_value = self.filled_quantity * self.avg_filled_price
        new_value = filled_qty * filled_price
        self.filled_quantity += filled_qty
        if self.filled_quantity > 0:
            self.avg_filled_price = (old_value + new_value) / self.filled_quantity
        self.commission += commission
        if commission_asset:
            self.commission_asset = commission_asset
        self.update_time = time.time() * 1000


class Position(BaseModel):
    """持仓模型"""
    symbol: str
    # 持仓方向
    side: PositionSide = PositionSide.LONG
    # 数量
    quantity: float = 0.0
    # 平均持仓价格
    avg_price: float = 0.0
    # 未实现盈亏
    unrealized_pnl: float = 0.0
    # 已实现盈亏
    realized_pnl: float = 0.0
    # 最新价格
    last_price: float = 0.0
    # 策略ID
    strategy_id: str = ""
    # 交易所
    exchange: str = ""

    @property
    def notional_value(self) -> float:
        """持仓名义价值"""
        return abs(self.quantity) * self.last_price


class Trade(BaseModel):
    """成交模型"""
    # 成交ID
    trade_id: str = Field(default_factory=lambda: str(generate_backtest_snowflake_id()))
    # 交易对
    symbol: str
    # 交易所
    exchange: str = ""
    # 订单ID
    order_id: str = ""
    # 交易所成交ID
    exchange_trade_id: str = ""
    # 买卖方向
    side: OrderSide
    # 成交数量
    quantity: float = 0.0
    # 成交价格
    price: float = 0.0
    # 成交金额
    amount: float = 0.0
    # 手续费
    commission: float = 0.0
    # 手续费币种
    commission_asset: str = ""
    # 策略ID
    strategy_id: str = ""
    # 成交时间（毫秒时间戳）
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)

    @property
    def id(self) -> str:
        """向后兼容：trade_id 的别名"""
        return self.trade_id

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "order_id": self.order_id,
            "side": self.side.value,
            "quantity": self.quantity,
            "price": self.price,
            "amount": self.amount,
            "commission": self.commission,
            "strategy_id": self.strategy_id,
            "timestamp": self.timestamp,
        }
