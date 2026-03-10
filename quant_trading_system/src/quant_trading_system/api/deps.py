"""
API 依赖注入模块
================

将公共依赖（如 get_orchestrator / get_orchestrator_dep）放在独立模块，
避免子路由直接导入 main.py 造成循环导入。
"""

from typing import Optional

from fastapi import Request, HTTPException

# ── 模块级 app 引用，供 get_orchestrator() 兼容接口使用 ──
_app_ref: Optional["FastAPI"] = None  # noqa: F821


def set_app_ref(app) -> None:
    """由 main.py 在 lifespan 中调用，设置 app 引用"""
    global _app_ref
    _app_ref = app


def clear_app_ref() -> None:
    """由 main.py 在 lifespan 关闭时调用，清除 app 引用"""
    global _app_ref
    _app_ref = None


def get_orchestrator():
    """
    获取全局交易编排器实例（兼容接口）

    返回当前系统的 TradingOrchestrator 实例。
    若交易系统未启动，则返回 None，调用方应返回 503 错误。

    注意：新代码请优先使用 get_orchestrator_dep() 依赖注入。
    """
    if _app_ref is not None:
        return getattr(_app_ref.state, "orchestrator", None)
    return None


async def get_orchestrator_dep(request: Request):
    """
    FastAPI 依赖注入：获取交易编排器实例

    用法：
        @router.get("/xxx")
        async def handler(orch = Depends(get_orchestrator_dep)):
            ...

    若编排器未就绪，自动返回 503 错误。
    """
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        raise HTTPException(status_code=503, detail="交易系统未就绪")
    return orch


# ── 通过 ServiceContainer 获取各服务实例的便捷函数 ──


def get_event_engine_dep():
    """FastAPI 依赖注入：获取事件引擎"""
    from quant_trading_system.core.container import container
    return container.event_engine


def get_market_service_dep():
    """FastAPI 依赖注入：获取行情服务"""
    from quant_trading_system.core.container import container
    return container.market_service


def get_indicator_engine_dep():
    """FastAPI 依赖注入：获取指标引擎"""
    from quant_trading_system.core.container import container
    return container.indicator_engine


def get_strategy_engine_dep():
    """FastAPI 依赖注入：获取策略引擎"""
    from quant_trading_system.core.container import container
    return container.strategy_engine


def get_trading_engine_dep():
    """FastAPI 依赖注入：获取交易引擎"""
    from quant_trading_system.core.container import container
    return container.trading_engine


async def get_signal_stream_engine_dep(request: Request):
    """
    FastAPI 依赖注入：获取信号监听引擎实例

    用法：
        @router.get("/xxx")
        async def handler(engine = Depends(get_signal_stream_engine_dep)):
            ...

    若信号监听引擎未就绪，自动返回 503 错误。
    """
    engine = getattr(request.app.state, "signal_stream_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="信号监听引擎未就绪")
    return engine


async def get_follow_engine_dep(request: Request):
    """
    FastAPI 依赖注入：获取信号监听引擎实例（跟单操作代理）

    用法：
        @router.get("/xxx")
        async def handler(engine = Depends(get_follow_engine_dep)):
            ...

    返回 SignalStreamEngine 实例，其内部代理了跟单相关操作。
    若信号引擎未就绪，自动返回 503 错误。
    """
    engine = getattr(request.app.state, "signal_stream_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="信号引擎未就绪")
    return engine
