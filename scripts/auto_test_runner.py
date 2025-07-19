#!/usr/bin/env python3
"""
Elders Guild 自動テストランナー
Git pre-commit hookから呼び出されるシンプルなテストランナー
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Elders Guild 自動テストランナー")
    parser.add_argument("files", nargs="*", help="テスト対象のファイル")
    parser.add_argument("--no-slack", action="store_true", help="Slack通知を無効化")
    args = parser.parse_args()

    # プロジェクトルート
    project_root = Path("/home/aicompany/ai_co")

    # 基本的なpytestコマンド
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit",
        "-v",
        "--tb=short",
        "--maxfail=5",
    ]

    # カバレッジオプションを追加
    if (project_root / "scripts" / "coverage-report.py").exists():
        cmd.extend(["--cov=.", "--cov-report=json", "--cov-report=term"])

    print(f"🧪 テストを実行中...")
    print(f"コマンド: {' '.join(cmd)}")

    # テスト実行
    result = subprocess.run(cmd, cwd=project_root)

    # カバレッジ情報を表示
    coverage_file = project_root / "coverage.json"
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)
            total_coverage = coverage_data["totals"]["percent_covered"]
            print(f"\n📊 総合カバレッジ: {total_coverage:.1f}%")

    # 結果を返す
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
