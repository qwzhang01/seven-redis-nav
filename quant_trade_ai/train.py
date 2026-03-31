"""
AI交易员训练主程序
包含数据获取、训练流程、回测评估
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from trading_env import TradingEnvironment
from dqn_agent import DQNAgent


def download_stock_data(symbol: str = 'AAPL', period: str = '2y') -> pd.DataFrame:
    """
    下载股票数据
    
    Args:
        symbol: 股票代码
        period: 数据周期
    
    Returns:
        包含OHLCV的DataFrame
    """
    print(f"Downloading {symbol} data...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    print(f"Downloaded {len(df)} days of data")
    return df


def train_agent(env: TradingEnvironment, agent: DQNAgent, 
                n_episodes: int = 100, verbose: bool = True):
    """
    训练智能体
    
    Args:
        env: 交易环境
        agent: DQN智能体
        n_episodes: 训练回合数
        verbose: 是否打印训练信息
    """
    episode_rewards = []
    episode_profits = []
    
    for episode in range(n_episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            # 选择动作
            action = agent.select_action(state, training=True)
            
            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # 存储经验
            agent.store_experience(state, action, reward, next_state, done)
            
            # 训练
            agent.train_step()
            
            state = next_state
            total_reward += reward
        
        episode_rewards.append(total_reward)
        episode_profits.append(info['total_profit'])
        
        if verbose and (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_profit = np.mean(episode_profits[-10:])
            print(f"Episode {episode + 1}/{n_episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Profit: ${avg_profit:.2f} | "
                  f"Epsilon: {agent.epsilon:.4f}")
    
    return episode_rewards, episode_profits


def evaluate_agent(env: TradingEnvironment, agent: DQNAgent, 
                   n_episodes: int = 10) -> dict:
    """
    评估智能体
    
    Args:
        env: 交易环境
        agent: DQN智能体
        n_episodes: 评估回合数
    
    Returns:
        评估结果字典
    """
    profits = []
    total_values = []
    
    for _ in range(n_episodes):
        state, _ = env.reset()
        done = False
        
        while not done:
            action = agent.select_action(state, training=False)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            state = next_state
        
        profits.append(info['total_profit'])
        total_values.append(info['total_value'])
    
    results = {
        'mean_profit': np.mean(profits),
        'std_profit': np.std(profits),
        'max_profit': np.max(profits),
        'min_profit': np.min(profits),
        'mean_return': (np.mean(total_values) - env.initial_balance) / env.initial_balance * 100
    }
    
    return results


def run_single_episode(env: TradingEnvironment, agent: DQNAgent):
    """
    运行单次回测并返回详细记录
    
    Returns:
        history: 交易历史DataFrame
    """
    state, _ = env.reset()
    done = False
    
    history = {
        'step': [],
        'price': [],
        'action': [],
        'balance': [],
        'shares': [],
        'total_value': []
    }
    
    action_names = ['HOLD', 'BUY', 'SELL']
    
    while not done:
        action = agent.select_action(state, training=False)
        next_state, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        
        history['step'].append(env.current_step)
        history['price'].append(info['current_price'])
        history['action'].append(action_names[action])
        history['balance'].append(info['balance'])
        history['shares'].append(info['shares_held'])
        history['total_value'].append(info['total_value'])
        
        state = next_state
    
    return pd.DataFrame(history), env.trades


def plot_training_results(episode_rewards: list, episode_profits: list,
                          save_path: str = None):
    """绘制训练结果"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 回合奖励
    axes[0, 0].plot(episode_rewards, alpha=0.6)
    axes[0, 0].plot(pd.Series(episode_rewards).rolling(10).mean(), 
                    linewidth=2, label='MA-10')
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Total Reward')
    axes[0, 0].set_title('Training Rewards')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 回合利润
    axes[0, 1].plot(episode_profits, alpha=0.6, color='green')
    axes[0, 1].plot(pd.Series(episode_profits).rolling(10).mean(), 
                    linewidth=2, color='darkgreen', label='MA-10')
    axes[0, 1].set_xlabel('Episode')
    axes[0, 1].set_ylabel('Profit ($)')
    axes[0, 1].set_title('Training Profits')
    axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 利润分布
    axes[1, 0].hist(episode_profits, bins=30, edgecolor='black', alpha=0.7)
    axes[1, 0].axvline(x=np.mean(episode_profits), color='red', 
                       linestyle='--', label=f'Mean: ${np.mean(episode_profits):.2f}')
    axes[1, 0].set_xlabel('Profit ($)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Profit Distribution')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 累计收益曲线
    cumulative_profit = np.cumsum(episode_profits)
    axes[1, 1].plot(cumulative_profit, linewidth=2)
    axes[1, 1].fill_between(range(len(cumulative_profit)), cumulative_profit, 
                            alpha=0.3)
    axes[1, 1].set_xlabel('Episode')
    axes[1, 1].set_ylabel('Cumulative Profit ($)')
    axes[1, 1].set_title('Cumulative Training Profit')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Training plot saved to {save_path}")
    
    plt.show()


def plot_backtest_results(df: pd.DataFrame, history: pd.DataFrame, 
                          trades: list, save_path: str = None):
    """绘制回测结果"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # 价格和交易点
    axes[0].plot(df['Close'].values, label='Price', alpha=0.7)
    
    buy_points = [(t[1], t[2]) for t in trades if t[0] == 'BUY']
    sell_points = [(t[1], t[2]) for t in trades if t[0] == 'SELL']
    
    if buy_points:
        buy_x, buy_y = zip(*buy_points)
        axes[0].scatter(buy_x, buy_y, marker='^', color='green', 
                       s=100, label='Buy', zorder=5)
    
    if sell_points:
        sell_x, sell_y = zip(*sell_points)
        axes[0].scatter(sell_x, sell_y, marker='v', color='red', 
                       s=100, label='Sell', zorder=5)
    
    axes[0].set_xlabel('Time Step')
    axes[0].set_ylabel('Price ($)')
    axes[0].set_title('Price Chart with Trading Signals')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 资产价值变化
    axes[1].plot(history['total_value'], label='Portfolio Value', 
                 linewidth=2, color='blue')
    axes[1].axhline(y=100000, color='gray', linestyle='--', 
                    alpha=0.5, label='Initial Balance')
    axes[1].fill_between(range(len(history)), history['total_value'], 100000, 
                         alpha=0.3, where=history['total_value'] >= 100000, 
                         color='green')
    axes[1].fill_between(range(len(history)), history['total_value'], 100000, 
                         alpha=0.3, where=history['total_value'] < 100000, 
                         color='red')
    axes[1].set_xlabel('Time Step')
    axes[1].set_ylabel('Value ($)')
    axes[1].set_title('Portfolio Value Over Time')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 持仓变化
    axes[2].bar(range(len(history)), history['shares'], alpha=0.6, color='purple')
    axes[2].set_xlabel('Time Step')
    axes[2].set_ylabel('Shares Held')
    axes[2].set_title('Position Over Time')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Backtest plot saved to {save_path}")
    
    plt.show()


def main():
    """主函数"""
    print("=" * 60)
    print("AI 交易员训练系统")
    print("=" * 60)
    
    # 1. 获取数据
    symbol = 'AAPL'
    df = download_stock_data(symbol, period='2y')
    
    # 划分训练集和测试集
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()
    
    print(f"\nTraining data: {len(train_df)} days")
    print(f"Testing data: {len(test_df)} days")
    
    # 2. 创建环境
    train_env = TradingEnvironment(train_df, initial_balance=100000)
    test_env = TradingEnvironment(test_df, initial_balance=100000)
    
    # 3. 创建智能体
    state_size = train_env.observation_space.shape[0]
    action_size = train_env.action_space.n
    
    print(f"\nState size: {state_size}")
    print(f"Action size: {action_size}")
    
    agent = DQNAgent(
        state_size=state_size,
        action_size=action_size,
        learning_rate=0.001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        batch_size=64
    )
    
    # 4. 训练
    print("\n" + "=" * 60)
    print("开始训练...")
    print("=" * 60)
    
    episode_rewards, episode_profits = train_agent(
        train_env, agent, n_episodes=100, verbose=True
    )
    
    # 5. 评估
    print("\n" + "=" * 60)
    print("评估结果 (测试集)")
    print("=" * 60)
    
    results = evaluate_agent(test_env, agent, n_episodes=10)
    print(f"平均利润: ${results['mean_profit']:.2f} ± ${results['std_profit']:.2f}")
    print(f"最大利润: ${results['max_profit']:.2f}")
    print(f"最小利润: ${results['min_profit']:.2f}")
    print(f"平均收益率: {results['mean_return']:.2f}%")
    
    # 6. 单次回测详情
    print("\n" + "=" * 60)
    print("执行详细回测...")
    print("=" * 60)
    
    history, trades = run_single_episode(test_env, agent)
    
    print(f"\n交易统计:")
    print(f"总交易次数: {len(trades)}")
    print(f"买入次数: {len([t for t in trades if t[0] == 'BUY'])}")
    print(f"卖出次数: {len([t for t in trades if t[0] == 'SELL'])}")
    print(f"最终资产: ${history['total_value'].iloc[-1]:.2f}")
    print(f"总收益率: {(history['total_value'].iloc[-1] - 100000) / 100000 * 100:.2f}%")
    
    # 7. 保存模型
    agent.save('trading_model.pth')
    
    # 8. 绘图
    print("\n生成图表...")
    plot_training_results(episode_rewards, episode_profits, 
                          save_path='training_results.png')
    plot_backtest_results(df.iloc[train_size:], history, trades,
                          save_path='backtest_results.png')
    
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
