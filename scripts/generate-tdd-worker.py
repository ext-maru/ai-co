#!/usr/bin/env python3
"""
TDDワーカー生成スクリプト
新しいワーカーとそのテストをTDD方式で生成します
"""

import argparse
import re
import sys
from pathlib import Path


def to_snake_case(name):
    """CamelCaseをsnake_caseに変換"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_camel_case(name):
    """snake_caseをCamelCaseに変換"""
    return "".join(word.capitalize() for word in name.split("_"))


def generate_worker(worker_name, worker_type):
    """ワーカーとテストファイルを生成"""

    # 名前の正規化
    snake_name = to_snake_case(worker_name)
    camel_name = to_camel_case(worker_name)

    if not camel_name.endswith("Worker"):
        camel_name += "Worker"
        snake_name = to_snake_case(camel_name)

    # パス設定
    project_root = Path(__file__).parent.parent
    worker_file = project_root / "workers" / f"{snake_name}.py"
    test_file = project_root / "tests" / "unit" / f"test_{snake_name}.py"

    # テンプレート読み込み
    worker_template_file = project_root / "templates" / "tdd_worker_template.py"
    test_template_file = project_root / "templates" / "tdd_worker_test_template.py"

    with open(worker_template_file, "r") as f:
        worker_template = f.read()

    with open(test_template_file, "r") as f:
        test_template = f.read()

    # テンプレート変数の置換
    replacements = {
        "{WorkerName}": camel_name,
        "{worker_type}": worker_type,
        "{worker_module}": snake_name,
    }

    for old, new in replacements.items():
        worker_template = worker_template.replace(old, new)
        test_template = test_template.replace(old, new)

    # ファイル生成
    print(f"🎯 TDD: {camel_name}の開発を開始します")
    print("")

    # テストファイルを先に生成（TDD: Red）
    if test_file.exists():
        print(f"⚠️  テストファイルは既に存在します: {test_file}")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != "y":
            print("中止しました")
            return

    test_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, "w") as f:
        f.write(test_template)
    print(f"📝 テストファイルを作成しました: {test_file}")

    # ワーカーファイルを生成
    if worker_file.exists():
        print(f"⚠️  ワーカーファイルは既に存在します: {worker_file}")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != "y":
            print("中止しました")
            return

    worker_file.parent.mkdir(parents=True, exist_ok=True)
    with open(worker_file, "w") as f:
        f.write(worker_template)
    print(f"📝 ワーカーファイルを作成しました: {worker_file}")

    print("")
    print("🔴 Red: テストを実行して失敗することを確認")
    print(f"   pytest {test_file} -v")
    print("")
    print("🟢 Green: 実装を追加してテストを通す")
    print(f"   vim {worker_file}")
    print("")
    print("🔵 Refactor: コードを改善")
    print("")
    print("📊 カバレッジ確認:")
    print(f"   pytest {test_file} -v --cov=workers.{snake_name}")


def main():
    parser = argparse.ArgumentParser(
        description="TDDワーカー生成ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python generate-tdd-worker.py DataProcessor data
  python generate-tdd-worker.py ReportGenerator report
  python generate-tdd-worker.py --list-types
        """,
    )

    parser.add_argument(
        "worker_name", nargs="?", help="ワーカー名（例: DataProcessor）"
    )

    parser.add_argument(
        "worker_type", nargs="?", help="ワーカータイプ（例: data, report, analysis）"
    )

    parser.add_argument(
        "--list-types", action="store_true", help="利用可能なワーカータイプを表示"
    )

    args = parser.parse_args()

    if args.list_types:
        print("利用可能なワーカータイプ:")
        print("  - task: 汎用タスク処理")
        print("  - data: データ処理")
        print("  - report: レポート生成")
        print("  - analysis: 分析処理")
        print("  - notification: 通知処理")
        print("  - integration: 外部連携")
        return

    if not args.worker_name or not args.worker_type:
        parser.print_help()
        return

    generate_worker(args.worker_name, args.worker_type)


if __name__ == "__main__":
    main()
