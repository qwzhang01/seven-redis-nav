"""
统计分析路由模块（Admin 端）
============================

提供系统运行统计数据的查询接口，供管理员监控系统状态。

M 端接口（管理员）：
- GET /overview   : 系统概览统计
- GET /users      : 用户统计数据
- GET /strategies : 策略统计数据
- GET /trading    : 交易统计数据
- GET /market     : 行情数据统计
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from quant_trading_system.models.signal import SignalTradeRecord, Signal
from quant_trading_system.models.user import User
from quant_trading_system.models.subscription import Subscription
from quant_trading_system.core.database import get_db

router = APIRouter()


async def _get_optional_orchestrator(request: Request):
    """
    可选的编排器依赖注入

    返回编排器实例或 None（系统未启动时不抛异常），
    适用于即使编排器不可用也能部分返回数据的接口。
    """
    return getattr(request.app.state, "orchestrator", None)


@router.get("/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_db),
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    系统概览统计

    返回系统核心指标的汇总数据，包括用户数、策略数、信号数等。

    返回：
    - total_users      : 总用户数
    - active_users_today: 今日活跃用户数
    - new_users_today  : 今日新增用户数
    - total_strategies : 总策略数
    - running_strategies: 运行中策略数
    - total_signals    : 总信号数
    - signals_today    : 今日信号数
    - subscriptions    : 订阅配置数
    - ws_connections   : 当前 WebSocket 连接数
    - timestamp        : 统计时间
    """
    from quant_trading_system.api.websocket.manager import ws_manager

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    def _overview_stats(s):
        total_users = s.query(func.count(User.id)).filter(User.enable_flag == True).scalar() or 0
        new_users_today = s.query(func.count(User.id)).filter(
            User.create_time >= today_start,
            User.enable_flag == True,
        ).scalar() or 0
        active_users_today = s.query(func.count(User.id)).filter(
            User.last_login_time >= today_start,
            User.enable_flag == True,
        ).scalar() or 0
        total_signals = s.query(func.count(SignalTradeRecord.id)).scalar() or 0
        signals_today = s.query(func.count(SignalTradeRecord.id)).filter(
            SignalTradeRecord.created_at >= today_start,
        ).scalar() or 0
        total_subscriptions = s.query(func.count(Subscription.id)).scalar() or 0
        return {
            "total_users": total_users,
            "active_users_today": active_users_today,
            "new_users_today": new_users_today,
            "total_signals": total_signals,
            "signals_today": signals_today,
            "subscriptions": total_subscriptions,
        }

    db_stats = await db.run_sync(_overview_stats)

    # 策略统计（从编排器获取）
    total_strategies = 0
    running_strategies = 0
    try:
        strategy_ids = orch.strategy_engine.list_strategies() if orch else []
        total_strategies = len(strategy_ids)
        running_strategies = sum(
            1 for sid in strategy_ids
            if orch.strategy_engine.get_strategy(sid) and
               orch.strategy_engine.get_strategy(sid).state.value == "running"
        )
    except Exception:
        pass

    return {
        **db_stats,
        "total_strategies": total_strategies,
        "running_strategies": running_strategies,
        "ws_connections": ws_manager.connection_count,
        "ws_channel_stats": ws_manager.channel_stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/users")
async def get_user_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    用户统计数据

    返回用户注册、活跃趋势等统计数据。

    参数：
    - days: 统计天数（1-90，默认7天）

    返回：
    - total_users    : 总用户数
    - user_type_dist : 用户类型分布
    - status_dist    : 用户状态分布
    - daily_new_users: 每日新增用户趋势
    - days           : 统计天数
    """
    def _user_stats(s):
        total_users = s.query(func.count(User.id)).filter(User.enable_flag == True).scalar() or 0

        type_rows = s.query(User.user_type, func.count(User.id)).filter(
            User.enable_flag == True
        ).group_by(User.user_type).all()
        user_type_dist = {row[0]: row[1] for row in type_rows}

        status_rows = s.query(User.status, func.count(User.id)).filter(
            User.enable_flag == True
        ).group_by(User.status).all()
        status_dist = {row[0]: row[1] for row in status_rows}

        daily_new = []
        for i in range(days - 1, -1, -1):
            day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = s.query(func.count(User.id)).filter(
                User.create_time >= day_start,
                User.create_time < day_end,
                User.enable_flag == True,
            ).scalar() or 0
            daily_new.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

        return {
            "total_users": total_users,
            "user_type_dist": user_type_dist,
            "status_dist": status_dist,
            "daily_new_users": daily_new,
            "days": days,
        }

    return await db.run_sync(_user_stats)


@router.get("/strategies")
async def get_strategy_stats(
    db: AsyncSession = Depends(get_db),
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    策略统计数据

    返回策略运行状态、信号产生等统计数据。

    返回：
    - total_strategies  : 总策略数
    - state_dist        : 策略状态分布
    - signal_by_strategy: 各策略信号数量
    - signal_type_dist  : 信号类型分布
    """
    # 策略状态分布（从编排器获取）
    state_dist = {}
    strategy_list = []
    try:
        for sid in (orch.strategy_engine.list_strategies() if orch else []):
            s = orch.strategy_engine.get_strategy(sid)
            if s:
                state = s.state.value
                state_dist[state] = state_dist.get(state, 0) + 1
                strategy_list.append({
                    "strategy_id": sid,
                    "name": s.name,
                    "state": state,
                    "symbols": s.symbols,
                })
    except Exception:
        pass

    def _strategy_db_stats(s):
        signal_rows = s.query(
            SignalTradeRecord.signal_id,
            Signal.name.label("signal_name"),
            func.count(SignalTradeRecord.id).label("signal_count"),
        ).join(
            Signal, SignalTradeRecord.signal_id == Signal.id,
        ).group_by(
            SignalTradeRecord.signal_id,
            Signal.name,
        ).order_by(func.count(SignalTradeRecord.id).desc()).limit(20).all()

        signal_by_strategy = [
            {
                "signal_id": row.signal_id,
                "signal_name": row.signal_name or str(row.signal_id),
                "signal_count": row.signal_count,
            }
            for row in signal_rows
        ]

        type_rows = s.query(
            SignalTradeRecord.action,
            func.count(SignalTradeRecord.id),
        ).group_by(SignalTradeRecord.action).all()
        signal_type_dist = {row[0]: row[1] for row in type_rows}

        return signal_by_strategy, signal_type_dist

    signal_by_strategy, signal_type_dist = await db.run_sync(_strategy_db_stats)

    return {
        "total_strategies": len(strategy_list),
        "state_dist": state_dist,
        "strategies": strategy_list,
        "signal_by_strategy": signal_by_strategy,
        "signal_type_dist": signal_type_dist,
    }


@router.get("/trading")
async def get_trading_stats(
    db: AsyncSession = Depends(get_db),
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    交易统计数据

    返回订单、成交、持仓等交易统计数据。

    返回：
    - active_orders  : 活跃订单数
    - total_positions: 持仓数量
    - total_equity   : 总资产
    - account_info   : 账户信息
    """
    active_orders = 0
    total_positions = 0
    total_equity = 0.0
    account_info = {}

    try:
        if orch:
            op = orch.order_processor
            if op:
                from quant_trading_system.core.enums import OrderStatus
                active_orders = sum(
                    1 for o in op.orders
                    if o.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED)
                )
                total_positions = len(op.position_manager.positions)

            acc = orch.account_manager.account
            if acc:
                total_equity = float(acc.total_balance)
                account_info = {
                    "total_balance": float(acc.total_balance),
                    "available_balance": float(acc.available_balance),
                    "margin_balance": float(acc.margin_balance),
                }
    except Exception:
        pass

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    signals_executed_today = await db.run_sync(
        lambda s: s.query(func.count(SignalTradeRecord.id)).filter(
            SignalTradeRecord.traded_at >= today_start,
        ).scalar() or 0
    )

    return {
        "active_orders": active_orders,
        "total_positions": total_positions,
        "total_equity": total_equity,
        "account_info": account_info,
        "signals_executed_today": signals_executed_today,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/market")
async def get_market_stats(
    db: AsyncSession = Depends(get_db),
    orch=Depends(_get_optional_orchestrator),
) -> dict[str, Any]:
    """
    行情数据统计

    返回行情订阅、K线数据量等统计数据。

    返回：
    - subscribed_symbols: 已订阅交易对数量
    - subscriptions_count: 订阅配置数量
    - running_subscriptions: 运行中订阅数量
    - kline_records_total: K线记录总数
    - market_service_stats: 行情服务统计
    """
    def _market_db_stats(s):
        total_subs = s.query(func.count(Subscription.id)).scalar() or 0
        running_subs = s.query(func.count(Subscription.id)).filter(
            Subscription.status == "running"
        ).scalar() or 0
        return total_subs, running_subs

    total_subs, running_subs = await db.run_sync(_market_db_stats)

    # K线记录总数（异步查询）
    kline_total = 0
    try:
        from quant_trading_system.core.database import get_async_database
        tsdb = get_async_database()
        if tsdb.is_connected:
            rows = await tsdb.execute_raw("SELECT COUNT(*) FROM kline_data;")
            kline_total = rows[0][0] if rows else 0
    except Exception:
        pass

    # 行情服务统计
    market_stats = {}
    subscribed_symbols = 0
    try:
        market_stats = orch.market_service.stats if orch else {}
        # 统计已订阅交易对数量
        for collector in (orch.market_service._collectors.values() if orch else []):
            subscribed_symbols += len(collector.subscriptions)
    except Exception:
        pass

    return {
        "subscribed_symbols": subscribed_symbols,
        "subscriptions_count": total_subs,
        "running_subscriptions": running_subs,
        "kline_records_total": kline_total,
        "market_service_stats": market_stats,
        "timestamp": datetime.utcnow().isoformat(),
    }
