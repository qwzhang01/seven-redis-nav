"""
AI 交易员训练器

整合环境、Agent 和特征工程，提供完整的训练流程。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import json
import os
import structlog

from .environment import TradingEnvironment
from .agent import BaseAgent, DQNAgent, PPOAgent, A2CAgent
from .feature_engineer import FeatureEngineer, FeatureConfig


@dataclass
class TrainingConfig:
    """训练配置"""
    # 基础配置
    agent_type: str = "DQN"  # DQN, PPO, A2C
    total_episodes: int = 1000
    max_steps_per_episode: int = None  # None 表示使用数据长度

    # 环境配置
    initial_capital: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    window_size: int = 20

    # Agent 配置
    learning_rate: float = 0.001
    gamma: float = 0.99
    batch_size: int = 64
    hidden_dims: List[int] = None

    # DQN 特有配置
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    buffer_size: int = 100000
    target_update_freq: int = 100
    use_double_dqn: bool = True
    use_dueling: bool = True
    use_per: bool = False

    # PPO 特有配置
    ppo_clip: float = 0.2
    ppo_epochs: int = 10
    gae_lambda: float = 0.95

    # 训练控制
    eval_interval: int = 10
    save_interval: int = 100
    early_stopping_patience: int = 50
    min_episodes: int = 100

    # 路径
    save_dir: str = "models/ai_trader"
    log_dir: str = "logs/ai_trader"

    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [256, 128, 64]


@dataclass
class TrainingResult:
    """训练结果"""
    episode: int
    total_reward: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    final_value: float

    def to_dict(self) -> Dict:
        return {
            "episode": self.episode,
            "total_reward": self.total_reward,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "final_value": self.final_value,
        }


logger = structlog.get_logger(__name__)


class AITrader:
    """
    AI 交易员训练器

    提供完整的强化学习交易训练流程：
    1. 数据预处理和特征工程
    2. 创建交易环境
    3. 训练 RL Agent
    4. 评估和可视化
    5. 模型保存和加载

    使用示例：
    ```python
    # 准备数据
    df = pd.read_csv("btc_1h.csv")

    # 创建训练器
    config = TrainingConfig(
        agent_type="DQN",
        total_episodes=500,
        initial_capital=10000.0,
    )
    trainer = AITrader(config)

    # 训练
    trainer.train(df)

    # 评估
    results = trainer.evaluate(test_df)

    # 保存模型
    trainer.save("my_model.pt")
    ```
    """

    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()

        # 创建目录
        os.makedirs(self.config.save_dir, exist_ok=True)
        os.makedirs(self.config.log_dir, exist_ok=True)

        # 组件
        self.feature_engineer: Optional[FeatureEngineer] = None
        self.env: Optional[TradingEnvironment] = None
        self.agent: Optional[BaseAgent] = None

        # 训练历史
        self.training_history: List[TrainingResult] = []
        self.best_return: float = float("-inf")
        self.best_episode: int = 0
        self.patience_counter: int = 0

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """准备数据和特征"""
        # 创建特征工程器
        feature_config = FeatureConfig(
            use_returns=True,
            use_log_returns=True,
            return_periods=[1, 5, 10, 20],
            use_ma=True,
            ma_periods=[5, 10, 20, 50],
            use_rsi=True,
            use_macd=True,
            use_bollinger=True,
            use_atr=True,
            use_volume_features=True,
            use_time_features=True,
            normalize=True,
        )

        self.feature_engineer = FeatureEngineer(feature_config)
        processed_df = self.feature_engineer.fit_transform(df)

        logger.info("数据预处理完成", original_rows=len(df), processed_rows=len(processed_df), feature_count=len(self.feature_engineer.get_feature_names()))

        return processed_df

    def create_environment(self, df: pd.DataFrame) -> TradingEnvironment:
        """创建交易环境"""
        feature_columns = self.feature_engineer.get_feature_names()

        env = TradingEnvironment(
            df=df,
            feature_columns=feature_columns,
            initial_capital=self.config.initial_capital,
            commission_rate=self.config.commission_rate,
            slippage_rate=self.config.slippage_rate,
            window_size=self.config.window_size,
            use_discrete_action=True,
        )

        return env

    def create_agent(self, state_dim: int, action_dim: int) -> BaseAgent:
        """创建 Agent"""
        if self.config.agent_type == "DQN":
            agent = DQNAgent(
                state_dim=state_dim,
                action_dim=action_dim,
                learning_rate=self.config.learning_rate,
                gamma=self.config.gamma,
                epsilon_start=self.config.epsilon_start,
                epsilon_end=self.config.epsilon_end,
                epsilon_decay=self.config.epsilon_decay,
                buffer_size=self.config.buffer_size,
                batch_size=self.config.batch_size,
                target_update_freq=self.config.target_update_freq,
                hidden_dims=self.config.hidden_dims,
                use_double_dqn=self.config.use_double_dqn,
                use_dueling=self.config.use_dueling,
                use_per=self.config.use_per,
            )
        elif self.config.agent_type == "PPO":
            agent = PPOAgent(
                state_dim=state_dim,
                action_dim=action_dim,
                learning_rate=self.config.learning_rate,
                gamma=self.config.gamma,
                clip_epsilon=self.config.ppo_clip,
                n_epochs=self.config.ppo_epochs,
                gae_lambda=self.config.gae_lambda,
                batch_size=self.config.batch_size,
                hidden_dims=self.config.hidden_dims,
            )
        elif self.config.agent_type == "A2C":
            agent = A2CAgent(
                state_dim=state_dim,
                action_dim=action_dim,
                learning_rate=self.config.learning_rate,
                gamma=self.config.gamma,
                hidden_dims=self.config.hidden_dims,
            )
        else:
            raise ValueError(f"Unknown agent type: {self.config.agent_type}")

        return agent

    def train(
        self,
        df: pd.DataFrame,
        validation_df: pd.DataFrame = None,
        callback: Callable[[int, TrainingResult], None] = None
    ) -> List[TrainingResult]:
        """
        训练 AI 交易员

        Args:
            df: 训练数据
            validation_df: 验证数据（可选）
            callback: 每轮回调函数

        Returns:
            训练历史
        """
        logger.info("开始训练 AI 交易员", agent_type=self.config.agent_type)

        # 准备数据
        processed_df = self.prepare_data(df)

        # 创建环境
        self.env = self.create_environment(processed_df)

        # 创建 Agent
        state_dim = self.env.observation_space.shape[0]
        action_dim = self.env.action_space.n

        logger.info("环境和Agent已创建", state_dim=state_dim, action_dim=action_dim)

        self.agent = self.create_agent(state_dim, action_dim)

        # 验证环境（如果提供）
        if validation_df is not None:
            val_processed = self.feature_engineer.transform(validation_df)
            val_env = self.create_environment(val_processed)
        else:
            val_env = None

        # 训练循环
        self.training_history = []
        self.best_return = float("-inf")
        self.patience_counter = 0

        for episode in range(self.config.total_episodes):
            # 训练一轮
            result = self._train_episode(episode)
            self.training_history.append(result)

            # 定期评估
            if episode > 0 and episode % self.config.eval_interval == 0:
                self._print_progress(episode, result)

                # 验证集评估
                if val_env is not None:
                    val_result = self._evaluate_episode(val_env)
                    logger.info("验证集评估", val_return=f"{val_result.total_return:.2f}%", val_max_drawdown=f"{val_result.max_drawdown*100:.2f}%")

            # 保存最佳模型
            if result.total_return > self.best_return:
                self.best_return = result.total_return
                self.best_episode = episode
                self.patience_counter = 0
                self._save_best_model()
            else:
                self.patience_counter += 1

            # 定期保存
            if episode > 0 and episode % self.config.save_interval == 0:
                self._save_checkpoint(episode)

            # 早停
            if (episode >= self.config.min_episodes and
                self.patience_counter >= self.config.early_stopping_patience):
                logger.info("早停触发", patience=self.config.early_stopping_patience)
                break

            # 回调
            if callback is not None:
                callback(episode, result)

        logger.info("训练完成", best_episode=self.best_episode, best_return=f"{self.best_return:.2f}%")

        return self.training_history

    def _train_episode(self, episode: int) -> TrainingResult:
        """训练一轮"""
        state, info = self.env.reset()
        total_reward = 0
        done = False

        self.agent.train_mode()

        while not done:
            # 选择动作
            action = self.agent.select_action(state)

            # 执行动作
            next_state, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated

            # 存储经验
            if self.config.agent_type == "DQN":
                self.agent.store_experience(state, action, reward, next_state, done)
                # 更新网络
                self.agent.update()
            else:
                self.agent.store_transition(state, action, reward, next_state, done)

            total_reward += reward
            state = next_state

        # PPO/A2C 在轮结束后更新
        if self.config.agent_type in ["PPO", "A2C"]:
            self.agent.update()

        # 计算绩效指标
        history_df = self.env.get_history_df()

        return TrainingResult(
            episode=episode,
            total_reward=total_reward,
            total_return=info.get("return_pct", 0),
            max_drawdown=info.get("max_drawdown", 0),
            sharpe_ratio=self._calculate_sharpe(history_df),
            win_rate=info.get("win_rate", 0),
            total_trades=info.get("total_trades", 0),
            final_value=info.get("total_value", self.config.initial_capital),
        )

    def _evaluate_episode(self, env: TradingEnvironment) -> TrainingResult:
        """评估一轮"""
        state, info = env.reset()
        total_reward = 0
        done = False

        self.agent.eval_mode()

        while not done:
            action = self.agent.select_action(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward
            state = next_state

        history_df = env.get_history_df()

        return TrainingResult(
            episode=-1,
            total_reward=total_reward,
            total_return=info.get("return_pct", 0),
            max_drawdown=info.get("max_drawdown", 0),
            sharpe_ratio=self._calculate_sharpe(history_df),
            win_rate=info.get("win_rate", 0),
            total_trades=info.get("total_trades", 0),
            final_value=info.get("total_value", self.config.initial_capital),
        )

    def _calculate_sharpe(self, history_df: pd.DataFrame, risk_free_rate: float = 0.0) -> float:
        """计算夏普比率"""
        if len(history_df) < 2:
            return 0.0

        values = history_df["total_value"].values
        returns = np.diff(values) / values[:-1]

        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        sharpe = (np.mean(returns) - risk_free_rate) / np.std(returns)
        # 年化（假设每小时一个数据点）
        sharpe *= np.sqrt(24 * 365)

        return sharpe

    def _print_progress(self, episode: int, result: TrainingResult):
        """打印进度"""
        logger.info(
            "训练进度",
            episode=f"{episode}/{self.config.total_episodes}",
            total_return=f"{result.total_return:.2f}%",
            max_drawdown=f"{result.max_drawdown*100:.2f}%",
            sharpe_ratio=f"{result.sharpe_ratio:.2f}",
            trades=result.total_trades,
            win_rate=f"{result.win_rate*100:.1f}%",
            best_return=f"{self.best_return:.2f}%",
            best_episode=self.best_episode,
        )

    def _save_best_model(self):
        """保存最佳模型"""
        path = os.path.join(self.config.save_dir, "best_model.pt")
        self.agent.save(path)

    def _save_checkpoint(self, episode: int):
        """保存检查点"""
        path = os.path.join(self.config.save_dir, f"checkpoint_ep{episode}.pt")
        self.agent.save(path)

        # 保存训练历史
        history_path = os.path.join(self.config.log_dir, "training_history.json")
        with open(history_path, "w") as f:
            json.dump([r.to_dict() for r in self.training_history], f, indent=2)

    def evaluate(self, df: pd.DataFrame) -> TrainingResult:
        """评估模型"""
        if self.feature_engineer is None or self.agent is None:
            raise RuntimeError("Model not trained. Call train() first.")

        # 处理数据
        processed_df = self.feature_engineer.transform(df)

        # 创建环境
        env = self.create_environment(processed_df)

        # 评估
        result = self._evaluate_episode(env)

        logger.info(
            "评估结果",
            total_return=f"{result.total_return:.2f}%",
            max_drawdown=f"{result.max_drawdown*100:.2f}%",
            sharpe_ratio=f"{result.sharpe_ratio:.2f}",
            trades=result.total_trades,
            win_rate=f"{result.win_rate*100:.1f}%",
        )

        return result

    def predict(self, df: pd.DataFrame) -> List[int]:
        """预测动作"""
        if self.feature_engineer is None or self.agent is None:
            raise RuntimeError("Model not trained. Call train() first.")

        processed_df = self.feature_engineer.transform(df)
        env = self.create_environment(processed_df)

        state, _ = env.reset()
        actions = []

        self.agent.eval_mode()

        for _ in range(len(processed_df) - self.config.window_size - 1):
            action = self.agent.select_action(state)
            actions.append(action)

            next_state, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
            state = next_state

        return actions

    def save(self, path: str = None):
        """保存完整模型"""
        if path is None:
            path = os.path.join(self.config.save_dir, "ai_trader.pt")

        # 保存 Agent
        self.agent.save(path)

        # 保存配置和特征工程器参数
        meta_path = path.replace(".pt", "_meta.json")
        meta = {
            "config": self.config.__dict__,
            "feature_names": self.feature_engineer.get_feature_names(),
            "scalers": {k: list(v) for k, v in self.feature_engineer.scalers.items()},
            "best_return": self.best_return,
            "best_episode": self.best_episode,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        logger.info("模型已保存", path=path)

    def load(self, path: str):
        """加载模型"""
        # 加载元数据
        meta_path = path.replace(".pt", "_meta.json")
        with open(meta_path, "r") as f:
            meta = json.load(f)

        # 恢复配置
        self.config = TrainingConfig(**meta["config"])

        # 恢复特征工程器
        self.feature_engineer = FeatureEngineer()
        self.feature_engineer.feature_names = meta["feature_names"]
        self.feature_engineer.scalers = {k: tuple(v) for k, v in meta["scalers"].items()}

        # 创建并加载 Agent
        state_dim = len(meta["feature_names"]) * self.config.window_size + 4
        action_dim = 3  # Hold, Buy, Sell

        self.agent = self.create_agent(state_dim, action_dim)
        self.agent.load(path)

        self.best_return = meta.get("best_return", 0)
        self.best_episode = meta.get("best_episode", 0)

        logger.info("模型已加载", path=path, best_return=f"{self.best_return:.2f}%", best_episode=self.best_episode)

    def get_training_summary(self) -> Dict:
        """获取训练摘要"""
        if not self.training_history:
            return {}

        returns = [r.total_return for r in self.training_history]
        drawdowns = [r.max_drawdown for r in self.training_history]
        sharpes = [r.sharpe_ratio for r in self.training_history]

        return {
            "total_episodes": len(self.training_history),
            "best_return": max(returns),
            "best_episode": returns.index(max(returns)),
            "avg_return": np.mean(returns),
            "avg_drawdown": np.mean(drawdowns),
            "avg_sharpe": np.mean(sharpes),
            "final_return": returns[-1],
        }
