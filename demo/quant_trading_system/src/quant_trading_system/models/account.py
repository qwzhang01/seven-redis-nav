from typing import Dict
from datetime import datetime
from pydantic import BaseModel

from quant_trading_system.core.enums import MarketType


# 向后兼容别名：AccountType -> MarketType
AccountType = MarketType


class Balance(BaseModel):
    """余额模型"""
    asset: str
    free: float
    locked: float
    total: float


class Account(BaseModel):
    """账户模型"""
    id: str
    type: AccountType
    balances: Dict[str, Balance]
    total_balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    realized_pnl: float
    updated_at: datetime
