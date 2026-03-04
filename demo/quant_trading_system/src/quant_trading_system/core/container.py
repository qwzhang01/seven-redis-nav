"""
DI容器模块
============

统一的依赖注入容器，集中管理所有核心服务实例的生命周期。

使用方式：
    from quant_trading_system.core.container import container

    # 获取服务实例
    event_engine = container.event_engine
    indicator_engine = container.indicator_engine

    # 或者通过 get 方法（带懒加载）
    market_service = container.get_market_service()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import structlog

if TYPE_CHECKING:
    from quant_trading_system.engines.event_engine import EventEngine
    from quant_trading_system.indicators.indicator_engine import IndicatorEngine
    from quant_trading_system.services.market.market_service import MarketService
    from quant_trading_system.strategy import StrategyEngine
    from quant_trading_system.services.trading.trading_engine import TradingEngine
    from quant_trading_system.services.risk.risk_manager import RiskManager

logger = structlog.get_logger(__name__)


class ServiceContainer:
    """
    统一管理所有核心服务实例，确保：
    - 全局只有一份实例（单例语义）
    - 依赖关系清晰可控
    - 支持懒加载，按需创建
    - 便于测试时替换 mock 实例
    """

    def __init__(self) -> None:
        # 核心组件实例（可从外部注入，也可懒加载创建）
        self._event_engine: Optional["EventEngine"] = None
        self._indicator_engine: Optional["IndicatorEngine"] = None
        self._market_service: Optional["MarketService"] = None
        self._strategy_engine: Optional["StrategyEngine"] = None
        self._trading_engine: Optional["TradingEngine"] = None
        self._risk_manager: Optional["RiskManager"] = None

    # ── EventEngine ──

    @property
    def event_engine(self) -> "EventEngine":
        """获取事件引擎（懒加载）"""
        if self._event_engine is None:
            from quant_trading_system.engines.event_engine import EventEngine
            self._event_engine = EventEngine(
                queue_size=100000,
                num_workers=4,
                name="MainEventEngine",
            )
            logger.debug("EventEngine created by container")
        return self._event_engine

    @event_engine.setter
    def event_engine(self, engine: "EventEngine") -> None:
        self._event_engine = engine

    # ── IndicatorEngine ──

    @property
    def indicator_engine(self) -> "IndicatorEngine":
        """获取指标引擎（懒加载）"""
        if self._indicator_engine is None:
            from quant_trading_system.indicators.indicator_engine import IndicatorEngine
            self._indicator_engine = IndicatorEngine()
            logger.debug("IndicatorEngine created by container")
        return self._indicator_engine

    @indicator_engine.setter
    def indicator_engine(self, engine: "IndicatorEngine") -> None:
        self._indicator_engine = engine

    # ── MarketService ──

    @property
    def market_service(self) -> "MarketService":
        """获取行情服务（懒加载）"""
        if self._market_service is None:
            from quant_trading_system.services.market.market_service import MarketService
            self._market_service = MarketService()
            logger.debug("MarketService created by container")
        return self._market_service

    @market_service.setter
    def market_service(self, service: "MarketService") -> None:
        self._market_service = service

    # ── StrategyEngine ──

    @property
    def strategy_engine(self) -> "StrategyEngine":
        """获取策略引擎（懒加载）"""
        if self._strategy_engine is None:
            from quant_trading_system.strategy import StrategyEngine
            self._strategy_engine = StrategyEngine(
                event_engine=self.event_engine,
                indicator_engine=self.indicator_engine,
            )
            logger.debug("StrategyEngine created by container")
        return self._strategy_engine

    @strategy_engine.setter
    def strategy_engine(self, engine: "StrategyEngine") -> None:
        self._strategy_engine = engine

    # ── TradingEngine ──

    @property
    def trading_engine(self) -> "TradingEngine":
        """获取交易引擎（懒加载）"""
        if self._trading_engine is None:
            from quant_trading_system.services.trading.trading_engine import TradingEngine
            self._trading_engine = TradingEngine(event_engine=self.event_engine)
            logger.debug("TradingEngine created by container")
        return self._trading_engine

    @trading_engine.setter
    def trading_engine(self, engine: "TradingEngine") -> None:
        self._trading_engine = engine

    # ── RiskManager ──

    @property
    def risk_manager(self) -> "RiskManager":
        """获取风控管理器（懒加载）"""
        if self._risk_manager is None:
            from quant_trading_system.services.risk.risk_manager import RiskManager, RiskConfig
            self._risk_manager = RiskManager(
                config=RiskConfig(),
                event_engine=self.event_engine,
            )
            logger.debug("RiskManager created by container")
        return self._risk_manager

    @risk_manager.setter
    def risk_manager(self, manager: "RiskManager") -> None:
        self._risk_manager = manager

    # ── 生命周期管理 ──

    def reset(self) -> None:
        """
        重置容器，清除所有服务实例。

        主要用于测试场景。
        """
        # 先优雅关闭持有线程池/后台资源的引擎
        if self._indicator_engine is not None:
            try:
                self._indicator_engine.shutdown()
            except Exception:
                logger.warning("IndicatorEngine shutdown failed during reset", exc_info=True)

        if self._event_engine is not None:
            try:
                self._event_engine.stop()
            except Exception:
                logger.warning("EventEngine stop failed during reset", exc_info=True)

        self._event_engine = None
        self._indicator_engine = None
        self._market_service = None
        self._strategy_engine = None
        self._trading_engine = None
        self._risk_manager = None
        logger.info("ServiceContainer reset")


# 全局容器单例
container = ServiceContainer()
