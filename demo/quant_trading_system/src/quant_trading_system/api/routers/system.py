"""
系统路由
========

系统信息和健康检查接口
"""

from typing import Any

from fastapi import APIRouter

from quant_trading_system.core.config import settings

router = APIRouter()


@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    """获取系统信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "env": settings.env,
        "debug": settings.debug,
    }


@router.get("/config")
async def get_config() -> dict[str, Any]:
    """获取系统配置（非敏感信息）"""
    return {
        "trading": {
            "order_timeout": settings.trading.order_timeout,
            "default_slippage": settings.trading.default_slippage,
            "default_commission_rate": settings.trading.default_commission_rate,
        },
        "strategy": {
            "max_concurrent_strategies": settings.strategy.max_concurrent_strategies,
            "backtest_start_capital": settings.strategy.backtest_start_capital,
        },
    }


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """健康检查"""
    return {
        "status": "healthy",
        "checks": {
            "api": True,
            "database": True,  # 实际应检查数据库连接
            "redis": True,     # 实际应检查Redis连接
        }
    }


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """获取系统指标"""
    return {
        "requests_total": 0,
        "requests_per_second": 0,
        "active_connections": 0,
        "memory_usage_mb": 0,
        "cpu_usage_percent": 0,
    }
