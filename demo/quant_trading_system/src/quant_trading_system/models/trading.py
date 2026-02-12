from enum import Enum
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class PositionSide(str, Enum):
    """持仓方向"""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order(BaseModel):
    """订单模型"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus
    exchange: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Position(BaseModel):
    """持仓模型"""
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    last_price: float


class Trade(BaseModel):
    """成交模型"""
    id: str
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    order_id: str
    commission: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "order_id": self.order_id,
            "commission": self.commission
        }
