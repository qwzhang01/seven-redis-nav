"""
风险管理系统性能测试
====================

测试风险管理系统在高负载、高并发下的性能表现
"""

import pytest
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from unittest.mock import Mock
from datetime import datetime

from quant_trading_system.services.risk.risk_manager import (
    RiskManager, RiskConfig, RiskLevel, RiskCheckResult
)
from quant_trading_system.models.trading import Order, OrderSide, OrderType, OrderStatus
from quant_trading_system.models.account import Account


class TestRiskPerformance:
    """风险管理系统性能测试"""

    @pytest.fixture
    def high_performance_config(self):
        """高性能配置（适合压力测试）"""
        return RiskConfig(
            max_position_value=10000000.0,
            max_position_ratio=0.9,
            max_single_position_ratio=0.3,
            max_order_value=1000000.0,
            max_order_quantity=10000.0,
            max_orders_per_minute=1000,
            max_orders_per_day=10000,
            max_daily_loss=500000.0,
            max_daily_loss_ratio=0.1,
            max_drawdown=0.3,
            min_order_interval=0.01,  # 更短的间隔
            max_price_deviation=0.2
        )

    @pytest.fixture
    def performance_account(self):
        """性能测试账户"""
        return Account(
            account_id="performance_account",
            total_equity=10000000.0,  # 1000万
            available_cash=8000000.0,
            margin=2000000.0,
            leverage=10.0,
            currency="USDT"
        )

    def test_single_order_check_performance(self, high_performance_config, performance_account):
        """测试单次订单检查性能"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 创建测试订单
        order = Order(
            order_id="performance_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="performance_account"
        )

        # 预热（避免冷启动影响）
        for _ in range(10):
            risk_manager.check_order(order, current_price=50000.0)

        # 性能测试
        start_time = time.perf_counter()

        iterations = 1000
        for i in range(iterations):
            result = risk_manager.check_order(order, current_price=50000.0)
            assert result.passed is True

        end_time = time.perf_counter()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        print(f"单次订单检查性能：")
        print(f"总时间：{total_time:.6f}秒")
        print(f"平均时间：{avg_time:.6f}秒")
        print(f"吞吐量：{iterations/total_time:.2f}次/秒")

        # 性能要求：平均检查时间 < 1毫秒
        assert avg_time < 0.001
        assert total_time < 1.0

    def test_bulk_order_check_performance(self, high_performance_config, performance_account):
        """测试批量订单检查性能"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 创建批量订单
        orders = []
        for i in range(1000):
            order = Order(
                order_id=f"bulk_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                type=OrderType.LIMIT,
                quantity=0.1 + (i % 10) * 0.1,
                price=50000.0 + (i % 100) * 100,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="performance_account"
            )
            orders.append(order)

        # 预热
        for i in range(10):
            risk_manager.check_order(orders[i], current_price=50000.0)

        # 批量性能测试
        start_time = time.perf_counter()

        passed_count = 0
        for order in orders:
            result = risk_manager.check_order(order, current_price=50000.0)
            if result.passed:
                passed_count += 1

        end_time = time.perf_counter()

        total_time = end_time - start_time
        throughput = len(orders) / total_time

        print(f"批量订单检查性能（{len(orders)}个订单）：")
        print(f"总时间：{total_time:.4f}秒")
        print(f"吞吐量：{throughput:.2f}次/秒")
        print(f"通过率：{passed_count/len(orders)*100:.1f}%")

        # 性能要求：吞吐量 > 1000次/秒
        assert throughput > 1000
        assert total_time < 1.0

    def test_concurrent_order_check_performance(self, high_performance_config, performance_account):
        """测试并发订单检查性能"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 创建共享的风险管理器（线程安全测试）
        shared_risk_manager = risk_manager

        def check_order_task(order_id, price):
            """订单检查任务"""
            order = Order(
                order_id=f"concurrent_order_{order_id}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=1.0,
                price=price,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="performance_account"
            )

            result = shared_risk_manager.check_order(order, current_price=price)
            return result.passed

        # 并发测试
        num_threads = 10
        num_orders_per_thread = 100

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                for j in range(num_orders_per_thread):
                    price = 50000.0 + (i * num_orders_per_thread + j) * 10
                    future = executor.submit(check_order_task, i * num_orders_per_thread + j, price)
                    futures.append(future)

            results = [future.result() for future in futures]

        end_time = time.perf_counter()

        total_time = end_time - start_time
        total_orders = num_threads * num_orders_per_thread
        throughput = total_orders / total_time

        print(f"并发订单检查性能（{num_threads}线程，{total_orders}订单）：")
        print(f"总时间：{total_time:.4f}秒")
        print(f"吞吐量：{throughput:.2f}次/秒")
        print(f"成功率：{sum(results)/len(results)*100:.1f}%")

        # 性能要求：并发吞吐量 > 5000次/秒
        assert throughput > 5000
        assert all(results)  # 所有检查都应该通过

    def test_memory_usage_performance(self, high_performance_config, performance_account):
        """测试内存使用性能"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # 初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 创建大量风险管理器实例
        risk_managers = []
        num_instances = 100

        for i in range(num_instances):
            risk_manager = RiskManager(config=high_performance_config)
            risk_manager.set_account(performance_account)
            risk_managers.append(risk_manager)

        # 内存使用增长
        memory_after_creation = process.memory_info().rss / 1024 / 1024
        memory_growth = memory_after_creation - initial_memory

        print(f"内存使用性能（{num_instances}个实例）：")
        print(f"初始内存：{initial_memory:.2f} MB")
        print(f"创建后内存：{memory_after_creation:.2f} MB")
        print(f"内存增长：{memory_growth:.2f} MB")
        print(f"平均每个实例：{memory_growth/num_instances:.2f} MB")

        # 内存要求：每个实例 < 1MB
        assert memory_growth / num_instances < 1.0

        # 清理
        del risk_managers

    def test_cpu_usage_performance(self, high_performance_config, performance_account):
        """测试CPU使用性能"""
        import psutil

        # 获取初始CPU使用率
        initial_cpu = psutil.cpu_percent(interval=0.1)

        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 创建大量订单进行CPU压力测试
        orders = []
        for i in range(10000):
            order = Order(
                order_id=f"cpu_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=1.0,
                price=50000.0,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="performance_account"
            )
            orders.append(order)

        # CPU压力测试
        start_time = time.perf_counter()

        for order in orders:
            risk_manager.check_order(order, current_price=50000.0)

        end_time = time.perf_counter()

        # 获取测试期间CPU使用率
        cpu_during_test = psutil.cpu_percent(interval=0.1)

        total_time = end_time - start_time
        throughput = len(orders) / total_time

        print(f"CPU使用性能（{len(orders)}个订单）：")
        print(f"总时间：{total_time:.4f}秒")
        print(f"吞吐量：{throughput:.2f}次/秒")
        print(f"初始CPU：{initial_cpu:.1f}%")
        print(f"测试期间CPU：{cpu_during_test:.1f}%")

        # 性能要求：CPU使用率不应显著增加
        assert cpu_during_test < 80.0  # 不应超过80%
        assert throughput > 5000

    def test_high_frequency_trading_performance(self, high_performance_config, performance_account):
        """测试高频交易场景性能"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 模拟高频交易：每秒1000次订单检查
        orders_per_second = 1000
        duration = 5  # 5秒测试
        total_orders = orders_per_second * duration

        orders = []
        for i in range(total_orders):
            order = Order(
                order_id=f"hft_order_{i}",
                symbol="BTC/USDT",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                type=OrderType.LIMIT,
                quantity=0.01,  # 小订单
                price=50000.0 + (i % 100) * 0.1,  # 微小价格变化
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="performance_account"
            )
            orders.append(order)

        start_time = time.perf_counter()

        passed_count = 0
        order_index = 0

        # 模拟实时高频交易
        while order_index < total_orders:
            batch_start = time.perf_counter()

            # 处理一批订单（模拟实时处理）
            batch_size = min(100, total_orders - order_index)
            for i in range(batch_size):
                order = orders[order_index + i]
                result = risk_manager.check_order(order, current_price=50000.0)
                if result.passed:
                    passed_count += 1

            order_index += batch_size

            # 控制处理速度（模拟实时性）
            batch_time = time.perf_counter() - batch_start
            if batch_time < 0.1:  # 如果处理太快，等待
                time.sleep(0.1 - batch_time)

        end_time = time.perf_counter()

        total_time = end_time - start_time
        actual_throughput = total_orders / total_time

        print(f"高频交易性能（{total_orders}订单，{duration}秒）：")
        print(f"实际时间：{total_time:.2f}秒")
        print(f"目标吞吐量：{orders_per_second}次/秒")
        print(f"实际吞吐量：{actual_throughput:.2f}次/秒")
        print(f"通过率：{passed_count/total_orders*100:.1f}%")

        # 性能要求：能够处理高频交易
        assert actual_throughput > orders_per_second * 0.8  # 达到目标80%
        assert total_time < duration * 1.5  # 不超过目标时间50%

    def test_large_scale_portfolio_performance(self, high_performance_config, performance_account):
        """测试大规模投资组合性能"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 模拟大规模投资组合：100个品种
        symbols = [f"SYMBOL_{i:03d}/USDT" for i in range(100)]

        # 为每个品种创建持仓
        for i, symbol in enumerate(symbols):
            mock_position = Mock()
            mock_position.symbol = symbol
            mock_position.notional_value = 100000.0 * (i + 1)  # 不同市值
            risk_manager.update_position(mock_position)

        # 测试指标更新性能
        start_time = time.perf_counter()

        # 多次更新指标
        for _ in range(1000):
            risk_manager._update_metrics()

        end_time = time.perf_counter()

        update_time = end_time - start_time
        avg_update_time = update_time / 1000

        print(f"大规模投资组合性能（100个品种）：")
        print(f"指标更新总时间：{update_time:.4f}秒")
        print(f"平均更新时间：{avg_update_time:.6f}秒")

        # 性能要求：指标更新 < 1毫秒
        assert avg_update_time < 0.001

        # 验证指标计算正确性
        assert risk_manager._metrics.total_position_value > 0
        assert 0 <= risk_manager._metrics.position_ratio <= 1

    def test_stress_test_extreme_conditions(self, high_performance_config, performance_account):
        """测试极端条件下的压力测试"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 极端条件：同时进行多种操作
        operations = []

        # 创建大量并发操作
        num_operations = 10000

        for i in range(num_operations):
            # 混合操作：订单检查、指标更新、风险级别更新
            if i % 3 == 0:
                # 订单检查
                order = Order(
                    order_id=f"stress_order_{i}",
                    symbol="BTC/USDT",
                    side=OrderSide.BUY,
                    type=OrderType.LIMIT,
                    quantity=1.0,
                    price=50000.0,
                    status=OrderStatus.PENDING,
                    created_time=datetime.now(),
                    account_id="performance_account"
                )
                operations.append(('check_order', order))
            elif i % 3 == 1:
                # 指标更新
                operations.append(('update_metrics', None))
            else:
                # 风险级别更新
                operations.append(('update_risk_level', None))

        start_time = time.perf_counter()

        # 执行混合操作
        for op_type, data in operations:
            if op_type == 'check_order':
                risk_manager.check_order(data, current_price=50000.0)
            elif op_type == 'update_metrics':
                risk_manager._update_metrics()
            elif op_type == 'update_risk_level':
                risk_manager._update_risk_level()

        end_time = time.perf_counter()

        total_time = end_time - start_time
        throughput = num_operations / total_time

        print(f"极端条件压力测试（{num_operations}次混合操作）：")
        print(f"总时间：{total_time:.4f}秒")
        print(f"吞吐量：{throughput:.2f}次/秒")

        # 性能要求：在极端条件下仍能保持性能
        assert throughput > 1000
        assert total_time < 10.0

    def test_long_running_stability(self, high_performance_config, performance_account):
        """测试长时间运行的稳定性"""
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 长时间运行测试：持续处理订单
        duration = 30  # 30秒
        start_time = time.perf_counter()

        order_count = 0
        last_report_time = start_time

        while time.perf_counter() - start_time < duration:
            # 持续生成和处理订单
            order = Order(
                order_id=f"long_run_order_{order_count}",
                symbol="BTC/USDT",
                side=OrderSide.BUY,
                type=OrderType.LIMIT,
                quantity=1.0,
                price=50000.0,
                status=OrderStatus.PENDING,
                created_time=datetime.now(),
                account_id="performance_account"
            )

            result = risk_manager.check_order(order, current_price=50000.0)
            assert result.passed is True

            order_count += 1

            # 定期报告
            current_time = time.perf_counter()
            if current_time - last_report_time >= 5.0:  # 每5秒报告一次
                elapsed = current_time - start_time
                throughput = order_count / elapsed
                print(f"运行 {elapsed:.1f}秒，处理 {order_count}订单，吞吐量 {throughput:.2f}次/秒")
                last_report_time = current_time

        total_time = time.perf_counter() - start_time
        final_throughput = order_count / total_time

        print(f"长时间运行稳定性测试（{duration}秒）：")
        print(f"总订单数：{order_count}")
        print(f"总时间：{total_time:.2f}秒")
        print(f"最终吞吐量：{final_throughput:.2f}次/秒")

        # 稳定性要求：长时间运行不崩溃，性能稳定
        assert order_count > 0
        assert final_throughput > 1000

        # 验证系统状态
        assert risk_manager._trading_enabled is True
        assert risk_manager._risk_level != RiskLevel.EMERGENCY

    def test_memory_leak_detection(self, high_performance_config, performance_account):
        """测试内存泄漏检测"""
        import psutil
        import os
        import gc

        process = psutil.Process(os.getpid())

        # 强制垃圾回收
        gc.collect()

        # 初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 创建并销毁大量风险管理器实例
        for i in range(1000):
            risk_manager = RiskManager(config=high_performance_config)
            risk_manager.set_account(performance_account)

            # 执行一些操作
            for j in range(10):
                order = Order(
                    order_id=f"leak_test_order_{i}_{j}",
                    symbol="BTC/USDT",
                    side=OrderSide.BUY,
                    type=OrderType.LIMIT,
                    quantity=1.0,
                    price=50000.0,
                    status=OrderStatus.PENDING,
                    created_time=datetime.now(),
                    account_id="performance_account"
                )
                risk_manager.check_order(order, current_price=50000.0)

            # 销毁实例
            del risk_manager

        # 强制垃圾回收
        gc.collect()

        # 最终内存
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        print(f"内存泄漏检测（1000个实例创建销毁）：")
        print(f"初始内存：{initial_memory:.2f} MB")
        print(f"最终内存：{final_memory:.2f} MB")
        print(f"内存增长：{memory_growth:.2f} MB")

        # 内存泄漏要求：增长 < 10MB
        assert memory_growth < 10.0

    def test_performance_regression(self, high_performance_config, performance_account):
        """测试性能回归"""
        # 基准性能测试
        risk_manager = RiskManager(config=high_performance_config)
        risk_manager.set_account(performance_account)

        # 创建测试订单
        order = Order(
            order_id="regression_order",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=1.0,
            price=50000.0,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            account_id="performance_account"
        )

        # 基准测试
        start_time = time.perf_counter()

        iterations = 10000
        for i in range(iterations):
            result = risk_manager.check_order(order, current_price=50000.0)
            assert result.passed is True

        end_time = time.perf_counter()

        baseline_time = end_time - start_time
        baseline_throughput = iterations / baseline_time

        print(f"性能回归测试基准：")
        print(f"基准时间：{baseline_time:.4f}秒")
        print(f"基准吞吐量：{baseline_throughput:.2f}次/秒")

        # 性能要求：基准性能应达到预期水平
        assert baseline_throughput > 5000
        assert baseline_time < 2.0

        # 记录基准值（可用于后续回归测试比较）
        performance_baseline = {
            'throughput': baseline_throughput,
            'time': baseline_time,
            'iterations': iterations
        }

        print(f"性能基准记录：{performance_baseline}")
