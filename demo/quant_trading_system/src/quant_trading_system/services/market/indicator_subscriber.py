"""
指标计算订阅器
==============

独立负责指标计算和推送，从 WebSocketSubscriber 中剥离。

职责：
- 监听K线闭合事件
- 检查前端是否订阅了指标频道
- 计算指标并推送到前端 WebSocket
"""

from typing import Any

import numpy as np
import structlog

from quant_trading_system.core.enums import KlineInterval
from quant_trading_system.engines.market_event_bus import (
    MarketEvent,
    MarketEventType,
    MarketSubscriber,
)

logger = structlog.get_logger(__name__)


class IndicatorSubscriber(MarketSubscriber):
    """
    指标计算推送订阅器

    职责：K线闭合后，检查是否有前端订阅了指标频道，
    若有则计算并推送指标数据。

    工作流程：
    1. 接收 KLINE 事件
    2. 仅处理已闭合的K线
    3. 获取当前被订阅的 indicator/{symbol}/{timeframe}/{indicator_name} 频道
    4. 匹配当前闭合K线对应的 symbol 和 timeframe
    5. 从 KLineEngine 内存缓冲区获取最近的 BarArray
    6. 用 IndicatorEngine 计算指标最新值
    7. 推送到对应频道
    """

    @property
    def name(self) -> str:
        return "IndicatorSubscriber"

    async def on_event(self, event: MarketEvent) -> None:
        """处理行情事件：仅处理已闭合K线的指标计算"""
        try:
            if event.type == MarketEventType.KLINE:
                if event.data.get("is_closed", False):
                    await self._push_indicators_for_kline(event.data)
        except Exception as e:
            logger.debug("指标计算推送失败", exc_info=True, event_type=event.type.name)

    async def _push_indicators_for_kline(self, data: dict[str, Any]) -> None:
        """
        K线闭合后，检查是否有前端订阅了指标频道，若有则计算并推送
        """
        from quant_trading_system.api.websocket.market_ws import (
            get_indicator_channels,
            push_indicator,
        )

        symbol_key = data.get("symbol", "").replace("/", "").replace("-", "")
        timeframe = data.get("interval", "1m")
        if not symbol_key:
            return

        # 获取当前被订阅的指标频道
        subscribed_channels = get_indicator_channels()
        if not subscribed_channels:
            return

        # 筛选出匹配当前 symbol + timeframe 的指标频道
        prefix = f"indicator/{symbol_key}/{timeframe}/"
        matched_indicators: list[str] = []
        for ch in subscribed_channels:
            if ch.startswith(prefix):
                indicator_name = ch[len(prefix):]
                if indicator_name:
                    matched_indicators.append(indicator_name)

        if not matched_indicators:
            return

        # 从 KLineEngine 缓冲区获取 BarArray
        try:
            from quant_trading_system.core.container import container
            market_service = container.market_service
            bar_array = market_service.get_bar_array(
                symbol_key,
                KlineInterval(timeframe),
            )
        except Exception as e:
            logger.debug("获取K线缓冲区数据失败", exc_info=True, symbol=symbol_key, timeframe=timeframe)
            return

        if bar_array is None or len(bar_array) == 0:
            return

        # 获取指标引擎
        try:
            from quant_trading_system.indicators.indicator_engine import get_indicator_engine
            indicator_engine = get_indicator_engine()
        except Exception as e:
            logger.debug("获取指标引擎失败", exc_info=True)
            return

        # 逐个计算并推送
        for indicator_name in matched_indicators:
            try:
                result = indicator_engine.calculate(indicator_name, bar_array)

                # 提取各输出字段的最新值
                latest_values: dict[str, Any] = {}
                for key, values in result.values.items():
                    if len(values) > 0 and not np.isnan(values[-1]):
                        latest_values[key] = round(float(values[-1]), 8)
                    else:
                        latest_values[key] = None

                await push_indicator(
                    symbol_key,
                    timeframe,
                    indicator_name,
                    {
                        "indicator": indicator_name,
                        "symbol": data.get("symbol", ""),
                        "timeframe": timeframe,
                        "timestamp": data.get("timestamp", 0),
                        "values": latest_values,
                    },
                )
            except Exception as e:
                logger.debug(
                    "指标计算或推送失败",
                    indicator=indicator_name,
                    exc_info=True,
                    symbol=symbol_key,
                    timeframe=timeframe,
                )
