#!/usr/bin/env python3
"""
量化交易系统 - 测试失败自动修复脚本

这个脚本可以诊断和修复常见的测试失败问题，包括：
- 导入错误
- 依赖缺失
- 配置问题
- 数据文件缺失
- 异步测试问题
"""

import subprocess
import sys
import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional


class TestFixer:
    """测试修复器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixes_applied = []
        self.errors_found = []
    
    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """执行命令"""
        print(f"\n🔧 {description}")
        print(f"命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.project_root,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def diagnose_import_errors(self, error_output: str) -> List[str]:
        """诊断导入错误"""
        errors = []
        
        # 检查常见的导入错误模式
        patterns = [
            (r"ModuleNotFoundError: No module named '([^']+)'", "缺少模块依赖"),
            (r"ImportError: cannot import name '([^']+)'", "导入名称错误"),
            (r"ImportError: attempted relative import beyond top-level package", "相对导入错误"),
            (r"AttributeError: module '([^']+)' has no attribute '([^']+)'", "模块属性错误")
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, error_output)
            if matches:
                errors.append(f"{description}: {matches[0]}")
        
        return errors
    
    def diagnose_dependency_issues(self, error_output: str) -> List[str]:
        """诊断依赖问题"""
        errors = []
        
        # 检查依赖相关错误
        patterns = [
            (r"pkg_resources.DistributionNotFound: The '([^']+)' distribution was not found", "缺少包依赖"),
            (r"VersionConflict: \(([^)]+)\)", "版本冲突"),
            (r"No module named '([^']+)'", "缺少Python模块"),
            (r"DLL load failed", "Windows DLL加载失败"),
            (r"library not found for", "库文件未找到")
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, error_output)
            if matches:
                errors.append(f"{description}: {matches[0]}")
        
        return errors
    
    def diagnose_configuration_issues(self, error_output: str) -> List[str]:
        """诊断配置问题"""
        errors = []
        
        patterns = [
            (r"FileNotFoundError: \[Errno 2\] No such file or directory: '([^']+)'", "配置文件缺失"),
            (r"KeyError: '([^']+)'", "配置键缺失"),
            (r"Environment variable '([^']+)' not set", "环境变量未设置"),
            (r"Invalid configuration", "配置无效"),
            (r"Missing required configuration", "缺少必要配置")
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, error_output)
            if matches:
                errors.append(f"{description}: {matches[0]}")
        
        return errors
    
    def diagnose_data_issues(self, error_output: str) -> List[str]:
        """诊断数据问题"""
        errors = []
        
        patterns = [
            (r"FileNotFoundError.*\.(csv|json|parquet|feather)", "数据文件缺失"),
            (r"No such file or directory.*data", "数据目录缺失"),
            (r"Invalid data format", "数据格式错误"),
            (r"Data file corrupted", "数据文件损坏"),
            (r"Unable to read data", "数据读取失败")
        ]
        
        for pattern, description in patterns:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(description)
        
        return errors
    
    def diagnose_async_issues(self, error_output: str) -> List[str]:
        """诊断异步问题"""
        errors = []
        
        patterns = [
            (r"RuntimeError: Event loop is closed", "事件循环关闭错误"),
            (r"asyncio.*timeout", "异步超时"),
            (r"coroutine.*was never awaited", "协程未等待"),
            (r"async.*not properly awaited", "异步函数未正确等待"),
            (r"pytest-asyncio.*error", "pytest-asyncio错误")
        ]
        
        for pattern, description in patterns:
            if re.search(pattern, error_output, re.IGNORECASE):
                errors.append(description)
        
        return errors
    
    def fix_missing_dependencies(self, missing_modules: List[str]) -> bool:
        """修复缺失依赖"""
        print("\n📦 修复缺失依赖...")
        
        # 映射模块名到包名
        module_to_package = {
            "pytest": "pytest",
            "pytest_asyncio": "pytest-asyncio",
            "ruff": "ruff",
            "mypy": "mypy",
            "pandas": "pandas",
            "numpy": "numpy",
            "aiohttp": "aiohttp",
            "asyncio": "python-asyncio",
            "sqlalchemy": "sqlalchemy",
            "fastapi": "fastapi",
            "pydantic": "pydantic",
            "ta": "ta-lib",
            "binance": "python-binance",
            "websockets": "websockets"
        }
        
        packages_to_install = []
        for module in missing_modules:
            package = module_to_package.get(module, module)
            if package not in packages_to_install:
                packages_to_install.append(package)
        
        if packages_to_install:
            print(f"安装包: {', '.join(packages_to_install)}")
            
            # 安装包
            result = self.run_command(
                [sys.executable, "-m", "pip", "install"] + packages_to_install,
                "安装缺失依赖"
            )
            
            if result["success"]:
                self.fixes_applied.append(f"安装依赖: {', '.join(packages_to_install)}")
                return True
            else:
                self.errors_found.append(f"依赖安装失败: {result['stderr']}")
                return False
        
        return True
    
    def fix_project_installation(self) -> bool:
        """修复项目安装问题"""
        print("\n🔧 修复项目安装...")
        
        # 检查是否已安装
        result = self.run_command(
            [sys.executable, "-m", "pip", "show", "quant-trading-system"],
            "检查项目安装状态"
        )
        
        if not result["success"]:
            # 安装项目
            install_result = self.run_command(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                "安装项目"
            )
            
            if install_result["success"]:
                self.fixes_applied.append("项目安装成功")
                return True
            else:
                self.errors_found.append("项目安装失败")
                return False
        
        return True
    
    def fix_configuration_files(self) -> bool:
        """修复配置文件"""
        print("\n⚙️ 修复配置文件...")
        
        config_files = [
            ".env.example",
            "pyproject.toml",
            "src/quant_trading_system/core/config.py"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if not file_path.exists():
                print(f"⚠️ 配置文件缺失: {config_file}")
                
                # 尝试从模板创建
                if config_file == ".env.example":
                    self.create_env_example()
                
        return True
    
    def create_env_example(self) -> bool:
        """创建.env.example文件"""
        env_content = """# 量化交易系统环境配置

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/quant_trading
REDIS_URL=redis://localhost:6379/0

# 交易所API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# 交易配置
TRADING_ENABLED=false
RISK_ENABLED=true
MAX_POSITION_SIZE=100000
MAX_LEVERAGE=10

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/quant_trading.log

# 监控配置
PROMETHEUS_PORT=9090
METRICS_ENABLED=true

# AI配置
AI_MODEL_PATH=models/ai_trader.pkl
TRAINING_ENABLED=false
"""
        
        env_file = self.project_root / ".env.example"
        try:
            env_file.parent.mkdir(parents=True, exist_ok=True)
            env_file.write_text(env_content)
            self.fixes_applied.append("创建.env.example文件")
            return True
        except Exception as e:
            self.errors_found.append(f"创建.env.example失败: {e}")
            return False
    
    def fix_test_data_files(self) -> bool:
        """修复测试数据文件"""
        print("\n📊 修复测试数据文件...")
        
        # 检查测试数据目录
        test_data_dir = self.project_root / "tests" / "data"
        if not test_data_dir.exists():
            try:
                test_data_dir.mkdir(parents=True, exist_ok=True)
                self.fixes_applied.append("创建测试数据目录")
            except Exception as e:
                self.errors_found.append(f"创建测试数据目录失败: {e}")
        
        # 创建简单的测试数据文件
        mock_data_file = test_data_dir / "mock_prices.csv"
        if not mock_data_file.exists():
            try:
                mock_content = """timestamp,symbol,open,high,low,close,volume
1700000000000,BTC/USDT,50000.0,51000.0,49000.0,50500.0,1000.0
1700003600000,BTC/USDT,50500.0,51500.0,49500.0,51000.0,1200.0
1700007200000,BTC/USDT,51000.0,52000.0,50000.0,51500.0,1500.0
1700010800000,BTC/USDT,51500.0,52500.0,50500.0,52000.0,1800.0
1700014400000,BTC/USDT,52000.0,53000.0,51000.0,52500.0,2000.0
"""
                mock_data_file.write_text(mock_content)
                self.fixes_applied.append("创建模拟价格数据文件")
            except Exception as e:
                self.errors_found.append(f"创建测试数据文件失败: {e}")
        
        return True
    
    def fix_async_test_issues(self) -> bool:
        """修复异步测试问题"""
        print("\n⚡ 修复异步测试问题...")
        
        # 检查pytest-asyncio安装
        result = self.run_command(
            [sys.executable, "-m", "pip", "show", "pytest-asyncio"],
            "检查pytest-asyncio安装"
        )
        
        if not result["success"]:
            # 安装pytest-asyncio
            install_result = self.run_command(
                [sys.executable, "-m", "pip", "install", "pytest-asyncio"],
                "安装pytest-asyncio"
            )
            
            if install_result["success"]:
                self.fixes_applied.append("安装pytest-asyncio")
            else:
                self.errors_found.append("pytest-asyncio安装失败")
                return False
        
        # 检查conftest.py中的异步配置
        conftest_file = self.project_root / "tests" / "conftest.py"
        if conftest_file.exists():
            content = conftest_file.read_text()
            
            # 检查是否包含pytest-asyncio配置
            if "pytest_configure" not in content and "asyncio_mode" not in content:
                print("⚠️ conftest.py缺少异步配置，建议手动检查")
        
        return True
    
    def fix_python_path_issues(self) -> bool:
        """修复Python路径问题"""
        print("\n🐍 修复Python路径问题...")
        
        # 检查src目录是否在Python路径中
        src_dir = self.project_root / "src"
        
        # 在conftest.py中添加路径设置（如果不存在）
        conftest_file = self.project_root / "tests" / "conftest.py"
        if conftest_file.exists():
            content = conftest_file.read_text()
            
            path_setup_code = """
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
"""
            
            if "sys.path.insert" not in content:
                # 在文件开头添加路径设置
                new_content = path_setup_code + "\n" + content
                try:
                    conftest_file.write_text(new_content)
                    self.fixes_applied.append("在conftest.py中添加路径设置")
                except Exception as e:
                    self.errors_found.append(f"修改conftest.py失败: {e}")
        
        return True
    
    def run_test_and_diagnose(self) -> Dict[str, Any]:
        """运行测试并诊断问题"""
        print("\n🔍 运行测试诊断问题...")
        
        # 运行快速测试以诊断问题
        result = self.run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"],
            "运行诊断测试"
        )
        
        diagnosis = {
            "success": result["success"],
            "errors": [],
            "warnings": []
        }
        
        if not result["success"]:
            error_output = result["stderr"] + result["stdout"]
            
            # 诊断各种错误类型
            diagnosis["errors"].extend(self.diagnose_import_errors(error_output))
            diagnosis["errors"].extend(self.diagnose_dependency_issues(error_output))
            diagnosis["errors"].extend(self.diagnose_configuration_issues(error_output))
            diagnosis["errors"].extend(self.diagnose_data_issues(error_output))
            diagnosis["errors"].extend(self.diagnose_async_issues(error_output))
        
        return diagnosis
    
    def apply_fixes_based_on_diagnosis(self, diagnosis: Dict[str, Any]) -> bool:
        """根据诊断结果应用修复"""
        print("\n🔧 根据诊断结果应用修复...")
        
        errors = diagnosis.get("errors", [])
        
        # 提取缺失的模块
        missing_modules = []
        for error in errors:
            if "缺少模块依赖" in error:
                module_match = re.search(r"缺少模块依赖: (.+)", error)
                if module_match:
                    missing_modules.append(module_match.group(1))
        
        # 应用修复
        fixes_to_apply = []
        
        if missing_modules:
            fixes_to_apply.append("fix_missing_dependencies")
        
        if any("配置" in error for error in errors):
            fixes_to_apply.append("fix_configuration_files")
        
        if any("数据" in error for error in errors):
            fixes_to_apply.append("fix_test_data_files")
        
        if any("异步" in error for error in errors):
            fixes_to_apply.append("fix_async_test_issues")
        
        # 总是检查项目安装和Python路径
        fixes_to_apply.extend(["fix_project_installation", "fix_python_path_issues"])
        
        # 应用修复
        for fix_name in fixes_to_apply:
            fix_method = getattr(self, fix_name)
            if not fix_method():
                return False
        
        return True
    
    def run_comprehensive_test(self) -> bool:
        """运行综合测试验证修复效果"""
        print("\n🧪 运行综合测试验证修复效果...")
        
        # 运行核心模块测试
        core_tests = [
            "test_risk_manager.py",
            "test_trading_engine.py", 
            "test_strategy_engine.py",
            "test_indicators.py"
        ]
        
        all_passed = True
        
        for test_file in core_tests:
            result = self.run_command(
                [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v"],
                f"运行{test_file}"
            )
            
            if not result["success"]:
                all_passed = False
                print(f"❌ {test_file} 测试失败")
                print(result["stderr"])
            else:
                print(f"✅ {test_file} 测试通过")
        
        return all_passed
    
    def generate_report(self) -> str:
        """生成修复报告"""
        report = []
        report.append("=" * 80)
        report.append("🔧 量化交易系统测试修复报告")
        report.append("=" * 80)
        report.append(f"修复时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if self.fixes_applied:
            report.append("## ✅ 已应用的修复")
            for fix in self.fixes_applied:
                report.append(f"- {fix}")
        else:
            report.append("## ℹ️ 未发现需要修复的问题")
        
        report.append("")
        
        if self.errors_found:
            report.append("## ❌ 修复过程中发现的错误")
            for error in self.errors_found:
                report.append(f"- {error}")
        
        report.append("")
        report.append("## 📋 建议下一步操作")
        
        if self.errors_found:
            report.append("1. 手动检查上述错误并修复")
            report.append("2. 重新运行测试验证修复效果")
            report.append("3. 如果问题持续存在，请检查项目配置和环境")
        elif self.fixes_applied:
            report.append("1. 修复已应用，建议重新运行完整测试套件")
            report.append("2. 验证所有功能正常工作")
            report.append("3. 如果仍有问题，请检查具体的错误信息")
        else:
            report.append("1. 未发现明显问题，测试环境正常")
            report.append("2. 可以直接运行完整测试套件")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """主函数"""
    project_root = Path(__file__).parent
    
    print("🚀 开始量化交易系统测试修复...")
    print(f"项目根目录: {project_root}")
    
    fixer = TestFixer(project_root)
    
    try:
        # 1. 诊断问题
        diagnosis = fixer.run_test_and_diagnose()
        
        # 2. 应用修复
        if not diagnosis["success"]:
            print("\n⚠️ 发现测试问题，开始修复...")
            fixer.apply_fixes_based_on_diagnosis(diagnosis)
        else:
            print("\n✅ 测试运行正常，无需修复")
        
        # 3. 验证修复效果
        print("\n🔍 验证修复效果...")
        final_test_result = fixer.run_comprehensive_test()
        
        # 4. 生成报告
        report = fixer.generate_report()
        
        # 5. 保存报告
        report_file = project_root / "test_fix_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        # 6. 显示报告
        print("\n" + report)
        
        print(f"\n📁 修复报告已保存到: {report_file}")
        
        if final_test_result:
            print("\n🎉 修复完成！所有核心测试通过。")
        else:
            print("\n⚠️ 修复完成，但仍有测试失败，请查看详细报告。")
        
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()