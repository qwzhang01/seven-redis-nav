"""
强化学习交易环境

遵循 Gymnasium (OpenAI Gym) 接口规范。
模拟真实的交易环境，用于训练 AI 交易员。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import gymnasium as gym
from gymnasium import spaces


class Action(Enum):
    """交易动作"""
    HOLD = 0       # 持有/不操作
    BUY = 1        # 买入
    SELL = 2       # 卖出


@dataclass
class TradingState:
    """交易状态"""
    step: int = 0
    position: float = 0.0        # 持仓数量
    cash: float = 10000.0        # 现金
    entry_price: float = 0.0     # 入场价格
    total_profit: float = 0.0    # 累计利润
    total_trades: int = 0        # 总交易次数
    winning_trades: int = 0      # 盈利交易次数
    max_drawdown: float = 0.0    # 最大回撤
    peak_value: float = 10000.0  # 历史最高净值


class TradingEnvironment(gym.Env):
    """
    强化学习交易环境
    
    遵循 Gymnasium 接口：
    - reset(): 重置环境
    - step(action): 执行动作
    - render(): 渲染环境（可选）
    
    观察空间 (Observation Space):
    - 价格数据：OHLCV
    - 技术指标：SMA, RSI, MACD 等
    - 账户状态：仓位、盈亏等
    
    动作空间 (Action Space):
    - 离散动作：Hold(0), Buy(1), Sell(2)
    - 或连续动作：[-1, 1] 表示仓位变化
    
    奖励函数 (Reward Function):
    - 基于盈亏的奖励
    - 风险调整后的奖励
    - 可自定义奖励函数
    """
    
    metadata = {"render_modes": ["human", "ansi"]}
    
    def __init__(
        self,
        df: "pd.DataFrame",
        feature_columns: List[str],
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        max_position: float = 1.0,
        reward_scaling: float = 1.0,
        use_discrete_action: bool = True,
        window_size: int = 20,
        render_mode: Optional[str] = None,
    ):
        """
        初始化交易环境
        
        参数:
            df: 包含 OHLCV 和特征的 DataFrame
            feature_columns: 用作观察的特征列名
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_rate: 滑点率
            max_position: 最大仓位（占资金比例）
            reward_scaling: 奖励缩放因子
            use_discrete_action: 是否使用离散动作空间
            window_size: 历史窗口大小
            render_mode: 渲染模式
        """
        super().__init__()
        
        self.df = df.reset_index(drop=True)
        self.feature_columns = feature_columns
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.max_position = max_position
        self.reward_scaling = reward_scaling
        self.use_discrete_action = use_discrete_action
        self.window_size = window_size
        self.render_mode = render_mode
        
        # 数据长度
        self.n_steps = len(df) - window_size
        
        # 特征维度
        n_features = len(feature_columns)
        
        # 定义观察空间
        # 包含：历史特征 + 账户状态
        obs_dim = window_size * n_features + 4  # 4个账户状态特征
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # 定义动作空间
        if use_discrete_action:
            # 离散动作：0=Hold, 1=Buy, 2=Sell
            self.action_space = spaces.Discrete(3)
        else:
            # 连续动作：[-1, 1] 表示目标仓位
            self.action_space = spaces.Box(
                low=-1.0,
                high=1.0,
                shape=(1,),
                dtype=np.float32
            )
        
        # 初始化状态
        self.state = TradingState()
        self.current_step = 0
        self.done = False
        
        # 历史记录
        self.history: List[Dict] = []
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """
        重置环境
        
        返回:
            observation: 初始观察
            info: 附加信息
        """
        super().reset(seed=seed)
        
        # 重置状态
        self.state = TradingState(
            cash=self.initial_capital,
            peak_value=self.initial_capital
        )
        self.current_step = 0
        self.done = False
        self.history = []
        
        # 获取初始观察
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        执行一步动作
        
        参数:
            action: 动作（0=Hold, 1=Buy, 2=Sell）
        
        返回:
            observation: 新的观察
            reward: 奖励
            terminated: 是否终止（正常结束）
            truncated: 是否截断（超时等）
            info: 附加信息
        """
        if self.done:
            raise RuntimeError("Episode has ended. Call reset() first.")
        
        # 获取当前价格
        current_idx = self.current_step + self.window_size
        current_price = self.df.iloc[current_idx]["close"]
        
        # 执行动作
        if self.use_discrete_action:
            reward = self._execute_discrete_action(action, current_price)
        else:
            reward = self._execute_continuous_action(action, current_price)
        
        # 更新步数
        self.current_step += 1
        
        # 检查是否结束
        terminated = self.current_step >= self.n_steps - 1
        truncated = False
        
        # 检查是否破产
        total_value = self._get_total_value(current_price)
        if total_value <= 0:
            terminated = True
            reward = -10.0  # 破产惩罚
        
        self.done = terminated or truncated
        
        # 记录历史
        self._record_history(action, current_price, reward)
        
        # 获取新的观察
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward * self.reward_scaling, terminated, truncated, info
    
    def _execute_discrete_action(self, action: int, price: float) -> float:
        """执行离散动作"""
        reward = 0.0
        
        # 计算滑点后的价格
        if action == Action.BUY.value:
            exec_price = price * (1 + self.slippage_rate)
        elif action == Action.SELL.value:
            exec_price = price * (1 - self.slippage_rate)
        else:
            exec_price = price
        
        if action == Action.BUY.value and self.state.position == 0:
            # 买入
            max_quantity = self.state.cash * self.max_position / exec_price
            cost = max_quantity * exec_price * (1 + self.commission_rate)
            
            if cost <= self.state.cash:
                self.state.cash -= cost
                self.state.position = max_quantity
                self.state.entry_price = exec_price
                self.state.total_trades += 1
        
        elif action == Action.SELL.value and self.state.position > 0:
            # 卖出
            value = self.state.position * exec_price * (1 - self.commission_rate)
            profit = value - self.state.position * self.state.entry_price
            
            self.state.cash += value
            self.state.total_profit += profit
            
            if profit > 0:
                self.state.winning_trades += 1
            
            # 奖励基于利润
            reward = profit / self.initial_capital
            
            self.state.position = 0
            self.state.entry_price = 0.0
        
        # 持仓时计算未实现盈亏
        if self.state.position > 0:
            unrealized_pnl = (price - self.state.entry_price) * self.state.position
            reward = unrealized_pnl / self.initial_capital * 0.1  # 小幅奖励
        
        # 更新最大回撤
        self._update_drawdown(price)
        
        return reward
    
    def _execute_continuous_action(self, action: np.ndarray, price: float) -> float:
        """执行连续动作"""
        target_position_ratio = float(action[0])  # [-1, 1]
        
        # 计算目标仓位
        total_value = self._get_total_value(price)
        target_position_value = total_value * target_position_ratio * self.max_position
        target_position = target_position_value / price if price > 0 else 0
        
        # 计算需要的交易量
        delta_position = target_position - self.state.position
        
        reward = 0.0
        
        if abs(delta_position) > 1e-6:
            if delta_position > 0:
                # 买入
                exec_price = price * (1 + self.slippage_rate)
                cost = delta_position * exec_price * (1 + self.commission_rate)
                
                if cost <= self.state.cash:
                    self.state.cash -= cost
                    self.state.position += delta_position
                    if self.state.entry_price == 0:
                        self.state.entry_price = exec_price
                    self.state.total_trades += 1
            else:
                # 卖出
                sell_quantity = min(abs(delta_position), self.state.position)
                exec_price = price * (1 - self.slippage_rate)
                value = sell_quantity * exec_price * (1 - self.commission_rate)
                profit = (exec_price - self.state.entry_price) * sell_quantity
                
                self.state.cash += value
                self.state.position -= sell_quantity
                self.state.total_profit += profit
                
                if profit > 0:
                    self.state.winning_trades += 1
                
                reward = profit / self.initial_capital
                
                if self.state.position < 1e-6:
                    self.state.entry_price = 0.0
        
        self._update_drawdown(price)
        
        return reward
    
    def _get_observation(self) -> np.ndarray:
        """获取当前观察"""
        # 获取历史特征
        start_idx = self.current_step
        end_idx = self.current_step + self.window_size
        
        features = self.df.iloc[start_idx:end_idx][self.feature_columns].values
        features = features.flatten()
        
        # 标准化特征
        features = np.nan_to_num(features, nan=0.0)
        
        # 账户状态特征
        current_price = self.df.iloc[end_idx - 1]["close"]
        total_value = self._get_total_value(current_price)
        
        account_state = np.array([
            self.state.position * current_price / total_value if total_value > 0 else 0,  # 仓位比例
            (total_value - self.initial_capital) / self.initial_capital,  # 总收益率
            self.state.max_drawdown,  # 最大回撤
            self.state.total_trades / max(self.current_step + 1, 1),  # 交易频率
        ])
        
        obs = np.concatenate([features, account_state]).astype(np.float32)
        
        return obs
    
    def _get_info(self) -> Dict:
        """获取附加信息"""
        current_idx = self.current_step + self.window_size - 1
        current_price = self.df.iloc[current_idx]["close"]
        total_value = self._get_total_value(current_price)
        
        return {
            "step": self.current_step,
            "total_value": total_value,
            "position": self.state.position,
            "cash": self.state.cash,
            "total_profit": self.state.total_profit,
            "total_trades": self.state.total_trades,
            "win_rate": self.state.winning_trades / max(self.state.total_trades, 1),
            "max_drawdown": self.state.max_drawdown,
            "return_pct": (total_value - self.initial_capital) / self.initial_capital * 100,
        }
    
    def _get_total_value(self, current_price: float) -> float:
        """计算总净值"""
        return self.state.cash + self.state.position * current_price
    
    def _update_drawdown(self, current_price: float):
        """更新最大回撤"""
        total_value = self._get_total_value(current_price)
        
        if total_value > self.state.peak_value:
            self.state.peak_value = total_value
        
        drawdown = (self.state.peak_value - total_value) / self.state.peak_value
        self.state.max_drawdown = max(self.state.max_drawdown, drawdown)
    
    def _record_history(self, action: int, price: float, reward: float):
        """记录历史"""
        self.history.append({
            "step": self.current_step,
            "action": action,
            "price": price,
            "reward": reward,
            "position": self.state.position,
            "cash": self.state.cash,
            "total_value": self._get_total_value(price),
        })
    
    def render(self):
        """渲染环境"""
        if self.render_mode == "human":
            info = self._get_info()
            print(f"Step {info['step']}: Value=${info['total_value']:.2f}, "
                  f"Return={info['return_pct']:.2f}%, "
                  f"Trades={info['total_trades']}, "
                  f"MaxDD={info['max_drawdown']*100:.2f}%")
    
    def get_history_df(self) -> "pd.DataFrame":
        """获取历史记录 DataFrame"""
        import pandas as pd
        return pd.DataFrame(self.history)


class MultiAssetTradingEnvironment(gym.Env):
    """
    多资产交易环境
    
    支持同时交易多个资产，学习投资组合管理。
    """
    
    def __init__(
        self,
        data_dict: Dict[str, "pd.DataFrame"],
        feature_columns: List[str],
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        window_size: int = 20,
    ):
        super().__init__()
        
        self.symbols = list(data_dict.keys())
        self.n_assets = len(self.symbols)
        self.data_dict = data_dict
        self.feature_columns = feature_columns
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.window_size = window_size
        
        # 确定数据长度（取最短的）
        self.n_steps = min(len(df) for df in data_dict.values()) - window_size
        
        # 观察空间：每个资产的特征 + 仓位
        n_features = len(feature_columns)
        obs_dim = self.n_assets * (window_size * n_features + 1) + 2
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32
        )
        
        # 动作空间：每个资产的目标权重
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.n_assets,),
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.current_step = 0
        self.cash = self.initial_capital
        self.positions = {symbol: 0.0 for symbol in self.symbols}
        self.done = False
        
        return self._get_observation(), self._get_info()
    
    def step(self, action):
        # 归一化动作为权重
        weights = self._normalize_weights(action)
        
        # 获取当前价格
        prices = self._get_current_prices()
        
        # 计算当前总值
        total_value = self._get_total_value(prices)
        
        # 重新平衡投资组合
        reward = self._rebalance(weights, prices, total_value)
        
        self.current_step += 1
        terminated = self.current_step >= self.n_steps - 1
        
        return self._get_observation(), reward, terminated, False, self._get_info()
    
    def _normalize_weights(self, action):
        """将动作归一化为权重（和为1）"""
        action = np.clip(action, 0, 1)  # 只做多
        total = np.sum(action)
        if total > 0:
            return action / total
        return np.zeros(self.n_assets)
    
    def _get_current_prices(self):
        idx = self.current_step + self.window_size
        return {
            symbol: self.data_dict[symbol].iloc[idx]["close"]
            for symbol in self.symbols
        }
    
    def _get_total_value(self, prices):
        position_value = sum(
            self.positions[s] * prices[s] for s in self.symbols
        )
        return self.cash + position_value
    
    def _rebalance(self, weights, prices, total_value):
        """重新平衡投资组合"""
        old_value = total_value
        
        # 计算目标持仓
        target_values = {s: total_value * weights[i] for i, s in enumerate(self.symbols)}
        target_positions = {s: target_values[s] / prices[s] for s in self.symbols}
        
        # 执行交易
        for symbol in self.symbols:
            delta = target_positions[symbol] - self.positions[symbol]
            if abs(delta) > 1e-6:
                trade_value = abs(delta) * prices[symbol]
                commission = trade_value * self.commission_rate
                
                if delta > 0:
                    self.cash -= trade_value + commission
                else:
                    self.cash += trade_value - commission
                
                self.positions[symbol] = target_positions[symbol]
        
        # 计算新总值
        new_value = self._get_total_value(prices)
        
        # 奖励为收益率
        return (new_value - old_value) / old_value
    
    def _get_observation(self):
        obs_list = []
        
        for symbol in self.symbols:
            df = self.data_dict[symbol]
            start_idx = self.current_step
            end_idx = self.current_step + self.window_size
            
            features = df.iloc[start_idx:end_idx][self.feature_columns].values.flatten()
            features = np.nan_to_num(features, nan=0.0)
            obs_list.append(features)
            
            # 当前仓位比例
            prices = self._get_current_prices()
            total_value = self._get_total_value(prices)
            position_ratio = self.positions[symbol] * prices[symbol] / total_value if total_value > 0 else 0
            obs_list.append(np.array([position_ratio]))
        
        # 账户状态
        total_value = self._get_total_value(self._get_current_prices())
        obs_list.append(np.array([
            self.cash / total_value if total_value > 0 else 1.0,
            (total_value - self.initial_capital) / self.initial_capital
        ]))
        
        return np.concatenate(obs_list).astype(np.float32)
    
    def _get_info(self):
        prices = self._get_current_prices()
        total_value = self._get_total_value(prices)
        return {
            "step": self.current_step,
            "total_value": total_value,
            "return_pct": (total_value - self.initial_capital) / self.initial_capital * 100,
            "positions": dict(self.positions),
        }
