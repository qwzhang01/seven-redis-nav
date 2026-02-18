"""
交易所枚举定义
包含BG、芝麻、币安等交易所的枚举定义
"""

from enum import Enum
from typing import Dict, Any


class ExchangeCode(str, Enum):
    """
    交易所代码枚举
    """
    BG = "bg"
    ZHI_MA = "zhima"
    BINANCE = "binance"


class ExchangeName(str, Enum):
    """
    交易所名称枚举
    """
    BG = "BG交易所"
    ZHI_MA = "芝麻交易所"
    BINANCE = "币安交易所"


class ExchangeType(str, Enum):
    """
    交易所类型枚举
    """
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


class ExchangeStatus(str, Enum):
    """
    交易所状态枚举
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ExchangeConfig:
    """
    交易所配置信息
    """

    # BG交易所配置
    BG_CONFIG = {
        "exchange_code": ExchangeCode.BG,
        "exchange_name": ExchangeName.BG,
        "exchange_type": ExchangeType.SPOT,
        "base_url": "https://api.bg.com",
        "api_doc_url": "https://docs.bg.com",
        "supported_pairs": ["BTCUSDT", "ETHUSDT", "BGUSDT"],
        "rate_limits": {
            "requests_per_minute": 1000,
            "requests_per_second": 10
        }
    }

    # 芝麻交易所配置
    ZHI_MA_CONFIG = {
        "exchange_code": ExchangeCode.ZHI_MA,
        "exchange_name": ExchangeName.ZHI_MA,
        "exchange_type": ExchangeType.SPOT,
        "base_url": "https://api.zhima.com",
        "api_doc_url": "https://docs.zhima.com",
        "supported_pairs": ["BTC-USDT", "ETH-USDT", "ZM-USDT"],
        "rate_limits": {
            "requests_per_minute": 800,
            "requests_per_second": 5
        }
    }

    # 币安交易所配置
    BINANCE_CONFIG = {
        "exchange_code": ExchangeCode.BINANCE,
        "exchange_name": ExchangeName.BINANCE,
        "exchange_type": ExchangeType.SPOT,
        "base_url": "https://api.binance.com",
        "api_doc_url": "https://binance-docs.github.io/apidocs",
        "supported_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        "rate_limits": {
            "requests_per_minute": 1200,
            "requests_per_second": 20
        }
    }

    @classmethod
    def get_exchange_config(cls, exchange_code: ExchangeCode) -> Dict[str, Any]:
        """
        获取交易所配置

        Args:
            exchange_code: 交易所代码

        Returns:
            Dict[str, Any]: 交易所配置信息
        """
        configs = {
            ExchangeCode.BG: cls.BG_CONFIG,
            ExchangeCode.ZHI_MA: cls.ZHI_MA_CONFIG,
            ExchangeCode.BINANCE: cls.BINANCE_CONFIG
        }
        return configs.get(exchange_code, {})

    @classmethod
    def get_all_exchanges(cls) -> Dict[ExchangeCode, Dict[str, Any]]:
        """
        获取所有交易所配置

        Returns:
            Dict[ExchangeCode, Dict[str, Any]]: 所有交易所配置
        """
        return {
            ExchangeCode.BG: cls.BG_CONFIG,
            ExchangeCode.ZHI_MA: cls.ZHI_MA_CONFIG,
            ExchangeCode.BINANCE: cls.BINANCE_CONFIG
        }


class ExchangeSymbolFormat:
    """
    交易所交易对格式
    """

    @staticmethod
    def format_symbol(exchange_code: ExchangeCode, base_asset: str, quote_asset: str) -> str:
        """
        格式化交易对符号

        Args:
            exchange_code: 交易所代码
            base_asset: 基础资产
            quote_asset: 计价资产

        Returns:
            str: 格式化后的交易对符号
        """
        formats = {
            ExchangeCode.BG: f"{base_asset}{quote_asset}",
            ExchangeCode.ZHI_MA: f"{base_asset}-{quote_asset}",
            ExchangeCode.BINANCE: f"{base_asset}{quote_asset}"
        }
        return formats.get(exchange_code, f"{base_asset}{quote_asset}")

    @staticmethod
    def parse_symbol(exchange_code: ExchangeCode, symbol: str) -> tuple[str, str]:
        """
        解析交易对符号

        Args:
            exchange_code: 交易所代码
            symbol: 交易对符号

        Returns:
            tuple[str, str]: (基础资产, 计价资产)
        """
        if exchange_code == ExchangeCode.ZHI_MA:
            if "-" in symbol:
                parts = symbol.split("-")
                if len(parts) == 2:
                    return parts[0], parts[1]

        # 默认处理：假设最后3-4个字符是计价资产
        if len(symbol) >= 6:
            for i in range(3, 5):
                if symbol[-i:].isalpha():
                    return symbol[:-i], symbol[-i:]

        return symbol, ""


# 便捷函数
def get_exchange_name(exchange_code: ExchangeCode) -> str:
    """获取交易所名称"""
    names = {
        ExchangeCode.BG: "BG交易所",
        ExchangeCode.ZHI_MA: "芝麻交易所",
        ExchangeCode.BINANCE: "币安交易所"
    }
    return names.get(exchange_code, "未知交易所")


def get_exchange_base_url(exchange_code: ExchangeCode) -> str:
    """获取交易所基础URL"""
    urls = {
        ExchangeCode.BG: "https://api.bg.com",
        ExchangeCode.ZHI_MA: "https://api.zhima.com",
        ExchangeCode.BINANCE: "https://api.binance.com"
    }
    return urls.get(exchange_code, "")


def is_exchange_active(exchange_code: ExchangeCode) -> bool:
    """检查交易所是否活跃"""
    # 这里可以根据实际情况添加逻辑
    return exchange_code in [ExchangeCode.BG, ExchangeCode.ZHI_MA, ExchangeCode.BINANCE]
