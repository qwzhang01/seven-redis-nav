#!/usr/bin/env python3
"""
量化交易系统 API 主入口
======================

职责：
- 创建 FastAPI 实例
- 注册中间件
- 注册路由
- 异常处理
- OpenAPI 配置
"""

from pathlib import Path

# 在导入其他模块之前加载.env文件
from dotenv import load_dotenv

# 加载项目根目录下的.env文件
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

import logging
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from quant_trading_system.core.config import settings
from quant_trading_system.core.logging import setup_logging
from quant_trading_system.api.lifespan import lifespan
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

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name + " API",
    description="用户管理和交易所API管理系统",
    version=settings.app_version,
    docs_url=settings.DOCS_URL or None,
    redoc_url=settings.REDOC_URL or None,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)


# ── 中间件注册（执行顺序：后注册先执行）──────────────────────────
# 实际执行顺序：RequestID → Logging → RateLimit → Auth → CORS → 路由

# 1. CORS（最先注册，最后执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 认证中间件
app.add_middleware(AuthMiddleware)

# 3. 限流中间件
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)

# 4. 请求日志中间件
app.add_middleware(LoggingMiddleware)

# 5. 请求 ID 中间件（最外层）
app.add_middleware(RequestIDMiddleware)


# ── 异常处理 ──────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "message": str(exc.detail),
                "path": request.url.path,
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "message": str(exc),
            "path": request.url.path,
        },
    )


# ── 路由注册 ──────────────────────────────────────────────────────

# C 端（普通用户）
app.include_router(c_router, prefix=f"{settings.API_PREFIX}/c")

# Admin 端（管理员）
app.include_router(m_router, prefix=f"{settings.API_PREFIX}/m")

# WebSocket 路由
app.include_router(market_ws_router, prefix=f"{settings.API_PREFIX}/ws", tags=["WebSocket-行情推送"])
app.include_router(trading_ws_router, prefix=f"{settings.API_PREFIX}/ws", tags=["WebSocket-交易推送"])
app.include_router(strategy_ws_router, prefix=f"{settings.API_PREFIX}/ws", tags=["WebSocket-策略推送"])


# ── 辅助路由 ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """根路径"""
    return {
        "message": f"欢迎使用{settings.app_name} API",
        "version": settings.app_version,
        "docs": settings.DOCS_URL or "/docs",
        "health": f"{settings.API_PREFIX}/m/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """返回空的 favicon 响应"""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    """自定义Swagger UI文档"""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        title=f"{settings.app_name} API - 文档",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# ── OpenAPI 配置 ──────────────────────────────────────────────────
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

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

def create_app() -> FastAPI:
    """创建FastAPI应用实例（用于在其他模块中导入使用）"""
    return app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "quant_trading_system.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
        log_level="info",
    )
