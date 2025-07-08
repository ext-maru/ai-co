#!/usr/bin/env python3
"""
Performance Regression Checker
パフォーマンス回帰チェッカー
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List
import statistics


class PerformanceRegression:
    """パフォーマンス回帰分析"""
    
    def __init__(self, threshold_percent: float = 10.0):
        self.threshold = threshold_percent / 100.0  # Convert to decimal
    
    def load_benchmark_data(self, file_path: str) -> Dict[str, Any]:
        """ベンチマークデータを読み込み"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error loading benchmark data from {file_path}: {e}")
            return {}
    
    def extract_metrics(self, benchmark_data: Dict[str, Any]) -> Dict[str, float]:
        """ベンチマークデータからメトリクスを抽出"""
        metrics = {}
        
        if 'benchmarks' in benchmark_data:
            for benchmark in benchmark_data['benchmarks']:
                name = benchmark.get('name', 'unknown')
                # Mean time in seconds
                mean_time = benchmark.get('stats', {}).get('mean', 0)
                if mean_time > 0:
                    # Convert to operations per second
                    metrics[name] = 1.0 / mean_time
        
        return metrics
    
    def compare_performance(self, current: Dict[str, float], baseline: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """パフォーマンスを比較"""
        results = {}
        
        for test_name in current.keys():
            if test_name in baseline:
                current_perf = current[test_name]
                baseline_perf = baseline[test_name]
                
                # Calculate percentage change
                if baseline_perf > 0:
                    change_percent = ((current_perf - baseline_perf) / baseline_perf)
                    
                    results[test_name] = {
                        'current': current_perf,
                        'baseline': baseline_perf,
                        'change_percent': change_percent,
                        'is_regression': change_percent < -self.threshold,
                        'is_improvement': change_percent > self.threshold,
                        'status': self._get_status(change_percent)
                    }
        
        return results
    
    def _get_status(self, change_percent: float) -> str:
        """変化率からステータスを取得"""
        if change_percent < -self.threshold:
            return "🔴 REGRESSION"
        elif change_percent > self.threshold:
            return "🟢 IMPROVEMENT"
        else:
            return "🟡 STABLE"
    
    def generate_report(self, comparison_results: Dict[str, Dict[str, Any]]) -> str:
        """パフォーマンスレポートを生成"""
        if not comparison_results:
            return "⚠️ No performance data to compare"
        
        report_lines = [
            "# 📊 Performance Regression Analysis",
            "",
            f"**Threshold**: ±{self.threshold*100:.1f}%",
            ""
        ]
        
        # Summary statistics
        regressions = sum(1 for r in comparison_results.values() if r['is_regression'])
        improvements = sum(1 for r in comparison_results.values() if r['is_improvement'])
        stable = len(comparison_results) - regressions - improvements
        
        report_lines.extend([
            "## 📈 Summary",
            f"- **Regressions**: {regressions}",
            f"- **Improvements**: {improvements}",
            f"- **Stable**: {stable}",
            ""
        ])
        
        # Detailed results
        report_lines.append("## 📋 Detailed Results")
        report_lines.append("")
        
        for test_name, result in sorted(comparison_results.items()):
            status = result['status']
            change = result['change_percent'] * 100
            current = result['current']
            baseline = result['baseline']
            
            report_lines.append(
                f"### {test_name}\n"
                f"- **Status**: {status}\n"
                f"- **Change**: {change:+.1f}%\n"
                f"- **Current**: {current:.2f} ops/sec\n"
                f"- **Baseline**: {baseline:.2f} ops/sec\n"
            )
        
        return "\n".join(report_lines)
    
    def check_for_failures(self, comparison_results: Dict[str, Dict[str, Any]]) -> bool:
        """回帰があるかチェック"""
        return any(result['is_regression'] for result in comparison_results.values())


def main():
    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument("--current", required=True, help="Current benchmark results file")
    parser.add_argument("--baseline", help="Baseline benchmark results file")
    parser.add_argument("--threshold", type=float, default=10.0, help="Regression threshold percentage")
    parser.add_argument("--output", help="Output report file")
    
    args = parser.parse_args()
    
    # Default baseline path
    if not args.baseline:
        baseline_dir = Path("benchmark-baselines")
        baseline_dir.mkdir(exist_ok=True)
        args.baseline = baseline_dir / "baseline.json"
    
    checker = PerformanceRegression(args.threshold)
    
    # Load data
    current_data = checker.load_benchmark_data(args.current)
    baseline_data = checker.load_benchmark_data(args.baseline)
    
    if not current_data:
        print("❌ No current benchmark data found")
        sys.exit(1)
    
    if not baseline_data:
        print("⚠️ No baseline data found. Saving current data as baseline.")
        # Save current as baseline for future comparisons
        with open(args.baseline, 'w') as f:
            json.dump(current_data, f, indent=2)
        print(f"✅ Baseline saved to {args.baseline}")
        sys.exit(0)
    
    # Extract metrics
    current_metrics = checker.extract_metrics(current_data)
    baseline_metrics = checker.extract_metrics(baseline_data)
    
    if not current_metrics:
        print("❌ No performance metrics found in current data")
        sys.exit(1)
    
    # Compare performance
    results = checker.compare_performance(current_metrics, baseline_metrics)
    
    # Generate report
    report = checker.generate_report(results)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📊 Report saved to {args.output}")
    else:
        print(report)
    
    # Check for regressions
    has_regressions = checker.check_for_failures(results)
    
    if has_regressions:
        print("\n❌ Performance regressions detected!")
        
        # Print regression details
        regressions = {k: v for k, v in results.items() if v['is_regression']}
        for test_name, result in regressions.items():
            change = result['change_percent'] * 100
            print(f"  🔴 {test_name}: {change:.1f}% slower")
        
        sys.exit(1)
    else:
        print("\n✅ No significant performance regressions detected")
        
        # Print improvements if any
        improvements = {k: v for k, v in results.items() if v['is_improvement']}
        if improvements:
            print("\n🎉 Performance improvements detected:")
            for test_name, result in improvements.items():
                change = result['change_percent'] * 100
                print(f"  🟢 {test_name}: {change:.1f}% faster")
        
        sys.exit(0)


if __name__ == "__main__":
    main()