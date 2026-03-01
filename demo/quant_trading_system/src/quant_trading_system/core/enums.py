"""
枚举定义模块
============

定义系统所有业务枚举类型，支持通过接口获取枚举KV信息供前端使用。
每个枚举类都实现了 label（中文标签）和 description（描述）属性。
"""

from enum import Enum
from typing import Any


# 全局标签和描述映射表（因为 Enum 不支持在类内定义 _xxx 属性作为类属性）
_ENUM_LABELS: dict[str, dict[str, str]] = {}
_ENUM_DESCRIPTIONS: dict[str, dict[str, str]] = {}


def _register_enum_meta(cls_name: str, labels: dict[str, str], descriptions: dict[str, str]):
    """注册枚举类的标签和描述"""
    _ENUM_LABELS[cls_name] = labels
    _ENUM_DESCRIPTIONS[cls_name] = descriptions


class BaseEnum(str, Enum):
    """
    枚举基类

    所有业务枚举继承此基类，提供统一的 label/description 和序列化方法。
    """

    @property
    def label(self) -> str:
        """获取枚举的中文标签"""
        labels = _ENUM_LABELS.get(self.__class__.__name__, {})
        return labels.get(self.value, self.value)

    @property
    def description(self) -> str:
        """获取枚举的描述"""
        descriptions = _ENUM_DESCRIPTIONS.get(self.__class__.__name__, {})
        return descriptions.get(self.value, "")

    @classmethod
    def to_list(cls) -> list[dict[str, str]]:
        """将枚举转为前端可用的 KV 列表"""
        return [
            {
                "value": item.value,
                "label": item.label,
                "description": item.description,
            }
            for item in cls
        ]

    @classmethod
    def values(cls) -> list[str]:
        """获取所有枚举值"""
        return [item.value for item in cls]


# ========== 风险等级 ==========

class RiskLevel(BaseEnum):
    """风险等级（统一定义，供策略定义和风控引擎共用）"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NORMAL = "normal"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


_register_enum_meta("RiskLevel", {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "normal": "正常",
    "warning": "警告",
    "alert": "告警",
    "critical": "危险",
    "emergency": "紧急",
}, {
    "low": "保守型策略，回撤较小",
    "medium": "均衡型策略，收益与风险适中",
    "high": "激进型策略，潜在高收益高回撤",
    "normal": "风控指标正常",
    "warning": "风控指标接近阈值",
    "alert": "风控指标超过阈值",
    "critical": "风控指标严重超标",
    "emergency": "触发熔断",
})


# ========== 策略状态 ==========

class StrategyStatus(BaseEnum):
    """策略状态（统一定义，涵盖策略定义状态和运行实例状态）"""
    DRAFT = "draft"
    TESTING = "testing"
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


_register_enum_meta("StrategyStatus", {
    "draft": "草稿",
    "testing": "测试中",
    "created": "已创建",
    "initializing": "初始化中",
    "ready": "就绪",
    "running": "运行中",
    "paused": "已暂停",
    "stopping": "停止中",
    "stopped": "已停止",
    "error": "异常",
}, {
    "draft": "策略创建未发布",
    "testing": "策略正在回测或测试",
    "created": "策略实例已创建",
    "initializing": "策略实例初始化中",
    "ready": "策略实例就绪等待启动",
    "running": "策略正在运行交易",
    "paused": "策略暂时停止，保留持仓",
    "stopping": "策略停止中",
    "stopped": "策略已停止并平仓",
    "error": "策略运行出错",
})

# 向后兼容别名：StrategyState = StrategyStatus
StrategyState = StrategyStatus


# ========== 市场类型 ==========

class MarketType(BaseEnum):
    """市场类型"""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


_register_enum_meta("MarketType", {
    "spot": "现货",
    "futures": "合约",
    "margin": "杠杆",
}, {
    "spot": "现货市场",
    "futures": "期货/合约市场",
    "margin": "杠杆交易市场",
})


# ========== 策略类型 ==========

class StrategyType(BaseEnum):
    """策略类型"""
    GRID = "grid"
    TREND = "trend"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    MARTINGALE = "martingale"
    DCA = "dca"
    SWING = "swing"


_register_enum_meta("StrategyType", {
    "grid": "网格交易",
    "trend": "趋势跟踪",
    "mean_reversion": "均值回归",
    "momentum": "动量突破",
    "arbitrage": "套利策略",
    "martingale": "马丁格尔",
    "dca": "DCA定投",
    "swing": "波段交易",
}, {
    "grid": "在设定价格区间内自动高抛低吸",
    "trend": "追踪市场趋势方向进行交易",
    "mean_reversion": "价格偏离均值时反向交易",
    "momentum": "价格突破关键位时跟随交易",
    "arbitrage": "利用价差进行无风险/低风险套利",
    "martingale": "亏损后加倍下注的策略",
    "dca": "定期定额投资策略",
    "swing": "捕捉中短期波段行情",
})


# ========== K线周期 ==========

class KlineInterval(BaseEnum):
    """K线周期"""
    SEC_1 = "1s"
    MIN_1 = "1m"
    MIN_3 = "3m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    DAY_3 = "3d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


_register_enum_meta("KlineInterval", {
    "1s": "1秒",
    "1m": "1分钟",
    "3m": "3分钟",
    "5m": "5分钟",
    "15m": "15分钟",
    "30m": "30分钟",
    "1h": "1小时",
    "2h": "2小时",
    "4h": "4小时",
    "6h": "6小时",
    "8h": "8小时",
    "12h": "12小时",
    "1d": "日线",
    "3d": "3日线",
    "1w": "周线",
    "1M": "月线",
}, {
    "1s": "1秒K线",
    "1m": "1分钟K线",
    "3m": "3分钟K线",
    "5m": "5分钟K线",
    "15m": "15分钟K线",
    "30m": "30分钟K线",
    "1h": "1小时K线",
    "2h": "2小时K线",
    "4h": "4小时K线",
    "6h": "6小时K线",
    "8h": "8小时K线",
    "12h": "12小时K线",
    "1d": "1天K线",
    "3d": "3天K线",
    "1w": "1周K线",
    "1M": "1月K线",
})


# ========== 交易所 ==========

class ExchangeEnum(BaseEnum):
    """交易所"""
    BINANCE = "binance"
    BYBIT = "bybit"
    BITGET = "bitget"
    GATE_IO = "gate_io"
    HUOBI = "huobi"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    WEEX = "weex"


_register_enum_meta("ExchangeEnum", {
    "binance": "Binance",
    "bybit": "Bybit",
    "bitget": "Bitget",
    "gate_io": "Gate.io",
    "huobi": "火币",
    "kraken": "Kraken",
    "coinbase": "Coinbase",
    "weex": "WEEX",
}, {
    "binance": "币安",
    "bybit": "Bybit",
    "bitget": "Bitget",
    "gate_io": "Gate.io",
    "huobi": "火币",
    "kraken": "Kraken",
    "coinbase": "Coinbase",
    "weex": "WEEX",
})


# ========== 交易对 ==========

class TradingPair(BaseEnum):
    """交易对"""
    BTC_USDT = "BTC/USDT"
    ETH_USDT = "ETH/USDT"
    SOL_USDT = "SOL/USDT"
    BNB_USDT = "BNB/USDT"
    XRP_USDT = "XRP/USDT"
    ADA_USDT = "ADA/USDT"
    DOGE_USDT = "DOGE/USDT"
    DOT_USDT = "DOT/USDT"


_register_enum_meta("TradingPair", {
    "BTC/USDT": "比特币/泰达币",
    "ETH/USDT": "以太坊/泰达币",
    "SOL/USDT": "Solana/泰达币",
    "BNB/USDT": "币安币/泰达币",
    "XRP/USDT": "瑞波币/泰达币",
    "ADA/USDT": "卡尔达诺/泰达币",
    "DOGE/USDT": "狗狗币/泰达币",
    "DOT/USDT": "波卡/泰达币",
}, {
    "BTC/USDT": "比特币/泰达币",
    "ETH/USDT": "以太坊/泰达币",
    "SOL/USDT": "Solana/泰达币",
    "BNB/USDT": "币安币/泰达币",
    "XRP/USDT": "瑞波币/泰达币",
    "ADA/USDT": "卡尔达诺/泰达币",
    "DOGE/USDT": "狗狗币/泰达币",
    "DOT/USDT": "波卡/泰达币",
})


# ========== 系统默认交易对（启动时自动订阅WS行情 + 历史数据拉取） ==========

class DefaultTradingPair(BaseEnum):
    """系统默认支持的交易对，启动后自动订阅实时行情"""
    BTC_USDT = "BTC/USDT"
    ETH_USDT = "ETH/USDT"
    SOL_USDT = "SOL/USDT"


_register_enum_meta("DefaultTradingPair", {
    "BTC/USDT": "比特币/泰达币",
    "ETH/USDT": "以太坊/泰达币",
    "SOL/USDT": "Solana/泰达币",
}, {
    "BTC/USDT": "系统默认订阅 - 比特币",
    "ETH/USDT": "系统默认订阅 - 以太坊",
    "SOL/USDT": "系统默认订阅 - Solana",
})


# ========== 开仓模式 ==========

class TradeMode(BaseEnum):
    """开仓模式"""
    BOTH = "both"
    LONG_ONLY = "long_only"
    SHORT_ONLY = "short_only"


_register_enum_meta("TradeMode", {
    "both": "多空双开",
    "long_only": "只做多",
    "short_only": "只做空",
}, {
    "both": "同时做多和做空",
    "long_only": "仅做多头交易",
    "short_only": "仅做空头交易",
})


# ========== 止盈止损模式 ==========

class StopMode(BaseEnum):
    """止盈止损模式"""
    BOTH = "both"
    TP_ONLY = "tp_only"
    SL_ONLY = "sl_only"


_register_enum_meta("StopMode", {
    "both": "两者都可触发",
    "tp_only": "仅止盈",
    "sl_only": "仅止损",
}, {
    "both": "止盈止损都可触发",
    "tp_only": "只触发止盈",
    "sl_only": "只触发止损",
})


# ========== 信号类型 ==========

class SignalType(BaseEnum):
    """信号类型（统一定义，涵盖所有交易信号）"""
    BUY = "buy"
    SELL = "sell"
    OPEN_LONG = "open_long"
    OPEN_SHORT = "open_short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    CANCEL = "cancel"
    HOLD = "hold"


_register_enum_meta("SignalType", {
    "buy": "买入",
    "sell": "卖出",
    "open_long": "开多",
    "open_short": "开空",
    "close_long": "平多",
    "close_short": "平空",
    "cancel": "取消",
    "hold": "持有",
}, {
    "buy": "买入信号",
    "sell": "卖出信号",
    "open_long": "开多头仓位",
    "open_short": "开空头仓位",
    "close_long": "平多头仓位",
    "close_short": "平空头仓位",
    "cancel": "取消信号",
    "hold": "持有不操作",
})


# ========== 交易方向 ==========

class TradeDirection(BaseEnum):
    """交易方向"""
    LONG = "long"
    SHORT = "short"


_register_enum_meta("TradeDirection", {
    "long": "多",
    "short": "空",
}, {
    "long": "做多方向",
    "short": "做空方向",
})


# ========== 策略运行模式 ==========

class StrategyMode(BaseEnum):
    """策略运行模式"""
    LIVE = "live"
    SIMULATE = "simulate"


_register_enum_meta("StrategyMode", {
    "live": "实盘",
    "simulate": "模拟",
}, {
    "live": "连接真实交易所进行实盘交易",
    "simulate": "使用虚拟资金进行模拟交易",
})


# ========== 再平衡频率 ==========

class RebalancingFrequency(BaseEnum):
    """再平衡频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


_register_enum_meta("RebalancingFrequency", {
    "daily": "每日",
    "weekly": "每周",
    "monthly": "每月",
}, {
    "daily": "每日再平衡",
    "weekly": "每周再平衡",
    "monthly": "每月再平衡",
})


# ========== 交易所状态 ==========

class ExchangeStatus(BaseEnum):
    """交易所状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


_register_enum_meta("ExchangeStatus", {
    "active": "正常",
    "inactive": "停用",
    "maintenance": "维护中",
}, {
    "active": "交易所正常运行",
    "inactive": "交易所已停用",
    "maintenance": "交易所维护中",
})


# ========== 订单方向 ==========

class OrderSide(BaseEnum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


_register_enum_meta("OrderSide", {
    "BUY": "买入",
    "SELL": "卖出",
}, {
    "BUY": "买入订单",
    "SELL": "卖出订单",
})


# ========== 持仓方向 ==========

class PositionSide(BaseEnum):
    """持仓方向"""
    LONG = "LONG"
    SHORT = "SHORT"


_register_enum_meta("PositionSide", {
    "LONG": "多头",
    "SHORT": "空头",
}, {
    "LONG": "多头持仓",
    "SHORT": "空头持仓",
})


# ========== 订单类型 ==========

class OrderType(BaseEnum):
    """订单类型"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


_register_enum_meta("OrderType", {
    "MARKET": "市价",
    "LIMIT": "限价",
    "STOP": "止损",
    "STOP_LIMIT": "止损限价",
}, {
    "MARKET": "市价订单",
    "LIMIT": "限价订单",
    "STOP": "止损订单",
    "STOP_LIMIT": "止损限价订单",
})


# ========== 订单状态 ==========

class OrderStatus(BaseEnum):
    """订单状态"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


_register_enum_meta("OrderStatus", {
    "PENDING": "待提交",
    "SUBMITTED": "已提交",
    "OPEN": "已挂单",
    "PARTIAL_FILLED": "部分成交",
    "FILLED": "已成交",
    "CANCELLED": "已取消",
    "REJECTED": "已拒绝",
}, {
    "PENDING": "订单待提交",
    "SUBMITTED": "订单已提交到交易所",
    "OPEN": "订单已挂单等待成交",
    "PARTIAL_FILLED": "订单部分成交",
    "FILLED": "订单完全成交",
    "CANCELLED": "订单已取消",
    "REJECTED": "订单被拒绝",
})


# ========== 枚举注册表 ==========

# 所有可供前端查询的枚举类注册表
ENUM_REGISTRY: dict[str, type[BaseEnum]] = {
    "RiskLevel": RiskLevel,
    "StrategyStatus": StrategyStatus,
    "MarketType": MarketType,
    "StrategyType": StrategyType,
    "KlineInterval": KlineInterval,
    "ExchangeEnum": ExchangeEnum,
    "ExchangeStatus": ExchangeStatus,
    "TradingPair": TradingPair,
    "DefaultTradingPair": DefaultTradingPair,
    "TradeMode": TradeMode,
    "StopMode": StopMode,
    "SignalType": SignalType,
    "TradeDirection": TradeDirection,
    "StrategyMode": StrategyMode,
    "RebalancingFrequency": RebalancingFrequency,
    "OrderSide": OrderSide,
    "PositionSide": PositionSide,
    "OrderType": OrderType,
    "OrderStatus": OrderStatus,
}
