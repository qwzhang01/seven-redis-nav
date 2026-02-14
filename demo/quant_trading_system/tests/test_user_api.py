#!/usr/bin/env python3
"""
用户管理API测试脚本
测试用户注册、登录、信息获取等基本功能
"""

import requests
import json
import time
from typing import Dict, Any

# API配置
BASE_URL = "http://localhost:8000/api/v1/user"
TEST_USERNAME = "test_user_001"
TEST_PASSWORD = "test_password_123"
TEST_EMAIL = "test001@example.com"


class UserAPITester:
    """用户API测试类"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.user_id = None

    def print_test_result(self, test_name: str, success: bool, message: str = ""):
        """打印测试结果"""
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if message:
            print(f"   {message}")

    def test_user_registration(self) -> bool:
        """测试用户注册"""
        print("\n=== 测试用户注册 ===")

        registration_data = {
            "username": TEST_USERNAME,
            "nickname": "测试用户001",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "phone": "13800138000",
            "avatar_url": "https://example.com/avatar.jpg",
            "user_type": "customer"
        }

        try:
            response = requests.post(f"{self.base_url}/register", json=registration_data)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    user_data = result.get("data", {})
                    self.user_id = user_data.get("id")
                    self.print_test_result("用户注册", True, f"用户ID: {self.user_id}")
                    return True
                else:
                    self.print_test_result("用户注册", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("用户注册", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("用户注册", False, f"异常: {str(e)}")
            return False

    def test_user_login(self) -> bool:
        """测试用户登录"""
        print("\n=== 测试用户登录 ===")

        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }

        try:
            response = requests.post(f"{self.base_url}/login", json=login_data)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data", {})
                    self.access_token = data.get("access_token")
                    self.print_test_result("用户登录", True, f"令牌获取成功")
                    return True
                else:
                    self.print_test_result("用户登录", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("用户登录", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("用户登录", False, f"异常: {str(e)}")
            return False

    def test_get_user_profile(self) -> bool:
        """测试获取用户信息"""
        print("\n=== 测试获取用户信息 ===")

        if not self.access_token:
            self.print_test_result("获取用户信息", False, "未登录，无法获取用户信息")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.get(f"{self.base_url}/profile", headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    user_data = result.get("data", {})
                    self.print_test_result("获取用户信息", True,
                                          f"用户名: {user_data.get('username')}, 昵称: {user_data.get('nickname')}")
                    return True
                else:
                    self.print_test_result("获取用户信息", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("获取用户信息", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("获取用户信息", False, f"异常: {str(e)}")
            return False

    def test_update_user_profile(self) -> bool:
        """测试更新用户信息"""
        print("\n=== 测试更新用户信息 ===")

        if not self.access_token:
            self.print_test_result("更新用户信息", False, "未登录，无法更新用户信息")
            return False

        update_data = {
            "nickname": "测试用户001-修改",
            "phone": "13900139000",
            "avatar_url": "https://example.com/new-avatar.jpg"
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.put(f"{self.base_url}/profile", headers=headers, json=update_data)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    user_data = result.get("data", {})
                    self.print_test_result("更新用户信息", True,
                                          f"新昵称: {user_data.get('nickname')}")
                    return True
                else:
                    self.print_test_result("更新用户信息", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("更新用户信息", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("更新用户信息", False, f"异常: {str(e)}")
            return False

    def test_change_password(self) -> bool:
        """测试修改密码"""
        print("\n=== 测试修改密码 ===")

        if not self.access_token:
            self.print_test_result("修改密码", False, "未登录，无法修改密码")
            return False

        password_data = {
            "old_password": TEST_PASSWORD,
            "new_password": "new_password_456"
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.post(f"{self.base_url}/password/change", headers=headers, json=password_data)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.print_test_result("修改密码", True, "密码修改成功")
                    return True
                else:
                    self.print_test_result("修改密码", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("修改密码", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("修改密码", False, f"异常: {str(e)}")
            return False

    def test_get_exchanges(self) -> bool:
        """测试获取交易所列表"""
        print("\n=== 测试获取交易所列表 ===")

        if not self.access_token:
            self.print_test_result("获取交易所列表", False, "未登录，无法获取交易所列表")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            response = requests.get(f"{self.base_url}/exchanges", headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data", {})
                    exchanges = data.get("items", [])
                    self.print_test_result("获取交易所列表", True,
                                          f"共找到 {len(exchanges)} 个交易所")
                    for exchange in exchanges:
                        print(f"   - {exchange.get('exchange_name')} ({exchange.get('exchange_code')})")
                    return True
                else:
                    self.print_test_result("获取交易所列表", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("获取交易所列表", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("获取交易所列表", False, f"异常: {str(e)}")
            return False

    def test_add_api_key(self) -> bool:
        """测试添加API密钥"""
        print("\n=== 测试添加API密钥 ===")

        if not self.access_token:
            self.print_test_result("添加API密钥", False, "未登录，无法添加API密钥")
            return False

        # 先获取交易所列表
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        try:
            # 获取交易所列表
            response = requests.get(f"{self.base_url}/exchanges", headers=headers)
            if response.status_code != 200:
                self.print_test_result("添加API密钥", False, "无法获取交易所列表")
                return False

            result = response.json()
            exchanges = result.get("data", {}).get("items", [])
            if not exchanges:
                self.print_test_result("添加API密钥", False, "没有可用的交易所")
                return False

            # 使用第一个交易所
            exchange = exchanges[0]
            exchange_id = exchange.get("id")

            api_key_data = {
                "exchange_id": exchange_id,
                "label": "测试API密钥",
                "api_key": "test_api_key_123",
                "secret_key": "test_secret_key_456",
                "passphrase": "test_passphrase",
                "permissions": {
                    "spot_trading": True,
                    "margin_trading": False,
                    "futures_trading": False,
                    "withdraw": False
                }
            }

            response = requests.post(f"{self.base_url}/api-keys", headers=headers, json=api_key_data)

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    api_key_data = result.get("data", {})
                    self.print_test_result("添加API密钥", True,
                                          f"API密钥ID: {api_key_data.get('id')}, 状态: {api_key_data.get('status')}")
                    return True
                else:
                    self.print_test_result("添加API密钥", False, f"响应错误: {result.get('error')}")
                    return False
            else:
                self.print_test_result("添加API密钥", False, f"HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            self.print_test_result("添加API密钥", False, f"异常: {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("开始用户管理API测试...")
        print("=" * 50)

        tests = [
            self.test_user_registration,
            self.test_user_login,
            self.test_get_user_profile,
            self.test_update_user_profile,
            self.test_change_password,
            self.test_get_exchanges,
            self.test_add_api_key
        ]

        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                time.sleep(0.5)  # 短暂延迟避免请求过快
            except Exception as e:
                print(f"测试异常: {str(e)}")
                results.append(False)

        # 统计结果
        passed = sum(results)
        total = len(results)

        print("\n" + "=" * 50)
        print(f"测试完成: {passed}/{total} 个测试通过")

        if passed == total:
            print("🎉 所有测试通过！")
        else:
            print("❌ 部分测试失败，请检查API服务是否正常运行")

        return passed == total


def main():
    """主函数"""
    print("用户管理API测试脚本")
    print("确保API服务在 http://localhost:8000 上运行")
    print("=" * 50)

    tester = UserAPITester(BASE_URL)
    success = tester.run_all_tests()

    if success:
        print("\n✅ 测试成功完成")
        return 0
    else:
        print("\n❌ 测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
