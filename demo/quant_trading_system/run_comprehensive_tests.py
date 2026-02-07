#!/usr/bin/env python3
"""
量化交易系统 - 综合测试执行和分析脚本
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def run_command(cmd: List[str], description: str) -> Dict[str, Any]:
    """执行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent,
            timeout=300  # 5分钟超时
        )
        
        execution_time = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "命令执行超时（5分钟）",
            "execution_time": 300
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "execution_time": time.time() - start_time
        }


def check_environment() -> Dict[str, Any]:
    """检查环境依赖"""
    print("\n🔍 检查Python环境...")
    
    env_info = {}
    
    # 检查Python版本
    python_result = run_command([sys.executable, "--version"], "Python版本检查")
    env_info["python_version"] = python_result["stdout"].strip() if python_result["success"] else "未知"
    
    # 检查pip
    pip_result = run_command([sys.executable, "-m", "pip", "--version"], "pip版本检查")
    env_info["pip_version"] = pip_result["stdout"].strip() if pip_result["success"] else "未知"
    
    # 检查关键依赖
    dependencies = ["pytest", "ruff", "mypy", "pandas", "numpy"]
    env_info["dependencies"] = {}
    
    for dep in dependencies:
        result = run_command([sys.executable, "-m", "pip", "show", dep], f"检查{dep}")
        env_info["dependencies"][dep] = result["success"]
    
    return env_info


def install_dependencies() -> bool:
    """安装项目依赖"""
    print("\n📦 安装项目依赖...")
    
    # 检查是否已安装
    result = run_command([sys.executable, "-m", "pip", "show", "quant-trading-system"], "检查项目安装")
    
    if not result["success"]:
        # 安装项目
        install_result = run_command([sys.executable, "-m", "pip", "install", "-e", "."], "安装项目")
        if not install_result["success"]:
            print("❌ 项目安装失败")
            print(install_result["stderr"])
            return False
    
    # 安装开发依赖
    dev_result = run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], "安装开发依赖")
    if not dev_result["success"]:
        print("⚠️ 开发依赖安装失败，但继续执行")
    
    return True


def run_code_quality_checks() -> Dict[str, Any]:
    """运行代码质量检查"""
    print("\n🔍 运行代码质量检查...")
    
    quality_results = {}
    
    # 1. Ruff代码检查
    ruff_result = run_command([sys.executable, "-m", "ruff", "check", "src/", "tests/"], "Ruff代码检查")
    quality_results["ruff"] = ruff_result
    
    # 2. MyPy类型检查
    mypy_result = run_command([sys.executable, "-m", "mypy", "src/", "--ignore-missing-imports"], "MyPy类型检查")
    quality_results["mypy"] = mypy_result
    
    # 3. 代码格式检查
    black_check = run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"], "Black格式检查")
    quality_results["black"] = black_check
    
    return quality_results


def run_tests() -> Dict[str, Any]:
    """运行测试套件"""
    print("\n🧪 运行测试套件...")
    
    test_results = {}
    
    # 1. 运行核心模块测试
    core_modules = [
        ("风险管理", "test_risk_manager.py"),
        ("交易引擎", "test_trading_engine.py"),
        ("策略引擎", "test_strategy_engine.py"),
        ("指标计算", "test_indicators.py"),
        ("AI交易", "test_ai_trader.py"),
        ("市场数据", "test_market_service.py")
    ]
    
    test_results["modules"] = {}
    
    for module_name, test_file in core_modules:
        print(f"\n📊 测试{module_name}...")
        result = run_command([
            sys.executable, "-m", "pytest", 
            f"tests/{test_file}",
            "-v", "--tb=short", "--disable-warnings"
        ], f"{module_name}测试")
        
        test_results["modules"][module_name] = result
    
    # 2. 运行完整测试套件
    print("\n📊 运行完整测试套件...")
    full_test_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/", "-v", "--tb=line", "--disable-warnings"
    ], "完整测试套件")
    
    test_results["full_suite"] = full_test_result
    
    # 3. 运行覆盖率测试
    print("\n📊 运行覆盖率测试...")
    coverage_result = run_command([
        sys.executable, "-m", "pytest",
        "tests/", "--cov=src/quant_trading_system",
        "--cov-report=term-missing", "--cov-report=html",
        "--cov-report=json:coverage.json",
        "--disable-warnings"
    ], "覆盖率测试")
    
    test_results["coverage"] = coverage_result
    
    return test_results


def analyze_test_coverage() -> Dict[str, Any]:
    """分析测试覆盖率"""
    coverage_file = Path(__file__).parent / "coverage.json"
    
    if not coverage_file.exists():
        return {"error": "覆盖率文件不存在"}
    
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)
    
    totals = coverage_data.get("totals", {})
    
    return {
        "percent_covered": totals.get("percent_covered", 0),
        "covered_lines": totals.get("covered_lines", 0),
        "missing_lines": totals.get("missing_lines", 0),
        "excluded_lines": totals.get("excluded_lines", 0),
        "num_statements": totals.get("num_statements", 0)
    }


def analyze_file_structure() -> Dict[str, Any]:
    """分析文件结构"""
    print("\n📁 分析文件结构...")
    
    src_dir = Path(__file__).parent / "src" / "quant_trading_system"
    tests_dir = Path(__file__).parent / "tests"
    
    analysis = {
        "source_files": {},
        "test_files": {},
        "summary": {}
    }
    
    # 统计源代码文件
    source_files = list(src_dir.rglob("*.py"))
    analysis["summary"]["source_files_count"] = len(source_files)
    
    for file_path in source_files:
        if "__pycache__" not in str(file_path):
            relative_path = file_path.relative_to(src_dir.parent.parent)
            analysis["source_files"][str(relative_path)] = {
                "size": file_path.stat().st_size,
                "lines": len(file_path.read_text().split('\n'))
            }
    
    # 统计测试文件
    test_files = list(tests_dir.glob("test_*.py"))
    analysis["summary"]["test_files_count"] = len(test_files)
    
    for file_path in test_files:
        analysis["test_files"][file_path.name] = {
            "size": file_path.stat().st_size,
            "lines": len(file_path.read_text().split('\n'))
        }
    
    return analysis


def generate_report(
    env_info: Dict[str, Any],
    quality_results: Dict[str, Any],
    test_results: Dict[str, Any],
    coverage_analysis: Dict[str, Any],
    file_analysis: Dict[str, Any]
) -> str:
    """生成测试报告"""
    
    report = []
    report.append("=" * 80)
    report.append("📊 量化交易系统 - 综合测试分析报告")
    report.append("=" * 80)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 1. 环境信息
    report.append("## 1. 环境信息")
    report.append(f"- Python版本: {env_info.get('python_version', '未知')}")
    report.append(f"- pip版本: {env_info.get('pip_version', '未知')}")
    
    deps_status = []
    for dep, available in env_info.get("dependencies", {}).items():
        status = "✅" if available else "❌"
        deps_status.append(f"{dep}: {status}")
    
    report.append(f"- 依赖状态: {', '.join(deps_status)}")
    report.append("")
    
    # 2. 代码质量检查结果
    report.append("## 2. 代码质量检查")
    
    for tool, result in quality_results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        report.append(f"- {tool.upper()}: {status}")
        if not result["success"] and result["stderr"]:
            report.append(f"  错误: {result['stderr'][:200]}...")
    report.append("")
    
    # 3. 测试结果
    report.append("## 3. 测试结果")
    
    # 模块测试结果
    module_results = test_results.get("modules", {})
    for module_name, result in module_results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        report.append(f"- {module_name}: {status} ({result['execution_time']:.2f}s)")
    
    # 完整测试套件结果
    full_result = test_results.get("full_suite", {})
    full_status = "✅ 通过" if full_result["success"] else "❌ 失败"
    report.append(f"- 完整测试套件: {full_status} ({full_result['execution_time']:.2f}s)")
    report.append("")
    
    # 4. 覆盖率分析
    report.append("## 4. 测试覆盖率")
    
    if "error" not in coverage_analysis:
        coverage = coverage_analysis.get("percent_covered", 0)
        report.append(f"- 总体覆盖率: {coverage:.2f}%")
        report.append(f"- 覆盖行数: {coverage_analysis.get('covered_lines', 0)}")
        report.append(f"- 未覆盖行数: {coverage_analysis.get('missing_lines', 0)}")
        report.append(f"- 总代码行数: {coverage_analysis.get('num_statements', 0)}")
        
        # 覆盖率评估
        if coverage >= 80:
            report.append("- 评估: ✅ 优秀（覆盖率 >= 80%）")
        elif coverage >= 70:
            report.append("- 评估: ⚠️ 良好（覆盖率 >= 70%）")
        elif coverage >= 60:
            report.append("- 评估: ⚠️ 一般（覆盖率 >= 60%）")
        else:
            report.append("- 评估: ❌ 不足（覆盖率 < 60%）")
    else:
        report.append("- 覆盖率数据不可用")
    report.append("")
    
    # 5. 文件结构分析
    report.append("## 5. 文件结构分析")
    report.append(f"- 源代码文件数: {file_analysis.get('summary', {}).get('source_files_count', 0)}")
    report.append(f"- 测试文件数: {file_analysis.get('summary', {}).get('test_files_count', 0)}")
    
    # 计算测试覆盖率比例
    source_count = file_analysis.get('summary', {}).get('source_files_count', 1)
    test_count = file_analysis.get('summary', {}).get('test_files_count', 0)
    test_ratio = (test_count / source_count) * 100 if source_count > 0 else 0
    
    report.append(f"- 测试文件覆盖率: {test_ratio:.1f}%")
    report.append("")
    
    # 6. 总体评估
    report.append("## 6. 总体评估")
    
    # 计算成功率
    quality_success = all(r["success"] for r in quality_results.values())
    module_success = all(r["success"] for r in module_results.values())
    full_suite_success = full_result.get("success", False)
    
    if quality_success and module_success and full_suite_success:
        report.append("✅ **所有检查通过** - 系统质量优秀")
        overall_status = "PASS"
    elif module_success and full_suite_success:
        report.append("⚠️ **测试通过但代码质量检查有警告** - 系统功能正常")
        overall_status = "WARNING"
    else:
        report.append("❌ **测试失败** - 需要修复问题")
        overall_status = "FAIL"
    
    report.append("")
    report.append("=" * 80)
    report.append(f"最终状态: {overall_status}")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """主函数"""
    print("🚀 开始量化交易系统综合测试分析...")
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 1. 检查环境
        env_info = check_environment()
        
        # 2. 安装依赖
        if not install_dependencies():
            print("❌ 依赖安装失败，退出测试")
            sys.exit(1)
        
        # 3. 代码质量检查
        quality_results = run_code_quality_checks()
        
        # 4. 运行测试
        test_results = run_tests()
        
        # 5. 分析覆盖率
        coverage_analysis = analyze_test_coverage()
        
        # 6. 分析文件结构
        file_analysis = analyze_file_structure()
        
        # 7. 生成报告
        report = generate_report(env_info, quality_results, test_results, coverage_analysis, file_analysis)
        
        # 8. 保存报告
        report_file = Path(__file__).parent / "test_analysis_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        # 9. 显示报告
        print("\n" + "=" * 80)
        print("📋 测试分析报告")
        print("=" * 80)
        print(report)
        
        # 10. 保存详细结果
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "execution_time": time.time() - start_time,
            "environment": env_info,
            "quality_checks": quality_results,
            "test_results": test_results,
            "coverage": coverage_analysis,
            "file_analysis": file_analysis
        }
        
        with open("detailed_test_results.json", "w") as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"\n📁 报告文件已保存:")
        print(f"   - 摘要报告: {report_file}")
        print(f"   - 详细结果: detailed_test_results.json")
        print(f"   - 覆盖率报告: htmlcov/index.html")
        
        print(f"\n⏱️ 总执行时间: {time.time() - start_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 测试执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()