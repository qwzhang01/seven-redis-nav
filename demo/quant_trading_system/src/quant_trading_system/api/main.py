#!/usr/bin/env python3
"""
量化交易系统 API 主入口
"""

from pathlib import Path

# 在导入其他模块之前加载.env文件
from dotenv import load_dotenv

# 加载项目根目录下的.env文件
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from quant_trading_system.config import settings
from quant_trading_system.core.logging import setup_logging
from quant_trading_system.api.middlewares import (
    RequestIDMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    AuthMiddleware,
)

# 导入 C 端（普通用户）和 Admin 端（管理员）聚合路由
from .c import c_router
from .m import m_router

# 导入 WebSocket 路由
from .websocket.market_ws import router as market_ws_router
from .websocket.trading_ws import router as trading_ws_router
from .websocket.strategy_ws import router as strategy_ws_router

from ..services.database.database import init_database

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 全局编排器实例（仅在启动交易引擎时设置）
_orchestrator = None


def get_orchestrator():
    """
    获取全局交易编排器实例

    返回当前系统的 TradingOrchestrator 实例。
    若交易系统未启动，则返回 None，调用方应返回 503 错误。
    """
    return _orchestrator


def set_orchestrator(orch) -> None:
    """设置全局交易编排器实例"""
    global _orchestrator
    _orchestrator = orch


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时初始化数据库，自动创建编排器并加载所有已注册策略（stopped 状态）
    - 策略不会自动运行，需用户通过 API 显式启动
    - 关闭时清理资源
    """
    # 启动时执行
    print("🚀 启动量化交易系统...")

    # 初始化数据库表
    try:
        await init_database()
        print("✅ 数据库表初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

    # 自动初始化编排器，加载所有已注册策略（不启动、不订阅行情）
    try:
        # 导入策略模块以触发注册
        import quant_trading_system.strategies  # noqa: F401

        from quant_trading_system.services.strategy.base import (
            list_strategies as list_registered,
            get_strategy_class,
        )
        from quant_trading_system.services.trading.orchestrator import \
            TradingOrchestrator

        orchestrator = TradingOrchestrator(
            mode="paper",  # 默认 paper 模式，用户启动策略时可按需覆盖
            exchange="binance",
            market_type="spot",
            api_key=settings.BINANCE_API_KEY or "",  # 从配置读取API key
            api_secret=settings.BINANCE_SECRET_KEY or "",  # 从配置读取API secret
        )
        await orchestrator.start()

        # 将所有已注册策略以 stopped 状态加入编排器（不启动、不订阅行情）
        registered = list_registered()
        for name in registered:
            cls = get_strategy_class(name)
            if cls is None:
                continue
            # 使用策略类自带的默认交易对（若有），否则留空
            default_symbols = list(cls.symbols) if cls.symbols else []
            orchestrator.add_strategy(cls, symbols=default_symbols)

        set_orchestrator(orchestrator)
        print(
            f"✅ 编排器启动完成，已加载 {len(registered)} 个策略类型（均处于 stopped 状态）")
        print(f"   已注册策略: {registered}")

    except Exception as e:
        print(f"❌ 编排器初始化失败: {e}")
        raise

    # 启动订阅监听器
    try:
        from quant_trading_system.services.market.subscription_monitor import \
            init_subscription_monitor
        await init_subscription_monitor()
        print("✅ 订阅监听器启动完成")
    except Exception as e:
        print(f"❌ 订阅监听器启动失败: {e}")
        raise

    # 启动历史数据同步执行器
    try:
        from quant_trading_system.services.market.historical_sync_executor import \
            init_historical_sync_executor
        await init_historical_sync_executor()
        print("✅ 历史数据同步执行器启动完成")
    except Exception as e:
        print(f"❌ 历史数据同步执行器启动失败: {e}")
        raise

    yield

    # 关闭时执行
    print("🛑 停止量化交易系统...")

    # 关闭历史数据同步执行器
    try:
        from quant_trading_system.services.market.historical_sync_executor import \
            close_historical_sync_executor
        await close_historical_sync_executor()
        print("✅ 历史数据同步执行器已停止")
    except Exception as e:
        print(f"❌ 历史数据同步执行器停止失败: {e}")

    # 关闭订阅监听器
    try:
        from quant_trading_system.services.market.subscription_monitor import \
            close_subscription_monitor
        await close_subscription_monitor()
        print("✅ 订阅监听器已停止")
    except Exception as e:
        print(f"❌ 订阅监听器停止失败: {e}")

    orch = get_orchestrator()
    if orch is not None:
        await orch.stop()
        set_orchestrator(None)
        print("✅ 交易引擎已停止")


# 创建FastAPI应用实例
app = FastAPI(
    title="量化交易系统 API",
    description="用户管理和交易所API管理系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# ── 中间件注册（执行顺序：后注册先执行）──────────────────────────
# 实际执行顺序：RequestID → Logging → RateLimit → Auth → CORS → 路由
# 注册顺序：CORS → Auth → RateLimit → Logging → RequestID

# 1. CORS（最先注册，最后执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 认证中间件：统一 JWT Token 校验，白名单路径自动跳过
app.add_middleware(AuthMiddleware)

# 3. 限流中间件：每 IP 每 60 秒最多 200 次请求
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)

# 4. 请求日志中间件：记录方法、路径、状态码、耗时
app.add_middleware(LoggingMiddleware)

# 5. 请求 ID 中间件（最外层，最先注册）：注入 X-Request-ID
app.add_middleware(RequestIDMiddleware)


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 处理所有类型的异常"""
    from fastapi import HTTPException

    # 如果是HTTPException，返回对应的状态码和错误信息
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "message": str(exc.detail),
                "path": request.url.path
            }
        )

    # 其他异常返回500状态码
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "message": str(exc),
            "path": request.url.path
        }
    )

# 注册路由
# C 端（普通用户）：/api/v1/c/user、/api/v1/c/market、/api/v1/c/trading、/api/v1/c/backtest
#                  /api/v1/c/signal、/api/v1/c/leaderboard、/api/v1/c/user/signal-follows
app.include_router(c_router, prefix="/api/v1/c")

# Admin 端（管理员）：/api/v1/m/strategy、/api/v1/m/system、/api/v1/m/health
#                    /api/v1/m/stats、/api/v1/m/logs、/api/v1/m/signal、/api/v1/m/leaderboard
app.include_router(m_router, prefix="/api/v1/m")

# WebSocket 路由：/api/v1/ws/market、/api/v1/ws/trading、/api/v1/ws/strategy
app.include_router(market_ws_router, prefix="/api/v1/ws", tags=["WebSocket-行情推送"])
app.include_router(trading_ws_router, prefix="/api/v1/ws", tags=["WebSocket-交易推送"])
app.include_router(strategy_ws_router, prefix="/api/v1/ws", tags=["WebSocket-策略推送"])


# 测试路由：验证异常处理器
@app.get("/api/v1/test/exception")
async def test_exception_handler():
    """测试异常处理器 - 抛出HTTPException应该被专门的处理器捕获"""
    raise HTTPException(
        status_code=418,
        detail="这是一个测试异常，应该被HTTPException处理器捕获"
    )


# 根路径
@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """
    根路径
    返回系统基本信息
    """
    return {
        "message": "欢迎使用量化交易系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/m/health"
    }


# 自定义OpenAPI文档
@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """自定义Swagger UI文档"""
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title="量化交易系统 API - 文档",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )


def custom_openapi():
    """自定义OpenAPI配置"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 添加安全配置
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # 添加全局安全要求
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    用于在其他模块中导入使用
    """
    return app


if __name__ == "__main__":
    import uvicorn

    # 启动开发服务器
    uvicorn.run(
        "src.quant_trading_system.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
        log_level="info"
    )
