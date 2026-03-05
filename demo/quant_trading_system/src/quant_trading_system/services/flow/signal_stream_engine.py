"""
信号监听引擎（SignalStreamEngine）
===================================

按 signal 表驱动，负责：
1. 系统启动时扫描 signal 表中 status='running' 且 auto_start_stream=True 的信号
2. 对 signal_source='subscribe' 类型的信号，建立 WebSocket 订阅监听目标账户
3. 注册 3 个订阅器到事件总线：
   - SignalRecordSubscriber: 信号记录本地落库
   - SignalWsSubscriber: WebSocket 推送到前端
   - FollowTradeSubscriber: 跟单交易下单
4. 支持运行时动态添加/移除信号监听

引擎层职责：编排调度，不包含业务逻辑。
业务逻辑由 services/flow/ 下的订阅器实现。

生命周期：
    engine = SignalStreamEngine()
    await engine.start()   # 扫描DB + 启动所有信号流 + 注册订阅器
    ...
    await engine.stop()    # 停止所有信号流 + 注销订阅器
"""

import asyncio
import structlog
from typing import Any, Optional

from sqlalchemy import select

from quant_trading_system.models.signal import Signal
from quant_trading_system.core.database import get_db
from quant_trading_system.services.flow.signal_record_subscriber import (
    SignalRecordSubscriber,
    ORDER_EVENTS,
    SNAPSHOT_EVENTS,
)
from quant_trading_system.services.flow.signal_ws_subscriber import (
    SignalWsSubscriber,
    WS_PUSH_EVENTS,
)
from quant_trading_system.services.flow.follow_trade_subscriber import (
    FollowTradeSubscriber,
    FOLLOW_ORDER_EVENTS,
)
from quant_trading_system.services.flow.flow_signal_stream import FlowSignalStream
from quant_trading_system.engines.signal_event_bus import SignalEventBus

logger = structlog.get_logger(__name__)


class SignalStreamEngine:
    """
    信号监听引擎

    核心职责：
    1. 系统启动时扫描 signal 表，对运行中的 subscribe 类型信号建立 WebSocket 监听
    2. 收到订单事件后发布到事件总线
    3. 注册 3 个内置订阅器：
       - SignalRecordSubscriber: 信号记录落库（订单事件 + 快照事件）
       - SignalWsSubscriber: WebSocket 推送到前端（订单事件 + 快照事件）
       - FollowTradeSubscriber: 跟单交易下单（订单事件）
    4. 支持运行时动态添加/移除信号监听
    """

    def __init__(self):
        # 引擎内部创建自己的事件总线实例（不使用全局单例）
        self._event_bus = SignalEventBus()
        self._streams: dict[int, FlowSignalStream] = {}
        self._lock = asyncio.Lock()
        self._running = False

        # 内置订阅器
        self._record_subscriber = SignalRecordSubscriber()
        self._ws_subscriber = SignalWsSubscriber()
        self._follow_subscriber = FollowTradeSubscriber()

    async def start(self) -> None:
        """
        启动信号监听引擎

        1. 启动跟单交易订阅器（加载跟单配置）
        2. 注册所有订阅器到事件总线
        3. 扫描 signal 表，启动所有运行中的 subscribe 类型信号的 WebSocket 监听
        """
        if self._running:
            logger.warning("信号监听引擎已在运行中")
            return

        self._running = True

        # 1. 启动跟单交易订阅器（需要先扫描DB加载跟单配置）
        await self._follow_subscriber.start()
        logger.info(
            f"  ✅ 跟单交易订阅器已启动（活跃跟单: {self._follow_subscriber.total_follows}）"
        )

        # 2. 注册订阅器到事件总线
        # 订阅器1：信号记录落库（全局监听所有订单事件 + 快照事件）
        self._event_bus.subscribe_many(
            list(ORDER_EVENTS | SNAPSHOT_EVENTS),
            self._record_subscriber,
        )
        logger.info("  ✅ 信号记录订阅器已注册（订单事件 + 快照事件）")

        # 订阅器2：WebSocket 推送到前端（全局监听所有订单事件 + 快照事件）
        self._event_bus.subscribe_many(
            list(WS_PUSH_EVENTS),
            self._ws_subscriber,
        )
        logger.info("  ✅ WebSocket 推送订阅器已注册（订单事件 + 快照事件）")

        # 订阅器3：跟单交易下单（全局监听所有实时订单事件）
        self._event_bus.subscribe_many(
            list(FOLLOW_ORDER_EVENTS),
            self._follow_subscriber,
        )
        logger.info("  ✅ 跟单交易订阅器已注册到事件总线（订单事件）")

        # 3. 从数据库扫描运行中的信号
        await self._scan_and_start_signals()

        logger.info(
            f"✅ 信号监听引擎已启动，活跃信号流: {len(self._streams)}"
        )

    async def stop(self) -> None:
        """停止信号监听引擎，关闭所有信号流和订阅器"""
        if not self._running:
            return

        self._running = False

        # 1. 停止所有信号流
        async with self._lock:
            for signal_id, stream in list(self._streams.items()):
                try:
                    await stream.stop()
                except Exception as e:
                    logger.error(f"停止信号流失败: signal_id={signal_id}, error={e}")
            self._streams.clear()

        # 2. 注销所有订阅器
        self._event_bus.unsubscribe_all(self._record_subscriber)
        self._event_bus.unsubscribe_all(self._ws_subscriber)
        self._event_bus.unsubscribe_all(self._follow_subscriber)

        # 3. 停止跟单交易订阅器（清理客户端资源）
        await self._follow_subscriber.stop()

        logger.info("✅ 信号监听引擎已停止")

    async def _scan_and_start_signals(self) -> None:
        """扫描 signal 表，启动运行中且需要自动监听的信号"""
        try:
            # 使用异步 Session 查询 ORM 模型
            async for db in get_db():
                try:
                    result = await db.execute(
                        select(Signal).where(
                            Signal.status == "running",
                            Signal.signal_source == "subscribe",
                            Signal.auto_start_stream == True,
                            Signal.enable_flag == True,
                        )
                    )
                    signals = result.scalars().all()

                    logger.info(f"扫描到 {len(signals)} 个需要自动启动的信号源")

                    for signal in signals:
                        if not signal.target_api_key or not signal.target_api_secret:
                            logger.warning(
                                f"信号源缺少 API 授权信息，跳过: "
                                f"signal_id={signal.id}, name={signal.name}"
                            )
                            continue

                        watch_symbols = signal.watch_symbols if signal.watch_symbols else None

                        try:
                            await self.add_signal_stream(
                                signal_id=signal.id,
                                signal_name=signal.name,
                                target_api_key=signal.target_api_key,
                                target_api_secret=signal.target_api_secret,
                                account_type=signal.account_type or "spot",
                                exchange=signal.exchange or "binance",
                                testnet=signal.testnet or False,
                                watch_symbols=watch_symbols,
                            )
                        except Exception as e:
                            logger.error(
                                f"启动信号流失败: signal_id={signal.id}, "
                                f"name={signal.name}, error={e}"
                            )
                except Exception as e:
                    logger.error(f"查询信号表失败: {e}", exc_info=True)
                break  # 只需要一个 session
        except Exception as e:
            logger.error(f"扫描信号表失败: {e}", exc_info=True)

    # ── 动态管理信号流 ────────────────────────────────────────

    async def add_signal_stream(
        self,
        signal_id: int,
        signal_name: str,
        target_api_key: str,
        target_api_secret: str,
        account_type: str = "spot",
        exchange: str = "binance",
        testnet: bool = False,
        watch_symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """添加并启动一个信号流"""
        async with self._lock:
            if signal_id in self._streams:
                return {
                    "status": "already_running",
                    "signal_id": signal_id,
                    "message": "该信号流已在运行中",
                }

            stream = FlowSignalStream(
                signal_id=signal_id,
                signal_name=signal_name,
                target_api_key=target_api_key,
                target_api_secret=target_api_secret,
                account_type=account_type,
                exchange=exchange,
                testnet=testnet,
                watch_symbols=watch_symbols,
                event_bus=self._event_bus,
            )

            await stream.start()
            self._streams[signal_id] = stream

            return {
                "status": "started",
                "signal_id": signal_id,
                "signal_name": signal_name,
                "account_type": account_type,
            }

    async def remove_signal_stream(self, signal_id: int) -> dict[str, Any]:
        """停止并移除一个信号流"""
        async with self._lock:
            stream = self._streams.pop(signal_id, None)
            if not stream:
                return {
                    "status": "not_found",
                    "signal_id": signal_id,
                    "message": "未找到运行中的信号流",
                }

            await stream.stop()
            self._event_bus.unsubscribe_signal(signal_id)

            return {
                "status": "stopped",
                "signal_id": signal_id,
            }

    # ── 跟单动态管理（代理到 FollowTradeSubscriber） ──────────

    async def add_follow(self, follow_order_id: int) -> bool:
        """动态添加跟单（代理到跟单订阅器）"""
        return await self._follow_subscriber.add_follow(follow_order_id)

    async def remove_follow(self, follow_order_id: int) -> bool:
        """动态移除跟单（代理到跟单订阅器）"""
        return await self._follow_subscriber.remove_follow(follow_order_id)

    async def update_follow_config(
        self,
        follow_order_id: int,
        follow_ratio: float | None = None,
        follow_amount: float | None = None,
        stop_loss: float | None = None,
    ) -> bool:
        """动态更新跟单配置（代理到跟单订阅器）"""
        return await self._follow_subscriber.update_follow_config(
            follow_order_id, follow_ratio, follow_amount, stop_loss,
        )

    # ── 状态查询 ──────────────────────────────────────────────

    def get_stream_status(self, signal_id: int) -> Optional[dict[str, Any]]:
        """获取指定信号流的状态"""
        stream = self._streams.get(signal_id)
        if not stream:
            return None
        return stream.get_status()

    def get_all_stream_statuses(self) -> dict[int, dict[str, Any]]:
        """获取所有信号流的状态"""
        return {sid: s.get_status() for sid, s in self._streams.items()}

    @property
    def active_count(self) -> int:
        """当前活跃信号流数量"""
        return len(self._streams)

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    @property
    def event_bus(self) -> SignalEventBus:
        """获取事件总线引用"""
        return self._event_bus

    @property
    def follow_subscriber(self) -> FollowTradeSubscriber:
        """获取跟单交易订阅器引用（供外部查询状态）"""
        return self._follow_subscriber

    @property
    def stats(self) -> dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "running": self._running,
            "active_streams": self.active_count,
            "streams": {
                sid: s.get_status() for sid, s in self._streams.items()
            },
            "follow_subscriber": self._follow_subscriber.stats,
            "event_bus": self._event_bus.stats,
        }
