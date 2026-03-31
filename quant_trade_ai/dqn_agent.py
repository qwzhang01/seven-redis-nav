"""
================================================================================
DQN 交易智能体
================================================================================

本模块实现了基于 Deep Q-Network (DQN) 的交易智能体。

什么是 DQN？
-----------
DQN 是 DeepMind 在2013年提出的算法，将深度学习与 Q-learning 结合，
使得强化学习能够处理高维状态空间的问题。

核心思想：
---------
1. 使用神经网络来近似 Q(s, a) 函数
2. Q值表示在状态s下执行动作a的预期累计奖励
3. 智能体学会选择Q值最高的动作

关键技术：
---------
1. 经验回放 (Experience Replay)
   - 将交互经验存储在缓冲区
   - 训练时随机采样，打破数据相关性
   
2. 目标网络 (Target Network)
   - 使用两个网络：主网络和目标网络
   - 目标网络提供稳定的学习目标
   
3. ε-贪婪策略 (ε-greedy)
   - 平衡探索（尝试新动作）和利用（选择已知最优）

使用方法：
---------
>>> from dqn_agent import DQNAgent
>>> 
>>> # 创建智能体
>>> agent = DQNAgent(state_size=14, action_size=3)
>>> 
>>> # 选择动作
>>> action = agent.select_action(state)
>>> 
>>> # 存储经验
>>> agent.store_experience(state, action, reward, next_state, done)
>>> 
>>> # 训练
>>> loss = agent.train_step()
>>> 
>>> # 保存/加载模型
>>> agent.save('model.pth')
>>> agent.load('model.pth')

作者: AI Trading Demo
版本: 1.0
================================================================================
"""

# ============================================================================
# 导入必要的库
# ============================================================================
import numpy as np          # 数值计算
import torch                # PyTorch 深度学习框架
import torch.nn as nn       # 神经网络模块
import torch.optim as optim # 优化器
import random               # 随机数生成
from collections import deque, namedtuple  # 数据结构


# ============================================================================
# 经验元组定义
# ============================================================================
# namedtuple 创建一个轻量级的类，用于存储一次交互的信息
# 相比普通元组，命名元组可以通过属性名访问，代码更清晰
Experience = namedtuple('Experience', [
    'state',      # 当前状态 (14维向量)
    'action',     # 执行的动作 (0, 1, 或 2)
    'reward',     # 获得的奖励 (浮点数)
    'next_state', # 下一个状态 (14维向量)
    'done'        # 是否结束 (布尔值)
])


class QNetwork(nn.Module):
    """
    Q值神经网络
    
    神经网络用于近似 Q(s, a) 函数，即估计在某个状态下执行某个动作的价值。
    
    网络结构：
    ---------
    输入层 (14个神经元) - 状态特征
       ↓
    隐藏层1 (128个神经元) - ReLU激活 - Dropout(0.2)
       ↓
    隐藏层2 (64个神经元) - ReLU激活 - Dropout(0.2)
       ↓
    隐藏层3 (32个神经元) - ReLU激活 - Dropout(0.2)
       ↓
    输出层 (3个神经元) - 每个动作的Q值
    
    为什么这样设计？
    ---------------
    1. 逐层减少神经元数量：从高维特征逐步抽象到低维决策
    2. ReLU激活函数：引入非线性，计算简单高效
    3. Dropout正则化：随机丢弃神经元，防止过拟合
    """
    
    def __init__(self, state_size: int, action_size: int, 
                 hidden_sizes: list = [128, 64, 32]):
        """
        初始化Q网络
        
        参数：
        -----
        state_size : int
            状态空间维度（输入大小）
            本项目中为14（12个技术指标 + 2个账户状态）
            
        action_size : int
            动作空间大小（输出大小）
            本项目中为3（买入/卖出/持有）
            
        hidden_sizes : list
            隐藏层大小列表
            默认 [128, 64, 32]，可以根据问题复杂度调整
        """
        # 调用父类构造函数（PyTorch要求）
        super(QNetwork, self).__init__()
        
        # 用于存储所有层
        layers = []
        prev_size = state_size  # 上一层的输出大小
        
        # ====================================================================
        # 构建隐藏层
        # ====================================================================
        for hidden_size in hidden_sizes:
            # ----------------------------------------------------------------
            # 全连接层 (Linear / Dense)
            # ----------------------------------------------------------------
            # 线性变换: y = Wx + b
            # - W: 权重矩阵，shape=(prev_size, hidden_size)
            # - b: 偏置向量，shape=(hidden_size,)
            # 全连接意味着上一层每个神经元都与下一层每个神经元相连
            layers.append(nn.Linear(prev_size, hidden_size))
            
            # ----------------------------------------------------------------
            # ReLU 激活函数
            # ----------------------------------------------------------------
            # ReLU(x) = max(0, x)
            # 
            # 为什么需要激活函数？
            # - 如果没有激活函数，多层线性变换等价于一层
            # - 激活函数引入非线性，让网络能学习复杂的模式
            # 
            # 为什么选择ReLU？
            # - 计算简单快速
            # - 不会有梯度消失问题（正区间梯度恒为1）
            # - 稀疏激活（负值输出0）
            layers.append(nn.ReLU())
            
            # ----------------------------------------------------------------
            # Dropout 正则化
            # ----------------------------------------------------------------
            # 训练时随机将20%的神经元输出设为0
            # 
            # 为什么使用Dropout？
            # - 防止过拟合：模型不能依赖特定神经元
            # - 相当于训练多个子网络的集成
            # - 测试时不使用Dropout（自动处理）
            layers.append(nn.Dropout(0.2))
            
            prev_size = hidden_size  # 更新上一层大小
        
        # ====================================================================
        # 输出层
        # ====================================================================
        # 不添加激活函数，因为Q值可以是任意实数（正/负/零）
        layers.append(nn.Linear(prev_size, action_size))
        
        # ====================================================================
        # 将所有层组合成序列模型
        # ====================================================================
        # Sequential 按顺序执行所有层
        # *layers 解包列表作为参数
        self.network = nn.Sequential(*layers)
    
    def forward(self, state):
        """
        前向传播
        
        数据从输入层流向输出层的过程。
        
        参数：
        -----
        state : torch.Tensor
            状态张量，shape可以是：
            - (state_size,): 单个状态
            - (batch_size, state_size): 一批状态
        
        返回：
        -----
        q_values : torch.Tensor
            每个动作的Q值，shape=(batch_size, action_size)
        
        示例：
        ------
        >>> network = QNetwork(state_size=14, action_size=3)
        >>> state = torch.randn(1, 14)  # 一个状态
        >>> q_values = network(state)
        >>> print(q_values.shape)  # torch.Size([1, 3])
        """
        return self.network(state)


class ReplayBuffer:
    """
    经验回放缓冲区
    
    经验回放是DQN的关键技术之一，用于存储和重用历史交互数据。
    
    为什么需要经验回放？
    -------------------
    1. 打破时间相关性
       - 连续的交易数据高度相关
       - 如果按顺序学习，网络会"忘记"之前学到的
       - 随机采样打破这种相关性
       
    2. 提高数据利用效率
       - 每条经验可以被多次使用
       - 不像在线学习那样只用一次就丢弃
       
    3. 稳定训练
       - 减少训练过程中的震荡
       - 让学习更加平滑
    
    实现细节：
    ---------
    使用固定大小的队列（deque）：
    - 新经验添加到队尾
    - 超出容量时自动删除队头（最旧的经验）
    """
    
    def __init__(self, capacity: int = 100000):
        """
        初始化缓冲区
        
        参数：
        -----
        capacity : int
            缓冲区最大容量
            容量太小：可能丢失有价值的经验
            容量太大：可能包含过时的经验，占用内存
            100000是一个常用的默认值
        """
        # deque是双端队列，支持高效的头尾操作
        # maxlen设置最大长度，满时自动删除最旧元素
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """
        添加一条经验到缓冲区
        
        参数：
        -----
        state : np.ndarray
            当前状态
        action : int
            执行的动作
        reward : float
            获得的奖励
        next_state : np.ndarray
            下一个状态
        done : bool
            是否为终止状态
        """
        # 创建Experience命名元组并添加到缓冲区
        self.buffer.append(Experience(state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        """
        从缓冲区随机采样一批经验
        
        参数：
        -----
        batch_size : int
            采样数量
        
        返回：
        -----
        states : torch.FloatTensor, shape=(batch_size, state_size)
            状态批次
        actions : torch.LongTensor, shape=(batch_size,)
            动作批次
        rewards : torch.FloatTensor, shape=(batch_size,)
            奖励批次
        next_states : torch.FloatTensor, shape=(batch_size, state_size)
            下一状态批次
        dones : torch.FloatTensor, shape=(batch_size,)
            终止标志批次
        """
        # 随机采样（不放回）
        experiences = random.sample(self.buffer, batch_size)
        
        # 将列表转换为NumPy数组，再转换为PyTorch张量
        # 这样可以进行批量计算，效率更高
        states = torch.FloatTensor(np.array([e.state for e in experiences]))
        actions = torch.LongTensor([e.action for e in experiences])
        rewards = torch.FloatTensor([e.reward for e in experiences])
        next_states = torch.FloatTensor(np.array([e.next_state for e in experiences]))
        dones = torch.FloatTensor([e.done for e in experiences])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        """返回当前缓冲区中的经验数量"""
        return len(self.buffer)


class DQNAgent:
    """
    DQN 交易智能体
    
    这是项目的核心类，实现了完整的DQN算法。
    
    算法流程：
    ---------
    1. 观察当前状态 s
    2. 使用ε-greedy策略选择动作 a
    3. 执行动作，观察奖励 r 和新状态 s'
    4. 将经验 (s, a, r, s', done) 存入缓冲区
    5. 从缓冲区采样一批经验
    6. 计算目标Q值和损失
    7. 更新神经网络参数
    8. 定期更新目标网络
    9. 衰减探索率
    10. 回到步骤1
    
    使用的改进技术：
    ---------------
    1. Double DQN: 减少Q值过估计
       - 主网络选择动作
       - 目标网络评估Q值
       
    2. 梯度裁剪: 防止梯度爆炸
       - 将梯度范数限制在1.0以内
    """
    
    def __init__(self, state_size: int, action_size: int, 
                 learning_rate: float = 0.001,
                 gamma: float = 0.99,
                 epsilon_start: float = 1.0,
                 epsilon_end: float = 0.01,
                 epsilon_decay: float = 0.995,
                 buffer_size: int = 100000,
                 batch_size: int = 64,
                 target_update_freq: int = 10):
        """
        初始化DQN智能体
        
        参数详解：
        ---------
        state_size : int
            状态空间维度
            本项目中为14
            
        action_size : int
            动作空间大小
            本项目中为3（买/卖/持有）
            
        learning_rate : float, 默认=0.001
            神经网络学习率
            控制每次参数更新的步长
            
            调参建议：
            - 太大(>0.01): 训练不稳定，可能发散
            - 太小(<0.0001): 收敛太慢
            - 常用范围: 0.0001 ~ 0.01
            
        gamma : float, 默认=0.99
            折扣因子（discount factor）
            决定未来奖励的重要性
            
            数学意义：
            - γ=0: 只关心即时奖励
            - γ=1: 同等重视所有奖励
            - γ=0.99: 100步后的奖励约等于现在的0.37倍
            
            调参建议：
            - 短期策略: 0.9 ~ 0.95
            - 长期策略: 0.99 ~ 0.999
            
        epsilon_start : float, 默认=1.0
            初始探索率
            训练开始时随机选择动作的概率
            1.0表示完全随机，先广泛探索
            
        epsilon_end : float, 默认=0.01
            最终探索率
            训练结束后保留的最小探索概率
            保留一定探索防止陷入局部最优
            
        epsilon_decay : float, 默认=0.995
            探索率衰减系数
            每步后 epsilon = epsilon × decay
            
            计算示例：
            - decay=0.995: 约500步后epsilon减半
            - decay=0.99: 约70步后epsilon减半
            
        buffer_size : int, 默认=100000
            经验缓冲区大小
            
        batch_size : int, 默认=64
            每次训练使用的样本数
            
            调参建议：
            - 太小(<16): 梯度估计方差大
            - 太大(>256): 内存占用大，收敛可能变慢
            - 常用: 32, 64, 128
            
        target_update_freq : int, 默认=10
            目标网络更新频率
            每多少步将主网络参数复制到目标网络
        """
        # 保存参数
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        
        # ====================================================================
        # 选择计算设备
        # ====================================================================
        # 优先使用GPU加速，如果没有则使用CPU
        # cuda: NVIDIA GPU
        # mps: Apple Silicon GPU (M1/M2)
        # cpu: 中央处理器
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # ====================================================================
        # 创建神经网络
        # ====================================================================
        # 主网络（Q-Network）：用于选择动作和训练
        self.q_network = QNetwork(state_size, action_size).to(self.device)
        
        # 目标网络（Target Network）：用于计算目标Q值
        # 初始时与主网络参数相同
        self.target_network = QNetwork(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # ====================================================================
        # 优化器
        # ====================================================================
        # Adam: 自适应学习率优化算法
        # 自动调整每个参数的学习率，是目前最常用的优化器
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # ====================================================================
        # 损失函数
        # ====================================================================
        # MSE (Mean Squared Error): 均方误差
        # Loss = mean((predicted - target)²)
        self.loss_fn = nn.MSELoss()
        
        # ====================================================================
        # 经验回放缓冲区
        # ====================================================================
        self.memory = ReplayBuffer(buffer_size)
        
        # 训练统计
        self.training_step = 0  # 总训练步数
        self.losses = []        # 损失值历史
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        选择动作
        
        使用ε-贪婪策略（epsilon-greedy）选择动作：
        - 以概率 ε 随机选择动作（探索）
        - 以概率 1-ε 选择Q值最大的动作（利用）
        
        为什么需要探索？
        ---------------
        如果智能体总是选择当前认为最好的动作，可能会：
        - 错过更好的策略
        - 陷入局部最优
        - 无法适应市场变化
        
        探索让智能体有机会发现新的盈利机会。
        
        参数：
        -----
        state : np.ndarray
            当前状态，shape=(state_size,)
            
        training : bool
            是否为训练模式
            训练时使用ε-greedy，测试时直接选择最优动作
        
        返回：
        -----
        action : int
            选择的动作（0, 1, 或 2）
        """
        # ====================================================================
        # 探索：随机选择动作
        # ====================================================================
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_size - 1)
        
        # ====================================================================
        # 利用：选择Q值最大的动作
        # ====================================================================
        with torch.no_grad():  # 不计算梯度，节省内存和计算
            # 将NumPy数组转换为PyTorch张量
            # unsqueeze(0): 添加batch维度，变成 (1, state_size)
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            
            # 前向传播，获取Q值
            q_values = self.q_network(state_tensor)
            
            # argmax: 返回最大值的索引，即最优动作
            # item(): 将张量转换为Python数字
            return q_values.argmax().item()
    
    def store_experience(self, state, action, reward, next_state, done):
        """
        存储一条经验
        
        将智能体与环境的一次交互存入经验缓冲区，
        以便后续训练时使用。
        
        参数：
        -----
        state : np.ndarray
            执行动作前的状态
        action : int
            执行的动作
        reward : float
            获得的奖励
        next_state : np.ndarray
            执行动作后的新状态
        done : bool
            是否到达终止状态
        """
        self.memory.push(state, action, reward, next_state, done)
    
    def train_step(self) -> float:
        """
        执行一步训练
        
        这是DQN学习的核心方法。
        
        训练流程：
        ---------
        1. 检查缓冲区是否有足够样本
        2. 从缓冲区随机采样一批经验
        3. 计算当前Q值：Q(s, a)
        4. 计算目标Q值：r + γ × max Q(s', a')
        5. 计算损失：MSE(当前Q值, 目标Q值)
        6. 反向传播，更新网络参数
        7. 定期同步目标网络
        8. 衰减探索率
        
        返回：
        -----
        loss : float
            训练损失值，可用于监控训练进度
        """
        # ====================================================================
        # 检查样本数量
        # ====================================================================
        # 如果缓冲区样本不足一个batch，跳过训练
        if len(self.memory) < self.batch_size:
            return 0.0
        
        # ====================================================================
        # 1. 采样经验
        # ====================================================================
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # 将数据移动到正确的设备（CPU/GPU）
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # ====================================================================
        # 2. 计算当前Q值
        # ====================================================================
        # q_network(states): 获取所有动作的Q值，shape=(batch_size, 3)
        # gather(1, actions.unsqueeze(1)): 选择实际执行的动作对应的Q值
        # squeeze(): 去掉多余的维度
        # 结果shape: (batch_size,)
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # ====================================================================
        # 3. 计算目标Q值 (Double DQN)
        # ====================================================================
        # Double DQN 的关键改进：
        # 标准DQN: target = r + γ × max_a Q_target(s', a)
        #   - 问题：使用同一个网络选择和评估，容易过高估计Q值
        # 
        # Double DQN: target = r + γ × Q_target(s', argmax_a Q_main(s', a))
        #   - 用主网络选择动作（argmax）
        #   - 用目标网络评估该动作的Q值
        #   - 减少过估计问题
        
        with torch.no_grad():  # 目标值不需要计算梯度
            # 用主网络选择下一状态的最优动作
            next_actions = self.q_network(next_states).argmax(1)
            
            # 用目标网络评估这些动作的Q值
            next_q_values = self.target_network(next_states).gather(
                1, next_actions.unsqueeze(1)
            ).squeeze()
            
            # 贝尔曼方程：Q = r + γ × Q'
            # done=1 时，没有下一状态，所以不加未来奖励
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # ====================================================================
        # 4. 计算损失
        # ====================================================================
        # MSE损失：衡量预测Q值与目标Q值的差距
        loss = self.loss_fn(current_q_values, target_q_values)
        
        # ====================================================================
        # 5. 反向传播和参数更新
        # ====================================================================
        self.optimizer.zero_grad()  # 清空之前的梯度
        loss.backward()             # 计算梯度
        
        # 梯度裁剪：防止梯度过大导致训练不稳定
        # 将梯度的L2范数限制在1.0以内
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        
        self.optimizer.step()       # 使用梯度更新参数
        
        self.training_step += 1
        
        # ====================================================================
        # 6. 更新目标网络
        # ====================================================================
        # 定期将主网络的参数复制到目标网络
        # 这样目标网络会"落后"于主网络，提供稳定的学习目标
        if self.training_step % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
        
        # ====================================================================
        # 7. 衰减探索率
        # ====================================================================
        # 随着训练进行，减少随机探索，增加利用已学知识
        # 但保持最小探索率，防止完全停止探索
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        loss_value = loss.item()  # 转换为Python数字
        self.losses.append(loss_value)
        
        return loss_value
    
    def save(self, filepath: str):
        """
        保存模型
        
        将模型的所有重要状态保存到文件，以便后续继续训练或部署使用。
        
        保存内容：
        ---------
        - 主网络参数
        - 目标网络参数
        - 优化器状态（包括动量等）
        - 当前探索率
        - 训练步数
        
        参数：
        -----
        filepath : str
            保存文件的路径
            建议使用 .pth 或 .pt 扩展名
        """
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_step': self.training_step
        }, filepath)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """
        加载模型
        
        从文件加载之前保存的模型状态。
        
        参数：
        -----
        filepath : str
            模型文件路径
        """
        # map_location确保模型能正确加载到当前设备
        checkpoint = torch.load(filepath, map_location=self.device)
        
        # 恢复所有状态
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.training_step = checkpoint['training_step']
        
        print(f"Model loaded from {filepath}")
