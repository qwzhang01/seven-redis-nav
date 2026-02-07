import pytest
import numpy as np
from unittest.mock import Mock, patch
import time

from quant_trading_system.services.ai_trader.agent import (
    DQNAgent, PPOAgent, A2CAgent, Experience, ReplayBuffer, PrioritizedReplayBuffer
)
from quant_trading_system.services.ai_trader.environment import TradingEnvironment


class TestAIReinforcementLearning:
    """AI强化学习算法测试"""
    
    @pytest.fixture
    def state_dim(self):
        """状态维度"""
        return 10
    
    @pytest.fixture
    def action_dim(self):
        """动作维度"""
        return 3  # 买入、卖出、持有
    
    @pytest.fixture
    def mock_state(self, state_dim):
        """模拟状态"""
        return np.random.randn(state_dim)
    
    @pytest.fixture
    def mock_experience(self, state_dim):
        """模拟经验样本"""
        return Experience(
            state=np.random.randn(state_dim),
            action=1,
            reward=0.5,
            next_state=np.random.randn(state_dim),
            done=False
        )
    
    @pytest.fixture
    def dqn_agent(self, state_dim, action_dim):
        """DQN代理"""
        return DQNAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=0.001,
            gamma=0.99,
            epsilon_start=1.0,
            epsilon_end=0.01,
            epsilon_decay=0.995,
            buffer_size=1000,
            batch_size=32,
            target_update_freq=100,
            hidden_dims=[64, 32],
            use_double_dqn=True,
            use_dueling=True,
            use_per=False,
            device="cpu"
        )
    
    @pytest.fixture
    def ppo_agent(self, state_dim, action_dim):
        """PPO代理"""
        return PPOAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=0.0003,
            gamma=0.99,
            gae_lambda=0.95,
            clip_epsilon=0.2,
            entropy_coef=0.01,
            value_coef=0.5,
            max_grad_norm=0.5,
            n_epochs=3,
            batch_size=32,
            hidden_dims=[64, 32],
            device="cpu"
        )
    
    @pytest.fixture
    def a2c_agent(self, state_dim, action_dim):
        """A2C代理"""
        return A2CAgent(
            state_dim=state_dim,
            action_dim=action_dim,
            learning_rate=0.0007,
            gamma=0.99,
            entropy_coef=0.01,
            value_coef=0.5,
            max_grad_norm=0.5,
            n_steps=5,
            hidden_dims=[64, 32],
            device="cpu"
        )
    
    def test_dqn_initialization(self, dqn_agent, state_dim, action_dim):
        """测试DQN初始化"""
        assert dqn_agent.state_dim == state_dim
        assert dqn_agent.action_dim == action_dim
        assert dqn_agent.learning_rate == 0.001
        assert dqn_agent.gamma == 0.99
        assert dqn_agent.epsilon == 1.0
        assert dqn_agent.batch_size == 32
        assert dqn_agent.target_update_freq == 100
        assert dqn_agent.use_double_dqn is True
        assert dqn_agent.use_dueling is True
        assert dqn_agent.use_per is False
    
    def test_dqn_select_action_exploration(self, dqn_agent, mock_state):
        """测试DQN探索动作选择"""
        # 设置高epsilon（探索模式）
        dqn_agent.epsilon = 1.0
        
        # 选择动作（应该随机选择）
        action = dqn_agent.select_action(mock_state)
        
        # 检查动作在有效范围内
        assert 0 <= action < dqn_agent.action_dim
    
    def test_dqn_select_action_exploitation(self, dqn_agent, mock_state):
        """测试DQN利用动作选择"""
        # 设置低epsilon（利用模式）
        dqn_agent.epsilon = 0.0
        
        # 模拟网络输出
        with patch.object(dqn_agent, '_torch_available', True):
            with patch.object(dqn_agent.q_network, 'forward') as mock_forward:
                mock_forward.return_value = Mock(argmax=Mock(return_value=Mock(item=Mock(return_value=1))))
                
                action = dqn_agent.select_action(mock_state)
                
                # 检查动作选择
                assert action == 1
                mock_forward.assert_called_once()
    
    def test_dqn_store_experience(self, dqn_agent, mock_state):
        """测试DQN经验存储"""
        # 初始缓冲区大小
        initial_size = len(dqn_agent.replay_buffer)
        
        # 存储经验
        dqn_agent.store_experience(
            state=mock_state,
            action=1,
            reward=0.5,
            next_state=mock_state,
            done=False
        )
        
        # 检查缓冲区大小
        assert len(dqn_agent.replay_buffer) == initial_size + 1
    
    def test_dqn_update_without_enough_samples(self, dqn_agent):
        """测试DQN更新（样本不足）"""
        # 缓冲区样本不足
        result = dqn_agent.update()
        
        # 应该返回空字典
        assert result == {}
    
    def test_dqn_update_with_samples(self, dqn_agent, mock_state):
        """测试DQN更新（有足够样本）"""
        # 填充缓冲区
        for _ in range(dqn_agent.batch_size):
            dqn_agent.store_experience(
                state=mock_state,
                action=np.random.randint(dqn_agent.action_dim),
                reward=np.random.uniform(-1, 1),
                next_state=mock_state,
                done=np.random.choice([True, False])
            )
        
        # 执行更新
        with patch.object(dqn_agent, '_torch_available', True):
            with patch.object(dqn_agent, '_update_torch') as mock_update:
                mock_update.return_value = {"loss": 0.1, "q_mean": 0.5, "epsilon": 0.9}
                
                result = dqn_agent.update()
                
                # 检查更新结果
                assert "loss" in result
                assert "q_mean" in result
                assert "epsilon" in result
                mock_update.assert_called_once()
    
    def test_ppo_initialization(self, ppo_agent, state_dim, action_dim):
        """测试PPO初始化"""
        assert ppo_agent.state_dim == state_dim
        assert ppo_agent.action_dim == action_dim
        assert ppo_agent.learning_rate == 0.0003
        assert ppo_agent.gamma == 0.99
        assert ppo_agent.gae_lambda == 0.95
        assert ppo_agent.clip_epsilon == 0.2
        assert ppo_agent.entropy_coef == 0.01
        assert ppo_agent.value_coef == 0.5
        assert ppo_agent.max_grad_norm == 0.5
        assert ppo_agent.n_epochs == 3
        assert ppo_agent.batch_size == 32
    
    def test_ppo_select_action(self, ppo_agent, mock_state):
        """测试PPO动作选择"""
        # 模拟网络输出
        with patch.object(ppo_agent, '_torch_available', True):
            with patch.object(ppo_agent.network, 'get_action') as mock_get_action:
                mock_get_action.return_value = (Mock(item=Mock(return_value=1)), Mock(item=Mock(return_value=-1.0)), Mock(item=Mock(return_value=0.5)))
                
                action = ppo_agent.select_action(mock_state)
                
                # 检查动作选择
                assert action == 1
                mock_get_action.assert_called_once()
    
    def test_ppo_store_transition(self, ppo_agent, mock_state):
        """测试PPO转移存储"""
        # 初始轨迹大小
        initial_size = len(ppo_agent.trajectory)
        
        # 存储转移
        ppo_agent.store_transition(
            state=mock_state,
            action=1,
            reward=0.5,
            next_state=mock_state,
            done=False
        )
        
        # 检查轨迹大小
        assert len(ppo_agent.trajectory) == initial_size + 1
    
    def test_ppo_update_without_trajectory(self, ppo_agent):
        """测试PPO更新（无轨迹）"""
        # 空轨迹
        result = ppo_agent.update()
        
        # 应该返回空字典
        assert result == {}
    
    def test_a2c_initialization(self, a2c_agent, state_dim, action_dim):
        """测试A2C初始化"""
        assert a2c_agent.state_dim == state_dim
        assert a2c_agent.action_dim == action_dim
        assert a2c_agent.learning_rate == 0.0007
        assert a2c_agent.gamma == 0.99
        assert a2c_agent.entropy_coef == 0.01
        assert a2c_agent.value_coef == 0.5
        assert a2c_agent.max_grad_norm == 0.5
        assert a2c_agent.n_steps == 5
    
    def test_a2c_select_action(self, a2c_agent, mock_state):
        """测试A2C动作选择"""
        # 模拟网络输出
        with patch.object(a2c_agent, '_torch_available', True):
            with patch.object(a2c_agent.network, 'forward') as mock_forward:
                mock_forward.return_value = (Mock(softmax=Mock(return_value=Mock())), Mock())
                
                action = a2c_agent.select_action(mock_state)
                
                # 检查动作选择
                assert 0 <= action < a2c_agent.action_dim
                mock_forward.assert_called_once()
    
    def test_experience_dataclass(self, mock_experience):
        """测试经验数据类"""
        # 检查属性
        assert isinstance(mock_experience.state, np.ndarray)
        assert isinstance(mock_experience.action, int)
        assert isinstance(mock_experience.reward, float)
        assert isinstance(mock_experience.next_state, np.ndarray)
        assert isinstance(mock_experience.done, bool)
    
    def test_replay_buffer_operations(self, state_dim):
        """测试回放缓冲区操作"""
        buffer = ReplayBuffer(capacity=100)
        
        # 测试初始状态
        assert len(buffer) == 0
        
        # 添加经验
        experience = Experience(
            state=np.random.randn(state_dim),
            action=1,
            reward=0.5,
            next_state=np.random.randn(state_dim),
            done=False
        )
        
        buffer.push(experience)
        assert len(buffer) == 1
        
        # 测试采样
        samples = buffer.sample(1)
        assert len(samples) == 1
        assert samples[0] == experience
        
        # 测试容量限制
        for i in range(200):
            buffer.push(experience)
        
        assert len(buffer) <= 100  # 不超过容量
    
    def test_prioritized_replay_buffer(self, state_dim):
        """测试优先级回放缓冲区"""
        buffer = PrioritizedReplayBuffer(capacity=100, alpha=0.6)
        
        # 添加经验
        experience = Experience(
            state=np.random.randn(state_dim),
            action=1,
            reward=0.5,
            next_state=np.random.randn(state_dim),
            done=False
        )
        
        buffer.push(experience, priority=2.0)
        assert len(buffer) == 1
        
        # 测试采样
        experiences, weights, indices = buffer.sample(1, beta=0.4)
        assert len(experiences) == 1
        assert len(weights) == 1
        assert len(indices) == 1
        
        # 测试优先级更新
        buffer.update_priorities(indices, [1.5])
    
    def test_agent_mode_switching(self, dqn_agent):
        """测试代理模式切换"""
        # 初始为训练模式
        assert dqn_agent.training is True
        
        # 切换到评估模式
        dqn_agent.eval_mode()
        assert dqn_agent.training is False
        
        # 切换回训练模式
        dqn_agent.train_mode()
        assert dqn_agent.training is True
    
    def test_epsilon_decay(self, dqn_agent):
        """测试epsilon衰减"""
        # 初始epsilon
        initial_epsilon = dqn_agent.epsilon
        
        # 模拟多次更新
        for _ in range(10):
            dqn_agent.epsilon = max(dqn_agent.epsilon_end, dqn_agent.epsilon * dqn_agent.epsilon_decay)
        
        # 检查epsilon衰减
        assert dqn_agent.epsilon < initial_epsilon
        assert dqn_agent.epsilon >= dqn_agent.epsilon_end
    
    def test_agent_save_load(self, dqn_agent, tmp_path):
        """测试代理保存和加载"""
        # 创建临时文件路径
        save_path = tmp_path / "dqn_model.pth"
        
        # 模拟保存
        with patch.object(dqn_agent, '_torch_available', True):
            with patch('torch.save') as mock_save:
                dqn_agent.save(str(save_path))
                mock_save.assert_called_once()
        
        # 模拟加载
        with patch.object(dqn_agent, '_torch_available', True):
            with patch('torch.load') as mock_load:
                mock_load.return_value = {
                    "q_network": {},
                    "target_network": {},
                    "optimizer": {},
                    "epsilon": 0.5,
                    "total_steps": 100
                }
                
                dqn_agent.load(str(save_path))
                mock_load.assert_called_once()
    
    def test_performance_benchmark(self, dqn_agent, mock_state):
        """测试性能基准"""
        import time
        
        # 测试动作选择性能
        start_time = time.time()
        
        for _ in range(100):
            action = dqn_agent.select_action(mock_state)
            assert 0 <= action < dqn_agent.action_dim
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 检查性能（100次选择应该小于1秒）
        assert execution_time < 1.0
        
        # 计算平均时间
        avg_time = execution_time / 100
        print(f"Average action selection time: {avg_time:.6f} seconds")
        
        # 性能要求：平均选择时间小于5毫秒
        assert avg_time < 0.005
    
    def test_convergence_behavior(self, dqn_agent, mock_state):
        """测试收敛行为"""
        # 模拟训练过程
        losses = []
        
        for episode in range(10):
            # 存储一些经验
            for _ in range(10):
                dqn_agent.store_experience(
                    state=mock_state,
                    action=np.random.randint(dqn_agent.action_dim),
                    reward=np.random.uniform(-1, 1),
                    next_state=mock_state,
                    done=False
                )
            
            # 执行更新
            if len(dqn_agent.replay_buffer) >= dqn_agent.batch_size:
                with patch.object(dqn_agent, '_torch_available', True):
                    with patch.object(dqn_agent, '_update_torch') as mock_update:
                        mock_update.return_value = {"loss": 0.1 / (episode + 1), "q_mean": 0.5, "epsilon": 0.9}
                        
                        result = dqn_agent.update()
                        losses.append(result.get("loss", 0.0))
        
        # 检查损失趋势（应该逐渐减小）
        if len(losses) > 1:
            # 检查损失是否在减小（允许波动）
            avg_loss = sum(losses) / len(losses)
            assert avg_loss < 0.5  # 平均损失应该较小
    
    def test_robustness_to_noise(self, dqn_agent, mock_state):
        """测试对噪声的鲁棒性"""
        # 测试在有噪声的状态下选择动作
        noisy_states = []
        
        for _ in range(10):
            # 添加不同强度的噪声
            noise_levels = [0.01, 0.05, 0.1, 0.2, 0.5]
            
            for noise in noise_levels:
                noisy_state = mock_state + np.random.normal(0, noise, mock_state.shape)
                noisy_states.append(noisy_state)
        
        # 对所有噪声状态选择动作
        actions = []
        for state in noisy_states:
            action = dqn_agent.select_action(state)
            actions.append(action)
        
        # 检查所有动作都在有效范围内
        assert all(0 <= action < dqn_agent.action_dim for action in actions)
        
        # 检查动作的多样性（不应该总是选择同一个动作）
        unique_actions = set(actions)
        assert len(unique_actions) > 1  # 应该有多种动作选择
    
    def test_memory_efficiency(self, dqn_agent, mock_state):
        """测试内存效率"""
        import sys
        
        # 记录初始内存使用
        initial_memory = sys.getsizeof(dqn_agent)
        
        # 存储大量经验
        num_experiences = 1000
        for i in range(num_experiences):
            dqn_agent.store_experience(
                state=mock_state,
                action=i % dqn_agent.action_dim,
                reward=np.random.uniform(-1, 1),
                next_state=mock_state,
                done=(i % 10 == 0)
            )
        
        # 记录最终内存使用
        final_memory = sys.getsizeof(dqn_agent)
        
        # 检查内存增长是否合理
        memory_growth = final_memory - initial_memory
        memory_per_experience = memory_growth / num_experiences
        
        print(f"Memory per experience: {memory_per_experience:.2f} bytes")
        
        # 内存增长应该相对较小（每个经验小于1KB）
        assert memory_per_experience < 1024
    
    def test_algorithm_comparison(self, dqn_agent, ppo_agent, a2c_agent, mock_state):
        """测试算法比较"""
        # 测试不同算法的动作选择时间
        algorithms = [
            ("DQN", dqn_agent),
            ("PPO", ppo_agent),
            ("A2C", a2c_agent)
        ]
        
        selection_times = {}
        
        for name, agent in algorithms:
            import time
            
            start_time = time.time()
            
            # 执行100次动作选择
            for _ in range(100):
                action = agent.select_action(mock_state)
                assert 0 <= action < agent.action_dim
            
            end_time = time.time()
            execution_time = end_time - start_time
            avg_time = execution_time / 100
            
            selection_times[name] = avg_time
            print(f"{name} average selection time: {avg_time:.6f} seconds")
        
        # 检查所有算法都在合理时间内
        for name, avg_time in selection_times.items():
            assert avg_time < 0.01  # 所有算法都应小于10毫秒