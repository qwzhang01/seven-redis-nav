"""
API主模块
=========

FastAPI应用入口
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from quant_trading_system.core.config import settings
from quant_trading_system.core.logging import setup_logging
from quant_trading_system.api.routers import (
    market_router,
    strategy_router,
    trading_router,
    backtest_router,
    system_router,
)


# ------------------------------------------------------------------
# 全局引擎实例（在 lifespan 中初始化）
# ------------------------------------------------------------------
_orchestrator = None


def get_orchestrator():
    """获取编排器实例（供路由使用）"""
    return _orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理"""
    global _orchestrator

    setup_logging(
        level=settings.monitor.log_level,
        log_format=settings.monitor.log_format,
    )

    # ---- 启动：初始化交易系统各组件 ----
    from quant_trading_system.services.trading.orchestrator import TradingOrchestrator

    _orchestrator = TradingOrchestrator(
        mode="paper",
        exchange="binance",
        market_type="spot",
        initial_capital=settings.strategy.backtest_start_capital,
    )
    await _orchestrator.start()

    yield

    # ---- 关闭：清理资源 ----
    if _orchestrator:
        await _orchestrator.stop()
        _orchestrator = None


def create_app() -> FastAPI:
    """创建FastAPI应用"""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="生产级量化交易系统API",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(system_router, prefix="/api/v1/system", tags=["系统"])
    app.include_router(market_router, prefix="/api/v1/market", tags=["行情"])
    app.include_router(strategy_router, prefix="/api/v1/strategy", tags=["策略"])
    app.include_router(trading_router, prefix="/api/v1/trading", tags=["交易"])
    app.include_router(backtest_router, prefix="/api/v1/backtest", tags=["回测"])

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        )

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        orch = get_orchestrator()
        return {
            "status": "healthy" if (orch and orch.is_running) else "degraded",
            "version": settings.app_version,
            "trading_mode": orch.mode if orch else None,
        }

    return app


# 创建应用实例
app = create_app()
