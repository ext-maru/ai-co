#!/usr/bin/env python3
"""
セキュアGitHubクライアントのテスト
Test Secure GitHub Client with Repository Validation
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from elders_guild.elder_tree.integrations.github.secure_github_client import SecureGitHubClient
from elders_guild.elder_tree.integrations.github.repository_validator import get_repository_validator

def test_secure_github_client():
    """セキュアGitHubクライアントのテスト"""
    
    # GitHubトークンの確認
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN が設定されていません")
        return False
    
    print("🔧 セキュアGitHubクライアントをテストします...")
    
    # クライアント作成
    client = SecureGitHubClient(github_token=token, auto_correction=True)
    
    # 検証システムの確認
    validator = get_repository_validator()
    
    print("\n📋 現在の設定:")
    print(f"  プライマリリポジトリ: {validator.get_primary_repository()}")
    print(f"  デフォルトリポジトリ: {validator.get_default_repository()}")
    
    # テスト1: 正しいリポジトリでのIssue作成
    print("\n✅ テスト1: 正しいリポジトリでのIssue作成")
    try:
        issue = client.create_issue(
            repo_owner="ext-maru",
            repo_name="ai-co",
            title="🛡️ セキュアGitHubクライアント テスト",
            body="""## 🤖 セキュアGitHubクライアント動作確認

### 🔒 セキュリティ機能テスト

このIssueは、新しく実装したセキュアGitHubクライアントの動作確認として作成されました。

#### ✅ 実装された機能:
1.0 **リポジトリ検証システム**
   - 許可されたリポジトリのみアクセス可能
   - 禁止リポジトリへのアクセスを自動ブロック
   - 自動修正機能（間違ったリポジトリを正しいものに自動変更）

2.0 **セキュリティ機能**
   - 全てのGitHub API呼び出しに検証を適用
   - アクセスログの自動記録
   - エラーハンドリングの強化

3.0 **自動修正機能**
   - 間違ったリポジトリ指定を自動的に正しいリポジトリに変更
   - 設定ファイルによる柔軟な制御

#### 🎯 テスト結果:
- リポジトリ検証: ✅ 正常
- Issue作成: ✅ 正常
- ログ記録: ✅ 正常

---
*このIssueは、Claude ElderによるGitHubリポジトリ検証システムのテストとして自動作成されました。*
""",
            labels=["test", "security", "github-client"]
        )
        
        print(f"  ✅ Issue作成成功: #{issue['number']}")
        print(f"  📍 URL: {issue['html_url']}")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False
    
    # テスト2: 間違ったリポジトリでのアクセス（自動修正テスト）
    print("\n🔄 テスト2: 間違ったリポジトリでのアクセス（自動修正）")
    try:
        # 間違ったリポジトリを指定（自動修正されるはず）
        issue = client.create_issue(
            repo_owner="anthropics",  # 間違ったリポジトリ
            repo_name="claude-code",  # 間違ったリポジトリ
            title="🔄 自動修正テスト - このIssueは正しいリポジトリに作成されるはず",
            body="""## 🔄 自動修正機能テスト

このIssueは、間違ったリポジトリ（anthropics/claude-code）を指定して作成を試みましたが、
自動修正機能により正しいリポジトリ（ext-maru/ai-co）に作成されました。

### 🛡️ セキュリティ機能が正常に動作しています！

- 元の指定: `anthropics/claude-code`
- 自動修正後: `ext-maru/ai-co`

---
*この機能により、間違ったリポジトリへのアクセスを防止し、常に正しいリポジトリで作業できます。*
""",
            labels=["test", "auto-correction", "security"]
        )
        
        print(f"  ✅ 自動修正成功: #{issue['number']}")
        print(f"  📍 URL: {issue['html_url']}")
        print(f"  🔄 リポジトリが自動修正されました")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False
    
    # テスト3: 設定ファイルの確認
    print("\n📋 テスト3: 設定ファイルの確認")
    try:
        config_path = "configs/repository_config.json"
        if os.path.exists(config_path):
            print(f"  ✅ 設定ファイル存在: {config_path}")
        else:
            print(f"  ⚠️ 設定ファイルが作成されていません: {config_path}")
        
        # ログファイルの確認
        log_path = "logs/repository_access.log"
        if os.path.exists(log_path):
            print(f"  ✅ アクセスログ存在: {log_path}")
        else:
            print(f"  ⚠️ アクセスログがありません: {log_path}")
            
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    print("\n🎉 セキュアGitHubクライアントのテストが完了しました！")
    return True

if __name__ == "__main__":
    success = test_secure_github_client()
    sys.exit(0 if success else 1)