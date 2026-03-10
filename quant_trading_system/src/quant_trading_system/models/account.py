from datetime import datetime
from typing import Dict

from pydantic import BaseModel

from quant_trading_system.core.enums import MarketType


class Balance(BaseModel):
    """余额模型"""
    asset: str
    free: float
    locked: float
    total: float


class Account(BaseModel):
    """账户模型"""
    id: str
    type: MarketType
    balances: Dict[str, Balance]
    total_balance: float
    available_balance: float
    margin_balance: float
    unrealized_pnl: float
    realized_pnl: float
    updated_at: datetime
