"""
PPO 交易智能体
基于 Proximal Policy Optimization 的强化学习交易策略
适合连续动作空间和更稳定的训练
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    """
    Actor-Critic 网络
    Actor: 输出动作概率分布
    Critic: 输出状态价值
    """
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        super(ActorCritic, self).__init__()
        
        # 共享特征提取层
        self.shared = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )
        
        # Actor头 (策略网络)
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_size),
            nn.Softmax(dim=-1)
        )
        
        # Critic头 (价值网络)
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )
    
    def forward(self, state):
        features = self.shared(state)
        action_probs = self.actor(features)
        value = self.critic(features)
        return action_probs, value
    
    def act(self, state):
        """根据策略选择动作"""
        action_probs, value = self.forward(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        log_prob = dist.log_prob(action)
        return action, log_prob, value


class PPOMemory:
    """PPO经验缓冲区"""
    
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
    
    def store(self, state, action, reward, log_prob, value, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)
    
    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.log_probs.clear()
        self.values.clear()
        self.dones.clear()
    
    def get_batch(self):
        return (
            torch.FloatTensor(np.array(self.states)),
            torch.LongTensor(self.actions),
            torch.FloatTensor(self.rewards),
            torch.stack(self.log_probs),
            torch.cat(self.values),
            torch.FloatTensor(self.dones)
        )


class PPOAgent:
    """
    PPO 交易智能体
    
    使用近端策略优化算法，具有更稳定的训练过程
    """
    
    def __init__(self, state_size: int, action_size: int,
                 learning_rate: float = 0.0003,
                 gamma: float = 0.99,
                 gae_lambda: float = 0.95,
                 clip_epsilon: float = 0.2,
                 value_coef: float = 0.5,
                 entropy_coef: float = 0.01,
                 n_epochs: int = 10,
                 batch_size: int = 64):
        """
        初始化PPO智能体
        
        Args:
            state_size: 状态空间维度
            action_size: 动作空间大小
            learning_rate: 学习率
            gamma: 折扣因子
            gae_lambda: GAE lambda参数
            clip_epsilon: PPO裁剪参数
            value_coef: 价值损失系数
            entropy_coef: 熵正则化系数
            n_epochs: 每次更新的训练轮数
            batch_size: 批次大小
        """
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.policy = ActorCritic(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
        
        self.memory = PPOMemory()
    
    def select_action(self, state: np.ndarray, training: bool = True):
        """选择动作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action_probs, value = self.policy(state_tensor)
        
        if training:
            dist = Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
            return action.item(), log_prob, value
        else:
            return action_probs.argmax().item(), None, None
    
    def store_transition(self, state, action, reward, log_prob, value, done):
        """存储经验"""
        self.memory.store(state, action, reward, log_prob, value, done)
    
    def compute_gae(self, rewards, values, dones, next_value):
        """计算广义优势估计 (GAE)"""
        advantages = []
        gae = 0
        
        values = torch.cat([values, next_value])
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        advantages = torch.FloatTensor(advantages)
        returns = advantages + values[:-1]
        
        return advantages, returns
    
    def update(self, next_value):
        """更新策略"""
        states, actions, rewards, old_log_probs, values, dones = self.memory.get_batch()
        
        states = states.to(self.device)
        actions = actions.to(self.device)
        old_log_probs = old_log_probs.to(self.device)
        values = values.to(self.device)
        
        # 计算优势和回报
        advantages, returns = self.compute_gae(rewards, values, dones, next_value)
        advantages = advantages.to(self.device)
        returns = returns.to(self.device)
        
        # 标准化优势
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 多轮更新
        for _ in range(self.n_epochs):
            # 重新计算动作概率和价值
            action_probs, new_values = self.policy(states)
            dist = Categorical(action_probs)
            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()
            
            # 计算比率
            ratio = torch.exp(new_log_probs - old_log_probs)
            
            # PPO裁剪目标
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages
            
            # 计算损失
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(new_values.squeeze(), returns)
            
            loss = actor_loss + self.value_coef * critic_loss - self.entropy_coef * entropy
            
            # 优化
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
            self.optimizer.step()
        
        # 清空缓冲区
        self.memory.clear()
        
        return actor_loss.item(), critic_loss.item()
    
    def save(self, filepath: str):
        """保存模型"""
        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, filepath)
        print(f"PPO Model saved to {filepath}")
    
    def load(self, filepath: str):
        """加载模型"""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        print(f"PPO Model loaded from {filepath}")


def train_ppo(env, agent, n_episodes: int = 100, update_freq: int = 20, verbose: bool = True):
    """
    使用PPO训练智能体
    
    Args:
        env: 交易环境
        agent: PPO智能体
        n_episodes: 训练回合数
        update_freq: 更新频率
        verbose: 是否打印训练信息
    """
    episode_rewards = []
    episode_profits = []
    step_count = 0
    
    for episode in range(n_episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            action, log_prob, value = agent.select_action(state, training=True)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            agent.store_transition(state, action, reward, log_prob, value, done)
            
            state = next_state
            total_reward += reward
            step_count += 1
            
            # 定期更新
            if step_count % update_freq == 0 and not done:
                with torch.no_grad():
                    _, next_value = agent.policy(
                        torch.FloatTensor(next_state).unsqueeze(0).to(agent.device)
                    )
                agent.update(next_value)
        
        # 回合结束时更新
        if len(agent.memory.states) > 0:
            next_value = torch.zeros(1).to(agent.device)
            agent.update(next_value)
        
        episode_rewards.append(total_reward)
        episode_profits.append(info['total_profit'])
        
        if verbose and (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_profit = np.mean(episode_profits[-10:])
            print(f"Episode {episode + 1}/{n_episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Profit: ${avg_profit:.2f}")
    
    return episode_rewards, episode_profits
