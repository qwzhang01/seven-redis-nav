"""
交易系统编排器
==============

将 EventEngine, MarketService, StrategyEngine, TradingEngine,
OrderProcessor, StrategyEvaluator, RiskManager
统一编排、启动和管理，为实盘/模拟交易提供一站式入口。
"""

import asyncio
import signal
from typing import Any, Type

import structlog

from quant_trading_system.core.enums import DefaultTradingPair
from quant_trading_system.core.enums import MarketType
from quant_trading_system.strategy import Strategy
from quant_trading_system.services.risk.risk_manager import RiskConfig
from quant_trading_system.services.order.order_executor import (
    SimulationExecutor,
    LiveExecutor,
    ExecutionConfig,
)
from quant_trading_system.services.order.position_manager import PositionManager
from quant_trading_system.services.order.account_manager import AccountManager
from quant_trading_system.services.order.order_processor import (
    OrderProcessor,
    OrderProcessorConfig,
)
from quant_trading_system.services.evaluation.strategy_evaluator import StrategyEvaluator

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
        commission_rate: float = 0.0004,
        slippage_rate: float = 0.0001,
        position_sizing: str = "fixed",
        fixed_quantity: float = 0.01,
        percent_risk: float = 0.02,
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
            commission_rate: 手续费率
            slippage_rate: 滑点比例
            position_sizing: 仓位计算模式 "fixed" | "percent" | "kelly"
            fixed_quantity: 固定交易数量
            percent_risk: 风险百分比
        """
        self.mode = mode
        self.exchange = exchange
        self.market_type = market_type
        self.api_key = api_key
        self.api_secret = api_secret
        self.initial_capital = initial_capital

        # ---- 核心组件（通过 ServiceContainer 获取基础组件） ----
        from quant_trading_system.core.container import container

        self.event_engine = container.event_engine
        self.market_service = container.market_service
        self.strategy_engine = container.strategy_engine
        self.trading_engine = container.trading_engine

        # ---- 新增模块：统一订单管理 ----
        self.position_manager = PositionManager(event_engine=self.event_engine)
        self.account_manager = AccountManager()

        # 根据模式创建不同的执行器
        exec_config = ExecutionConfig(
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
        )

        if mode == "live":
            self._executor = LiveExecutor(config=exec_config)
        else:
            self._executor = SimulationExecutor(config=exec_config)

        # 风控管理器（事件驱动）
        if risk_config:
            # 使用自定义风控配置时，创建新实例并同步到全局容器
            from quant_trading_system.services.risk.risk_manager import RiskManager
            self.risk_manager = RiskManager(
                config=risk_config,
                event_engine=self.event_engine,
            )
            container.risk_manager = self.risk_manager
        else:
            self.risk_manager = container.risk_manager

        # 订单处理器（核心管道）
        self.order_processor = OrderProcessor(
            executor=self._executor,
            position_manager=self.position_manager,
            account_manager=self.account_manager,
            event_engine=self.event_engine,
            risk_manager=self.risk_manager,
            config=OrderProcessorConfig(
                position_sizing=position_sizing,
                fixed_quantity=fixed_quantity,
                percent_risk=percent_risk,
            ),
        )

        # 策略评价器（事件驱动）
        self.evaluator = StrategyEvaluator(
            event_engine=self.event_engine,
            initial_equity=initial_capital,
        )

        # ---- 注入依赖到 TradingEngine ----
        self.trading_engine.set_order_processor(self.order_processor)

        # ---- 状态 ----
        self._running = False
        self._strategy_ids: list[str] = []
        self._subscribed_symbols: list[str] = []  # 实际已通过 WebSocket 订阅的交易对
        self._strategy_symbols: list[str] = []    # 策略关注但尚未订阅的交易对

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
        account = self.account_manager.create_account(
            initial_capital=self.initial_capital,
            account_id=f"{self.mode}_{self.exchange}",
            account_type=MarketType.SPOT if self.market_type == "spot" else MarketType.FUTURES,
        )
        self.strategy_engine.set_account(account)

        # 3. 配置风控
        self.risk_manager.set_account(account)
        self.risk_manager.set_positions(self.position_manager.positions)

        # 4. 配置交易所网关（仅 live 模式）
        if self.mode == "live":
            self._setup_gateway()

        # 5. 启动风控管理器（注册事件监听）
        await self.risk_manager.start()

        # 6. 启动策略评价器（注册事件监听）
        await self.evaluator.start()

        # 7. 添加行情数据源
        await self.market_service.add_exchange(
            exchange=self.exchange,
            market_type=self.market_type,
            api_key=self.api_key,
            api_secret=self.api_secret,
        )

        # 8. 启动各引擎
# 注：K线 → EventEngine BAR 的桥接由 MarketDataDispatcher 自动完成
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
        await self.evaluator.stop()
        await self.risk_manager.stop()
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

        # 如果调用方指定了 symbols，覆盖实例的交易对（遮蔽 ClassVar）
        if symbols:
            instance.symbols = tuple(symbols)

        strategy_id = self.strategy_engine.add_strategy(instance)
        self._strategy_ids.append(strategy_id)

        # 收集策略关注的 symbol（仅记录，不实际订阅）
        for sym in instance.symbols:
            if sym not in self._strategy_symbols:
                self._strategy_symbols.append(sym)

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
        # 找出尚未实际订阅的策略交易对
        new_symbols = [
            sym for sym in self._strategy_symbols
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
                "Subscribed market data",
                symbols=new_symbols,
            )

    async def subscribe_default_symbols(self) -> None:
        """
        订阅系统默认交易对的实时行情（WS）

        从 DefaultTradingPair 枚举读取配置，合并策略关注的交易对，
        自动订阅尚未订阅的交易对。
        """
        # 合并默认交易对和策略关注的交易对
        all_symbols = list(DefaultTradingPair.values())
        for sym in self._strategy_symbols:
            if sym not in all_symbols:
                all_symbols.append(sym)

        new_symbols = [
            sym for sym in all_symbols
            if sym not in self._subscribed_symbols
        ]

        if not new_symbols:
            logger.info("All default symbols already subscribed",
                       symbols=all_symbols)
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

    def _setup_gateway(self) -> None:
        """配置交易所网关（实盘模式）"""
        if not self.api_key or not self.api_secret:
            logger.warning(
                "Live mode without API keys — falling back to paper trading"
            )
            return

        try:
            from quant_trading_system.exchange_adapter.factory import create_gateway
            from quant_trading_system.core.config import settings

            gateway = create_gateway(
                exchange=self.exchange,
                api_key=self.api_key,
                api_secret=self.api_secret,
                market_type=self.market_type,
                proxy_url=settings.exchange.proxy_url,
            )
        except ValueError as e:
            logger.warning(f"Gateway 创建失败: {e}")
            return

        # 注入到 LiveExecutor
        if isinstance(self._executor, LiveExecutor):
            self._executor.set_gateway(gateway)

        # 注册到 TradingEngine
        self.trading_engine.register_gateway(self.exchange, gateway)
        self.trading_engine.set_default_exchange(self.exchange)

        logger.info("Gateway configured for live trading", exchange=self.exchange)

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
            "order_processor": self.order_processor.stats,
            "risk_manager": self.risk_manager.stats,
            "evaluator": self.evaluator.stats,
            "position_manager": self.position_manager.stats,
            "account_manager": self.account_manager.stats,
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
