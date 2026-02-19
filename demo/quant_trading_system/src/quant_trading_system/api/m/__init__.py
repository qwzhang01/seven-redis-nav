"""
Admin 端（管理员）路由聚合包
============================

包含所有面向管理员的 API 接口，统一挂载在 /api/v1/m/ 前缀下。

模块列表：
- strategy : 策略创建、启停、参数管理
- system   : 系统信息、配置、健康检查、性能指标
- health   : 健康探针（DB、完整检查、K8s 探针）
"""

from fastapi import APIRouter

from quant_trading_system.api.strategies.api.strategy import router as strategy_router
from quant_trading_system.api.system.api.system import router as system_router
from quant_trading_system.api.health.api.health import router as health_router

# Admin 端聚合路由
m_router = APIRouter()

m_router.include_router(strategy_router, prefix="/strategy", tags=["Admin-策略管理"])
m_router.include_router(system_router, prefix="/system", tags=["Admin-系统管理"])
m_router.include_router(health_router, prefix="", tags=["Admin-健康检查"])

__all__ = ["m_router"]
