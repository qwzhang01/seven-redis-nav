"""
跟单的3个订阅器

1. 信号记录订阅器：记录信号事件到数据库
2. 信号ws订阅器：将信号事件推送到ws
3. 跟单订阅器：将信号事件转换为跟单事件，推送到订单引擎
"""


import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from quant_trading_system.core.database import get_db
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.engines.signal_event_bus import (
    SignalEvent,
    SignalEventType,
    SignalSubscriber,
)
from quant_trading_system.exchange_adapter.factory import create_rest_client
from quant_trading_system.models.follow import (
    ExchangeCopyAccount,
    SignalFollowEvent,
    SignalFollowOrder,
    SignalFollowPosition,
    SignalFollowTrade,
)
from quant_trading_system.models.signal import SignalPosition, SignalTradeRecord
from quant_trading_system.models.user import UserExchangeAPI

logger = structlog.get_logger(__name__)

# 需要推送到前端的订单事件类型
_WS_ORDER_EVENTS = {
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
}

# 需要推送到前端的快照事件类型
_WS_SNAPSHOT_EVENTS = {
    SignalEventType.SNAPSHOT_OPEN_ORDERS,
    SignalEventType.SNAPSHOT_POSITIONS,
    SignalEventType.SNAPSHOT_ACCOUNT,
    SignalEventType.SNAPSHOT_TRADE_HISTORY,
}

# 所有需要推送的事件类型集合（供外部注册使用）
WS_PUSH_EVENTS = _WS_ORDER_EVENTS | _WS_SNAPSHOT_EVENTS

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

# 跟单订阅器需要监听的事件类型
FOLLOW_ORDER_EVENTS = {
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
}


# ═══════════════════════════════════════════════════════════════
# 跟单上下文 — 单个跟单订单的运行时数据
# ═══════════════════════════════════════════════════════════════


@dataclass
class FollowContext:
    """
    跟单上下文

    保存一个跟单订单在运行时所需的全部信息，
    避免每次收到事件都查数据库。
    """

    follow_order_id: int  # 跟单订单ID
    user_id: int  # 用户ID
    signal_id: int  # 信号源ID
    signal_name: str  # 信号名称
    follow_amount: float  # 跟单资金（USDT）
    follow_ratio: float  # 跟单比例
    stop_loss: float | None  # 止损比例
    exchange: str  # 交易所

    # 跟单账户 API 信息
    follower_api_key: str = ""
    follower_api_secret: str = ""
    account_type: str = "spot"
    testnet: bool = False

    # 运行统计
    total_trades: int = 0
    signals_received: int = 0
    last_signal_time: datetime | None = None


# ═══════════════════════════════════════════════════════════════
# 跟单交易订阅器
# ═══════════════════════════════════════════════════════════════


class FollowTradeSubscriber(SignalSubscriber):
    """
    跟单交易订阅器

    作为 SignalEventBus 的订阅器，监听信号源的订单事件，
    按 signal_follow_orders 的跟单配置发起下单操作，
    并将订单状态变化保存到数据库。

    生命周期：
        subscriber = FollowTradeSubscriber()
        await subscriber.start()   # 扫描DB加载跟单配置
        # 注册到事件总线后自动处理事件
        ...
        await subscriber.stop()    # 清理资源
    """

    def __init__(self):
        # 内存中的跟单映射：{signal_id(int): [FollowContext, ...]}
        self._follow_map: dict[int, list[FollowContext]] = {}
        self._lock = asyncio.Lock()

        # 缓存下单客户端：{(api_key, account_type): rest_client}
        self._clients: dict[tuple[str, str], Any] = {}
        self._client_lock = asyncio.Lock()

        # 统计
        self._total_executed = 0
        self._total_failed = 0

    @property
    def name(self) -> str:
        return "FollowTradeSubscriber"

    # ── 生命周期 ──────────────────────────────────────────────

    async def start(self) -> None:
        """启动：扫描数据库加载活跃跟单配置到内存"""
        await self._scan_and_load_follows()
        logger.info(
            f"✅ 跟单交易订阅器已启动，活跃跟单: {self.total_follows} 个，"
            f"监听信号源: {len(self._follow_map)} 个"
        )

    async def stop(self) -> None:
        """停止：清理内存和关闭客户端"""
        async with self._lock:
            self._follow_map.clear()

        async with self._client_lock:
            for key, client in self._clients.items():
                try:
                    if hasattr(client, "close"):
                        client.close()
                except Exception as e:
                    logger.warning(f"关闭客户端失败: {key}, error={e}")
            self._clients.clear()

        logger.info(
            f"✅ 跟单交易订阅器已停止 "
            f"(执行: {self._total_executed}, 失败: {self._total_failed})"
        )

    # ── 事件处理 ──────────────────────────────────────────────

    async def on_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件（SignalSubscriber 接口实现）

        监听所有实时订单状态变化事件：
        - ORDER_NEW: 新订单创建，记录日志
        - ORDER_PARTIALLY_FILLED: 部分成交，记录日志
        - ORDER_FILLED: 完全成交，触发跟单下单
        - ORDER_CANCELED: 订单取消，记录日志
        """
        if event.type not in FOLLOW_ORDER_EVENTS:
            return

        signal_id = event.signal_id
        contexts = self._follow_map.get(signal_id, [])

        if not contexts:
            return

        data = event.data
        symbol = data.get("symbol", "")
        side = data.get("side", "")
        quantity = data.get("quantity", 0)
        price = data.get("price", 0)
        status_label = event.type.name.replace("ORDER_", "")

        logger.info(
            f"🔔 跟单订阅器收到信号 [{status_label}]: signal_id={signal_id} {symbol} {side} "
            f"qty={quantity:.6f} price={price:.4f}, "
            f"关联跟单数: {len(contexts)}"
        )

        # 只有完全成交才触发跟单下单
        if event.type == SignalEventType.ORDER_FILLED:
            tasks = []
            for ctx in contexts:
                ctx.signals_received += 1
                ctx.last_signal_time = datetime.now(timezone.utc)
                tasks.append(self._process_follow(ctx, event))
            await asyncio.gather(*tasks, return_exceptions=True)

        elif event.type == SignalEventType.ORDER_CANCELED:
            for ctx in contexts:
                ctx.signals_received += 1
                ctx.last_signal_time = datetime.now(timezone.utc)
            logger.info(
                f"📋 信号源订单已取消: signal_id={signal_id} {symbol} {side}, "
                f"已通知 {len(contexts)} 个跟单上下文"
            )
        else:
            # ORDER_NEW / ORDER_PARTIALLY_FILLED：仅更新统计
            for ctx in contexts:
                ctx.signals_received += 1
                ctx.last_signal_time = datetime.now(timezone.utc)

    # ── 跟单下单逻辑 ─────────────────────────────────────────

    async def _process_follow(self, ctx: FollowContext, event: SignalEvent) -> None:
        """处理单个跟单订单的跟单逻辑"""
        data = event.data
        symbol = data.get("symbol", "")
        side = data.get("side", "")
        original_qty = data.get("quantity", 0)
        price = data.get("price", 0)
        original_order_id = data.get("original_order_id", "")

        # 按比例计算跟单数量
        adjusted_qty = original_qty * ctx.follow_ratio

        # 金额限制（跟单资金作为最大金额）
        if price > 0 and ctx.follow_amount > 0:
            max_qty = ctx.follow_amount / price
            adjusted_qty = min(adjusted_qty, max_qty)

        if adjusted_qty <= 0:
            logger.warning(
                f"跟单数量为0，跳过: follow_order_id={ctx.follow_order_id} "
                f"{symbol} {side}"
            )
            return

        # 执行跟单下单
        await self._execute_copy(
            ctx=ctx,
            symbol=symbol,
            side=side,
            quantity=adjusted_qty,
            signal_price=price,
            original_order_id=original_order_id,
            signal_time=data.get("trade_time", 0),
        )

    async def _execute_copy(
        self,
        ctx: FollowContext,
        symbol: str,
        side: str,
        quantity: float,
        signal_price: float,
        original_order_id: str = "",
        signal_time: int = 0,
    ) -> None:
        """
        执行跟单下单

        通过交易所 REST 客户端执行市价单，并将结果记录到数据库。
        """
        client = self._get_or_create_client(
            ctx.follower_api_key, ctx.follower_api_secret,
            ctx.account_type, ctx.testnet,
        )

        # 在线程池中执行同步下单
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=quantity,
                ),
            )

            self._total_executed += 1
            ctx.total_trades += 1
            logger.info(
                f"✅ 跟单下单成功: follow_order_id={ctx.follow_order_id} "
                f"{symbol} {side} qty={quantity:.6f}, "
                f"订单ID={result.get('orderId')}"
            )

            # 异步记录成功结果到数据库
            await self._record_success(
                ctx=ctx,
                symbol=symbol,
                side=side,
                quantity=quantity,
                signal_price=signal_price,
                result=result,
                original_order_id=original_order_id,
                signal_time=signal_time,
            )

        except Exception as e:
            self._total_failed += 1
            logger.error(
                f"❌ 跟单下单失败: follow_order_id={ctx.follow_order_id} "
                f"{symbol} {side} qty={quantity:.6f}, 错误: {e}"
            )

            # 记录失败事件到数据库
            await self._record_failure(
                ctx=ctx,
                symbol=symbol,
                side=side,
                quantity=quantity,
                error=str(e),
                original_order_id=original_order_id,
            )

    def _get_or_create_client(
        self,
        api_key: str,
        api_secret: str,
        account_type: str = "spot",
        testnet: bool = False,
    ) -> Any:
        """获取或创建下单客户端（按 API Key + 账户类型缓存）"""
        cache_key = (api_key, account_type)
        if cache_key not in self._clients:
            self._clients[cache_key] = create_rest_client(
                "binance",
                api_key=api_key,
                api_secret=api_secret,
                market_type=account_type,
                testnet=testnet,
            )
        return self._clients[cache_key]

    # ── 数据库记录 ────────────────────────────────────────────

    async def _record_success(
        self,
        ctx: FollowContext,
        symbol: str,
        side: str,
        quantity: float,
        signal_price: float,
        result: dict[str, Any],
        original_order_id: str,
        signal_time: int,
    ) -> None:
        """
        记录成功的跟单交易到数据库

        写入：
        1. signal_follow_trades — 交易流水
        2. signal_follow_positions — 持仓更新
        3. signal_follow_events — 成功事件日志
        4. signal_follow_orders — 更新统计字段
        """
        try:
            async for db in get_db():
                try:
                    now = datetime.now(timezone.utc)

                    # 提取实际成交数据
                    exec_qty = float(result.get("executedQty", quantity))
                    cum_quote = float(result.get("cummulativeQuoteQty", 0))
                    exec_price = (
                            cum_quote / exec_qty) if exec_qty > 0 else signal_price
                    total = cum_quote if cum_quote > 0 else exec_price * exec_qty

                    # 计算滑点
                    slippage = 0.0
                    if signal_price > 0 and exec_price > 0:
                        slippage = abs(exec_price - signal_price) / signal_price * 100

                    # 信号时间
                    signal_dt = (
                        datetime.fromtimestamp(signal_time / 1000, tz=timezone.utc)
                        if signal_time
                        else now
                    )

                    side_lower = side.lower()

                    # 1. 写入交易流水
                    trade = SignalFollowTrade(
                        id=generate_snowflake_id(),
                        follow_order_id=ctx.follow_order_id,
                        user_id=ctx.user_id,
                        symbol=symbol,
                        side=side_lower,
                        price=Decimal(str(round(exec_price, 8))),
                        amount=Decimal(str(round(exec_qty, 8))),
                        total=Decimal(str(round(total, 8))),
                        fee=Decimal("0"),
                        signal_time=signal_dt,
                        slippage=Decimal(str(round(slippage, 6))),
                        trade_time=now,
                        create_time=now,
                    )
                    db.add(trade)

                    # 2. 更新持仓
                    await self._update_position(
                        db, ctx.follow_order_id, ctx.user_id,
                        symbol, side_lower, exec_qty, exec_price, now,
                    )

                    # 3. 更新跟单订单统计
                    result_order = await db.execute(
                        select(SignalFollowOrder).where(
                            SignalFollowOrder.id == ctx.follow_order_id,
                        )
                    )
                    follow_order = result_order.scalars().first()
                    if follow_order:
                        follow_order.total_trades = (follow_order.total_trades or 0) + 1
                        follow_order.update_time = now

                    # 4. 记录成功事件
                    event = SignalFollowEvent(
                        id=generate_snowflake_id(),
                        follow_order_id=ctx.follow_order_id,
                        user_id=ctx.user_id,
                        event_type="success",
                        type_label="成交",
                        message=(
                            f"跟单成交: {symbol} {side.upper()} "
                            f"数量={exec_qty:.6f} 价格={exec_price:.4f} "
                            f"滑点={slippage:.4f}%"
                        ),
                        event_meta={
                            "action": "copy_trade_executed",
                            "symbol": symbol,
                            "side": side_lower,
                            "quantity": exec_qty,
                            "price": exec_price,
                            "total": total,
                            "slippage": slippage,
                            "signal_price": signal_price,
                            "original_order_id": original_order_id,
                            "copy_order_id": str(result.get("orderId", "")),
                        },
                        event_time=now,
                        create_time=now,
                    )
                    db.add(event)

                    await db.commit()

                except Exception as e:
                    await db.rollback()
                    logger.error(f"记录跟单成功到数据库失败: {e}", exc_info=True)
                break
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    async def _update_position(
        self,
        db: AsyncSession,
        follow_order_id: int,
        user_id: int,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        now: datetime,
    ) -> None:
        """
        更新持仓快照

        - BUY: 新增或增加持仓（加权平均成本）
        - SELL: 减少持仓，计算已实现盈亏
        """
        result = await db.execute(
            select(SignalFollowPosition).where(
                SignalFollowPosition.follow_order_id == follow_order_id,
                SignalFollowPosition.symbol == symbol,
                SignalFollowPosition.status == "open",
            )
        )
        position = result.scalars().first()

        if side == "buy":
            if position:
                # 加仓：加权平均成本
                old_amount = float(position.amount)
                old_price = float(position.entry_price)
                new_amount = old_amount + quantity
                new_avg_price = (
                    (old_amount * old_price + quantity * price) / new_amount
                    if new_amount > 0
                    else price
                )
                position.amount = Decimal(str(round(new_amount, 8)))
                position.entry_price = Decimal(str(round(new_avg_price, 8)))
                position.current_price = Decimal(str(round(price, 8)))
                position.update_time = now
            else:
                # 新建持仓
                position = SignalFollowPosition(
                    id=generate_snowflake_id(),
                    follow_order_id=follow_order_id,
                    user_id=user_id,
                    symbol=symbol,
                    side="long",
                    amount=Decimal(str(round(quantity, 8))),
                    entry_price=Decimal(str(round(price, 8))),
                    current_price=Decimal(str(round(price, 8))),
                    pnl=Decimal("0"),
                    pnl_percent=Decimal("0"),
                    status="open",
                    open_time=now,
                    create_time=now,
                    update_time=now,
                )
                db.add(position)

        elif side == "sell":
            if position:
                old_amount = float(position.amount)
                reduce_qty = min(quantity, old_amount)
                entry_price = float(position.entry_price)

                # 计算已实现盈亏
                pnl = (price - entry_price) * reduce_qty
                new_amount = old_amount - reduce_qty

                if new_amount <= 0.000001:
                    # 完全平仓
                    position.amount = Decimal("0")
                    position.status = "closed"
                    position.close_time = now
                    position.pnl = Decimal(str(round(pnl, 8)))
                    if entry_price > 0:
                        position.pnl_percent = Decimal(
                            str(round((price - entry_price) / entry_price * 100, 6))
                        )
                else:
                    # 部分平仓
                    position.amount = Decimal(str(round(new_amount, 8)))

                position.current_price = Decimal(str(round(price, 8)))
                position.update_time = now

    async def _record_failure(
        self,
        ctx: FollowContext,
        symbol: str,
        side: str,
        quantity: float,
        error: str,
        original_order_id: str,
    ) -> None:
        """记录失败的跟单事件到数据库"""
        try:
            async for db in get_db():
                try:
                    now = datetime.now(timezone.utc)
                    event = SignalFollowEvent(
                        id=generate_snowflake_id(),
                        follow_order_id=ctx.follow_order_id,
                        user_id=ctx.user_id,
                        event_type="error",
                        type_label="异常",
                        message=(
                            f"跟单失败: {symbol} {side.upper()} "
                            f"数量={quantity:.6f}, 错误: {error}"
                        ),
                        event_meta={
                            "action": "copy_trade_failed",
                            "symbol": symbol,
                            "side": side.lower(),
                            "quantity": quantity,
                            "error": error,
                            "original_order_id": original_order_id,
                        },
                        event_time=now,
                        create_time=now,
                    )
                    db.add(event)
                    await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(f"记录跟单失败事件到数据库失败: {e}", exc_info=True)
                break
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    # ── 数据库扫描 ────────────────────────────────────────────

    async def _scan_and_load_follows(self) -> None:
        """扫描 signal_follow_orders 表，加载活跃跟单到内存"""
        try:
            async for db in get_db():
                try:
                    result = await db.execute(
                        select(SignalFollowOrder).where(
                            SignalFollowOrder.status == "following",
                            SignalFollowOrder.enable_flag == True,
                        )
                    )
                    orders = result.scalars().all()

                    logger.info(f"扫描到 {len(orders)} 个活跃跟单订单")

                    for order in orders:
                        signal_id = int(order.strategy_id) if order.strategy_id else 0
                        if signal_id == 0:
                            logger.warning(
                                f"跟单订单缺少 strategy_id，跳过: "
                                f"follow_order_id={order.id}"
                            )
                            continue

                        # 查询跟单账户配置
                        result_ca = await db.execute(
                            select(ExchangeCopyAccount).where(
                                ExchangeCopyAccount.follow_order_id == order.id,
                                ExchangeCopyAccount.status == "active",
                                ExchangeCopyAccount.enable_flag == True,
                            )
                        )
                        copy_account = result_ca.scalars().first()

                        if not copy_account:
                            logger.warning(
                                f"跟单订单无跟单账户配置，跳过: "
                                f"follow_order_id={order.id}"
                            )
                            continue

                        # 获取跟单账户 API
                        result_api = await db.execute(
                            select(UserExchangeAPI).where(
                                UserExchangeAPI.id == copy_account.api_key_id,
                                UserExchangeAPI.enable_flag == True,
                            )
                        )
                        follower_api = result_api.scalars().first()

                        if not follower_api:
                            logger.warning(
                                f"跟单账户 API 不存在，跳过: "
                                f"follow_order_id={order.id}"
                            )
                            continue

                        config = copy_account.config or {}

                        ctx = FollowContext(
                            follow_order_id=order.id,
                            user_id=order.user_id,
                            signal_id=signal_id,
                            signal_name=order.signal_name or "",
                            follow_amount=float(
                                order.follow_amount) if order.follow_amount else 0,
                            follow_ratio=float(
                                order.follow_ratio) if order.follow_ratio else 1.0,
                            stop_loss=float(
                                order.stop_loss) if order.stop_loss else None,
                            exchange=order.exchange or "binance",
                            follower_api_key=follower_api.api_key,
                            follower_api_secret=follower_api.secret_key,
                            account_type=copy_account.account_type or "spot",
                            testnet=config.get("testnet", False),
                        )

                        if signal_id not in self._follow_map:
                            self._follow_map[signal_id] = []
                        self._follow_map[signal_id].append(ctx)

                        logger.debug(
                            f"加载跟单: follow_order_id={order.id} → signal_id={signal_id}"
                        )
                except Exception as e:
                    logger.error(f"扫描跟单订单表查询失败: {e}", exc_info=True)
                break
        except Exception as e:
            logger.error(f"扫描跟单订单表失败: {e}", exc_info=True)

    # ── 动态管理 ──────────────────────────────────────────────

    async def add_follow(self, follow_order_id: int) -> bool:
        """
        动态添加一个跟单到内存（用户通过 API 创建跟单后调用）
        """
        try:
            async for db in get_db():
                try:
                    result = await db.execute(
                        select(SignalFollowOrder).where(
                            SignalFollowOrder.id == follow_order_id,
                            SignalFollowOrder.status == "following",
                            SignalFollowOrder.enable_flag == True,
                        )
                    )
                    order = result.scalars().first()

                    if not order:
                        logger.warning(f"跟单订单不存在或不活跃: {follow_order_id}")
                        break

                    signal_id = int(order.strategy_id) if order.strategy_id else 0
                    if signal_id == 0:
                        break

                    result_ca = await db.execute(
                        select(ExchangeCopyAccount).where(
                            ExchangeCopyAccount.follow_order_id == follow_order_id,
                            ExchangeCopyAccount.status == "active",
                            ExchangeCopyAccount.enable_flag == True,
                        )
                    )
                    copy_account = result_ca.scalars().first()
                    if not copy_account:
                        break

                    result_api = await db.execute(
                        select(UserExchangeAPI).where(
                            UserExchangeAPI.id == copy_account.api_key_id,
                            UserExchangeAPI.enable_flag == True,
                        )
                    )
                    follower_api = result_api.scalars().first()
                    if not follower_api:
                        break

                    config = copy_account.config or {}

                    ctx = FollowContext(
                        follow_order_id=order.id,
                        user_id=order.user_id,
                        signal_id=signal_id,
                        signal_name=order.signal_name or "",
                        follow_amount=float(
                            order.follow_amount) if order.follow_amount else 0,
                        follow_ratio=float(
                            order.follow_ratio) if order.follow_ratio else 1.0,
                        stop_loss=float(order.stop_loss) if order.stop_loss else None,
                        exchange=order.exchange or "binance",
                        follower_api_key=follower_api.api_key,
                        follower_api_secret=follower_api.secret_key,
                        account_type=copy_account.account_type or "spot",
                        testnet=config.get("testnet", False),
                    )

                    async with self._lock:
                        if signal_id not in self._follow_map:
                            self._follow_map[signal_id] = []
                        if not any(c.follow_order_id == follow_order_id for c in
                                   self._follow_map[signal_id]):
                            self._follow_map[signal_id].append(ctx)

                    logger.info(
                        f"动态添加跟单成功: follow_order_id={follow_order_id} → signal_id={signal_id}")
                    return True
                except Exception as e:
                    logger.error(f"动态添加跟单查询失败: {e}", exc_info=True)
                break
        except Exception as e:
            logger.error(f"动态添加跟单失败: {e}", exc_info=True)
            return False

    async def remove_follow(self, follow_order_id: int) -> bool:
        """动态移除一个跟单（用户停止跟单后调用）"""
        async with self._lock:
            for signal_id, contexts in list(self._follow_map.items()):
                self._follow_map[signal_id] = [
                    c for c in contexts if c.follow_order_id != follow_order_id
                ]
                if not self._follow_map[signal_id]:
                    del self._follow_map[signal_id]

        logger.info(f"跟单已从订阅器移除: follow_order_id={follow_order_id}")
        return True

    async def update_follow_config(
        self,
        follow_order_id: int,
        follow_ratio: float | None = None,
        follow_amount: float | None = None,
        stop_loss: float | None = None,
    ) -> bool:
        """动态更新跟单配置（用户修改配置后调用）"""
        async with self._lock:
            for contexts in self._follow_map.values():
                for ctx in contexts:
                    if ctx.follow_order_id == follow_order_id:
                        if follow_ratio is not None:
                            ctx.follow_ratio = follow_ratio
                        if follow_amount is not None:
                            ctx.follow_amount = follow_amount
                        if stop_loss is not None:
                            ctx.stop_loss = stop_loss
                        logger.info(
                            f"跟单配置已更新: follow_order_id={follow_order_id}"
                        )
                        return True
        return False

    # ── 状态查询 ──────────────────────────────────────────────

    def get_follow_count(self, signal_id: int) -> int:
        """获取指定信号源的跟单数量"""
        return len(self._follow_map.get(signal_id, []))

    @property
    def total_follows(self) -> int:
        """总跟单数量"""
        return sum(len(v) for v in self._follow_map.values())

    @property
    def monitored_signals(self) -> list[int]:
        """正在监听的信号源ID列表"""
        return list(self._follow_map.keys())

    @property
    def stats(self) -> dict[str, Any]:
        """获取订阅器统计信息"""
        follow_details = []
        for signal_id, contexts in self._follow_map.items():
            for ctx in contexts:
                follow_details.append({
                    "follow_order_id": ctx.follow_order_id,
                    "signal_id": ctx.signal_id,
                    "signal_name": ctx.signal_name,
                    "follow_ratio": ctx.follow_ratio,
                    "follow_amount": ctx.follow_amount,
                    "signals_received": ctx.signals_received,
                    "total_trades": ctx.total_trades,
                    "last_signal_time": ctx.last_signal_time.isoformat() if ctx.last_signal_time else None,
                })

        return {
            "total_follows": self.total_follows,
            "monitored_signals": len(self._follow_map),
            "total_executed": self._total_executed,
            "total_failed": self._total_failed,
            "active_clients": len(self._clients),
            "follows": follow_details,
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
            async for db in get_db():
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
                        result = await db.execute(
                            select(SignalTradeRecord).where(
                                SignalTradeRecord.signal_id == event.signal_id,
                                SignalTradeRecord.symbol == symbol,
                                SignalTradeRecord.action == "buy",
                                SignalTradeRecord.order_status == "FILLED",
                            ).order_by(SignalTradeRecord.traded_at.desc())
                        )
                        open_trade = result.scalars().first()
                        if open_trade:
                            open_trade_id = open_trade.id

                        # 查询当前持仓，提前计算 pnl
                        result = await db.execute(
                            select(SignalPosition).where(
                                SignalPosition.signal_id == event.signal_id,
                                SignalPosition.symbol == symbol,
                                SignalPosition.status == "open",
                            )
                        )
                        position = result.scalars().first()
                        if position and position.entry_price and position.entry_price > 0:
                            if position.side == "long":
                                trade_pnl = round(
                                    (price - position.entry_price) * amount, 4)
                                pnl_pct = abs((
                                                      price - position.entry_price) / position.entry_price * 100)
                            else:
                                trade_pnl = round(
                                    (position.entry_price - price) * amount, 4)
                                pnl_pct = abs((
                                                      position.entry_price - price) / position.entry_price * 100)

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
                        index_elements=["signal_id", "original_order_id",
                                        "order_status"],
                    )
                    result = await db.execute(stmt)

                    # 如果是卖出（平仓）成交，更新 signal_position 表
                    if is_close_trade and result.rowcount > 0 and position:
                        # 计算并写入持仓盈亏
                        if position.entry_price and position.entry_price > 0:
                            if position.side == "long":
                                pnl_percent = (
                                                      price - position.entry_price) / position.entry_price * Decimal(
                                    "100")
                            else:
                                pnl_percent = (
                                                      position.entry_price - price) / position.entry_price * Decimal(
                                    "100")
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

                    await db.commit()

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
                    await db.rollback()
                    logger.error(f"存储信号记录失败: {e}", exc_info=True)
                break
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
            async for db in get_db():
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
                            result = await db.execute(
                                select(SignalTradeRecord.id).where(
                                    SignalTradeRecord.signal_id == event.signal_id,
                                    SignalTradeRecord.original_order_id == original_order_id,
                                    SignalTradeRecord.order_status == "SNAPSHOT",
                                )
                            )
                            existing = result.scalars().first()
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

                    await db.commit()
                    logger.info(
                        f"📝 挂单快照已存储: signal_id={event.signal_id}, "
                        f"保存 {saved_count} 条, 跳过重复 {skipped_count} 条"
                    )
                except Exception as e:
                    await db.rollback()
                    logger.error(f"存储挂单快照失败: {e}", exc_info=True)
                break
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
            async for db in get_db():
                try:
                    now = datetime.now(timezone.utc)

                    # 获取数据库中当前打开的持仓（仅 open 状态）
                    result = await db.execute(
                        select(SignalPosition).where(
                            SignalPosition.signal_id == signal_id,
                            SignalPosition.status == "open",
                        )
                    )
                    existing_positions = result.scalars().all()
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
                            amount = float(pos.get("free", 0)) + float(
                                pos.get("locked", 0))
                            side = "long"
                            entry_price = 0  # 现货无入场价概念
                            current_price = 0
                        else:
                            # 合约
                            amount = abs(float(pos.get("positionAmt", 0)))
                            entry_price = float(pos.get("entryPrice", 0))
                            current_price = float(pos.get("markPrice", 0))
                            side = "long" if float(
                                pos.get("positionAmt", 0)) > 0 else "short"

                        if amount <= 0:
                            continue

                        if symbol in existing_map:
                            # 更新现有持仓
                            existing = existing_map[symbol]
                            existing.amount = Decimal(str(round(amount, 8)))
                            if entry_price > 0:
                                existing.entry_price = Decimal(
                                    str(round(entry_price, 8)))
                            if current_price > 0:
                                existing.current_price = Decimal(
                                    str(round(current_price, 8)))
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
                                current_price=Decimal(str(round(current_price,
                                                                8))) if current_price else None,
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
                                    pnl = (
                                                  pos.current_price - pos.entry_price) * pos.amount
                                else:
                                    pnl = (
                                                  pos.entry_price - pos.current_price) * pos.amount
                                pnl_percent = ((
                                                       pos.current_price - pos.entry_price) / pos.entry_price * Decimal(
                                    "100")) if pos.side == "long" else ((
                                                                                pos.entry_price - pos.current_price) / pos.entry_price * Decimal(
                                    "100"))
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

                    await db.commit()
                    logger.info(
                        f"📝 持仓快照已更新: signal_id={signal_id}, "
                        f"更新/新建 {upsert_count} 条, 关闭 {closed_count} 条持仓记录"
                    )
                except Exception as e:
                    await db.rollback()
                    logger.error(f"存储持仓快照失败: {e}", exc_info=True)
                break
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
            async for db in get_db():
                try:
                    now = datetime.now(timezone.utc)
                    saved_count = 0
                    skipped_count = 0

                    for trade in trades:
                        symbol = trade.get("symbol", "")
                        original_order_id = str(
                            trade.get("orderId", "") or trade.get("id", ""))
                        side = trade.get("side", "BUY") if trade.get(
                            "isBuyer") is None else (
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
                            result = await db.execute(
                                select(SignalTradeRecord.id).where(
                                    SignalTradeRecord.signal_id == event.signal_id,
                                    SignalTradeRecord.original_order_id == original_order_id,
                                    SignalTradeRecord.order_status == "SNAPSHOT_HISTORY",
                                )
                            )
                            existing = result.scalars().first()
                            if existing:
                                skipped_count += 1
                                continue

                        traded_at = (
                            datetime.fromtimestamp(trade_time_ms / 1000,
                                                   tz=timezone.utc)
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

                    await db.commit()
                    logger.info(
                        f"📝 成交历史快照已存储: signal_id={event.signal_id}, "
                        f"保存 {saved_count} 条, 跳过重复 {skipped_count} 条"
                    )
                except Exception as e:
                    await db.rollback()
                    logger.error(f"存储成交历史快照失败: {e}", exc_info=True)
                break
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")


class SignalWsSubscriber(SignalSubscriber):
    """
    信号 WebSocket 推送订阅器

    监听所有订单事件和快照事件，将最新的仓位变化推送到前端 WebSocket：
    - 实时订单事件 → 推送订单状态变化
    - 快照事件 → 推送持仓/挂单/账户快照
    """

    @property
    def name(self) -> str:
        return "SignalWsSubscriber"

    async def on_signal_event(self, event: SignalEvent) -> None:
        """根据事件类型推送到前端 WebSocket"""
        if event.type in _WS_ORDER_EVENTS:
            await self._push_order_event(event)
        elif event.type in _WS_SNAPSHOT_EVENTS:
            await self._push_snapshot_event(event)

    async def _push_order_event(self, event: SignalEvent) -> None:
        """
        推送实时订单事件到前端 WebSocket

        将订单状态变化（NEW / FILLED / PARTIALLY_FILLED / CANCELED）
        通过 WebSocket 推送到订阅了 signal/{signal_id} 频道的前端客户端。
        """
        data = event.data
        original_order_id = data.get("original_order_id", "")
        order_status = data.get("status", "")

        try:
            from quant_trading_system.api.websocket.trading_ws import \
                push_copy_trade_signal

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
            logger.debug(
                f"📤 已推送订单事件到前端: signal_id={event.signal_id}, "
                f"type={event.type.name}, symbol={data.get('symbol', '')}"
            )
        except Exception as e:
            # WebSocket 推送失败不应影响其他订阅器
            logger.debug(f"WebSocket 推送订单事件失败: {e}")

    async def _push_snapshot_event(self, event: SignalEvent) -> None:
        """
        推送快照事件到前端 WebSocket

        将启动时拉取的快照数据（持仓/挂单/账户/成交历史）
        通过 WebSocket 推送到订阅了 signal/{signal_id} 频道的前端客户端。
        """
        try:
            from quant_trading_system.api.websocket.trading_ws import \
                push_copy_trade_signal

            snapshot_type = event.type.name  # 如 SNAPSHOT_POSITIONS
            await push_copy_trade_signal(
                signal_id=event.signal_id,
                event_type=snapshot_type,
                trade_data={
                    "signal_id": event.signal_id,
                    "snapshot_type": snapshot_type,
                    "data": event.data,
                },
            )
            logger.debug(
                f"📤 已推送快照事件到前端: signal_id={event.signal_id}, "
                f"type={snapshot_type}"
            )
        except Exception as e:
            logger.debug(f"WebSocket 推送快照事件失败: {e}")
