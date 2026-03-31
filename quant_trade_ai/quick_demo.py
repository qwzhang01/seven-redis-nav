"""
================================================================================
快速演示 - 使用模拟数据验证AI交易员训练流程
================================================================================

本脚本提供一个完整的端到端演示，包括：
1. 生成模拟股票数据
2. 创建交易环境
3. 训练DQN智能体
4. 评估测试表现
5. 可视化结果

为什么使用模拟数据？
------------------
- 无需网络连接
- 可控制数据特性（趋势、波动率等）
- 便于快速验证和调试
- 可重复性好（使用固定随机种子）

运行方法：
---------
在终端中执行：
    python3 quick_demo.py

预期结果：
---------
- 训练50个回合
- 在测试集上评估
- 生成 demo_results.png 图表

作者: AI Trading Demo
版本: 1.0
================================================================================
"""

# ============================================================================
# 导入必要的库
# ============================================================================
import numpy as np          # 数值计算
import pandas as pd         # 数据处理
import matplotlib.pyplot as plt  # 绑图
import warnings
warnings.filterwarnings('ignore')  # 忽略警告，使输出更清晰

# 导入自定义模块
from trading_env import TradingEnvironment  # 交易环境
from dqn_agent import DQNAgent              # DQN智能体


def generate_synthetic_data(n_days: int = 500, 
                            initial_price: float = 100.0,
                            volatility: float = 0.02,
                            trend: float = 0.0002,
                            seed: int = 42) -> pd.DataFrame:
    """
    生成模拟股票数据
    
    使用几何布朗运动 (Geometric Brownian Motion, GBM) 模拟股票价格。
    GBM 是金融学中最常用的股价模型，也是期权定价（Black-Scholes模型）的基础。
    
    数学原理：
    ---------
    GBM 的微分方程：
        dS = μSdt + σSdW
    
    其中：
    - S: 股票价格
    - μ (mu): 漂移率（drift），决定长期趋势
    - σ (sigma): 波动率（volatility），决定价格波动幅度
    - dW: 维纳过程（随机游走）
    
    离散化近似：
        S(t+1) = S(t) × exp(μ - σ²/2 + σε)
        其中 ε ~ N(0, 1) 是标准正态随机数
    
    参数说明：
    ---------
    n_days : int, 默认=500
        生成数据的天数
        500天约2年的交易日
        
    initial_price : float, 默认=100.0
        初始股票价格
        使用100便于计算百分比变化
        
    volatility : float, 默认=0.02
        日波动率（标准差）
        这是股票的"风险"度量
        
        参考值：
        - 0.01 (1%): 低波动（蓝筹股）
        - 0.02 (2%): 中等波动（普通股票）
        - 0.05 (5%): 高波动（成长股、小盘股）
        - 0.10 (10%): 极高波动（加密货币）
        
    trend : float, 默认=0.0002
        日均趋势（漂移率）
        决定股票的长期走势
        
        参考值：
        - 0: 无趋势（随机游走）
        - 0.0002: 约年化5%（保守增长）
        - 0.0004: 约年化10%（中等增长）
        - 0.001: 约年化28%（高增长）
        - -0.0002: 下跌趋势
        
    seed : int, 默认=42
        随机数种子
        使用固定种子可以重现相同的数据
        42是常用的默认值（源自《银河系漫游指南》）
    
    返回：
    -----
    df : pd.DataFrame
        包含以下列的股票数据：
        - Open: 开盘价
        - High: 最高价
        - Low: 最低价
        - Close: 收盘价
        - Volume: 成交量
    
    示例：
    ------
    >>> # 生成上涨市场
    >>> df_bull = generate_synthetic_data(trend=0.001)
    >>> 
    >>> # 生成下跌市场
    >>> df_bear = generate_synthetic_data(trend=-0.001)
    >>> 
    >>> # 生成高波动市场
    >>> df_volatile = generate_synthetic_data(volatility=0.05)
    """
    # 设置随机种子，确保结果可重现
    np.random.seed(seed)
    
    # ========================================================================
    # 生成日收益率序列
    # ========================================================================
    # 使用正态分布生成随机收益率
    # 均值 = trend（趋势），标准差 = volatility（波动率）
    returns = np.random.normal(trend, volatility, n_days)
    
    # ========================================================================
    # 添加周期性波动
    # ========================================================================
    # 真实市场通常存在周期性因素（如季节性、月末效应等）
    # 这里添加一个简单的正弦波模拟周期性
    t = np.arange(n_days)  # 时间序列 [0, 1, 2, ..., n_days-1]
    
    # 50天周期的正弦波，振幅0.01（1%）
    # 这模拟了约2.5个月的周期波动
    seasonal = 0.01 * np.sin(2 * np.pi * t / 50)
    returns += seasonal
    
    # ========================================================================
    # 从收益率计算价格
    # ========================================================================
    # 使用对数收益率的累积和
    # 价格 = 初始价格 × exp(累积对数收益率)
    # 这确保价格始终为正数
    price = initial_price * np.exp(np.cumsum(returns))
    
    # ========================================================================
    # 生成 OHLCV 数据
    # ========================================================================
    data = {
        'Open': [],   # 开盘价
        'High': [],   # 最高价
        'Low': [],    # 最低价
        'Close': [],  # 收盘价
        'Volume': []  # 成交量
    }
    
    for i in range(n_days):
        close = price[i]  # 收盘价来自我们生成的价格序列
        
        # 日内波动范围：收盘价的1%-3%
        # 这决定了High和Low与Close的差距
        daily_range = close * np.random.uniform(0.01, 0.03)
        
        # 开盘价在收盘价附近随机波动
        open_price = close + np.random.uniform(-daily_range/2, daily_range/2)
        
        # 最高价 >= max(开盘价, 收盘价)
        high = max(open_price, close) + np.random.uniform(0, daily_range/2)
        
        # 最低价 <= min(开盘价, 收盘价)
        low = min(open_price, close) - np.random.uniform(0, daily_range/2)
        
        # 随机生成成交量（100万到500万之间）
        volume = np.random.randint(1000000, 5000000)
        
        # 添加到数据字典
        data['Open'].append(open_price)
        data['High'].append(high)
        data['Low'].append(low)
        data['Close'].append(close)
        data['Volume'].append(volume)
    
    # ========================================================================
    # 创建 DataFrame
    # ========================================================================
    df = pd.DataFrame(data)
    
    # 添加日期索引（从2023年开始）
    df.index = pd.date_range(start='2023-01-01', periods=n_days)
    
    return df


def quick_demo():
    """
    快速演示训练流程
    
    这个函数演示了 AI 交易员训练的完整流程：
    
    流程概览：
    ---------
    1. 数据准备
       - 生成模拟股票数据
       - 划分训练集和测试集
       
    2. 环境设置
       - 创建交易环境（计算技术指标）
       - 配置初始资金、手续费等
       
    3. 智能体初始化
       - 创建DQN智能体
       - 设置超参数
       
    4. 训练循环
       - 在训练集上反复交易
       - 存储经验，更新网络
       
    5. 评估测试
       - 在测试集上运行
       - 计算盈亏统计
       
    6. 结果可视化
       - 绘制训练曲线
       - 绘制回测图表
    """
    # ========================================================================
    # 打印标题
    # ========================================================================
    print("=" * 60)
    print("AI 交易员训练演示 (使用模拟数据)")
    print("=" * 60)
    
    # ========================================================================
    # 第1步：生成模拟数据
    # ========================================================================
    print("\n[1] 生成模拟股票数据...")
    
    # 生成500天的模拟数据
    # volatility=0.02: 日波动率2%
    # trend=0.0003: 微弱上涨趋势
    df = generate_synthetic_data(n_days=500, volatility=0.02, trend=0.0003)
    
    # 打印数据概览
    print(f"数据形状: {df.shape}")  # (500, 5)
    print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    print(f"平均成交量: {df['Volume'].mean():.0f}")
    
    # ========================================================================
    # 第2步：划分训练集和测试集
    # ========================================================================
    # 使用前80%数据训练，后20%数据测试
    # 这模拟了"用历史数据训练，预测未来"的场景
    train_size = int(len(df) * 0.8)  # 400天
    train_df = df.iloc[:train_size].copy()   # 训练集
    test_df = df.iloc[train_size:].copy()    # 测试集
    
    print(f"\n训练集: {len(train_df)} 天")
    print(f"测试集: {len(test_df)} 天")
    
    # ========================================================================
    # 第3步：创建交易环境
    # ========================================================================
    print("\n[2] 创建交易环境...")
    
    # 训练环境：用于学习
    train_env = TradingEnvironment(train_df, initial_balance=100000)
    
    # 测试环境：用于评估
    test_env = TradingEnvironment(test_df, initial_balance=100000)
    
    # 获取状态和动作空间的大小
    state_size = train_env.observation_space.shape[0]  # 14
    action_size = train_env.action_space.n              # 3
    
    print(f"状态维度: {state_size}")
    print(f"动作数量: {action_size}")
    
    # ========================================================================
    # 第4步：创建DQN智能体
    # ========================================================================
    print("\n[3] 创建DQN智能体...")
    
    agent = DQNAgent(
        state_size=state_size,    # 状态空间大小：14
        action_size=action_size,  # 动作空间大小：3
        learning_rate=0.001,      # 学习率
        gamma=0.99,               # 折扣因子
        epsilon_start=1.0,        # 初始探索率：100%随机
        epsilon_end=0.05,         # 最终探索率：5%随机
        epsilon_decay=0.99,       # 探索率衰减：每步乘0.99
        batch_size=32             # 批次大小
    )
    
    # ========================================================================
    # 第5步：训练
    # ========================================================================
    print("\n[4] 开始训练 (50回合)...")
    print("-" * 60)
    
    # 记录训练过程
    episode_rewards = []  # 每回合的总奖励
    episode_profits = []  # 每回合的总利润
    
    # 训练50个回合
    for episode in range(50):
        # --------------------------------------------------------------------
        # 回合开始：重置环境
        # --------------------------------------------------------------------
        state, _ = train_env.reset()  # 获取初始状态
        total_reward = 0              # 累计奖励
        done = False                  # 是否结束
        
        # --------------------------------------------------------------------
        # 回合循环：持续交易直到结束
        # --------------------------------------------------------------------
        while not done:
            # 1. 选择动作（基于当前状态）
            action = agent.select_action(state, training=True)
            
            # 2. 执行动作，获取反馈
            next_state, reward, terminated, truncated, info = train_env.step(action)
            done = terminated or truncated
            
            # 3. 存储经验（用于后续训练）
            agent.store_experience(state, action, reward, next_state, done)
            
            # 4. 训练网络（从经验中学习）
            agent.train_step()
            
            # 5. 更新状态
            state = next_state
            total_reward += reward
        
        # --------------------------------------------------------------------
        # 回合结束：记录结果
        # --------------------------------------------------------------------
        episode_rewards.append(total_reward)
        episode_profits.append(info['total_profit'])
        
        # 每10回合打印一次进度
        if (episode + 1) % 10 == 0:
            # 计算最近10回合的平均值
            avg_reward = np.mean(episode_rewards[-10:])
            avg_profit = np.mean(episode_profits[-10:])
            print(f"Episode {episode + 1:3d} | "
                  f"Reward: {avg_reward:8.2f} | "
                  f"Profit: ${avg_profit:10.2f} | "
                  f"Epsilon: {agent.epsilon:.3f}")
    
    # ========================================================================
    # 第6步：测试集评估
    # ========================================================================
    print("\n[5] 测试集评估...")
    print("-" * 60)
    
    # 在测试集上运行10次，计算统计数据
    test_profits = []
    
    for _ in range(10):
        state, _ = test_env.reset()
        done = False
        
        while not done:
            # 测试时不探索（training=False）
            action = agent.select_action(state, training=False)
            next_state, reward, terminated, truncated, info = test_env.step(action)
            done = terminated or truncated
            state = next_state
        
        test_profits.append(info['total_profit'])
    
    # 打印测试结果
    print(f"测试集平均利润: ${np.mean(test_profits):.2f} ± ${np.std(test_profits):.2f}")
    print(f"测试集最大利润: ${np.max(test_profits):.2f}")
    print(f"测试集最小利润: ${np.min(test_profits):.2f}")
    
    # ========================================================================
    # 第7步：详细回测
    # ========================================================================
    print("\n[6] 详细回测...")
    print("-" * 60)
    
    # 运行一次完整回测，记录详细过程
    state, _ = test_env.reset()
    done = False
    history = []  # 保存每一步的状态
    
    while not done:
        action = agent.select_action(state, training=False)
        next_state, reward, terminated, truncated, info = test_env.step(action)
        done = terminated or truncated
        history.append(info.copy())
        state = next_state
    
    # 获取交易记录
    trades = test_env.trades
    
    # 打印回测统计
    print(f"总交易次数: {len(trades)}")
    print(f"买入: {len([t for t in trades if t[0] == 'BUY'])} 次")
    print(f"卖出: {len([t for t in trades if t[0] == 'SELL'])} 次")
    print(f"最终资产: ${history[-1]['total_value']:.2f}")
    print(f"收益率: {(history[-1]['total_value'] - 100000) / 100000 * 100:.2f}%")
    
    # ========================================================================
    # 第8步：生成可视化图表
    # ========================================================================
    print("\n[7] 生成可视化图表...")
    
    # 创建2×2的子图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # ------------------------------------------------------------------------
    # 图1：训练奖励曲线（左上）
    # ------------------------------------------------------------------------
    axes[0, 0].plot(episode_rewards, alpha=0.5, label='Episode Reward')
    # 添加10期移动平均线，显示趋势
    axes[0, 0].plot(pd.Series(episode_rewards).rolling(10).mean(), 
                    linewidth=2, label='MA-10')
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Total Reward')
    axes[0, 0].set_title('Training Rewards')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # ------------------------------------------------------------------------
    # 图2：训练利润曲线（右上）
    # ------------------------------------------------------------------------
    axes[0, 1].plot(episode_profits, alpha=0.5, color='green')
    axes[0, 1].plot(pd.Series(episode_profits).rolling(10).mean(), 
                    linewidth=2, color='darkgreen', label='MA-10')
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Profit ($)')
    axes[0, 1].set_title('Training Profits')
    axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)  # 零线
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # ------------------------------------------------------------------------
    # 图3：价格和交易信号（左下）
    # ------------------------------------------------------------------------
    # 获取测试集价格（跳过窗口期）
    test_prices = test_df['Close'].values[20:]
    axes[1, 0].plot(test_prices, label='Price', alpha=0.7)
    
    # 绘制买入点（绿色向上三角形）
    buy_points = [(t[1]-train_size-20, t[2]) for t in trades if t[0] == 'BUY']
    if buy_points:
        bx, by = zip(*buy_points)
        axes[1, 0].scatter(bx, by, marker='^', color='green', s=100, label='Buy', zorder=5)
    
    # 绘制卖出点（红色向下三角形）
    sell_points = [(t[1]-train_size-20, t[2]) for t in trades if t[0] == 'SELL']
    if sell_points:
        sx, sy = zip(*sell_points)
        axes[1, 0].scatter(sx, sy, marker='v', color='red', s=100, label='Sell', zorder=5)
    
    axes[1, 0].set_xlabel('Time Step')
    axes[1, 0].set_ylabel('Price ($)')
    axes[1, 0].set_title('Backtest: Price & Trading Signals')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # ------------------------------------------------------------------------
    # 图4：投资组合价值变化（右下）
    # ------------------------------------------------------------------------
    portfolio_values = [h['total_value'] for h in history]
    axes[1, 1].plot(portfolio_values, linewidth=2, color='blue')
    axes[1, 1].axhline(y=100000, color='gray', linestyle='--', alpha=0.5, label='Initial')
    
    # 盈利区域填充绿色
    axes[1, 1].fill_between(range(len(portfolio_values)), portfolio_values, 100000,
                            where=[v >= 100000 for v in portfolio_values], 
                            alpha=0.3, color='green')
    # 亏损区域填充红色
    axes[1, 1].fill_between(range(len(portfolio_values)), portfolio_values, 100000,
                            where=[v < 100000 for v in portfolio_values], 
                            alpha=0.3, color='red')
    
    axes[1, 1].set_xlabel('Time Step')
    axes[1, 1].set_ylabel('Portfolio Value ($)')
    axes[1, 1].set_title('Backtest: Portfolio Value')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 调整布局并保存
    plt.tight_layout()
    plt.savefig('demo_results.png', dpi=150)
    print("图表已保存至 demo_results.png")
    plt.show()
    
    # ========================================================================
    # 完成
    # ========================================================================
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


# ============================================================================
# 主程序入口
# ============================================================================
if __name__ == '__main__':
    # 当直接运行此脚本时，执行演示
    quick_demo()
