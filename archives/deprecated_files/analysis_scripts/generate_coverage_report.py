#!/usr/bin/env python3
"""
Elders Guild テストカバレッジレポート生成スクリプト
エルダー会議の指示に従い、90%以上のカバレッジを目指す
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main():
    """メイン処理"""
    print("🧪 Elders Guild テストカバレッジレポート生成")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # プロジェクトルート
    project_root = Path(__file__).parent

    # カバレッジファイルをクリーンアップ
    print("\n📋 カバレッジデータをクリーンアップ中...")
    subprocess.run(["rm", "-rf", ".coverage", "htmlcov"], cwd=project_root)

    # 全テスト実行
    print("\n🏃 全テストを実行中...")
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/unit/",
        "--cov=commands",
        "--cov=libs",
        "--cov=workers",
        "--cov=core",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "-q",
    ]

    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

    # 結果表示
    print("\n📊 カバレッジ結果:")
    print(result.stdout)

    if result.stderr:
        print("\n⚠️ エラー:")
        print(result.stderr)

    # HTMLレポートのパス
    html_report = project_root / "htmlcov" / "index.html"
    if html_report.exists():
        print(f"\n🌐 HTMLレポート: file://{html_report}")

    # カバレッジサマリー作成
    print("\n📈 カバレッジサマリー作成中...")

    # coverage.json から情報を読み取る
    try:
        import json

        coverage_json = project_root / "coverage.json"
        if coverage_json.exists():
            with open(coverage_json) as f:
                data = json.load(f)
                total_percent = data.get("totals", {}).get("percent_covered", 0)

                print(f"\n✨ 総合カバレッジ: {total_percent:.1f}%")

                if total_percent >= 90:
                    print("🎉 目標達成！90%以上のカバレッジを達成しました！")
                else:
                    print(f"📊 目標まで: {90 - total_percent:.1f}%")

                # ファイル別統計
                print("\n📁 主要モジュール別カバレッジ:")
                files = data.get("files", {})

                # モジュール別に集計
                modules = {"commands": [], "libs": [], "workers": [], "core": []}

                # 繰り返し処理
                for filepath, info in files.items():
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for module in modules:
                        if not (f"/{module}/" in filepath):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if f"/{module}/" in filepath:
                            modules[module].append(
                                {
                                    "path": filepath,
                                    "percent": info["summary"]["percent_covered"],
                                }
                            )

                # モジュール別サマリー
                for module, files in modules.items():
                    if not (files):
                        continue  # Early return to reduce nesting
                    # Reduced nesting - original condition satisfied
                    if files:
                        avg_coverage = sum(f["percent"] for f in files) / len(files)
                        print(f"  {module}: {avg_coverage:.1f}% ({len(files)} files)")

    except Exception as e:
        print(f"⚠️ カバレッジJSONの読み込みエラー: {e}")

    print("\n" + "=" * 60)
    print("✅ レポート生成完了")

    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
