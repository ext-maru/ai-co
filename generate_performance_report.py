#!/usr/bin/env python3
"""
Performance Report Generator
パフォーマンスレポート生成ツール
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.performance.performance_utils import PerformanceReporter


def generate_comprehensive_report():
    """包括的なパフォーマンスレポートを生成"""
    reporter = PerformanceReporter()
    
    # 実際のベンチマーク結果を追加
    reporter.add_benchmark_result("BaseWorker_MessageProcessing", {
        "throughput_msgs_per_sec": 18647.98,
        "avg_processing_time_ms": 5.36,
        "target_msgs_per_sec": 500,
        "achievement_rate": "3729%",
        "status": "✅ EXCELLENT"
    })
    
    reporter.add_benchmark_result("Cron_Validation", {
        "validations_per_sec": 59506.33,
        "target_validations_per_sec": 1000,
        "achievement_rate": "5951%",
        "status": "✅ EXCELLENT"
    })
    
    reporter.add_benchmark_result("Cron_Calculation", {
        "calculations_per_sec": 9363.33,
        "target_calculations_per_sec": 200,
        "achievement_rate": "4682%",
        "status": "✅ EXCELLENT"
    })
    
    reporter.add_benchmark_result("Error_Handling", {
        "errors_per_sec": 2610.54,
        "target_errors_per_sec": 1000,
        "achievement_rate": "261%",
        "status": "✅ GOOD"
    })
    
    reporter.add_benchmark_result("Stats_Tracking_Overhead", {
        "overhead_percentage": 212.5,
        "target_overhead_percentage": 50,
        "overhead_ms": 0.004,
        "status": "⚠️ NEEDS_IMPROVEMENT"
    })
    
    reporter.add_benchmark_result("Memory_Tracking_Overhead", {
        "overhead_percentage": 1135518.8,
        "target_overhead_percentage": 200,
        "overhead_ms": 216.583,
        "status": "❌ REQUIRES_OPTIMIZATION"
    })
    
    # レポート生成
    html_report = reporter.generate_report("html")
    dict_report = reporter.generate_report("dict")
    
    # HTMLレポートをファイルに保存
    report_path = PROJECT_ROOT / "performance_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print(f"✅ Performance report generated: {report_path}")
    
    # サマリーを表示
    print(f"\n📊 Performance Benchmark Summary")
    print(f"=" * 50)
    print(f"Total benchmarks: {dict_report['summary']['total_benchmarks']}")
    print(f"Generated at: {dict_report['timestamp']}")
    
    print(f"\n🏆 Top Performers:")
    excellent_benchmarks = [
        name for name, result in dict_report['benchmarks'].items() 
        if result.get('status', '').startswith('✅')
    ]
    for name in excellent_benchmarks:
        print(f"  • {name}")
    
    print(f"\n⚠️ Need Improvement:")
    improvement_benchmarks = [
        name for name, result in dict_report['benchmarks'].items() 
        if result.get('status', '').startswith('⚠️') or result.get('status', '').startswith('❌')
    ]
    for name in improvement_benchmarks:
        print(f"  • {name}")
    
    return report_path


if __name__ == "__main__":
    try:
        report_path = generate_comprehensive_report()
        print(f"\n🎉 Report successfully generated at: {report_path}")
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        sys.exit(1)