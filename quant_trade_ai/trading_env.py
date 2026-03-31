"""
================================================================================
交易环境 - 模拟股票交易市场
================================================================================

本模块实现了一个基于 Gymnasium 接口的股票交易模拟环境。

核心概念：
---------
1. 环境 (Environment): 模拟真实的股票交易市场
2. 状态 (State): 当前市场的信息表示（技术指标、持仓等）
3. 动作 (Action): 买入(1)、卖出(2)、持有(0)
4. 奖励 (Reward): 交易带来的收益或损失

使用方法：
---------
>>> from trading_env import TradingEnvironment
>>> import pandas as pd
>>> 
>>> # 准备股票数据 (需要包含 Open, High, Low, Close, Volume 列)
>>> df = pd.read_csv('stock_data.csv')
>>> 
>>> # 创建环境
>>> env = TradingEnvironment(df, initial_balance=100000)
>>> 
>>> # 重置环境
>>> state, info = env.reset()
>>> 
>>> # 执行交易
>>> action = 1  # 买入
>>> next_state, reward, done, truncated, info = env.step(action)

作者: AI Trading Demo
版本: 1.0
================================================================================
"""

# ============================================================================
# 导入必要的库
# ============================================================================
import numpy as np          # 数值计算库，用于数组操作和数学计算
import pandas as pd         # 数据处理库，用于处理表格数据（DataFrame）
import gymnasium as gym     # 强化学习环境标准接口库
from gymnasium import spaces  # 用于定义状态空间和动作空间
import ta                   # 技术分析库，用于计算各种技术指标


class TradingEnvironment(gym.Env):
    """
    股票交易强化学习环境
    
    这个类模拟了一个简化的股票交易市场，智能体可以在其中进行买入、卖出或持有操作。
    
    继承关系：
    ---------
    继承自 gym.Env，需要实现两个核心方法：
    - reset(): 重置环境到初始状态，开始新的交易回合
    - step(action): 执行一个动作，返回结果
    
    属性说明：
    ---------
    observation_space : gym.spaces.Box
        状态空间的定义，是一个14维的连续向量
        包含12个技术指标 + 持仓比例 + 未实现盈亏
        
    action_space : gym.spaces.Discrete
        动作空间的定义，包含3个离散动作：
        - 0: 持有 (Hold) - 不进行任何交易
        - 1: 买入 (Buy) - 使用50%现金买入股票
        - 2: 卖出 (Sell) - 卖出50%持有的股票
    
    核心流程：
    ---------
    1. 创建环境，传入股票数据
    2. 调用 reset() 开始新回合
    3. 循环调用 step(action) 进行交易
    4. 当 done=True 时，本回合结束
    """
    
    # 元数据配置
    # render_modes: 支持的渲染模式，'human' 表示输出到控制台
    metadata = {'render_modes': ['human']}
    
    def __init__(self, df: pd.DataFrame, initial_balance: float = 100000, 
                 transaction_fee: float = 0.001, window_size: int = 20):
        """
        初始化交易环境
        
        参数说明：
        ---------
        df : pd.DataFrame
            股票数据，必须包含以下列：
            - Open: 开盘价（当天第一笔交易的价格）
            - High: 最高价（当天的最高成交价格）
            - Low: 最低价（当天的最低成交价格）
            - Close: 收盘价（当天最后一笔交易的价格）
            - Volume: 成交量（当天交易的股票数量）
            
        initial_balance : float, 默认=100000
            初始资金，单位：美元
            智能体开始交易时的现金数量
            
        transaction_fee : float, 默认=0.001
            交易手续费比例
            0.001 表示 0.1%，即每交易100美元收取0.1美元手续费
            
        window_size : int, 默认=20
            技术指标计算窗口大小
            许多技术指标需要历史数据来计算，如20日移动平均
            交易从第 window_size 天开始，之前的数据用于计算指标
        
        示例：
        ------
        >>> df = pd.DataFrame({
        ...     'Open': [100, 101, 102],
        ...     'High': [105, 106, 107],
        ...     'Low': [99, 100, 101],
        ...     'Close': [104, 105, 106],
        ...     'Volume': [1000000, 1100000, 1050000]
        ... })
        >>> env = TradingEnvironment(df, initial_balance=50000)
        """
        # 调用父类构造函数（必须）
        super().__init__()
        
        # ====================================================================
        # 保存参数
        # ====================================================================
        self.df = df.copy()  # 复制数据，避免修改原始数据
        self.initial_balance = initial_balance  # 初始资金
        self.transaction_fee = transaction_fee  # 交易费率
        self.window_size = window_size  # 窗口大小
        
        # ====================================================================
        # 计算技术指标
        # ====================================================================
        # 在原始数据上计算各种技术指标，添加为新的列
        self._calculate_indicators()
        
        # ====================================================================
        # 定义特征列
        # ====================================================================
        # 这些是智能体能够"看到"的市场信息
        # 每个特征都经过归一化处理，使得数值范围更合理
        self.feature_columns = [
            'returns',      # 日收益率：今天相比昨天的涨跌幅
            'rsi',          # RSI(14)：相对强弱指数，判断超买超卖
            'macd',         # MACD：移动平均收敛散度
            'macd_signal',  # MACD信号线
            'macd_diff',    # MACD柱状图（MACD与信号线的差值）
            'bb_high',      # 布林带上轨距离：价格离上轨有多远
            'bb_low',       # 布林带下轨距离：价格离下轨有多远
            'bb_mid',       # 布林带中轨距离：价格离中轨有多远
            'sma_20',       # 20日简单移动平均与当前价的偏离
            'ema_20',       # 20日指数移动平均与当前价的偏离
            'volume_sma',   # 成交量相对于20日均量的比例
            'atr'           # 平均真实波幅：衡量波动性
        ]
        
        # ====================================================================
        # 定义状态空间 (Observation Space)
        # ====================================================================
        # 状态是智能体观察到的环境信息
        # 包括：12个技术指标 + 持仓比例 + 未实现盈亏 = 14维向量
        n_features = len(self.feature_columns) + 2  # +2 是持仓比例和未实现盈亏
        
        # Box: 连续空间，每个维度的值可以是任意实数
        # low/high: 值的范围，这里设为正负无穷
        # shape: 状态向量的形状
        # dtype: 数据类型，float32节省内存
        self.observation_space = spaces.Box(
            low=-np.inf,    # 最小值
            high=np.inf,    # 最大值
            shape=(n_features,),  # 一维向量，14个元素
            dtype=np.float32
        )
        
        # ====================================================================
        # 定义动作空间 (Action Space)
        # ====================================================================
        # Discrete(3): 离散空间，包含3个选项
        # 0 = 持有 (Hold): 不做任何交易
        # 1 = 买入 (Buy): 使用现金购买股票
        # 2 = 卖出 (Sell): 卖出持有的股票
        self.action_space = spaces.Discrete(3)
        
        # ====================================================================
        # 重置环境到初始状态
        # ====================================================================
        self.reset()
    
    def _calculate_indicators(self):
        """
        计算技术指标
        
        技术指标是量化交易的重要工具，通过数学公式从价格和成交量中提取信息。
        这些指标可以帮助判断：
        - 市场趋势（上涨/下跌/震荡）
        - 买卖时机（超买/超卖）
        - 波动程度（风险高低）
        
        本方法计算以下指标：
        1. 收益率 (Returns)
        2. RSI (Relative Strength Index)
        3. MACD (Moving Average Convergence Divergence)
        4. Bollinger Bands (布林带)
        5. SMA/EMA (移动平均线)
        6. Volume SMA (成交量均值)
        7. ATR (Average True Range)
        
        注意：
        -----
        - 所有指标都经过归一化处理
        - 前几天的数据可能因为窗口不足而为NaN，会被填充为0
        """
        df = self.df  # 引用数据框，方便操作
        
        # ====================================================================
        # 1. 收益率 (Returns)
        # ====================================================================
        # 公式: Returns = (今日收盘价 - 昨日收盘价) / 昨日收盘价
        # 例如: 昨天100，今天105，收益率 = 5%
        # pct_change() 自动计算相邻元素的百分比变化
        df['returns'] = df['Close'].pct_change()
        
        # ====================================================================
        # 2. RSI - 相对强弱指数 (Relative Strength Index)
        # ====================================================================
        # RSI 衡量价格上涨的力度与下跌的力度之比
        # 
        # 计算方法:
        # 1. 计算14天内上涨日的平均涨幅 (avg_gain)
        # 2. 计算14天内下跌日的平均跌幅 (avg_loss)
        # 3. RS = avg_gain / avg_loss
        # 4. RSI = 100 - 100 / (1 + RS)
        # 
        # RSI 的范围是 0-100:
        # - RSI > 70: 超买区域，价格可能过高，有回调风险
        # - RSI < 30: 超卖区域，价格可能过低，有反弹机会
        # - RSI ≈ 50: 中性区域
        # 
        # 这里除以100进行归一化，使范围变为0-1
        df['rsi'] = ta.momentum.RSIIndicator(
            df['Close'], 
            window=14  # 使用14天的数据计算
        ).rsi() / 100
        
        # ====================================================================
        # 3. MACD - 移动平均收敛散度
        # ====================================================================
        # MACD 用于判断趋势方向和强度
        # 
        # 组成部分:
        # - MACD线: 12日EMA - 26日EMA（快线减慢线）
        # - 信号线: MACD线的9日EMA（平滑后的MACD）
        # - 柱状图: MACD线 - 信号线
        # 
        # 交易信号:
        # - 金叉: MACD线从下方穿过信号线，买入信号
        # - 死叉: MACD线从上方穿过信号线，卖出信号
        # - 柱状图由负转正: 上涨动能增强
        # - 柱状图由正转负: 下跌动能增强
        # 
        # 归一化: 除以当前价格，得到相对值
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd() / df['Close']  # MACD线
        df['macd_signal'] = macd.macd_signal() / df['Close']  # 信号线
        df['macd_diff'] = macd.macd_diff() / df['Close']  # 柱状图
        
        # ====================================================================
        # 4. Bollinger Bands - 布林带
        # ====================================================================
        # 布林带用于判断价格是否偏离正常范围
        # 
        # 组成部分:
        # - 中轨: 20日简单移动平均线
        # - 上轨: 中轨 + 2倍标准差
        # - 下轨: 中轨 - 2倍标准差
        # 
        # 统计原理: 正态分布下，95%的数据落在均值±2标准差内
        # 
        # 交易信号:
        # - 价格触及上轨: 可能超买，价格偏高
        # - 价格触及下轨: 可能超卖，价格偏低
        # - 带宽收窄: 波动减小，可能即将突破
        # - 带宽扩大: 波动增加
        bb = ta.volatility.BollingerBands(df['Close'], window=20)
        # 计算价格与各轨道的相对距离
        df['bb_high'] = (bb.bollinger_hband() - df['Close']) / df['Close']  # 离上轨的距离
        df['bb_low'] = (df['Close'] - bb.bollinger_lband()) / df['Close']   # 离下轨的距离
        df['bb_mid'] = (bb.bollinger_mavg() - df['Close']) / df['Close']    # 离中轨的距离
        
        # ====================================================================
        # 5. 移动平均线 (Moving Averages)
        # ====================================================================
        # 移动平均线平滑价格波动，显示趋势方向
        # 
        # SMA (简单移动平均): 所有数据权重相同
        # - SMA(20) = (P1 + P2 + ... + P20) / 20
        # 
        # EMA (指数移动平均): 近期数据权重更大
        # - 对最新价格更敏感，反应更快
        # 
        # 交易信号:
        # - 价格在均线上方: 上涨趋势
        # - 价格在均线下方: 下跌趋势
        # - 价格穿越均线: 趋势可能反转
        df['sma_20'] = (ta.trend.SMAIndicator(
            df['Close'], window=20
        ).sma_indicator() - df['Close']) / df['Close']
        
        df['ema_20'] = (ta.trend.EMAIndicator(
            df['Close'], window=20
        ).ema_indicator() - df['Close']) / df['Close']
        
        # ====================================================================
        # 6. 成交量指标 (Volume Indicator)
        # ====================================================================
        # 成交量反映市场参与程度
        # 
        # 计算方法: 当前成交量 / 20日平均成交量 - 1
        # 
        # 解读:
        # - > 0: 成交量高于平均，市场活跃
        # - < 0: 成交量低于平均，市场冷清
        # - 放量上涨: 上涨趋势得到确认
        # - 缩量下跌: 下跌可能即将结束
        df['volume_sma'] = df['Volume'] / df['Volume'].rolling(window=20).mean() - 1
        
        # ====================================================================
        # 7. ATR - 平均真实波幅 (Average True Range)
        # ====================================================================
        # ATR 衡量价格波动的剧烈程度
        # 
        # 真实波幅 (TR) 是以下三者的最大值:
        # 1. 今日最高价 - 今日最低价
        # 2. |今日最高价 - 昨日收盘价|
        # 3. |今日最低价 - 昨日收盘价|
        # 
        # ATR = TR的14日平均值
        # 
        # 用途:
        # - 设置止损位: 通常设在 入场价 ± 2×ATR
        # - 判断波动: ATR高说明波动大，风险高
        # - 仓位管理: 波动大时减小仓位
        df['atr'] = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close']
        ).average_true_range() / df['Close']  # 归一化为相对值
        
        # ====================================================================
        # 填充缺失值
        # ====================================================================
        # 前几天因为计算窗口不足，会产生NaN值
        # 用0填充这些缺失值，避免后续计算出错
        df.fillna(0, inplace=True)
        
        self.df = df
    
    def reset(self, seed=None, options=None):
        """
        重置环境到初始状态
        
        每次开始新的交易回合时调用此方法。
        它会：
        1. 重置时间步到起始位置
        2. 重置账户余额为初始资金
        3. 清空所有持仓
        4. 清空交易记录
        
        参数：
        -----
        seed : int, 可选
            随机种子，用于可重复性
            
        options : dict, 可选
            额外的重置选项（当前未使用）
        
        返回：
        -----
        observation : np.ndarray
            初始状态观测，shape=(14,)
            
        info : dict
            空字典，符合Gymnasium接口要求
        
        示例：
        ------
        >>> env = TradingEnvironment(df)
        >>> state, info = env.reset()
        >>> print(state.shape)  # (14,)
        """
        # 调用父类的reset方法设置随机种子
        super().reset(seed=seed)
        
        # ====================================================================
        # 重置时间步
        # ====================================================================
        # 从 window_size 位置开始，因为之前的数据用于计算技术指标
        self.current_step = self.window_size
        
        # ====================================================================
        # 重置账户状态
        # ====================================================================
        self.balance = self.initial_balance  # 现金余额
        self.shares_held = 0                  # 当前持有的股票数量
        self.total_shares_sold = 0            # 累计卖出的股票数量（统计用）
        self.total_sales_value = 0            # 累计卖出的金额（统计用）
        self.cost_basis = 0                   # 持仓的平均成本价
        self.total_profit = 0                 # 累计已实现利润
        self.trades = []                      # 交易记录列表
        
        # 返回初始观测和空的info字典
        return self._get_observation(), {}
    
    def _get_observation(self):
        """
        获取当前状态观测
        
        状态是智能体"看到"的环境信息，包括：
        1. 技术指标特征（12个维度）
        2. 持仓比例（1个维度）
        3. 未实现盈亏比例（1个维度）
        
        返回：
        -----
        obs : np.ndarray
            状态向量，shape=(14,)，dtype=float32
        """
        # ====================================================================
        # 获取技术指标特征
        # ====================================================================
        # iloc[current_step] 获取当前时间步的数据
        features = self.df[self.feature_columns].iloc[self.current_step].values
        
        # ====================================================================
        # 计算持仓比例
        # ====================================================================
        # 持仓比例 = 股票市值 / 总资产
        # 这告诉智能体当前有多少资产是股票形式
        current_price = self.df['Close'].iloc[self.current_step]
        total_value = self.balance + self.shares_held * current_price
        
        if total_value > 0:
            position_ratio = (self.shares_held * current_price) / total_value
        else:
            position_ratio = 0
        
        # ====================================================================
        # 计算未实现盈亏比例
        # ====================================================================
        # 未实现盈亏 = (当前价格 - 成本价) / 成本价
        # 正值表示浮盈，负值表示浮亏
        unrealized_pnl = 0
        if self.shares_held > 0 and self.cost_basis > 0:
            unrealized_pnl = (current_price - self.cost_basis) / self.cost_basis
        
        # ====================================================================
        # 拼接所有特征
        # ====================================================================
        obs = np.concatenate([features, [position_ratio, unrealized_pnl]])
        
        return obs.astype(np.float32)
    
    def step(self, action):
        """
        执行一步交易
        
        这是环境的核心方法，实现智能体与环境的交互：
        1. 根据动作执行交易（买入/卖出/持有）
        2. 时间向前推进一步
        3. 计算奖励（基于资产变化）
        4. 返回新的状态和相关信息
        
        参数：
        -----
        action : int
            要执行的动作：
            - 0: 持有 (Hold)
            - 1: 买入 (Buy)
            - 2: 卖出 (Sell)
        
        返回：
        -----
        observation : np.ndarray
            新的状态观测，shape=(14,)
            
        reward : float
            这一步获得的奖励，基于资产变化百分比
            
        terminated : bool
            是否达到终止状态（数据用完）
            
        truncated : bool
            是否被截断（当前实现中总是False）
            
        info : dict
            额外信息，包含：
            - total_value: 当前总资产
            - balance: 现金余额
            - shares_held: 持有股数
            - current_price: 当前股价
            - total_profit: 总盈亏
        
        示例：
        ------
        >>> state, info = env.reset()
        >>> action = 1  # 买入
        >>> next_state, reward, done, truncated, info = env.step(action)
        >>> print(f"奖励: {reward:.2f}, 总资产: ${info['total_value']:.2f}")
        """
        # 获取当前价格
        current_price = self.df['Close'].iloc[self.current_step]
        
        # ====================================================================
        # 记录交易前的总资产（用于计算奖励）
        # ====================================================================
        prev_total_value = self.balance + self.shares_held * current_price
        
        # ====================================================================
        # 根据动作执行交易
        # ====================================================================
        if action == 1:  # 买入
            self._buy(current_price)
        elif action == 2:  # 卖出
            self._sell(current_price)
        # action == 0 时不执行任何操作（持有）
        
        # ====================================================================
        # 时间向前推进
        # ====================================================================
        self.current_step += 1
        
        # ====================================================================
        # 检查是否结束
        # ====================================================================
        # 当到达数据末尾时，回合结束
        terminated = self.current_step >= len(self.df) - 1
        truncated = False  # 当前实现不使用截断
        
        # ====================================================================
        # 计算奖励
        # ====================================================================
        # 获取新的价格（时间已经前进了一步）
        new_price = self.df['Close'].iloc[self.current_step]
        current_total_value = self.balance + self.shares_held * new_price
        
        # 奖励 = 资产变化百分比 × 100
        # 乘以100是为了让奖励值更明显，便于学习
        # 例如：资产增长1%，奖励为1.0
        reward = (current_total_value - prev_total_value) / prev_total_value * 100
        
        # ====================================================================
        # 风险惩罚
        # ====================================================================
        # 当亏损超过2%时，额外惩罚（乘以1.5）
        # 这鼓励智能体避免大幅亏损
        if reward < -2:
            reward *= 1.5
        
        # ====================================================================
        # 构建返回信息
        # ====================================================================
        info = {
            'total_value': current_total_value,  # 总资产
            'balance': self.balance,              # 现金
            'shares_held': self.shares_held,      # 持股数
            'current_price': new_price,           # 当前价格
            'total_profit': current_total_value - self.initial_balance  # 盈亏
        }
        
        return self._get_observation(), reward, terminated, truncated, info
    
    def _buy(self, price):
        """
        执行买入操作
        
        买入策略：
        - 使用当前现金的50%买入股票
        - 这样设计是为了分批建仓，降低风险
        - 保留部分现金以应对价格下跌时加仓
        
        参数：
        -----
        price : float
            当前股票价格
        
        注意：
        -----
        - 只有当有现金时才能买入
        - 会扣除交易手续费
        - 会更新持仓成本（加权平均）
        """
        if self.balance > 0:
            # ================================================================
            # 计算买入金额和股数
            # ================================================================
            buy_amount = self.balance * 0.5  # 使用50%的现金
            
            # 计算可买入股数（整数）
            # 总成本 = 股价 × 股数 × (1 + 手续费率)
            # 股数 = 买入金额 / (股价 × (1 + 手续费率))
            shares_to_buy = int(buy_amount / (price * (1 + self.transaction_fee)))
            
            if shares_to_buy > 0:
                # ============================================================
                # 执行买入
                # ============================================================
                cost = shares_to_buy * price * (1 + self.transaction_fee)
                self.balance -= cost  # 扣除现金
                
                # ============================================================
                # 更新成本基础（加权平均成本）
                # ============================================================
                # 首次买入：成本就是买入价
                # 加仓：新成本 = (原成本×原股数 + 新价×新股数) / 总股数
                if self.shares_held == 0:
                    self.cost_basis = price
                else:
                    self.cost_basis = (
                        self.cost_basis * self.shares_held + price * shares_to_buy
                    ) / (self.shares_held + shares_to_buy)
                
                self.shares_held += shares_to_buy  # 增加持股数
                
                # ============================================================
                # 记录交易
                # ============================================================
                # 格式: (动作类型, 时间步, 价格, 股数)
                self.trades.append(('BUY', self.current_step, price, shares_to_buy))
    
    def _sell(self, price):
        """
        执行卖出操作
        
        卖出策略：
        - 卖出当前持仓的50%
        - 如果只剩1股，则全部卖出
        - 这样设计是为了分批止盈/止损
        
        参数：
        -----
        price : float
            当前股票价格
        
        注意：
        -----
        - 只有当持有股票时才能卖出
        - 会扣除交易手续费
        - 会计算并累加已实现盈亏
        """
        if self.shares_held > 0:
            # ================================================================
            # 计算卖出股数
            # ================================================================
            shares_to_sell = self.shares_held // 2  # 卖出50%（整数除法）
            
            # 如果只剩1股或更少，全部卖出
            if shares_to_sell == 0:
                shares_to_sell = self.shares_held
            
            # ================================================================
            # 执行卖出
            # ================================================================
            # 卖出收入 = 股数 × 价格 × (1 - 手续费率)
            sell_value = shares_to_sell * price * (1 - self.transaction_fee)
            self.balance += sell_value  # 增加现金
            self.shares_held -= shares_to_sell  # 减少持股数
            
            # ================================================================
            # 计算已实现盈亏
            # ================================================================
            # 盈亏 = (卖出价 - 成本价) × 股数
            profit = (price - self.cost_basis) * shares_to_sell
            self.total_profit += profit
            
            # ================================================================
            # 更新统计数据
            # ================================================================
            self.total_shares_sold += shares_to_sell
            self.total_sales_value += sell_value
            
            # ================================================================
            # 记录交易
            # ================================================================
            self.trades.append(('SELL', self.current_step, price, shares_to_sell))
            
            # ================================================================
            # 清仓时重置成本基础
            # ================================================================
            if self.shares_held == 0:
                self.cost_basis = 0
    
    def render(self, mode='human'):
        """
        渲染当前环境状态
        
        将当前的交易状态打印到控制台，方便观察。
        
        参数：
        -----
        mode : str, 默认='human'
            渲染模式，目前只支持'human'（控制台输出）
        
        输出内容：
        ---------
        - Step: 当前时间步
        - Price: 当前股价
        - Balance: 现金余额
        - Shares: 持有股数
        - Total Value: 总资产
        - Profit: 收益率
        """
        current_price = self.df['Close'].iloc[self.current_step]
        total_value = self.balance + self.shares_held * current_price
        profit_pct = (total_value - self.initial_balance) / self.initial_balance * 100
        
        print(f"Step: {self.current_step}")
        print(f"Price: ${current_price:.2f}")
        print(f"Balance: ${self.balance:.2f}")
        print(f"Shares: {self.shares_held}")
        print(f"Total Value: ${total_value:.2f}")
        print(f"Profit: {profit_pct:.2f}%")
        print("-" * 40)
