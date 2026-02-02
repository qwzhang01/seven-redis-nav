"""
特征工程模块

为 AI 交易员准备输入特征。
包含技术指标、价格特征、时间特征等。
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """特征配置"""
    # 价格特征
    use_returns: bool = True
    use_log_returns: bool = True
    return_periods: List[int] = None
    
    # 技术指标
    use_ma: bool = True
    ma_periods: List[int] = None
    use_rsi: bool = True
    rsi_period: int = 14
    use_macd: bool = True
    use_bollinger: bool = True
    bollinger_period: int = 20
    use_atr: bool = True
    atr_period: int = 14
    
    # 成交量特征
    use_volume_features: bool = True
    
    # 时间特征
    use_time_features: bool = True
    
    # 标准化
    normalize: bool = True
    
    def __post_init__(self):
        if self.return_periods is None:
            self.return_periods = [1, 5, 10, 20]
        if self.ma_periods is None:
            self.ma_periods = [5, 10, 20, 50]


class FeatureEngineer:
    """
    特征工程器
    
    将原始 OHLCV 数据转换为 AI 模型可用的特征。
    
    特征类别：
    1. 价格特征：收益率、对数收益率
    2. 技术指标：MA、RSI、MACD、布林带、ATR
    3. 成交量特征：成交量变化、成交量均值
    4. 时间特征：小时、星期几等
    5. 统计特征：波动率、偏度、峰度
    """
    
    def __init__(self, config: FeatureConfig = None):
        self.config = config or FeatureConfig()
        self.feature_names: List[str] = []
        self.scalers: Dict[str, Tuple[float, float]] = {}
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """拟合并转换特征"""
        df = df.copy()
        
        # 计算所有特征
        df = self._add_price_features(df)
        df = self._add_technical_indicators(df)
        df = self._add_volume_features(df)
        df = self._add_time_features(df)
        df = self._add_statistical_features(df)
        
        # 获取特征列名
        self.feature_names = [col for col in df.columns if col not in 
                            ["timestamp", "open", "high", "low", "close", "volume", "symbol"]]
        
        # 标准化
        if self.config.normalize:
            df = self._normalize(df, fit=True)
        
        # 删除 NaN
        df = df.dropna()
        
        return df
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换特征（使用已拟合的参数）"""
        df = df.copy()
        
        df = self._add_price_features(df)
        df = self._add_technical_indicators(df)
        df = self._add_volume_features(df)
        df = self._add_time_features(df)
        df = self._add_statistical_features(df)
        
        if self.config.normalize:
            df = self._normalize(df, fit=False)
        
        df = df.dropna()
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加价格特征"""
        if self.config.use_returns:
            for period in self.config.return_periods:
                df[f"return_{period}"] = df["close"].pct_change(period)
        
        if self.config.use_log_returns:
            for period in self.config.return_periods:
                df[f"log_return_{period}"] = np.log(df["close"] / df["close"].shift(period))
        
        # 价格相对位置
        df["price_position"] = (df["close"] - df["low"]) / (df["high"] - df["low"] + 1e-8)
        
        # 日内波动幅度
        df["range_pct"] = (df["high"] - df["low"]) / df["open"]
        
        # 涨跌方向
        df["price_direction"] = np.sign(df["close"] - df["open"])
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        close = df["close"]
        high = df["high"]
        low = df["low"]
        
        # 移动平均线
        if self.config.use_ma:
            for period in self.config.ma_periods:
                ma = close.rolling(period).mean()
                df[f"ma_{period}"] = ma
                df[f"ma_{period}_ratio"] = close / ma - 1  # 价格与均线的偏离度
        
        # RSI
        if self.config.use_rsi:
            df["rsi"] = self._calculate_rsi(close, self.config.rsi_period)
            df["rsi_normalized"] = df["rsi"] / 100 - 0.5  # 归一化到 [-0.5, 0.5]
        
        # MACD
        if self.config.use_macd:
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9, adjust=False).mean()
            
            df["macd"] = macd
            df["macd_signal"] = signal
            df["macd_hist"] = macd - signal
            df["macd_normalized"] = macd / close  # 相对于价格的 MACD
        
        # 布林带
        if self.config.use_bollinger:
            period = self.config.bollinger_period
            ma = close.rolling(period).mean()
            std = close.rolling(period).std()
            
            df["bb_upper"] = ma + 2 * std
            df["bb_lower"] = ma - 2 * std
            df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / ma
            df["bb_position"] = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-8)
        
        # ATR
        if self.config.use_atr:
            df["atr"] = self._calculate_atr(high, low, close, self.config.atr_period)
            df["atr_normalized"] = df["atr"] / close  # 相对波动率
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加成交量特征"""
        if not self.config.use_volume_features:
            return df
        
        volume = df["volume"]
        
        # 成交量变化率
        df["volume_change"] = volume.pct_change()
        
        # 成交量与均值的比率
        for period in [5, 20]:
            vol_ma = volume.rolling(period).mean()
            df[f"volume_ratio_{period}"] = volume / vol_ma
        
        # 成交量趋势
        df["volume_trend"] = volume.rolling(10).mean() / volume.rolling(20).mean()
        
        # 价量关系
        df["price_volume_corr"] = df["close"].rolling(20).corr(volume)
        
        return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加时间特征"""
        if not self.config.use_time_features:
            return df
        
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])
            
            # 小时（周期编码）
            hour = ts.dt.hour
            df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
            df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
            
            # 星期几（周期编码）
            dayofweek = ts.dt.dayofweek
            df["dow_sin"] = np.sin(2 * np.pi * dayofweek / 7)
            df["dow_cos"] = np.cos(2 * np.pi * dayofweek / 7)
            
            # 月份（周期编码）
            month = ts.dt.month
            df["month_sin"] = np.sin(2 * np.pi * month / 12)
            df["month_cos"] = np.cos(2 * np.pi * month / 12)
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加统计特征"""
        close = df["close"]
        returns = close.pct_change()
        
        # 滚动波动率
        for period in [5, 20]:
            df[f"volatility_{period}"] = returns.rolling(period).std()
        
        # 滚动偏度
        df["skewness_20"] = returns.rolling(20).skew()
        
        # 滚动峰度
        df["kurtosis_20"] = returns.rolling(20).kurt()
        
        # 最大/最小值
        for period in [10, 20]:
            df[f"high_ratio_{period}"] = close / close.rolling(period).max()
            df[f"low_ratio_{period}"] = close / close.rolling(period).min()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算 RSI"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, 
                       close: pd.Series, period: int = 14) -> pd.Series:
        """计算 ATR"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    def _normalize(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """标准化特征"""
        for col in self.feature_names:
            if col not in df.columns:
                continue
            
            if fit:
                mean = df[col].mean()
                std = df[col].std()
                if std == 0:
                    std = 1
                self.scalers[col] = (mean, std)
            else:
                if col not in self.scalers:
                    continue
                mean, std = self.scalers[col]
            
            df[col] = (df[col] - mean) / std
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """获取特征列名"""
        return self.feature_names


class FeatureSelector:
    """
    特征选择器
    
    使用统计方法或机器学习方法选择重要特征。
    """
    
    def __init__(self, method: str = "correlation", n_features: int = None):
        """
        初始化特征选择器
        
        Args:
            method: 选择方法 ("correlation", "variance", "importance")
            n_features: 选择的特征数量，None 表示自动
        """
        self.method = method
        self.n_features = n_features
        self.selected_features: List[str] = []
        self.feature_scores: Dict[str, float] = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray = None, 
            feature_names: List[str] = None) -> "FeatureSelector":
        """拟合特征选择器"""
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        if self.method == "correlation":
            self._fit_correlation(X, y, feature_names)
        elif self.method == "variance":
            self._fit_variance(X, feature_names)
        else:
            # 默认使用方差方法
            self._fit_variance(X, feature_names)
        
        return self
    
    def _fit_correlation(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]):
        """基于相关性选择特征"""
        if y is None:
            # 如果没有目标变量，使用下一期收益率
            y = np.roll(X[:, 0], -1)  # 假设第一个特征是收益率
            y[-1] = 0
        
        scores = {}
        for i, name in enumerate(feature_names):
            # 计算与目标的相关性
            corr = np.corrcoef(X[:, i], y)[0, 1]
            scores[name] = abs(corr) if not np.isnan(corr) else 0
        
        self.feature_scores = scores
        
        # 选择相关性最高的特征
        sorted_features = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        n = self.n_features or len(sorted_features) // 2
        self.selected_features = [f[0] for f in sorted_features[:n]]
    
    def _fit_variance(self, X: np.ndarray, feature_names: List[str]):
        """基于方差选择特征"""
        scores = {}
        for i, name in enumerate(feature_names):
            var = np.var(X[:, i])
            scores[name] = var if not np.isnan(var) else 0
        
        self.feature_scores = scores
        
        # 过滤掉方差太小的特征
        threshold = np.median(list(scores.values()))
        self.selected_features = [name for name, score in scores.items() if score >= threshold]
    
    def transform(self, X: np.ndarray, feature_names: List[str] = None) -> np.ndarray:
        """转换特征"""
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        indices = [i for i, name in enumerate(feature_names) if name in self.selected_features]
        return X[:, indices]
    
    def fit_transform(self, X: np.ndarray, y: np.ndarray = None, 
                      feature_names: List[str] = None) -> np.ndarray:
        """拟合并转换"""
        self.fit(X, y, feature_names)
        return self.transform(X, feature_names)
    
    def get_selected_features(self) -> List[str]:
        """获取选中的特征"""
        return self.selected_features
    
    def get_feature_scores(self) -> Dict[str, float]:
        """获取特征分数"""
        return self.feature_scores
