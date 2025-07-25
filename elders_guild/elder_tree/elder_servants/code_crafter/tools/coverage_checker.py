#!/usr/bin/env python3
"""
🧪 Elders Guild 4-Sage System カバレッジチェッカー
各ライブラリのテストカバレッジを分析・報告
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict
from typing import List
from typing import Set

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class CoverageAnalyzer:
    """テストカバレッジ分析器"""

    def __init__(self):
        self.libs_dir = PROJECT_ROOT / "libs"
        self.tests_dir = PROJECT_ROOT / "tests" / "unit" / "libs"

    def analyze_file_coverage(self, lib_file: Path) -> Dict[str, any]:
        """ファイルのカバレッジ分析"""

        # ライブラリファイルの関数・クラス・メソッドを抽出
        lib_functions = self._extract_definitions(lib_file)

        # 対応するテストファイルを探す
        test_file = self.tests_dir / f"test_{lib_file.stem}.py"

        if not test_file.exists():
            # スタンドアロンテストランナーを確認
            test_runner = (
                self.tests_dir / f"run_{lib_file.stem.replace('_', '_')}_tests.py"
            )
            if test_runner.exists():
                test_file = test_runner
            else:
                return {
                    "lib_file": lib_file.name,
                    "total_definitions": len(lib_functions),
                    "tested_definitions": 0,
                    "coverage_percentage": 0.0,
                    "untested_functions": lib_functions,
                    "test_file_exists": False,
                }

        # テストファイルでテストされている関数を抽出
        tested_functions = self._extract_tested_functions(test_file)

        # カバレッジ計算
        tested_count = len([f for f in lib_functions if f in tested_functions])
        total_count = len(lib_functions)
        coverage = (tested_count / total_count * 100) if total_count > 0 else 0

        untested = [f for f in lib_functions if f not in tested_functions]

        return {
            "lib_file": lib_file.name,
            "total_definitions": total_count,
            "tested_definitions": tested_count,
            "coverage_percentage": coverage,
            "untested_functions": untested,
            "test_file_exists": True,
            "test_file": test_file.name,
        }

    def _extract_definitions(self, python_file: Path) -> Set[str]:
        """Pythonファイルから関数・クラス・メソッド定義を抽出"""
        definitions = set()

        try:
            with open(python_file, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
            # 繰り返し処理
                if isinstance(node, ast.FunctionDef):
                    definitions.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    definitions.add(node.name)
                    # クラス内のメソッドも追加
                    # Deep nesting detected (depth: 5) - consider refactoring
                    for item in node.body:
                        if not (isinstance(item, ast.FunctionDef)):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if isinstance(item, ast.FunctionDef):
                            definitions.add(f"{node.name}.{item.name}")
                elif isinstance(node, ast.AsyncFunctionDef):
                    definitions.add(node.name)

        except Exception as e:
            print(f"⚠️ ファイル解析エラー {python_file}: {e}")

        # プライベート関数と特殊メソッドを除外
        filtered_definitions = {
            d
            for d in definitions
            if not d.startswith("_") or d.startswith("__") and d.endswith("__")
        }

        return filtered_definitions

    def _extract_tested_functions(self, test_file: Path) -> Set[str]:
        """テストファイルからテスト対象の関数を抽出"""
        tested_functions = set()

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            # テスト関数名からテスト対象を推測
            test_function_pattern = r"def test_(\w+)"
            test_functions = re.findall(test_function_pattern, content)

            for test_func in test_functions:
                # test_create_node -> create_node
                if test_func.startswith("test_"):
                    tested_functions.add(test_func[5:])
                else:
                    tested_functions.add(test_func)

            # 直接呼び出されている関数も検出
            function_call_pattern = r"\.(\w+)\("
            function_calls = re.findall(function_call_pattern, content)
            tested_functions.update(function_calls)

            # クラスメソッド呼び出しの検出
            method_call_pattern = r"(\w+)\.(\w+)\("
            method_calls = re.findall(method_call_pattern, content)
            for class_name, method_name in method_calls:
                if not method_name.startswith("_"):
                    tested_functions.add(method_name)
                    tested_functions.add(f"{class_name}.{method_name}")

        except Exception as e:
            print(f"⚠️ テストファイル解析エラー {test_file}: {e}")

        return tested_functions

    def generate_coverage_report(self) -> Dict[str, any]:
        """包括的カバレッジレポート生成"""

        # Phase 2の主要ライブラリ
        target_libs = [
            "quantum_collaboration_engine.py",
            "predictive_incident_manager.py",
            "dynamic_knowledge_graph.py",
        ]

        results = []
        total_definitions = 0
        total_tested = 0

        print("🧪 Elders Guild 4-Sage System カバレッジ分析")
        print("=" * 60)

        # 繰り返し処理
        for lib_name in target_libs:
            lib_file = self.libs_dir / lib_name

            if lib_file.exists():
                result = self.analyze_file_coverage(lib_file)
                results.append(result)

                total_definitions += result["total_definitions"]
                total_tested += result["tested_definitions"]

                # 個別レポート
                status = (
                    "✅"
                    if result["coverage_percentage"] >= 90
                    else "🟡" if result["coverage_percentage"] >= 70 else "❌"
                )
                print(f"\n{status} {result['lib_file']}")
                print(f"   📊 カバレッジ: {result['coverage_percentage']:0.1f}%")
                print(f"   📝 定義数: {result['total_definitions']}")
                print(f"   ✅ テスト済み: {result['tested_definitions']}")

                if result["untested_functions"]:
                    print(f"   ❌ 未テスト: {len(result['untested_functions'])}件")
                    for func in list(result["untested_functions"])[
                        :5
                    ]:  # 最初の5件のみ表示
                        print(f"      - {func}")
                    if len(result["untested_functions"]) > 5:
                        print(f"      ... 他{len(result['untested_functions']) - 5}件")

        # 全体サマリー
        overall_coverage = (
            (total_tested / total_definitions * 100) if total_definitions > 0 else 0
        )

        print("\n🎯 全体カバレッジサマリー")
        print("=" * 30)
        print(f"📊 総合カバレッジ: {overall_coverage:0.1f}%")
        print(f"📝 総定義数: {total_definitions}")
        print(f"✅ テスト済み: {total_tested}")
        print(f"❌ 未テスト: {total_definitions - total_tested}")

        if overall_coverage >= 90:
            print("🎉 素晴らしい！90%以上のカバレッジです！")
        elif overall_coverage >= 70:
            print("🟡 良好です。90%目指して頑張りましょう！")
        else:
            print("❌ カバレッジが不足しています。テスト強化が必要です。")

        return {
            "overall_coverage": overall_coverage,
            "total_definitions": total_definitions,
            "total_tested": total_tested,
            "results": results,
        }

    def suggest_test_improvements(self, results: Dict[str, any]) -> List[str]:
        """テスト改善提案"""
        suggestions = []

        for result in results["results"]:
            if result["coverage_percentage"] < 90:
                lib_name = result["lib_file"]
                suggestions.append(
                    f"📝 {lib_name}: {len(result['untested_functions'])}個の関数にテスト追加"
                )

                # 重要そうな関数を優先
                important_functions = [
                    f
                    for f in result["untested_functions"]
                    if any(
                        keyword in f.lower()
                        for keyword in [
                            "create",
                            "update",
                            "delete",
                            "process",
                            "analyze",
                            "calculate",
                        ]
                    )
                ]

                if important_functions:
                    suggestions.append(
                        f"   🎯 優先テスト対象: {', '.join(important_functions[:3])}"
                    )

        return suggestions


def main():
    """メイン実行"""
    analyzer = CoverageAnalyzer()
    results = analyzer.generate_coverage_report()

    # 改善提案
    suggestions = analyzer.suggest_test_improvements(results)
    if suggestions:
        print("\n💡 テスト改善提案")
        print("=" * 20)
        for suggestion in suggestions:
            print(suggestion)

    # 目標到達チェック
    if results["overall_coverage"] < 90:
        print(f"\n🎯 90%カバレッジまであと {90 - results['overall_coverage']:0.1f}% !")
        needed_tests = int(
            (90 * results["total_definitions"] / 100) - results["total_tested"]
        )
        print(f"   📝 追加テスト数: 約{needed_tests}個の関数/メソッド")

    return 0 if results["overall_coverage"] >= 90 else 1


if __name__ == "__main__":
    sys.exit(main())
