#!/usr/bin/env python3
"""
历史数据同步执行器测试

测试历史数据同步任务执行器的基本功能
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from quant_trading_system.models.database import HistoricalSyncTask
from quant_trading_system.services.market.historical_sync_executor import (
    HistoricalSyncExecutor
)


class TestHistoricalSyncExecutor:
    """历史数据同步执行器测试类"""

    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return HistoricalSyncExecutor(
            check_interval=0.1,  # 快速检查间隔
            max_concurrent_tasks=2,
            max_retries=1
        )

    @pytest.fixture
    def mock_task(self):
        """创建模拟的历史同步任务"""
        task = Mock(spec=HistoricalSyncTask)
        task.id = "test-task-123"
        task.name = "Test Sync Task"
        task.exchange = "binance"
        task.data_type = "kline"
        task.symbols = ["BTCUSDT", "ETHUSDT"]
        task.interval = "1h"
        task.start_time = datetime.utcnow() - timedelta(days=7)
        task.end_time = datetime.utcnow()
        task.batch_size = 100
        task.status = "pending"
        task.progress = 0
        task.total_records = 0
        task.synced_records = 0
        task.error_message = None
        task.created_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        return task

    @pytest.mark.asyncio
    async def test_executor_start_stop(self, executor):
        """测试执行器启动和停止"""
        # 启动执行器
        await executor.start()
        assert executor.is_running is True

        # 停止执行器
        await executor.stop()
        assert executor.is_running is False

    @pytest.mark.asyncio
    async def test_check_pending_tasks(self, executor, mock_task):
        """测试检查待处理任务"""
        # 模拟数据库查询返回待处理任务
        with patch.object(executor, '_get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

            # 启动执行器
            await executor.start()

            # 等待检查周期
            await asyncio.sleep(0.2)

            # 检查任务是否被添加到活跃任务中
            assert len(executor._active_tasks) == 1
            assert mock_task.id in executor._active_tasks

            await executor.stop()

    @pytest.mark.asyncio
    async def test_task_execution(self, executor, mock_task):
        """测试任务执行流程"""
        # 模拟Binance API客户端
        mock_api = Mock()
        mock_api.fetch_klines = AsyncMock(return_value=[])

        with patch.object(executor, '_get_api_client', return_value=mock_api):
            with patch.object(executor, '_get_db_session') as mock_session:
                # 模拟数据库操作
                mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_task

                # 执行任务
                await executor._execute_sync_task(mock_task.id)

                # 验证API被调用
                mock_api.fetch_klines.assert_called()

    @pytest.mark.asyncio
    async def test_task_retry_logic(self, executor, mock_task):
        """测试任务重试逻辑"""
        # 模拟API调用失败
        mock_api = Mock()
        mock_api.fetch_klines = AsyncMock(side_effect=Exception("API Error"))

        with patch.object(executor, '_get_api_client', return_value=mock_api):
            with patch.object(executor, '_get_db_session') as mock_session:
                # 模拟数据库操作
                mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_task

                # 执行任务（应该会重试）
                await executor._execute_sync_task(mock_task.id)

                # 验证API被多次调用（重试）
                assert mock_api.fetch_klines.call_count == executor.max_retries

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, executor):
        """测试并发任务限制"""
        # 创建多个模拟任务
        tasks = []
        for i in range(5):
            task = Mock(spec=HistoricalSyncTask)
            task.id = f"task-{i}"
            task.status = "pending"
            tasks.append(task)

        with patch.object(executor, '_get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.order_by.return_value.all.return_value = tasks

            # 启动执行器
            await executor.start()

            # 等待检查周期
            await asyncio.sleep(0.2)

            # 检查活跃任务数量不超过限制
            assert len(executor._active_tasks) <= executor.max_concurrent_tasks

            await executor.stop()

    @pytest.mark.asyncio
    async def test_api_client_caching(self, executor):
        """测试API客户端缓存"""
        # 第一次获取
        client1 = executor._get_api_client("binance")

        # 第二次获取（应该返回缓存实例）
        client2 = executor._get_api_client("binance")

        assert client1 is client2

        # 不同交易所应该返回不同实例
        client3 = executor._get_api_client("okx")
        assert client3 is not client1

    @pytest.mark.asyncio
    async def test_executor_stats(self, executor):
        """测试执行器统计信息"""
        stats = executor.stats

        assert "running" in stats
        assert "active_tasks" in stats
        assert "task_ids" in stats

        assert stats["running"] == executor.is_running
        assert stats["active_tasks"] == len(executor._active_tasks)

    @pytest.mark.asyncio
    async def test_unsupported_exchange(self, executor, mock_task):
        """测试不支持的交易所处理"""
        mock_task.exchange = "unsupported_exchange"

        with patch.object(executor, '_get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_task

            # 执行任务（应该抛出异常）
            with pytest.raises(ValueError, match="Unsupported exchange"):
                await executor._execute_sync_task(mock_task.id)

    @pytest.mark.asyncio
    async def test_unsupported_data_type(self, executor, mock_task):
        """测试不支持的数据类型处理"""
        mock_task.data_type = "unsupported_type"

        with patch.object(executor, '_get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_task

            # 执行任务（应该抛出异常）
            with pytest.raises(ValueError, match="Unsupported data type"):
                await executor._execute_sync_task(mock_task.id)

    @pytest.mark.asyncio
    async def test_kline_data_without_interval(self, executor, mock_task):
        """测试K线数据缺少interval参数"""
        mock_task.data_type = "kline"
        mock_task.interval = None

        with patch.object(executor, '_get_db_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_task

            # 执行任务（应该抛出异常）
            with pytest.raises(ValueError, match="Kline data type requires interval"):
                await executor._execute_sync_task(mock_task.id)


@pytest.mark.asyncio
async def test_executor_lifecycle():
    """测试执行器完整生命周期"""
    executor = HistoricalSyncExecutor(check_interval=0.1)

    # 启动执行器
    await executor.start()
    assert executor.is_running is True

    # 检查统计信息
    stats = executor.stats
    assert stats["running"] is True

    # 停止执行器
    await executor.stop()
    assert executor.is_running is False


@pytest.mark.asyncio
async def test_executor_with_real_api():
    """测试执行器与真实API的集成（需要网络连接）"""
    # 这个测试需要实际的网络连接，可以在有网络的环境下运行
    executor = HistoricalSyncExecutor(check_interval=1.0)

    # 测试API客户端创建
    binance_client = executor._get_api_client("binance")
    assert binance_client is not None

    okx_client = executor._get_api_client("okx")
    assert okx_client is not None

    # 测试不支持的交易所
    unsupported_client = executor._get_api_client("unsupported")
    assert unsupported_client is None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
