"""
跟单订单引擎（CopyOrderEngine）
================================

核心职责：
1. 接收跟单引擎（FollowEngine）转发的跟单指令
2. 通过 BinanceRestClient 在跟单账户上执行市价单
3. 将成交结果写入数据库：
   - signal_follow_trades: 交易流水记录
   - signal_follow_positions: 持仓快照更新
   - signal_follow_events: 事件日志
   - signal_follow_orders: 更新统计字段

数据流：
    FollowEngine._process_follow()
        → CopyOrderEngine.execute_copy()
    → BinanceRestClient.place_order()  (同步下单，run_in_executor)
            → _record_success() / _record_failure()  (异步写 DB)

设计特点：
- 下单客户端按需创建并缓存（同一跟单账户复用同一客户端）
- 下单操作在线程池中执行（BinanceRestClient 是同步 httpx）
- 数据库写操作与下单解耦，失败不影响下单结果
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from quant_trading_system.core.config import settings
from quant_trading_system.core.snowflake import generate_snowflake_id
from quant_trading_system.models.follow import (
    SignalFollowEvent,
    SignalFollowOrder,
    SignalFollowPosition,
    SignalFollowTrade,
)
from quant_trading_system.services.database.database import get_db
from quant_trading_system.exchange_adapter.binance.binance_rest_client import (
    BinanceRestClient,
)

logger = logging.getLogger(__name__)


class CopyOrderEngine:
    """
    跟单订单引擎

    负责执行具体的跟单下单操作，并将结果记录到数据库。

    生命周期：
        engine = CopyOrderEngine()
        # 被 FollowEngine 调用，无需显式 start
        await engine.execute_copy(...)
        ...
        await engine.shutdown()  # 关闭所有客户端连接
    """

    def __init__(self):
        # 缓存下单客户端：{(api_key, account_type): BinanceRestClient}
        self._clients: dict[tuple[str, str], BinanceRestClient] = {}
        self._lock = asyncio.Lock()

        # 统计
        self._total_executed = 0
        self._total_failed = 0

    def _get_client(
        self,
        api_key: str,
        api_secret: str,
        account_type: str = "spot",
        testnet: bool = False,
    ) -> BinanceRestClient:
        """
        获取或创建下单客户端（按 API Key + 账户类型 缓存）

        开发环境自动使用 MockBinanceCopyTradeClient，不连接真实 Binance。

        Args:
            api_key: 跟单账户 API Key
            api_secret: 跟单账户 API Secret
            account_type: 账户类型
            testnet: 是否测试网

        Returns:
            BinanceRestClient 实例（或 Mock 实例）
        """
        cache_key = (api_key, account_type)
        if cache_key not in self._clients:
            if settings.is_development:
                from quant_trading_system.exchange_adapter.mock.mock_binance_copy_trade import (
                    MockBinanceCopyTradeClient,
                )
                self._clients[cache_key] = MockBinanceCopyTradeClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    account_type=account_type,
                    testnet=testnet,
                )
            else:
                self._clients[cache_key] = BinanceRestClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    market_type=account_type,
                    testnet=testnet,
                )
        return self._clients[cache_key]

    async def execute_copy(
        self,
        follow_order_id: int,
        user_id: int,
        signal_id: int,
        follower_api_key: str,
        follower_api_secret: str,
        account_type: str,
        testnet: bool,
        symbol: str,
        side: str,
        quantity: float,
        signal_price: float,
        original_order_id: str = "",
        signal_time: int = 0,
    ) -> Optional[dict[str, Any]]:
        """
        执行跟单下单

        Args:
            follow_order_id: 跟单订单ID
            user_id: 用户ID
            signal_id: 信号源ID
            follower_api_key: 跟单账户 API Key
            follower_api_secret: 跟单账户 API Secret
            account_type: 账户类型
            testnet: 是否测试网
            symbol: 交易对
            side: BUY/SELL
            quantity: 跟单数量
            signal_price: 信号源成交价格（用于计算滑点）
            original_order_id: 原始订单ID
            signal_time: 信号时间戳（毫秒）

        Returns:
            下单结果，失败返回 None
        """
        client = self._get_client(
            follower_api_key, follower_api_secret, account_type, testnet
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
            logger.info(
                f"✅ 跟单下单成功: follow_order_id={follow_order_id} "
                f"{symbol} {side} qty={quantity:.6f}, "
                f"订单ID={result.get('orderId')}"
            )

            # 异步记录成功结果到数据库
            await self._record_success(
                follow_order_id=follow_order_id,
                user_id=user_id,
                signal_id=signal_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                signal_price=signal_price,
                result=result,
                original_order_id=original_order_id,
                signal_time=signal_time,
            )

            return result

        except Exception as e:
            self._total_failed += 1
            logger.error(
                f"❌ 跟单下单失败: follow_order_id={follow_order_id} "
                f"{symbol} {side} qty={quantity:.6f}, 错误: {e}"
            )

            # 记录失败事件到数据库
            await self._record_failure(
                follow_order_id=follow_order_id,
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                error=str(e),
                original_order_id=original_order_id,
            )

            return None

    async def _record_success(
        self,
        follow_order_id: int,
        user_id: int,
        signal_id: int,
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
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)

                # 提取实际成交数据
                exec_qty = float(result.get("executedQty", quantity))
                cum_quote = float(result.get("cummulativeQuoteQty", 0))
                exec_price = (cum_quote / exec_qty) if exec_qty > 0 else signal_price
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
                    follow_order_id=follow_order_id,
                    user_id=user_id,
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
                self._update_position(
                    db, follow_order_id, user_id,
                    symbol, side_lower, exec_qty, exec_price, now,
                )

                # 3. 更新跟单订单统计
                follow_order = db.query(SignalFollowOrder).filter(
                    SignalFollowOrder.id == follow_order_id,
                ).first()
                if follow_order:
                    follow_order.total_trades = (follow_order.total_trades or 0) + 1
                    follow_order.update_time = now

                # 4. 记录成功事件
                event = SignalFollowEvent(
                    id=generate_snowflake_id(),
                    follow_order_id=follow_order_id,
                    user_id=user_id,
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
                        "source": "copy_order_engine",
                    },
                    event_time=now,
                    create_time=now,
                )
                db.add(event)

                db.commit()

            except Exception as e:
                db.rollback()
                logger.error(f"记录跟单成功到数据库失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    def _update_position(
        self,
        db: Session,
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
        # 查找现有持仓
        position = db.query(SignalFollowPosition).filter(
            SignalFollowPosition.follow_order_id == follow_order_id,
            SignalFollowPosition.symbol == symbol,
            SignalFollowPosition.status == "open",
        ).first()

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
        follow_order_id: int,
        user_id: int,
        symbol: str,
        side: str,
        quantity: float,
        error: str,
        original_order_id: str,
    ) -> None:
        """记录失败的跟单事件到数据库"""
        try:
            db: Session = next(get_db())
            try:
                now = datetime.now(timezone.utc)
                event = SignalFollowEvent(
                    id=generate_snowflake_id(),
                    follow_order_id=follow_order_id,
                    user_id=user_id,
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
                        "source": "copy_order_engine",
                    },
                    event_time=now,
                    create_time=now,
                )
                db.add(event)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"记录跟单失败事件到数据库失败: {e}", exc_info=True)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取数据库会话失败: {e}")

    async def shutdown(self) -> None:
        """关闭所有客户端连接"""
        async with self._lock:
            for key, client in self._clients.items():
                try:
                    client.close()
                except Exception as e:
                    logger.warning(f"关闭客户端失败: {key}, error={e}")
            self._clients.clear()

        logger.info(
            f"✅ 跟单订单引擎已关闭 "
            f"(执行: {self._total_executed}, 失败: {self._total_failed})"
        )

    @property
    def stats(self) -> dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "total_executed": self._total_executed,
            "total_failed": self._total_failed,
            "active_clients": len(self._clients),
        }
