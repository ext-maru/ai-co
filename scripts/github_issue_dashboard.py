#!/usr/bin/env python3
"""
GitHub Issue Dashboard for Elder Guild
Sub Issue進捗管理とコメント閲覧の改善
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional


class GitHubIssueDashboard:
    def __init__(self):
    """GitHubIssueDashboardクラス"""
        self.repo = "ext-maru/ai-co"

    def get_issue_with_comments(self, issue_number: int) -> Dict:
        """Issue情報をコメント付きで取得"""
        try:
            # Issue本体の情報
            issue_result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "title,body,number,state,labels,assignees,author,createdAt",
                ],
                capture_output=True,
                text=True,
            )

            issue_data = json.loads(issue_result.stdout)

            # コメントの情報
            comments_result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "view",
                    str(issue_number),
                    "--comments",
                    "--json",
                    "comments",
                ],
                capture_output=True,
                text=True,
            )

            comments_data = json.loads(comments_result.stdout)
            issue_data["comments"] = comments_data.get("comments", [])

            return issue_data

        except Exception as e:
            print(f"❌ Error fetching issue {issue_number}: {e}")
            return {}

    def display_issue_dashboard(self, issue_number: int)issue = self.get_issue_with_comments(issue_number)
    """Issue情報を見やすく表示"""
        if not issue:
            return

        print(f"\n🏛️ Issue #{issue['number']}: {issue['title']}")
        print(f"📊 状態: {issue['state']}")
        print(f"👤 作成者: {issue['author']['login']}")
        print(f"📅 作成日: {issue['createdAt']}")

        # ラベル表示
        if issue["labels"]:
            labels = [label["name"] for label in issue["labels"]]
            print(f"🏷️ ラベル: {', '.join(labels)}")

        # 本文表示
        print(f"\n📝 本文:")
        print("=" * 50)
        print(issue["body"])

        # コメント表示
        if issue["comments"]:
            print(f"\n💬 コメント ({len(issue['comments'])}件):")
            print("=" * 50)

            for i, comment in enumerate(issue["comments"], 1):
                print(f"\n[{i}] {comment['author']['login']} - {comment['createdAt']}")
                print("-" * 30)
                print(comment["body"])

                # 進捗キーワードをハイライト
                if any(
                    keyword in comment["body"]
                    for keyword in ["完了", "進行中", "開始", "%"]
                ):
                    print("📈 進捗情報あり")
        else:
            print("\n💬 コメントなし")

    def get_master_issue_progress(self, master_issue_number: int) -> Dictissue = self.get_issue_with_comments(master_issue_number):
    """aster Issueの進捗を分析""":
        if not issue:
            return {}

        progress_data = {
            "total_sub_issues": 0,
            "completed_sub_issues": 0,
            "in_progress_sub_issues": 0,
            "pending_sub_issues": 0,
            "progress_percentage": 0,
        }

        # 本文とコメントから進捗情報を抽出
        all_text = issue["body"] + "\n"
        for comment in issue["comments"]:
            all_text += comment["body"] + "\n"

        # Sub Issueの参照を検索
        import re

        sub_issue_refs = re.findall(r"#(\d+)", all_text)

        for ref in sub_issue_refs:
            try:
                sub_issue_num = int(ref)
                if sub_issue_num != master_issue_number:  # Master Issue自体を除外
                    progress_data["total_sub_issues"] += 1

                    # Sub Issueの状態を確認
                    sub_issue = self.get_issue_with_comments(sub_issue_num)
                    if sub_issue:
                        if sub_issue["state"] == "CLOSED":
                            progress_data["completed_sub_issues"] += 1
                        elif "進行中" in all_text or "in-progress" in str(
                            sub_issue.get("labels", [])
                        ):
                            progress_data["in_progress_sub_issues"] += 1
                        else:
                            progress_data["pending_sub_issues"] += 1
            except:
                continue

        if progress_data["total_sub_issues"] > 0:
            progress_data["progress_percentage"] = (
                progress_data["completed_sub_issues"]
                / progress_data["total_sub_issues"]
                * 100
            )

        return progress_data

    def display_master_issue_dashboard(self, master_issue_number: int)print(f"\n🏛️ Master Issue Dashboard - #{master_issue_number}")
    """Master Issue専用ダッシュボード"""
        print("=" * 60)

        # 基本情報表示
        self.display_issue_dashboard(master_issue_number)

        # 進捗分析
        progress = self.get_master_issue_progress(master_issue_number)

        print(f"\n📊 進捗分析:")
        print(f"総Sub Issue数: {progress['total_sub_issues']}")
        print(f"完了: {progress['completed_sub_issues']}")
        print(f"進行中: {progress['in_progress_sub_issues']}")
        print(f"待機中: {progress['pending_sub_issues']}")
        print(f"完了率: {progress['progress_percentage']:0.1f}%")

        # プログレスバー
        completed = progress["completed_sub_issues"]
        total = progress["total_sub_issues"]
        if total > 0:
            bar_length = 30
            filled_length = int(bar_length * completed / total)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)
            print(f"進捗: [{bar}] {completed}/{total}")


def main()dashboard = GitHubIssueDashboard()
"""mainメソッド"""

    if len(sys.argv) < 2:
        print("使用方法:")
        print("python3 github_issue_dashboard.py <issue_number>")
        print("python3 github_issue_dashboard.py master <master_issue_number>")
        return

    if sys.argv[1] == "master":
        if len(sys.argv) < 3:
            print("Master Issue番号を指定してください")
            return
        dashboard.display_master_issue_dashboard(int(sys.argv[2]))
    else:
        dashboard.display_issue_dashboard(int(sys.argv[1]))


if __name__ == "__main__":
    main()
