#!/usr/bin/env python3
"""
实时数据订阅管理 API 测试脚本
测试订阅配置 CRUD、状态控制以及手动同步任务管理
"""

import requests
import time
from typing import Optional

# API 配置
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"
NORMAL_USERNAME = "user1"
NORMAL_PASSWORD = "password123"


class SubscriptionAPITester:
    """订阅管理 API 测试类"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.admin_token: Optional[str] = None
        self.normal_token: Optional[str] = None
        self.created_subscription_id: Optional[str] = None
        self.created_task_id: Optional[str] = None
        self.pass_count = 0
        self.fail_count = 0

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    def _print(self, name: str, ok: bool, msg: str = "") -> None:
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  {name}: {status}")
        if msg:
            print(f"    {msg}")
        if ok:
            self.pass_count += 1
        else:
            self.fail_count += 1

    def _admin_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.admin_token}"}

    def _normal_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.normal_token}"}

    def _login(self, username: str, password: str) -> Optional[str]:
        """登录并返回 token"""
        resp = requests.post(
            f"{self.base_url}/c/user/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json()["data"]["access_token"]
        return None

    # ── 准备工作 ──────────────────────────────────────────────────────────────

    def setup(self) -> bool:
        """登录管理员和普通用户"""
        print("\n=== 准备：登录账号 ===")
        self.admin_token = self._login(ADMIN_USERNAME, ADMIN_PASSWORD)
        self._print("管理员登录", self.admin_token is not None)

        self.normal_token = self._login(NORMAL_USERNAME, NORMAL_PASSWORD)
        self._print("普通用户登录", self.normal_token is not None)

        return self.admin_token is not None

    # ── 订阅管理测试 ──────────────────────────────────────────────────────────

    def test_create_subscription_by_admin(self) -> bool:
        """管理员创建订阅"""
        print("\n=== 测试：创建订阅（管理员）===")
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._admin_headers(),
            json={
                "name": "测试-Binance BTC K线",
                "exchange": "binance",
                "market_type": "spot",
                "data_type": "kline",
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "interval": "1h",
                "config": {
                    "auto_restart": True,
                    "max_retries": 3,
                    "batch_size": 1000,
                    "sync_interval": 60,
                },
            },
        )
        ok = resp.status_code == 201 and resp.json().get("success")
        if ok:
            self.created_subscription_id = resp.json()["data"]["id"]
        self._print("创建订阅（管理员）", ok, f"ID={self.created_subscription_id}" if ok else resp.text[:200])
        return ok

    def test_create_subscription_by_normal_user(self) -> None:
        """普通用户创建订阅应被拒绝（403）"""
        print("\n=== 测试：创建订阅（普通用户，应被拒绝）===")
        if not self.normal_token:
            self._print("普通用户创建订阅被拒绝", False, "普通用户未登录，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._normal_headers(),
            json={
                "name": "非法订阅",
                "exchange": "binance",
                "data_type": "ticker",
                "symbols": ["BTCUSDT"],
            },
        )
        ok = resp.status_code == 403
        self._print("普通用户创建订阅被拒绝（403）", ok, f"实际状态码={resp.status_code}")

    def test_create_subscription_invalid_exchange(self) -> None:
        """非法交易所名称应返回 422"""
        print("\n=== 测试：创建订阅（非法交易所）===")
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._admin_headers(),
            json={
                "name": "非法交易所订阅",
                "exchange": "invalid_exchange",
                "data_type": "ticker",
                "symbols": ["BTCUSDT"],
            },
        )
        ok = resp.status_code == 422
        self._print("非法交易所返回 422", ok, f"实际状态码={resp.status_code}")

    def test_create_subscription_kline_without_interval(self) -> None:
        """kline 类型不传 interval 应返回 422"""
        print("\n=== 测试：创建订阅（kline 缺少 interval）===")
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._admin_headers(),
            json={
                "name": "缺少interval的K线订阅",
                "exchange": "binance",
                "data_type": "kline",
                "symbols": ["BTCUSDT"],
                # 故意不传 interval
            },
        )
        ok = resp.status_code == 422
        self._print("kline 缺少 interval 返回 422", ok, f"实际状态码={resp.status_code}")

    def test_list_subscriptions(self) -> None:
        """获取订阅列表"""
        print("\n=== 测试：获取订阅列表 ===")
        resp = requests.get(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._admin_headers(),
            params={"page": 1, "page_size": 10},
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        data = resp.json().get("data", {}) if ok else {}
        self._print(
            "获取订阅列表",
            ok,
            f"total={data.get('total', '?')}" if ok else resp.text[:200],
        )

    def test_list_subscriptions_with_filter(self) -> None:
        """按交易所和状态筛选订阅列表"""
        print("\n=== 测试：筛选订阅列表 ===")
        resp = requests.get(
            f"{self.base_url}/m/market/subscriptions",
            headers=self._admin_headers(),
            params={"exchange": "binance", "status": "stopped", "page": 1, "page_size": 10},
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("筛选订阅列表（exchange+status）", ok, resp.text[:200] if not ok else "")

    def test_get_subscription_statistics(self) -> None:
        """获取订阅统计信息"""
        print("\n=== 测试：获取订阅统计信息 ===")
        resp = requests.get(
            f"{self.base_url}/m/market/subscriptions/statistics",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        data = resp.json().get("data", {}) if ok else {}
        self._print(
            "获取订阅统计信息",
            ok,
            f"total={data.get('total_subscriptions', '?')}, running={data.get('running_subscriptions', '?')}"
            if ok else resp.text[:200],
        )

    def test_get_subscription_detail(self) -> None:
        """获取订阅详情"""
        print("\n=== 测试：获取订阅详情 ===")
        if not self.created_subscription_id:
            self._print("获取订阅详情", False, "无可用订阅ID，跳过")
            return
        resp = requests.get(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("获取订阅详情", ok, resp.text[:200] if not ok else "")

    def test_get_subscription_not_found(self) -> None:
        """获取不存在的订阅应返回 404"""
        print("\n=== 测试：获取不存在的订阅 ===")
        resp = requests.get(
            f"{self.base_url}/m/market/subscriptions/nonexistent-id-000",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 404
        self._print("获取不存在订阅返回 404", ok, f"实际状态码={resp.status_code}")

    def test_update_subscription(self) -> None:
        """更新订阅配置"""
        print("\n=== 测试：更新订阅配置 ===")
        if not self.created_subscription_id:
            self._print("更新订阅配置", False, "无可用订阅ID，跳过")
            return
        resp = requests.put(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}",
            headers=self._admin_headers(),
            json={
                "name": "测试-Binance BTC K线（已更新）",
                "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
                "config": {"sync_interval": 30},
            },
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("更新订阅配置", ok, resp.text[:200] if not ok else "")

    # ── 状态控制测试 ──────────────────────────────────────────────────────────

    def test_start_subscription(self) -> None:
        """启动订阅"""
        print("\n=== 测试：启动订阅 ===")
        if not self.created_subscription_id:
            self._print("启动订阅", False, "无可用订阅ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}/start",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        status_val = resp.json().get("data", {}).get("status") if ok else None
        self._print("启动订阅", ok and status_val == "running", f"status={status_val}" if ok else resp.text[:200])

    def test_pause_subscription(self) -> None:
        """暂停订阅"""
        print("\n=== 测试：暂停订阅 ===")
        if not self.created_subscription_id:
            self._print("暂停订阅", False, "无可用订阅ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}/pause",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        status_val = resp.json().get("data", {}).get("status") if ok else None
        self._print("暂停订阅", ok and status_val == "paused", f"status={status_val}" if ok else resp.text[:200])

    def test_stop_subscription(self) -> None:
        """停止订阅"""
        print("\n=== 测试：停止订阅 ===")
        if not self.created_subscription_id:
            self._print("停止订阅", False, "无可用订阅ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}/stop",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        status_val = resp.json().get("data", {}).get("status") if ok else None
        self._print("停止订阅", ok and status_val == "stopped", f"status={status_val}" if ok else resp.text[:200])

    def test_invalid_state_transition(self) -> None:
        """非法状态转换（stopped 状态下暂停）应返回 400"""
        print("\n=== 测试：非法状态转换 ===")
        if not self.created_subscription_id:
            self._print("非法状态转换返回 400", False, "无可用订阅ID，跳过")
            return
        # 当前应为 stopped，尝试暂停（不合法）
        resp = requests.post(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}/pause",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 400
        self._print("非法状态转换返回 400", ok, f"实际状态码={resp.status_code}")

    # ── 同步任务测试 ──────────────────────────────────────────────────────────

    def test_create_sync_task(self) -> bool:
        """创建同步任务"""
        print("\n=== 测试：创建同步任务 ===")
        if not self.created_subscription_id:
            self._print("创建同步任务", False, "无可用订阅ID，跳过")
            return False
        resp = requests.post(
            f"{self.base_url}/m/market/sync-tasks",
            headers=self._admin_headers(),
            json={
                "subscription_id": self.created_subscription_id,
                "start_time": "2026-01-01T00:00:00Z",
                "end_time": "2026-01-31T23:59:59Z",
            },
        )
        ok = resp.status_code == 201 and resp.json().get("success")
        if ok:
            self.created_task_id = resp.json()["data"]["id"]
        self._print("创建同步任务", ok, f"ID={self.created_task_id}" if ok else resp.text[:200])
        return ok

    def test_create_sync_task_invalid_time_range(self) -> None:
        """结束时间早于开始时间应返回 400"""
        print("\n=== 测试：创建同步任务（非法时间范围）===")
        if not self.created_subscription_id:
            self._print("非法时间范围返回 400", False, "无可用订阅ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/sync-tasks",
            headers=self._admin_headers(),
            json={
                "subscription_id": self.created_subscription_id,
                "start_time": "2026-02-01T00:00:00Z",
                "end_time": "2026-01-01T00:00:00Z",  # 结束早于开始
            },
        )
        ok = resp.status_code == 400
        self._print("非法时间范围返回 400", ok, f"实际状态码={resp.status_code}")

    def test_list_sync_tasks(self) -> None:
        """获取同步任务列表"""
        print("\n=== 测试：获取同步任务列表 ===")
        resp = requests.get(
            f"{self.base_url}/m/market/sync-tasks",
            headers=self._admin_headers(),
            params={"page": 1, "page_size": 10},
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        data = resp.json().get("data", {}) if ok else {}
        self._print(
            "获取同步任务列表",
            ok,
            f"total={data.get('total', '?')}" if ok else resp.text[:200],
        )

    def test_list_sync_tasks_by_subscription(self) -> None:
        """按订阅ID筛选同步任务"""
        print("\n=== 测试：按订阅ID筛选同步任务 ===")
        if not self.created_subscription_id:
            self._print("按订阅ID筛选同步任务", False, "无可用订阅ID，跳过")
            return
        resp = requests.get(
            f"{self.base_url}/m/market/sync-tasks",
            headers=self._admin_headers(),
            params={"subscription_id": self.created_subscription_id, "page": 1, "page_size": 10},
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("按订阅ID筛选同步任务", ok, resp.text[:200] if not ok else "")

    def test_get_sync_task_detail(self) -> None:
        """获取同步任务详情"""
        print("\n=== 测试：获取同步任务详情 ===")
        if not self.created_task_id:
            self._print("获取同步任务详情", False, "无可用任务ID，跳过")
            return
        resp = requests.get(
            f"{self.base_url}/m/market/sync-tasks/{self.created_task_id}",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("获取同步任务详情", ok, resp.text[:200] if not ok else "")

    def test_cancel_sync_task(self) -> None:
        """取消同步任务"""
        print("\n=== 测试：取消同步任务 ===")
        if not self.created_task_id:
            self._print("取消同步任务", False, "无可用任务ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/sync-tasks/{self.created_task_id}/cancel",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        status_val = resp.json().get("data", {}).get("status") if ok else None
        self._print("取消同步任务", ok and status_val == "cancelled", f"status={status_val}" if ok else resp.text[:200])

    def test_cancel_already_cancelled_task(self) -> None:
        """重复取消已取消的任务应返回 400"""
        print("\n=== 测试：重复取消任务 ===")
        if not self.created_task_id:
            self._print("重复取消任务返回 400", False, "无可用任务ID，跳过")
            return
        resp = requests.post(
            f"{self.base_url}/m/market/sync-tasks/{self.created_task_id}/cancel",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 400
        self._print("重复取消任务返回 400", ok, f"实际状态码={resp.status_code}")

    # ── 清理 ──────────────────────────────────────────────────────────────────

    def test_delete_subscription(self) -> None:
        """删除订阅（级联删除同步任务）"""
        print("\n=== 测试：删除订阅 ===")
        if not self.created_subscription_id:
            self._print("删除订阅", False, "无可用订阅ID，跳过")
            return
        resp = requests.delete(
            f"{self.base_url}/m/market/subscriptions/{self.created_subscription_id}",
            headers=self._admin_headers(),
        )
        ok = resp.status_code == 200 and resp.json().get("success")
        self._print("删除订阅", ok, resp.text[:200] if not ok else "")
        if ok:
            self.created_subscription_id = None

    # ── 主流程 ────────────────────────────────────────────────────────────────

    def run_all_tests(self) -> bool:
        print("=" * 60)
        print("  实时数据订阅管理 API 测试")
        print("=" * 60)

        if not self.setup():
            print("\n❌ 管理员登录失败，无法继续测试")
            return False

        # 订阅管理
        self.test_create_subscription_by_admin()
        self.test_create_subscription_by_normal_user()
        self.test_create_subscription_invalid_exchange()
        self.test_create_subscription_kline_without_interval()
        self.test_list_subscriptions()
        self.test_list_subscriptions_with_filter()
        self.test_get_subscription_statistics()
        self.test_get_subscription_detail()
        self.test_get_subscription_not_found()
        self.test_update_subscription()

        # 状态控制
        self.test_start_subscription()
        self.test_pause_subscription()
        self.test_stop_subscription()
        self.test_invalid_state_transition()

        # 同步任务
        self.test_create_sync_task()
        self.test_create_sync_task_invalid_time_range()
        self.test_list_sync_tasks()
        self.test_list_sync_tasks_by_subscription()
        self.test_get_sync_task_detail()
        self.test_cancel_sync_task()
        self.test_cancel_already_cancelled_task()

        # 清理
        self.test_delete_subscription()

        # 汇总
        total = self.pass_count + self.fail_count
        print("\n" + "=" * 60)
        print(f"  测试完成：{self.pass_count}/{total} 通过，{self.fail_count} 失败")
        print("=" * 60)
        if self.fail_count == 0:
            print("🎉 所有测试通过！")
        else:
            print("❌ 部分测试失败，请检查 API 服务是否正常运行")
        return self.fail_count == 0


def main():
    print("实时数据订阅管理 API 测试脚本")
    print("确保 API 服务在 http://localhost:8000 上运行")
    tester = SubscriptionAPITester(BASE_URL)
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
