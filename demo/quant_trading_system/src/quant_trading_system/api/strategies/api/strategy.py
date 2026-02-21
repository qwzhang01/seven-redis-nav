"""
C 端策略管理路由
================

面向普通用户（customer）的策略管理接口，挂载在 /api/v1/c/strategy/ 下。

与 M 端（管理员）策略接口的区别：
- 用户只能操作自己创建的策略（通过 JWT 中的 username 绑定）
- 策略 ID 格式为 {username}__{strategy_id}，实现用户隔离
- 不允许操作其他用户的策略

主要功能：
- 策略创建、更新、删除管理
- 策略启动、停止、暂停、恢复控制
- 策略列表和详情查询
- 策略信号历史记录查询
- 可用策略类型查询
- 首页优选策略展示
- 策略订阅、收藏、点赞操作
- 策略模拟交易
- 策略性能指标查询
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

# 创建 C 端策略路由实例
router = APIRouter()


def _get_engines():
    """
    获取编排器中的引擎实例

    返回当前系统的编排器实例，用于访问策略引擎和其他组件。

    异常：
    - HTTPException: 当交易系统未启动时返回503错误
    """
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


def _get_current_username(request: Request) -> str:
    """
    从请求状态中获取当前登录用户名。

    AuthMiddleware 已将 JWT 中的 username 写入 request.state.username。

    异常：
    - HTTPException: 当用户未认证时返回401错误
    """
    username = getattr(request.state, "username", None)
    if not username:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    return username


def _make_strategy_id(username: str, strategy_id: str) -> str:
    """
    生成用户隔离的策略 ID。

    格式：{username}__{strategy_id}
    """
    return f"{username}__{strategy_id}"


def _is_owned_by(strategy_id: str, username: str) -> bool:
    """
    判断策略是否属于指定用户。

    策略 ID 以 {username}__ 开头则认为属于该用户。
    """
    return strategy_id.startswith(f"{username}__")


class CreateStrategyRequest(BaseModel):
    """
    创建策略请求数据模型

    参数说明：
    - name: 策略名称（用户自定义）
    - strategy_type: 策略类型名称（系统注册的策略类型）
    - symbols: 策略监控的交易对列表
    - params: 策略参数配置字典
    """
    name: str
    strategy_type: str
    symbols: list[str]
    params: dict[str, Any] = {}


class UpdateStrategyRequest(BaseModel):
    """
    更新策略请求数据模型

    参数说明：
    - params: 要更新的策略参数字典
    """
    params: dict[str, Any] = {}


class SimulateStrategyRequest(BaseModel):
    """
    模拟交易请求数据模型

    参数说明：
    - strategy_type: 策略类型名称
    - symbols: 策略监控的交易对列表
    - params: 策略参数配置字典
    - initial_capital: 模拟初始资金（USDT），默认 10000
    """
    strategy_type: str
    symbols: list[str]
    params: dict[str, Any] = {}
    initial_capital: float = 10000.0


@router.get("/featured")
async def get_featured_strategies(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
) -> dict[str, Any]:
    """
    获取首页优选策略

    返回系统推荐的优质策略列表，用于首页展示。
    优选策略从已发布（published=True）的策略中按信号数量降序排列。

    参数：
    - limit: 返回策略数量（1-50，默认10）

    返回：
    - strategies: 优选策略列表
    - total: 返回数量

    策略信息包含：
    - strategy_id: 策略唯一标识
    - name: 策略名称
    - state: 策略状态
    - symbols: 监控的交易对列表
    - timeframes: 使用的时间周期列表
    - signal_count: 累计信号数（用于排序参考）
    """
    orch = _get_engines()
    se = orch.strategy_engine
    featured = []
    for sid in se.list_strategies():
        s = se.get_strategy(sid)
        if not s:
            continue
        # 只展示已发布的策略
        if not s.params.get("published", False):
            continue
        featured.append({
            "strategy_id": sid,
            "name": s.name,
            "state": s.state.value,
            "symbols": s.symbols,
            "timeframes": [tf.value for tf in s.timeframes],
            "signal_count": s._signal_count,
        })
    # 按信号数降序排列，取前 limit 条
    featured.sort(key=lambda x: x["signal_count"], reverse=True)
    featured = featured[:limit]
    return {"strategies": featured, "total": len(featured)}


@router.get("/types")
async def get_strategy_types() -> dict[str, Any]:
    """
    获取可用的策略类型

    查询系统中所有已注册的策略类型及其配置信息。
    普通用户可查看所有可用策略类型，用于创建策略时选择。

    返回：
    - types: 策略类型信息列表

    策略类型信息包含：
    - name: 策略类型名称
    - description: 策略描述
    - params: 策略参数定义
    - timeframes: 支持的时间周期列表
    """
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import (
        list_strategies as list_registered,
        get_strategy_class,
    )

    def _serialize_params_def(params_def: dict) -> dict:
        """将 params_def 中的 type 字段（Python 类对象）转换为字符串"""
        result = {}
        for key, definition in params_def.items():
            serialized = {}
            for k, v in definition.items():
                if k == "type" and isinstance(v, type):
                    serialized[k] = v.__name__
                else:
                    serialized[k] = v
            result[key] = serialized
        return result

    types = []
    for name in list_registered():
        cls = get_strategy_class(name)
        if cls:
            types.append({
                "name": name,
                "description": cls.description,
                "params": _serialize_params_def(cls.params_def),
                "timeframes": [tf.value for tf in cls.timeframes],
            })
    return {"types": types}


@router.get("/list")
async def list_strategies(
    request: Request,
    state: Optional[str] = Query(None, description="按状态筛选：running / stopped / paused"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict[str, Any]:
    """
    获取当前用户的策略列表

    查询当前登录用户创建的所有策略基本信息列表，支持状态筛选和分页。
    用户只能看到自己创建的策略，不能看到其他用户的策略。

    参数：
    - state: 策略状态筛选（running/stopped/paused）
    - page: 页码（从1开始）
    - page_size: 每页数量（1-100）

    返回：
    - strategies: 策略信息列表
    - total: 符合条件的策略总数
    - page: 当前页码
    - page_size: 每页数量

    策略信息包含：
    - strategy_id: 策略唯一标识
    - name: 策略名称
    - state: 策略状态（running/stopped/paused）
    - symbols: 监控的交易对列表
    - timeframes: 使用的时间周期列表
    """
    username = _get_current_username(request)
    orch = _get_engines()
    se = orch.strategy_engine
    strategies = []
    for sid in se.list_strategies():
        # 只返回属于当前用户的策略
        if not _is_owned_by(sid, username):
            continue
        s = se.get_strategy(sid)
        if not s:
            continue
        # 状态过滤
        if state and s.state.value != state:
            continue
        strategies.append({
            "strategy_id": sid,
            "name": s.name,
            "state": s.state.value,
            "symbols": s.symbols,
            "timeframes": [tf.value for tf in s.timeframes],
        })

    total = len(strategies)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "strategies": strategies[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    获取策略性能指标

    查询当前用户指定策略的运行性能统计数据。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - strategy_id: 策略ID
    - performance: 性能指标字典，包含：
        - signal_count: 累计信号数
        - trade_count: 累计交易次数
        - running_seconds: 运行时长（秒）
        - total_return: 累计收益率（占位，待接入实际数据）
        - max_drawdown: 最大回撤（占位）
        - sharpe_ratio: 夏普比率（占位）
        - win_rate: 胜率（占位）

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    - HTTPException 404: 当策略不存在时
    """
    import time as _time
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权访问该策略")
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")

    running_seconds = 0.0
    if s.started_at:
        stopped = s.stopped_at if s.stopped_at else _time.time()
        running_seconds = stopped - s.started_at

    return {
        "strategy_id": strategy_id,
        "performance": {
            "signal_count": s._signal_count,
            "trade_count": s._trade_count,
            "running_seconds": round(running_seconds, 2),
            # 以下指标需接入回测/实盘数据后实现
            "total_return": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "win_rate": None,
        },
    }


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    获取策略详情

    查询当前用户指定策略的详细信息和运行状态。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - strategy_id: 策略ID
    - name: 策略名称
    - state: 策略状态
    - params: 策略参数配置
    - symbols: 监控的交易对列表
    - timeframes: 使用的时间周期列表
    - stats: 策略统计信息

    异常：
    - HTTPException 404: 当策略不存在时
    - HTTPException 403: 当策略不属于当前用户时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权访问该策略")
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": strategy_id,
        "name": s.name,
        "state": s.state.value,
        "params": s.params,
        "symbols": s.symbols,
        "timeframes": [tf.value for tf in s.timeframes],
        "stats": {
            "signal_count": s._signal_count,
            "trade_count": s._trade_count,
        },
    }


@router.post("/create")
async def create_strategy(request: Request, body: CreateStrategyRequest) -> dict[str, Any]:
    """
    创建实盘策略

    根据指定的策略类型和参数为当前用户创建新的实盘策略实例。
    策略 ID 会自动绑定当前用户，实现用户隔离。

    参数：
    - body: 创建策略请求参数

    返回：
    - success: 操作是否成功
    - strategy_id: 新创建的策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 400: 当策略类型不存在时
    """
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import get_strategy_class
    from quant_trading_system.core.snowflake import generate_snowflake_id

    username = _get_current_username(request)
    orch = _get_engines()
    cls = get_strategy_class(body.strategy_type)
    if not cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy type: {body.strategy_type}",
        )

    # 生成用户隔离的策略 ID
    raw_id = str(generate_snowflake_id())
    strategy_id = _make_strategy_id(username, raw_id)

    # 创建策略实例，传入用户隔离的 ID
    instance = cls(strategy_id=strategy_id, **body.params)
    orch.add_strategy(instance, symbols=body.symbols)

    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy created",
    }


@router.post("/simulate")
async def simulate_strategy(request: Request, body: SimulateStrategyRequest) -> dict[str, Any]:
    """
    创建模拟交易策略

    为当前用户创建一个模拟交易（纸交易）策略实例。
    模拟策略与实盘策略共享相同的行情数据，但不产生真实订单。
    策略 ID 带有 sim__ 前缀以区分模拟和实盘。

    参数：
    - body: 模拟交易请求参数

    返回：
    - success: 操作是否成功
    - strategy_id: 新创建的模拟策略ID
    - mode: 交易模式（simulate）
    - initial_capital: 模拟初始资金
    - message: 操作结果描述

    异常：
    - HTTPException 400: 当策略类型不存在时
    """
    import quant_trading_system.strategies  # noqa: F401
    from quant_trading_system.services.strategy.base import get_strategy_class
    from quant_trading_system.core.snowflake import generate_snowflake_id

    username = _get_current_username(request)
    orch = _get_engines()
    cls = get_strategy_class(body.strategy_type)
    if not cls:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy type: {body.strategy_type}",
        )

    # 模拟策略 ID 带 sim 标记
    raw_id = str(generate_snowflake_id())
    strategy_id = _make_strategy_id(username, f"sim__{raw_id}")

    # 将模拟模式和初始资金写入参数
    sim_params = dict(body.params)
    sim_params["mode"] = "simulate"
    sim_params["initial_capital"] = body.initial_capital

    instance = cls(strategy_id=strategy_id, **sim_params)
    orch.add_strategy(instance, symbols=body.symbols)

    return {
        "success": True,
        "strategy_id": strategy_id,
        "mode": "simulate",
        "initial_capital": body.initial_capital,
        "message": "Simulate strategy created",
    }


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    request: Request,
    body: UpdateStrategyRequest,
) -> dict[str, Any]:
    """
    更新策略参数

    更新当前用户指定策略的参数配置。

    参数：
    - strategy_id: 策略唯一标识
    - body: 更新策略请求参数

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    s.params.update(body.params)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy updated",
    }


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    删除策略

    从系统中删除当前用户指定的策略实例。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 被删除的策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    orch.strategy_engine.remove_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy deleted",
    }


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    启动策略

    启动当前用户指定的策略实例，开始接收行情数据并生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    try:
        await orch.strategy_engine.start_strategy(strategy_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy started",
    }


@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    停止策略

    停止当前用户指定的策略实例，不再接收行情数据和生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    await orch.strategy_engine.stop_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy stopped",
    }


@router.post("/{strategy_id}/pause")
async def pause_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    暂停策略

    暂停当前用户指定的策略实例，暂时停止生成交易信号但保持订阅行情数据。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    await orch.strategy_engine.pause_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy paused",
    }


@router.post("/{strategy_id}/resume")
async def resume_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    恢复策略

    恢复当前用户之前暂停的策略实例，重新开始生成交易信号。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - message: 操作结果描述

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权操作该策略")
    orch = _get_engines()
    await orch.strategy_engine.resume_strategy(strategy_id)
    return {
        "success": True,
        "strategy_id": strategy_id,
        "message": "Strategy resumed",
    }


@router.post("/{strategy_id}/subscribe")
async def subscribe_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    订阅策略

    订阅指定的公开策略，订阅后可接收该策略的信号通知。
    用户可订阅任意已发布的策略，不限于自己创建的策略。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 持久化订阅关系到数据库
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy subscribed",
    }


@router.delete("/{strategy_id}/subscribe")
async def unsubscribe_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    取消订阅策略

    取消对指定策略的订阅，不再接收该策略的信号通知。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 从数据库删除订阅关系
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy unsubscribed",
    }


@router.post("/{strategy_id}/favorite")
async def favorite_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    收藏策略

    将指定策略加入当前用户的收藏列表，方便后续快速访问。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 持久化收藏关系到数据库
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy favorited",
    }


@router.delete("/{strategy_id}/favorite")
async def unfavorite_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    取消收藏策略

    将指定策略从当前用户的收藏列表中移除。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 从数据库删除收藏关系
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy unfavorited",
    }


@router.post("/{strategy_id}/like")
async def like_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    点赞策略

    为指定策略点赞，每个用户对同一策略只能点赞一次。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 持久化点赞记录到数据库，并更新策略点赞计数
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy liked",
    }


@router.delete("/{strategy_id}/like")
async def unlike_strategy(strategy_id: str, request: Request) -> dict[str, Any]:
    """
    取消点赞策略

    取消对指定策略的点赞。

    参数：
    - strategy_id: 策略唯一标识

    返回：
    - success: 操作是否成功
    - strategy_id: 策略ID
    - username: 当前用户名
    - message: 操作结果描述

    异常：
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    # TODO: 从数据库删除点赞记录，并更新策略点赞计数
    return {
        "success": True,
        "strategy_id": strategy_id,
        "username": username,
        "message": "Strategy unliked",
    }


@router.get("/{strategy_id}/signals")
async def get_strategy_signals(
    strategy_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    获取策略信号历史

    查询当前用户指定策略生成的交易信号历史记录。

    参数：
    - strategy_id: 策略唯一标识
    - limit: 返回信号数量限制（1-1000）

    返回：
    - strategy_id: 策略ID
    - signals: 信号历史记录列表
    - total: 总信号数量

    异常：
    - HTTPException 403: 当策略不属于当前用户时
    - HTTPException 404: 当策略不存在时
    """
    username = _get_current_username(request)
    if not _is_owned_by(strategy_id, username):
        raise HTTPException(status_code=403, detail="无权访问该策略")
    orch = _get_engines()
    s = orch.strategy_engine.get_strategy(strategy_id)
    if not s:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "strategy_id": strategy_id,
        "signals": [],  # TODO: 实现信号历史存储
        "total": 0,
    }
