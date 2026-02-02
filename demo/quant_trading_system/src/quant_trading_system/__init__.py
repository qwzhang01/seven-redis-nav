"""
生产级量化交易系统
==================

完整的量化交易解决方案，包含：
- 行情数据采集与处理
- 策略研发与回测
- 实盘交易执行
- 风险控制
- 监控告警
"""

__version__ = "1.0.0"
__author__ = "Quant Team"

from quant_trading_system.core.config import settings

__all__ = ["settings", "__version__"]
