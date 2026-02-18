"""
交易路由模块
===========

提供交易执行和订单管理相关的API接口，接入TradingEngine实例，支持完整的交易生命周期管理。

主要功能：
- 下单和订单执行管理
- 订单查询和状态监控
- 持仓管理和查询
- 账户信息查询
- 风险信息查询
- 成交记录查询
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 创建交易路由实例
router = APIRouter()


def _get_engines():
    """
    获取编排器中的引擎实例

    返回当前系统的编排器实例，用于访问交易引擎和其他组件。

    异常：
    - HTTPException: 当交易系统未启动时返回503错误
    """
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


class PlaceOrderRequest(BaseModel):
    """
    下单请求数据模型

    参数说明：
    - symbol: 交易对符号
    - side: 交易方向（buy/sell）
    - order_type: 订单类型（market/limit）
    - quantity: 交易数量
    - price: 限价单价格（限价单必填）
    - strategy_id: 策略ID（可选，用于关联策略）
    """
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit
    quantity: float
    price: float | None = None
    strategy_id: str = ""


class CancelOrderRequest(BaseModel):
    """
    取消订单请求数据模型

    参数说明：
    - order_id: 要取消的订单ID
    """
    order_id: str


@router.post("/order")
async def place_order(request: PlaceOrderRequest) -> dict[str, Any]:
    """
    下单接口

    提交新的交易订单到交易引擎执行。

    参数：
    - request: 下单请求参数

    返回：
    - success: 操作是否成功
    - order_id: 新创建的订单ID
    - message: 操作结果描述

    异常：
    - HTTPException: 当订单被拒绝时返回400错误

    说明：
    - 市价单：立即按当前市场价格成交，无需指定价格
    - 限价单：按指定价格或更优价格成交
    """
    from quant_trading_system.services.strategy.signal import Signal, SignalType

    orch = _get_engines()

    # 确定交易方向
    signal_type = SignalType.BUY if request.side.upper() == "BUY" else SignalType.SELL
    signal = Signal(
        strategy_id=request.strategy_id or "manual",
        symbol=request.symbol,
        signal_type=signal_type,
        price=request.price or 0.0,
        quantity=request.quantity,
    )

    # 执行交易信号
    order = await orch.trading_engine.execute_signal(signal)
    if order is None:
        raise HTTPException(status_code=400, detail="Order rejected")

    return {
        "success": True,
        "order_id": order.id,
        "message": "Order submitted",
    }


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str) -> dict[str, Any]:
    """
    取消订单接口

    取消指定的未成交订单。

    参数：
    - order_id: 要取消的订单ID

    返回：
    - success: 操作是否成功
    - order_id: 被取消的订单ID
    - message: 操作结果描述

    异常：
    - HTTPException: 当取消操作失败时返回400错误
    """
    orch = _get_engines()
    success = await orch.trading_engine.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cancel failed")
    return {
        "success": True,
        "order_id": order_id,
        "message": "Order cancelled",
    }


@router.post("/order/cancel-all")
async def cancel_all_orders(
    symbol: str | None = Query(None, description="交易对"),
) -> dict[str, Any]:
    """
    取消所有订单接口

    取消所有未成交订单，可选择指定交易对。

    参数：
    - symbol: 可选，指定交易对，为空则取消所有订单

    返回：
    - success: 操作是否成功
    - cancelled_count: 取消的订单数量
    - message: 操作结果描述
    """
    orch = _get_engines()
    count = await orch.trading_engine.cancel_all_orders(symbol)
    return {
        "success": True,
        "cancelled_count": count,
        "message": "All orders cancelled",
    }


@router.get("/orders")
async def get_orders(
    status: str = Query("active", description="订单状态 active|all"),
    symbol: str | None = Query(None, description="交易对"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    获取订单列表接口

    查询订单列表，支持按状态和交易对过滤。

    参数：
    - status: 订单状态（active: 仅活跃订单，all: 所有订单）
    - symbol: 可选，交易对过滤
    - limit: 返回记录数量限制（1-1000）

    返回：
    - orders: 订单信息列表
    - total: 总订单数量

    订单信息包含：
    - order_id: 订单ID
    - symbol: 交易对
    - side: 交易方向
    - type: 订单类型
    - status: 订单状态
    - quantity: 订单数量
    - price: 订单价格
    - strategy_id: 关联策略ID
    """
    orch = _get_engines()
    om = orch.trading_engine.order_manager

    # 根据状态和交易对过滤订单
    if status == "active":
        if symbol:
            orders = om.get_active_orders_by_symbol(symbol)
        else:
            orders = om.get_active_orders()
    else:
        if symbol:
            orders = om.get_orders_by_symbol(symbol)
        else:
            orders = list(om._orders.values())

    # 格式化订单信息
    order_list = []
    for o in orders[:limit]:
        order_list.append({
            "order_id": o.order_id,
            "symbol": o.symbol,
            "side": o.side.value,
            "type": o.order_type.value,
            "status": o.status.value,
            "quantity": o.quantity,
            "price": o.price,
            "strategy_id": o.strategy_id,
        })

    return {"orders": order_list, "total": len(order_list)}


@router.get("/order/{order_id}")
async def get_order(order_id: str) -> dict[str, Any]:
    """
    获取订单详情接口

    查询指定订单的详细信息。

    参数：
    - order_id: 订单ID

    返回：
    - order_id: 订单ID
    - symbol: 交易对
    - side: 交易方向
    - type: 订单类型
    - status: 订单状态
    - quantity: 订单数量
    - filled_quantity: 已成交数量
    - price: 订单价格
    - avg_price: 平均成交价格

    异常：
    - HTTPException: 当订单不存在时返回404错误
    """
    orch = _get_engines()
    o = orch.trading_engine.order_manager.get_order(order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": o.order_id,
        "symbol": o.symbol,
        "side": o.side.value,
        "type": o.order_type.value,
        "status": o.status.value,
        "quantity": o.quantity,
        "filled_quantity": o.filled_quantity,
        "price": o.price,
        "avg_price": o.avg_price,
    }


@router.get("/trades")
async def get_trades(
    symbol: str | None = Query(None, description="交易对"),
    order_id: str | None = Query(None, description="订单ID"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    获取成交记录接口

    查询成交记录，支持按交易对和订单ID过滤。

    参数：
    - symbol: 可选，交易对过滤
    - order_id: 可选，订单ID过滤
    - limit: 返回记录数量限制（1-1000）

    返回：
    - trades: 成交记录列表
    - total: 总成交记录数

    成交记录包含：
    - trade_id: 成交ID
    - order_id: 关联订单ID
    - symbol: 交易对
    - side: 交易方向
    - price: 成交价格
    - quantity: 成交数量
    - commission: 手续费
    """
    orch = _get_engines()
    om = orch.trading_engine.order_manager

    # 根据过滤条件获取成交记录
    if order_id:
        trades = om.get_trades_by_order(order_id)
    else:
        trades = list(om._trades.values())
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

    # 格式化成交记录
    trade_list = []
    for t in trades[:limit]:
        trade_list.append({
            "trade_id": t.trade_id,
            "order_id": t.order_id,
            "symbol": t.symbol,
            "side": t.side.value,
            "price": t.price,
            "quantity": t.quantity,
            "commission": t.commission,
        })

    return {"trades": trade_list, "total": len(trade_list)}


@router.get("/positions")
async def get_positions() -> dict[str, Any]:
    """
    获取持仓列表接口

    查询所有持仓的详细信息。

    返回：
    - positions: 持仓信息列表
    - total_value: 持仓总价值

    持仓信息包含：
    - symbol: 交易对
    - quantity: 持仓数量
    - avg_price: 平均成本价
    - last_price: 最新价格
    - unrealized_pnl: 未实现盈亏
    - realized_pnl: 已实现盈亏
    - value: 持仓价值
    """
    orch = _get_engines()
    positions = orch.trading_engine._positions

    pos_list = []
    total_value = 0.0
    for sym, pos in positions.items():
        value = pos.quantity * pos.last_price
        total_value += value
        pos_list.append({
            "symbol": sym,
            "quantity": pos.quantity,
            "avg_price": pos.avg_price,
            "last_price": pos.last_price,
            "unrealized_pnl": pos.unrealized_pnl,
            "realized_pnl": pos.realized_pnl,
            "value": value,
        })

    return {"positions": pos_list, "total_value": total_value}


@router.get("/position/{symbol}")
async def get_position(symbol: str) -> dict[str, Any]:
    """
    获取单个持仓详情接口

    查询指定交易对的持仓详细信息。

    参数：
    - symbol: 交易对符号

    返回：
    - symbol: 交易对
    - quantity: 持仓数量
    - avg_price: 平均成本价
    - current_price: 当前价格
    - unrealized_pnl: 未实现盈亏
    - realized_pnl: 已实现盈亏
    """
    orch = _get_engines()
    pos = orch.trading_engine._positions.get(symbol)
    if not pos:
        return {
            "symbol": symbol,
            "quantity": 0,
            "avg_price": 0,
            "current_price": 0,
            "unrealized_pnl": 0,
            "realized_pnl": 0,
        }
    return {
        "symbol": symbol,
        "quantity": pos.quantity,
        "avg_price": pos.avg_price,
        "current_price": pos.last_price,
        "unrealized_pnl": pos.unrealized_pnl,
        "realized_pnl": pos.realized_pnl,
    }


@router.get("/account")
async def get_account() -> dict[str, Any]:
    """
    获取账户信息接口

    查询账户余额、保证金等账户信息。

    返回：
    - total_equity: 总资产
    - available_margin: 可用保证金
    - used_margin: 已用保证金
    - balances: 各币种余额信息

    余额信息包含：
    - free: 可用余额
    - locked: 冻结余额
    - total: 总余额
    """
    orch = _get_engines()
    acc = orch.trading_engine._account
    if not acc:
        return {"total_equity": 0, "available_margin": 0, "used_margin": 0, "balances": {}}
    return {
        "total_equity": acc.total_balance,
        "available_margin": acc.available_balance,
        "used_margin": acc.margin_balance - acc.available_balance,
        "balances": {k: {"free": v.free, "locked": v.locked, "total": v.total} for k, v in acc.balances.items()},
    }


@router.get("/risk")
async def get_risk_info() -> dict[str, Any]:
    """
    获取风险信息接口

    查询风险管理器的统计信息和风险指标。

    返回：
    - 风险管理器的统计信息字典

    风险信息可能包含：
    - 最大回撤
    - 风险敞口
    - 杠杆率
    - 风险等级
    """
    orch = _get_engines()
    return orch.risk_manager.stats
