"""订单管理模块

统一的订单处理管道，适用于回测/模拟/实盘三种模式。
"""

from quant_trading_system.services.order.order_executor import (
    OrderExecutor,
    BacktestExecutor,
    SimulationExecutor,
    LiveExecutor,
    ExecutionConfig,
    ExecutionResult,
)
from quant_trading_system.services.order.position_manager import PositionManager
from quant_trading_system.services.order.account_manager import AccountManager
from quant_trading_system.services.order.order_processor import (
    OrderProcessor,
    OrderProcessorConfig,
)

__all__ = [
    "OrderExecutor",
    "BacktestExecutor",
    "SimulationExecutor",
    "LiveExecutor",
    "ExecutionConfig",
    "ExecutionResult",
    "PositionManager",
    "AccountManager",
    "OrderProcessor",
    "OrderProcessorConfig",
]
