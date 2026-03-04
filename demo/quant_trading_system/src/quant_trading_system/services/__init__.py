"""
服务模块
========

导出引擎层服务。API 业务服务直接从 api/ 子模块导入，不再在此代理。
"""

# ── 引擎层服务 ──
from quant_trading_system.services.market import MarketService
from quant_trading_system.strategy import Strategy, StrategyEngine
from quant_trading_system.services.trading import TradingEngine, TradingOrchestrator
from quant_trading_system.services.backtest import BacktestEngine
from quant_trading_system.services.risk import RiskManager
from quant_trading_system.services.order import OrderProcessor, PositionManager, AccountManager
from quant_trading_system.services.evaluation import StrategyEvaluator, PerformanceAnalyzer

__all__ = [
    "MarketService",
    "Strategy",
    "StrategyEngine",
    "TradingEngine",
    "TradingOrchestrator",
    "BacktestEngine",
    "RiskManager",
    "OrderProcessor",
    "PositionManager",
    "AccountManager",
    "StrategyEvaluator",
    "PerformanceAnalyzer",
]
