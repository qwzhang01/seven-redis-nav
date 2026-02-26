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

from quant_trading_system.models.database import (
    SignalRecord,
    SignalProvider,
    SignalReview,
    SignalReviewLike,
    SignalSubscription,
    SignalFollowOrder,
    User,
)
from quant_trading_system.core.snowflake import generate_snowflake_id

logger = logging.getLogger(__name__)


class SignalService:
    """信号核心业务服务"""

    # ── 信号详情 ──────────────────────────────────────────────

    @staticmethod
    def get_signal_detail(db: Session, signal_id: int, user_id: Optional[int] = None) -> Optional[dict[str, Any]]:
        """
        获取信号完整详情，包括基本信息、风险参数、绩效指标、持仓等。

        Args:
            db: 数据库会话
            signal_id: 信号ID
            user_id: 当前用户ID（可选，用于判断是否已跟单）

        Returns:
            信号详情字典，不存在返回 None
        """
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            return None

        # 基本信息
        result = {
            "id": signal.id,
            "name": signal.strategy_name or f"Signal #{signal.id}",
            "description": signal.reason or "",
            "platform": signal.exchange or "Binance",
            "type": "live",
            "status": signal.status,
            "exchange": signal.exchange or "Binance",
            "tradingPair": signal.symbol,
            "timeframe": signal.timeframe or "4H",
            "signalFrequency": "medium",
            "followers": signal.subscriber_count or 0,
            "cumulativeReturn": 0.0,
            "maxDrawdown": 0.0,
            "runDays": 0,
            "returnCurve": [],
            "returnCurveLabels": [],
            "riskParameters": {
                "maxPositionSize": 30,
                "stopLossPercentage": 5,
                "takeProfitPercentage": 15,
                "riskRewardRatio": 3,
                "volatilityFilter": True,
            },
            "performanceMetrics": {
                "sharpeRatio": 0.0,
                "winRate": 0.0,
                "profitFactor": 0.0,
                "averageHoldingPeriod": 0.0,
                "maxConsecutiveLosses": 0,
            },
            "notificationSettings": {
                "emailAlerts": True,
                "pushNotifications": True,
                "telegramBot": False,
                "discordWebhook": False,
                "alertThreshold": 5,
            },
            "positions": [],
            "createdAt": signal.created_at.isoformat() if signal.created_at else None,
            "updatedAt": signal.updated_at.isoformat() if signal.updated_at else None,
        }

        # 计算运行天数
        if signal.created_at:
            result["runDays"] = (datetime.utcnow() - signal.created_at).days

        # 计算该信号源的历史统计（基于同策略的信号记录）
        stats = SignalService._compute_signal_stats(db, signal.strategy_id)
        result.update(stats)

        # 获取当前持仓（从跟单的position中聚合）
        result["positions"] = SignalService._get_signal_positions(db, signal.strategy_id)

        # 收益曲线数据
        curve_data = SignalService._generate_return_curve(db, signal.strategy_id, signal.created_at)
        result["returnCurve"] = curve_data["values"]
        result["returnCurveLabels"] = curve_data["labels"]

        return result

    @staticmethod
    def _compute_signal_stats(db: Session, strategy_id: str) -> dict[str, Any]:
        """计算信号源的统计数据"""
        signals = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == strategy_id,
            SignalRecord.status == "executed",
        ).all()

        if not signals:
            return {}

        total = len(signals)
        executed_with_profit = [s for s in signals if s.executed_price and s.price and float(s.executed_price) > float(s.price)]
        win_count = len(executed_with_profit)

        win_rate = (win_count / total * 100) if total > 0 else 0.0

        # 计算累计收益
        cum_return = 0.0
        for s in signals:
            if s.executed_price and s.price and float(s.price) > 0:
                ret = (float(s.executed_price) - float(s.price)) / float(s.price) * 100
                cum_return += ret

        return {
            "cumulativeReturn": round(cum_return, 2),
            "performanceMetrics": {
                "sharpeRatio": round(cum_return / max(abs(cum_return) * 0.3, 1), 2),
                "winRate": round(win_rate, 1),
                "profitFactor": round(win_count / max(total - win_count, 1), 2),
                "averageHoldingPeriod": 3.5,
                "maxConsecutiveLosses": 0,
            },
        }

    @staticmethod
    def _get_signal_positions(db: Session, strategy_id: str) -> list[dict]:
        """获取信号源当前持仓（来自关联跟单的持仓）"""
        from quant_trading_system.models.database import SignalFollowPosition

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

    @staticmethod
    def _generate_return_curve(db: Session, strategy_id: str, start_date: Optional[datetime] = None) -> dict:
        """生成收益曲线数据"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=180)

        signals = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == strategy_id,
            SignalRecord.status == "executed",
            SignalRecord.executed_at is not None,
        ).order_by(SignalRecord.executed_at.asc()).all()

        values = []
        labels = []
        cum_return = 0.0

        for s in signals:
            if s.executed_price and s.price and float(s.price) > 0:
                ret = (float(s.executed_price) - float(s.price)) / float(s.price) * 100
                cum_return += ret
                values.append(round(cum_return, 2))
                labels.append(s.executed_at.strftime("%Y-%m-%d") if s.executed_at else "")

        return {"values": values, "labels": labels}

    # ── 信号历史记录 ──────────────────────────────────────────

    @staticmethod
    def get_signal_history(
        db: Session, signal_id: int, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """获取信号历史交易记录"""
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            return {"total": 0, "page": page, "pageSize": page_size, "records": []}

        # 查询同策略的全部信号
        query = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == signal.strategy_id,
        ).order_by(SignalRecord.created_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for r in records:
            pnl = None
            status = "open"
            if r.executed_price and r.price:
                pnl = round(float(r.executed_price) - float(r.price), 2)
                status = "closed"

            items.append({
                "id": str(r.id),
                "action": r.signal_type,
                "symbol": r.symbol,
                "price": float(r.price) if r.price else 0,
                "amount": float(r.quantity) if r.quantity else 0,
                "time": r.created_at.isoformat() if r.created_at else None,
                "strength": getattr(r, 'signal_strength', None) or "medium",
                "pnl": pnl,
                "status": status,
            })

        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "records": items,
        }

    # ── 信号提供者 ────────────────────────────────────────────

    @staticmethod
    def get_signal_provider(db: Session, signal_id: int) -> Optional[dict[str, Any]]:
        """获取信号提供者信息"""
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            return None

        provider_id = getattr(signal, 'provider_id', None)
        provider = None
        if provider_id:
            provider = db.query(SignalProvider).filter(
                SignalProvider.id == provider_id,
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

        # 如果没有provider记录，则使用策略信息生成默认值
        return {
            "id": f"auto_{signal.strategy_id}",
            "name": signal.strategy_name or "System",
            "avatar": "",
            "verified": False,
            "bio": f"策略 {signal.strategy_name or signal.strategy_id} 的自动生成提供者信息",
            "totalSignals": db.query(func.count(SignalRecord.id)).filter(
                SignalRecord.strategy_id == signal.strategy_id
            ).scalar() or 0,
            "avgReturn": 0,
            "totalFollowers": signal.subscriber_count or 0,
            "rating": 0,
            "joinDate": signal.created_at.strftime("%Y-%m-%d") if signal.created_at else "",
            "experience": "",
            "badges": [],
        }

    # ── 月度收益分布 ──────────────────────────────────────────

    @staticmethod
    def get_monthly_returns(
        db: Session, signal_id: int, months: int = 12
    ) -> dict[str, Any]:
        """获取月度收益分布"""
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            return {"months": [], "statistics": {}}

        # 按月汇总已执行的信号收益
        cutoff = datetime.utcnow() - timedelta(days=months * 31)
        signals = db.query(SignalRecord).filter(
            SignalRecord.strategy_id == signal.strategy_id,
            SignalRecord.status == "executed",
            SignalRecord.executed_at >= cutoff,
        ).order_by(SignalRecord.executed_at.asc()).all()

        monthly_data: dict[str, float] = {}
        for s in signals:
            if s.executed_at and s.executed_price and s.price and float(s.price) > 0:
                month_key = s.executed_at.strftime("%Y-%m")
                ret = (float(s.executed_price) - float(s.price)) / float(s.price) * 100
                monthly_data[month_key] = monthly_data.get(month_key, 0) + ret

        month_list = [{"month": k, "return": round(v, 2)} for k, v in sorted(monthly_data.items())]
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

    # ── 回撤分析 ──────────────────────────────────────────────

    @staticmethod
    def get_drawdown_analysis(db: Session, signal_id: int) -> dict[str, Any]:
        """获取回撤分析数据"""
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            return {"drawdownCurve": [], "labels": [], "statistics": {}}

        # 获取收益曲线，计算回撤
        curve_data = SignalService._generate_return_curve(db, signal.strategy_id, signal.created_at)
        values = curve_data["values"]
        labels = curve_data["labels"]

        if not values:
            return {
                "drawdownCurve": [],
                "labels": [],
                "statistics": {
                    "currentDrawdown": 0,
                    "maxDrawdown": 0,
                    "avgDrawdown": 0,
                    "maxDrawdownDate": "",
                    "maxDrawdownDuration": 0,
                },
            }

        # 计算回撤曲线
        drawdown_curve = []
        peak = values[0]
        max_dd = 0.0
        max_dd_idx = 0
        dd_sum = 0.0

        for i, v in enumerate(values):
            if v > peak:
                peak = v
            dd = v - peak  # 回撤为负值
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
        # 检查信号是否存在
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
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
        signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
        if not signal:
            raise ValueError("信号不存在")

        if signal.status == "expired" or signal.status == "ignored":
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
            signal_name=signal.strategy_name or f"Signal #{signal.id}",
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

        # 更新订阅人数
        signal.subscriber_count = (signal.subscriber_count or 0) + 1
        signal.updated_at = now

        # 记录系统事件
        from quant_trading_system.models.database import SignalFollowEvent
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

    # ── 公开信号列表 ──────────────────────────────────────────

    @staticmethod
    def list_public_signals(
        db: Session,
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        strategy_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取公开信号列表（信号广场）"""
        query = db.query(SignalRecord).filter(SignalRecord.is_public == True)
        if symbol:
            query = query.filter(SignalRecord.symbol == symbol.upper())
        if signal_type:
            query = query.filter(SignalRecord.signal_type == signal_type.lower())
        if strategy_id:
            query = query.filter(SignalRecord.strategy_id == strategy_id)

        total = query.count()
        items = query.order_by(SignalRecord.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        signal_list = []
        for s in items:
            signal_list.append({
                "id": s.id,
                "strategy_id": s.strategy_id,
                "strategy_name": s.strategy_name,
                "symbol": s.symbol,
                "exchange": s.exchange,
                "signal_type": s.signal_type,
                "price": float(s.price) if s.price is not None else None,
                "quantity": float(s.quantity) if s.quantity is not None else None,
                "confidence": float(s.confidence) if s.confidence is not None else None,
                "timeframe": s.timeframe,
                "reason": s.reason,
                "indicators": s.indicators,
                "status": s.status,
                "is_public": s.is_public,
                "subscriber_count": s.subscriber_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })

        return {
            "items": signal_list,
            "total": total,
            "page": page,
            "pages": (total + page_size - 1) // page_size,
        }
