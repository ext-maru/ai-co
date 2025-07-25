#!/usr/bin/env python3
"""
unittest to pytest移行パフォーマンス比較スクリプト
Issue #93: OSS移行プロジェクト
"""
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class TestMigrationComparator:
    """テスト移行比較ツール"""

    def __init__(self):
        self.results = {"unittest": [], "pytest": []}

    def run_unittest(self, test_file: str, iterations: int = 3) -> Dict[str, Any]:
        """unittestフレームワーク実行"""
        print(f"🔧 unittest実行中: {test_file}")
        durations = []
        test_counts = []

        for i in range(iterations):
            start_time = time.time()

            try:
                result = subprocess.run(
                    ["python3", "-m", "unittest", test_file, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                duration = time.time() - start_time
                durations.append(duration)

                # テスト数をカウント
                output_lines = result.stderr.split("\n")
                test_count = len(
                    [line for line in output_lines if line.strip().endswith("ok")]
                )
                test_counts.append(test_count)

                print(f"  実行 {i+1}/{iterations}: {duration:0.2f}秒, {test_count}テスト")
            except Exception as e:
                print(f"  エラー: {e}")
                continue

        return {
            "framework": "unittest",
            "test_file": test_file,
            "durations": durations,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "test_count": max(test_counts) if test_counts else 0,
            "success": len(durations) == iterations,
        }

    def run_pytest(self, test_file: str, iterations: int = 3) -> Dict[str, Any]:
        """pytestフレームワーク実行"""
        print(f"🚀 pytest実行中: {test_file}")
        durations = []
        test_counts = []

        for i in range(iterations):
            start_time = time.time()

            try:
                # pytest実行（カバレッジなし）
                result = subprocess.run(
                    ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={
                        **subprocess.os.environ,
                        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                    },
                )
                duration = time.time() - start_time
                durations.append(duration)

                # テスト数をカウント
                output_lines = result.stdout.split("\n")
                test_count = len([line for line in output_lines if " PASSED" in line])
                test_counts.append(test_count)

                print(f"  実行 {i+1}/{iterations}: {duration:0.2f}秒, {test_count}テスト")
            except Exception as e:
                print(f"  エラー: {e}")
                continue

        return {
            "framework": "pytest",
            "test_file": test_file,
            "durations": durations,
            "avg_duration": statistics.mean(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "test_count": max(test_counts) if test_counts else 0,
            "success": len(durations) == iterations,
        }

    def analyze_code_metrics(
        self, unittest_file: str, pytest_file: str
    ) -> Dict[str, Any]:
        """コードメトリクス分析"""
        metrics = {}

        # unittestファイル
        if Path(unittest_file).exists():
            with open(unittest_file) as f:
                unittest_lines = f.readlines()
            metrics["unittest"] = {
                "lines_of_code": len(unittest_lines),
                "test_methods": len(
                    [l for l in unittest_lines if l.strip().startswith("def test_")]
                ),
                "class_count": len(
                    [l for l in unittest_lines if l.strip().startswith("class Test")]
                ),
            }

        # pytestファイル
        if Path(pytest_file).exists():
            with open(pytest_file) as f:
                pytest_lines = f.readlines()
            metrics["pytest"] = {
                "lines_of_code": len(pytest_lines),
                "test_functions": len(
                    [l for l in pytest_lines if l.strip().startswith("def test_")]
                ),
                "fixture_count": len(
                    [l for l in pytest_lines if "@pytest.fixture" in l]
                ),
            }

        # 削減率計算
        if "unittest" in metrics and "pytest" in metrics:
            reduction = (
                1
                - metrics["pytest"]["lines_of_code"]
                / metrics["unittest"]["lines_of_code"]
            ) * 100
            metrics["code_reduction_percentage"] = reduction

        return metrics

    def generate_report(
        self, unittest_result: Dict, pytest_result: Dict, code_metrics: Dict
    ) -> str:
        """比較レポート生成"""
        report = f"""# 🔄 unittest → pytest 移行比較レポート
**Issue #93: OSS移行プロジェクト**
**生成日**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 📊 実行時間比較

| メトリクス | unittest | pytest | 改善率 |
|------------|----------|---------|--------|
| 平均実行時間 | {unittest_result['avg_duration']:0.3f}秒 | {pytest_result[ \
    'avg_duration']:0.3f}秒 | {((unittest_result['avg_duration'] - \
        pytest_result['avg_duration']) / unittest_result['avg_duration'] * 100):0.1f}% |
| 最小実行時間 | {unittest_result['min_duration']:0.3f}秒 | {pytest_result['min_duration']:0.3f}秒 | - |
| 最大実行時間 | {unittest_result['max_duration']:0.3f}秒 | {pytest_result['max_duration']:0.3f}秒 | - |
| テスト数 | {unittest_result['test_count']} | {pytest_result['test_count']} | - |

## 📈 コードメトリクス

| メトリクス | unittest | pytest | 削減率 |
|------------|----------|---------|--------|
| コード行数 | {
    code_metrics.get('unittest',
    {}).get('lines_of_code',
    'N/A')} | {code_metrics.get('pytest',
    {}).get('lines_of_code',
    'N/A')} | {code_metrics.get('code_reduction_percentage',
    0):0.1f
}% |
| テスト数 | {code_metrics.get('unittest', { \
    }).get('test_methods', 'N/A')} | {code_metrics.get('pytest', {}).get('test_functions', 'N/A')} | - |
| クラス/フィクスチャ | {code_metrics.get('unittest', { \
    }).get('class_count', 'N/A')} | {code_metrics.get('pytest', {}).get('fixture_count', 'N/A')} | - |

## 🎯 移行のメリット

1.0 **コード削減**: より簡潔で読みやすいテストコード
2.0 **フィクスチャ**: 再利用可能なセットアップコード
3.0 **パラメータ化**: 同じテストロジックの効率的な再利用
4.0 **より良いアサーション**: シンプルなassert文での詳細なエラー出力
5.0 **豊富なプラグイン**: 並列実行、カバレッジ、レポート生成など

## 📝 推奨事項

- 段階的移行: 新規テストからpytest採用
- 既存テストは動作確認後に移行
- CI/CD統合でpytest-xdistによる並列実行を活用
"""

        return report


def main():
    """メイン実行関数"""
    if len(sys.argv) < 3:
        print(
            "使用方法: python3 compare_unittest_to_pytest.py <unittest_file> <pytest_file>"
        )
        sys.exit(1)

    unittest_file = sys.argv[1]
    pytest_file = sys.argv[2]

    comparator = TestMigrationComparator()

    print("🔍 テスト移行比較を開始します...")

    # unittest実行
    unittest_result = comparator.run_unittest(unittest_file)

    # pytest実行
    pytest_result = comparator.run_pytest(pytest_file)

    # コードメトリクス分析
    code_metrics = comparator.analyze_code_metrics(unittest_file, pytest_file)

    # レポート生成
    report = comparator.generate_report(unittest_result, pytest_result, code_metrics)

    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # レポート保存
    report_path = Path("test_reports/migration_comparison.md")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ レポート保存先: {report_path}")


if __name__ == "__main__":
    main()
