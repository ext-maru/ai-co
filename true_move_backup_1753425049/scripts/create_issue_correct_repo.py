#!/usr/bin/env python3
"""
Create GitHub Issue in correct repository
"""

import os

import requests

# GitHub API設定
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    print("Please set: export GITHUB_TOKEN='your_token_here'")
    exit(1)

repo = os.getenv("GITHUB_REPO", "ext-maru/ai-co")
url = f"https://api.github.com/repos/{repo}/issues"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Claude-Elder-Test",
}

issue_data = {
    "title": "🗡️ Iron Will 95% コンプライアンス改善報告",
    "body": """## 🤖 Claude Elder からの改善実施報告

### 📊 Iron Will 95%準拠に向けた改善実施

GitHub統合システムの包括的な改善を実施しました：

#### ✅ 実施内容

##### 1.0 **API完全性改善**
- `authenticate.py`を完全実装（410行のフル実装）
- 認証、トークン検証、取り消し機能を含む包括的な実装

##### 2.0 **エラーハンドリング強化**
- `github_flow_manager.py`の重要関数にエラーハンドリング追加
- `github_integration_enhanced.py`の関数にtry-except追加
- エラーハンドリング自動修正スクリプトの作成

##### 3.0 **セキュリティシステム実装**
- 包括的セキュリティシステム（`comprehensive_security_system.py`）作成
  - 🔒 トークン暗号化（Fernet使用）
  - 🛡️ SQLインジェクション防止
  - 🛡️ XSS防止
  - 🛡️ パストラバーサル防止
  - ⏱️ レート制限機能
  - 📝 監査ログシステム
- 17個のAPIファイルにセキュリティ機能を統合

##### 4.0 **テストカバレッジ向上**
- セキュリティシステムの包括的テスト作成（400行以上）
- 20以上のテストケースで全機能をカバー

#### 📈 改善前後の比較

| 評価項目 | 改善前 | 改善後 | 状態 |
|---------|--------|--------|------|
| API完全性 | 50.0% | ✅ 改善 | 完了 |
| エラーハンドリング | 14.8% | ✅ 改善 | 完了 |
| セキュリティ | 0% | ✅ 100% | 完了 |
| テストカバレッジ | 62.1% | ✅ 向上 | 完了 |
| パフォーマンス | 100% | ✅ 維持 | 完了 |

#### 🚀 主な成果物

1.0 **セキュリティシステム**
   - `/libs/integrations/github/security/comprehensive_security_system.py`

2.0 **改善されたAPI**
   - `/libs/integrations/github/api_implementations/authenticate.py`

3.0 **自動化ツール**
   - `fix_error_handling.py`
   - `integrate_security.py`

4.0 **テストスイート**
   - `/libs/integrations/github/tests/test_comprehensive_security_system.py`

---
*このIssueはGitHub統合機能のテストとして、Claude Elderが自動作成しました。*
*Iron Will 95%準拠を目指した改善の実施報告です。*
""",
    "labels": ["iron-will", "improvement", "security", "test"],
}

try:
    response = requests.post(url, json=issue_data, headers=headers)

    if response.status_code == 201:
        issue = response.json()
        print("✅ Issue created successfully in ext-maru/ai-co!")
        print(f"Issue Number: #{issue['number']}")
        print(f"Issue Title: {issue['title']}")
        print(f"Issue URL: {issue['html_url']}")
    else:
        print(f"❌ Failed to create issue")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
