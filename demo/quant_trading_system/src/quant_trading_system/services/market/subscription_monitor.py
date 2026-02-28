#!/usr/bin/env python3
"""
订阅状态监听器

监控数据库中的订阅状态变化，自动启动/停止数据收集器
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional
import structlog
from sqlalchemy.orm import Session

from quant_trading_system.models.database import Subscription
from quant_trading_system.services.database.database import get_db
from quant_trading_system.services.market.market_service import MarketService
from quant_trading_system.core.events import Event, EventType, EventEngine

logger = structlog.get_logger(__name__)


class SubscriptionMonitor:
    """订阅状态监听器"""

    def __init__(
        self,
        market_service: MarketService,
        event_engine: Optional[EventEngine] = None,
        check_interval: float = 5.0
    ) -> None:
        self.market_service = market_service
        self.event_engine = event_engine
        self.check_interval = check_interval

        # 当前活跃的订阅
        self.active_subscriptions: Dict[str, Subscription] = {}

        # 运行状态
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        logger.info("SubscriptionMonitor initialized", check_interval=check_interval)

    async def start(self) -> None:
        """启动监听器"""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("SubscriptionMonitor started")

    async def stop(self) -> None:
        """停止监听器"""
        if not self._running:
            return

        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # 停止所有活跃的订阅
        for sub_id in list(self.active_subscriptions.keys()):
            await self._stop_subscription(sub_id)

        logger.info("SubscriptionMonitor stopped")

    async def _monitor_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                await self._check_subscriptions()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitor loop", error=str(e))
                await asyncio.sleep(self.check_interval)

    async def _check_subscriptions(self) -> None:
        """检查所有订阅的状态变化"""
        try:
            # 正确使用get_db()生成器获取Session
            db_gen = get_db()
            session = next(db_gen)

            try:
                # 获取所有订阅
                subscriptions = session.query(Subscription).all()

                # 检查需要启动的订阅
                for subscription in subscriptions:
                    if subscription.status == "running" and subscription.id not in self.active_subscriptions:
                        await self._start_subscription(subscription, session)

                    elif subscription.status != "running" and subscription.id in self.active_subscriptions:
                        await self._stop_subscription(subscription.id)

                # 检查需要停止的订阅（已从数据库中删除）
                active_ids = set(self.active_subscriptions.keys())
                db_ids = {sub.id for sub in subscriptions}

                for sub_id in active_ids - db_ids:
                    await self._stop_subscription(sub_id)

            finally:
                # 确保Session被正确关闭
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        except Exception as e:
            logger.error("Error checking subscriptions", error=str(e))

    async def _start_subscription(self, subscription: Subscription, session: Session) -> None:
        """启动订阅的数据收集"""
        try:
            sub_id = subscription.id

            # 确保市场服务已启动
            if not self.market_service.is_running:
                await self.market_service.start()

            # 添加交易所数据源
            await self.market_service.add_exchange(
                exchange=subscription.exchange,
                market_type=subscription.market_type or "spot"
            )

            # 订阅行情数据
            symbols = subscription.symbols or []
            if symbols:
                await self.market_service.subscribe(
                    symbols=symbols,
                    exchange=subscription.exchange,
                    market_type=subscription.market_type or "spot"
                )

            # 记录活跃订阅
            self.active_subscriptions[sub_id] = subscription

            # 更新订阅状态
            subscription.last_sync_time = datetime.utcnow()
            session.commit()

            logger.info(
                "Subscription started",
                subscription_id=sub_id,
                name=subscription.name,
                exchange=subscription.exchange,
                symbols=symbols
            )

            # 发送事件
            if self.event_engine and hasattr(self.event_engine, '_running') and self.event_engine._running:
                await self.event_engine.put(Event(
                    type=EventType.STRATEGY_START,
                    data={
                        "subscription_id": sub_id,
                        "name": subscription.name,
                        "exchange": subscription.exchange,
                        "symbols": symbols
                    }
                ))
            elif self.event_engine:
                logger.warning("EventEngine not running, STRATEGY_START event dropped")

        except Exception as e:
            logger.error(
                "Failed to start subscription",
                subscription_id=subscription.id,
                error=str(e)
            )

    async def _stop_subscription(self, subscription_id: str) -> None:
        """停止订阅的数据收集"""
        try:
            if subscription_id not in self.active_subscriptions:
                return

            subscription = self.active_subscriptions[subscription_id]

            # 取消订阅
            symbols = subscription.symbols or []
            if symbols:
                await self.market_service.unsubscribe(
                    symbols=symbols,
                    exchange=subscription.exchange,
                    market_type=subscription.market_type or "spot"
                )

            # 移除活跃订阅
            del self.active_subscriptions[subscription_id]

            logger.info(
                "Subscription stopped",
                subscription_id=subscription_id,
                name=subscription.name
            )

            # 发送事件
            if self.event_engine and hasattr(self.event_engine, '_running') and self.event_engine._running:
                await self.event_engine.put(Event(
                    type=EventType.STRATEGY_STOP,
                    data={
                        "subscription_id": subscription_id,
                        "name": subscription.name
                    }
                ))
            elif self.event_engine:
                logger.warning("EventEngine not running, STRATEGY_STOP event dropped")

        except Exception as e:
            logger.error(
                "Failed to stop subscription",
                subscription_id=subscription_id,
                error=str(e)
            )

    @property
    def is_running(self) -> bool:
        """检查监听器是否在运行"""
        return self._running

    @property
    def stats(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            "running": self._running,
            "active_subscriptions": len(self.active_subscriptions),
            "subscriptions": list(self.active_subscriptions.keys())
        }


# 全局订阅监听器实例
_subscription_monitor: Optional[SubscriptionMonitor] = None


def get_subscription_monitor() -> SubscriptionMonitor:
    """获取订阅监听器实例（委托到 ServiceContainer 获取依赖）"""
    global _subscription_monitor
    if _subscription_monitor is None:
        from quant_trading_system.core.container import container

        _subscription_monitor = SubscriptionMonitor(
            market_service=container.market_service,
            event_engine=container.event_engine,
        )
    return _subscription_monitor


async def init_subscription_monitor() -> SubscriptionMonitor:
    """初始化订阅监听器"""
    monitor = get_subscription_monitor()
    await monitor.start()
    return monitor


async def close_subscription_monitor() -> None:
    """关闭订阅监听器"""
    global _subscription_monitor
    if _subscription_monitor:
        await _subscription_monitor.stop()
        _subscription_monitor = None
