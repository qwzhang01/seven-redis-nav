"""
应用生命周期管理
================

管理 FastAPI 应用的启动/关闭流程，包括：
- 数据库初始化
- 编排器启动（加载策略、订阅行情、预加载历史数据）
- WebSocket 心跳
- 信号监听引擎（信号流 + 3个订阅器：落库/推送/跟单）
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from quant_trading_system.core.config import settings
from quant_trading_system.api.deps import set_app_ref, clear_app_ref
from quant_trading_system.api.websocket.manager import ws_manager
from quant_trading_system.core.container import container
from quant_trading_system.core.database import init_database, close_database
from quant_trading_system.core.enums import DefaultTradingPair

logger = logging.getLogger(__name__)


# ── Lifespan 启动步骤 ────────────────────────────────────────────


async def _startup_database() -> None:
    """初始化数据库连接和表结构"""
    try:
        await init_database()
        print("✅ 数据库初始化完成（同步引擎 + 异步引擎）")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


async def _shutdown_database() -> None:
    """关闭数据库连接"""
    try:
        await close_database()
        print("✅ 数据库连接已关闭")
    except Exception as e:
        print(f"❌ 数据库关闭失败: {e}")


async def _startup_orchestrator(app: FastAPI) -> None:
    """
    创建编排器，加载所有已注册策略（stopped 状态），
    订阅默认交易对行情，并预加载历史K线数据。
    """
    # 导入策略模块以触发注册
    import quant_trading_system.strategy.strategies  # noqa: F401

    from quant_trading_system.strategy import (
        list_strategies as list_registered,
        get_strategy_class,
    )
    from quant_trading_system.services.trading.orchestrator import \
        TradingOrchestrator

    orchestrator = TradingOrchestrator(
        mode="paper",
        # 开发环境使用 mock 数据源，无需连接真实交易所
        exchange="mock" if settings.is_development else "binance",
        market_type="spot",
        api_key=settings.BINANCE_API_KEY or "",
        api_secret=settings.BINANCE_SECRET_KEY or "",
    )
    await orchestrator.start()

    # 将所有已注册策略以 stopped 状态加入编排器（不启动、不订阅行情）
    registered = list_registered()
    for name in registered:
        cls = get_strategy_class(name)
        if cls is None:
            continue
        default_symbols = list(cls.symbols) if cls.symbols else []
        orchestrator.add_strategy(cls, symbols=default_symbols)

    # 保存到 app.state
    app.state.orchestrator = orchestrator
    print(f"✅ 编排器启动完成，加载 {len(registered)} 个策略类型（均处于 stopped 状态）")

async def _subscribe_default_symbols() -> None:
    """自动订阅默认交易对的 WebSocket 实时行情"""
    try:
        await container.market_service.subscribe(
            symbols=list(DefaultTradingPair.values()),
            exchange=settings.exchange.data_provider,
        )
    except Exception as e:
        print(f"⚠️ 自动订阅默认交易对失败（不影响系统启动）: {e}")


async def _preload_history() -> None:
    """
    自动拉取历史K线数据，预加载到内存缓冲区。
    """
    try:
        from quant_trading_system.core.enums import DefaultTradingPair
        default_symbols = DefaultTradingPair.values()

        if settings.is_production:
            print("📡 生产环境：从交易所拉取历史K线数据...")
            stats = await container.market_service.load_history(
                symbols=default_symbols,
                limit=500,
                exchange=settings.exchange.data_provider,
                source="exchange",
                save_to_db=True,
            )
            total = sum(stats.values())
            print(
                f"✅ 已从交易所预加载历史K线数据并保存到数据库: {total} 条 ({stats})")
        else:
            print("💾 开发环境：从数据库加载历史K线数据...")
            stats = await container.market_service.load_history(
                symbols=default_symbols,
                limit=500,
                exchange=settings.exchange.data_provider,
                source="database",
            )
            total = sum(stats.values())
            print(f"✅ 已从数据库预加载历史K线数据: {total} 条 ({stats})")
    except Exception as e:
        print(f"⚠️ 预加载历史K线数据失败（不影响系统启动）: {e}")


async def _startup_websocket_heartbeat() -> None:
    """启动 WebSocket 心跳检测"""
    try:
        await ws_manager.start_heartbeat()
        print("✅ WebSocket 心跳检测已启动")
    except Exception as e:
        print(f"⚠️ WebSocket 心跳检测启动失败: {e}")


async def _startup_flow_engines(app: FastAPI) -> None:
    """
    初始化并启动信号监听引擎

    SignalStreamEngine 内部统一管理：
    1. SignalRecordSubscriber（信号记录落库）
    2. SignalWsSubscriber（WebSocket 推送前端）
    3. FollowTradeSubscriber（跟单交易下单）
    4. FlowSignalStream（WebSocket 监听大佬账户）
    """
    try:
        from quant_trading_system.services.flow.signal_stream_engine import SignalStreamEngine

        if settings.is_development:
            print("  🎭 开发环境：信号引擎使用 Mock 模式（不连接真实 Binance API）")

        # 创建并启动信号监听引擎（内部自动注册所有订阅器）
        signal_stream_engine = SignalStreamEngine()
        await signal_stream_engine.start()
        app.state.signal_stream_engine = signal_stream_engine
        print(f"  ✅ 信号监听引擎已启动（活跃信号流: {signal_stream_engine.active_count}）")

    except Exception as e:
        print(f"⚠️ 信号引擎初始化失败（不影响系统启动）: {e}")
        import traceback
        traceback.print_exc()


# ── Lifespan 关闭步骤 ────────────────────────────────────────────


async def _shutdown_websocket_heartbeat() -> None:
    """停止 WebSocket 心跳检测"""
    try:
        await ws_manager.stop_heartbeat()
        print("✅ WebSocket 心跳检测已停止")
    except Exception as e:
        print(f"❌ WebSocket 心跳检测停止失败: {e}")


async def _shutdown_flow_engines(app: FastAPI) -> None:
    """停止信号监听引擎（内部自动停止所有订阅器和信号流）"""
    signal_stream_engine = getattr(app.state, "signal_stream_engine", None)
    if signal_stream_engine is not None:
        try:
            count = signal_stream_engine.active_count
            await signal_stream_engine.stop()
            app.state.signal_stream_engine = None
            print(f"  ✅ 信号监听引擎已停止（已关闭 {count} 个信号流）")
        except Exception as e:
            print(f"  ❌ 信号监听引擎停止失败: {e}")


async def _shutdown_orchestrator(app: FastAPI) -> None:
    """停止编排器并清理状态"""
    orch = getattr(app.state, "orchestrator", None)
    if orch is not None:
        await orch.stop()
        app.state.orchestrator = None
        print("✅ 交易引擎已停止")


# ── Lifespan 主函数 ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时初始化数据库，自动创建编排器并加载所有已注册策略（stopped 状态）
    - 策略不会自动运行，需用户通过 API 显式启动
    - 关闭时清理资源
    """
    set_app_ref(app)

    # ── 启动 ──
    print("🚀 启动量化交易系统...")
    await _startup_database()
    await _subscribe_default_symbols()
    await _preload_history()
    await _startup_orchestrator(app)
    await _startup_websocket_heartbeat()
    await _startup_flow_engines(app)

    yield

    # ── 关闭 ──
    print("🛑 停止量化交易系统...")
    await _shutdown_flow_engines(app)
    await _shutdown_websocket_heartbeat()
    await _shutdown_orchestrator(app)
    await _shutdown_database()
    clear_app_ref()
