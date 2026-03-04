"""
信号监听引擎（SignalStreamEngine）
===================================

按 signal 表驱动，负责：
1. 系统启动时扫描 signal 表中 status='running' 且 auto_start_stream=True 的信号
2. 对 signal_source='subscribe' 类型的信号，建立 WebSocket 订阅监听目标账户
3. 收到仓位/订单事件后，解析为标准化 SignalEvent 并发布到事件总线
4. 支持运行时动态添加/移除信号监听

整体架构：
    SignalStreamEngine
        ├── BinanceUserStreamManager × N  （每个 subscribe 类型信号一个 WebSocket 连接）
        ├── SignalEventBus                （发布事件到事件总线）
        └── DB Session                    （扫描 signal 表 + 存储 signal_trade_record）

事件流：
    WebSocket (executionReport)
        → _on_order_event() 解析
        → SignalEventBus.publish(ORDER_FILLED)
            ├→ SignalRecordSubscriber  → 存储到 signal_trade_record
            └→ FollowEngine           → 触发跟单
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.database import Signal, SignalTradeRecord
from quant_trading_system.services.database.database import get_db
from quant_trading_system.services.exchange.binance_user_stream import (
    BinanceUserStreamManager,
)
from quant_trading_system.services.exchange.signal_event_bus import (
    OrderFilledData,
    SignalEvent,
    SignalEventBus,
    SignalEventType,
    SignalSubscriber,
    signal_event_bus,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 信号记录订阅器 — 将事件存储到 signal_trade_record 表
# ═══════════════════════════════════════════════════════════════


class SignalRecordSubscriber(SignalSubscriber):
    """
    信号记录存储订阅器

    监听 ORDER_FILLED 事件，将目标账户的成交记录
    存储到 signal_trade_record 表中。
    """

    @property
    def name(self) -> str:
        return "SignalRecordSubscriber"

    async def on_signal_event(self, event: SignalEvent) -> None:
        """将订单成交事件存储到 signal_trade_record"""
        if event.type != SignalEventType.ORDER_FILLED:
            return

        data = event.data
        try:
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)
                trade_time_ms = data.get("trade_time", 0)
                traded_at = (
                    datetime.fromtimestamp(trade_time_ms / 1000, tz=timezone.utc)
                    if trade_time_ms
                    else now
                )

                record = SignalTradeRecord(
                    id=generate_snowflake_id(),
                    signal_id=event.signal_id,
                    action=data.get("side", "").lower(),
                    symbol=data.get("symbol", ""),
                    price=Decimal(str(round(data.get("price", 0), 8))),
                    amount=Decimal(str(round(data.get("quantity", 0), 8))),
                    total=Decimal(str(round(data.get("quote_quantity", 0), 4))),
                    traded_at=traded_at,
                    created_at=now,
                )
                db.add(record)
                db.commit()

                logger.info(
                    f"📝 信号记录已存储: signal_id={event.signal_id}, "
                    f"{data.get('symbol')} {data.get('side')} "
                    f"qty={data.get('quantity'):.6f} price={data.get('price'):.4f}"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"存储信号记录失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")


# ═══════════════════════════════════════════════════════════════
# 单个信号流实例
# ═══════════════════════════════════════════════════════════════


class _SignalStream:
    """
    单个信号流实例

    负责监听一个 subscribe 类型信号源的目标账户 WebSocket。
    收到订单事件后解析并发布到事件总线。
    """

    def __init__(
        self,
        signal_id: int,
        signal_name: str,
        target_api_key: str,
        target_api_secret: str,
        account_type: str = "spot",
        exchange: str = "binance",
        testnet: bool = False,
        watch_symbols: list[str] | None = None,
        event_bus: SignalEventBus | None = None,
    ):
        self.signal_id = signal_id
        self.signal_name = signal_name
        self.account_type = account_type
        self.exchange = exchange
        self.watch_symbols = set(
            s.upper().replace("/", "") for s in (watch_symbols or [])
        )

        self._event_bus = event_bus or signal_event_bus

        # 目标账户 WebSocket 监听器
        self._stream_manager = BinanceUserStreamManager(
            api_key=target_api_key,
            api_secret=target_api_secret,
            account_type=account_type,
            testnet=testnet,
        )

        # 统计
        self._events_received = 0
        self._events_published = 0

    async def start(self) -> None:
        """启动信号流"""
        self._stream_manager.on_order_update = self._on_order_event
        self._stream_manager.on_account_update = self._on_account_event
        self._stream_manager.on_snapshot_ready = self._on_snapshot_ready
        await self._stream_manager.start()
        logger.info(f"信号流已启动: signal_id={self.signal_id}, name={self.signal_name}")

    async def stop(self) -> None:
        """停止信号流"""
        await self._stream_manager.stop()
        logger.info(f"信号流已停止: signal_id={self.signal_id}, name={self.signal_name}")

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        ws_status = self._stream_manager.get_status()
        return {
            "signal_id": self.signal_id,
            "signal_name": self.signal_name,
            "account_type": self.account_type,
            "exchange": self.exchange,
            "watch_symbols": list(self.watch_symbols) if self.watch_symbols else "all",
            "events_received": self._events_received,
            "events_published": self._events_published,
            "websocket": ws_status,
        }

    async def _on_order_event(self, event: dict[str, Any]) -> None:
        """
        处理订单事件回调

        解析 WebSocket 推送的订单事件，转换为标准化 SignalEvent 并发布。
        仅处理 FILLED 状态的订单。
        """
        event_type = event.get("e", "")
        self._events_received += 1

        # 解析事件
        if event_type == "executionReport":
            order_data = self._parse_spot_execution_report(event)
        elif event_type == "ORDER_TRADE_UPDATE":
            order_data = self._parse_futures_order_update(event)
        else:
            return

        if not order_data:
            return

        # 交易对过滤
        symbol = order_data.get("symbol", "")
        if self.watch_symbols and symbol not in self.watch_symbols:
            return

        # 根据订单状态决定事件类型
        status = order_data.get("status", "")
        if status == "FILLED":
            signal_event_type = SignalEventType.ORDER_FILLED
        elif status == "PARTIALLY_FILLED":
            signal_event_type = SignalEventType.ORDER_PARTIALLY_FILLED
        elif status == "NEW":
            signal_event_type = SignalEventType.ORDER_NEW
        elif status in ("CANCELED", "CANCELLED", "EXPIRED"):
            signal_event_type = SignalEventType.ORDER_CANCELED
        else:
            return

        # 只对 FILLED 记录详细日志
        if signal_event_type == SignalEventType.ORDER_FILLED:
            logger.info(
                f"📡 信号事件: signal_id={self.signal_id} {symbol} "
                f"{order_data.get('side')} qty={order_data.get('quantity'):.6f} "
                f"price={order_data.get('price'):.4f}"
            )

        # 发布到事件总线
        signal_event = SignalEvent(
            type=signal_event_type,
            signal_id=self.signal_id,
            data=order_data,
            exchange=self.exchange,
            symbol=symbol,
            raw_event=event,
        )
        await self._event_bus.publish(signal_event)
        self._events_published += 1

    async def _on_account_event(self, event: dict[str, Any]) -> None:
        """处理账户变化事件"""
        signal_event = SignalEvent(
            type=SignalEventType.ACCOUNT_UPDATE,
            signal_id=self.signal_id,
            data=event,
            exchange=self.exchange,
            raw_event=event,
        )
        await self._event_bus.publish(signal_event)

    async def _on_snapshot_ready(self, snapshot: dict[str, Any]) -> None:
        """
        处理启动时的历史快照回调

        将快照数据拆分为不同的事件类型发布到事件总线：
        - SNAPSHOT_OPEN_ORDERS: 当前挂单
        - SNAPSHOT_POSITIONS: 当前持仓
        - SNAPSHOT_ACCOUNT: 账户信息
        """
        logger.info(
            f"📸 收到初始快照: signal_id={self.signal_id}, "
            f"open_orders={len(snapshot.get('open_orders', []))}, "
            f"positions={len(snapshot.get('positions', []))}, "
            f"has_account={'yes' if snapshot.get('account') else 'no'}"
        )

        # 发布挂单快照
        if snapshot.get("open_orders"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_OPEN_ORDERS,
                signal_id=self.signal_id,
                data={"open_orders": snapshot["open_orders"]},
                exchange=self.exchange,
            ))

        # 发布持仓快照
        if snapshot.get("positions"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_POSITIONS,
                signal_id=self.signal_id,
                data={"positions": snapshot["positions"]},
                exchange=self.exchange,
            ))

        # 发布账户信息快照
        if snapshot.get("account"):
            await self._event_bus.publish(SignalEvent(
                type=SignalEventType.SNAPSHOT_ACCOUNT,
                signal_id=self.signal_id,
                data={"account": snapshot["account"]},
                exchange=self.exchange,
            ))

    async def fetch_snapshot(self) -> dict[str, Any]:
        """
        手动拉取当前快照（挂单、持仓、账户信息）

        可在运行时按需调用，拉取后同样通过事件总线发布。

        Returns:
            快照数据字典
        """
        snapshot = await self._stream_manager.fetch_initial_snapshot()
        return snapshot

    async def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """
        手动拉取当前挂单

        Args:
            symbol: 交易对（为 None 则查询所有）

        Returns:
            挂单列表
        """
        return await self._stream_manager.fetch_open_orders(symbol=symbol)

    async def fetch_positions(self) -> list[dict[str, Any]]:
        """
        手动拉取当前持仓

        Returns:
            持仓列表
        """
        return await self._stream_manager.fetch_positions()

    async def fetch_account_info(self) -> dict[str, Any]:
        """
        手动拉取账户信息

        Returns:
            账户信息字典
        """
        return await self._stream_manager.fetch_account_info()

    async def fetch_trade_history(self, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        手动拉取指定交易对的成交记录

        Args:
            symbol: 交易对
            limit: 返回数量上限

        Returns:
            成交记录列表
        """
        return await self._stream_manager.fetch_trade_history(symbol=symbol, limit=limit)

    def _parse_spot_execution_report(self, event: dict) -> Optional[dict[str, Any]]:
        """解析现货订单事件"""
        try:
            executed_qty = float(event.get("z", 0))
            cum_quote = float(event.get("Z", 0))
            avg_price = (cum_quote / executed_qty) if executed_qty > 0 else 0
            commission = float(event.get("n", 0))
            commission_asset = event.get("N", "")

            return {
                "symbol": event.get("s", ""),
                "side": event.get("S", ""),
                "order_type": event.get("o", "MARKET"),
                "status": event.get("X", ""),
                "quantity": executed_qty,
                "price": avg_price,
                "quote_quantity": cum_quote,
                "original_order_id": str(event.get("i", "")),
                "trade_time": event.get("T", 0),
                "commission": commission,
                "commission_asset": commission_asset,
            }
        except (ValueError, TypeError) as e:
            logger.error(f"解析现货订单事件失败: {e}")
            return None

    def _parse_futures_order_update(self, event: dict) -> Optional[dict[str, Any]]:
        """解析合约订单事件"""
        try:
            order = event.get("o", {})
            qty = float(order.get("z", 0))
            avg_price = float(order.get("ap", 0))

            return {
                "symbol": order.get("s", ""),
                "side": order.get("S", ""),
                "order_type": order.get("o", "MARKET"),
                "status": order.get("X", ""),
                "quantity": qty,
                "price": avg_price,
                "quote_quantity": qty * avg_price,
                "original_order_id": str(order.get("i", "")),
                "trade_time": order.get("T", 0),
                "commission": float(order.get("n", 0)),
                "commission_asset": order.get("N", ""),
            }
        except (ValueError, TypeError) as e:
            logger.error(f"解析合约订单事件失败: {e}")
            return None


# ═══════════════════════════════════════════════════════════════
# 信号监听引擎
# ═══════════════════════════════════════════════════════════════


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
        self._streams: dict[int, _SignalStream] = {}
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

        # 注册内置订阅器：信号记录存储（全局监听 ORDER_FILLED）
        self._event_bus.subscribe(
            SignalEventType.ORDER_FILLED,
            self._record_subscriber,
        )
        logger.info("✅ 信号记录存储订阅器已注册")

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

            stream = _SignalStream(
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

    # ── 手动查询历史数据 ────────────────────────────────────────

    def _get_stream(self, signal_id: int) -> _SignalStream:
        """
        获取指定信号流实例，不存在则抛异常

        Args:
            signal_id: 信号源ID

        Returns:
            _SignalStream 实例

        Raises:
            ValueError: 指定的信号流不存在
        """
        stream = self._streams.get(signal_id)
        if not stream:
            raise ValueError(f"未找到运行中的信号流: signal_id={signal_id}")
        return stream

    async def fetch_snapshot(self, signal_id: int) -> dict[str, Any]:
        """
        手动拉取指定信号流的完整快照（挂单、持仓、账户信息）

        拉取后会自动通过事件总线发布 SNAPSHOT_* 事件。

        Args:
            signal_id: 信号源ID

        Returns:
            快照数据字典: {"open_orders": [...], "positions": [...], "account": {...}}
        """
        stream = self._get_stream(signal_id)
        return await stream.fetch_snapshot()

    async def fetch_open_orders(self, signal_id: int, symbol: str | None = None) -> list[dict[str, Any]]:
        """
        手动拉取指定信号流的当前挂单

        Args:
            signal_id: 信号源ID
            symbol: 交易对（为 None 则查询所有）

        Returns:
            挂单列表
        """
        stream = self._get_stream(signal_id)
        return await stream.fetch_open_orders(symbol=symbol)

    async def fetch_positions(self, signal_id: int) -> list[dict[str, Any]]:
        """
        手动拉取指定信号流的当前持仓

        Args:
            signal_id: 信号源ID

        Returns:
            持仓列表
        """
        stream = self._get_stream(signal_id)
        return await stream.fetch_positions()

    async def fetch_account_info(self, signal_id: int) -> dict[str, Any]:
        """
        手动拉取指定信号流的账户信息

        Args:
            signal_id: 信号源ID

        Returns:
            账户信息字典
        """
        stream = self._get_stream(signal_id)
        return await stream.fetch_account_info()

    async def fetch_trade_history(self, signal_id: int, symbol: str, limit: int = 50) -> list[dict[str, Any]]:
        """
        手动拉取指定信号流的成交记录

        Args:
            signal_id: 信号源ID
            symbol: 交易对（必填）
            limit: 返回数量上限，默认50

        Returns:
            成交记录列表
        """
        stream = self._get_stream(signal_id)
        return await stream.fetch_trade_history(symbol=symbol, limit=limit)

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
