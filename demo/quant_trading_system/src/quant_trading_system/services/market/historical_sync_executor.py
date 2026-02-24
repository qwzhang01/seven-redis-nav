#!/usr/bin/env python3
"""
历史数据同步任务执行器

负责执行历史数据同步任务：
- 定期检查数据库中的pending状态的历史同步任务
- 执行实际的数据同步逻辑
- 更新任务状态和进度
- 处理错误和重试机制
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import structlog
import traceback  # 新增导入，用于获取完整异常堆栈
from sqlalchemy.orm import Session

from quant_trading_system.models.database import HistoricalSyncTask
from quant_trading_system.services.database.database import get_db
from quant_trading_system.services.market.binance_api import BinanceAPI
from quant_trading_system.services.market.okx_api import OKXAPI
from quant_trading_system.models.market import TimeFrame, Bar
from quant_trading_system.services.market.common_utils import RetryUtils

logger = structlog.get_logger(__name__)


class HistoricalSyncExecutor:
    """历史数据同步任务执行器"""

    def __init__(
        self,
        check_interval: float = 30.0,  # 检查间隔（秒）
        max_concurrent_tasks: int = 3,  # 最大并发任务数
        max_retries: int = 3,  # 最大重试次数
    ) -> None:
        self.check_interval = check_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_retries = max_retries

        # 运行状态
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # 当前正在执行的任务
        self._active_tasks: Dict[str, asyncio.Task] = {}

        # API客户端缓存
        self._api_clients: Dict[str, any] = {}

        logger.info(
            "HistoricalSyncExecutor initialized",
            check_interval=check_interval,
            max_concurrent=max_concurrent_tasks,
            max_retries=max_retries
        )

    async def start(self) -> None:
        """启动执行器"""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        logger.info("HistoricalSyncExecutor started")

    async def stop(self) -> None:
        """停止执行器"""
        if not self._running:
            return

        self._running = False

        # 取消监控任务
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # 取消所有正在执行的任务
        for task_id, task in self._active_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._active_tasks.clear()

        # 关闭API客户端
        for client in self._api_clients.values():
            if hasattr(client, 'close'):
                client.close()
        self._api_clients.clear()

        logger.info("HistoricalSyncExecutor stopped")

    async def _monitor_loop(self) -> None:
        """监控循环 - 定期检查待处理的任务"""
        while self._running:
            try:
                await self._check_pending_tasks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 获取完整的异常堆栈信息
                error_stack = traceback.format_exc()
                logger.error("Error in monitor loop",
                           error=str(e),
                           error_type=type(e).__name__,
                           error_stack=error_stack)  # 新增：记录完整堆栈信息
                await asyncio.sleep(self.check_interval)

    async def _check_pending_tasks(self) -> None:
        """检查待处理的历史同步任务"""
        if len(self._active_tasks) >= self.max_concurrent_tasks:
            return

        try:
            db_gen = get_db()
            session = next(db_gen)

            try:
                # 查找pending状态的任务，按创建时间排序
                pending_tasks = session.query(HistoricalSyncTask).filter(
                    HistoricalSyncTask.status == "pending"
                ).order_by(HistoricalSyncTask.created_at.asc()).all()

                for task in pending_tasks:
                    if len(self._active_tasks) >= self.max_concurrent_tasks:
                        break

                    # 检查任务是否已存在（避免重复执行）
                    if task.id not in self._active_tasks:
                        # 启动任务执行
                        self._active_tasks[task.id] = asyncio.create_task(
                            self._execute_sync_task(task.id),
                            name=f"sync-task-{task.id}"
                        )
                        logger.info("Started sync task", task_id=task.id, name=task.name)

            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        except Exception as e:
            # 获取完整的异常堆栈信息
            error_stack = traceback.format_exc()
            logger.error("Error checking pending tasks",
                       error=str(e),
                       error_type=type(e).__name__,
                       error_stack=error_stack)  # 新增：记录完整堆栈信息

    async def _execute_sync_task(self, task_id: str) -> None:
        """执行单个历史数据同步任务"""
        retry_count = 0

        while retry_count < self.max_retries and self._running:
            try:
                db_gen = get_db()
                session = next(db_gen)

                try:
                    # 获取任务详情
                    task = session.query(HistoricalSyncTask).filter(
                        HistoricalSyncTask.id == task_id
                    ).first()

                    if not task:
                        logger.warning("Task not found", task_id=task_id)
                        break

                    # 检查任务状态（可能已被取消）
                    if task.status != "pending":
                        logger.info("Task status changed, skipping",
                                  task_id=task_id, status=task.status)
                        break

                    # 更新任务状态为running
                    task.status = "running"
                    task.updated_at = datetime.utcnow()
                    session.commit()

                    logger.info("Starting historical data sync",
                              task_id=task_id, name=task.name,
                              exchange=task.exchange, data_type=task.data_type)

                    # 执行数据同步
                    await self._sync_historical_data(task, session)

                    # 任务完成
                    task.status = "completed"
                    task.progress = 100
                    task.completed_at = datetime.utcnow()
                    task.updated_at = datetime.utcnow()
                    session.commit()

                    logger.info("Historical data sync completed",
                              task_id=task_id, name=task.name)
                    break

                except Exception as e:
                    session.rollback()

                    # 获取完整的异常堆栈信息
                    error_stack = traceback.format_exc()

                    # 更新任务状态为failed
                    db_gen = get_db()
                    session = next(db_gen)

                    task = session.query(HistoricalSyncTask).filter(
                        HistoricalSyncTask.id == task_id
                    ).first()

                    if task:
                        task.status = "failed"
                        task.error_message = str(e)
                        task.updated_at = datetime.utcnow()
                        session.commit()

                    logger.error("Historical data sync failed",
                               task_id=task_id, error=str(e),
                               error_type=type(e).__name__,
                               error_stack=error_stack,  # 新增：记录完整堆栈信息
                               retry_count=retry_count)

                    retry_count += 1

                    if retry_count < self.max_retries:
                        # 等待一段时间后重试
                        await asyncio.sleep(60 * retry_count)  # 指数退避
                    else:
                        break

                finally:
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            except Exception as e:
                # 获取完整的异常堆栈信息
                error_stack = traceback.format_exc()
                logger.error("Unexpected error in task execution",
                           task_id=task_id, error=str(e),
                           error_type=type(e).__name__,
                           error_stack=error_stack)  # 新增：记录完整堆栈信息
                retry_count += 1
                await asyncio.sleep(30)

        # 从活跃任务中移除
        if task_id in self._active_tasks:
            del self._active_tasks[task_id]

    async def _sync_historical_data(self, task: HistoricalSyncTask, session: Session) -> None:
        """执行实际的历史数据同步逻辑"""
        exchange = task.exchange.lower()
        data_type = task.data_type
        symbols = task.symbols

        # 获取对应的API客户端
        api_client = self._get_api_client(exchange)
        if not api_client:
            raise ValueError(f"Unsupported exchange: {exchange}")

        # 根据数据类型执行不同的同步逻辑
        if data_type == "kline":
            await self._sync_kline_data(task, api_client, session)
        elif data_type == "ticker":
            await self._sync_ticker_data(task, api_client, session)
        elif data_type == "depth":
            await self._sync_depth_data(task, api_client, session)
        elif data_type == "trade":
            await self._sync_trade_data(task, api_client, session)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    async def _sync_kline_data(self, task: HistoricalSyncTask, api_client, session: Session) -> None:
        """同步K线数据"""
        if not task.interval:
            raise ValueError("Kline data type requires interval parameter")

        # 转换时间周期格式
        timeframe_map = {
            "1m": TimeFrame.M1,
            "5m": TimeFrame.M5,
            "15m": TimeFrame.M15,
            "30m": TimeFrame.M30,
            "1h": TimeFrame.H1,
            "4h": TimeFrame.H4,
            "1d": TimeFrame.D1,
            "1w": TimeFrame.W1,
        }

        timeframe = timeframe_map.get(task.interval)
        if not timeframe:
            raise ValueError(f"Unsupported interval: {task.interval}")

        total_records = 0

        # 获取数据存储服务
        from quant_trading_system.services.database.data_store import get_data_store
        data_store = get_data_store()

        for symbol in task.symbols:
            try:
                # 使用改进的重试机制获取K线数据
                bar_array = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: RetryUtils.execute_with_progressive_retry(
                        api_client.fetch_klines,
                        max_retries=5,  # 增加重试次数
                        base_delay=2.0,  # 增加基础延迟
                        symbol=symbol,
                        timeframe=timeframe,
                        start_time=task.start_time.isoformat(),
                        end_time=task.end_time.isoformat(),
                        limit=task.batch_size
                    )
                )

                # 将数据存储到数据库
                for i in range(len(bar_array)):
                    # 将numpy.datetime64转换为Python datetime
                    timestamp_dt = bar_array.timestamp[i].astype(datetime)

                    # 创建Bar对象
                    bar = Bar(
                        timestamp=timestamp_dt,
                        open=bar_array.open[i],
                        high=bar_array.high[i],
                        low=bar_array.low[i],
                        close=bar_array.close[i],
                        volume=bar_array.volume[i],
                        symbol=symbol,
                        exchange=task.exchange,
                        timeframe=timeframe,
                        is_closed=True
                    )

                    # 存储到数据库
                    await data_store.store_kline(bar)

                total_records += len(bar_array)

                # 更新进度
                progress = min(100, int((total_records / (len(task.symbols) * 1000)) * 100))

                task.progress = progress
                task.total_records = total_records
                task.synced_records = total_records
                task.updated_at = datetime.utcnow()
                session.commit()

                logger.info("Synced kline data",
                         symbol=symbol, records=len(bar_array), progress=progress)

            except Exception as e:
                # 获取完整的异常堆栈信息
                error_stack = traceback.format_exc()
                logger.error(
                    "Failed to sync kline data for symbol",
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__,
                    error_stack=error_stack  # 新增：记录完整堆栈信息
                )
                # 继续处理下一个symbol，而不是整个任务失败
                continue

        # 确保所有数据都刷新到数据库
        await data_store.flush_all()

    async def _sync_ticker_data(self, task: HistoricalSyncTask, api_client, session: Session) -> None:
        """同步Ticker数据"""
        # Ticker数据通常是实时数据，历史Ticker可能需要特殊处理
        # 这里需要根据具体交易所API来实现
        raise NotImplementedError("Ticker data sync not implemented")

    async def _sync_depth_data(self, task: HistoricalSyncTask, api_client, session: Session) -> None:
        """同步深度数据"""
        # 深度数据通常是实时数据，历史深度数据可能需要特殊处理
        raise NotImplementedError("Depth data sync not implemented")

    async def _sync_trade_data(self, task: HistoricalSyncTask, api_client, session: Session) -> None:
        """同步成交数据"""
        # 成交数据通常是实时数据，历史成交数据可能需要特殊处理
        raise NotImplementedError("Trade data sync not implemented")

    def _get_api_client(self, exchange: str):
        """获取API客户端"""
        if exchange not in self._api_clients:
            if exchange == "binance":
                self._api_clients[exchange] = BinanceAPI()
            elif exchange == "okx":
                self._api_clients[exchange] = OKXAPI()
            else:
                return None

        return self._api_clients[exchange]

    @property
    def is_running(self) -> bool:
        """检查执行器是否在运行"""
        return self._running

    @property
    def stats(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            "running": self._running,
            "active_tasks": len(self._active_tasks),
            "task_ids": list(self._active_tasks.keys())
        }


# 全局执行器实例
_historical_sync_executor: Optional[HistoricalSyncExecutor] = None


def get_historical_sync_executor() -> HistoricalSyncExecutor:
    """获取历史数据同步执行器实例（单例模式）"""
    global _historical_sync_executor
    if _historical_sync_executor is None:
        _historical_sync_executor = HistoricalSyncExecutor()
    return _historical_sync_executor


async def init_historical_sync_executor() -> HistoricalSyncExecutor:
    """初始化历史数据同步执行器"""
    executor = get_historical_sync_executor()
    await executor.start()
    return executor


async def close_historical_sync_executor() -> None:
    """关闭历史数据同步执行器"""
    global _historical_sync_executor
    if _historical_sync_executor:
        await _historical_sync_executor.stop()
        _historical_sync_executor = None
