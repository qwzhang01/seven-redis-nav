#!/bin/bash

# 量化交易系统 - 测试启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║           🚀 量化交易系统 - 测试套件启动器                 ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE} 项目路径: $PROJECT_ROOT${NC}"
echo -e "${BLUE} 生成时间: $(date)${NC}"
echo ""

# 函数定义
print_section() {
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_environment() {
    print_section "1. 检查环境"
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_success "找到 Python3: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        print_success "找到 Python: $(python --version)"
    else
        print_error "未找到Python，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查pip
    if $PYTHON_CMD -m pip --version &> /dev/null; then
        print_success "pip 可用"
    else
        print_error "pip 不可用，请先安装pip"
        exit 1
    fi
    
    # 检查项目目录
    if [ ! -f "pyproject.toml" ]; then
        print_error "未找到pyproject.toml，请确保在项目根目录运行此脚本"
        exit 1
    fi
}

install_dependencies() {
    print_section "2. 安装依赖"
    
    echo "检查并安装项目依赖..."
    
    # 检查是否已安装
    if $PYTHON_CMD -m pip show quant-trading-system &> /dev/null; then
        print_success "项目已安装"
    else
        echo "安装项目..."
        if $PYTHON_CMD -m pip install -e .; then
            print_success "项目安装成功"
        else
            print_error "项目安装失败"
            exit 1
        fi
    fi
    
    # 安装开发依赖
    echo "安装开发依赖..."
    if $PYTHON_CMD -m pip install -e .[dev]; then
        print_success "开发依赖安装成功"
    else
        print_warning "开发依赖安装失败，但继续执行"
    fi
}

run_quick_test() {
    print_section "3. 快速测试（核心功能）"
    
    echo "运行核心模块测试..."
    
    # 定义核心测试文件
    core_tests=(
        "test_risk_manager.py"
        "test_trading_engine.py"
        "test_strategy_engine.py"
        "test_indicators.py"
    )
    
    passed_count=0
    failed_count=0
    
    for test_file in "${core_tests[@]}"; do
        echo -e "\n${BLUE}测试: $test_file${NC}"
        
        if $PYTHON_CMD -m pytest "tests/$test_file" -v --tb=short --disable-warnings; then
            print_success "$test_file 通过"
            ((passed_count++))
        else
            print_error "$test_file 失败"
            ((failed_count++))
        fi
    done
    
    echo -e "\n${BLUE}快速测试结果:${NC}"
    echo -e "${GREEN}通过: $passed_count${NC}"
    echo -e "${RED}失败: $failed_count${NC}"
    
    if [ $failed_count -eq 0 ]; then
        print_success "所有核心测试通过！"
        return 0
    else
        print_warning "有测试失败，建议运行完整测试套件"
        return 1
    fi
}

run_full_test() {
    print_section "4. 完整测试套件"
    
    echo "运行完整测试套件..."
    
    if $PYTHON_CMD -m pytest tests/ -v --tb=line --disable-warnings; then
        print_success "完整测试套件通过！"
        return 0
    else
        print_error "完整测试套件有失败"
        return 1
    fi
}

run_coverage_test() {
    print_section "5. 覆盖率测试"
    
    echo "运行覆盖率测试..."
    
    if $PYTHON_CMD -m pytest tests/ --cov=src/quant_trading_system --cov-report=term-missing --cov-report=html --disable-warnings; then
        print_success "覆盖率测试完成"
        
        # 获取覆盖率
        COVERAGE=$($PYTHON_CMD -m pytest tests/ --cov=src/quant_trading_system --cov-report=term-missing --quiet | grep "TOTAL" | awk '{print $4}')
        echo -e "${BLUE}测试覆盖率: $COVERAGE${NC}"
        
        if [[ $COVERAGE =~ ^[0-9]+([.][0-9]+)?$ ]] && (( $(echo "$COVERAGE >= 80" | bc -l) )); then
            print_success "覆盖率达标（>=80%）"
        else
            print_warning "覆盖率未达标（<80%）"
        fi
        
        return 0
    else
        print_error "覆盖率测试失败"
        return 1
    fi
}

run_code_quality() {
    print_section "6. 代码质量检查"
    
    echo "运行代码质量检查..."
    
    # Ruff检查
    echo -e "\n${BLUE}Ruff检查...${NC}"
    if $PYTHON_CMD -m ruff check src/ tests/; then
        print_success "Ruff检查通过"
    else
        print_warning "Ruff检查有警告"
    fi
    
    # MyPy类型检查
    echo -e "\n${BLUE}MyPy类型检查...${NC}"
    if $PYTHON_CMD -m mypy src/ --ignore-missing-imports; then
        print_success "MyPy检查通过"
    else
        print_warning "MyPy检查有警告"
    fi
    
    return 0
}

run_comprehensive_analysis() {
    print_section "7. 综合测试分析"
    
    echo "运行综合测试分析..."
    
    if [ -f "run_comprehensive_tests.py" ]; then
        if $PYTHON_CMD run_comprehensive_tests.py; then
            print_success "综合测试分析完成"
        else
            print_error "综合测试分析失败"
        fi
    else
        print_warning "综合测试分析脚本不存在，跳过此步骤"
    fi
}

fix_test_issues() {
    print_section "8. 自动修复测试问题"
    
    echo "尝试自动修复测试问题..."
    
    if [ -f "fix_test_failures.py" ]; then
        if $PYTHON_CMD fix_test_failures.py; then
            print_success "自动修复完成"
        else
            print_error "自动修复失败"
        fi
    else
        print_warning "自动修复脚本不存在，跳过此步骤"
    fi
}

generate_report() {
    print_section "9. 生成测试报告"
    
    echo "生成测试报告..."
    
    REPORT_FILE="test_execution_report.md"
    
    cat > "$REPORT_FILE" << EOF
# 量化交易系统测试执行报告

## 基本信息
- 项目路径: $PROJECT_ROOT
- 执行时间: $(date)
- Python版本: $($PYTHON_CMD --version)

## 测试结果
EOF
    
    # 添加测试结果到报告
    echo "报告已生成: $REPORT_FILE"
    print_success "测试报告生成完成"
}

show_menu() {
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                    🎯 测试选项菜单                        ${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1. 快速测试（核心功能）${NC}"
    echo -e "${GREEN}2. 完整测试套件${NC}"
    echo -e "${GREEN}3. 覆盖率测试${NC}"
    echo -e "${GREEN}4. 代码质量检查${NC}"
    echo -e "${GREEN}5. 综合测试分析${NC}"
    echo -e "${GREEN}6. 自动修复测试问题${NC}"
    echo -e "${GREEN}7. 完整流程（全部执行）${NC}"
    echo -e "${RED}0. 退出${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════════${NC}"
}

main() {
    # 检查命令行参数
    if [ $# -eq 1 ]; then
        case $1 in
            "quick")
                check_environment
                install_dependencies
                run_quick_test
                ;;
            "full")
                check_environment
                install_dependencies
                run_full_test
                ;;
            "coverage")
                check_environment
                install_dependencies
                run_coverage_test
                ;;
            "quality")
                check_environment
                run_code_quality
                ;;
            "fix")
                check_environment
                fix_test_issues
                ;;
            "all")
                check_environment
                install_dependencies
                run_quick_test
                run_full_test
                run_coverage_test
                run_code_quality
                run_comprehensive_analysis
                generate_report
                ;;
            *)
                echo "用法: $0 [quick|full|coverage|quality|fix|all]"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # 交互式菜单
    while true; do
        show_menu
        read -p "请选择操作 (0-7): " choice
        
        case $choice in
            1)
                check_environment
                install_dependencies
                run_quick_test
                ;;
            2)
                check_environment
                install_dependencies
                run_full_test
                ;;
            3)
                check_environment
                install_dependencies
                run_coverage_test
                ;;
            4)
                check_environment
                run_code_quality
                ;;
            5)
                check_environment
                run_comprehensive_analysis
                ;;
            6)
                check_environment
                fix_test_issues
                ;;
            7)
                check_environment
                install_dependencies
                run_quick_test
                run_full_test
                run_coverage_test
                run_code_quality
                run_comprehensive_analysis
                generate_report
                ;;
            0)
                echo "退出测试套件"
                exit 0
                ;;
            *)
                echo "无效选择，请重新输入"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi