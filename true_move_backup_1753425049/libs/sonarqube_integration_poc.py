#!/usr/bin/env python3
"""
SonarQube統合POC - OSS移行プロジェクト
既存のautomated_code_review.pyをSonarQube + 各種リンターで置き換える
"""
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

# SonarQube設定
SONARQUBE_URL = "http://localhost:9000"
SONARQUBE_TOKEN = "your-token-here"


class SonarQubeIntegration:
    """SonarQube統合クラス"""

    def __init__(self, url: str = SONARQUBE_URL, token: str = SONARQUBE_TOKEN):
        """初期化"""
        self.url = url
        self.token = token
        self.logger = logging.getLogger(__name__)

    def analyze_project(self, project_path: str, project_key: str) -> Dict[str, Any]:
        """プロジェクト分析の実行"""
        # sonar-scanner実行
        cmd = [
            "sonar-scanner",
            f"-Dsonar.projectKey={project_key}",
            f"-Dsonar.sources={project_path}",
            f"-Dsonar.host.url={self.url}",
            f"-Dsonar.login={self.token}",
            "-Dsonar.python.version=3.8,3.9,3.10,3.11",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # 分析結果を取得
                return self._get_analysis_results(project_key)
            else:
                self.logger.error(f"SonarQube analysis failed: {result.stderr}")
                return {"error": result.stderr}
        except Exception as e:
            self.logger.error(f"Error running sonar-scanner: {e}")
            return {"error": str(e)}

    def _get_analysis_results(self, project_key: str) -> Dict[str, Any]:
        """分析結果の取得"""
        # API経由で結果を取得
        headers = {"Authorization": f"Bearer {self.token}"}

        # 品質ゲート状態
        qg_url = f"{self.url}/api/qualitygates/project_status?projectKey={project_key}"
        qg_response = requests.get(qg_url, headers=headers)

        # Issues取得
        issues_url = f"{self.url}/api/issues/search?componentKeys={project_key}"
        issues_response = requests.get(issues_url, headers=headers)

        # メトリクス取得
        metrics_url = f"{self.url}/api/measures/component"
        metrics_params = {
            "component": project_key,
            "metricKeys": "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density",
        }
        metrics_response = requests.get(
            metrics_url, headers=headers, params=metrics_params
        )

        return {
            "quality_gate": qg_response.json() if qg_response.ok else None,
            "issues": issues_response.json() if issues_response.ok else None,
            "metrics": metrics_response.json() if metrics_response.ok else None,
        }


class PythonLinterIntegration:
    """Python用リンター統合"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.linters = {
            "flake8": Flake8Linter(),
            "pylint": PylintLinter(),
            "bandit": BanditLinter(),
            "mypy": MypyLinter(),
            "black": BlackFormatter(),
            "isort": IsortFormatter(),
        }

    def run_all_linters(self, file_path: str) -> Dict[str, Any]:
        """すべてのリンターを実行"""
        results = {}

        for name, linter in self.linters.items():
            try:
                results[name] = linter.run(file_path)
            except Exception as e:
                self.logger.error(f"Error running {name}: {e}")
                results[name] = {"error": str(e)}

        return results

    def get_consolidated_issues(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """結果を統合"""
        issues = []

        # 各リンターの結果を統一フォーマットに変換
        for linter_name, result in results.items():
            if "issues" in result:
                for issue in result["issues"]:
                    issues.append(
                        {
                            "source": linter_name,
                            "severity": issue.get("severity", "medium"),
                            "type": issue.get("type", "code_smell"),
                            "message": issue.get("message", ""),
                            "line": issue.get("line", 0),
                            "column": issue.get("column", 0),
                            "rule": issue.get("rule", ""),
                        }
                    )

        return issues


class Flake8Linter:
    """Flake8リンター"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """Flake8実行"""
        cmd = ["flake8", "--format=json", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                # Flake8のJSON出力をパース
                issues = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(":")
                        if not (len(parts) >= 4):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if len(parts) >= 4:
                            issues.append(
                                {
                                    "line": int(parts[1]),
                                    "column": int(parts[2]),
                                    "message": parts[3].strip(),
                                    "severity": "medium",
                                    "type": "style",
                                }
                            )
                return {"issues": issues}
            return {"issues": []}
        except Exception as e:
            return {"error": str(e)}


class PylintLinter:
    """Pylintリンター"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """Pylint実行"""
        cmd = ["pylint", "--output-format=json", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                issues_data = json.loads(result.stdout)
                issues = []
                for issue in issues_data:
                    severity = (
                        "high" if issue["type"] in ["error", "fatal"] else "medium"
                    )
                    issues.append(
                        {
                            "line": issue["line"],
                            "column": issue["column"],
                            "message": issue["message"],
                            "severity": severity,
                            "type": issue["type"],
                            "rule": issue["message-id"],
                        }
                    )
                return {"issues": issues}
            return {"issues": []}
        except Exception as e:
            return {"error": str(e)}


class BanditLinter:
    """Banditセキュリティリンター"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """Bandit実行"""
        cmd = ["bandit", "-f", "json", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                data = json.loads(result.stdout)
                issues = []
                for issue in data.get("results", []):
                    issues.append(
                        {
                            "line": issue["line_number"],
                            "message": issue["issue_text"],
                            "severity": issue["issue_severity"].lower(),
                            "type": "security",
                            "rule": issue["test_id"],
                        }
                    )
                return {"issues": issues}
            return {"issues": []}
        except Exception as e:
            return {"error": str(e)}


class MypyLinter:
    """Mypy型チェッカー"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """Mypy実行"""
        cmd = ["mypy", "--json-report", "-", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            issues = []
            for line in result.stdout.strip().split("\n"):
                if line and "error:" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        issues.append(
                            {
                                "line": int(parts[1]) if parts[1].isdigit() else 0,
                                "message": ":".join(parts[2:]).strip(),
                                "severity": "high",
                                "type": "type_error",
                            }
                        )
            return {"issues": issues}
        except Exception as e:
            return {"error": str(e)}


class BlackFormatter:
    """Blackフォーマッター"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """Black実行（チェックモード）"""
        cmd = ["black", "--check", "--diff", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "issues": [
                        {
                            "message": "Code formatting issues detected",
                            "severity": "low",
                            "type": "style",
                            "suggestion": "Run 'black' to auto-format",
                        }
                    ],
                    "diff": result.stdout,
                }
            return {"issues": []}
        except Exception as e:
            return {"error": str(e)}


class IsortFormatter:
    """isortインポートソーター"""

    def run(self, file_path: str) -> Dict[str, Any]:
        """isort実行（チェックモード）"""
        cmd = ["isort", "--check-only", "--diff", file_path]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return {
                    "issues": [
                        {
                            "message": "Import sorting issues detected",
                            "severity": "low",
                            "type": "style",
                            "suggestion": "Run 'isort' to auto-sort imports",
                        }
                    ],
                    "diff": result.stdout,
                }
            return {"issues": []}
        except Exception as e:
            return {"error": str(e)}


class UnifiedCodeReview:
    """統合コードレビューシステム"""

    def __init__(self):
        """初期化"""
        self.sonarqube = SonarQubeIntegration()
        self.linters = PythonLinterIntegration()
        self.logger = logging.getLogger(__name__)

    def review_file(
        self, file_path: str, use_sonarqube: bool = False
    ) -> Dict[str, Any]:
        """ファイルのレビュー実行"""
        results = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "linters": {},
            "sonarqube": None,
            "summary": {},
        }

        # リンター実行
        linter_results = self.linters.run_all_linters(file_path)
        results["linters"] = linter_results

        # SonarQube実行（オプション）
        if use_sonarqube:
            project_key = Path(file_path).stem
            results["sonarqube"] = self.sonarqube.analyze_project(
                Path(file_path).parent, project_key
            )

        # サマリー生成
        all_issues = self.linters.get_consolidated_issues(linter_results)
        results["summary"] = {
            "total_issues": len(all_issues),
            "by_severity": self._count_by_field(all_issues, "severity"),
            "by_type": self._count_by_field(all_issues, "type"),
            "by_source": self._count_by_field(all_issues, "source"),
        }

        return results

    def _count_by_field(self, issues: List[Dict], field: str) -> Dict[str, int]:
        """フィールド別カウント"""
        counts = {}
        for issue in issues:
            value = issue.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def generate_report(self, results: Dict[str, Any]) -> str:
        """レポート生成"""
        report = []
        report.append("# Code Review Report")
        report.append(f"**File**: {results['file']}")
        report.append(f"**Date**: {results['timestamp']}")
        report.append("")

        # サマリー
        summary = results["summary"]
        report.append("## Summary")
        report.append(f"- Total Issues: {summary['total_issues']}")
        report.append("")

        # 重要度別
        report.append("### By Severity")
        for severity, count in summary["by_severity"].items():
            report.append(f"- {severity}: {count}")
        report.append("")

        # タイプ別
        report.append("### By Type")
        for issue_type, count in summary["by_type"].items():
            report.append(f"- {issue_type}: {count}")
        report.append("")

        # ツール別
        report.append("### By Tool")
        for source, count in summary["by_source"].items():
            report.append(f"- {source}: {count}")

        return "\n".join(report)


# 既存APIとの互換性レイヤー
class AutomatedCodeReviewCompat:
    """既存のautomated_code_reviewとの互換性レイヤー"""

    def __init__(self):
        """初期化メソッド"""
        self.unified_review = UnifiedCodeReview()

    def analyze_code_quality(
        self, code: str, language: str = "python"
    ) -> Dict[str, Any]:
        """既存APIとの互換性メソッド"""
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # レビュー実行
            results = self.unified_review.review_file(temp_path)

            # 既存フォーマットに変換
            all_issues = self.unified_review.linters.get_consolidated_issues(
                results["linters"]
            )

            # 品質スコア計算（簡易版）
            quality_score = max(0, 100 - len(all_issues) * 5)

            return {
                "quality_score": quality_score,
                "issues": all_issues,
                "metrics": {
                    "total_issues": len(all_issues),
                    "critical_issues": sum(
                        1 for i in all_issues if i["severity"] == "critical"
                    ),
                    "high_issues": sum(
                        1 for i in all_issues if i["severity"] == "high"
                    ),
                },
            }
        finally:
            # 一時ファイル削除
            Path(temp_path).unlink()


# デモ用関数
def demo_sonarqube_integration():
    """SonarQube統合のデモ"""
    print("🚀 SonarQube Integration Demo")

    # サンプルコード
    sample_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"]
    return total

# セキュリティ問題の例
import pickle
def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)  # Banditが検出

# 型の問題の例
def process_data(data: List[str]) -> int:
    return len(data) + "10"  # Mypyが検出
"""

    # レビュー実行
    compat = AutomatedCodeReviewCompat()
    results = compat.analyze_code_quality(sample_code)

    print(f"\n📊 Analysis Results:")
    print(f"Quality Score: {results['quality_score']}")
    print(f"Total Issues: {results['metrics']['total_issues']}")
    print(f"Critical Issues: {results['metrics']['critical_issues']}")
    print(f"High Issues: {results['metrics']['high_issues']}")

    print("\n📋 Issues Found:")
    for issue in results["issues"][:5]:  # 最初の5件
        print(f"- [{issue['severity']}] {issue['source']}: {issue['message']}")


if __name__ == "__main__":
    demo_sonarqube_integration()
