"""
API测试脚本
==========

测试量化交易系统的API端点是否正常工作
"""

import requests
import time

def test_api_endpoints():
    """测试API端点"""
    base_url = "http://127.0.0.1:8000"

    print("🚀 开始测试量化交易系统API...")

    # 测试健康检查端点
    print("\n📊 测试健康检查端点...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ 健康检查端点正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查端点异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查端点连接失败: {e}")

    # 测试API文档端点
    print("\n📚 测试API文档端点...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API文档端点正常")
        else:
            print(f"❌ API文档端点异常: {response.status_code}")
    except Exception as e:
        print(f"❌ API文档端点连接失败: {e}")

    # 测试OpenAPI端点
    print("\n🔍 测试OpenAPI端点...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            print("✅ OpenAPI端点正常")
        else:
            print(f"❌ OpenAPI端点异常: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenAPI端点连接失败: {e}")

    print("\n🎉 API测试完成！")

if __name__ == "__main__":
    # 等待服务器完全启动
    print("⏳ 等待服务器启动...")
    time.sleep(3)

    test_api_endpoints()
