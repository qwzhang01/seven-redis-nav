"""
交易所枚举定义
从 core/enums.py 统一导入，此文件保留向后兼容的别名
"""

from quant_trading_system.core.enums import (
    ExchangeEnum,
    ExchangeStatus,
    MarketType,
)

# 向后兼容别名
ExchangeCode = ExchangeEnum
ExchangeType = MarketType

__all__ = [
    "ExchangeEnum",
    "ExchangeCode",
    "ExchangeType",
    "ExchangeStatus",
    "MarketType",
]
