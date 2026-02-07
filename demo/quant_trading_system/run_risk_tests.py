#!/usr/bin/env python3
"""
风险管理系统测试运行脚本
======================

运行所有风险管理系统相关的测试，并生成测试报告和性能分析。
"""

import os
import sys
import subprocess
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def run_tests(test_patterns, output_dir, verbose=False, performance=False):
    """运行指定的测试模式"""
    results = {}

    for pattern in test_patterns:
        print(f"\n{'='*60}")
        print(f"运行测试模式: {pattern}")
        print(f"{'='*60}")

        # 构建pytest命令
        cmd = [
            'python', '-m', 'pytest',
            '-v' if verbose else '-q',
            '--tb=short',
            '--html', os.path.join(output_dir, f'report_{pattern.replace("/", "_")}.html'),
            '--self-contained-html',
            '--json-report',
            '--json-report-file', os.path.join(output_dir, f'json_report_{pattern.replace("/", "_")}.json'),
        ]

        if performance:
            cmd.extend(['-m', 'performance', '--run-slow'])

        cmd.append(pattern)

        # 运行测试
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            end_time = time.time()

            results[pattern] = {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': end_time - start_time
            }

            print(f"退出码: {result.returncode}")
            print(f"耗时: {end_time - start_time:.2f}秒")

            if result.returncode == 0:
                print("✅ 测试通过")
            else:
                print("❌ 测试失败")
                if verbose:
                    print("标准输出:")
                    print(result.stdout)
                    print("错误输出:")
                    print(result.stderr)

        except Exception as e:
            print(f"❌ 运行测试时出错: {e}")
            results[pattern] = {
                'success': False,
                'error': str(e)
            }

    return results


def generate_summary_report(results, output_dir):
    """生成测试总结报告"""
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_patterns': len(results),
        'successful_patterns': sum(1 for r in results.values() if r.get('success', False)),
        'failed_patterns': sum(1 for r in results.values() if not r.get('success', True)),
        'total_duration': sum(r.get('duration', 0) for r in results.values()),
        'details': results
    }

    # 保存JSON报告
    report_file = os.path.join(output_dir, 'test_summary.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 生成文本报告
    text_report = os.path.join(output_dir, 'test_summary.txt')
    with open(text_report, 'w', encoding='utf-8') as f:
        f.write("风险管理系统测试总结报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"生成时间: {summary['timestamp']}\n")
        f.write(f"测试模式数量: {summary['total_patterns']}\n")
        f.write(f"成功模式: {summary['successful_patterns']}\n")
        f.write(f"失败模式: {summary['failed_patterns']}\n")
        f.write(f"总耗时: {summary['total_duration']:.2f}秒\n\n")

        f.write("详细结果:\n")
        for pattern, result in results.items():
            status = "✅ 通过" if result.get('success', False) else "❌ 失败"
            duration = result.get('duration', 0)
            f.write(f"  {pattern}: {status} ({duration:.2f}秒)\n")

    return summary


def run_coverage_analysis(output_dir):
    """运行代码覆盖率分析"""
    print("\n" + "="*60)
    print("运行代码覆盖率分析")
    print("="*60)

    coverage_dir = os.path.join(output_dir, 'coverage')
    os.makedirs(coverage_dir, exist_ok=True)

    cmd = [
        'python', '-m', 'pytest',
        'tests/test_risk_manager.py',
        'tests/test_risk_scenarios.py',
        'tests/test_risk_config.py',
        'tests/test_risk_performance.py',
        '--cov=quant_trading_system.services.risk',
        '--cov-report=html:' + os.path.join(coverage_dir, 'html'),
        '--cov-report=xml:' + os.path.join(coverage_dir, 'coverage.xml'),
        '--cov-report=term-missing',
        '-q'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))

        # 保存覆盖率报告
        coverage_report = os.path.join(coverage_dir, 'coverage_summary.txt')
        with open(coverage_report, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n错误输出:\n")
                f.write(result.stderr)

        print("覆盖率分析完成")
        print(f"报告保存在: {coverage_dir}")

    except Exception as e:
        print(f"覆盖率分析失败: {e}")


def run_performance_benchmark(output_dir):
    """运行性能基准测试"""
    print("\n" + "="*60)
    print("运行性能基准测试")
    print("="*60)

    performance_dir = os.path.join(output_dir, 'performance')
    os.makedirs(performance_dir, exist_ok=True)

    cmd = [
        'python', '-m', 'pytest',
        'tests/test_risk_performance.py',
        '-v',
        '--run-slow',
        '-m', 'performance'
    ]

    try:
        # 运行性能测试
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))

        # 保存性能测试输出
        performance_report = os.path.join(performance_dir, 'performance_results.txt')
        with open(performance_report, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n错误输出:\n")
                f.write(result.stderr)

        print("性能基准测试完成")
        print(f"报告保存在: {performance_dir}")

    except Exception as e:
        print(f"性能基准测试失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行风险管理系统测试')
    parser.add_argument('--output', '-o', default='test_reports',
                       help='测试报告输出目录')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出模式')
    parser.add_argument('--coverage', action='store_true',
                       help='运行代码覆盖率分析')
    parser.add_argument('--performance', action='store_true',
                       help='运行性能基准测试')
    parser.add_argument('--pattern', nargs='+',
                       default=[
                           'tests/test_risk_manager.py',
                           'tests/test_risk_scenarios.py',
                           'tests/test_risk_config.py',
                           'tests/test_risk_performance.py'
                       ],
                       help='要运行的测试模式')

    args = parser.parse_args()

    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print("风险管理系统测试运行器")
    print("=" * 60)
    print(f"输出目录: {output_dir.absolute()}")
    print(f"测试模式: {args.pattern}")
    print(f"时间: {datetime.now().isoformat()}")
    print("=" * 60)

    # 运行测试
    results = run_tests(args.pattern, output_dir, args.verbose, args.performance)

    # 生成总结报告
    summary = generate_summary_report(results, output_dir)

    # 运行覆盖率分析（如果指定）
    if args.coverage:
        run_coverage_analysis(output_dir)

    # 运行性能基准测试（如果指定）
    if args.performance:
        run_performance_benchmark(output_dir)

    # 最终总结
    print("\n" + "="*60)
    print("测试运行完成")
    print("="*60)
    print(f"总测试模式: {summary['total_patterns']}")
    print(f"成功模式: {summary['successful_patterns']}")
    print(f"失败模式: {summary['failed_patterns']}")
    print(f"总耗时: {summary['total_duration']:.2f}秒")
    print(f"报告目录: {output_dir.absolute()}")

    # 显示失败详情
    failed_patterns = [p for p, r in results.items() if not r.get('success', False)]
    if failed_patterns:
        print("\n失败的模式:")
        for pattern in failed_patterns:
            print(f"  - {pattern}")

    # 退出码
    exit_code = 0 if summary['failed_patterns'] == 0 else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
