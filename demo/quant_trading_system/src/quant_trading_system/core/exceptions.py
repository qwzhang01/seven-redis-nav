"""
异常定义模块
============

定义系统所有自定义异常
"""

from typing import Any


class QuantTradingError(Exception):
    """量化交易系统基础异常"""
    
    def __init__(self, message: str, code: str = "", details: dict[str, Any] | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


# ========== 配置相关异常 ==========

class ConfigError(QuantTradingError):
    """配置错误"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass


# ========== 数据相关异常 ==========

class DataError(QuantTradingError):
    """数据错误"""
    pass


class DataNotFoundError(DataError):
    """数据未找到"""
    pass


class DataValidationError(DataError):
    """数据验证错误"""
    pass


class DataConnectionError(DataError):
    """数据连接错误"""
    pass


# ========== 交易相关异常 ==========

class TradingError(QuantTradingError):
    """交易错误"""
    pass


class OrderError(TradingError):
    """订单错误"""
    pass


class OrderValidationError(OrderError):
    """订单验证错误"""
    pass


class OrderSubmitError(OrderError):
    """订单提交错误"""
    pass


class OrderCancelError(OrderError):
    """订单取消错误"""
    pass


class InsufficientFundsError(TradingError):
    """资金不足"""
    pass


class InsufficientPositionError(TradingError):
    """持仓不足"""
    pass


# ========== 策略相关异常 ==========

class StrategyError(QuantTradingError):
    """策略错误"""
    pass


class StrategyNotFoundError(StrategyError):
    """策略未找到"""
    pass


class StrategyValidationError(StrategyError):
    """策略验证错误"""
    pass


class StrategyRuntimeError(StrategyError):
    """策略运行时错误"""
    pass


# ========== 回测相关异常 ==========

class BacktestError(QuantTradingError):
    """回测错误"""
    pass


class BacktestDataError(BacktestError):
    """回测数据错误"""
    pass


class BacktestConfigError(BacktestError):
    """回测配置错误"""
    pass


# ========== 风控相关异常 ==========

class RiskError(QuantTradingError):
    """风控错误"""
    pass


class RiskLimitExceededError(RiskError):
    """风险限额超出"""
    pass


class RiskCheckFailedError(RiskError):
    """风险检查失败"""
    pass


# ========== 交易所相关异常 ==========

class ExchangeError(QuantTradingError):
    """交易所错误"""
    pass


class ExchangeConnectionError(ExchangeError):
    """交易所连接错误"""
    pass


class ExchangeAPIError(ExchangeError):
    """交易所API错误"""
    
    def __init__(
        self, 
        message: str, 
        code: str = "", 
        http_status: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)
        self.http_status = http_status


class ExchangeRateLimitError(ExchangeError):
    """交易所限流错误"""
    pass


class ExchangeAuthError(ExchangeError):
    """交易所认证错误"""
    pass


# ========== 系统相关异常 ==========

class SystemError(QuantTradingError):
    """系统错误"""
    pass


class InitializationError(SystemError):
    """初始化错误"""
    pass


class ShutdownError(SystemError):
    """关闭错误"""
    pass


class TimeoutError(SystemError):
    """超时错误"""
    pass
