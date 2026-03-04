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

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from quant_trading_system.core.config import settings
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.signal import Signal, SignalPosition, SignalTradeRecord
from quant_trading_system.services.database.database import get_db
from quant_trading_system.services.exchange.binance_user_stream import (
    BinanceUserStreamManager,
)
from quant_trading_system.engines.signal_event_bus import (
    OrderFilledData,
    SignalEvent,
    SignalEventBus,
    SignalEventType,
    SignalSubscriber,
    signal_event_bus,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 信号记录订阅器 — 将事件存储到数据库
# ═══════════════════════════════════════════════════════════════


# 需要存储到 signal_trade_record 的订单事件类型集合
_ORDER_EVENTS = {
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
}

# 需要存储到 signal_trade_record 的快照事件类型集合
_SNAPSHOT_EVENTS = {
    SignalEventType.SNAPSHOT_OPEN_ORDERS,
    SignalEventType.SNAPSHOT_POSITIONS,
    SignalEventType.SNAPSHOT_ACCOUNT,
    SignalEventType.SNAPSHOT_TRADE_HISTORY,
}


class SignalRecordSubscriber(SignalSubscriber):
    """
    信号记录存储订阅器

    监听所有订单事件和快照事件，将数据存储到数据库：
    - 实时订单事件 (ORDER_NEW / ORDER_FILLED / ORDER_PARTIALLY_FILLED / ORDER_CANCELED)
      → 存储到 signal_trade_record 表
    - 快照-挂单 (SNAPSHOT_OPEN_ORDERS)
      → 存储到 signal_trade_record 表
    - 快照-持仓 (SNAPSHOT_POSITIONS)
      → 更新 signal_position 表（upsert）
    - 快照-账户 (SNAPSHOT_ACCOUNT)
      → 记录日志（可扩展）
    - 快照-成交历史 (SNAPSHOT_TRADE_HISTORY)
      → 存储到 signal_trade_record 表（去重）
    """

    @property
    def name(self) -> str:
        return "SignalRecordSubscriber"

    async def on_signal_event(self, event: SignalEvent) -> None:
        """根据事件类型分发到对应的存储处理方法"""
        if event.type in _ORDER_EVENTS:
            await self._save_order_event(event)
        elif event.type == SignalEventType.SNAPSHOT_OPEN_ORDERS:
            await self._save_snapshot_open_orders(event)
        elif event.type == SignalEventType.SNAPSHOT_POSITIONS:
            await self._save_snapshot_positions(event)
        elif event.type == SignalEventType.SNAPSHOT_ACCOUNT:
            await self._on_snapshot_account(event)
        elif event.type == SignalEventType.SNAPSHOT_TRADE_HISTORY:
            await self._save_snapshot_trade_history(event)

    # ── 实时订单事件存储 ──────────────────────────────────────

    async def _save_order_event(self, event: SignalEvent) -> None:
        """
        将实时订单事件存储到 signal_trade_record 表

        处理所有订单状态变化：NEW / PARTIALLY_FILLED / FILLED / CANCELED
        通过 signal_id + original_order_id + order_status 去重，避免重复写入。
        卖出（平仓）时：
        - 关联对应的开仓交易记录（open_trade_id）
        - 更新 signal_position 表（计算盈亏、标记关闭）
        """
        data = event.data
        original_order_id = data.get("original_order_id", "")
        order_status = data.get("status", "")

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

                action = data.get("side", "").lower()
                symbol = data.get("symbol", "")
                price = Decimal(str(round(data.get("price", 0), 8)))
                amount = Decimal(str(round(data.get("quantity", 0), 8)))

                # 如果是卖出（平仓）且订单已成交，提前查询持仓和开仓记录，计算 pnl
                open_trade_id = None
                trade_pnl = None
                trade_strength = None
                position = None
                is_close_trade = (action == "sell" and order_status == "FILLED")

                if is_close_trade:
                    # 查找对应的开仓交易记录
                    open_trade = db.query(SignalTradeRecord).filter(
                        SignalTradeRecord.signal_id == event.signal_id,
                        SignalTradeRecord.symbol == symbol,
                        SignalTradeRecord.action == "buy",
                        SignalTradeRecord.order_status == "FILLED",
                    ).order_by(SignalTradeRecord.traded_at.desc()).first()
                    if open_trade:
                        open_trade_id = open_trade.id

                    # 查询当前持仓，提前计算 pnl
                    position = db.query(SignalPosition).filter(
                        SignalPosition.signal_id == event.signal_id,
                        SignalPosition.symbol == symbol,
                        SignalPosition.status == "open",
                    ).first()
                    if position and position.entry_price and position.entry_price > 0:
                        if position.side == "long":
                            trade_pnl = round((price - position.entry_price) * amount, 4)
                            pnl_pct = abs((price - position.entry_price) / position.entry_price * 100)
                        else:
                            trade_pnl = round((position.entry_price - price) * amount, 4)
                            pnl_pct = abs((position.entry_price - price) / position.entry_price * 100)

                        # 根据盈亏比例判定信号强度
                        if pnl_pct >= 5:
                            trade_strength = "strong"
                        elif pnl_pct >= 2:
                            trade_strength = "medium"
                        else:
                            trade_strength = "weak"

                values = {
                    "id": generate_snowflake_id(),
                    "signal_id": event.signal_id,
                    "original_order_id": original_order_id or None,
                    "order_status": order_status or None,
                    "action": action,
                    "symbol": symbol,
                    "price": price,
                    "amount": amount,
                    "total": Decimal(str(round(data.get("quote_quantity", 0), 4))),
                    "strength": trade_strength,
                    "pnl": trade_pnl,
                    "open_trade_id": open_trade_id,
                    "traded_at": traded_at,
                    "created_at": now,
                }

                # 使用 PostgreSQL 原生 INSERT ... ON CONFLICT DO NOTHING
                # 依赖唯一索引 idx_signal_trade_dedup (signal_id, original_order_id, order_status)
                stmt = pg_insert(SignalTradeRecord).values(**values)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["signal_id", "original_order_id", "order_status"],
                )
                result = db.execute(stmt)

                # 如果是卖出（平仓）成交，更新 signal_position 表
                if is_close_trade and result.rowcount > 0 and position:
                    # 计算并写入持仓盈亏
                    if position.entry_price and position.entry_price > 0:
                        if position.side == "long":
                            pnl_percent = (price - position.entry_price) / position.entry_price * Decimal("100")
                        else:
                            pnl_percent = (position.entry_price - price) / position.entry_price * Decimal("100")
                        position.pnl = trade_pnl
                        position.pnl_percent = round(pnl_percent, 4)

                    # 更新持仓数量
                    remaining = position.amount - amount
                    if remaining <= 0:
                        # 全部平仓
                        position.amount = Decimal("0")
                        position.status = "closed"
                        position.closed_at = now
                    else:
                        # 部分平仓，仅减少数量
                        position.amount = remaining

                    position.current_price = price
                    position.updated_at = now
                    logger.info(
                        f"📉 持仓已更新: signal_id={event.signal_id}, symbol={symbol}, "
                        f"remaining={position.amount}, pnl={position.pnl}, status={position.status}"
                    )

                db.commit()

                # rowcount == 1 表示插入成功，== 0 表示冲突被跳过
                if result.rowcount == 0:
                    logger.debug(
                        f"⏭️ 跳过重复订单记录: signal_id={event.signal_id}, "
                        f"order_id={original_order_id}, status={order_status}"
                    )
                    return

                status_label = event.type.name.replace("ORDER_", "")
                logger.info(
                    f"📝 信号记录已存储 [{status_label}]: signal_id={event.signal_id}, "
                    f"order_id={original_order_id}, "
                    f"{data.get('symbol')} {data.get('side')} "
                    f"qty={data.get('quantity', 0):.6f} price={data.get('price', 0):.4f}"
                )

                # 通过 WebSocket 推送跟单信号到前端页面
                try:
                    from quant_trading_system.api.websocket.trading_ws import push_copy_trade_signal

                    await push_copy_trade_signal(
                        signal_id=event.signal_id,
                        event_type=event.type.name,
                        trade_data={
                            "signal_id": event.signal_id,
                            "original_order_id": original_order_id,
                            "order_status": order_status,
                            "symbol": data.get("symbol", ""),
                            "side": data.get("side", ""),
                            "price": float(data.get("price", 0)),
                            "quantity": float(data.get("quantity", 0)),
                            "quote_quantity": float(data.get("quote_quantity", 0)),
                            "trade_time": data.get("trade_time", 0),
                            "commission": float(data.get("commission", 0)),
                            "commission_asset": data.get("commission_asset", ""),
                        },
                    )
                except Exception as e:
                    # WebSocket 推送失败不应影响主逻辑
                    logger.debug(f"WebSocket 推送跟单信号失败: {e}")
            except Exception as e:
                db.rollback()
                logger.error(f"存储信号记录失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    # ── 快照事件存储 ──────────────────────────────────────────

    async def _save_snapshot_open_orders(self, event: SignalEvent) -> None:
        """
        将挂单快照存储到 signal_trade_record 表

        启动时拉取的当前挂单，记录到交易记录中。
        通过 signal_id + original_order_id + order_status 去重。
        """
        open_orders = event.data.get("open_orders", [])
        if not open_orders:
            return

        try:
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)
                saved_count = 0
                skipped_count = 0

                for order in open_orders:
                    # 解析挂单数据（兼容现货和合约的 API 返回格式）
                    symbol = order.get("symbol", "")
                    side = order.get("side", "").lower()
                    price = float(order.get("price", 0))
                    orig_qty = float(order.get("origQty", 0))
                    executed_qty = float(order.get("executedQty", 0))
                    order_time_ms = order.get("time", 0)
                    original_order_id = str(order.get("orderId", ""))

                    # 去重检查
                    if original_order_id:
                        existing = db.query(SignalTradeRecord.id).filter(
                            SignalTradeRecord.signal_id == event.signal_id,
                            SignalTradeRecord.original_order_id == original_order_id,
                            SignalTradeRecord.order_status == "SNAPSHOT",
                        ).first()
                        if existing:
                            skipped_count += 1
                            continue

                    traded_at = (
                        datetime.fromtimestamp(order_time_ms / 1000, tz=timezone.utc)
                        if order_time_ms
                        else now
                    )

                    record = SignalTradeRecord(
                        id=generate_snowflake_id(),
                        signal_id=event.signal_id,
                        original_order_id=original_order_id or None,
                        order_status="SNAPSHOT",
                        action=side,
                        symbol=symbol,
                        price=Decimal(str(round(price, 8))),
                        amount=Decimal(str(round(orig_qty, 8))),
                        total=Decimal(str(round(price * orig_qty, 4))),
                        traded_at=traded_at,
                        created_at=now,
                    )
                    db.add(record)
                    saved_count += 1

                db.commit()
                logger.info(
                    f"📝 挂单快照已存储: signal_id={event.signal_id}, "
                    f"保存 {saved_count} 条, 跳过重复 {skipped_count} 条"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"存储挂单快照失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    async def _save_snapshot_positions(self, event: SignalEvent) -> None:
        """
        将持仓快照更新到 signal_position 表（upsert 逻辑）

        - 现有持仓存在 → 更新 current_price、amount
        - 现有持仓不存在 → 新建
        - 数据库中有但快照中无 → 标记关闭（仓位已平）
        """
        positions = event.data.get("positions", [])
        signal_id = event.signal_id

        try:
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)

                # 获取数据库中当前打开的持仓（仅 open 状态）
                existing_positions = db.query(SignalPosition).filter(
                    SignalPosition.signal_id == signal_id,
                    SignalPosition.status == "open",
                ).all()
                existing_map: dict[str, SignalPosition] = {
                    pos.symbol: pos for pos in existing_positions
                }

                snapshot_symbols: set[str] = set()
                upsert_count = 0

                for pos in positions:
                    # 解析持仓数据（兼容现货和合约的 API 返回格式）
                    symbol = pos.get("symbol", "") or pos.get("asset", "")
                    if not symbol:
                        continue

                    snapshot_symbols.add(symbol)

                    # 现货：free + locked 作为数量
                    if "free" in pos:
                        amount = float(pos.get("free", 0)) + float(pos.get("locked", 0))
                        side = "long"
                        entry_price = 0  # 现货无入场价概念
                        current_price = 0
                    else:
                        # 合约
                        amount = abs(float(pos.get("positionAmt", 0)))
                        entry_price = float(pos.get("entryPrice", 0))
                        current_price = float(pos.get("markPrice", 0))
                        side = "long" if float(pos.get("positionAmt", 0)) > 0 else "short"

                    if amount <= 0:
                        continue

                    if symbol in existing_map:
                        # 更新现有持仓
                        existing = existing_map[symbol]
                        existing.amount = Decimal(str(round(amount, 8)))
                        if entry_price > 0:
                            existing.entry_price = Decimal(str(round(entry_price, 8)))
                        if current_price > 0:
                            existing.current_price = Decimal(str(round(current_price, 8)))
                        existing.side = side
                        existing.updated_at = now
                    else:
                        # 新建持仓
                        new_position = SignalPosition(
                            id=generate_snowflake_id(),
                            signal_id=signal_id,
                            symbol=symbol,
                            side=side,
                            amount=Decimal(str(round(amount, 8))),
                            entry_price=Decimal(str(round(entry_price, 8))),
                            current_price=Decimal(str(round(current_price, 8))) if current_price else None,
                            opened_at=now,
                            updated_at=now,
                        )
                        db.add(new_position)
                    upsert_count += 1

                # ── 数据库中有但快照中无 → 标记关闭（仓位已平） ──
                closed_count = 0
                for symbol, pos in existing_map.items():
                    if symbol not in snapshot_symbols:
                        # 计算平仓盈亏
                        if pos.entry_price and pos.current_price and pos.entry_price > 0:
                            if pos.side == "long":
                                pnl = (pos.current_price - pos.entry_price) * pos.amount
                            else:
                                pnl = (pos.entry_price - pos.current_price) * pos.amount
                            pnl_percent = ((pos.current_price - pos.entry_price) / pos.entry_price * Decimal("100")) if pos.side == "long" else ((pos.entry_price - pos.current_price) / pos.entry_price * Decimal("100"))
                            pos.pnl = round(pnl, 4)
                            pos.pnl_percent = round(pnl_percent, 4)
                        pos.status = "closed"
                        pos.closed_at = now
                        pos.amount = Decimal("0")
                        pos.updated_at = now
                        closed_count += 1
                        logger.info(
                            f"📉 持仓已平仓: signal_id={signal_id}, symbol={symbol}, "
                            f"pnl={pos.pnl}, pnl_percent={pos.pnl_percent}%"
                        )

                db.commit()
                logger.info(
                    f"📝 持仓快照已更新: signal_id={signal_id}, "
                    f"更新/新建 {upsert_count} 条, 关闭 {closed_count} 条持仓记录"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"存储持仓快照失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    async def _on_snapshot_account(self, event: SignalEvent) -> None:
        """
        处理账户信息快照

        目前仅记录日志，后续可扩展为存储账户余额快照。
        """
        account = event.data.get("account", {})
        logger.info(
            f"📝 账户快照已接收: signal_id={event.signal_id}, "
            f"account_keys={list(account.keys())[:5]}"
        )

    async def _save_snapshot_trade_history(self, event: SignalEvent) -> None:
        """
        将成交历史快照存储到 signal_trade_record 表

        通过 signal_id + original_order_id + order_status 去重，避免与实时事件重复写入。
        """
        trades = event.data.get("trades", [])
        if not trades:
            return

        try:
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)
                saved_count = 0
                skipped_count = 0

                for trade in trades:
                    symbol = trade.get("symbol", "")
                    original_order_id = str(trade.get("orderId", "") or trade.get("id", ""))
                    side = trade.get("side", "BUY") if trade.get("isBuyer") is None else (
                        "buy" if trade.get("isBuyer") else "sell"
                    )
                    if isinstance(side, str):
                        side = side.lower()
                    price = float(trade.get("price", 0))
                    qty = float(trade.get("qty", 0))
                    quote_qty = float(trade.get("quoteQty", price * qty))
                    trade_time_ms = trade.get("time", 0)

                    # 去重检查：避免与实时事件或多次快照拉取重复
                    if original_order_id:
                        existing = db.query(SignalTradeRecord.id).filter(
                            SignalTradeRecord.signal_id == event.signal_id,
                            SignalTradeRecord.original_order_id == original_order_id,
                            SignalTradeRecord.order_status == "SNAPSHOT_HISTORY",
                        ).first()
                        if existing:
                            skipped_count += 1
                            continue

                    traded_at = (
                        datetime.fromtimestamp(trade_time_ms / 1000, tz=timezone.utc)
                        if trade_time_ms
                        else now
                    )

                    record = SignalTradeRecord(
                        id=generate_snowflake_id(),
                        signal_id=event.signal_id,
                        original_order_id=original_order_id or None,
                        order_status="SNAPSHOT_HISTORY",
                        action=side,
                        symbol=symbol,
                        price=Decimal(str(round(price, 8))),
                        amount=Decimal(str(round(qty, 8))),
                        total=Decimal(str(round(quote_qty, 4))),
                        traded_at=traded_at,
                        created_at=now,
                    )
                    db.add(record)
                    saved_count += 1

                db.commit()
                logger.info(
                    f"📝 成交历史快照已存储: signal_id={event.signal_id}, "
                    f"保存 {saved_count} 条, 跳过重复 {skipped_count} 条"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"存储成交历史快照失败: {e}", exc_info=True)
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
        # 开发环境使用 Mock，不连接真实 Binance
        if settings.is_development:
            from quant_trading_system.mock.mock_binance_user_stream import (
                MockBinanceUserStreamManager,
            )
            self._stream_manager = MockBinanceUserStreamManager(
                api_key=target_api_key,
                api_secret=target_api_secret,
                account_type=account_type,
                testnet=testnet,
            )
        else:
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

        # 注册内置订阅器：信号记录存储（全局监听所有订单事件 + 快照事件）
        self._event_bus.subscribe_many(
            list(_ORDER_EVENTS | _SNAPSHOT_EVENTS),
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
