#!/usr/bin/env python3
"""
量化交易系统测试执行和分析脚本
"""

import subprocess
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any


def run_pytest_tests() -> Dict[str, Any]:
    """执行pytest测试并返回结果"""
    print("正在执行pytest测试...")
    
    # 执行pytest测试
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "--tb=short",
        "--disable-warnings",
        "--json-report",
        "--json-report-file=test_results.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        # 读取JSON测试结果
        test_results = {}
        if os.path.exists("test_results.json"):
            with open("test_results.json", "r") as f:
                test_results = json.load(f)
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "test_results": test_results
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "test_results": {}
        }


def analyze_test_coverage() -> Dict[str, Any]:
    """分析测试覆盖率"""
    print("正在分析测试覆盖率...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src/quant_trading_system",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=json:coverage.json",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        # 读取覆盖率报告
        coverage_data = {}
        if os.path.exists("coverage.json"):
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage_data": coverage_data
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "coverage_data": {}
        }


def analyze_test_files() -> Dict[str, Any]:
    """分析测试文件结构和完整性"""
    print("正在分析测试文件结构...")
    
    test_dir = Path("tests")
    src_dir = Path("src/quant_trading_system")
    
    # 收集测试文件信息
    test_files = {}
    for test_file in test_dir.glob("test_*.py"):
        with open(test_file, "r") as f:
            content = f.read()
            
        # 统计测试函数数量
        test_functions = re.findall(r"def test_[^(]+", content)
        
        test_files[test_file.name] = {
            "size": test_file.stat().st_size,
            "test_count": len(test_functions),
            "functions": test_functions
        }
    
    # 收集源代码文件信息
    source_files = {}
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            source_files[str(py_file.relative_to(src_dir))] = {
                "size": py_file.stat().st_size
            }
    
    return {
        "test_files": test_files,
        "source_files": source_files,
        "test_file_count": len(test_files),
        "source_file_count": len(source_files)
    }


def check_code_quality() -> Dict[str, Any]:
    """检查代码质量"""
    print("正在检查代码质量...")
    
    # 使用ruff进行代码检查
    cmd = [sys.executable, "-m", "ruff", "check", "src/", "tests/"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e)
        }


def generate_test_report(results: Dict[str, Any]) -> str:
    """生成测试报告"""
    report = []
    report.append("=" * 80)
    report.append("量化交易系统测试分析报告")
    report.append("=" * 80)
    
    # 测试执行结果
    if "pytest_results" in results:
        pytest_results = results["pytest_results"]
        report.append("\n1. 测试执行结果:")
        report.append(f"   退出码: {pytest_results['returncode']}")
        
        if pytest_results["test_results"]:
            summary = pytest_results["test_results"].get("summary", {})
            report.append(f"   通过测试: {summary.get('passed', 0)}")
            report.append(f"   失败测试: {summary.get('failed', 0)}")
            report.append(f"   跳过测试: {summary.get('skipped', 0)}")
            report.append(f"   错误测试: {summary.get('error', 0)}")
            report.append(f"   总测试数: {summary.get('total', 0)}")
    
    # 测试覆盖率
    if "coverage_results" in results:
        coverage_results = results["coverage_results"]
        if coverage_results["coverage_data"]:
            totals = coverage_results["coverage_data"].get("totals", {})
            report.append("\n2. 测试覆盖率:")
            report.append(f"   语句覆盖率: {totals.get('percent_covered', 0):.2f}%")
            report.append(f"   覆盖语句数: {totals.get('covered_lines', 0)}")
            report.append(f"   总语句数: {totals.get('num_statements', 0)}")
    
    # 文件分析
    if "file_analysis" in results:
        file_analysis = results["file_analysis"]
        report.append("\n3. 文件结构分析:")
        report.append(f"   测试文件数量: {file_analysis['test_file_count']}")
        report.append(f"   源代码文件数量: {file_analysis['source_file_count']}")
        
        # 显示测试文件详情
        report.append("\n   测试文件详情:")
        for test_file, info in file_analysis["test_files"].items():
            report.append(f"     {test_file}: {info['test_count']}个测试函数")
    
    # 代码质量检查
    if "code_quality" in results:
        code_quality = results["code_quality"]
        report.append("\n4. 代码质量检查:")
        if code_quality["returncode"] == 0:
            report.append("   代码质量检查通过")
        else:
            report.append("   代码质量检查发现问题:")
            if code_quality["stdout"]:
                for line in code_quality["stdout"].split('\n')[:10]:  # 只显示前10个问题
                    if line.strip():
                        report.append(f"     {line}")
    
    # 失败测试分析
    if "pytest_results" in results and results["pytest_results"]["returncode"] != 0:
        report.append("\n5. 失败测试分析:")
        stdout_lines = results["pytest_results"]["stdout"].split('\n')
        failed_tests = []
        for line in stdout_lines:
            if "FAILED" in line:
                failed_tests.append(line.strip())
        
        for test in failed_tests[:5]:  # 只显示前5个失败测试
            report.append(f"   {test}")
    
    report.append("\n" + "=" * 80)
    return "\n".join(report)


def main():
    """主函数"""
    print("开始执行量化交易系统测试分析...")
    
    results = {}
    
    # 执行pytest测试
    results["pytest_results"] = run_pytest_tests()
    
    # 分析测试覆盖率
    results["coverage_results"] = analyze_test_coverage()
    
    # 分析测试文件结构
    results["file_analysis"] = analyze_test_files()
    
    # 检查代码质量
    results["code_quality"] = check_code_quality()
    
    # 生成报告
    report = generate_test_report(results)
    
    # 保存报告到文件
    with open("test_analysis_report.txt", "w") as f:
        f.write(report)
    
    print("\n测试分析完成！")
    print("详细报告已保存到: test_analysis_report.txt")
    print("\n" + "=" * 80)
    print(report)
    
    # 返回退出码
    sys.exit(results["pytest_results"]["returncode"])


if __name__ == "__main__":
    main()