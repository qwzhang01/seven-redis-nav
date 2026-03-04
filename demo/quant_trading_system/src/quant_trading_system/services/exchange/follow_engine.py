"""
跟单引擎（FollowEngine）
========================

核心职责：
1. 系统启动时扫描 signal_follow_orders 表，将活跃跟单数据 load 到内存
2. 订阅事件总线上对应信号源的 ORDER_FILLED 事件
3. 收到仓位变化后，按跟单配置（比例、金额限制）计算跟单参数
4. 将跟单指令转发到订单引擎（CopyOrderEngine）执行

数据流：
    SignalEventBus (ORDER_FILLED)
        → FollowEngine._on_signal_event()
        → 按 signal_id 查找所有关联的跟单订单
        → 按比例计算跟单数量
        → CopyOrderEngine.execute_copy() 执行下单

内存结构：
    _follow_map: {signal_id: [FollowContext, ...]}
    每个 FollowContext 包含跟单订单配置和跟单账户 API 信息
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from quant_trading_system.models.follow import (
    ExchangeCopyAccount,
    SignalFollowOrder,
)
from quant_trading_system.models.user import UserExchangeAPI
from quant_trading_system.services.database.database import get_db
from quant_trading_system.engines.signal_event_bus import (
    SignalEvent,
    SignalEventBus,
    SignalEventType,
    SignalSubscriber,
    signal_event_bus,
)

if TYPE_CHECKING:
    from quant_trading_system.services.exchange.copy_order_engine import CopyOrderEngine

logger = logging.getLogger(__name__)

# 跟单引擎需要监听的所有实时订单事件类型
_FOLLOW_ORDER_EVENTS = [
    SignalEventType.ORDER_FILLED,
    SignalEventType.ORDER_PARTIALLY_FILLED,
    SignalEventType.ORDER_NEW,
    SignalEventType.ORDER_CANCELED,
]


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

    follow_order_id: int           # 跟单订单ID
    user_id: int                   # 用户ID
    signal_id: int                 # 信号源ID（signal 表的 strategy_id 对应）
    signal_name: str               # 信号名称
    follow_amount: float           # 跟单资金（USDT）
    follow_ratio: float            # 跟单比例
    stop_loss: float | None        # 止损比例
    exchange: str                  # 交易所

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
# 跟单引擎
# ═══════════════════════════════════════════════════════════════


class FollowEngine(SignalSubscriber):
    """
    跟单引擎

    作为 SignalEventBus 的订阅器，监听信号源的仓位变化事件，
    并将跟单指令转发给 CopyOrderEngine 执行。

    生命周期：
        engine = FollowEngine(copy_order_engine)
        await engine.start()   # 扫描DB + 订阅事件总线
        ...
        await engine.stop()    # 取消订阅 + 清理内存
    """

    def __init__(
        self,
        copy_order_engine: "CopyOrderEngine",
        event_bus: SignalEventBus | None = None,
    ):
        self._copy_order_engine = copy_order_engine
        self._event_bus = event_bus or signal_event_bus
        self._running = False

        # 内存中的跟单映射：{signal_id(int): [FollowContext, ...]}
        # 一个信号源可以有多个跟单订单（不同用户跟同一个信号）
        self._follow_map: dict[int, list[FollowContext]] = {}
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return "FollowEngine"

    # ── 生命周期 ──────────────────────────────────────────────

    async def start(self) -> None:
        """
        启动跟单引擎

        1. 扫描 signal_follow_orders 表，加载活跃跟单到内存
        2. 注册为事件总线的全局 ORDER_FILLED 订阅器
        """
        if self._running:
            logger.warning("跟单引擎已在运行中")
            return

        self._running = True

        # 从数据库加载活跃跟单
        await self._scan_and_load_follows()

        # 注册到事件总线（全局监听所有实时订单事件）
        self._event_bus.subscribe_many(_FOLLOW_ORDER_EVENTS, self)

        logger.info(
            f"✅ 跟单引擎已启动，活跃跟单: {sum(len(v) for v in self._follow_map.values())} 个，"
            f"监听信号源: {len(self._follow_map)} 个，"
            f"监听事件类型: {[e.name for e in _FOLLOW_ORDER_EVENTS]}"
        )

    async def stop(self) -> None:
        """停止跟单引擎"""
        if not self._running:
            return

        self._running = False

        # 从事件总线注销
        self._event_bus.unsubscribe_all(self)

        # 清理内存
        async with self._lock:
            self._follow_map.clear()

        logger.info("✅ 跟单引擎已停止")

    # ── 事件处理 ──────────────────────────────────────────────

    async def on_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件（SignalSubscriber 接口实现）

        监听所有实时订单状态变化事件：
        - ORDER_NEW: 新订单创建，记录日志
        - ORDER_PARTIALLY_FILLED: 部分成交，记录日志
        - ORDER_FILLED: 完全成交，触发跟单下单
        - ORDER_CANCELED: 订单取消，记录日志（后续可扩展取消跟单挂单）
        """
        if event.type not in {
            SignalEventType.ORDER_FILLED,
            SignalEventType.ORDER_PARTIALLY_FILLED,
            SignalEventType.ORDER_NEW,
            SignalEventType.ORDER_CANCELED,
        }:
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
            f"🔔 跟单引擎收到信号 [{status_label}]: signal_id={signal_id} {symbol} {side} "
            f"qty={quantity:.6f} price={price:.4f}, "
            f"关联跟单数: {len(contexts)}"
        )

        # 只有完全成交才触发跟单下单
        if event.type == SignalEventType.ORDER_FILLED:
            # 并发处理所有关联的跟单订单
            tasks = []
            for ctx in contexts:
                ctx.signals_received += 1
                ctx.last_signal_time = datetime.now(timezone.utc)
                tasks.append(self._process_follow(ctx, event))

            await asyncio.gather(*tasks, return_exceptions=True)

        elif event.type == SignalEventType.ORDER_CANCELED:
            # 订单取消：记录到各跟单上下文，后续可扩展为取消对应的跟单挂单
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

    async def _process_follow(
        self,
        ctx: FollowContext,
        event: SignalEvent,
    ) -> None:
        """
        处理单个跟单订单的跟单逻辑

        Args:
            ctx: 跟单上下文
            event: 信号事件
        """
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

        # 发送到订单引擎执行
        try:
            await self._copy_order_engine.execute_copy(
                follow_order_id=ctx.follow_order_id,
                user_id=ctx.user_id,
                signal_id=ctx.signal_id,
                follower_api_key=ctx.follower_api_key,
                follower_api_secret=ctx.follower_api_secret,
                account_type=ctx.account_type,
                testnet=ctx.testnet,
                symbol=symbol,
                side=side,
                quantity=adjusted_qty,
                signal_price=price,
                original_order_id=original_order_id,
                signal_time=data.get("trade_time", 0),
            )
            ctx.total_trades += 1
        except Exception as e:
            logger.error(
                f"跟单指令执行失败: follow_order_id={ctx.follow_order_id} "
                f"{symbol} {side}, error={e}",
                exc_info=True,
            )

    # ── 数据库扫描 ────────────────────────────────────────────

    async def _scan_and_load_follows(self) -> None:
        """扫描 signal_follow_orders 表，加载活跃跟单到内存"""
        try:
            db: Session = next(get_db())
            try:
                # 查询所有活跃的跟单订单
                orders = db.query(SignalFollowOrder).filter(
                    SignalFollowOrder.status == "following",
                    SignalFollowOrder.enable_flag == True,
                ).all()

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
                    copy_account = db.query(ExchangeCopyAccount).filter(
                        ExchangeCopyAccount.follow_order_id == order.id,
                        ExchangeCopyAccount.status == "active",
                        ExchangeCopyAccount.enable_flag == True,
                    ).first()

                    if not copy_account:
                        logger.warning(
                            f"跟单订单无跟单账户配置，跳过: "
                            f"follow_order_id={order.id}"
                        )
                        continue

                    # 获取跟单账户 API
                    follower_api = db.query(UserExchangeAPI).filter(
                        UserExchangeAPI.id == copy_account.api_key_id,
                        UserExchangeAPI.enable_flag == True,
                    ).first()

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
                        follow_amount=float(order.follow_amount) if order.follow_amount else 0,
                        follow_ratio=float(order.follow_ratio) if order.follow_ratio else 1.0,
                        stop_loss=float(order.stop_loss) if order.stop_loss else None,
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
            finally:
                db.close()
        except Exception as e:
            logger.error(f"扫描跟单订单表失败: {e}", exc_info=True)

    # ── 动态管理 ──────────────────────────────────────────────

    async def add_follow(self, follow_order_id: int) -> bool:
        """
        动态添加一个跟单到内存（用户通过 API 创建跟单后调用）

        Args:
            follow_order_id: 跟单订单ID

        Returns:
            是否添加成功
        """
        try:
            db: Session = next(get_db())
            try:
                order = db.query(SignalFollowOrder).filter(
                    SignalFollowOrder.id == follow_order_id,
                    SignalFollowOrder.status == "following",
                    SignalFollowOrder.enable_flag == True,
                ).first()

                if not order:
                    logger.warning(f"跟单订单不存在或不活跃: {follow_order_id}")
                    return False

                signal_id = int(order.strategy_id) if order.strategy_id else 0
                if signal_id == 0:
                    return False

                # 查询跟单账户配置
                copy_account = db.query(ExchangeCopyAccount).filter(
                    ExchangeCopyAccount.follow_order_id == follow_order_id,
                    ExchangeCopyAccount.status == "active",
                    ExchangeCopyAccount.enable_flag == True,
                ).first()
                if not copy_account:
                    return False

                follower_api = db.query(UserExchangeAPI).filter(
                    UserExchangeAPI.id == copy_account.api_key_id,
                    UserExchangeAPI.enable_flag == True,
                ).first()
                if not follower_api:
                    return False

                config = copy_account.config or {}

                ctx = FollowContext(
                    follow_order_id=order.id,
                    user_id=order.user_id,
                    signal_id=signal_id,
                    signal_name=order.signal_name or "",
                    follow_amount=float(order.follow_amount) if order.follow_amount else 0,
                    follow_ratio=float(order.follow_ratio) if order.follow_ratio else 1.0,
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
                    # 避免重复添加
                    if not any(c.follow_order_id == follow_order_id for c in self._follow_map[signal_id]):
                        self._follow_map[signal_id].append(ctx)

                logger.info(f"动态添加跟单成功: follow_order_id={follow_order_id} → signal_id={signal_id}")
                return True
            finally:
                db.close()
        except Exception as e:
            logger.error(f"动态添加跟单失败: {e}", exc_info=True)
            return False

    async def remove_follow(self, follow_order_id: int) -> bool:
        """
        动态移除一个跟单（用户停止跟单后调用）

        Args:
            follow_order_id: 跟单订单ID

        Returns:
            是否移除成功
        """
        async with self._lock:
            for signal_id, contexts in list(self._follow_map.items()):
                self._follow_map[signal_id] = [
                    c for c in contexts if c.follow_order_id != follow_order_id
                ]
                # 如果该信号源没有跟单了，移除条目
                if not self._follow_map[signal_id]:
                    del self._follow_map[signal_id]

        logger.info(f"跟单已从引擎移除: follow_order_id={follow_order_id}")
        return True

    async def update_follow_config(
        self,
        follow_order_id: int,
        follow_ratio: float | None = None,
        follow_amount: float | None = None,
        stop_loss: float | None = None,
    ) -> bool:
        """
        动态更新跟单配置（用户修改配置后调用）

        Args:
            follow_order_id: 跟单订单ID
            follow_ratio: 新的跟单比例
            follow_amount: 新的跟单资金
            stop_loss: 新的止损比例

        Returns:
            是否更新成功
        """
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
        """获取引擎统计信息"""
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
            "running": self._running,
            "total_follows": self.total_follows,
            "monitored_signals": len(self._follow_map),
            "follows": follow_details,
        }
