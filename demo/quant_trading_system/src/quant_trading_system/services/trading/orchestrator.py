"""
交易系统编排器
==============

将 EventEngine, MarketService, StrategyEngine, TradingEngine, RiskManager
统一编排、启动和管理，为实盘/模拟交易提供一站式入口。
"""

import asyncio
import signal
from datetime import datetime
from typing import Any, Type

import structlog

from quant_trading_system.core.enums import DefaultTradingPair
from quant_trading_system.core.events import EventEngine, EventType, Event
from quant_trading_system.models.account import Account, AccountType, Balance
from quant_trading_system.services.strategy.base import Strategy
from quant_trading_system.services.risk.risk_manager import RiskConfig

logger = structlog.get_logger(__name__)


class TradingOrchestrator:
    """
    交易系统编排器

    职责：
    - 按正确顺序启动/停止所有引擎
    - 管理组件之间的依赖注入
    - 支持实盘 (live) 和模拟 (paper) 两种模式
    - 提供统一的状态查询接口
    """

    def __init__(
        self,
        mode: str = "paper",
        exchange: str = "binance",
        market_type: str = "spot",
        api_key: str = "",
        api_secret: str = "",
        initial_capital: float = 100_000.0,
        risk_config: RiskConfig | None = None,
    ) -> None:
        """
        Args:
            mode: 运行模式 "live" | "paper"
        exchange: 交易所 "binance"
            market_type: 市场类型 "spot" | "futures"
            api_key: 交易所 API Key（live 模式必填）
            api_secret: 交易所 API Secret（live 模式必填）
            initial_capital: 模拟资金（paper 模式使用）
            risk_config: 风控配置
        """
        self.mode = mode
        self.exchange = exchange
        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret
        self.initial_capital = initial_capital

        # ---- 核心组件（通过 ServiceContainer 统一管理） ----
        from quant_trading_system.core.container import container

        self.event_engine = container.event_engine
        self.market_service = container.market_service
        self.strategy_engine = container.strategy_engine
        self.trading_engine = container.trading_engine
        self.risk_manager = container.risk_manager

        # ---- 状态 ----
        self._running = False
        self._strategy_ids: list[str] = []
        self._subscribed_symbols: list[str] = []

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """按依赖顺序启动所有组件"""
        if self._running:
            logger.warning("Orchestrator already running")
            return

        logger.info(
            "Starting trading orchestrator",
            mode=self.mode,
            exchange=self.exchange,
        )

        # 1. 启动事件引擎
        await self.event_engine.start()

        # 2. 创建账户
        account = self._create_account()
        self.strategy_engine.set_account(account)
        self.trading_engine.set_account(account)
        self.risk_manager.set_account(account)

        # 3. 配置交易所网关（仅 live 模式）
        if self.mode == "live":
            self._setup_gateway()

        # 4. 注入风控到交易引擎
        self.trading_engine._risk_manager = self.risk_manager

        # 5. 添加行情数据源
        await self.market_service.add_exchange(
            exchange=self.exchange,
            market_type=self.market_type,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )

        # 6. 将 K 线事件桥接到 EventEngine（KLineEngine 回调 → EventEngine BAR）
        async def _bar_to_event(bar: Any) -> None:
            await self.event_engine.put(Event(
                type=EventType.BAR,
                data=bar,
                source="market_service",
            ))

        self.market_service.add_bar_callback(_bar_to_event)

        # 7. 启动各引擎
        await self.strategy_engine.start()
        await self.trading_engine.start()
        await self.market_service.start()

        self._running = True
        logger.info("Trading orchestrator started successfully")

    async def stop(self) -> None:
        """按逆序停止所有组件"""
        if not self._running:
            return

        logger.info("Stopping trading orchestrator")

        await self.market_service.stop()
        await self.trading_engine.stop()
        await self.strategy_engine.stop()
        await self.event_engine.stop()

        self._running = False
        logger.info("Trading orchestrator stopped")

    # ------------------------------------------------------------------
    # 策略管理
    # ------------------------------------------------------------------

    def add_strategy(
        self,
        strategy: Strategy | Type[Strategy],
        symbols: list[str] | None = None,
        **params: Any,
    ) -> str:
        """
        添加策略并返回 strategy_id

        Args:
            strategy: 策略实例或策略类
            symbols: 需要订阅的交易对（默认从策略 class 定义中获取）
            **params: 策略参数
        """
        if isinstance(strategy, type):
            instance = strategy(**params)
        else:
            instance = strategy

        # 设置交易对
        if symbols:
            instance._symbols = symbols

        strategy_id = self.strategy_engine.add_strategy(instance)
        self._strategy_ids.append(strategy_id)

        # 收集需要订阅的 symbol
        for sym in instance.symbols:
            if sym not in self._subscribed_symbols:
                self._subscribed_symbols.append(sym)

        return strategy_id

    async def start_strategy(self, strategy_id: str) -> None:
        """
        启动策略，并自动订阅该策略所需的行情数据（增量订阅，已订阅的不重复）
        """
        await self.strategy_engine.start_strategy(strategy_id)

        # 获取该策略实例，订阅其尚未订阅的交易对行情
        strategy_instance = self.strategy_engine.get_strategy(strategy_id)
        if strategy_instance:
            new_symbols = [
                sym for sym in strategy_instance.symbols
                if sym not in self._subscribed_symbols
            ]
            if new_symbols:
                await self.market_service.subscribe(
                    symbols=new_symbols,
                    exchange=self.exchange,
                    market_type=self.market_type,
                )
                self._subscribed_symbols.extend(new_symbols)
                logger.info(
                    "Subscribed market data for strategy",
                    strategy_id=strategy_id,
                    new_symbols=new_symbols,
                )

    async def start_all_strategies(self) -> None:
        """启动所有已添加的策略"""
        for sid in self._strategy_ids:
            await self.strategy_engine.start_strategy(sid)

    async def subscribe_market(self) -> None:
        """订阅所有策略关注的交易对行情"""
        if self._subscribed_symbols:
            await self.market_service.subscribe(
                symbols=self._subscribed_symbols,
                exchange=self.exchange,
                market_type=self.market_type,
            )
            logger.info(
                "Subscribed market data",
                symbols=self._subscribed_symbols,
            )

    async def subscribe_default_symbols(self) -> None:
        """
        订阅系统默认交易对的实时行情（WS）

        从 DefaultTradingPair 枚举读取配置，自动订阅尚未订阅的交易对。
        """
        default_symbols = DefaultTradingPair.values()
        new_symbols = [
            sym for sym in default_symbols
            if sym not in self._subscribed_symbols
        ]

        if not new_symbols:
            logger.info("All default symbols already subscribed",
                       symbols=default_symbols)
            return

        await self.market_service.subscribe(
            symbols=new_symbols,
            exchange=self.exchange,
            market_type=self.market_type,
        )
        self._subscribed_symbols.extend(new_symbols)

        logger.info(
            "Subscribed default trading pairs",
            symbols=new_symbols,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _create_account(self) -> Account:
        """创建账户对象"""
        usdt_balance = Balance(
            asset="USDT",
            free=self.initial_capital,
            locked=0.0,
            total=self.initial_capital,
        )
        return Account(
            id=f"{self.mode}_{self.exchange}",
            type=AccountType.SPOT if self.market_type == "spot" else AccountType.FUTURES,
            balances={"USDT": usdt_balance},
            total_balance=self.initial_capital,
            available_balance=self.initial_capital,
            margin_balance=self.initial_capital,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            updated_at=datetime.now(),
        )

    def _setup_gateway(self) -> None:
        """配置交易所网关（实盘模式）"""
        if not self.api_key or not self.api_secret:
            logger.warning(
                "Live mode without API keys — falling back to paper trading"
            )
            return

        if self.exchange == "binance":
            from quant_trading_system.services.trading.gateway import BinanceGateway

            gateway = BinanceGateway(
                api_key=self.api_key,
                api_secret=self.api_secret,
                market_type=self.market_type,
            )
            self.trading_engine._gateways[self.exchange] = gateway
            self.trading_engine._default_exchange = self.exchange

            logger.info("Binance gateway configured for live trading")
        else:
            logger.warning(f"Gateway not implemented for {self.exchange}")

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict[str, Any]:
        """获取全局统计"""
        return {
            "mode": self.mode,
            "running": self._running,
            "exchange": self.exchange,
            "market_type": self.market_type,
            "event_engine": self.event_engine.stats,
            "market_service": self.market_service.stats,
            "strategy_engine": self.strategy_engine.stats,
            "trading_engine": self.trading_engine.stats,
            "risk_manager": self.risk_manager.stats,
        }


# ------------------------------------------------------------------
# 便捷运行函数
# ------------------------------------------------------------------

async def run_live(
    strategy: Strategy | Type[Strategy],
    symbols: list[str],
    exchange: str = "binance",
    market_type: str = "spot",
    api_key: str = "",
    api_secret: str = "",
    initial_capital: float = 100_000.0,
    mode: str = "paper",
    **strategy_params: Any,
) -> None:
    """
    一键启动实盘/模拟交易

    Args:
        strategy: 策略实例或类
        symbols: 订阅的交易对列表
        exchange: 交易所
        market_type: 市场类型
        api_key: API Key (live 模式需要)
        api_secret: API Secret
        initial_capital: 初始资金
        mode: "live" | "paper"
        **strategy_params: 策略参数
    """
    orchestrator = TradingOrchestrator(
        mode=mode,
        exchange=exchange,
        market_type=market_type,
        api_key=api_key,
        api_secret=api_secret,
        initial_capital=initial_capital,
    )

    # 注册停止信号
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _handle_signal() -> None:
        logger.info("Received shutdown signal")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    try:
        await orchestrator.start()

        orchestrator.add_strategy(strategy, symbols=symbols, **strategy_params)
        await orchestrator.start_all_strategies()
        await orchestrator.subscribe_market()

        logger.info(
            "Trading system running",
            mode=mode,
            symbols=symbols,
            exchange=exchange,
        )

        # 阻塞直到收到停止信号
        await stop_event.wait()

    except Exception as e:
        logger.exception("Trading system error", error=str(e))
    finally:
        await orchestrator.stop()
