#!/usr/bin/env python3
"""
量化交易系统 - FastAPI主应用
用户管理和交易所API管理系统的入口点
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .routers import user, health
from ..services.database.database import init_database
from ..config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时初始化数据库
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

    yield

    # 关闭时执行
    print("🛑 停止量化交易系统...")


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
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])


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
