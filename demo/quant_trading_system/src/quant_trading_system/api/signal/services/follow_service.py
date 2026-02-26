"""
跟单服务层
==========

提供跟单详情、收益对比、仓位分布、事件日志、配置管理等核心业务逻辑。
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from quant_trading_system.models.database import (
    SignalFollowOrder,
    SignalFollowPosition,
    SignalFollowTrade,
    SignalFollowEvent,
    SignalRecord,
    User,
)
from quant_trading_system.core.snowflake import generate_snowflake_id

logger = logging.getLogger(__name__)


class FollowService:
    """跟单核心业务服务"""

    # ── 跟单详情 ──────────────────────────────────────────────

    @staticmethod
    def get_follow_detail(db: Session, follow_id: int, user_id: int) -> Optional[dict[str, Any]]:
        """
        获取跟单完整详情

        Args:
            db: 数据库会话
            follow_id: 跟单ID
            user_id: 当前用户ID

        Returns:
            跟单详情字典
        """
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            return None
        if order.user_id != user_id:
            raise PermissionError("无权访问此跟单记录")

        follow_days = 0
        if order.start_time:
            follow_days = (datetime.utcnow() - order.start_time).days

        # 获取持仓列表
        positions = db.query(SignalFollowPosition).filter(
            SignalFollowPosition.follow_order_id == follow_id,
            SignalFollowPosition.status == "open",
        ).all()

        position_list = []
        for p in positions:
            position_list.append({
                "id": str(p.id),
                "symbol": p.symbol,
                "side": p.side,
                "amount": float(p.amount) if p.amount else 0,
                "entryPrice": float(p.entry_price) if p.entry_price else 0,
                "currentPrice": float(p.current_price) if p.current_price else 0,
                "pnl": float(p.pnl) if p.pnl else 0,
                "pnlPercent": float(p.pnl_percent) if p.pnl_percent else 0,
            })

        # 获取最近交易点位
        recent_trades = db.query(SignalFollowTrade).filter(
            SignalFollowTrade.follow_order_id == follow_id,
        ).order_by(SignalFollowTrade.trade_time.desc()).limit(20).all()

        trading_points = []
        for t in recent_trades:
            trading_points.append({
                "id": str(t.id),
                "type": t.side,
                "symbol": t.symbol,
                "price": float(t.price) if t.price else 0,
                "amount": float(t.amount) if t.amount else 0,
                "time": t.trade_time.isoformat() if t.trade_time else None,
            })

        return {
            "id": str(order.id),
            "signalId": order.strategy_id,
            "signalName": order.signal_name,
            "exchange": order.exchange,
            "status": order.status,
            "totalReturn": float(order.total_return) if order.total_return else 0,
            "todayReturn": float(order.today_return) if order.today_return else 0,
            "followAmount": float(order.follow_amount) if order.follow_amount else 0,
            "currentValue": float(order.current_value) if order.current_value else 0,
            "maxDrawdown": float(order.max_drawdown) if order.max_drawdown else 0,
            "currentDrawdown": float(order.current_drawdown) if order.current_drawdown else 0,
            "followDays": follow_days,
            "winRate": float(order.win_rate) if order.win_rate else 0,
            "followRatio": float(order.follow_ratio) if order.follow_ratio else 1.0,
            "stopLoss": float(order.stop_loss) if order.stop_loss else 0,
            "startTime": order.start_time.isoformat() if order.start_time else None,
            "riskLevel": order.risk_level or "low",
            "currentPrice": 0,  # 需要从行情获取
            "priceChange24h": 0,
            "volume24h": "0",
            "totalTrades": order.total_trades or 0,
            "winTrades": order.win_trades or 0,
            "lossTrades": order.loss_trades or 0,
            "avgWin": float(order.avg_win) if order.avg_win else 0,
            "avgLoss": float(order.avg_loss) if order.avg_loss else 0,
            "profitFactor": float(order.profit_factor) if order.profit_factor else 0,
            "returnCurve": order.return_curve or [],
            "returnCurveLabels": order.return_curve_labels or [],
            "positions": position_list,
            "tradingPoints": trading_points,
        }

    # ── 收益对比 ──────────────────────────────────────────────

    @staticmethod
    def get_comparison(db: Session, follow_id: int, user_id: int) -> dict[str, Any]:
        """
        获取跟单收益与信号源收益的对比数据

        Args:
            db: 数据库会话
            follow_id: 跟单ID
            user_id: 当前用户ID

        Returns:
            收益对比数据
        """
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权访问此跟单记录")

        # 跟单收益曲线
        follow_curve = order.return_curve or []
        labels = order.return_curve_labels or []

        # 信号源收益曲线（从信号记录中计算）
        signal_curve = FollowService._compute_signal_curve(db, order.strategy_id, order.start_time)

        # 确保两条曲线长度一致
        max_len = max(len(follow_curve), len(signal_curve))
        while len(follow_curve) < max_len:
            follow_curve.append(follow_curve[-1] if follow_curve else 0)
        while len(signal_curve) < max_len:
            signal_curve.append(signal_curve[-1] if signal_curve else 0)
        while len(labels) < max_len:
            labels.append("")

        follow_final = follow_curve[-1] if follow_curve else 0
        signal_final = signal_curve[-1] if signal_curve else 0
        return_diff = round(follow_final - signal_final, 2)

        # 计算平均滑点
        avg_slippage = FollowService._compute_avg_slippage(db, follow_id)

        # 计算跟单复制率
        copy_rate = FollowService._compute_copy_rate(db, follow_id, order.strategy_id)

        return {
            "labels": labels,
            "followCurve": follow_curve,
            "signalCurve": signal_curve,
            "statistics": {
                "returnDiff": return_diff,
                "avgSlippage": avg_slippage,
                "copyRate": copy_rate,
                "followFinalReturn": follow_final,
                "signalFinalReturn": signal_final,
            },
        }

    @staticmethod
    def _compute_signal_curve(db: Session, strategy_id: str, start_time: Optional[datetime]) -> list[float]:
        """计算信号源收益曲线"""
        query = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == strategy_id,
            SignalRecord.status == "executed",
        )
        if start_time:
            query = query.filter(SignalRecord.executed_at >= start_time)

        signals = query.order_by(SignalRecord.executed_at.asc()).all()
        curve = []
        cum_return = 0.0
        for s in signals:
            if s.executed_price and s.price and float(s.price) > 0:
                ret = (float(s.executed_price) - float(s.price)) / float(s.price) * 100
                cum_return += ret
            curve.append(round(cum_return, 2))
        return curve

    @staticmethod
    def _compute_avg_slippage(db: Session, follow_id: int) -> float:
        """计算平均滑点"""
        result = db.query(
            func.avg(SignalFollowTrade.slippage)
        ).filter(
            SignalFollowTrade.follow_order_id == follow_id,
        ).scalar()
        return round(float(result or 0), 2)

    @staticmethod
    def _compute_copy_rate(db: Session, follow_id: int, strategy_id: str) -> float:
        """计算跟单复制率"""
        total_signals = db.query(func.count(SignalRecord.id)).filter(
            SignalRecord.strategy_id == strategy_id,
            SignalRecord.status == "executed",
        ).scalar() or 0

        if total_signals == 0:
            return 100.0

        copied = db.query(func.count(SignalFollowTrade.id)).filter(
            SignalFollowTrade.follow_order_id == follow_id,
        ).scalar() or 0

        return round(min(copied / total_signals * 100, 100), 1)

    # ── 交易记录 ──────────────────────────────────────────────

    @staticmethod
    def get_trades(
        db: Session,
        follow_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        side: Optional[str] = None,
    ) -> dict[str, Any]:
        """获取跟单交易记录"""
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权访问此跟单记录")

        query = db.query(SignalFollowTrade).filter(
            SignalFollowTrade.follow_order_id == follow_id,
        )
        if side:
            query = query.filter(SignalFollowTrade.side == side.lower())

        total = query.count()
        trades = query.order_by(
            SignalFollowTrade.trade_time.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        records = []
        for t in trades:
            records.append({
                "id": str(t.id),
                "side": t.side,
                "symbol": t.symbol,
                "price": float(t.price) if t.price else 0,
                "amount": float(t.amount) if t.amount else 0,
                "total": float(t.total) if t.total else 0,
                "pnl": float(t.pnl) if t.pnl else None,
                "time": t.trade_time.isoformat() if t.trade_time else None,
                "signalTime": getattr(t, 'signal_time', None),
                "slippage": float(getattr(t, 'slippage', 0) or 0),
            })

        return {
            "total": total,
            "page": page,
            "records": records,
        }

    # ── 事件日志 ──────────────────────────────────────────────

    @staticmethod
    def get_events(
        db: Session,
        follow_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """获取跟单事件日志"""
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权访问此跟单记录")

        query = db.query(SignalFollowEvent).filter(
            SignalFollowEvent.follow_order_id == follow_id,
        )
        if event_type:
            query = query.filter(SignalFollowEvent.event_type == event_type)

        total = query.count()
        events = query.order_by(
            SignalFollowEvent.event_time.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        records = []
        for e in events:
            records.append({
                "id": str(e.id),
                "type": e.event_type,
                "typeLabel": e.type_label,
                "message": e.message,
                "time": e.event_time.isoformat() if e.event_time else None,
"metadata": e.event_meta or {},
            })

        return {
            "total": total,
            "records": records,
        }

    # ── 仓位分布 ──────────────────────────────────────────────

    @staticmethod
    def get_positions(db: Session, follow_id: int, user_id: int) -> dict[str, Any]:
        """获取跟单仓位分布"""
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权访问此跟单记录")

        current_value = float(order.current_value) if order.current_value else 0

        positions = db.query(SignalFollowPosition).filter(
            SignalFollowPosition.follow_order_id == follow_id,
            SignalFollowPosition.status == "open",
        ).all()

        # 计算持仓分布
        position_list = []
        used_value = 0.0
        distribution = []

        for p in positions:
            value = float(p.amount or 0) * float(p.entry_price or 0)
            used_value += value
            pct = (value / current_value * 100) if current_value > 0 else 0
            position_list.append({
                "symbol": p.symbol,
                "value": round(value, 2),
                "percentage": round(pct, 1),
            })
            distribution.append({
                "name": p.symbol,
                "value": round(value, 2),
            })

        free_value = current_value - used_value
        capital_usage = (used_value / current_value * 100) if current_value > 0 else 0

        if free_value > 0:
            distribution.append({
                "name": "可用资金",
                "value": round(free_value, 2),
            })

        return {
            "totalValue": round(current_value, 2),
            "usedValue": round(used_value, 2),
            "freeValue": round(free_value, 2),
            "capitalUsageRate": round(capital_usage, 1),
            "positions": position_list,
            "distribution": distribution,
        }

    # ── 更新跟单配置 ─────────────────────────────────────────

    @staticmethod
    def update_config(
        db: Session,
        follow_id: int,
        user_id: int,
        follow_ratio: Optional[float] = None,
        stop_loss: Optional[float] = None,
        follow_amount: Optional[float] = None,
    ) -> dict[str, Any]:
        """更新跟单配置"""
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权操作此跟单记录")
        if order.status == "stopped":
            raise ValueError("跟单已停止，无法修改配置")

        now = datetime.utcnow()
        changes = {}

        if follow_ratio is not None:
            order.follow_ratio = follow_ratio
            changes["followRatio"] = follow_ratio
        if stop_loss is not None:
            order.stop_loss = stop_loss / 100.0  # 百分比转小数
            changes["stopLoss"] = stop_loss
        if follow_amount is not None:
            if follow_amount <= 0:
                raise ValueError("跟单资金必须大于0")
            order.follow_amount = follow_amount
            changes["followAmount"] = follow_amount

        order.update_time = now
        db.commit()
        db.refresh(order)

        # 记录配置更新事件
        event = SignalFollowEvent(
            id=generate_snowflake_id(),
            follow_order_id=follow_id,
            user_id=user_id,
            event_type="system",
            type_label="系统",
            message=f"跟单参数更新: {changes}",
            event_meta={"action": "config_update", "config": changes},
            event_time=now,
            create_time=now,
        )
        db.add(event)
        db.commit()

        return {
            "followRatio": float(order.follow_ratio) if order.follow_ratio else 1.0,
            "stopLoss": float(order.stop_loss) * 100 if order.stop_loss else 0,
            "followAmount": float(order.follow_amount) if order.follow_amount else 0,
            "updatedAt": now.isoformat(),
        }

    # ── 停止跟单 ──────────────────────────────────────────────

    @staticmethod
    def stop_follow(
        db: Session,
        follow_id: int,
        user_id: int,
        close_positions: bool = True,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        停止跟单

        Args:
            db: 数据库会话
            follow_id: 跟单ID
            user_id: 用户ID
            close_positions: 是否平仓
            reason: 停止原因
        """
        order = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.id == follow_id,
            SignalFollowOrder.enable_flag == True,
        ).first()
        if not order:
            raise ValueError("跟单记录不存在")
        if order.user_id != user_id:
            raise PermissionError("无权操作此跟单记录")
        if order.status == "stopped":
            raise ValueError("跟单已停止")

        now = datetime.utcnow()
        order.status = "stopped"
        order.stop_time = now
        order.update_time = now

        closed_count = 0
        if close_positions:
            result = db.query(SignalFollowPosition).filter(
                SignalFollowPosition.follow_order_id == follow_id,
                SignalFollowPosition.status == "open",
            ).update({
                "status": "closed",
                "close_time": now,
                "update_time": now,
            })
            closed_count = result

        # 记录停止事件
        event = SignalFollowEvent(
            id=generate_snowflake_id(),
            follow_order_id=follow_id,
            user_id=user_id,
            event_type="system",
            type_label="系统",
            message=f"跟单已停止，原因: {reason or '手动停止'}，平仓 {closed_count} 个持仓",
            event_meta={
                "action": "stop",
                "close_positions": close_positions,
                "closed_count": closed_count,
                "reason": reason,
            },
            event_time=now,
            create_time=now,
        )
        db.add(event)

        # 更新信号源订阅数
        signals = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == order.strategy_id,
        ).all()
        for s in signals:
            if s.subscriber_count and s.subscriber_count > 0:
                s.subscriber_count -= 1

        db.commit()
        db.refresh(order)

        return {
            "followId": str(order.id),
            "status": "stopped",
            "finalReturn": float(order.total_return) if order.total_return else 0,
            "closedPositions": closed_count,
            "stoppedAt": now.isoformat(),
        }

    # ── 记录事件 ──────────────────────────────────────────────

    @staticmethod
    def log_event(
        db: Session,
        follow_order_id: int,
        user_id: int,
        event_type: str,
        message: str,
        event_meta: Optional[dict] = None,
    ) -> None:
        """记录跟单事件日志"""
        type_labels = {
            "trade": "交易",
            "success": "成交",
            "risk": "风控",
            "error": "异常",
            "system": "系统",
        }

        event = SignalFollowEvent(
            id=generate_snowflake_id(),
            follow_order_id=follow_order_id,
            user_id=user_id,
            event_type=event_type,
            type_label=type_labels.get(event_type, "其他"),
            message=message,
            event_meta=event_meta,
            event_time=datetime.utcnow(),
            create_time=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
