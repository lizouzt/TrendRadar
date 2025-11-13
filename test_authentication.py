#!/usr/bin/env python3
"""
TrendRadar MCP Server 认证测试脚本

用于快速验证密码认证中间件是否正常工作。

使用方式:
  python test_authentication.py [--host localhost] [--port 3333] [--password YOUR_PASSWORD]

示例:
  python test_authentication.py
  python test_authentication.py --password MySecurePass123
"""

import requests
import sys
import argparse
import json
from typing import Tuple, Dict, Any
from datetime import datetime


class AuthenticationTester:
    """认证功能测试类"""
    
    def __init__(self, host: str = "localhost", port: int = 3333, password: str = "TrendRadar@2025SecurePass"):
        self.host = host
        self.port = port
        self.password = password
        self.base_url = f"http://{host}:{port}/mcp"
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"\n{status} | {test_name}")
        if details:
            print(f"       {details}")
    
    def test_correct_password_via_header(self) -> Tuple[bool, str]:
        """测试：使用正确的密码通过请求头访问"""
        try:
            response = requests.get(
                self.base_url,
                headers={"X-MCP-Password": self.password},
                timeout=5
            )
            passed = response.status_code == 200
            details = f"Status: {response.status_code}" + (
                f" (expected 200)" if not passed else ""
            )
            return passed, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_correct_password_via_query(self) -> Tuple[bool, str]:
        """测试：使用正确的密码通过URL查询参数访问"""
        try:
            response = requests.get(
                f"{self.base_url}?pwd={self.password}",
                timeout=5
            )
            passed = response.status_code == 200
            details = f"Status: {response.status_code}" + (
                f" (expected 200)" if not passed else ""
            )
            return passed, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_wrong_password_header(self) -> Tuple[bool, str]:
        """测试：使用错误的密码通过请求头应该被拒绝"""
        try:
            response = requests.get(
                self.base_url,
                headers={"X-MCP-Password": "wrong_password"},
                timeout=5
            )
            passed = response.status_code == 403
            details = f"Status: {response.status_code}" + (
                f" (expected 403)" if not passed else ""
            )
            return passed, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_wrong_password_query(self) -> Tuple[bool, str]:
        """测试：使用错误的密码通过URL查询参数应该被拒绝"""
        try:
            response = requests.get(
                f"{self.base_url}?pwd=wrong_password",
                timeout=5
            )
            passed = response.status_code == 403
            details = f"Status: {response.status_code}" + (
                f" (expected 403)" if not passed else ""
            )
            return passed, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_missing_password(self) -> Tuple[bool, str]:
        """测试：不提供密码应该被拒绝"""
        try:
            response = requests.get(
                self.base_url,
                timeout=5
            )
            passed = response.status_code == 403
            details = f"Status: {response.status_code}" + (
                f" (expected 403)" if not passed else ""
            )
            return passed, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def test_response_format_error(self) -> Tuple[bool, str]:
        """测试：验证错误响应格式"""
        try:
            response = requests.get(
                self.base_url,
                headers={"X-MCP-Password": "wrong_password"},
                timeout=5
            )
            data = response.json()
            has_error = "error" in data and "message" in data
            details = f"Response keys: {list(data.keys())}"
            return has_error, details
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("=" * 70)
        print("TrendRadar MCP Server - 认证功能测试")
        print("=" * 70)
        print(f"\n🔗 服务器地址: {self.base_url}")
        print(f"🔑 测试密码: {self.password}")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "-" * 70)
        
        # 首先检查服务器是否在线
        print("\n🔍 检查服务器连接...")
        try:
            response = requests.get(f"http://{self.host}:{self.port}", timeout=3)
            print(f"✅ 服务器在线 (HTTP {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务器 ({self.host}:{self.port})")
            print("   请确保服务器已启动")
            return False
        except Exception as e:
            print(f"⚠️  连接检查异常: {str(e)}")
        
        print("\n" + "-" * 70)
        print("🧪 运行认证测试...\n")
        
        # 运行测试
        tests = [
            ("✅ 测试1: 正确密码 (请求头)", self.test_correct_password_via_header),
            ("✅ 测试2: 正确密码 (URL参数)", self.test_correct_password_via_query),
            ("❌ 测试3: 错误密码 (请求头)", self.test_wrong_password_header),
            ("❌ 测试4: 错误密码 (URL参数)", self.test_wrong_password_query),
            ("❌ 测试5: 缺失密码", self.test_missing_password),
            ("📋 测试6: 错误响应格式", self.test_response_format_error),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            passed, details = test_func()
            self.log_test(test_name, passed, details)
            if not passed:
                all_passed = False
        
        # 打印总结
        print("\n" + "=" * 70)
        print("📊 测试总结")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if "✅" in r["status"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        
        if all_passed:
            print("\n🎉 所有测试通过！认证功能正常工作。")
        else:
            print("\n⚠️  部分测试失败。请检查服务器配置和密码设置。")
        
        print("\n" + "=" * 70)
        
        return all_passed


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TrendRadar MCP Server 认证功能测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_authentication.py
  python test_authentication.py --host localhost --port 3333
  python test_authentication.py --password MySecurePassword123
  python test_authentication.py --host 192.168.1.100 --port 8888 --password secret
        """
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="MCP服务器主机地址 (默认: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3333,
        help="MCP服务器端口 (默认: 3333)"
    )
    parser.add_argument(
        "--password",
        default="TrendRadar@2025SecurePass",
        help="测试用的密码 (默认: TrendRadar@2025SecurePass)"
    )
    
    args = parser.parse_args()
    
    tester = AuthenticationTester(
        host=args.host,
        port=args.port,
        password=args.password
    )
    
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
