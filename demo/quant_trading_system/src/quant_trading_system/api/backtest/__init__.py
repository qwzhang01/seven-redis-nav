"""
回测业务域
===========

提供策略回测功能，包括回测执行、结果分析、历史记录管理等功能。

模块组成：
- api: 回测API路由
- schemas: 回测数据模型和验证模式
- services: 回测业务逻辑服务
- repositories: 回测数据访问层
- models: 回测数据模型定义
"""

from .api.backtest import router as backtest_router

__all__ = [
    "backtest_router",
]
