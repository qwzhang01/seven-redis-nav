"""
===============================================================================
第二章：量化交易核心概念
===============================================================================

本章介绍量化交易的基本概念，帮助你理解这个项目的业务背景。
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict
from datetime import datetime, timedelta

# =============================================================================
# 1. 什么是量化交易？
# =============================================================================
print("=" * 70)
print("1. 什么是量化交易？")
print("=" * 70)

intro = """
量化交易 (Quantitative Trading) 是指：
- 使用数学模型和计算机程序来分析市场
- 根据预设的规则自动执行交易
- 减少人为情绪的影响，提高交易的一致性

量化交易的优势：
1. 纪律性：严格按照策略执行，不受情绪影响
2. 速度：毫秒级响应，比人工快很多
3. 回测：可以用历史数据验证策略
4. 多元化：同时监控多个市场、多个品种

常见的量化策略类型：
- 趋势跟踪：顺势而为，涨了买，跌了卖
- 均值回归：价格偏离均值后会回归
- 套利策略：利用价格差异获利
- 高频交易：毫秒级的快速交易
- 机器学习：用 AI 预测市场走势
"""
print(intro)


# =============================================================================
# 2. 行情数据结构
# =============================================================================
print("\n" + "=" * 70)
print("2. 行情数据结构")
print("=" * 70)


@dataclass
class Tick:
    """Tick 数据 - 逐笔成交数据
    
    这是最细粒度的行情数据，每笔交易产生一个 Tick。
    高频交易策略通常基于 Tick 数据。
    """
    symbol: str          # 交易对，如 "BTCUSDT"（比特币/美元）
    price: float         # 成交价格
    volume: float        # 成交数量（多少个币）
    amount: float        # 成交金额（price * volume）
    timestamp: datetime  # 成交时间
    trade_id: str        # 交易ID


@dataclass  
class Bar:
    """K线/蜡烛图数据 - OHLCV
    
    K线是最常用的行情数据格式，将一段时间内的交易汇总。
    
    一根 K线 的组成：
    
        最高价 (High)
           │
        ───┬───  ← 上影线
           │
        ┌──┴──┐
        │     │  ← 实体（红色/绿色）
        │     │     - 收盘价 > 开盘价：阳线（红色），上涨
        │     │     - 收盘价 < 开盘价：阴线（绿色），下跌
        └──┬──┘
           │
        ───┴───  ← 下影线
           │
        最低价 (Low)
    """
    symbol: str
    interval: str        # 周期：1m, 5m, 15m, 1h, 4h, 1d 等
    open: float          # 开盘价：该周期第一笔成交价
    high: float          # 最高价：该周期内最高成交价
    low: float           # 最低价：该周期内最低成交价
    close: float         # 收盘价：该周期最后一笔成交价
    volume: float        # 成交量：该周期内总成交数量
    turnover: float      # 成交额：该周期内总成交金额
    timestamp: datetime  # 该 K线 的开始时间


@dataclass
class OrderBook:
    """订单簿/盘口数据
    
    显示当前市场上买卖双方的挂单情况。
    
    买盘（Bids）：想要买入的订单，按价格从高到低排列
    卖盘（Asks）：想要卖出的订单，按价格从低到高排列
    
    示例：
    卖5: 50050  x 1.5   ← 有人想以 50050 的价格卖出 1.5 个币
    卖4: 50040  x 2.0
    卖3: 50030  x 0.8
    卖2: 50020  x 1.2
    卖1: 50010  x 3.0   ← 最低卖价（卖一）
    ─────────────────
    买1: 50000  x 2.5   ← 最高买价（买一）
    买2: 49990  x 1.8
    买3: 49980  x 4.0
    买4: 49970  x 2.2
    买5: 49960  x 1.0
    
    价差 (Spread) = 卖一价 - 买一价 = 50010 - 50000 = 10
    """
    symbol: str
    bids: List[tuple]    # 买盘：[(价格, 数量), ...]
    asks: List[tuple]    # 卖盘：[(价格, 数量), ...]
    timestamp: datetime


# 创建示例数据
example_bar = Bar(
    symbol="BTCUSDT",
    interval="1h",
    open=49000.0,
    high=51000.0,
    low=48500.0,
    close=50500.0,
    volume=1000.0,
    turnover=50000000.0,
    timestamp=datetime.now()
)

print(f"""
K线示例：
  交易对: {example_bar.symbol}
  周期: {example_bar.interval}
  开盘价: ${example_bar.open:,.2f}
  最高价: ${example_bar.high:,.2f}
  最低价: ${example_bar.low:,.2f}
  收盘价: ${example_bar.close:,.2f}
  成交量: {example_bar.volume} BTC
  涨跌幅: {(example_bar.close - example_bar.open) / example_bar.open * 100:.2f}%
""")


# =============================================================================
# 3. 订单与交易
# =============================================================================
print("\n" + "=" * 70)
print("3. 订单与交易")
print("=" * 70)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"       # 市价单：以当前市场最优价立即成交
    LIMIT = "limit"         # 限价单：指定价格，等待成交
    STOP_LOSS = "stop_loss" # 止损单：价格触发后变成市价单
    TAKE_PROFIT = "take_profit"  # 止盈单


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"    # 买入（做多）
    SELL = "sell"  # 卖出（做空/平仓）


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"          # 等待提交
    SUBMITTED = "submitted"      # 已提交到交易所
    PARTIAL_FILLED = "partial"   # 部分成交
    FILLED = "filled"            # 完全成交
    CANCELLED = "cancelled"      # 已取消
    REJECTED = "rejected"        # 被拒绝


@dataclass
class Order:
    """订单
    
    订单是交易的指令，告诉交易所你想买/卖什么、多少、什么价格。
    """
    order_id: str            # 订单ID
    symbol: str              # 交易对
    side: OrderSide          # 买/卖
    order_type: OrderType    # 订单类型
    price: float             # 价格（限价单需要）
    quantity: float          # 数量
    filled_quantity: float   # 已成交数量
    status: OrderStatus      # 订单状态
    created_at: datetime     # 创建时间


order_explanation = """
订单类型详解：

1. 市价单 (Market Order)
   - 以当前市场最优价格立即成交
   - 优点：保证成交
   - 缺点：成交价格不确定，可能有滑点
   - 适用：紧急买卖，流动性好的市场

2. 限价单 (Limit Order)
   - 指定价格，只有达到或更优时才成交
   - 优点：控制成交价格
   - 缺点：可能不成交
   - 适用：不急的交易，想要好价格

3. 止损单 (Stop Loss)
   - 价格触发条件后自动卖出
   - 用于限制亏损
   - 例：50000 买入，设置 48000 止损

4. 止盈单 (Take Profit)  
   - 价格触发条件后自动卖出
   - 用于锁定利润
   - 例：50000 买入，设置 55000 止盈
"""
print(order_explanation)


# =============================================================================
# 4. 仓位与账户
# =============================================================================
print("\n" + "=" * 70)
print("4. 仓位与账户")
print("=" * 70)


@dataclass
class Position:
    """持仓
    
    仓位代表你当前持有的资产。
    """
    symbol: str              # 交易对
    side: str                # 多/空 (long/short)
    quantity: float          # 持仓数量
    entry_price: float       # 入场均价
    current_price: float     # 当前价格
    unrealized_pnl: float    # 未实现盈亏
    realized_pnl: float      # 已实现盈亏
    
    @property
    def pnl_percent(self) -> float:
        """盈亏百分比"""
        if self.entry_price == 0:
            return 0.0
        if self.side == "long":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - self.current_price) / self.entry_price * 100


# 示例仓位
position = Position(
    symbol="BTCUSDT",
    side="long",
    quantity=1.0,
    entry_price=50000.0,
    current_price=52000.0,
    unrealized_pnl=2000.0,
    realized_pnl=0.0
)

print(f"""
持仓示例：
  交易对: {position.symbol}
  方向: {position.side} (做多)
  数量: {position.quantity} BTC
  入场价: ${position.entry_price:,.2f}
  当前价: ${position.current_price:,.2f}
  未实现盈亏: ${position.unrealized_pnl:,.2f}
  盈亏比例: {position.pnl_percent:.2f}%
""")


# =============================================================================
# 5. 技术指标简介
# =============================================================================
print("\n" + "=" * 70)
print("5. 技术指标简介")
print("=" * 70)

# 模拟价格数据
np.random.seed(42)
prices = 50000 + np.cumsum(np.random.randn(100) * 100)


def sma(data: np.ndarray, period: int) -> np.ndarray:
    """简单移动平均线 (Simple Moving Average)
    
    计算最近 period 个价格的平均值。
    
    用途：
    - 判断趋势方向
    - 价格在 SMA 之上 → 上涨趋势
    - 价格在 SMA 之下 → 下跌趋势
    
    常用参数：
    - SMA(20)：短期趋势
    - SMA(50)：中期趋势
    - SMA(200)：长期趋势
    """
    result = np.full_like(data, np.nan)
    for i in range(period - 1, len(data)):
        result[i] = np.mean(data[i - period + 1:i + 1])
    return result


def ema(data: np.ndarray, period: int) -> np.ndarray:
    """指数移动平均线 (Exponential Moving Average)
    
    与 SMA 类似，但给近期价格更高的权重，对价格变化更敏感。
    
    计算公式：
    EMA[t] = price[t] * k + EMA[t-1] * (1 - k)
    其中 k = 2 / (period + 1)
    """
    result = np.zeros_like(data)
    k = 2 / (period + 1)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    """相对强弱指数 (Relative Strength Index)
    
    衡量价格上涨和下跌的相对强度。
    
    取值范围：0 - 100
    - RSI > 70：超买区域，可能要下跌
    - RSI < 30：超卖区域，可能要上涨
    
    常用于判断买卖时机。
    """
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.zeros(len(data))
    avg_loss = np.zeros(len(data))
    
    # 初始平均
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])
    
    # 平滑计算
    for i in range(period + 1, len(data)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
    rsi_values = 100 - (100 / (1 + rs))
    rsi_values[:period] = np.nan
    
    return rsi_values


# 计算指标
sma_20 = sma(prices, 20)
ema_20 = ema(prices, 20)
rsi_14 = rsi(prices, 14)

print(f"""
技术指标计算示例（使用 100 个价格数据）：

最新价格: ${prices[-1]:,.2f}

移动平均线：
  SMA(20): ${sma_20[-1]:,.2f}
  EMA(20): ${ema_20[-1]:,.2f}
  
  趋势判断：
  - 价格 > SMA(20): {'是 ✓ 上涨趋势' if prices[-1] > sma_20[-1] else '否 ✗ 下跌趋势'}

RSI(14): {rsi_14[-1]:.2f}
  - 状态: {'超买区域 ⚠️' if rsi_14[-1] > 70 else '超卖区域 ⚠️' if rsi_14[-1] < 30 else '正常区域 ✓'}
""")

indicators_explanation = """
常用技术指标分类：

1. 趋势指标 (Trend Indicators)
   - MA/EMA：移动平均线
   - MACD：趋势和动量的结合
   - 布林带：价格波动范围

2. 动量指标 (Momentum Indicators)
   - RSI：相对强弱
   - KDJ：随机指标
   - CCI：商品通道指数

3. 成交量指标 (Volume Indicators)
   - OBV：能量潮
   - VWAP：成交量加权平均价

4. 波动率指标 (Volatility Indicators)
   - ATR：平均真实波幅
   - 标准差
"""
print(indicators_explanation)


# =============================================================================
# 6. 回测概念
# =============================================================================
print("\n" + "=" * 70)
print("6. 回测概念")
print("=" * 70)

backtest_explanation = """
什么是回测 (Backtesting)？

回测是用历史数据测试交易策略的过程：
1. 获取历史行情数据
2. 模拟执行交易策略
3. 计算交易结果和绩效指标

为什么需要回测？
- 在真金白银交易之前验证策略
- 了解策略的风险和收益特征
- 优化策略参数

回测的注意事项：
1. 避免未来函数：不能使用未来的数据做决策
2. 考虑交易成本：手续费、滑点等
3. 避免过拟合：策略不能过度适应历史数据
4. 样本外测试：用策略没见过的数据测试

关键绩效指标：

1. 总收益率 (Total Return)
   策略的总盈利百分比

2. 年化收益率 (Annual Return)  
   换算成年化的收益率，便于比较

3. 最大回撤 (Maximum Drawdown)
   从最高点到最低点的最大亏损
   - 衡量风险的重要指标
   - 回撤越小，策略越稳定

4. 夏普比率 (Sharpe Ratio)
   收益与风险的比值
   - > 1：较好
   - > 2：优秀
   - > 3：极好

5. 胜率 (Win Rate)
   盈利交易占总交易的比例

6. 盈亏比 (Profit Factor)
   总盈利 / 总亏损
"""
print(backtest_explanation)


# 简单回测示例
def simple_backtest(prices: np.ndarray, sma_period: int = 20):
    """简单的均线策略回测
    
    策略逻辑：
    - 价格上穿均线 → 买入
    - 价格下穿均线 → 卖出
    """
    sma_values = sma(prices, sma_period)
    
    position = 0  # 0: 空仓, 1: 持仓
    cash = 10000.0
    holdings = 0.0
    trades = []
    
    for i in range(sma_period, len(prices)):
        if np.isnan(sma_values[i]):
            continue
            
        # 买入信号：价格从下方穿过均线
        if prices[i] > sma_values[i] and prices[i-1] <= sma_values[i-1]:
            if position == 0:
                holdings = cash / prices[i]
                cash = 0
                position = 1
                trades.append(('BUY', i, prices[i]))
        
        # 卖出信号：价格从上方穿过均线
        elif prices[i] < sma_values[i] and prices[i-1] >= sma_values[i-1]:
            if position == 1:
                cash = holdings * prices[i]
                holdings = 0
                position = 0
                trades.append(('SELL', i, prices[i]))
    
    # 最终价值
    final_value = cash + holdings * prices[-1]
    total_return = (final_value - 10000) / 10000 * 100
    
    return {
        'initial_capital': 10000.0,
        'final_value': final_value,
        'total_return': total_return,
        'num_trades': len(trades),
        'trades': trades
    }


result = simple_backtest(prices, sma_period=20)
print(f"""
简单均线策略回测结果：

  初始资金: ${result['initial_capital']:,.2f}
  最终价值: ${result['final_value']:,.2f}
  总收益率: {result['total_return']:.2f}%
  交易次数: {result['num_trades']}
""")


# =============================================================================
# 7. 风险管理
# =============================================================================
print("\n" + "=" * 70)
print("7. 风险管理")
print("=" * 70)

risk_management = """
风险管理是量化交易的核心！

"控制风险比追求收益更重要"

常见的风险类型：

1. 市场风险
   - 价格波动造成的损失
   - 应对：止损、仓位控制、分散投资

2. 流动性风险
   - 无法以合理价格买卖
   - 应对：选择流动性好的品种、限制单笔规模

3. 系统风险
   - 技术故障、网络问题
   - 应对：冗余部署、熔断机制

风控指标：

1. 单笔风险限额
   - 每笔交易最多亏损多少
   - 建议：不超过总资金的 1-2%

2. 每日风险限额
   - 每天最多亏损多少
   - 达到限额后停止交易

3. 最大持仓限制
   - 单个品种的最大仓位
   - 避免过度集中

4. 止损设置
   - 每笔交易设置止损价
   - 严格执行，不要心存侥幸

仓位管理公式：

    单笔交易金额 = 总资金 × 风险比例 / 止损幅度
    
    例如：
    总资金 = $10000
    风险比例 = 2%（愿意承担的最大亏损）
    止损幅度 = 5%（止损位置）
    
    单笔交易金额 = 10000 × 0.02 / 0.05 = $4000
    即：可以用 $4000 买入，设置 5% 止损
"""
print(risk_management)


# =============================================================================
# 8. 面试高频问题
# =============================================================================
print("\n" + "=" * 70)
print("8. 量化交易面试高频问题")
print("=" * 70)

interview_qa = """
Q1: 什么是滑点 (Slippage)？
A: 预期成交价格与实际成交价格的差异。
   原因：市场波动、流动性不足、订单延迟
   应对：使用限价单、选择流动性好的品种

Q2: 什么是回撤 (Drawdown)？
A: 资产从最高点下跌的幅度。
   最大回撤是衡量策略风险的重要指标。
   公式：Drawdown = (Peak - Trough) / Peak

Q3: 什么是夏普比率 (Sharpe Ratio)？
A: 衡量风险调整后收益的指标。
   公式：Sharpe = (策略收益 - 无风险收益) / 收益标准差
   越高越好，说明单位风险获得的收益越多

Q4: 什么是 Alpha 和 Beta？
A: Beta：策略与市场的相关性（系统性风险）
   Alpha：策略超越市场的超额收益
   量化策略追求高 Alpha、低 Beta

Q5: 如何避免过拟合？
A: - 使用足够长的历史数据
   - 样本外测试
   - 保持策略简单
   - 理解策略逻辑，不要纯粹靠参数拟合

Q6: 什么是做市策略 (Market Making)？
A: 同时挂买单和卖单，赚取买卖价差。
   风险：库存风险、市场剧烈波动

Q7: 什么是事件驱动架构？
A: 系统通过事件（如新行情、订单成交）触发相应处理。
   优点：解耦、可扩展、响应快

Q8: 如何处理行情数据延迟？
A: - 使用时间戳记录每个环节
   - 监控端到端延迟
   - 优化网络连接
   - 使用专线

Q9: 描述一个你设计的交易策略？
A: 准备一个简单但完整的策略描述：
   - 策略类型（趋势/均值回归等）
   - 使用的指标
   - 入场/出场条件
   - 风险管理方法
   - 回测结果

Q10: 高频交易的技术挑战？
A: - 超低延迟要求
   - 高吞吐量处理
   - 可靠性和容错
   - 硬件优化（FPGA、专线）
"""
print(interview_qa)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("量化交易概念学习完成！")
    print("下一步：运行 03_project_walkthrough.py 了解项目架构")
    print("=" * 70)
