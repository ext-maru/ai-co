#!/usr/bin/env python3
"""
OSS移行プロジェクト - ベースラインメトリクス測定スクリプト
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class BaselineMetrics:
    def __init__(self):
        self.base_dir = Path("/home/aicompany/ai_co")
        self.target_files = [
            "libs/automated_code_review.py",
            "libs/async_worker_optimization.py",
            "libs/integration_test_framework.py",
            "libs/advanced_monitoring_dashboard.py",
            "libs/security_audit_system.py",
        ]
        self.metrics = defaultdict(dict)

    def count_lines(self, filepath):
        """ファイルの行数を計測"""
        try:
            with open(self.base_dir / filepath, "r") as f:
                total_lines = len(f.readlines())

            # 空行とコメント行を除外
            with open(self.base_dir / filepath, "r") as f:
                code_lines = 0
                comment_lines = 0
                blank_lines = 0
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        blank_lines += 1
                    elif stripped.startswith("#"):
                        comment_lines += 1
                    else:
                        code_lines += 1

            return {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines,
            }
        except Exception as e:
            return {"error": str(e)}

    def count_functions_classes(self, filepath):
        """関数とクラスの数を計測"""
        try:
            with open(self.base_dir / filepath, "r") as f:
                content = f.read()

            import ast

            tree = ast.parse(content)

            functions = 0
            classes = 0
            methods = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions += 1
                elif isinstance(node, ast.ClassDef):
                    classes += 1
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods += 1
                            functions -= 1  # メソッドは関数から除外

            return {
                "functions": functions,
                "classes": classes,
                "methods": methods,
                "total_definitions": functions + classes + methods,
            }
        except Exception as e:
            return {"error": str(e)}

    def check_tests(self, filepath):
        """対応するテストファイルの存在と数を確認"""
        test_file = filepath.replace("libs/", "tests/unit/test_")
        test_path = self.base_dir / test_file

        if test_path.exists():
            try:
                with open(test_path, "r") as f:
                    content = f.read()

                # テスト関数をカウント
                import re

                test_functions = len(re.findall(r"def test_\w+\(", content))

                return {"test_file_exists": True, "test_functions": test_functions}
            except Exception as e:
                return {"test_file_exists": True, "error": str(e)}
        else:
            return {"test_file_exists": False, "test_functions": 0}

    def analyze_complexity(self, filepath):
        """循環的複雑度の分析（簡易版）"""
        try:
            with open(self.base_dir / filepath, "r") as f:
                content = f.read()

            # 簡易的な複雑度の指標
            complexity_indicators = {
                "if_statements": len(
                    [1 for line in content.split("\n") if "if " in line]
                ),
                "for_loops": len([1 for line in content.split("\n") if "for " in line]),
                "while_loops": len(
                    [1 for line in content.split("\n") if "while " in line]
                ),
                "try_blocks": len(
                    [1 for line in content.split("\n") if "try:" in line]
                ),
                "nested_functions": content.count("def ") - content.count("\ndef "),
            }

            complexity_score = sum(complexity_indicators.values())

            return {**complexity_indicators, "complexity_score": complexity_score}
        except Exception as e:
            return {"error": str(e)}

    def analyze_dependencies(self, filepath):
        """依存関係の分析"""
        try:
            with open(self.base_dir / filepath, "r") as f:
                content = f.read()

            import ast

            tree = ast.parse(content)

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(
                            f"{module}.{alias.name}" if module else alias.name
                        )

            # 標準ライブラリとサードパーティを分離
            stdlib_modules = {
                "os",
                "sys",
                "json",
                "time",
                "datetime",
                "pathlib",
                "logging",
                "asyncio",
                "typing",
                "collections",
                "functools",
                "re",
                "uuid",
            }

            stdlib_imports = [
                imp for imp in imports if imp.split(".")[0] in stdlib_modules
            ]
            third_party_imports = [
                imp
                for imp in imports
                if imp.split(".")[0] not in stdlib_modules and not imp.startswith(".")
            ]
            local_imports = [imp for imp in imports if imp.startswith(".")]

            return {
                "total_imports": len(imports),
                "stdlib_imports": len(stdlib_imports),
                "third_party_imports": len(third_party_imports),
                "local_imports": len(local_imports),
                "unique_dependencies": len(
                    set(imp.split(".")[0] for imp in third_party_imports)
                ),
            }
        except Exception as e:
            return {"error": str(e)}

    def collect_all_metrics(self):
        """すべてのメトリクスを収集"""
        timestamp = datetime.now().isoformat()

        for filepath in self.target_files:
            print(f"Analyzing {filepath}...")

            self.metrics[filepath] = {
                "lines": self.count_lines(filepath),
                "structure": self.count_functions_classes(filepath),
                "tests": self.check_tests(filepath),
                "complexity": self.analyze_complexity(filepath),
                "dependencies": self.analyze_dependencies(filepath),
            }

        # サマリー統計
        total_lines = sum(
            m["lines"]["total_lines"]
            for m in self.metrics.values()
            if "total_lines" in m.get("lines", {})
        )
        total_code_lines = sum(
            m["lines"]["code_lines"]
            for m in self.metrics.values()
            if "code_lines" in m.get("lines", {})
        )
        total_classes = sum(
            m["structure"]["classes"]
            for m in self.metrics.values()
            if "classes" in m.get("structure", {})
        )
        total_functions = sum(
            m["structure"]["functions"]
            for m in self.metrics.values()
            if "functions" in m.get("structure", {})
        )
        total_tests = sum(
            m["tests"]["test_functions"]
            for m in self.metrics.values()
            if "test_functions" in m.get("tests", {})
        )

        self.metrics["summary"] = {
            "timestamp": timestamp,
            "total_files": len(self.target_files),
            "total_lines": total_lines,
            "total_code_lines": total_code_lines,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_tests": total_tests,
            "test_coverage_estimate": (
                f"{(total_tests / (total_classes + total_functions) * 100):.1f}%"
                if (total_classes + total_functions) > 0
                else "0%"
            ),
        }

        return self.metrics

    def save_report(self, output_path=None):
        """レポートを保存"""
        if output_path is None:
            output_path = self.base_dir / "docs" / "oss_baseline_metrics.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.metrics, f, indent=2)

        print(f"\nBaseline metrics saved to: {output_path}")

    def print_summary(self):
        """サマリーを表示"""
        print("\n" + "=" * 60)
        print("📊 OSS移行プロジェクト - ベースラインメトリクス")
        print("=" * 60)

        summary = self.metrics.get("summary", {})
        print(f"\n📅 測定日時: {summary.get('timestamp', 'N/A')}")
        print(f"📁 対象ファイル数: {summary.get('total_files', 0)}")
        print(f"📝 総行数: {summary.get('total_lines', 0):,}")
        print(f"💻 実コード行数: {summary.get('total_code_lines', 0):,}")
        print(f"🏗️ クラス数: {summary.get('total_classes', 0)}")
        print(f"⚡ 関数数: {summary.get('total_functions', 0)}")
        print(f"🧪 テスト数: {summary.get('total_tests', 0)}")
        print(f"📈 推定テストカバレッジ: {summary.get('test_coverage_estimate', '0%')}")

        print("\n" + "-" * 60)
        print("📋 ファイル別詳細:")
        print("-" * 60)

        for filepath, metrics in self.metrics.items():
            if filepath == "summary":
                continue

            print(f"\n🔍 {filepath}")
            lines = metrics.get("lines", {})
            structure = metrics.get("structure", {})
            tests = metrics.get("tests", {})
            complexity = metrics.get("complexity", {})

            print(
                f"   行数: {lines.get('total_lines', 0)} (コード: {lines.get('code_lines', 0)})"
            )
            print(
                (
                    f"f"   構造: クラス {structure.get('classes', 0)}, 関数 {structure.get('functions', 0)}, メソッド "
                    f"{structure.get('methods', 0)}""
                )
            )
            print(
                f"   テスト: {'✅' if tests.get('test_file_exists') else '❌'} {tests.get('test_functions', 0)} 個"
            )
            print(f"   複雑度スコア: {complexity.get('complexity_score', 0)}")


if __name__ == "__main__":
    metrics = BaselineMetrics()
    metrics.collect_all_metrics()
    metrics.print_summary()
    metrics.save_report()
