"""
AI 交易员示例

演示如何使用 AI 交易员模块训练强化学习交易策略。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.quant_trading_system.services.ai_trader import (
    AITrader,
    TrainingConfig,
    TradingEnvironment,
    DQNAgent,
    FeatureEngineer,
    FeatureConfig,
)


def generate_mock_data(days: int = 365, interval: str = "1h") -> pd.DataFrame:
    """生成模拟 K 线数据"""
    np.random.seed(42)
    
    # 计算数据点数量
    intervals_per_day = {"1m": 1440, "5m": 288, "15m": 96, "1h": 24, "4h": 6, "1d": 1}
    n_points = days * intervals_per_day.get(interval, 24)
    
    # 生成时间序列
    start_time = datetime.now() - timedelta(days=days)
    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
    minutes = interval_minutes.get(interval, 60)
    timestamps = [start_time + timedelta(minutes=i * minutes) for i in range(n_points)]
    
    # 几何布朗运动
    initial_price = 30000.0
    mu = 0.0001
    sigma = 0.02
    
    returns = np.random.normal(mu, sigma, n_points)
    # 添加一些趋势
    trend = np.sin(np.linspace(0, 4 * np.pi, n_points)) * 0.01
    returns += trend
    
    prices = initial_price * np.exp(np.cumsum(returns))
    
    data = []
    for i, (ts, close) in enumerate(zip(timestamps, prices)):
        volatility = sigma * close
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = prices[i-1] if i > 0 else close
        
        high = max(open_price, close, high)
        low = min(open_price, close, low)
        
        volume = 100 + abs(np.random.normal(0, 50)) * (1 + abs(returns[i]) * 10)
        
        data.append({
            "timestamp": ts,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
    
    return pd.DataFrame(data)


def demo_feature_engineering():
    """演示特征工程"""
    print("=" * 70)
    print("1. 特征工程演示")
    print("=" * 70)
    
    # 生成数据
    df = generate_mock_data(days=30)
    print(f"原始数据: {len(df)} 行")
    
    # 创建特征工程器
    config = FeatureConfig(
        use_returns=True,
        use_log_returns=True,
        use_ma=True,
        use_rsi=True,
        use_macd=True,
        use_bollinger=True,
        use_atr=True,
        use_volume_features=True,
        use_time_features=True,
        normalize=True,
    )
    
    fe = FeatureEngineer(config)
    processed_df = fe.fit_transform(df)
    
    print(f"处理后数据: {len(processed_df)} 行")
    print(f"\n生成的特征 ({len(fe.get_feature_names())} 个):")
    
    # 按类别显示特征
    features = fe.get_feature_names()
    categories = {
        "价格特征": [f for f in features if "return" in f or "price" in f or "range" in f],
        "均线特征": [f for f in features if "ma_" in f],
        "RSI 特征": [f for f in features if "rsi" in f],
        "MACD 特征": [f for f in features if "macd" in f],
        "布林带特征": [f for f in features if "bb_" in f],
        "波动率特征": [f for f in features if "atr" in f or "volatility" in f],
        "成交量特征": [f for f in features if "volume" in f],
        "时间特征": [f for f in features if "hour" in f or "dow" in f or "month" in f],
        "统计特征": [f for f in features if "skew" in f or "kurt" in f or "high_ratio" in f or "low_ratio" in f],
    }
    
    for category, cols in categories.items():
        if cols:
            print(f"\n  {category}:")
            for col in cols[:5]:  # 最多显示5个
                print(f"    - {col}")
            if len(cols) > 5:
                print(f"    ... 共 {len(cols)} 个")


def demo_trading_environment():
    """演示交易环境"""
    print("\n" + "=" * 70)
    print("2. 交易环境演示")
    print("=" * 70)
    
    # 准备数据
    df = generate_mock_data(days=30)
    
    fe = FeatureEngineer(FeatureConfig(normalize=True))
    processed_df = fe.fit_transform(df)
    
    # 创建环境
    env = TradingEnvironment(
        df=processed_df,
        feature_columns=fe.get_feature_names(),
        initial_capital=10000.0,
        commission_rate=0.001,
        slippage_rate=0.0005,
        window_size=20,
    )
    
    print(f"观察空间维度: {env.observation_space.shape}")
    print(f"动作空间: {env.action_space}")
    
    # 运行一个随机 episode
    state, info = env.reset()
    total_reward = 0
    actions_taken = {0: 0, 1: 0, 2: 0}  # Hold, Buy, Sell
    
    done = False
    step = 0
    
    while not done:
        # 简单策略：随机动作
        action = np.random.choice([0, 1, 2], p=[0.7, 0.15, 0.15])
        actions_taken[action] += 1
        
        next_state, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        
        total_reward += reward
        state = next_state
        step += 1
    
    print(f"\n随机策略运行结果:")
    print(f"  总步数: {step}")
    print(f"  总奖励: {total_reward:.4f}")
    print(f"  最终收益率: {info['return_pct']:.2f}%")
    print(f"  最大回撤: {info['max_drawdown']*100:.2f}%")
    print(f"  交易次数: {info['total_trades']}")
    print(f"  动作分布: Hold={actions_taken[0]}, Buy={actions_taken[1]}, Sell={actions_taken[2]}")


def demo_dqn_agent():
    """演示 DQN Agent"""
    print("\n" + "=" * 70)
    print("3. DQN Agent 演示")
    print("=" * 70)
    
    # 创建 Agent
    state_dim = 100
    action_dim = 3
    
    agent = DQNAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        learning_rate=0.001,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.01,
        epsilon_decay=0.995,
        buffer_size=10000,
        batch_size=32,
        hidden_dims=[64, 32],
        use_double_dqn=True,
        use_dueling=True,
    )
    
    print(f"Agent 类型: DQN")
    print(f"状态维度: {state_dim}")
    print(f"动作维度: {action_dim}")
    print(f"使用 Double DQN: {agent.use_double_dqn}")
    print(f"使用 Dueling: {agent.use_dueling}")
    
    # 模拟训练几步
    print(f"\n模拟训练:")
    
    for i in range(100):
        state = np.random.randn(state_dim).astype(np.float32)
        action = agent.select_action(state)
        next_state = np.random.randn(state_dim).astype(np.float32)
        reward = np.random.randn()
        done = i == 99
        
        agent.store_experience(state, action, reward, next_state, done)
        
        if len(agent.replay_buffer) >= 32:
            metrics = agent.update()
            if i % 20 == 0 and metrics:
                print(f"  Step {i}: loss={metrics.get('loss', 0):.4f}, "
                      f"epsilon={metrics.get('epsilon', 0):.4f}")


def demo_full_training():
    """演示完整训练流程"""
    print("\n" + "=" * 70)
    print("4. 完整训练流程演示")
    print("=" * 70)
    
    # 生成数据
    print("\n生成模拟数据...")
    train_df = generate_mock_data(days=200)
    test_df = generate_mock_data(days=50)
    
    # 配置
    config = TrainingConfig(
        agent_type="DQN",
        total_episodes=50,  # 演示用，实际训练需要更多
        initial_capital=10000.0,
        commission_rate=0.001,
        window_size=20,
        learning_rate=0.001,
        batch_size=32,
        hidden_dims=[128, 64],
        epsilon_start=1.0,
        epsilon_end=0.1,
        epsilon_decay=0.99,
        eval_interval=10,
        save_interval=25,
        early_stopping_patience=20,
        min_episodes=30,
        save_dir="models/demo",
        log_dir="logs/demo",
    )
    
    # 创建训练器
    trainer = AITrader(config)
    
    # 训练
    print("\n开始训练...")
    history = trainer.train(train_df)
    
    # 评估
    print("\n在测试集上评估...")
    test_result = trainer.evaluate(test_df)
    
    # 打印训练摘要
    summary = trainer.get_training_summary()
    print("\n训练摘要:")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")


def demo_quick_start():
    """快速开始示例"""
    print("\n" + "=" * 70)
    print("5. 快速开始示例代码")
    print("=" * 70)
    
    code = '''
# 快速开始使用 AI 交易员

import pandas as pd
from quant_trading_system.services.ai_trader import AITrader, TrainingConfig

# 1. 加载数据
df = pd.read_csv("your_data.csv")  # 需要包含 timestamp, open, high, low, close, volume

# 2. 配置训练参数
config = TrainingConfig(
    agent_type="DQN",           # 或 "PPO", "A2C"
    total_episodes=500,         # 训练轮数
    initial_capital=10000.0,    # 初始资金
    commission_rate=0.001,      # 手续费率
    window_size=20,             # 观察窗口
    learning_rate=0.001,        # 学习率
    hidden_dims=[256, 128],     # 网络结构
)

# 3. 创建训练器
trainer = AITrader(config)

# 4. 训练
history = trainer.train(df)

# 5. 评估
test_df = pd.read_csv("test_data.csv")
result = trainer.evaluate(test_df)

# 6. 保存模型
trainer.save("my_ai_trader.pt")

# 7. 加载模型
trainer.load("my_ai_trader.pt")

# 8. 预测
actions = trainer.predict(new_data)
# actions: [0, 0, 1, 0, 2, ...] 
# 0=持有, 1=买入, 2=卖出
'''
    print(code)


if __name__ == "__main__":
    print("=" * 70)
    print("AI 交易员模块演示")
    print("=" * 70)
    
    # 运行演示
    demo_feature_engineering()
    demo_trading_environment()
    demo_dqn_agent()
    
    # 完整训练演示（需要较长时间）
    print("\n是否运行完整训练演示？(需要约1-2分钟)")
    print("输入 'y' 运行，其他跳过: ", end="")
    
    try:
        response = input().strip().lower()
        if response == 'y':
            demo_full_training()
        else:
            print("跳过完整训练演示")
    except EOFError:
        print("\n自动跳过完整训练演示（非交互模式）")
    
    demo_quick_start()
    
    print("\n" + "=" * 70)
    print("演示完成！")
    print("=" * 70)
