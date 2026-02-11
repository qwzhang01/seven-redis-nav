"""
系统路由
========

系统信息和健康检查接口
"""

from typing import Any

from fastapi import APIRouter

from quant_trading_system.core.config import settings

router = APIRouter()


def _get_orchestrator():
    from quant_trading_system.api.main import get_orchestrator
    return get_orchestrator()


@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    """获取系统信息"""
    orch = _get_orchestrator()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "env": settings.env,
        "debug": settings.debug,
        "trading_mode": orch.mode if orch else None,
        "trading_running": orch.is_running if orch else False,
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
    orch = _get_orchestrator()
    return {
        "status": "healthy" if (orch and orch.is_running) else "degraded",
        "checks": {
            "api": True,
            "event_engine": orch.event_engine.is_running if orch else False,
            "market_service": orch.market_service.is_running if orch else False,
            "strategy_engine": orch.strategy_engine.is_running if orch else False,
            "trading_engine": orch.trading_engine.is_running if orch else False,
        },
    }


@router.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """获取系统指标"""
    orch = _get_orchestrator()
    if not orch:
        return {
            "event_engine": {},
            "market_service": {},
            "strategy_engine": {},
            "trading_engine": {},
            "risk_manager": {},
        }
    return orch.stats
