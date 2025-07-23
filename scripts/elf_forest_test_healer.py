#!/usr/bin/env python3
"""
エルフの森 - テスト修復魔法
失敗したテストを自動的に修復する統合スクリプト
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestHealer:
    """テスト修復を行うヒーリングエルフ"""

    def __init__(self):
        self.test_dir = PROJECT_ROOT / "tests"
        self.common_fixes = {
            "ModuleNotFoundError: No module named 'base_test'": self.fix_base_test_import,
            "ImportError": self.fix_import_error,
            "AttributeError": self.fix_attribute_error,
            "TypeError": self.fix_type_error,
        }
        self.successful_patterns = []
        self.failed_patterns = []

    def diagnose_test_failures(self) -> List[Dict]:
        """テスト失敗の診断"""
        print("🧪 テスト失敗パターンを診断中...")

        failures = []
        test_files = list(self.test_dir.rglob("test_*.py"))

        for test_file in test_files[:10]:  # まず10ファイルで試行
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                failure_info = {
                    "file": str(test_file),
                    "output": result.stdout + result.stderr,
                    "errors": self.extract_errors(result.stdout + result.stderr),
                }
                failures.append(failure_info)

        return failures

    def extract_errors(self, output: str) -> List[str]:
        """エラーメッセージの抽出"""
        error_patterns = [
            r"E\s+(\w+Error: .+)",
            r"ERROR\s+(.+)",
            r"FAILED\s+.+::\s+(.+)",
        ]

        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, output)
            errors.extend(matches)

        return errors

    def fix_base_test_import(self, test_file: Path) -> bool:
        """base_testインポートエラーの修正"""
        print(f"🔧 {test_file}のbase_testインポートを修正中...")

        with open(test_file, "r") as f:
            content = f.read()

        # base_testインポートをtest_base_utilsに置換
        fixed_content = content.replace(
            "from base_test import", "from tests.test_base_utils import"
        )

        # 相対インポートの修正
        fixed_content = re.sub(
            r"sys\.path\.insert\(0, str\(Path\(__file__\)\.parent\.parent\)\)",
            "",
            fixed_content,
        )

        with open(test_file, "w") as f:
            f.write(fixed_content)

        return True

    def fix_import_error(self, test_file: Path) -> bool:
        """一般的なインポートエラーの修正"""
        print(f"🔧 {test_file}のインポートエラーを修正中...")

        with open(test_file, "r") as f:
            content = f.read()

        # 相対インポートを絶対インポートに変換
        fixed_content = re.sub(r"from \.\.(\w+) import", r"from \1 import", content)

        # libsやworkersの前にプロジェクトルートを確保
        if "sys.path.insert" not in fixed_content:
            import_section = """import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
            fixed_content = import_section + fixed_content

        with open(test_file, "w") as f:
            f.write(fixed_content)

        return True

    def fix_attribute_error(self, test_file: Path) -> bool:
        """属性エラーの修正"""
        print(f"🔧 {test_file}の属性エラーを修正中...")

        # モックの適切な設定を追加
        with open(test_file, "r") as f:
            content = f.read()

        # 一般的な属性エラーパターンを修正
        if "MagicMock()" in content and "spec=" not in content:
            fixed_content = re.sub(r"MagicMock\(\)", r"MagicMock(spec=True)", content)

            with open(test_file, "w") as f:
                f.write(fixed_content)

            return True

        return False

    def fix_type_error(self, test_file: Path) -> bool:
        """型エラーの修正"""
        print(f"🔧 {test_file}の型エラーを修正中...")

        # 一般的な型エラーの修正パターンを適用
        return False

    def apply_healing_magic(self, failures: List[Dict]) -> Dict[str, int]:
        """修復魔法の適用"""
        results = {"fixed": 0, "failed": 0, "skipped": 0}

        # 繰り返し処理
        for failure in failures:
            test_file = Path(failure["file"])
            fixed = False

            # エラーパターンに基づいて修正を試行
            for error in failure["errors"]:
                for pattern, fix_func in self.common_fixes.items():
                    if pattern in error:
                        if not (fix_func(test_file)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if fix_func(test_file):
                            fixed = True
                            break

                if fixed:
                    break

            if fixed:
                # 修正後にテストを再実行
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_file), "-v"],
                    capture_output=True,
                )

                if result.returncode == 0:
                    results["fixed"] += 1
                    print(f"✅ {test_file.name} - 修復成功！")
                else:
                    results["failed"] += 1
                    print(f"❌ {test_file.name} - 修復後も失敗")
            else:
                results["skipped"] += 1
                print(f"⏭️  {test_file.name} - 修復方法が見つかりません")

        return results

    def generate_healing_report(self, results: Dict[str, int]):
        """修復レポートの生成"""
        report = f"""
🌲 エルフの森 - テスト修復レポート
=====================================

📊 修復結果:
- ✅ 修復成功: {results['fixed']}
- ❌ 修復失敗: {results['failed']}
- ⏭️  スキップ: {results['skipped']}

🎯 次のステップ:
1. 修復成功したパターンを他のテストに適用
2. 修復失敗したテストの手動確認
3. 共通テストユーティリティの強化
"""

        report_path = PROJECT_ROOT / "elf_forest_healing_report.md"
        with open(report_path, "w") as f:
            f.write(report)

        print(report)
        return report_path


def main():
    """メイン処理"""
    print("🌲 エルフの森 - テスト修復魔法を開始します")

    healer = TestHealer()

    # 1. テスト失敗の診断
    failures = healer.diagnose_test_failures()
    print(f"\n📋 診断結果: {len(failures)}個のテストで問題を検出")

    # 2. 修復魔法の適用
    if failures:
        results = healer.apply_healing_magic(failures)

        # 3. レポート生成
        report_path = healer.generate_healing_report(results)
        print(f"\n📄 詳細レポート: {report_path}")
    else:
        print("✨ すべてのテストが正常です！")


if __name__ == "__main__":
    main()
