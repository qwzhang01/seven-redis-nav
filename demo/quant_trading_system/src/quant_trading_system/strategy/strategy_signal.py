"""
交易信号
========

定义策略产生的交易信号
"""

import time
from typing import Any
from pydantic import BaseModel, Field
from quant_trading_system.core.enums import SignalType


class StrategySignal(BaseModel):
    """
    交易信号

    策略产生的交易信号
    """

    # 基本信息
    symbol: str
    signal_type: SignalType

    # 策略信息
    strategy_id: str = ""
    strategy_name: str = ""

    # 价格和数量
    price: float = 0.0  # 建议价格（0表示市价）
    quantity: float = 0.0  # 建议数量（0表示由资金管理决定）

    # 止损止盈
    stop_loss: float = 0.0  # 止损价
    take_profit: float = 0.0  # 止盈价

    # 信号强度 (0-1)
    strength: float = 1.0

    # 时间
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
    expire_time: float = 0.0  # 信号过期时间

    # 额外信息
    reason: str = ""  # 信号原因
    data: dict[str, Any] = Field(default_factory=dict)  # 附加数据

    @property
    def is_buy(self) -> bool:
        """是否为买入方向操作（买入开多 / 买入平空）"""
        return self.signal_type in (
            SignalType.BUY,
            SignalType.OPEN_LONG,
            SignalType.CLOSE_SHORT,  # 平空 = 买入平仓
        )

    @property
    def is_sell(self) -> bool:
        """是否为卖出方向操作（卖出开空 / 卖出平多）"""
        return self.signal_type in (
            SignalType.SELL,
            SignalType.OPEN_SHORT,  # 开空 = 卖出开仓
            SignalType.CLOSE_LONG,  # 平多 = 卖出平仓
        )

    @property
    def is_open(self) -> bool:
        return self.signal_type in (
            SignalType.BUY,
            SignalType.OPEN_LONG,
            SignalType.OPEN_SHORT,
        )

    @property
    def is_close(self) -> bool:
        return self.signal_type in (
            SignalType.SELL,
            SignalType.CLOSE_LONG,
            SignalType.CLOSE_SHORT,
        )

    @property
    def is_expired(self) -> bool:
        if self.expire_time <= 0:
            return False
        return time.time() * 1000 > self.expire_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "price": self.price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "strength": self.strength,
            "timestamp": self.timestamp,
            "expire_time": self.expire_time,
            "reason": self.reason,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategySignal":
        # 浅拷贝避免修改原始字典
        d = dict(data)
        d["signal_type"] = SignalType(d["signal_type"])
        return cls(**d)
