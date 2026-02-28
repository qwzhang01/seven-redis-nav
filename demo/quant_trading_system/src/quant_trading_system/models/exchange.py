"""
交易所枚举定义
包含BG、芝麻、币安等交易所的枚举定义
"""

from enum import Enum


class ExchangeCode(str, Enum):
    """
    交易所代码枚举
    """
    BG = "bg"
    ZHI_MA = "zhima"
    BINANCE = "binance"


class ExchangeType(str, Enum):
    """
    交易所类型枚举
    """
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


class ExchangeStatus(str, Enum):
    """
    交易所状态枚举
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
