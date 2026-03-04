"""交易模块

负责策略的实盘和模拟交易，只管理策略实例的运行。
订单/仓位/账户管理已委托给 order 模块。
"""

from quant_trading_system.services.trading.trading_engine import TradingEngine
from quant_trading_system.exchange_adapter.binance_gateway import ExchangeGateway, BinanceGateway
from quant_trading_system.services.trading.orchestrator import TradingOrchestrator, run_live

__all__ = [
    "TradingEngine",
    "ExchangeGateway",
    "BinanceGateway",
    "TradingOrchestrator",
    "run_live",
]
