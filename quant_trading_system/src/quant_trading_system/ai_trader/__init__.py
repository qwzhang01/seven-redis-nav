"""
AI 交易员模块

使用强化学习训练自动交易策略。
支持多种 RL 算法：DQN, PPO, A2C 等。
"""

from .environment import TradingEnvironment
from .agent import (
    BaseAgent,
    DQNAgent,
    PPOAgent,
    A2CAgent,
)
from .trainer import AITrader, TrainingConfig
from .feature_engineer import FeatureEngineer

__all__ = [
    "TradingEnvironment",
    "BaseAgent",
    "DQNAgent",
    "PPOAgent",
    "A2CAgent",
    "AITrader",
    "TrainingConfig",
    "FeatureEngineer",
]
