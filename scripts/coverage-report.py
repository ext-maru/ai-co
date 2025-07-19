#!/usr/bin/env python3
"""
Elders Guild カバレッジレポート生成ツール
テストカバレッジの可視化と分析を行います
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# カラー定義
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


class CoverageReporter:
    """カバレッジレポート生成クラス"""

    def __init__(self, project_root: Path = Path("/home/aicompany/ai_co")):
        self.project_root = project_root
        self.coverage_file = project_root / ".coverage"
        self.htmlcov_dir = project_root / "htmlcov"
        self.report_dir = project_root / ".coverage-reports"
        self.report_dir.mkdir(exist_ok=True)

    def run_coverage(self, test_path: str = "tests/unit") -> bool:
        """カバレッジ測定を実行"""
        print(f"{BLUE}📊 カバレッジ測定を開始します...{NC}")

        cmd = [
            "python",
            "-m",
            "pytest",
            test_path,
            "--cov=.",
            "--cov-report=html",
            "--cov-report=json",
            "--cov-report=term",
            "-v",
        ]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"{GREEN}✅ テスト実行成功{NC}")
                return True
            else:
                print(f"{RED}❌ テスト実行失敗{NC}")
                print(result.stderr)
                return False

        except Exception as e:
            print(f"{RED}エラー: {e}{NC}")
            return False

    def analyze_coverage(self) -> Dict:
        """カバレッジデータを分析"""
        coverage_json = self.project_root / "coverage.json"

        if not coverage_json.exists():
            print(f"{YELLOW}⚠️  coverage.jsonが見つかりません{NC}")
            return {}

        with open(coverage_json, "r") as f:
            data = json.load(f)

        # 全体のカバレッジ
        total_coverage = data.get("totals", {}).get("percent_covered", 0)

        # モジュール別カバレッジ
        module_coverage = {}
        for file_path, file_data in data.get("files", {}).items():
            # プロジェクト内のファイルのみ対象
            if file_path.startswith(str(self.project_root)):
                rel_path = Path(file_path).relative_to(self.project_root)
                module_coverage[str(rel_path)] = {
                    "coverage": file_data["summary"]["percent_covered"],
                    "missing_lines": file_data["summary"]["missing_lines"],
                    "covered_lines": file_data["summary"]["covered_lines"],
                }

        return {
            "total_coverage": total_coverage,
            "module_coverage": module_coverage,
            "timestamp": datetime.now().isoformat(),
        }

    def generate_badge(self, coverage: float) -> str:
        """カバレッジバッジを生成"""
        if coverage >= 90:
            color = "brightgreen"
        elif coverage >= 80:
            color = "green"
        elif coverage >= 70:
            color = "yellow"
        elif coverage >= 50:
            color = "orange"
        else:
            color = "red"

        badge_url = f"https://img.shields.io/badge/coverage-{coverage:.1f}%25-{color}"
        return badge_url

    def generate_report(self, analysis: Dict) -> str:
        """マークダウン形式のレポートを生成"""
        report = f"""# Elders Guild テストカバレッジレポート

生成日時: {analysis['timestamp']}

## 📊 全体カバレッジ

**{analysis['total_coverage']:.1f}%**

![Coverage Badge]({self.generate_badge(analysis['total_coverage'])})

## 📁 モジュール別カバレッジ

| モジュール | カバレッジ | カバー行数 | 未カバー行数 |
|-----------|-----------|-----------|-------------|
"""

        # モジュールをカテゴリ別に分類
        categories = {
            "workers": [],
            "libs": [],
            "core": [],
            "commands": [],
            "other": [],
        }

        for module, data in analysis["module_coverage"].items():
            if module.startswith("workers/"):
                categories["workers"].append((module, data))
            elif module.startswith("libs/"):
                categories["libs"].append((module, data))
            elif module.startswith("core/"):
                categories["core"].append((module, data))
            elif module.startswith("commands/"):
                categories["commands"].append((module, data))
            else:
                categories["other"].append((module, data))

        # カテゴリ別に出力
        for category, modules in categories.items():
            if modules:
                report += f"\n### {category.title()}\n\n"
                for module, data in sorted(modules):
                    coverage_percent = data["coverage"]
                    emoji = (
                        "✅"
                        if coverage_percent >= 80
                        else "⚠️"
                        if coverage_percent >= 60
                        else "❌"
                    )
                    report += f"| {emoji} {module} | {coverage_percent:.1f}% | {data['covered_lines']} | {data['missing_lines']} |\n"

        # 改善が必要なモジュール
        low_coverage = [
            (m, d) for m, d in analysis["module_coverage"].items() if d["coverage"] < 80
        ]
        if low_coverage:
            report += "\n## ⚠️ 改善が必要なモジュール\n\n"
            for module, data in sorted(low_coverage, key=lambda x: x[1]["coverage"]):
                report += f"- **{module}**: {data['coverage']:.1f}% (目標: 80%)\n"

        return report

    def save_history(self, analysis: Dict):
        """カバレッジ履歴を保存"""
        history_file = self.report_dir / "coverage_history.json"

        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []

        history.append(
            {
                "timestamp": analysis["timestamp"],
                "total_coverage": analysis["total_coverage"],
            }
        )

        # 最新100件のみ保持
        history = history[-100:]

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def main(self):
        """メイン処理"""
        # テスト実行
        if not self.run_coverage():
            sys.exit(1)

        # カバレッジ分析
        analysis = self.analyze_coverage()
        if not analysis:
            print(f"{RED}カバレッジデータの分析に失敗しました{NC}")
            sys.exit(1)

        # レポート生成
        report = self.generate_report(analysis)

        # レポート保存
        report_file = (
            self.report_dir
            / f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(report_file, "w") as f:
            f.write(report)

        # 最新レポートのシンボリックリンク
        latest_link = self.report_dir / "latest_report.md"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(report_file.name)

        # 履歴保存
        self.save_history(analysis)

        # 結果表示
        print(f"\n{GREEN}📊 カバレッジレポートを生成しました{NC}")
        print(f"全体カバレッジ: {analysis['total_coverage']:.1f}%")
        print(f"\nレポート: {report_file}")
        print(f"HTMLレポート: file://{self.htmlcov_dir}/index.html")

        # カバレッジ基準チェック
        if analysis["total_coverage"] < 80:
            print(f"\n{YELLOW}⚠️  警告: カバレッジが80%未満です{NC}")
            sys.exit(1)


if __name__ == "__main__":
    reporter = CoverageReporter()
    reporter.main()
