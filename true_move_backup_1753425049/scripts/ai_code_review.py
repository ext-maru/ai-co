#!/usr/bin/env python3
"""
AI Code Review Tool
AIコードレビューツール
"""

import argparse
import os
import sys
import subprocess
from typing import List, Dict, Any
import json


class AICodeReviewer:
    """AIコードレビュークラス"""

    def __init__(self, pr_number: int, base_branch: str, head_branch: str):
        self.pr_number = pr_number
        self.base_branch = base_branch
        self.head_branch = head_branch
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        self.claude_api_key = os.environ.get("CLAUDE_API_KEY", "")

    def get_changed_files(self) -> List[str]:
        """変更されたファイルのリストを取得"""
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self.base_branch}...{self.head_branch}",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return [
                    f.strip() for f in result.stdout.strip().split("\n") if f.strip()
                ]
            else:
                return []
        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []

    def get_file_diff(self, file_path: str) -> str:
        """ファイルの差分を取得"""
        try:
            result = subprocess.run(
                [
                    "git",
                    "diff",
                    f"{self.base_branch}...{self.head_branch}",
                    "--",
                    file_path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return ""
        except Exception as e:
            print(f"Error getting diff for {file_path}: {e}")
            return ""

    def analyze_code_quality(self, file_path: str, diff: str) -> Dict[str, Any]:
        """コード品質の分析"""
        issues = []
        suggestions = []

        # Basic static analysis
        if file_path.endswith(".py"):
            # Check for common Python issues
            lines = diff.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("+"):
                    # Check for print statements
                    if "print(" in line and "debug" not in line.lower():
                        issues.append(
                            {
                                "line": i,
                                "type": "warning",
                                "message": "Consider using logging instead of print statements",
                            }
                        )

                    # Check for bare except
                    if "except:" in line:
                        issues.append(
                            {
                                "line": i,
                                "type": "error",
                                "message": "Avoid bare except clauses",
                            }
                        )

                    # Check for TODO comments
                    if "TODO" in line or "FIXME" in line:
                        issues.append(
                            {
                                "line": i,
                                "type": "info",
                                "message": "TODO/FIXME comment found",
                            }
                        )

        return {"file": file_path, "issues": issues, "suggestions": suggestions}

    def generate_review_summary(self, analyses: List[Dict[str, Any]]) -> str:
        """レビューサマリーを生成"""
        total_issues = sum(len(a["issues"]) for a in analyses)

        summary = f"""## 🤖 AI Code Review Summary

**Pull Request**: #{self.pr_number}
**Base**: {self.base_branch} → **Head**: {self.head_branch}

### 📊 Overview
- **Files Changed**: {len(analyses)}
- **Total Issues**: {total_issues}

### 📋 Issues by Type
"""

        # Count issues by type
        issue_counts = {"error": 0, "warning": 0, "info": 0}
        for analysis in analyses:
            for issue in analysis["issues"]:
                issue_type = issue.get("type", "info")
                issue_counts[issue_type] += 1

        summary += f"- 🔴 Errors: {issue_counts['error']}\n"
        summary += f"- 🟡 Warnings: {issue_counts['warning']}\n"
        summary += f"- 🔵 Info: {issue_counts['info']}\n\n"

        # Add file-specific issues
        if total_issues > 0:
            summary += "### 📝 Detailed Findings\n\n"

            for analysis in analyses:
                if analysis["issues"]:
                    summary += f"#### `{analysis['file']}`\n"
                    for issue in analysis["issues"]:
                        icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                            issue["type"], "🔵"
                        )
                        summary += (
                            f"- {icon} Line {issue['line']}: {issue['message']}\n"
                        )
                    summary += "\n"
        else:
            summary += "✅ No issues found! Great job!\n"

        # Add general suggestions
        summary += "\n### 💡 General Suggestions\n"
        summary += "- Ensure all new code has appropriate test coverage\n"
        summary += "- Follow the Elders Guild coding standards\n"
        summary += "- Update documentation if APIs have changed\n"

        return summary

    def run_review(self) -> str:
        """コードレビューを実行"""
        print(f"🤖 Starting AI code review for PR #{self.pr_number}")

        # Get changed files
        changed_files = self.get_changed_files()
        if not changed_files:
            return "No files changed in this PR."

        print(f"Found {len(changed_files)} changed files")

        # Analyze each file
        analyses = []
        for file_path in changed_files:
            # Skip non-code files
            if not any(
                file_path.endswith(ext) for ext in [".py", ".js", ".ts", ".jsx", ".tsx"]
            ):
                continue

            print(f"Analyzing {file_path}...")
            diff = self.get_file_diff(file_path)
            if diff:
                analysis = self.analyze_code_quality(file_path, diff)
                analyses.append(analysis)

        # Generate summary
        summary = self.generate_review_summary(analyses)

        return summary


def main():
    """mainメソッド"""
    parser = argparse.ArgumentParser(description="AI-powered code review")
    parser.add_argument(
        "--pr-number", type=int, required=True, help="Pull request number"
    )
    parser.add_argument("--base-branch", required=True, help="Base branch")
    parser.add_argument("--head-branch", required=True, help="Head branch")
    parser.add_argument("--output", help="Output file for review summary")

    args = parser.parse_args()

    reviewer = AICodeReviewer(args.pr_number, args.base_branch, args.head_branch)
    summary = reviewer.run_review()

    if args.output:
        with open(args.output, "w") as f:
            f.write(summary)
        print(f"✅ Review summary saved to {args.output}")
    else:
        print("\n" + summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
