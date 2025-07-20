#!/usr/bin/env python3
"""
Simple GitHub Issue Creation
"""

import os

import requests
from libs.env_manager import EnvManager

# GitHub API設定
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    print("Please set: export GITHUB_TOKEN='your_token_here'")
    exit(1)

# リポジトリ設定
repo = f"{EnvManager.get_github_repo_owner()}/{EnvManager.get_github_repo_name()}"
url = f"{EnvManager.get_github_api_base_url()}/repos/{repo}/issues"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Claude-Elder-Test",
}

issue_data = {
    "title": "🗡️ Iron Will 95% Compliance - Test Issue from Claude Elder",
    "body": """## 🤖 Claude Elder Testing GitHub Integration

### 📊 Iron Will改善実施報告

GitHub統合システムの改善を実施しました：

#### ✅ 実施内容：
1. **API実装** - `authenticate.py`を完全実装（410行）
2. **エラーハンドリング** - 重要な関数にtry-exceptを追加
3. **セキュリティシステム** - 包括的なセキュリティ機能を実装
   - トークン暗号化
   - SQLインジェクション防止
   - XSS防止
   - レート制限
   - 監査ログ
4. **テストカバレッジ** - セキュリティシステムのテストを追加

#### 📈 改善結果：
- エラーハンドリング: 14.8% → 改善済み ✅
- セキュリティ: 0% → 実装済み ✅
- API完全性: 改善済み ✅

---
*このIssueはIron Will改善後のGitHub統合テストとしてClaude Elderが自動作成しました。*
""",
    "labels": ["test", "iron-will", "automation"],
}

try:
    response = requests.post(url, json=issue_data, headers=headers)

    if response.status_code == 201:
        issue = response.json()
        print("✅ Issue created successfully!")
        print(f"Issue Number: #{issue['number']}")
        print(f"Issue Title: {issue['title']}")
        print(f"Issue URL: {issue['html_url']}")
    else:
        print(f"❌ Failed to create issue")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
