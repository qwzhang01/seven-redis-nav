"""
强化学习 Agent 实现

实现多种 RL 算法用于训练 AI 交易员：
- DQN (Deep Q-Network)
- PPO (Proximal Policy Optimization)
- A2C (Advantage Actor-Critic)
"""

import numpy as np
import structlog
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import deque
import random


@dataclass
class Experience:
    """经验样本"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


logger = structlog.get_logger(__name__)


class ReplayBuffer:
    """经验回放缓冲区"""

    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)

    def push(self, experience: Experience):
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)


class PrioritizedReplayBuffer:
    """优先级经验回放缓冲区"""

    def __init__(self, capacity: int = 100000, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha
        self.buffer = []
        self.priorities = []
        self.position = 0

    def push(self, experience: Experience, priority: float = 1.0):
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority ** self.alpha)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = priority ** self.alpha
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, beta: float = 0.4) -> Tuple[List[Experience], np.ndarray, List[int]]:
        priorities = np.array(self.priorities)
        probabilities = priorities / priorities.sum()

        indices = np.random.choice(len(self.buffer), min(batch_size, len(self.buffer)),
                                   p=probabilities, replace=False)

        experiences = [self.buffer[i] for i in indices]

        # 计算重要性采样权重
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-beta)
        weights /= weights.max()

        return experiences, weights, indices.tolist()

    def update_priorities(self, indices: List[int], priorities: List[float]):
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority ** self.alpha

    def __len__(self):
        return len(self.buffer)


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        device: str = "cpu"
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.device = device

        self.training = True
        self.total_steps = 0

    @abstractmethod
    def select_action(self, state: np.ndarray) -> int:
        """选择动作"""
        pass

    @abstractmethod
    def update(self, experiences: List[Experience]) -> Dict[str, float]:
        """更新模型"""
        pass

    @abstractmethod
    def save(self, path: str):
        """保存模型"""
        pass

    @abstractmethod
    def load(self, path: str):
        """加载模型"""
        pass

    def train_mode(self):
        self.training = True

    def eval_mode(self):
        self.training = False


class DQNAgent(BaseAgent):
    """
    Deep Q-Network (DQN) Agent

    DQN 是最经典的深度强化学习算法之一。

    核心思想：
    - 使用神经网络近似 Q 函数
    - 经验回放打破数据相关性
    - 目标网络稳定训练

    算法流程：
    1. 使用 ε-greedy 策略选择动作
    2. 执行动作，获得奖励和新状态
    3. 将经验存入回放缓冲区
    4. 从缓冲区采样批量数据
    5. 计算 TD 目标：r + γ * max_a' Q(s', a')
    6. 更新 Q 网络最小化 TD 误差
    7. 定期更新目标网络
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 100000,
        batch_size: int = 64,
        target_update_freq: int = 100,
        hidden_dims: List[int] = None,
        use_double_dqn: bool = True,
        use_dueling: bool = True,
        use_per: bool = False,
        device: str = "cpu"
    ):
        super().__init__(state_dim, action_dim, learning_rate, gamma, device)

        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.use_double_dqn = use_double_dqn
        self.use_dueling = use_dueling
        self.use_per = use_per

        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        # 经验回放缓冲区
        if use_per:
            self.replay_buffer = PrioritizedReplayBuffer(buffer_size)
        else:
            self.replay_buffer = ReplayBuffer(buffer_size)

        # 构建网络
        self._build_network(hidden_dims)

    def _build_network(self, hidden_dims: List[int]):
        """构建 Q 网络"""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim

            self.torch = torch

            if self.use_dueling:
                # Dueling DQN 架构
                class DuelingNetwork(nn.Module):
                    def __init__(self, state_dim, action_dim, hidden_dims):
                        super().__init__()

                        # 共享特征层
                        layers = []
                        prev_dim = state_dim
                        for dim in hidden_dims[:-1]:
                            layers.extend([
                                nn.Linear(prev_dim, dim),
                                nn.ReLU(),
                                nn.LayerNorm(dim),
                            ])
                            prev_dim = dim
                        self.feature = nn.Sequential(*layers)

                        # 价值流
                        self.value_stream = nn.Sequential(
                            nn.Linear(prev_dim, hidden_dims[-1]),
                            nn.ReLU(),
                            nn.Linear(hidden_dims[-1], 1)
                        )

                        # 优势流
                        self.advantage_stream = nn.Sequential(
                            nn.Linear(prev_dim, hidden_dims[-1]),
                            nn.ReLU(),
                            nn.Linear(hidden_dims[-1], action_dim)
                        )

                    def forward(self, x):
                        features = self.feature(x)
                        value = self.value_stream(features)
                        advantage = self.advantage_stream(features)
                        # Q = V + (A - mean(A))
                        q_values = value + advantage - advantage.mean(dim=-1, keepdim=True)
                        return q_values

                self.q_network = DuelingNetwork(self.state_dim, self.action_dim, hidden_dims).to(self.device)
                self.target_network = DuelingNetwork(self.state_dim, self.action_dim, hidden_dims).to(self.device)
            else:
                # 标准 DQN 架构
                class QNetwork(nn.Module):
                    def __init__(self, state_dim, action_dim, hidden_dims):
                        super().__init__()
                        layers = []
                        prev_dim = state_dim
                        for dim in hidden_dims:
                            layers.extend([
                                nn.Linear(prev_dim, dim),
                                nn.ReLU(),
                            ])
                            prev_dim = dim
                        layers.append(nn.Linear(prev_dim, action_dim))
                        self.network = nn.Sequential(*layers)

                    def forward(self, x):
                        return self.network(x)

                self.q_network = QNetwork(self.state_dim, self.action_dim, hidden_dims).to(self.device)
                self.target_network = QNetwork(self.state_dim, self.action_dim, hidden_dims).to(self.device)

            # 复制权重到目标网络
            self.target_network.load_state_dict(self.q_network.state_dict())

            # 优化器
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)

            self._torch_available = True

        except ImportError:
            logger.warning("PyTorch不可用，使用基于numpy的简单网络")
            self._torch_available = False
            self._build_numpy_network(hidden_dims)

    def _build_numpy_network(self, hidden_dims: List[int]):
        """构建 NumPy 版本的简单网络"""
        self.weights = []
        self.target_weights = []

        dims = [self.state_dim] + hidden_dims + [self.action_dim]

        for i in range(len(dims) - 1):
            # Xavier 初始化
            w = np.random.randn(dims[i], dims[i+1]) * np.sqrt(2.0 / dims[i])
            b = np.zeros(dims[i+1])
            self.weights.append((w, b))
            self.target_weights.append((w.copy(), b.copy()))

    def _forward_numpy(self, x: np.ndarray, weights: List) -> np.ndarray:
        """NumPy 前向传播"""
        for i, (w, b) in enumerate(weights):
            x = x @ w + b
            if i < len(weights) - 1:
                x = np.maximum(0, x)  # ReLU
        return x

    def select_action(self, state: np.ndarray) -> int:
        """选择动作（ε-greedy）"""
        if self.training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        if self._torch_available:
            with self.torch.no_grad():
                state_tensor = self.torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.q_network(state_tensor)
                return q_values.argmax().item()
        else:
            q_values = self._forward_numpy(state, self.weights)
            return np.argmax(q_values)

    def update(self, experiences: List[Experience] = None) -> Dict[str, float]:
        """更新 Q 网络"""
        if len(self.replay_buffer) < self.batch_size:
            return {}

        # 从回放缓冲区采样
        if self.use_per:
            experiences, weights, indices = self.replay_buffer.sample(self.batch_size)
        else:
            experiences = self.replay_buffer.sample(self.batch_size)
            weights = np.ones(len(experiences))
            indices = None

        if self._torch_available:
            return self._update_torch(experiences, weights, indices)
        else:
            return self._update_numpy(experiences)

    def _update_torch(self, experiences, weights, indices) -> Dict[str, float]:
        """PyTorch 版本的更新"""
        torch = self.torch

        # 转换为张量
        states = torch.FloatTensor(np.array([e.state for e in experiences])).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in experiences]).to(self.device)
        next_states = torch.FloatTensor(np.array([e.next_state for e in experiences])).to(self.device)
        dones = torch.FloatTensor([e.done for e in experiences]).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        # 计算当前 Q 值
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # 计算目标 Q 值
        with torch.no_grad():
            if self.use_double_dqn:
                # Double DQN：用 q_network 选动作，用 target_network 评估
                next_actions = self.q_network(next_states).argmax(1)
                next_q = self.target_network(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            else:
                next_q = self.target_network(next_states).max(1)[0]

            target_q = rewards + self.gamma * next_q * (1 - dones)

        # 计算 TD 误差
        td_errors = torch.abs(current_q - target_q).detach().cpu().numpy()

        # 计算损失（加权）
        loss = (weights * (current_q - target_q) ** 2).mean()

        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()

        # 更新优先级
        if self.use_per and indices is not None:
            self.replay_buffer.update_priorities(indices, td_errors.tolist())

        # 更新目标网络
        self.total_steps += 1
        if self.total_steps % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # 衰减 epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return {
            "loss": loss.item(),
            "q_mean": current_q.mean().item(),
            "epsilon": self.epsilon,
        }

    def _update_numpy(self, experiences) -> Dict[str, float]:
        """NumPy 版本的简单更新"""
        # 简化的梯度下降
        learning_rate = 0.001

        total_loss = 0
        for exp in experiences:
            # 计算当前 Q 值
            q_values = self._forward_numpy(exp.state, self.weights)
            current_q = q_values[exp.action]

            # 计算目标 Q 值
            next_q_values = self._forward_numpy(exp.next_state, self.target_weights)
            target_q = exp.reward + self.gamma * np.max(next_q_values) * (1 - exp.done)

            # TD 误差
            td_error = target_q - current_q
            total_loss += td_error ** 2

            # 简化的权重更新（只更新最后一层）
            w, b = self.weights[-1]
            grad = np.zeros_like(w)
            grad[:, exp.action] = -2 * td_error * self._get_last_hidden(exp.state)
            self.weights[-1] = (w - learning_rate * grad, b)

        # 更新目标网络
        self.total_steps += 1
        if self.total_steps % self.target_update_freq == 0:
            self.target_weights = [(w.copy(), b.copy()) for w, b in self.weights]

        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return {"loss": total_loss / len(experiences), "epsilon": self.epsilon}

    def _get_last_hidden(self, state):
        """获取最后一个隐藏层的输出"""
        x = state
        for w, b in self.weights[:-1]:
            x = np.maximum(0, x @ w + b)
        return x

    def store_experience(self, state, action, reward, next_state, done):
        """存储经验"""
        exp = Experience(state, action, reward, next_state, done)
        if self.use_per:
            # 新经验给予最高优先级
            max_priority = max(self.replay_buffer.priorities) if self.replay_buffer.priorities else 1.0
            self.replay_buffer.push(exp, max_priority)
        else:
            self.replay_buffer.push(exp)

    def save(self, path: str):
        """保存模型"""
        if self._torch_available:
            self.torch.save({
                "q_network": self.q_network.state_dict(),
                "target_network": self.target_network.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "total_steps": self.total_steps,
            }, path)
        else:
            np.savez(path,
                     weights=self.weights,
                     target_weights=self.target_weights,
                     epsilon=self.epsilon,
                     total_steps=self.total_steps)

    def load(self, path: str):
        """加载模型"""
        if self._torch_available:
            checkpoint = self.torch.load(path, map_location=self.device)
            self.q_network.load_state_dict(checkpoint["q_network"])
            self.target_network.load_state_dict(checkpoint["target_network"])
            self.optimizer.load_state_dict(checkpoint["optimizer"])
            self.epsilon = checkpoint["epsilon"]
            self.total_steps = checkpoint["total_steps"]
        else:
            data = np.load(path, allow_pickle=True)
            self.weights = data["weights"].tolist()
            self.target_weights = data["target_weights"].tolist()
            self.epsilon = data["epsilon"].item()
            self.total_steps = data["total_steps"].item()


class PPOAgent(BaseAgent):
    """
    Proximal Policy Optimization (PPO) Agent

    PPO 是目前最流行的策略梯度算法之一。

    核心思想：
    - 使用 Actor-Critic 架构
    - 通过裁剪限制策略更新幅度
    - 平衡探索和利用

    优点：
    - 稳定性好
    - 样本效率较高
    - 超参数相对不敏感
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.0003,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        n_epochs: int = 10,
        batch_size: int = 64,
        hidden_dims: List[int] = None,
        device: str = "cpu"
    ):
        super().__init__(state_dim, action_dim, learning_rate, gamma, device)

        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        self.n_epochs = n_epochs
        self.batch_size = batch_size

        if hidden_dims is None:
            hidden_dims = [256, 128]

        # 轨迹缓冲区
        self.trajectory = []

        self._build_network(hidden_dims)

    def _build_network(self, hidden_dims: List[int]):
        """构建 Actor-Critic 网络"""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.distributions import Categorical

            self.torch = torch
            self.Categorical = Categorical

            class ActorCritic(nn.Module):
                def __init__(self, state_dim, action_dim, hidden_dims):
                    super().__init__()

                    # 共享特征提取器
                    layers = []
                    prev_dim = state_dim
                    for dim in hidden_dims:
                        layers.extend([
                            nn.Linear(prev_dim, dim),
                            nn.Tanh(),
                        ])
                        prev_dim = dim
                    self.features = nn.Sequential(*layers)

                    # Actor（策略网络）
                    self.actor = nn.Sequential(
                        nn.Linear(prev_dim, action_dim),
                        nn.Softmax(dim=-1)
                    )

                    # Critic（价值网络）
                    self.critic = nn.Linear(prev_dim, 1)

                def forward(self, x):
                    features = self.features(x)
                    action_probs = self.actor(features)
                    value = self.critic(features)
                    return action_probs, value

                def get_action(self, state):
                    action_probs, value = self.forward(state)
                    dist = Categorical(action_probs)
                    action = dist.sample()
                    log_prob = dist.log_prob(action)
                    return action, log_prob, value

                def evaluate(self, states, actions):
                    action_probs, values = self.forward(states)
                    dist = Categorical(action_probs)
                    log_probs = dist.log_prob(actions)
                    entropy = dist.entropy()
                    return log_probs, values.squeeze(-1), entropy

            self.network = ActorCritic(self.state_dim, self.action_dim, hidden_dims).to(self.device)
            self.optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)

            self._torch_available = True

        except ImportError:
            logger.warning("PyTorch不可用，PPO算法需要PyTorch支持")
            self._torch_available = False

    def select_action(self, state: np.ndarray) -> int:
        """选择动作"""
        if not self._torch_available:
            return random.randint(0, self.action_dim - 1)

        with self.torch.no_grad():
            state_tensor = self.torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action, log_prob, value = self.network.get_action(state_tensor)

            if self.training:
                # 保存用于更新的信息
                self._last_log_prob = log_prob.item()
                self._last_value = value.item()

            return action.item()

    def store_transition(self, state, action, reward, next_state, done):
        """存储转移"""
        self.trajectory.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "log_prob": getattr(self, "_last_log_prob", 0),
            "value": getattr(self, "_last_value", 0),
        })

    def update(self, experiences: List = None) -> Dict[str, float]:
        """更新网络"""
        if not self._torch_available or len(self.trajectory) == 0:
            return {}

        # 计算 GAE（广义优势估计）
        advantages, returns = self._compute_gae()

        # 准备数据
        states = self.torch.FloatTensor(np.array([t["state"] for t in self.trajectory])).to(self.device)
        actions = self.torch.LongTensor([t["action"] for t in self.trajectory]).to(self.device)
        old_log_probs = self.torch.FloatTensor([t["log_prob"] for t in self.trajectory]).to(self.device)
        advantages = self.torch.FloatTensor(advantages).to(self.device)
        returns = self.torch.FloatTensor(returns).to(self.device)

        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # 多轮更新
        total_loss = 0
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0

        dataset_size = len(self.trajectory)

        for _ in range(self.n_epochs):
            # 随机打乱
            indices = np.random.permutation(dataset_size)

            for start in range(0, dataset_size, self.batch_size):
                end = min(start + self.batch_size, dataset_size)
                batch_indices = indices[start:end]

                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]

                # 评估当前策略
                log_probs, values, entropy = self.network.evaluate(batch_states, batch_actions)

                # 计算比率
                ratio = (log_probs - batch_old_log_probs).exp()

                # 裁剪的策略损失
                surr1 = ratio * batch_advantages
                surr2 = self.torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -self.torch.min(surr1, surr2).mean()

                # 价值损失
                value_loss = ((values - batch_returns) ** 2).mean()

                # 熵奖励（鼓励探索）
                entropy_loss = -entropy.mean()

                # 总损失
                loss = policy_loss + self.value_coef * value_loss + self.entropy_coef * entropy_loss

                # 优化
                self.optimizer.zero_grad()
                loss.backward()
                self.torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
                self.optimizer.step()

                total_loss += loss.item()
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()

        # 清空轨迹
        self.trajectory = []

        n_updates = self.n_epochs * (dataset_size // self.batch_size + 1)

        return {
            "loss": total_loss / n_updates,
            "policy_loss": total_policy_loss / n_updates,
            "value_loss": total_value_loss / n_updates,
            "entropy": total_entropy / n_updates,
        }

    def _compute_gae(self):
        """计算广义优势估计 (GAE)"""
        rewards = [t["reward"] for t in self.trajectory]
        values = [t["value"] for t in self.trajectory]
        dones = [t["done"] for t in self.trajectory]

        # 获取最后一个状态的价值
        with self.torch.no_grad():
            last_state = self.torch.FloatTensor(self.trajectory[-1]["next_state"]).unsqueeze(0).to(self.device)
            _, last_value = self.network(last_state)
            next_value = last_value.item()

        advantages = []
        returns = []
        gae = 0

        for i in reversed(range(len(self.trajectory))):
            if dones[i]:
                next_value = 0
                gae = 0

            delta = rewards[i] + self.gamma * next_value - values[i]
            gae = delta + self.gamma * self.gae_lambda * gae

            advantages.insert(0, gae)
            returns.insert(0, gae + values[i])

            next_value = values[i]

        return advantages, returns

    def save(self, path: str):
        if self._torch_available:
            self.torch.save({
                "network": self.network.state_dict(),
                "optimizer": self.optimizer.state_dict(),
            }, path)

    def load(self, path: str):
        if self._torch_available:
            checkpoint = self.torch.load(path, map_location=self.device)
            self.network.load_state_dict(checkpoint["network"])
            self.optimizer.load_state_dict(checkpoint["optimizer"])


class A2CAgent(BaseAgent):
    """
    Advantage Actor-Critic (A2C) Agent

    A2C 是 PPO 的简化版本，直接使用优势函数更新。

    核心思想：
    - Actor 输出动作概率
    - Critic 评估状态价值
    - 使用优势函数减少方差
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.0007,
        gamma: float = 0.99,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        n_steps: int = 5,
        hidden_dims: List[int] = None,
        device: str = "cpu"
    ):
        super().__init__(state_dim, action_dim, learning_rate, gamma, device)

        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        self.n_steps = n_steps

        if hidden_dims is None:
            hidden_dims = [128, 64]

        self.trajectory = []

        self._build_network(hidden_dims)

    def _build_network(self, hidden_dims):
        """构建网络"""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.distributions import Categorical

            self.torch = torch
            self.Categorical = Categorical

            class A2CNetwork(nn.Module):
                def __init__(self, state_dim, action_dim, hidden_dims):
                    super().__init__()

                    # 共享层
                    layers = []
                    prev_dim = state_dim
                    for dim in hidden_dims:
                        layers.extend([
                            nn.Linear(prev_dim, dim),
                            nn.ReLU(),
                        ])
                        prev_dim = dim
                    self.shared = nn.Sequential(*layers)

                    # Actor
                    self.actor = nn.Linear(prev_dim, action_dim)

                    # Critic
                    self.critic = nn.Linear(prev_dim, 1)

                def forward(self, x):
                    shared = self.shared(x)
                    return self.actor(shared), self.critic(shared)

            self.network = A2CNetwork(self.state_dim, self.action_dim, hidden_dims).to(self.device)
            self.optimizer = optim.Adam(self.network.parameters(), lr=self.learning_rate)

            self._torch_available = True

        except ImportError:
            self._torch_available = False

    def select_action(self, state: np.ndarray) -> int:
        if not self._torch_available:
            return random.randint(0, self.action_dim - 1)

        with self.torch.no_grad():
            state_tensor = self.torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action_logits, value = self.network(state_tensor)
            probs = self.torch.softmax(action_logits, dim=-1)
            dist = self.Categorical(probs)
            action = dist.sample()

            if self.training:
                self._last_log_prob = dist.log_prob(action).item()
                self._last_value = value.item()

            return action.item()

    def store_transition(self, state, action, reward, next_state, done):
        self.trajectory.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "log_prob": getattr(self, "_last_log_prob", 0),
            "value": getattr(self, "_last_value", 0),
        })

    def update(self, experiences=None) -> Dict[str, float]:
        if not self._torch_available or len(self.trajectory) < self.n_steps:
            return {}

        # 计算回报和优势
        returns = []
        advantages = []

        # 获取最后状态的价值
        with self.torch.no_grad():
            last_state = self.torch.FloatTensor(self.trajectory[-1]["next_state"]).unsqueeze(0).to(self.device)
            _, last_value = self.network(last_state)
            R = last_value.item() if not self.trajectory[-1]["done"] else 0

        for t in reversed(self.trajectory):
            R = t["reward"] + self.gamma * R * (1 - t["done"])
            returns.insert(0, R)
            advantages.insert(0, R - t["value"])

        # 转换为张量
        states = self.torch.FloatTensor(np.array([t["state"] for t in self.trajectory])).to(self.device)
        actions = self.torch.LongTensor([t["action"] for t in self.trajectory]).to(self.device)
        returns = self.torch.FloatTensor(returns).to(self.device)
        advantages = self.torch.FloatTensor(advantages).to(self.device)

        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # 前向传播
        action_logits, values = self.network(states)
        probs = self.torch.softmax(action_logits, dim=-1)
        dist = self.Categorical(probs)

        log_probs = dist.log_prob(actions)
        entropy = dist.entropy().mean()

        # 计算损失
        policy_loss = -(log_probs * advantages.detach()).mean()
        value_loss = ((values.squeeze(-1) - returns) ** 2).mean()

        loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        self.torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
        self.optimizer.step()

        # 清空轨迹
        self.trajectory = []

        return {
            "loss": loss.item(),
            "policy_loss": policy_loss.item(),
            "value_loss": value_loss.item(),
            "entropy": entropy.item(),
        }

    def save(self, path: str):
        if self._torch_available:
            self.torch.save({
                "network": self.network.state_dict(),
                "optimizer": self.optimizer.state_dict(),
            }, path)

    def load(self, path: str):
        if self._torch_available:
            checkpoint = self.torch.load(path, map_location=self.device)
            self.network.load_state_dict(checkpoint["network"])
            self.optimizer.load_state_dict(checkpoint["optimizer"])
