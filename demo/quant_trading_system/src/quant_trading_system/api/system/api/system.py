"""
系统路由模块
===========

提供系统管理和监控相关的API接口，包括系统信息、配置查询、健康检查和性能指标等功能。

主要功能：
- 系统基本信息查询
- 配置参数查询（非敏感信息）
- 系统健康状态检查
- 性能指标和统计信息查询
"""

from typing import Any

from fastapi import APIRouter, Request, Depends

from quant_trading_system.core.config import settings

# 创建系统路由实例
router = APIRouter()


async def _get_optional_orchestrator(request: Request):
    """
    可选的编排器依赖注入

    返回编排器实例或 None（系统未启动时不抛异常）。
    """
    return getattr(request.app.state, "orchestrator", None)


@router.get("/info")
async def get_system_info(
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    获取系统基本信息

    查询量化交易系统的版本、环境、运行状态等基本信息。

    返回：
    - name: 系统名称
    - version: 系统版本号
    - env: 运行环境（development/production）
    - debug: 调试模式状态
    - trading_mode: 交易模式（live/backtest）
    - trading_running: 交易系统是否正在运行
    """
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
    """
    获取系统配置信息（非敏感信息）

    查询系统的公开配置参数，不包含敏感信息如API密钥等。

    返回：
    - trading: 交易相关配置
    - strategy: 策略相关配置

    交易配置包含：
    - order_timeout: 订单超时时间
    - default_slippage: 默认滑点率
    - default_commission_rate: 默认手续费率

    策略配置包含：
    - max_concurrent_strategies: 最大并发策略数
    - backtest_start_capital: 回测初始资金
    """
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
async def health_check(
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    系统健康检查

    检查系统各核心组件的运行状态，评估系统整体健康度。

    返回：
    - status: 系统整体状态（healthy/degraded）
    - checks: 各组件健康状态检查结果

    组件检查包含：
    - api: API服务状态
    - event_engine: 事件引擎状态
    - market_service: 市场服务状态
    - strategy_engine: 策略引擎状态
    - trading_engine: 交易引擎状态
    """
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
async def get_metrics(
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    获取系统性能指标

    查询系统各核心组件的性能统计数据和运行指标。

    返回：
    - event_engine: 事件引擎统计信息
    - market_service: 市场服务统计信息
    - strategy_engine: 策略引擎统计信息
    - trading_engine: 交易引擎统计信息
    - risk_manager: 风险管理器统计信息

    当系统未启动时返回空的统计信息字典。
    """
    if not orch:
        return {
            "event_engine": {},
            "market_service": {},
            "strategy_engine": {},
            "trading_engine": {},
            "risk_manager": {},
        }
    return orch.stats
