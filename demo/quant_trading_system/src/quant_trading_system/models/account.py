from enum import Enum
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel


class AccountType(str, Enum):
    """账户类型"""
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"


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
