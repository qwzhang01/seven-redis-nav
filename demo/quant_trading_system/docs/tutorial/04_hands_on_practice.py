"""
===============================================================================
第四章：实战练习 - 从零编写一个量化策略
===============================================================================

本章通过实际代码，带你完成一个完整的量化策略开发流程。
你将学会：
1. 获取和处理数据
2. 计算技术指标
3. 编写策略逻辑
4. 进行策略回测
5. 分析回测结果
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum
import random

# =============================================================================
# 1. 准备数据
# =============================================================================
print("=" * 70)
print("1. 准备模拟数据")
print("=" * 70)


def generate_mock_klines(
    symbol: str = "BTCUSDT",
    days: int = 365,
    interval: str = "1h"
) -> pd.DataFrame:
    """生成模拟K线数据
    
    使用几何布朗运动模型模拟价格走势
    """
    np.random.seed(42)
    
    # 计算数据点数量
    intervals_per_day = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24, "4h": 6, "1d": 1}
    n_points = days * intervals_per_day.get(interval, 24)
    
    # 生成时间序列
    start_time = datetime.now() - timedelta(days=days)
    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
    minutes = interval_minutes.get(interval, 60)
    timestamps = [start_time + timedelta(minutes=i * minutes) for i in range(n_points)]
    
    # 几何布朗运动参数
    initial_price = 30000.0
    mu = 0.0002      # 漂移率（趋势）
    sigma = 0.02     # 波动率
    
    # 生成收益率
    returns = np.random.normal(mu, sigma, n_points)
    
    # 生成价格序列
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # 生成 OHLCV 数据
    data = []
    for i, (ts, close) in enumerate(zip(timestamps, prices)):
        # 模拟日内波动
        volatility = sigma * close
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = prices[i-1] if i > 0 else close
        
        # 确保 OHLC 逻辑正确
        high = max(open_price, close, high)
        low = min(open_price, close, low)
        
        # 成交量与价格变化相关
        volume = 100 + abs(np.random.normal(0, 50)) * (1 + abs(returns[i]) * 10)
        
        data.append({
            "timestamp": ts,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
    
    df = pd.DataFrame(data)
    df["symbol"] = symbol
    return df


# 生成数据
klines = generate_mock_klines(symbol="BTCUSDT", days=365, interval="1h")
print(f"生成了 {len(klines)} 条K线数据")
print(f"时间范围: {klines['timestamp'].min()} 到 {klines['timestamp'].max()}")
print(f"\n数据预览:")
print(klines.tail(5).to_string(index=False))


# =============================================================================
# 2. 计算技术指标
# =============================================================================
print("\n" + "=" * 70)
print("2. 计算技术指标")
print("=" * 70)


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均线"""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均线"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """相对强弱指数"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD 指标
    
    返回：
    - macd_line: MACD 线（快线 - 慢线）
    - signal_line: 信号线（MACD 的 EMA）
    - histogram: 柱状图（MACD - 信号线）
    """
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2):
    """布林带
    
    返回：
    - middle: 中轨（SMA）
    - upper: 上轨（中轨 + n倍标准差）
    - lower: 下轨（中轨 - n倍标准差）
    """
    middle = calculate_sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return middle, upper, lower


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """平均真实波幅 (ATR)"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


# 计算所有指标
klines["sma_20"] = calculate_sma(klines["close"], 20)
klines["sma_50"] = calculate_sma(klines["close"], 50)
klines["ema_12"] = calculate_ema(klines["close"], 12)
klines["ema_26"] = calculate_ema(klines["close"], 26)
klines["rsi"] = calculate_rsi(klines["close"], 14)
klines["macd"], klines["macd_signal"], klines["macd_hist"] = calculate_macd(klines["close"])
klines["boll_middle"], klines["boll_upper"], klines["boll_lower"] = calculate_bollinger_bands(klines["close"])
klines["atr"] = calculate_atr(klines["high"], klines["low"], klines["close"])

print(f"\n添加的指标列：")
print(f"  - SMA(20), SMA(50): 移动平均线")
print(f"  - EMA(12), EMA(26): 指数移动平均线")
print(f"  - RSI(14): 相对强弱指数")
print(f"  - MACD, MACD Signal, MACD Hist: MACD指标")
print(f"  - Bollinger Bands: 布林带")
print(f"  - ATR(14): 平均真实波幅")

print(f"\n最新数据的指标值：")
latest = klines.iloc[-1]
print(f"  价格: ${latest['close']:,.2f}")
print(f"  SMA(20): ${latest['sma_20']:,.2f}")
print(f"  SMA(50): ${latest['sma_50']:,.2f}")
print(f"  RSI(14): {latest['rsi']:.2f}")
print(f"  MACD: {latest['macd']:.2f}")
print(f"  ATR(14): ${latest['atr']:,.2f}")


# =============================================================================
# 3. 编写策略
# =============================================================================
print("\n" + "=" * 70)
print("3. 编写交易策略")
print("=" * 70)


class Signal(Enum):
    """交易信号"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    side: str
    price: float
    quantity: float
    value: float
    pnl: float = 0.0


class BaseStrategy:
    """策略基类"""
    
    def __init__(self, name: str, initial_capital: float = 10000.0):
        self.name = name
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0.0  # 持仓数量
        self.position_value = 0.0  # 持仓价值
        self.entry_price = 0.0  # 入场价格
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
    
    def generate_signal(self, data: pd.Series) -> Signal:
        """生成交易信号（子类实现）"""
        raise NotImplementedError
    
    def calculate_position_size(self, price: float) -> float:
        """计算仓位大小"""
        # 简单策略：全仓买入
        return self.capital / price
    
    def execute_buy(self, timestamp: datetime, price: float):
        """执行买入"""
        if self.capital <= 0:
            return
        
        quantity = self.calculate_position_size(price)
        cost = quantity * price * 1.001  # 0.1% 手续费
        
        if cost <= self.capital:
            self.capital -= cost
            self.position += quantity
            self.entry_price = price
            
            self.trades.append(Trade(
                timestamp=timestamp,
                side="buy",
                price=price,
                quantity=quantity,
                value=cost
            ))
    
    def execute_sell(self, timestamp: datetime, price: float):
        """执行卖出"""
        if self.position <= 0:
            return
        
        value = self.position * price * 0.999  # 0.1% 手续费
        pnl = value - self.position * self.entry_price
        
        self.capital += value
        
        self.trades.append(Trade(
            timestamp=timestamp,
            side="sell",
            price=price,
            quantity=self.position,
            value=value,
            pnl=pnl
        ))
        
        self.position = 0.0
        self.entry_price = 0.0
    
    def get_equity(self, current_price: float) -> float:
        """计算当前净值"""
        return self.capital + self.position * current_price


class MACrossStrategy(BaseStrategy):
    """均线交叉策略
    
    策略逻辑：
    - 快线上穿慢线 → 买入（金叉）
    - 快线下穿慢线 → 卖出（死叉）
    """
    
    def __init__(self, fast_period: int = 20, slow_period: int = 50, **kwargs):
        super().__init__(name="MA Cross Strategy", **kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signal(self, data: pd.Series, prev_data: pd.Series) -> Signal:
        fast_ma = data[f"sma_{self.fast_period}"]
        slow_ma = data[f"sma_{self.slow_period}"]
        prev_fast_ma = prev_data[f"sma_{self.fast_period}"]
        prev_slow_ma = prev_data[f"sma_{self.slow_period}"]
        
        if pd.isna(fast_ma) or pd.isna(slow_ma):
            return Signal.HOLD
        
        # 金叉：快线从下方穿过慢线
        if fast_ma > slow_ma and prev_fast_ma <= prev_slow_ma:
            return Signal.BUY
        
        # 死叉：快线从上方穿过慢线
        if fast_ma < slow_ma and prev_fast_ma >= prev_slow_ma:
            return Signal.SELL
        
        return Signal.HOLD


class RSIStrategy(BaseStrategy):
    """RSI 策略
    
    策略逻辑：
    - RSI < 30 → 超卖，买入
    - RSI > 70 → 超买，卖出
    """
    
    def __init__(self, oversold: float = 30, overbought: float = 70, **kwargs):
        super().__init__(name="RSI Strategy", **kwargs)
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, data: pd.Series, prev_data: pd.Series) -> Signal:
        rsi = data["rsi"]
        prev_rsi = prev_data["rsi"]
        
        if pd.isna(rsi):
            return Signal.HOLD
        
        # RSI 从超卖区域回升
        if rsi > self.oversold and prev_rsi <= self.oversold:
            return Signal.BUY
        
        # RSI 从超买区域回落
        if rsi < self.overbought and prev_rsi >= self.overbought:
            return Signal.SELL
        
        return Signal.HOLD


class MACDStrategy(BaseStrategy):
    """MACD 策略
    
    策略逻辑：
    - MACD 线上穿信号线 → 买入
    - MACD 线下穿信号线 → 卖出
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="MACD Strategy", **kwargs)
    
    def generate_signal(self, data: pd.Series, prev_data: pd.Series) -> Signal:
        macd = data["macd"]
        signal = data["macd_signal"]
        prev_macd = prev_data["macd"]
        prev_signal = prev_data["macd_signal"]
        
        if pd.isna(macd) or pd.isna(signal):
            return Signal.HOLD
        
        # MACD 金叉
        if macd > signal and prev_macd <= prev_signal:
            return Signal.BUY
        
        # MACD 死叉
        if macd < signal and prev_macd >= prev_signal:
            return Signal.SELL
        
        return Signal.HOLD


print("定义了以下策略：")
print("  1. MACrossStrategy: 均线交叉策略")
print("  2. RSIStrategy: RSI超买超卖策略")
print("  3. MACDStrategy: MACD交叉策略")


# =============================================================================
# 4. 回测引擎
# =============================================================================
print("\n" + "=" * 70)
print("4. 运行回测")
print("=" * 70)


class Backtester:
    """回测引擎"""
    
    def __init__(self, data: pd.DataFrame, strategy: BaseStrategy):
        self.data = data.copy()
        self.strategy = strategy
    
    def run(self) -> Dict:
        """运行回测"""
        print(f"\n运行策略: {self.strategy.name}")
        print("-" * 50)
        
        for i in range(1, len(self.data)):
            current = self.data.iloc[i]
            previous = self.data.iloc[i - 1]
            
            # 生成信号
            signal = self.strategy.generate_signal(current, previous)
            
            # 执行交易
            if signal == Signal.BUY and self.strategy.position == 0:
                self.strategy.execute_buy(current["timestamp"], current["close"])
            elif signal == Signal.SELL and self.strategy.position > 0:
                self.strategy.execute_sell(current["timestamp"], current["close"])
            
            # 记录净值
            equity = self.strategy.get_equity(current["close"])
            self.strategy.equity_curve.append(equity)
        
        # 计算绩效
        return self.calculate_performance()
    
    def calculate_performance(self) -> Dict:
        """计算绩效指标"""
        equity = np.array(self.strategy.equity_curve)
        initial = self.strategy.initial_capital
        
        # 总收益率
        total_return = (equity[-1] - initial) / initial * 100
        
        # 计算每日收益率
        returns = np.diff(equity) / equity[:-1]
        
        # 年化收益率（假设每小时一根K线）
        hours_per_year = 365 * 24
        annual_return = (1 + total_return / 100) ** (hours_per_year / len(equity)) - 1
        annual_return *= 100
        
        # 最大回撤
        peak = np.maximum.accumulate(equity)
        drawdown = (peak - equity) / peak * 100
        max_drawdown = np.max(drawdown)
        
        # 夏普比率（年化）
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(hours_per_year)
        else:
            sharpe_ratio = 0.0
        
        # 交易统计
        trades = self.strategy.trades
        n_trades = len([t for t in trades if t.side == "sell"])
        
        if n_trades > 0:
            winning_trades = len([t for t in trades if t.side == "sell" and t.pnl > 0])
            win_rate = winning_trades / n_trades * 100
            
            profits = sum(t.pnl for t in trades if t.pnl > 0)
            losses = abs(sum(t.pnl for t in trades if t.pnl < 0))
            profit_factor = profits / losses if losses > 0 else float("inf")
        else:
            win_rate = 0.0
            profit_factor = 0.0
        
        return {
            "strategy_name": self.strategy.name,
            "initial_capital": initial,
            "final_equity": equity[-1],
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "total_trades": n_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
        }


def print_performance(result: Dict):
    """打印绩效报告"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                         回测绩效报告                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  策略名称: {result['strategy_name']:<54} ║
╠══════════════════════════════════════════════════════════════════════╣
║  资金与收益                                                          ║
║    初始资金:     ${result['initial_capital']:>12,.2f}                              ║
║    最终净值:     ${result['final_equity']:>12,.2f}                              ║
║    总收益率:     {result['total_return']:>12.2f}%                               ║
║    年化收益率:   {result['annual_return']:>12.2f}%                               ║
╠══════════════════════════════════════════════════════════════════════╣
║  风险指标                                                            ║
║    最大回撤:     {result['max_drawdown']:>12.2f}%                               ║
║    夏普比率:     {result['sharpe_ratio']:>12.2f}                                ║
╠══════════════════════════════════════════════════════════════════════╣
║  交易统计                                                            ║
║    交易次数:     {result['total_trades']:>12}                                ║
║    胜率:         {result['win_rate']:>12.2f}%                               ║
║    盈亏比:       {result['profit_factor']:>12.2f}                                ║
╚══════════════════════════════════════════════════════════════════════╝
""")


# 运行多个策略的回测
strategies = [
    MACrossStrategy(fast_period=20, slow_period=50, initial_capital=10000),
    RSIStrategy(oversold=30, overbought=70, initial_capital=10000),
    MACDStrategy(initial_capital=10000),
]

results = []
for strategy in strategies:
    backtester = Backtester(klines, strategy)
    result = backtester.run()
    results.append(result)
    print_performance(result)


# =============================================================================
# 5. 策略对比分析
# =============================================================================
print("\n" + "=" * 70)
print("5. 策略对比分析")
print("=" * 70)

print(f"""
┌────────────────────┬────────────┬────────────┬────────────┬────────────┐
│       策略         │  总收益率  │ 最大回撤   │  夏普比率  │   胜率     │
├────────────────────┼────────────┼────────────┼────────────┼────────────┤""")

for r in results:
    name = r['strategy_name'][:18]
    print(f"│ {name:<18} │ {r['total_return']:>9.2f}% │ {r['max_drawdown']:>9.2f}% │ {r['sharpe_ratio']:>10.2f} │ {r['win_rate']:>9.2f}% │")

print(f"""└────────────────────┴────────────┴────────────┴────────────┴────────────┘

策略评估要点：
1. 总收益率：越高越好，但要结合风险看
2. 最大回撤：越低越好，代表最坏情况下的亏损
3. 夏普比率：> 1 较好，> 2 优秀，代表风险调整后收益
4. 胜率：并非越高越好，要结合盈亏比

⚠️ 注意事项：
- 这是模拟数据的回测结果
- 实盘交易会有滑点、延迟等额外成本
- 历史表现不代表未来收益
- 需要进行样本外测试验证策略
""")


# =============================================================================
# 6. 面试实战问题
# =============================================================================
print("\n" + "=" * 70)
print("6. 面试实战问题")
print("=" * 70)

interview_questions = """
面试官可能问的问题：

Q1: 请描述你写的这个策略的逻辑？
A: "我实现了一个均线交叉策略：
   - 使用 20 日和 50 日均线
   - 当短期均线上穿长期均线时（金叉），发出买入信号
   - 当短期均线下穿长期均线时（死叉），发出卖出信号
   - 这是一个趋势跟踪策略，适合有明显趋势的市场"

Q2: 这个策略的优缺点是什么？
A: "优点：
   - 逻辑简单，容易理解和实现
   - 在趋势明显的市场表现较好
   - 能够捕捉大的趋势行情
   
   缺点：
   - 在震荡市场中会频繁交易，产生亏损
   - 信号滞后，可能错过最佳入场点
   - 对参数敏感，需要优化"

Q3: 如何优化这个策略？
A: "可以从以下几个方面优化：
   1. 参数优化：使用网格搜索或遗传算法寻找最优参数
   2. 添加过滤条件：结合成交量、波动率等指标
   3. 动态止损：使用 ATR 设置动态止损位
   4. 仓位管理：根据信号强度调整仓位
   5. 市场状态识别：判断趋势/震荡市场，选择性交易"

Q4: 如何避免过拟合？
A: "1. 使用足够长的历史数据
   2. 将数据分为训练集和测试集
   3. 保持策略逻辑简单，参数不宜过多
   4. 进行滚动回测
   5. 理解策略背后的逻辑，而非纯粹曲线拟合"

Q5: 回测结果和实盘会有什么差异？
A: "主要差异包括：
   1. 滑点：实盘成交价格可能与预期不同
   2. 延迟：订单从发出到成交有时间延迟
   3. 流动性：大单可能无法以预期价格成交
   4. 市场冲击：自己的交易可能影响价格
   5. 交易所限制：API 频率限制、断线等"

Q6: 这个项目中你遇到的最大挑战是什么？
A: 准备一个具体的例子，如：
   "最大的挑战是优化行情数据处理的延迟。
   最初直接处理 Tick 数据时延迟较高，后来通过：
   1. 使用异步处理
   2. 引入消息队列做缓冲
   3. 优化数据结构减少内存复制
   最终将延迟从 50ms 降低到 5ms 以内"
"""
print(interview_questions)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("实战练习完成！")
    print("你已经学会了完整的量化策略开发流程")
    print("=" * 70)
