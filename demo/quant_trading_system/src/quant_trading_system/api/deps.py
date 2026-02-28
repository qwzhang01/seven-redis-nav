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
