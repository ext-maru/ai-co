#!/usr/bin/env python3
"""
テストフレームワークパフォーマンス比較スクリプト
Issue #93: OSS移行プロジェクト
既存のIntegrationTestRunnerとpytestの性能比較

作成日: 2025年7月19日
"""
import json
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd


class TestPerformanceComparator:
    """テストパフォーマンス比較ツール"""

    def __init__(self):
        self.results = {"original": [], "pytest": []}
        self.report_dir = Path("test_reports")
        self.report_dir.mkdir(exist_ok=True)

    def run_original_tests(self, iterations: int = 5) -> Dict[str, Any]:
        """既存のテストフレームワーク実行"""
        print("🔧 既存のIntegrationTestRunner実行中...")
        durations = []

        for i in range(iterations):
            start_time = time.time()

            # 既存のテストを実行（簡易版）
            try:
                result = subprocess.run(
                    [
                        "python3",
                        "-m",
                        "pytest",
                        "tests/unit/test_integration_test_framework.py",
                        "-v",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                duration = time.time() - start_time
                durations.append(duration)
                print(f"  実行 {i+1}/{iterations}: {duration:0.2f}秒")
            except Exception as e:
                print(f"  エラー: {e}")
                continue

        return {
            "framework": "original",
            "durations": durations,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
        }

    def run_pytest_tests(self, iterations: int = 5) -> Dict[str, Any]:
        """pytest版テスト実行"""
        print("🚀 pytest版テスト実行中...")
        durations = []

        for i in range(iterations):
            start_time = time.time()

            try:
                result = subprocess.run(
                    [
                        "python3",
                        "-m",
                        "pytest",
                        "tests/poc/test_integration_pytest.py",
                        "-v",
                        "--tb=short",
                        "-n",
                        "auto",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                duration = time.time() - start_time
                durations.append(duration)
                print(f"  実行 {i+1}/{iterations}: {duration:0.2f}秒")
            except Exception as e:
                print(f"  エラー: {e}")
                continue

        return {
            "framework": "pytest",
            "durations": durations,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
        }

    def compare_code_metrics(self) -> Dict[str, Any]:
        """コード行数とコンプレキシティ比較"""
        metrics = {}

        # 既存コード
        original_file = Path("libs/integration_test_framework.py")
        if original_file.exists():
            with open(original_file) as f:
                original_lines = len(f.readlines())
            metrics["original"] = {
                "lines_of_code": original_lines,
                "file_size": original_file.stat().st_size,
            }

        # pytest版
        pytest_file = Path("tests/poc/test_integration_pytest.py")
        if pytest_file.exists():
            with open(pytest_file) as f:
                pytest_lines = len(f.readlines())
            metrics["pytest"] = {
                "lines_of_code": pytest_lines,
                "file_size": pytest_file.stat().st_size,
            }

        # 削減率計算
        if "original" in metrics and "pytest" in metrics:
            reduction = (
                1
                - metrics["pytest"]["lines_of_code"]
                / metrics["original"]["lines_of_code"]
            ) * 100
            metrics["code_reduction_percentage"] = reduction

        return metrics

    def generate_report(self, original_results: Dict, pytest_results: Dict) -> str:
        """比較レポート生成"""
        code_metrics = self.compare_code_metrics()

        report = f"""# 🚀 pytest移行パフォーマンス比較レポート
**Issue #93: OSS移行プロジェクト**
**生成日**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 📊 実行時間比較

| メトリクス | 既存フレームワーク | pytest | 改善率 |
|------------|-------------------|---------|--------|
| 平均実行時間 | {original_results['avg_duration']:0.2f}秒 | {pytest_results[ \
    'avg_duration']:0.2f}秒 | {((original_results['avg_duration'] - \
        pytest_results['avg_duration']) / original_results['avg_duration'] * 100):0.1f}% |
| 最小実行時間 | {original_results['min_duration']:0.2f}秒 | {pytest_results['min_duration']:0.2f}秒 | - |
| 最大実行時間 | {original_results['max_duration']:0.2f}秒 | {pytest_results['max_duration']:0.2f}秒 | - |
| 標準偏差 | {original_results['std_deviation']:0.2f} | {pytest_results['std_deviation']:0.2f} | - |

## 📈 コード削減

| メトリクス | 既存フレームワーク | pytest | 削減率 |
|------------|-------------------|---------|--------|
| コード行数 | {
    code_metrics.get('original',
    {}).get('lines_of_code',
    'N/A')} | {code_metrics.get('pytest',
    {}).get('lines_of_code',
    'N/A')} | {code_metrics.get('code_reduction_percentage',
    0):0.1f
}% |
| ファイルサイズ | {
    code_metrics.get('original',
    {}).get('file_size',
    0) / 1024:0.1f} KB | {code_metrics.get('pytest',
    {}).get('file_size',
    0) / 1024:0.1f
} KB | - |

## 🎯 pytest移行のメリット

1 **並列実行サポート**: pytest-xdistによる自動並列化
2 **豊富なフィクスチャ**: 再利用可能なテストセットアップ
3 **testcontainers統合**: Dockerコンテナの自動管理
4 **詳細なレポート**: HTML/XML形式の出力サポート
5 **プラグインエコシステム**: 豊富な拡張機能

## 🚧 移行時の考慮事項

1 **学習コスト**: pytestの概念とベストプラクティス習得
2 **依存関係**: 追加パッケージのインストール必要
3 **設定移行**: 既存の設定をpytest.iniへ移行

## 📝 推奨事項

- 段階的移行: 新規テストからpytest採用
- CI/CD統合: pytest-xdistで並列実行を活用
- カバレッジ向上: pytest-covでカバレッジ測定を強化
"""

        # レポート保存
        report_path = self.report_dir / "pytest_migration_comparison.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # グラフ生成
        self._generate_charts(original_results, pytest_results)

        return report

    def _generate_charts(self, original_results: Dict, pytest_results: Dict):
        """比較チャート生成"""
        # 実行時間比較グラフ
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 平均実行時間の棒グラフ
        frameworks = ["既存", "pytest"]
        durations = [original_results["avg_duration"], pytest_results["avg_duration"]]
        colors = ["#3498db", "#2ecc71"]

        ax1.bar(frameworks, durations, color=colors)
        ax1.set_ylabel("実行時間（秒）")
        ax1.set_title("平均実行時間比較")
        ax1.grid(axis="y", alpha=0.3)

        # 実行時間の分布
        ax2.boxplot(
            [original_results["durations"], pytest_results["durations"]],
            labels=frameworks,
        )
        ax2.set_ylabel("実行時間（秒）")
        ax2.set_title("実行時間分布")
        ax2.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.report_dir / "performance_comparison.png", dpi=300)
        plt.close()


def main():
    """メイン実行関数"""
    comparator = TestPerformanceComparator()

    print("🔍 テストパフォーマンス比較を開始します...")

    # 既存テスト実行
    original_results = comparator.run_original_tests(iterations=3)

    # pytest版実行
    pytest_results = comparator.run_pytest_tests(iterations=3)

    # レポート生成
    report = comparator.generate_report(original_results, pytest_results)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    print(f"\n✅ レポート保存先: test_reports/pytest_migration_comparison.md")
    print(f"📊 グラフ保存先: test_reports/performance_comparison.png")


if __name__ == "__main__":
    main()
