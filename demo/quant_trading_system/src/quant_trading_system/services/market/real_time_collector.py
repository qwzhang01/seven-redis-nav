"""
实时数据采集服务

集成数据收集器和数据存储服务，实现实时数据采集和存储
"""

import asyncio
from typing import List, Dict, Any, Optional
import structlog

from quant_trading_system.services.market.data_collector import (
    BinanceDataCollector,
    OKXDataCollector,
    DataCollector
)
from quant_trading_system.services.database.data_store import get_data_store

logger = structlog.get_logger(__name__)


class RealTimeCollector:
    """实时数据采集服务"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._collectors: Dict[str, DataCollector] = {}
        self._running = False

        # 数据存储服务
        self._data_store = get_data_store()

    async def start(self) -> None:
        """启动实时数据采集服务"""
        if self._running:
            return

        self._running = True

        # 启动数据存储服务
        await self._data_store.start()

        # 根据配置创建数据收集器
        await self._create_collectors()

        # 启动所有收集器
        for name, collector in self._collectors.items():
            await collector.start()

        logger.info("Real-time data collector started",
                   collectors=list(self._collectors.keys()))

    async def stop(self) -> None:
        """停止实时数据采集服务"""
        if not self._running:
            return

        self._running = False

        # 停止所有收集器
        for collector in self._collectors.values():
            await collector.stop()

        # 停止数据存储服务
        await self._data_store.stop()

        logger.info("Real-time data collector stopped")

    async def _create_collectors(self) -> None:
        """根据配置创建数据收集器"""
        # 默认配置
        default_config = {
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "market_type": "spot",
                    "symbols": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
                },
                "okx": {
                    "enabled": True,
                    "symbols": ["BTC-USDT", "ETH-USDT", "BNB-USDT"]
                }
            }
        }

        config = {**default_config, **self.config}

        # 创建币安收集器
        if config["exchanges"]["binance"]["enabled"]:
            binance_config = config["exchanges"]["binance"]
            collector = BinanceDataCollector(
                market_type=binance_config.get("market_type", "spot"),
                enable_storage=True
            )

            # 添加数据存储回调
            collector.add_callback("tick", self._on_tick_data)
            collector.add_callback("depth", self._on_depth_data)

            self._collectors["binance"] = collector

            # 订阅品种
            symbols = binance_config.get("symbols", [])
            if symbols:
                await collector.subscribe(symbols)

        # 创建OKX收集器
        if config["exchanges"]["okx"]["enabled"]:
            okx_config = config["exchanges"]["okx"]
            collector = OKXDataCollector(
                enable_storage=True
            )

            # 添加数据存储回调
            collector.add_callback("tick", self._on_tick_data)
            collector.add_callback("depth", self._on_depth_data)

            self._collectors["okx"] = collector

            # 订阅品种
            symbols = okx_config.get("symbols", [])
            if symbols:
                await collector.subscribe(symbols)

    async def _on_tick_data(self, data: Dict[str, Any]) -> None:
        """处理Tick数据"""
        try:
            # 数据已经在收集器中存储，这里可以添加额外的处理逻辑
            logger.debug("Tick data received",
                        symbol=data.get("symbol"),
                        exchange=data.get("exchange"),
                        price=data.get("last_price"))
        except Exception as e:
            logger.error("Failed to process tick data", error=str(e))

    async def _on_depth_data(self, data: Dict[str, Any]) -> None:
        """处理深度数据"""
        try:
            # 数据已经在收集器中存储，这里可以添加额外的处理逻辑
            logger.debug("Depth data received",
                        symbol=data.get("symbol"),
                        exchange=data.get("exchange"),
                        bids_count=len(data.get("bids", [])),
                        asks_count=len(data.get("asks", [])))
        except Exception as e:
            logger.error("Failed to process depth data", error=str(e))

    async def subscribe_symbols(self, exchange: str, symbols: List[str]) -> None:
        """订阅新的交易对"""
        if exchange not in self._collectors:
            logger.warning("Exchange not found", exchange=exchange)
            return

        collector = self._collectors[exchange]
        await collector.subscribe(symbols)

        logger.info("Subscribed to symbols",
                   exchange=exchange,
                   symbols=symbols)

    async def unsubscribe_symbols(self, exchange: str, symbols: List[str]) -> None:
        """取消订阅交易对"""
        if exchange not in self._collectors:
            logger.warning("Exchange not found", exchange=exchange)
            return

        collector = self._collectors[exchange]
        await collector.unsubscribe(symbols)

        logger.info("Unsubscribed from symbols",
                   exchange=exchange,
                   symbols=symbols)

    def get_collector_stats(self) -> Dict[str, Any]:
        """获取收集器统计信息"""
        stats = {}
        for name, collector in self._collectors.items():
            if hasattr(collector, '_ws_client') and collector._ws_client:
                stats[name] = {
                    'connected': collector._ws_client.is_connected,
                    'subscriptions': list(collector.subscriptions),
                    'message_count': collector._ws_client.stats.message_count if hasattr(collector._ws_client, 'stats') else 0,
                    'error_count': collector._ws_client.stats.error_count if hasattr(collector._ws_client, 'stats') else 0,
                }
        return stats

    @property
    def is_running(self) -> bool:
        return self._running


# 全局实时采集器实例
_real_time_collector: Optional[RealTimeCollector] = None


def get_real_time_collector(config: Dict[str, Any] = None) -> RealTimeCollector:
    """获取实时数据采集服务实例（单例模式）"""
    global _real_time_collector
    if _real_time_collector is None:
        _real_time_collector = RealTimeCollector(config)
    return _real_time_collector


async def start_real_time_collection(config: Dict[str, Any] = None) -> RealTimeCollector:
    """启动实时数据采集服务"""
    collector = get_real_time_collector(config)
    await collector.start()
    return collector


async def stop_real_time_collection() -> None:
    """停止实时数据采集服务"""
    global _real_time_collector
    if _real_time_collector:
        await _real_time_collector.stop()
        _real_time_collector = None
