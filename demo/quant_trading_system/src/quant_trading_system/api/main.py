#!/usr/bin/env python3
"""
量化交易系统 API 主入口
"""

import os
from pathlib import Path

# 在导入其他模块之前加载.env文件
from dotenv import load_dotenv

# 加载项目根目录下的.env文件
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from quant_trading_system.core.config import settings
from quant_trading_system.core.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# 导入新的业务域路由
from .users.api.user import router as user_router
from .strategies.api.strategy import router as strategy_router
from .trading.api.trading import router as trading_router
from .market.api.market import router as market_router
from .backtest.api.backtest import router as backtest_router
from .system.api.system import router as system_router
from .health.api.health import router as health_router

from ..services.database.database import init_database
from ..config import settings

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
    - 启动时初始化数据库，并按需启动交易引擎（支持多策略并发）
    - 关闭时清理资源
    """
    import json
    import asyncio

    # 启动时执行
    print("🚀 启动量化交易系统...")

    # 初始化数据库表
    try:
        await init_database()
        print("✅ 数据库表初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

    # 若 serve 命令传入了策略配置，则自动启动交易引擎
    strategies_json = os.environ.get("_TRADE_STRATEGIES", "")
    if strategies_json:
        try:
            # 导入策略模块以触发注册
            import quant_trading_system.strategies  # noqa: F401

            from quant_trading_system.services.strategy.base import get_strategy_class
            from quant_trading_system.services.trading.orchestrator import TradingOrchestrator

            strategy_specs: list[dict] = json.loads(strategies_json)
            exchange    = os.environ.get("_TRADE_EXCHANGE", "binance")
            market_type = os.environ.get("_TRADE_MARKET_TYPE", "spot")
            capital     = float(os.environ.get("_TRADE_CAPITAL", "100000"))
            api_key     = os.environ.get("_TRADE_API_KEY", "")
            api_secret  = os.environ.get("_TRADE_API_SECRET", "")
            mode        = os.environ.get("_TRADE_MODE", "paper")

            orchestrator = TradingOrchestrator(
                mode=mode,
                exchange=exchange,
                market_type=market_type,
                api_key=api_key,
                api_secret=api_secret,
                initial_capital=capital,
            )
            await orchestrator.start()

            # 并发添加所有策略（add_strategy 是同步的，但可以并发 start_strategy）
            for spec in strategy_specs:
                strategy_class = get_strategy_class(spec["name"])
                if strategy_class is None:
                    print(f"⚠️  策略 '{spec['name']}' 未找到，已跳过")
                    continue
                orchestrator.add_strategy(strategy_class, symbols=spec["symbols"])

            # 并发启动所有策略
            await orchestrator.start_all_strategies()
            # 订阅所有策略关注的行情
            await orchestrator.subscribe_market()

            set_orchestrator(orchestrator)

            names = [f"{s['name']}→{s['symbols']}" for s in strategy_specs]
            print(f"✅ 交易引擎启动完成 | 模式={mode} | 策略={names}")

        except Exception as e:
            print(f"❌ 交易引擎启动失败: {e}")
            raise

    yield

    # 关闭时执行
    print("🛑 停止量化交易系统...")
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

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "message": str(exc),
            "path": request.url.path
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "message": str(exc.detail),
            "path": request.url.path
        }
    )


# 注册路由
app.include_router(user_router, prefix="/api/v1/user", tags=["user"])
app.include_router(strategy_router, prefix="/api/v1/strategy", tags=["strategy"])
app.include_router(trading_router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(market_router, prefix="/api/v1/market", tags=["market"])
app.include_router(backtest_router, prefix="/api/v1/backtest", tags=["backtest"])
app.include_router(system_router, prefix="/api/v1/system", tags=["system"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])


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
        "health": "/api/v1/health"
    }


@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点
    用于负载均衡器和监控系统
    """
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
        "service": "quant-trading-system"
    }


@app.get("/api/v1/info")
async def system_info() -> Dict[str, Any]:
    """
    系统信息接口
    返回系统配置和状态信息
    """
    return {
        "success": True,
        "data": {
            "system": {
                "name": "量化交易系统",
                "version": "1.0.0",
                "description": "用户管理和交易所API管理系统"
            },
            "features": {
                "user_management": True,
                "exchange_management": True,
                "api_key_management": True,
                "jwt_authentication": True,
                "password_reset": True
            },
            "database": {
                "type": "PostgreSQL",
                "timescale_support": True
            },
            "security": {
                "password_hashing": "bcrypt",
                "jwt_algorithm": "HS256",
                "cors_enabled": True
            }
        }
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
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
