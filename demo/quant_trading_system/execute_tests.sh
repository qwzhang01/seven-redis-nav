#!/bin/bash

# 量化交易系统测试执行脚本

echo "=== 量化交易系统测试分析 ==="
echo ""

# 1. 检查Python环境
echo "1. 检查Python环境..."
python --version
pip --version
echo ""

# 2. 安装依赖（如果需要）
echo "2. 检查依赖..."
pip install -e .
echo ""

# 3. 执行pytest测试
echo "3. 执行pytest测试..."
python -m pytest tests/ -v --tb=short --disable-warnings
TEST_EXIT_CODE=$?
echo ""

# 4. 生成测试报告
echo "4. 生成测试报告..."
python -m pytest tests/ --tb=line -q --disable-warnings > test_summary.txt 2>&1
echo "测试摘要已保存到: test_summary.txt"
echo ""

# 5. 检查测试覆盖率
echo "5. 检查测试覆盖率..."
python -m pytest tests/ --cov=src/quant_trading_system --cov-report=term-missing --cov-report=html:htmlcov --disable-warnings
COVERAGE_EXIT_CODE=$?
echo ""

# 6. 代码质量检查
echo "6. 代码质量检查..."
python -m ruff check src/ tests/ --exit-zero
RUFF_EXIT_CODE=$?
echo ""

# 7. 类型检查
echo "7. 类型检查..."
python -m mypy src/ --ignore-missing-imports
MYPY_EXIT_CODE=$?
echo ""

# 8. 生成分析报告
echo "8. 生成分析报告..."
cat > analysis_report.md << 'EOF'
# 量化交易系统测试分析报告

## 测试执行结果
- 测试退出码: $TEST_EXIT_CODE
- 覆盖率检查退出码: $COVERAGE_EXIT_CODE
- 代码质量检查退出码: $RUFF_EXIT_CODE
- 类型检查退出码: $MYPY_EXIT_CODE

## 测试文件统计
EOF

# 统计测试文件
echo "## 测试文件统计" >> analysis_report.md
echo "" >> analysis_report.md
find tests/ -name "test_*.py" | wc -l | xargs echo "- 测试文件数量: " >> analysis_report.md
find src/quant_trading_system -name "*.py" | grep -v __pycache__ | wc -l | xargs echo "- 源代码文件数量: " >> analysis_report.md

# 显示测试文件列表
echo "" >> analysis_report.md
echo "## 测试文件列表" >> analysis_report.md
find tests/ -name "test_*.py" -exec basename {} \; | sort | while read file; do
    echo "- $file" >> analysis_report.md
done

echo "分析报告已保存到: analysis_report.md"
echo ""

# 9. 显示关键信息
echo "=== 关键信息 ==="
echo "测试退出码: $TEST_EXIT_CODE (0表示全部通过)"
echo "覆盖率检查: $COVERAGE_EXIT_CODE (0表示通过)"
echo "代码质量检查: $RUFF_EXIT_CODE (0表示通过)"
echo "类型检查: $MYPY_EXIT_CODE (0表示通过)"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 所有测试通过！"
else
    echo "❌ 有测试失败，请查看详细报告"
fi

echo ""
echo "=== 测试执行完成 ==="