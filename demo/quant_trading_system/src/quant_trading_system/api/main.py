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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期管理"""
    # 启动时
    setup_logging(
        level=settings.monitor.log_level,
        log_format=settings.monitor.log_format,
    )
    
    # 初始化服务
    # 这里可以初始化数据库连接、消息队列等
    
    yield
    
    # 关闭时
    # 清理资源


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
        return {
            "status": "healthy",
            "version": settings.app_version,
        }
    
    return app


# 创建应用实例
app = create_app()
