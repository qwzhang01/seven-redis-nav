"""
交易路由
========

交易管理API接口 — 接入 TradingEngine 实例
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


def _get_engines():
    """获取编排器"""
    from quant_trading_system.api.main import get_orchestrator

    orch = get_orchestrator()
    if orch is None:
        raise HTTPException(status_code=503, detail="Trading system not started")
    return orch


class PlaceOrderRequest(BaseModel):
    """下单请求"""
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit
    quantity: float
    price: float | None = None
    strategy_id: str = ""


class CancelOrderRequest(BaseModel):
    """取消订单请求"""
    order_id: str


@router.post("/order")
async def place_order(request: PlaceOrderRequest) -> dict[str, Any]:
    """下单"""
    from quant_trading_system.services.strategy.signal import Signal, SignalType

    orch = _get_engines()

    signal_type = SignalType.BUY if request.side.upper() == "BUY" else SignalType.SELL
    signal = Signal(
        strategy_id=request.strategy_id or "manual",
        symbol=request.symbol,
        signal_type=signal_type,
        price=request.price or 0.0,
        quantity=request.quantity,
    )

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
    """取消订单"""
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
    """取消所有订单"""
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
    """获取订单列表"""
    orch = _get_engines()
    om = orch.trading_engine.order_manager

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
    """获取订单详情"""
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
    """获取成交记录"""
    orch = _get_engines()
    om = orch.trading_engine.order_manager

    if order_id:
        trades = om.get_trades_by_order(order_id)
    else:
        trades = list(om._trades.values())
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]

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
    """获取持仓列表"""
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
    """获取单个持仓"""
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
    """获取账户信息"""
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
    """获取风险信息"""
    orch = _get_engines()
    return orch.risk_manager.stats
