#!/usr/bin/env python3
"""
历史数据同步功能演示脚本

演示如何使用历史数据同步API和执行器：
1. 创建历史数据同步任务
2. 监控任务执行状态
3. 查看执行器运行状态
"""

import asyncio
import time
import requests
import json
from datetime import datetime, timedelta

# API配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1/m"

# 认证头（需要替换为实际的JWT token）
HEADERS = {
    "Authorization": "Bearer your-jwt-token-here",
    "Content-Type": "application/json"
}


def create_historical_sync_task():
    """创建历史数据同步任务"""
    url = f"{BASE_URL}{API_PREFIX}/admin/historical-sync"

    # 创建任务数据
    task_data = {
        "name": "BTC-ETH 7天历史K线数据同步",
        "exchange": "binance",
        "data_type": "kline",
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "interval": "1h",
        "start_time": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "end_time": datetime.utcnow().isoformat(),
        "batch_size": 1000
    }

    try:
        response = requests.post(url, json=task_data, headers=HEADERS)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            task_id = result["data"]["id"]
            print(f"✅ 历史数据同步任务创建成功")
            print(f"   任务ID: {task_id}")
            print(f"   任务名称: {task_data['name']}")
            print(f"   交易所: {task_data['exchange']}")
            print(f"   交易对: {', '.join(task_data['symbols'])}")
            return task_id
        else:
            print(f"❌ 创建任务失败: {result.get('error', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return None


def get_task_status(task_id: str):
    """获取任务状态"""
    url = f"{BASE_URL}{API_PREFIX}/admin/historical-sync/{task_id}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            task = result["data"]
            print(f"📊 任务状态:")
            print(f"   状态: {task['status']}")
            print(f"   进度: {task['progress']}%")
            print(f"   总记录数: {task['total_records']}")
            print(f"   已同步记录数: {task['synced_records']}")
            if task['error_message']:
                print(f"   错误信息: {task['error_message']}")
            return task
        else:
            print(f"❌ 获取任务状态失败: {result.get('error', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return None


def get_executor_status():
    """获取执行器状态"""
    url = f"{BASE_URL}{API_PREFIX}/admin/historical-sync/status/executor"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            status = result["data"]
            print(f"⚙️  执行器状态:")
            print(f"   运行状态: {'运行中' if status['executor_running'] else '已停止'}")
            print(f"   活跃任务数: {status['active_tasks']}")
            print(f"   活跃任务ID: {status['task_ids']}")
            print(f"   最大并发任务数: {status['max_concurrent_tasks']}")
            print(f"   检查间隔: {status['check_interval']}秒")
            return status
        else:
            print(f"❌ 获取执行器状态失败: {result.get('error', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return None


def list_tasks():
    """列出所有历史同步任务"""
    url = f"{BASE_URL}{API_PREFIX}/admin/historical-sync"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            tasks = result["data"]["items"]
            print(f"📋 历史同步任务列表 (共{len(tasks)}个任务):")
            for task in tasks:
                print(f"   - {task['name']} (ID: {task['id']}, 状态: {task['status']}, 进度: {task['progress']}%)")
            return tasks
        else:
            print(f"❌ 获取任务列表失败: {result.get('error', 'Unknown error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return None


async def monitor_task_progress(task_id: str, max_wait: int = 300):
    """监控任务进度"""
    print(f"🔍 开始监控任务进度 (最多等待{max_wait}秒)...")

    start_time = time.time()
    last_progress = -1

    while time.time() - start_time < max_wait:
        task = get_task_status(task_id)
        if not task:
            break

        # 检查任务状态
        if task["status"] in ["completed", "failed", "cancelled"]:
            print(f"✅ 任务完成状态: {task['status']}")
            break

        # 显示进度变化
        current_progress = task["progress"]
        if current_progress != last_progress:
            print(f"📈 进度更新: {current_progress}%")
            last_progress = current_progress

        # 等待5秒后再次检查
        await asyncio.sleep(5)
    else:
        print("⏰ 监控超时，任务仍在进行中...")


def main():
    """主演示函数"""
    print("🚀 历史数据同步功能演示")
    print("=" * 50)

    # 1. 检查执行器状态
    print("\n1. 检查执行器状态...")
    executor_status = get_executor_status()
    if not executor_status:
        print("❌ 无法获取执行器状态，请确保API服务正在运行")
        return

    # 2. 列出现有任务
    print("\n2. 查看现有任务...")
    tasks = list_tasks()

    # 3. 创建新任务
    print("\n3. 创建历史数据同步任务...")
    task_id = create_historical_sync_task()
    if not task_id:
        print("❌ 任务创建失败，演示终止")
        return

    # 4. 监控任务进度
    print("\n4. 监控任务执行进度...")
    asyncio.run(monitor_task_progress(task_id))

    # 5. 最终状态检查
    print("\n5. 最终状态检查...")
    get_executor_status()
    list_tasks()

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    # 使用说明
    print("""
使用说明:
1. 确保量化交易系统API服务正在运行 (uvicorn src.quant_trading_system.api.main:app)
2. 更新脚本中的BASE_URL和HEADERS配置
3. 运行此脚本查看历史数据同步功能演示

注意: 此演示需要有效的JWT认证token
""")

    # 询问是否继续
    response = input("是否继续演示? (y/n): ")
    if response.lower() in ['y', 'yes']:
        main()
    else:
        print("演示已取消")
