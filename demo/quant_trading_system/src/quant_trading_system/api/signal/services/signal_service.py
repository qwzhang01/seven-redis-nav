"""
信号服务层
==========

提供信号详情、月度收益、回撤分析、评价管理等核心业务逻辑。
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, case, extract, desc, and_
from sqlalchemy.orm import Session

from quant_trading_system.models.signal import (
    SignalProvider,
    SignalReview,
    SignalReviewLike,
    SignalSubscription,
    Signal,
    SignalRiskParameters,
    SignalPerformanceMetrics,
    SignalNotificationSettings,
    SignalPosition,
    SignalTradeRecord,
    SignalReturnCurve,
    SignalMonthlyReturn,
)
from quant_trading_system.models.follow import SignalFollowOrder
from quant_trading_system.models.user import User
from quant_trading_system.core.snowflake import generate_snowflake_id

logger = logging.getLogger(__name__)


class SignalService:
    """信号核心业务服务"""

    # ── 信号广场列表（基于signal主表） ─────────────────────────

    @staticmethod
    def list_signals(
        db: Session,
        platform: Optional[str] = None,
        signal_type: Optional[str] = None,
        min_days: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "return_desc",
        page: int = 1,
        page_size: int = 9,
    ) -> dict[str, Any]:
        """
        获取信号广场信号列表（基于signal主表），支持筛选、排序、分页。

        优先查询signal主表。
        """
        return SignalService._list_signals_from_signal_table(
            db, platform, signal_type, min_days, search, sort_by, page, page_size,
        )

    @staticmethod
    def _list_signals_from_signal_table(
        db: Session,
        platform: Optional[str] = None,
        signal_type: Optional[str] = None,
        min_days: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "return_desc",
        page: int = 1,
        page_size: int = 9,
    ) -> dict[str, Any]:
        """从signal主表查询信号广场列表"""
        query = db.query(Signal).filter(Signal.enable_flag == True)

        if platform:
            query = query.filter(Signal.platform == platform)
        if signal_type:
            query = query.filter(Signal.type == signal_type)
        if min_days and min_days > 0:
            query = query.filter(Signal.run_days >= min_days)
        if search:
            query = query.filter(Signal.name.ilike(f"%{search}%"))

        # 排序
        if sort_by == "return_asc":
            query = query.order_by(Signal.cumulative_return.asc())
        elif sort_by == "drawdown_asc":
            query = query.order_by(Signal.max_drawdown.asc())
        elif sort_by == "followers":
            query = query.order_by(Signal.followers_count.desc())
        else:  # return_desc（默认）
            query = query.order_by(Signal.cumulative_return.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        signal_list = []
        for s in items:
            # 获取近30天收益曲线用于缩略图
            curve_data = db.query(SignalReturnCurve).filter(
                SignalReturnCurve.signal_id == s.id,
            ).order_by(SignalReturnCurve.time.desc()).limit(30).all()
            curve_data.reverse()

            signal_list.append({
                "id": s.id,
                "name": s.name,
                "platform": s.platform,
                "type": s.type,
                "status": s.status,
                "cumulativeReturn": float(s.cumulative_return) if s.cumulative_return else 0,
                "maxDrawdown": float(s.max_drawdown) if s.max_drawdown else 0,
                "runDays": s.run_days or 0,
                "followersCount": s.followers_count or 0,
                "returnCurve": [float(c.return_value) for c in curve_data],
                "returnCurveLabels": [c.time.strftime("%Y-%m-%d") for c in curve_data],
            })

        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "items": signal_list,
        }

    @staticmethod
    def get_platforms(db: Session) -> list[str]:
        """获取所有平台列表（用于筛选项）"""
        platforms = db.query(Signal.platform).filter(
            Signal.enable_flag == True,
        ).distinct().all()
        return [p[0] for p in platforms if p[0]]

    # ── 信号详情（基于signal主表） ────────────────────────────

    @staticmethod
    def get_signal_detail_v2(db: Session, signal_id: int, user_id: Optional[int] = None) -> Optional[dict[str, Any]]:
        """
        获取信号详情（优先从signal主表查询）

        从signal主表及关联表获取完整数据。
        """
        signal = db.query(Signal).filter(
            Signal.id == signal_id, Signal.enable_flag == True,
        ).first()

        if signal:
            return SignalService._build_signal_detail_from_signal(db, signal, user_id)

        return None

    @staticmethod
    def _build_signal_detail_from_signal(
        db: Session, signal: "Signal", user_id: Optional[int] = None
    ) -> dict[str, Any]:
        """从signal主表构建完整的信号详情"""
        result = {
            "id": signal.id,
            "name": signal.name,
            "description": signal.description or "",
            "platform": signal.platform,
            "type": signal.type,
            "status": signal.status,
            "exchange": signal.exchange or signal.platform,
            "tradingPair": signal.trading_pair or "",
            "timeframe": signal.timeframe or "4H",
            "signalFrequency": signal.signal_frequency or "medium",
            "followers": signal.followers_count or 0,
            "cumulativeReturn": float(signal.cumulative_return) if signal.cumulative_return else 0,
            "maxDrawdown": float(signal.max_drawdown) if signal.max_drawdown else 0,
            "runDays": signal.run_days or 0,
            "createdAt": signal.created_at.isoformat() if signal.created_at else None,
            "updatedAt": signal.updated_at.isoformat() if signal.updated_at else None,
        }

        # 风险参数（从关联表获取）
        rp = signal.risk_parameters
        if rp:
            result["riskParameters"] = {
                "maxPositionSize": float(rp.max_position_size) if rp.max_position_size else 0,
                "stopLossPercentage": float(rp.stop_loss_percentage) if rp.stop_loss_percentage else 0,
                "takeProfitPercentage": float(rp.take_profit_percentage) if rp.take_profit_percentage else 0,
                "riskRewardRatio": float(rp.risk_reward_ratio) if rp.risk_reward_ratio else 0,
                "volatilityFilter": rp.volatility_filter or False,
            }
        else:
            result["riskParameters"] = {
                "maxPositionSize": 30, "stopLossPercentage": 5,
                "takeProfitPercentage": 15, "riskRewardRatio": 3,
                "volatilityFilter": True,
            }

        # 绩效指标（从关联表获取）
        pm = signal.performance_metrics
        if pm:
            result["performanceMetrics"] = {
                "sharpeRatio": float(pm.sharpe_ratio) if pm.sharpe_ratio else 0,
                "winRate": float(pm.win_rate) if pm.win_rate else 0,
                "profitFactor": float(pm.profit_factor) if pm.profit_factor else 0,
                "averageHoldingPeriod": float(pm.average_holding_period) if pm.average_holding_period else 0,
                "maxConsecutiveLosses": pm.max_consecutive_losses or 0,
            }
        else:
            result["performanceMetrics"] = {
                "sharpeRatio": 0, "winRate": 0, "profitFactor": 0,
                "averageHoldingPeriod": 0, "maxConsecutiveLosses": 0,
            }

        # 通知设置（从关联表获取）
        ns = signal.notification_settings
        if ns:
            result["notificationSettings"] = {
                "emailAlerts": ns.email_alerts,
                "pushNotifications": ns.push_notifications,
                "telegramBot": ns.telegram_bot,
                "discordWebhook": ns.discord_webhook,
                "alertThreshold": float(ns.alert_threshold) if ns.alert_threshold else 5,
            }
        else:
            result["notificationSettings"] = {
                "emailAlerts": True, "pushNotifications": True,
                "telegramBot": False, "discordWebhook": False,
                "alertThreshold": 5,
            }

        # 当前持仓
        positions = signal.positions or []
        result["positions"] = [
            {
                "symbol": p.symbol,
                "side": p.side,
                "amount": float(p.amount) if p.amount else 0,
                "entryPrice": float(p.entry_price) if p.entry_price else 0,
                "currentPrice": float(p.current_price) if p.current_price else 0,
                "pnlPercent": float(p.pnl_percent) if p.pnl_percent else 0,
            }
            for p in positions
        ]

        # 收益曲线
        curve_data = db.query(SignalReturnCurve).filter(
            SignalReturnCurve.signal_id == signal.id,
        ).order_by(SignalReturnCurve.time.asc()).all()
        result["returnCurve"] = [float(c.return_value) for c in curve_data]
        result["returnCurveLabels"] = [c.time.strftime("%Y-%m-%d") for c in curve_data]

        # 提供者信息
        provider = signal.provider
        if provider:
            result["provider"] = {
                "id": str(provider.id),
                "name": provider.name,
                "avatar": provider.avatar or "",
                "verified": provider.verified,
                "bio": provider.bio or "",
                "totalSignals": provider.total_signals,
                "avgReturn": float(provider.avg_return) if provider.avg_return else 0,
                "totalFollowers": provider.total_followers,
                "rating": float(provider.rating) if provider.rating else 0,
                "joinDate": provider.create_time.strftime("%Y-%m-%d") if provider.create_time else "",
                "experience": provider.experience or "",
                "badges": provider.badges or [],
            }

        return result

    # ── 信号收益曲线（基于signal_return_curve时序表） ──────────

    @staticmethod
    def get_signal_return_curve(
        db: Session, signal_id: int, period: str = "all"
    ) -> dict[str, Any]:
        """
        获取信号收益曲线和回撤曲线（优先从时序表获取）

        Args:
            period: 时间范围 7d/30d/90d/180d/all
        """
        # 确定时间过滤
        cutoff = None
        period_days = {"7d": 7, "30d": 30, "90d": 90, "180d": 180}
        if period in period_days:
            cutoff = datetime.utcnow() - timedelta(days=period_days[period])

        query = db.query(SignalReturnCurve).filter(
            SignalReturnCurve.signal_id == signal_id,
        )
        if cutoff:
            query = query.filter(SignalReturnCurve.time >= cutoff)

        curve_data = query.order_by(SignalReturnCurve.time.asc()).all()

        if curve_data:
            return {
                "returnCurve": [float(c.return_value) for c in curve_data],
                "drawdownCurve": [float(c.drawdown) if c.drawdown else 0 for c in curve_data],
                "labels": [c.time.strftime("%Y-%m-%d") for c in curve_data],
            }

        return {"returnCurve": [], "drawdownCurve": [], "labels": []}

    # ── 信号月度收益（基于signal_monthly_return表） ────────────

    @staticmethod
    def get_signal_monthly_returns(
        db: Session, signal_id: int, months: int = 12
    ) -> dict[str, Any]:
        """获取信号月度收益分布（优先从月度收益表获取）"""
        cutoff = datetime.utcnow() - timedelta(days=months * 31)

        records = db.query(SignalMonthlyReturn).filter(
            SignalMonthlyReturn.signal_id == signal_id,
            SignalMonthlyReturn.month >= cutoff,
        ).order_by(SignalMonthlyReturn.month.asc()).all()

        if records:
            month_list = [
                {"month": r.month.strftime("%Y-%m"), "return": round(float(r.return_value), 2)}
                for r in records
            ]
            returns = [m["return"] for m in month_list]
            profit_months = sum(1 for r in returns if r > 0)
            loss_months = sum(1 for r in returns if r < 0)

            return {
                "months": month_list,
                "statistics": {
                    "profitMonths": profit_months,
                    "lossMonths": loss_months,
                    "bestMonth": max(returns) if returns else 0,
                    "worstMonth": min(returns) if returns else 0,
                    "avgMonthlyReturn": round(sum(returns) / len(returns), 2) if returns else 0,
                },
            }

        return {"months": [], "statistics": {}}

    # ── 信号回撤分析（基于signal_return_curve时序表） ──────────

    @staticmethod
    def get_signal_drawdown(db: Session, signal_id: int) -> dict[str, Any]:
        """获取信号回撤分析数据（优先从时序表获取）"""
        curve_data = db.query(SignalReturnCurve).filter(
            SignalReturnCurve.signal_id == signal_id,
        ).order_by(SignalReturnCurve.time.asc()).all()

        if curve_data:
            values = [float(c.return_value) for c in curve_data]
            labels = [c.time.strftime("%Y-%m-%d") for c in curve_data]
            drawdown_from_db = [float(c.drawdown) if c.drawdown else None for c in curve_data]

            # 如果数据库中已有drawdown数据，直接使用
            if any(d is not None for d in drawdown_from_db):
                dd_curve = [d or 0 for d in drawdown_from_db]
                max_dd = min(dd_curve) if dd_curve else 0
                max_dd_idx = dd_curve.index(max_dd) if max_dd != 0 else 0
                current_dd = dd_curve[-1] if dd_curve else 0
                avg_dd = sum(dd_curve) / len(dd_curve) if dd_curve else 0

                return {
                    "drawdownCurve": dd_curve,
                    "labels": labels,
                    "statistics": {
                        "currentDrawdown": round(current_dd, 2),
                        "maxDrawdown": round(max_dd, 2),
                        "avgDrawdown": round(avg_dd, 2),
                        "maxDrawdownDate": labels[max_dd_idx] if max_dd_idx < len(labels) else "",
                        "maxDrawdownDuration": 0,
                    },
                }

            # 从收益曲线计算回撤
            drawdown_curve = []
            peak = values[0] if values else 0
            max_dd = 0.0
            max_dd_idx = 0
            dd_sum = 0.0

            for i, v in enumerate(values):
                if v > peak:
                    peak = v
                dd = v - peak
                drawdown_curve.append(round(dd, 2))
                dd_sum += dd
                if dd < max_dd:
                    max_dd = dd
                    max_dd_idx = i

            current_dd = drawdown_curve[-1] if drawdown_curve else 0
            avg_dd = dd_sum / len(drawdown_curve) if drawdown_curve else 0

            return {
                "drawdownCurve": drawdown_curve,
                "labels": labels,
                "statistics": {
                    "currentDrawdown": round(current_dd, 2),
                    "maxDrawdown": round(max_dd, 2),
                    "avgDrawdown": round(avg_dd, 2),
                    "maxDrawdownDate": labels[max_dd_idx] if max_dd_idx < len(labels) else "",
                    "maxDrawdownDuration": 0,
                },
            }

        return {"drawdownCurve": [], "labels": [], "statistics": {}}

    # ── 信号交易记录（基于signal_trade_record表） ─────────────

    @staticmethod
    def get_signal_trades(
        db: Session, signal_id: int, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """获取信号交易记录（优先从signal_trade_record表查询）"""
        total = db.query(func.count(SignalTradeRecord.id)).filter(
            SignalTradeRecord.signal_id == signal_id,
        ).scalar() or 0

        if total > 0:
            records = db.query(SignalTradeRecord).filter(
                SignalTradeRecord.signal_id == signal_id,
            ).order_by(
                SignalTradeRecord.traded_at.desc()
            ).offset((page - 1) * page_size).limit(page_size).all()

            items = []
            for r in records:
                items.append({
                    "id": str(r.id),
                    "action": r.action,
                    "symbol": r.symbol,
                    "price": float(r.price) if r.price else 0,
                    "amount": float(r.amount) if r.amount else 0,
                    "total": float(r.total) if r.total else 0,
                    "strength": r.strength or "medium",
                    "pnl": float(r.pnl) if r.pnl else None,
                    "tradedAt": r.traded_at.isoformat() if r.traded_at else None,
                })

            return {
                "total": total,
                "page": page,
                "pageSize": page_size,
                "records": items,
            }

        return {"total": 0, "page": page, "pageSize": page_size, "records": []}

    @staticmethod
    def get_signal_history(
        db: Session, signal_id: int, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """
        获取信号历史记录（交易信号历史列表，支持分页）

        基于 signal_trade_record 表查询指定信号的历史交易记录。
        """
        total = db.query(func.count(SignalTradeRecord.id)).filter(
            SignalTradeRecord.signal_id == signal_id,
        ).scalar() or 0

        records = db.query(SignalTradeRecord).filter(
            SignalTradeRecord.signal_id == signal_id,
            SignalTradeRecord.order_status == "FILLED",
        ).order_by(
            SignalTradeRecord.traded_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for r in records:
            items.append({
                "id": str(r.id),
                "action": r.action,
                "symbol": r.symbol,
                "price": float(r.price) if r.price else 0,
                "amount": float(r.amount) if r.amount else 0,
                "total": float(r.total) if r.total else 0,
                "strength": r.strength or "medium",
                "pnl": float(r.pnl) if r.pnl else None,
                "tradedAt": r.traded_at.isoformat() if r.traded_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }

    @staticmethod
    def _get_signal_positions(db: Session, strategy_id: str) -> list[dict]:
        """获取信号源当前持仓（来自关联跟单的持仓）"""
        from quant_trading_system.models.follow import SignalFollowPosition

        positions = db.query(SignalFollowPosition).join(
            SignalFollowOrder,
            SignalFollowPosition.follow_order_id == SignalFollowOrder.id,
        ).filter(
            SignalFollowOrder.strategy_id == strategy_id,
            SignalFollowPosition.status == "open",
        ).limit(20).all()

        result = []
        for p in positions:
            result.append({
                "symbol": p.symbol,
                "side": p.side,
                "amount": float(p.amount) if p.amount else 0,
                "entryPrice": float(p.entry_price) if p.entry_price else 0,
                "currentPrice": float(p.current_price) if p.current_price else 0,
                "pnlPercent": float(p.pnl_percent) if p.pnl_percent else 0,
            })
        return result



    # ── 信号提供者 ────────────────────────────────────────────

    @staticmethod
    def get_signal_provider(db: Session, signal_id: int) -> Optional[dict[str, Any]]:
        """获取信号提供者信息"""
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            return None

        provider = None
        if signal.provider_id:
            provider = db.query(SignalProvider).filter(
                SignalProvider.id == signal.provider_id,
                SignalProvider.enable_flag == True,
            ).first()

        if provider:
            return {
                "id": str(provider.id),
                "name": provider.name,
                "avatar": provider.avatar or "",
                "verified": provider.verified,
                "bio": provider.bio or "",
                "totalSignals": provider.total_signals,
                "avgReturn": float(provider.avg_return) if provider.avg_return else 0,
                "totalFollowers": provider.total_followers,
                "rating": float(provider.rating) if provider.rating else 0,
                "joinDate": provider.create_time.strftime("%Y-%m-%d") if provider.create_time else "",
                "experience": provider.experience or "",
                "badges": provider.badges or [],
            }

        # 如果没有provider记录，则使用信号源信息生成默认值
        return {
            "id": f"auto_{signal.strategy_id}",
            "name": signal.name or "System",
            "avatar": "",
            "verified": False,
            "bio": f"信号 {signal.name or signal.strategy_id} 的自动生成提供者信息",
            "totalSignals": db.query(func.count(Signal.id)).filter(
                Signal.provider_id == signal.provider_id
            ).scalar() or 0,
            "avgReturn": float(signal.cumulative_return) if signal.cumulative_return else 0,
            "totalFollowers": signal.followers_count or 0,
            "rating": 0,
            "joinDate": signal.created_at.strftime("%Y-%m-%d") if signal.created_at else "",
            "experience": "",
            "badges": [],
        }



    # ── 用户评价 ──────────────────────────────────────────────

    @staticmethod
    def get_reviews(
        db: Session,
        signal_id: int,
        page: int = 1,
        page_size: int = 10,
        sort: str = "latest",
        current_user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取用户评价列表"""
        query = db.query(SignalReview).filter(
            SignalReview.signal_id == signal_id,
            SignalReview.status == "active",
        )

        # 排序
        if sort == "highest":
            query = query.order_by(SignalReview.rating.desc(), SignalReview.create_time.desc())
        elif sort == "lowest":
            query = query.order_by(SignalReview.rating.asc(), SignalReview.create_time.desc())
        elif sort == "most_liked":
            query = query.order_by(SignalReview.likes.desc(), SignalReview.create_time.desc())
        else:
            query = query.order_by(SignalReview.create_time.desc())

        total = query.count()
        reviews = query.offset((page - 1) * page_size).limit(page_size).all()

        # 计算评分分布
        rating_dist = {}
        for i in range(1, 6):
            count = db.query(func.count(SignalReview.id)).filter(
                SignalReview.signal_id == signal_id,
                SignalReview.status == "active",
                SignalReview.rating == i,
            ).scalar() or 0
            rating_dist[str(i)] = count

        # 计算平均评分
        avg_rating = db.query(func.avg(SignalReview.rating)).filter(
            SignalReview.signal_id == signal_id,
            SignalReview.status == "active",
        ).scalar() or 0

        # 构建评价列表
        review_list = []
        for r in reviews:
            user = db.query(User).filter(User.id == r.user_id).first()
            is_liked = False
            if current_user_id:
                like = db.query(SignalReviewLike).filter(
                    SignalReviewLike.review_id == r.id,
                    SignalReviewLike.user_id == current_user_id,
                ).first()
                is_liked = like is not None

            review_list.append({
                "id": str(r.id),
                "user": user.nickname if user else "匿名",
                "userId": str(r.user_id),
                "avatar": user.avatar_url if user else "",
                "date": r.create_time.strftime("%Y-%m-%d") if r.create_time else "",
                "rating": r.rating,
                "content": r.content,
                "likes": r.likes or 0,
                "isLiked": is_liked,
            })

        return {
            "total": total,
            "averageRating": round(float(avg_rating), 1),
            "ratingDistribution": rating_dist,
            "reviews": review_list,
        }

    @staticmethod
    def submit_review(
        db: Session, signal_id: int, user_id: int, rating: int, content: str
    ) -> dict[str, Any]:
        """提交用户评价"""
        # 检查信号是否存在（从signal主表校验）
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            raise ValueError("信号不存在")

        # 检查是否已评价
        existing = db.query(SignalReview).filter(
            SignalReview.signal_id == signal_id,
            SignalReview.user_id == user_id,
            SignalReview.status == "active",
        ).first()
        if existing:
            raise ValueError("已评价过该信号")

        # 校验内容长度
        if len(content) < 10 or len(content) > 500:
            raise ValueError("评价内容需在10-500字之间")

        now = datetime.utcnow()
        review = SignalReview(
            id=generate_snowflake_id(),
            signal_id=signal_id,
            user_id=user_id,
            rating=rating,
            content=content,
            likes=0,
            status="active",
            create_time=now,
            update_time=now,
        )
        db.add(review)
        db.commit()
        db.refresh(review)

        return {
            "id": str(review.id),
            "rating": review.rating,
            "content": review.content,
            "date": review.create_time.strftime("%Y-%m-%d"),
        }

    @staticmethod
    def toggle_review_like(
        db: Session, signal_id: int, review_id: int, user_id: int
    ) -> dict[str, Any]:
        """评价点赞/取消点赞"""
        review = db.query(SignalReview).filter(
            SignalReview.id == review_id,
            SignalReview.signal_id == signal_id,
            SignalReview.status == "active",
        ).first()
        if not review:
            raise ValueError("评价不存在")

        existing = db.query(SignalReviewLike).filter(
            SignalReviewLike.review_id == review_id,
            SignalReviewLike.user_id == user_id,
        ).first()

        if existing:
            # 取消点赞
            db.delete(existing)
            review.likes = max((review.likes or 0) - 1, 0)
            liked = False
        else:
            # 点赞
            like = SignalReviewLike(
                id=generate_snowflake_id(),
                review_id=review_id,
                user_id=user_id,
                create_time=datetime.utcnow(),
            )
            db.add(like)
            review.likes = (review.likes or 0) + 1
            liked = True

        db.commit()

        return {
            "liked": liked,
            "totalLikes": review.likes,
        }

    # ── 创建跟单 ──────────────────────────────────────────────

    @staticmethod
    def create_follow(
        db: Session,
        signal_id: int,
        user_id: int,
        amount: float,
        ratio: float,
        stop_loss: float,
    ) -> dict[str, Any]:
        """
        创建跟单

        Args:
            signal_id: 信号ID
            user_id: 用户ID
            amount: 跟单资金 (USDT)
            ratio: 跟单比例
            stop_loss: 止损百分比 (1-50)

        Returns:
            创建的跟单信息
        """
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            raise ValueError("信号不存在")

        if signal.status == "paused" or signal.status == "stopped":
            raise ValueError("信号已停止，无法跟单")

        if amount < 100:
            raise ValueError("跟单资金低于最低限额(100 USDT)")

        if stop_loss < 1 or stop_loss > 50:
            raise ValueError("止损比例超出范围(1-50)")

        # 检查是否已跟单
        existing = db.query(SignalFollowOrder).filter(
            SignalFollowOrder.user_id == user_id,
            SignalFollowOrder.strategy_id == signal.strategy_id,
            SignalFollowOrder.status == "following",
            SignalFollowOrder.enable_flag == True,
        ).first()
        if existing:
            raise ValueError("已跟单该信号，不可重复跟单")

        now = datetime.utcnow()
        order = SignalFollowOrder(
            id=generate_snowflake_id(),
            user_id=user_id,
            strategy_id=signal.strategy_id,
            signal_name=signal.name or f"Signal #{signal.id}",
            exchange=signal.exchange or "binance",
            follow_amount=amount,
            current_value=amount,
            follow_ratio=ratio,
            stop_loss=stop_loss / 100.0,  # 百分比转小数
            total_return=0,
            max_drawdown=0,
            current_drawdown=0,
            today_return=0,
            win_rate=0,
            total_trades=0,
            win_trades=0,
            loss_trades=0,
            avg_win=0,
            avg_loss=0,
            profit_factor=0,
            risk_level="low",
            status="following",
            start_time=now,
            return_curve=[],
            return_curve_labels=[],
            create_by=str(user_id),
            create_time=now,
            update_time=now,
            enable_flag=True,
        )
        db.add(order)
        db.flush()  # 先将 order 刷入数据库，确保外键引用有效

        # 更新关注人数
        signal.followers_count = (signal.followers_count or 0) + 1
        signal.updated_at = now

        # 记录系统事件
        from quant_trading_system.models.follow import SignalFollowEvent
        event = SignalFollowEvent(
            id=generate_snowflake_id(),
            follow_order_id=order.id,
            user_id=user_id,
            event_type="system",
            type_label="系统",
            message=f"创建跟单，初始资金 {amount} USDT，跟单比例 {ratio}x",
            event_meta={"amount": amount, "ratio": ratio, "stop_loss": stop_loss},
            event_time=now,
            create_time=now,
        )
        db.add(event)

        db.commit()
        db.refresh(order)

        return {
            "followId": str(order.id),
            "signalId": str(signal_id),
            "amount": amount,
            "ratio": ratio,
            "stopLoss": stop_loss,
            "status": "following",
            "startTime": now.isoformat(),
        }


