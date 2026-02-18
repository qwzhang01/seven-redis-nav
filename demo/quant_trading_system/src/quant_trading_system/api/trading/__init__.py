"""
交易执行业务域
===============

提供交易执行和订单管理功能，包括下单、撤单、持仓查询、账户信息等。

模块组成：
- api: 交易执行API路由
- schemas: 交易数据模型和验证模式
- services: 交易业务逻辑服务
- repositories: 交易数据访问层
- models: 交易数据模型定义
"""

from .api.trading import router as trading_router

__all__ = [
    "trading_router",
]
