#!/usr/bin/env python3
"""
🏛️ エルダーズ開発標準チェッカー
プレコミット時に開発標準の適合性を自動検証
"""

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# カラー出力
class Colors:
    """Colorsクラス"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def print_header():
    """ヘッダー表示"""
    print(
        f"\n{Colors.PURPLE}{Colors.BOLD}🏛️ エルダーズギルド開発標準チェック{Colors.ENDC}"
    )
    print("=" * 50)

def check_costar_documentation() -> Tuple[bool, str]:
    """CO-STAR文書の確認"""
    costar_files = list(Path(".").glob("**/COSTAR*.md")) + list(
        Path(".").glob("**/costar*.md")
    )

    if not costar_files:
        return False, "CO-STAR定義文書が見つかりません"

    # 最新のCO-STAR文書をチェック
    latest_file = max(costar_files, key=lambda p: p.stat().st_mtime)
    content = latest_file.read_text(encoding="utf-8")

    required_sections = [
        "Context",
        "Objective",
        "Style",
        "Tone",
        "Audience",
        "Response",
    ]
    missing = [s for s in required_sections if s not in content]

    if missing:
        return False, f"CO-STAR文書に不足セクション: {', '.join(missing)}"

    return True, f"CO-STAR文書確認済み: {latest_file}"

def check_tdd_compliance() -> Tuple[bool, str]:
    """TDD準拠の確認"""
    # 変更されたPythonファイルを取得
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )

    py_files = [
        f
        for f in result.stdout.strip().split("\n")
        if f.endswith(".py") and not f.startswith("test_")
    ]

    issues = []
    for py_file in py_files:
        # 対応するテストファイルの存在確認
        test_file = Path(f"tests/unit/test_{Path(py_file).name}")
        if not test_file.exists():
            # プロジェクト内のテストディレクトリも確認
            project_test = Path(py_file).parent / f"test_{Path(py_file).name}"
            if not project_test.exists():
                issues.append(f"テストなし: {py_file}")

    if issues:
        return (
            False,
            f"TDD違反: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}",
        )

    return True, "全ファイルにテスト確認"

def check_pdca_tracking() -> Tuple[bool, str]:
    """PDCAトラッキングの確認"""
    pdca_files = list(Path(".").glob("**/.pdca/*.json"))

    if not pdca_files:
        # プロジェクトルートの.pdcaディレクトリを作成
        pdca_dir = Path(".pdca")
        pdca_dir.mkdir(exist_ok=True)

        # 初期PDCAファイルを作成
        initial_pdca = {
            "project": Path.cwd().name,
            "created_at": str(Path.cwd().stat().st_mtime),
            "cycles": [],
        }

        pdca_file = pdca_dir / "pdca_tracking.json"
        pdca_file.write_text(json.dumps(initial_pdca, indent=2))

        return True, "PDCAトラッキング初期化完了"

    return True, f"PDCAトラッキング確認: {len(pdca_files)}ファイル"

def check_gui_standards() -> Tuple[bool, str]:
    """GUI標準適合性の確認"""
    # TSX/JSXファイルの確認
    tsx_files = list(Path(".").glob("**/*.tsx")) + list(Path(".").glob("**/*.jsx"))

    issues = []
    for file_path in tsx_files[:5]:  # 最初の5ファイルのみチェック
        content = file_path.read_text(encoding="utf-8")

        # エルダーコンポーネントの使用確認
        if "Elder" not in content and "elder" not in content:
            issues.append(f"エルダー標準未適用: {file_path.name}")

    if issues:
        return False, f"GUI標準違反: {', '.join(issues[:3])}"

    return True, "GUI標準適合確認"

def check_elder_decorators() -> Tuple[bool, str]:
    """エルダーデコレーターの使用確認"""
    py_files = list(Path(".").glob("**/*.py"))

    decorated_count = 0
    for file_path in py_files:
        if "__pycache__" in str(file_path) or "venv" in str(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            if "@incident_aware" in content or "@pdca_aware" in content:
                decorated_count += 1
        except:
            pass

    if decorated_count == 0:
        return False, "エルダーデコレーター未使用"

    return True, f"エルダーデコレーター使用: {decorated_count}ファイル"

def auto_fix_issues(issues: List[Tuple[str, bool, str]]) -> int:
    """自動修正可能な問題を修正"""
    fixed_count = 0

    for check_name, passed, message in issues:
        if not passed:
            if "CO-STAR" in message:
                # CO-STARテンプレート生成

## Context（背景）
[プロジェクトの背景と現状を記述]

## Objective（目的）
[明確な目標と成功指標を記述]

## Style（スタイル）
- TDD必須
- エルダーズギルド開発標準準拠

## Tone（トーン）
- 品質第一
- 透明性と説明責任

## Audience（対象）
- 開発チーム
- ステークホルダー

## Response（期待成果）
[測定可能な成果を記述]
"""

                print(f"{Colors.GREEN}✅ CO-STARテンプレート生成{Colors.ENDC}")
                fixed_count += 1

    return fixed_count

def main():
    """メインチェック処理"""
    print_header()

    # チェック項目
    checks = [
        ("CO-STAR文書", check_costar_documentation),
        ("TDD準拠", check_tdd_compliance),
        ("PDCAトラッキング", check_pdca_tracking),
        ("GUI標準", check_gui_standards),
        ("エルダーデコレーター", check_elder_decorators),
    ]

    results = []
    all_passed = True

    # 各チェック実行
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            results.append((check_name, passed, message))

            if passed:
                print(f"{Colors.GREEN}✅ {check_name}: {message}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}❌ {check_name}: {message}{Colors.ENDC}")
                all_passed = False
        except Exception as e:
            print(f"{Colors.RED}❌ {check_name}: エラー - {str(e)}{Colors.ENDC}")
            results.append((check_name, False, str(e)))
            all_passed = False

    # 自動修正
    if not all_passed:
        print(f"\n{Colors.YELLOW}🔧 自動修正を試みています...{Colors.ENDC}")
        fixed_count = auto_fix_issues(results)
        if fixed_count > 0:
            print(
                f"{Colors.GREEN}✅ {fixed_count}件の問題を自動修正しました{Colors.ENDC}"
            )

    # 結果サマリ
    print("\n" + "=" * 50)
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ エルダーズ開発標準: 合格{Colors.ENDC}")
        print(f"{Colors.BLUE}品質第一で開発を進めてください！{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ エルダーズ開発標準: 不合格{Colors.ENDC}")
        print(f"{Colors.YELLOW}上記の問題を修正してください{Colors.ENDC}")
        print(
            f"\n{Colors.PURPLE}ヒント: 'ai-dev-fix' コマンドで自動修正を試みることができます{Colors.ENDC}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
