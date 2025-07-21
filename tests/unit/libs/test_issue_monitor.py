#!/usr/bin/env python3
"""
GitHub Issue監視システムのテスト
Test GitHub Issue Monitor System
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.integrations.github.issue_monitor import GitHubIssueMonitor, get_issue_monitor
from libs.integrations.github.secure_github_client import get_secure_github_client

async def test_issue_monitor():
    """Issue監視システムのテスト"""
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 GitHub Issue監視システムのテストを開始...")
    
    # 環境変数設定
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    if not os.getenv('GITHUB_TOKEN'):
        print("❌ GITHUB_TOKEN が設定されていません")
        return False
    
    # モニター作成
    monitor = get_issue_monitor()
    
    print(f"📋 監視対象: {monitor.repo_owner}/{monitor.repo_name}")
    print(f"⏰ チェック間隔: {monitor.check_interval}秒")
    
    # テスト用Issue作成
    print("\n🎯 テスト用Issue作成...")
    client = get_secure_github_client()
    
    try:
        test_issue = client.create_issue(
            repo_owner="ext-maru",
            repo_name="ai-co",
            title="🤖 Issue監視システム テスト",
            body="""## 🔧 Issue監視システム動作テスト

このIssueは、GitHub Issue監視システムの動作をテストするために作成されました。

### 📋 テスト予定項目:
1. **コメント検出**: 新しいコメントの自動検出
2. **コマンド解析**: コメント内のコマンドの自動解析
3. **自動応答**: コマンドに応じた自動実行・応答
4. **状態管理**: 処理済みコメントの管理

### 🎯 使用方法:
以下のようなコメントをしてみてください：
- `implement OAuth認証` - 実装コマンド
- `fix バグ修正` - 修正コマンド
- `test 動作確認` - テストコマンド
- `これはどうですか？` - 質問
- `OK` - 承認
- `NO` - 拒否

---
*このIssueは自動監視システムのテストです。コメントすると自動応答します。*
""",
            labels=["test", "automation", "issue-monitor"]
        )
        
        issue_number = test_issue['number']
        print(f"✅ テスト用Issue作成成功: #{issue_number}")
        print(f"🌐 URL: {test_issue['html_url']}")
        
        # 短時間の監視テスト
        print("\n🎯 短時間監視テストを開始...")
        print("💬 上記のIssueにコメントを追加してください（30秒間監視）")
        
        # 30秒間の監視
        monitor.check_interval = 5  # 5秒間隔でチェック
        
        async def limited_monitoring():
            """制限付き監視"""
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < 30:
                await monitor._check_issues()
                await asyncio.sleep(5)
        
        await limited_monitoring()
        
        print("✅ 30秒間の監視テストが完了しました")
        
        # 状態確認
        print(f"\n📊 監視状態:")
        print(f"  処理済みコメント数: {len(monitor.processed_comments)}")
        print(f"  最終チェック時刻: {monitor.last_check_time}")
        
        # 状態ファイル確認
        if monitor.state_file.exists():
            print(f"  状態ファイル: {monitor.state_file} (存在)")
        else:
            print(f"  状態ファイル: {monitor.state_file} (未作成)")
        
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False

async def test_comment_parsing():
    """コメント解析のテスト"""
    print("\n🔍 コメント解析テスト...")
    
    monitor = get_issue_monitor()
    
    test_comments = [
        "implement OAuth認証システム",
        "fix この部分のバグ",
        "test 動作確認をお願いします",
        "これはどうですか？",
        "OK, 承認します",
        "NO, やり直してください",
        "document APIの使用方法",
        "普通のコメントです"
    ]
    
    for comment in test_comments:
        command = monitor._parse_comment(comment)
        if command:
            print(f"  📝 '{comment}' → {command['type']}: {command['text']}")
        else:
            print(f"  📝 '{comment}' → コマンドなし")
    
    print("✅ コメント解析テスト完了")

if __name__ == "__main__":
    async def main():
        """メイン処理"""
        print("🚀 GitHub Issue監視システム テストスイート\n")
        
        # コメント解析テスト
        await test_comment_parsing()
        
        # 実際の監視テスト
        success = await test_issue_monitor()
        
        if success:
            print("\n🎉 すべてのテストが完了しました！")
            print("\n💡 継続的な監視を開始するには:")
            print("   python libs/integrations/github/issue_monitor.py")
        else:
            print("\n❌ テストが失敗しました")
        
        return success
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ テストを中断しました")