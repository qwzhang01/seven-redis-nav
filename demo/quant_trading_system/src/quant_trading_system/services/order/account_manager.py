"""
账户管理器
==========

统一的账户余额管理，适用于回测/模拟/实盘三种模式。
负责：
- 余额更新（买入扣款、卖出入账）
- 权益计算
- 资金校验
"""

from datetime import datetime
from typing import Any

import structlog

from quant_trading_system.core.enums import OrderSide
from quant_trading_system.models.account import Account, Balance
from quant_trading_system.core.enums import MarketType
from quant_trading_system.models.trading import Trade

logger = structlog.get_logger(__name__)


class AccountManager:
    """
    统一账户管理器

    负责所有模式下的账户余额更新和权益计算
    """

    def __init__(self, account: Account | None = None) -> None:
        self._account = account

    def create_account(
        self,
        initial_capital: float,
        account_id: str = "default",
        account_type: MarketType = MarketType.SPOT,
    ) -> Account:
        """
        创建账户

        Args:
            initial_capital: 初始资金
            account_id: 账户ID
            account_type: 账户类型

        Returns:
            账户对象
        """
        usdt_balance = Balance(
            asset="USDT",
            free=initial_capital,
            locked=0.0,
            total=initial_capital,
        )

        self._account = Account(
            id=account_id,
            type=account_type,
            balances={"USDT": usdt_balance},
            total_balance=initial_capital,
            available_balance=initial_capital,
            margin_balance=initial_capital,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            updated_at=datetime.now(),
        )

        logger.info(
            "账户创建",
            account_id=account_id,
            initial_capital=f"{initial_capital:,.2f}",
        )

        return self._account

    def set_account(self, account: Account) -> None:
        """设置账户"""
        self._account = account

    def update_from_trade(self, trade: Trade) -> None:
        """
        根据成交更新账户余额

        Args:
            trade: 成交记录
        """
        if self._account is None:
            logger.warning("账户未设置，跳过余额更新")
            return

        cost = trade.quantity * trade.price

        if trade.side == OrderSide.BUY:
            # 买入：扣除 USDT 余额（成交金额 + 手续费）
            total_cost = cost + trade.commission
            if "USDT" in self._account.balances:
                usdt = self._account.balances["USDT"]
                usdt.free -= total_cost
                usdt.total = usdt.free + usdt.locked
                self._account.total_balance -= total_cost
                self._account.available_balance = usdt.free
        else:
            # 卖出：增加 USDT 余额（成交金额 - 手续费）
            net_proceeds = cost - trade.commission
            if "USDT" in self._account.balances:
                usdt = self._account.balances["USDT"]
                usdt.free += net_proceeds
                usdt.total = usdt.free + usdt.locked
                self._account.total_balance += net_proceeds
                self._account.available_balance = usdt.free

        self._account.updated_at = datetime.now()

    def calculate_equity(self, total_position_value: float) -> float:
        """
        计算总权益

        Args:
            total_position_value: 总持仓市值

        Returns:
            总权益
        """
        if self._account is None:
            return 0.0

        return self._account.total_balance + total_position_value

    def has_sufficient_balance(self, amount: float) -> bool:
        """
        检查余额是否足够

        Args:
            amount: 所需金额

        Returns:
            是否足够
        """
        if self._account is None:
            return False

        return self._account.available_balance >= amount

    @property
    def account(self) -> Account | None:
        """获取账户"""
        return self._account

    @property
    def available_balance(self) -> float:
        """获取可用余额"""
        if self._account is None:
            return 0.0
        return self._account.available_balance

    @property
    def total_balance(self) -> float:
        """获取总余额"""
        if self._account is None:
            return 0.0
        return self._account.total_balance

    def reset(self) -> None:
        """重置账户状态（用于回测重新运行）"""
        self._account = None
        logger.debug("账户管理器已重置")

    @property
    def stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if self._account is None:
            return {"account": None}

        return {
            "account_id": self._account.id,
            "total_balance": self._account.total_balance,
            "available_balance": self._account.available_balance,
            "realized_pnl": self._account.realized_pnl,
        }
