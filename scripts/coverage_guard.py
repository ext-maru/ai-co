#!/usr/bin/env python3
"""
📊 テストカバレッジ監視騎士
指定されたカバレッジ閾値を守る
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict
from typing import Tuple

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CoverageGuard:
    """カバレッジ監視クラス"""

    def __init__(self, min_coverage: float = 80.0):
        self.min_coverage = min_coverage
        self.coverage_file = PROJECT_ROOT / ".coverage"
        self.report_file = PROJECT_ROOT / "coverage_report.json"

    def check_coverage(self) -> Tuple[bool, float, Dict]:
        """カバレッジをチェック"""
        print("📊 テストカバレッジチェック開始")
        print("=" * 50)
        print(f"最小カバレッジ要求: {self.min_coverage}%")

        # pytest-covを実行
        if not self._run_coverage():
            return False, 0.0, {}

        # カバレッジレポートを解析
        coverage_data = self._parse_coverage()

        if not coverage_data:
            print("❌ カバレッジデータを取得できませんでした")
            return False, 0.0, {}

        # 総合カバレッジを取得
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0.0)

        # 結果表示
        print(f"\n📊 総合カバレッジ: {total_coverage:.1f}%")

        # 各ファイルのカバレッジを表示（低い順）
        files_data = coverage_data.get("files", {})
        if files_data:
            print("\n📁 ファイル別カバレッジ（低い順）:")

            # カバレッジでソート
            sorted_files = sorted(
                files_data.items(),
                key=lambda x: x[1].get("summary", {}).get("percent_covered", 0),
            )

            # 下位10ファイルを表示
            for file_path, file_data in sorted_files[:10]:
                file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
                relative_path = Path(file_path).relative_to(PROJECT_ROOT)
                print(f"   {file_coverage:5.1f}% - {relative_path}")

        # 閾値チェック
        passed = total_coverage >= self.min_coverage

        if passed:
            print("\n✅ カバレッジ基準を満たしています")
        else:
            print("\n❌ カバレッジ基準を下回っています")
            print(f"   必要: {self.min_coverage}%, 実際: {total_coverage:.1f}%")

        return passed, total_coverage, coverage_data

    def _run_coverage(self) -> bool:
        """pytest-covを実行"""
        print("\n🧪 テスト実行中...")

        try:
            # カバレッジ測定コマンド
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "--cov=.",
                "--cov-report=json",
                "--cov-report=term",
                "-q",
            ]

            # テスト実行
            result = subprocess.run(
                cmd, cwd=PROJECT_ROOT, capture_output=True, text=True
            )

            # 結果確認（テストが失敗してもカバレッジは測定される）
            if result.returncode not in [0, 1]:
                print(f"❌ テスト実行エラー: {result.stderr}")
                return False

            # カバレッジファイルの存在確認
            json_report = PROJECT_ROOT / "coverage.json"
            if not json_report.exists():
                print("❌ カバレッジレポートが生成されませんでした")
                return False

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ pytest実行エラー: {e}")
            return False
        except FileNotFoundError:
            print("❌ pytestがインストールされていません")
            print("   pip install pytest pytest-cov を実行してください")
            return False

    def _parse_coverage(self) -> Dict:
        """カバレッジレポートを解析"""
        json_report = PROJECT_ROOT / "coverage.json"

        try:
            with open(json_report, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ カバレッジレポート解析エラー: {e}")
            return {}

    def generate_badge(self, coverage: float):
        """カバレッジバッジを生成（オプション）"""
        # バッジの色を決定
        if coverage >= 90:
            color = "brightgreen"
        elif coverage >= 80:
            color = "green"
        elif coverage >= 70:
            color = "yellow"
        elif coverage >= 60:
            color = "orange"
        else:
            color = "red"

        # バッジデータ
        badge_data = {
            "schemaVersion": 1,
            "label": "coverage",
            "message": f"{coverage:.1f}%",
            "color": color,
        }

        badge_file = PROJECT_ROOT / "coverage_badge.json"
        with open(badge_file, "w") as f:
            json.dump(badge_data, f, indent=2)

        print(f"\n🏷️ カバレッジバッジ生成: {badge_file}")

    def suggest_improvements(self, coverage_data: Dict):
        """カバレッジ改善の提案"""
        print("\n💡 カバレッジ改善の提案:")

        files_data = coverage_data.get("files", {})
        low_coverage_files = []

        # カバレッジが低いファイルを抽出
        for file_path, file_data in files_data.items():
            file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
            if file_coverage < self.min_coverage:
                missing_lines = file_data.get("missing_lines", [])
                low_coverage_files.append(
                    {
                        "path": file_path,
                        "coverage": file_coverage,
                        "missing_lines": len(missing_lines),
                    }
                )

        # カバレッジが低い順にソート
        low_coverage_files.sort(key=lambda x: x["coverage"])

        # 上位5ファイルの提案
        for file_info in low_coverage_files[:5]:
            relative_path = Path(file_info["path"]).relative_to(PROJECT_ROOT)
            print(f"\n   📁 {relative_path}")
            print(f"      現在: {file_info['coverage']:.1f}%")
            print(f"      未テスト行数: {file_info['missing_lines']}")
            print(f"      提案: test_{relative_path.stem}.py を作成/更新")


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="📊 テストカバレッジ監視騎士")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="最小カバレッジ閾値（デフォルト: 80.0%）",
    )
    parser.add_argument(
        "--generate-badge", action="store_true", help="カバレッジバッジを生成"
    )
    parser.add_argument("--suggest", action="store_true", help="改善提案を表示")

    args = parser.parse_args()

    # カバレッジ監視を初期化
    guard = CoverageGuard(min_coverage=args.min_coverage)

    # カバレッジチェック実行
    passed, total_coverage, coverage_data = guard.check_coverage()

    # バッジ生成（オプション）
    if args.generate_badge:
        guard.generate_badge(total_coverage)

    # 改善提案（オプション）
    if args.suggest and coverage_data:
        guard.suggest_improvements(coverage_data)

    print("\n" + "=" * 50)

    # 終了コード
    if passed:
        print("✅ カバレッジチェック成功")
        sys.exit(0)
    else:
        print("❌ カバレッジチェック失敗")
        print(f"   テストを追加して{args.min_coverage}%以上を目指してください")
        sys.exit(1)


if __name__ == "__main__":
    main()
