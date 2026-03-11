"""
全局枚举接口
===========

提供全局枚举信息查询接口，前端可以按枚举名称获取枚举 KV 信息。
"""

from typing import Any, List, Dict

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.api.users.services.user_service import UserService
from quant_trading_system.core.database import get_db
from quant_trading_system.core.enums import ENUM_REGISTRY

router = APIRouter()


@router.get("/list")
async def list_enums() -> dict[str, Any]:
    """
    获取所有可用枚举名称列表

    返回系统中注册的所有枚举类名称，前端可根据名称获取对应枚举详情。

    返回：
    - enums: 枚举名称列表
    """
    return {
        "enums": list(ENUM_REGISTRY.keys()),
    }


@router.get("/{enum_name}")
async def get_enum_values(enum_name: str) -> dict[str, Any]:
    """
    按枚举名称获取枚举 KV 信息

    根据枚举名称返回该枚举的所有选项，包含 value（值）、label（中文标签）、description（描述）。
    前端可用于渲染下拉框、筛选器等组件。

    参数：
    - enum_name: 枚举名称（如 RiskLevel、StrategyStatus 等）

    返回：
    - name: 枚举名称
    - items: 枚举选项列表，每项包含 value/label/description

    异常：
    - HTTPException 404: 枚举名称不存在时
    """
    enum_cls = ENUM_REGISTRY.get(enum_name)
    if enum_cls is None:
        raise HTTPException(
            status_code=404,
            detail=f"枚举 '{enum_name}' 不存在，可用枚举: {list(ENUM_REGISTRY.keys())}",
        )
    return {
        "name": enum_name,
        "items": enum_cls.to_list(),
    }


@router.get("/batch/{enum_names}")
async def get_batch_enum_values(enum_names: str) -> dict[str, Any]:
    """
    批量获取多个枚举 KV 信息

    支持一次请求获取多个枚举信息，枚举名称用英文逗号分隔。

    参数：
    - enum_names: 逗号分隔的枚举名称（如 "RiskLevel,StrategyStatus,MarketType"）

    返回：
    - enums: 枚举字典，key 为枚举名称，value 为枚举选项列表
    """
    names = [n.strip() for n in enum_names.split(",") if n.strip()]
    result = {}
    for name in names:
        enum_cls = ENUM_REGISTRY.get(name)
        if enum_cls is not None:
            result[name] = enum_cls.to_list()
    return {
        "enums": result,
    }


@router.get("/fine/exchanges")
async def get_exchanges(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    获取所有交易所列表

    返回系统中注册的所有交易所信息。
    """
    user_service = UserService(db)

    result = await user_service.get_exchanges()
    return result
