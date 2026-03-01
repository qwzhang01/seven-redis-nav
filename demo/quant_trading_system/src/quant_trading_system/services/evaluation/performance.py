"""
绩效分析器
==========

提供详细的回测绩效分析。
从 backtest 模块迁移到 evaluation 模块，
作为最终报告生成器，与 StrategyEvaluator 配合使用。
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from quant_trading_system.services.backtest.backtest_engine import BacktestResult


@dataclass
class PerformanceMetrics:
    """绩效指标"""

    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_return: float = 0.0

    # 风险指标
    volatility: float = 0.0
    downside_volatility: float = 0.0
    max_drawdown: float = 0.0
    avg_drawdown: float = 0.0

    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # 交易指标
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win_loss_ratio: float = 0.0
    expectancy: float = 0.0

    # 其他
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0


class PerformanceAnalyzer:
    """
    绩效分析器

    提供详细的策略绩效分析
    """

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        """
        Args:
            risk_free_rate: 无风险利率（年化）
        """
        self.risk_free_rate = risk_free_rate

    def analyze(self, result: BacktestResult) -> PerformanceMetrics:
        """
        分析回测结果

        Args:
            result: 回测结果

        Returns:
            绩效指标
        """
        metrics = PerformanceMetrics()

        if not result.equity_curve or len(result.equity_curve) < 2:
            return metrics

        equity = np.array(result.equity_curve)
        returns = np.diff(equity) / equity[:-1]

        # 基本收益指标
        metrics.total_return = result.total_return
        metrics.annual_return = result.annual_return

        if result.duration_days > 0:
            months = result.duration_days / 30
            if months > 0:
                metrics.monthly_return = (1 + result.total_return) ** (1 / months) - 1

        # 波动率
        metrics.volatility = float(np.std(returns) * np.sqrt(252))

        # 下行波动率
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            metrics.downside_volatility = float(
                np.std(negative_returns) * np.sqrt(252)
            )

        # 回撤分析
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak
        metrics.max_drawdown = float(np.max(drawdown))
        metrics.avg_drawdown = float(np.mean(drawdown))

        # 夏普比率
        excess_return = metrics.annual_return - self.risk_free_rate
        if metrics.volatility > 0:
            metrics.sharpe_ratio = excess_return / metrics.volatility

        # 索提诺比率
        if metrics.downside_volatility > 0:
            metrics.sortino_ratio = excess_return / metrics.downside_volatility

        # 卡玛比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown

        # 交易指标
        metrics.win_rate = result.win_rate
        metrics.profit_factor = result.profit_factor

        if result.avg_loss > 0:
            metrics.avg_win_loss_ratio = result.avg_win / result.avg_loss

        # 期望值
        metrics.expectancy = (
            metrics.win_rate * result.avg_win -
            (1 - metrics.win_rate) * result.avg_loss
        )

        # 高阶矩
        if len(returns) > 3:
            metrics.skewness = float(self._calculate_skewness(returns))
            metrics.kurtosis = float(self._calculate_kurtosis(returns))

        # VaR 和 CVaR
        if len(returns) > 0:
            metrics.var_95 = float(np.percentile(returns, 5))
            metrics.cvar_95 = float(np.mean(returns[returns <= metrics.var_95]))

        return metrics

    @staticmethod
    def _calculate_skewness(returns: np.ndarray) -> float:
        """计算偏度"""
        n = len(returns)
        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        skew = (n / ((n - 1) * (n - 2))) * np.sum(((returns - mean) / std) ** 3)
        return skew

    @staticmethod
    def _calculate_kurtosis(returns: np.ndarray) -> float:
        """计算峰度"""
        n = len(returns)
        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        kurt = (
            (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3)) *
            np.sum(((returns - mean) / std) ** 4) -
            3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
        )
        return kurt

    def generate_report(self, result: BacktestResult) -> dict[str, Any]:
        """
        生成分析报告

        Args:
            result: 回测结果

        Returns:
            报告数据
        """
        metrics = self.analyze(result)

        report = {
            "summary": {
                "strategy_name": result.strategy_name,
                "duration_days": result.duration_days,
                "initial_capital": result.initial_capital,
                "final_capital": result.final_capital,
            },
            "returns": {
                "total_return": f"{metrics.total_return:.2%}",
                "annual_return": f"{metrics.annual_return:.2%}",
                "monthly_return": f"{metrics.monthly_return:.2%}",
            },
            "risk": {
                "volatility": f"{metrics.volatility:.2%}",
                "max_drawdown": f"{metrics.max_drawdown:.2%}",
                "var_95": f"{metrics.var_95:.2%}",
                "cvar_95": f"{metrics.cvar_95:.2%}",
            },
            "risk_adjusted": {
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "sortino_ratio": f"{metrics.sortino_ratio:.2f}",
                "calmar_ratio": f"{metrics.calmar_ratio:.2f}",
            },
            "trading": {
                "total_trades": result.total_trades,
                "win_rate": f"{metrics.win_rate:.2%}",
                "profit_factor": f"{metrics.profit_factor:.2f}",
                "avg_win_loss_ratio": f"{metrics.avg_win_loss_ratio:.2f}",
                "expectancy": f"{metrics.expectancy:.2f}",
            },
            "costs": {
                "total_commission": result.total_commission,
                "total_slippage": result.total_slippage,
            },
        }

        return report

    def compare_strategies(
        self,
        results: list[BacktestResult]
    ) -> list[dict[str, Any]]:
        """
        比较多个策略

        Args:
            results: 回测结果列表

        Returns:
            比较数据
        """
        comparisons = []

        for result in results:
            metrics = self.analyze(result)
            comparisons.append({
                "strategy_name": result.strategy_name,
                "total_return": metrics.total_return,
                "annual_return": metrics.annual_return,
                "max_drawdown": metrics.max_drawdown,
                "sharpe_ratio": metrics.sharpe_ratio,
                "win_rate": metrics.win_rate,
                "profit_factor": metrics.profit_factor,
                "total_trades": result.total_trades,
            })

        # 按夏普比率排序
        comparisons.sort(key=lambda x: x["sharpe_ratio"], reverse=True)

        return comparisons
