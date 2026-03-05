"""
信号记录存储订阅器
==================

监听信号事件总线上的订单事件和快照事件，将数据存储到数据库。

职责单一：
- 接收事件 → 写入/更新数据库
- 不涉及交易所对接，纯业务逻辑
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.signal import Signal, SignalPosition, SignalTradeRecord
from quant_trading_system.services.database.database import get_db
from quant_trading_system.engines.signal_event_bus import (
    SignalEvent,
    SignalEventType,
    SignalSubscriber,
)

logger = logging.getLogger(__name__)


# 需要存储到 signal_trade_record 的订单事件类型集合
ORDER_EVENTS = {
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
}

# 需要存储到 signal_trade_record 的快照事件类型集合
SNAPSHOT_EVENTS = {
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
        if event.type in ORDER_EVENTS:
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
