#!/usr/bin/env python3
"""
Close GitHub Issue
"""

import os
import sys

import requests

# GitHub API設定
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    print("Please set: export GITHUB_TOKEN='your_token_here'")
    exit(1)

# コマンドライン引数からIssue番号を取得
if len(sys.argv) < 2:
    print("Usage: python close_github_issue.py <issue_number>")
    exit(1)

issue_number = int(sys.argv[1])
repo = os.getenv("GITHUB_REPO", "ext-maru/ai-co")
url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Claude-Elder-Test",
}

# Issueをクローズする
close_data = {"state": "closed"}

try:
    response = requests.patch(url, json=close_data, headers=headers)

    if response.status_code == 200:
        print(f"✅ Issue #{issue_number} closed successfully!")
    else:
        print(f"❌ Failed to close issue")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")

# コメントを追加（オプション）
comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
comment_data = {"body": "Issue closed via CLI tool."}

try:
    response = requests.post(comment_url, json=comment_data, headers=headers)
    if response.status_code == 201:
        print("✅ Apology comment added")
except:
    pass
