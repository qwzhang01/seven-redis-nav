"""
信号监听引擎（SignalStreamEngine）
===================================

按 signal 表驱动，负责：
1. 系统启动时扫描 signal 表中 status='running' 且 auto_start_stream=True 的信号
2. 对 signal_source='subscribe' 类型的信号，建立 WebSocket 订阅监听目标账户
3. 支持运行时动态添加/移除信号监听

生命周期：
    engine = SignalStreamEngine()
    await engine.start()   # 扫描DB + 启动所有信号流 + 注册存储订阅器
    ...
    await engine.stop()    # 停止所有信号流
"""

import asyncio
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.models.signal import Signal
from quant_trading_system.services.database.database import get_db
from quant_trading_system.services.signal.signal_record_subscriber import (
    SignalRecordSubscriber,
    ORDER_EVENTS,
    SNAPSHOT_EVENTS,
)
from quant_trading_system.exchange_adapter.signal_stream import SignalStream
from quant_trading_system.engines.signal_event_bus import (
    SignalEventBus,
    signal_event_bus,
)

logger = logging.getLogger(__name__)


class SignalStreamEngine:
    """
    信号监听引擎

    核心职责：
    1. 系统启动时扫描 signal 表，对运行中的 subscribe 类型信号建立 WebSocket 监听
    2. 收到订单事件后发布到事件总线
    3. 注册 SignalRecordSubscriber 自动存储信号记录
    4. 支持运行时动态添加/移除信号监听
    5. 预留配置项：手动拉取历史仓位订单及账户信息变化

    生命周期：
        engine = SignalStreamEngine()
        await engine.start()   # 扫描DB + 启动所有信号流 + 注册存储订阅器
        ...
        await engine.stop()    # 停止所有信号流
    """

    def __init__(self, event_bus: SignalEventBus | None = None):
        self._event_bus = event_bus or signal_event_bus
        self._streams: dict[int, SignalStream] = {}
        self._lock = asyncio.Lock()
        self._running = False

        # 内置的信号记录存储订阅器
        self._record_subscriber = SignalRecordSubscriber()

    async def start(self) -> None:
        """
        启动信号监听引擎

        1. 注册信号记录存储订阅器到事件总线
        2. 扫描 signal 表，启动所有运行中的 subscribe 类型信号的 WebSocket 监听
        """
        if self._running:
            logger.warning("信号监听引擎已在运行中")
            return

        self._running = True

        # 注册内置订阅器：信号记录存储（全局监听所有订单事件 + 快照事件）
        self._event_bus.subscribe_many(
            list(ORDER_EVENTS | SNAPSHOT_EVENTS),
            self._record_subscriber,
        )
        logger.info("✅ 信号记录存储订阅器已注册（订单事件 + 快照事件）")

        # 从数据库扫描运行中的信号
        await self._scan_and_start_signals()

        logger.info(
            f"✅ 信号监听引擎已启动，活跃信号流: {len(self._streams)}"
        )

    async def stop(self) -> None:
        """停止信号监听引擎，关闭所有信号流"""
        if not self._running:
            return

        self._running = False

        async with self._lock:
            for signal_id, stream in list(self._streams.items()):
                try:
                    await stream.stop()
                except Exception as e:
                    logger.error(f"停止信号流失败: signal_id={signal_id}, error={e}")
            self._streams.clear()

        # 注销内置订阅器
        self._event_bus.unsubscribe_all(self._record_subscriber)

        logger.info("✅ 信号监听引擎已停止")

    async def _scan_and_start_signals(self) -> None:
        """扫描 signal 表，启动运行中且需要自动监听的信号"""
        try:
            db: Session = next(get_db())
            try:
                signals = db.query(Signal).filter(
                    Signal.status == "running",
                    Signal.signal_source == "subscribe",
                    Signal.auto_start_stream == True,
                    Signal.enable_flag == True,
                ).all()

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
            finally:
                db.close()
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
        """
        添加并启动一个信号流

        Args:
            signal_id: 信号源ID（signal 表的 id）
            signal_name: 信号名称
            target_api_key: 目标账户 API Key
            target_api_secret: 目标账户 API Secret
            account_type: 账户类型 spot/futures
            exchange: 交易所
            testnet: 是否测试网
            watch_symbols: 限定监听的交易对

        Returns:
            启动结果信息
        """
        async with self._lock:
            if signal_id in self._streams:
                return {
                    "status": "already_running",
                    "signal_id": signal_id,
                    "message": "该信号流已在运行中",
                }

            stream = SignalStream(
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
        """
        停止并移除一个信号流

        Args:
            signal_id: 信号源ID

        Returns:
            停止结果信息
        """
        async with self._lock:
            stream = self._streams.pop(signal_id, None)
            if not stream:
                return {
                    "status": "not_found",
                    "signal_id": signal_id,
                    "message": "未找到运行中的信号流",
                }

            await stream.stop()
            # 同时清理事件总线上该信号的订阅
            self._event_bus.unsubscribe_signal(signal_id)

            return {
                "status": "stopped",
                "signal_id": signal_id,
            }

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
    def stats(self) -> dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "running": self._running,
            "active_streams": self.active_count,
            "streams": {
                sid: s.get_status() for sid, s in self._streams.items()
            },
            "event_bus": self._event_bus.stats,
        }


# 全局单例
signal_stream_engine = SignalStreamEngine()
