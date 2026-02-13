#!/usr/bin/env python3
"""
CLI调试脚本 - 用于在PyCharm中调试量化交易系统命令
"""

import asyncio
import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_backtest():
    """调试回测功能"""
    print("=== 调试回测功能 ===")

    # 模拟CLI参数
    sys.argv = [
        "cli.py",
        "backtest",
        "--strategy", "moving_average",
        "--symbol", "BTCUSDT",
        "--timeframe", "1m",
        "--start", "2024-01-01",
        "--end", "2024-01-31",
        "--capital", "100000",
        "--commission", "0.0004",
        "--slippage", "0.0001",
        "--mock"  # 使用模拟数据，避免网络请求
    ]

    # 导入并运行CLI
    from src.quant_trading_system.cli import main
    main()


def debug_real_time_collection():
    """调试实时数据采集"""
    print("=== 调试实时数据采集 ===")

    async def run_collection():
        from src.quant_trading_system.services.market.real_time_collector import start_real_time_collection, stop_real_time_collection

        config = {
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "market_type": "spot",
                    "symbols": ["BTC/USDT", "ETH/USDT"]
                }
            },
            "storage": {
                "enabled": True,
                "batch_size": 100
            }
        }

        try:
            collector = await start_real_time_collection(config)
            print("实时数据采集已启动，运行30秒...")

            # 运行30秒后停止
            await asyncio.sleep(30)

            await stop_real_time_collection()
            print("实时数据采集已停止")

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(run_collection())


def debug_database_query():
    """调试数据库查询功能"""
    print("=== 调试数据库查询 ===")

    async def run_query():
        from src.quant_trading_system.services.database.data_query import get_data_query_service
        from src.quant_trading_system.models.market import TimeFrame
        from datetime import datetime, timedelta

        try:
            query_service = get_data_query_service()

            # 查询可用交易对
            symbols = await query_service.get_available_symbols()
            print(f"可用交易对: {symbols}")

            # 查询可用时间框架
            timeframes = await query_service.get_available_timeframes()
            print(f"可用时间框架: {timeframes}")

            # 查询数据时间范围
            time_range = await query_service.get_data_time_range(
                symbol="BTC/USDT",
                timeframe=TimeFrame.M5
            )
            print(f"BTC/USDT M5数据时间范围: {time_range}")

            # 查询K线数据
            klines = await query_service.get_klines(
                symbol="BTC/USDT",
                timeframe=TimeFrame.M5,
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now(),
                limit=100
            )
            print(f"查询到 {len(klines)} 条K线数据")

        except Exception as e:
            print(f"数据库查询错误: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(run_query())


def debug_api_server():
    """调试API服务器"""
    print("=== 调试API服务器 ===")

    # 模拟启动API服务器（开发模式）
    sys.argv = [
        "cli.py",
        "serve",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]

    from src.quant_trading_system.cli import main
    main()


def debug_strategy_list():
    """调试策略列表"""
    print("=== 调试策略列表 ===")

    sys.argv = ["cli.py", "list_strategies"]
    from src.quant_trading_system.cli import main
    main()


def debug_indicator_list():
    """调试指标列表"""
    print("=== 调试指标列表 ===")

    sys.argv = ["cli.py", "list_indicators"]
    from src.quant_trading_system.cli import main
    main()


def debug_config_check():
    """调试配置检查"""
    print("=== 调试配置检查 ===")

    sys.argv = ["cli.py", "check_config"]
    from src.quant_trading_system.cli import main
    main()


if __name__ == "__main__":
    print("量化交易系统CLI调试工具")
    print("=" * 50)

    # 选择调试功能
    options = {
        "1": ("回测功能", debug_backtest),
        "2": ("实时数据采集", debug_real_time_collection),
        "3": ("数据库查询", debug_database_query),
        "4": ("API服务器", debug_api_server),
        "5": ("策略列表", debug_strategy_list),
        "6": ("指标列表", debug_indicator_list),
        "7": ("配置检查", debug_config_check),
    }

    while True:
        print("\n选择调试功能:")
        for key, (desc, _) in options.items():
            print(f"  {key}. {desc}")
        print("  q. 退出")

        choice = input("请输入选择: ").strip()

        if choice == "q":
            print("退出调试工具")
            break

        if choice in options:
            try:
                options[choice][1]()
            except KeyboardInterrupt:
                print("\n用户中断")
            except Exception as e:
                print(f"调试过程中发生错误: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("无效选择，请重新输入")
