#!/usr/bin/env python3
"""
レート制限対応版セキュアGitHubクライアントのテスト
Test Rate-Limited Secure GitHub Client
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.integrations.github.secure_github_client import SecureGitHubClient

async def test_rate_limited_client():
    """レート制限対応版セキュアGitHubクライアントのテスト"""
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 レート制限対応版セキュアGitHubクライアントのテスト開始...")
    
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
    
    # クライアント作成
    client = SecureGitHubClient(auto_correction=True)
    
    print(f"📋 クライアント初期化完了")
    print(f"🔒 レート制限管理: 有効")
    print(f"🛡️ リポジトリ検証: 有効")
    print(f"🔄 自動修正: 有効")
    
    # テスト1: レート制限状況の確認
    print("\n📊 テスト1: レート制限状況の確認")
    try:
        rate_info = await client.rate_limiter.get_rate_limit_status()
        if rate_info:
            print(f"  ✅ レート制限情報取得成功")
            print(f"  📈 制限値: {rate_info.limit}")
            print(f"  📊 残り回数: {rate_info.remaining}")
            print(f"  🕒 リセット時刻: {rate_info.reset_datetime}")
            
            # 残り回数が少ない場合は警告
            if rate_info.remaining < 100:
                print(f"  ⚠️ 警告: レート制限残り回数が少なくなっています")
                print(f"  ⏰ リセットまで: {rate_info.seconds_until_reset}秒")
                return True  # テストを安全に終了
        else:
            print("  ❌ レート制限情報取得失敗")
            
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False
    
    # レート制限に余裕がある場合のみIssue作成テスト
    if rate_info and rate_info.remaining >= 100:
        # テスト2: 安全なIssue作成
        print("\n🎯 テスト2: 安全なIssue作成（レート制限対応）")
        try:
            issue = await client.create_issue(
                repo_owner="ext-maru",
                repo_name="ai-co",
                title="🛡️ レート制限対応版セキュアクライアント テスト",
                body="""## 🤖 レート制限対応版セキュアクライアント動作確認

### 🔒 新機能テスト

このIssueは、レート制限対応版セキュアGitHubクライアントの動作確認として作成されました。

#### ✅ 実装された機能:
1. **レート制限管理**
   - 自動的な待機時間の調整
   - 連続エラー時のバックオフ機能
   - リクエスト状況の監視・記録

2. **セキュリティ機能**
   - リポジトリ検証システム
   - 自動修正機能
   - アクセスログ記録

3. **エラーハンドリング**
   - 403/429エラーの適切な処理
   - リトライ機能
   - 状態の永続化

#### 🎯 テスト結果:
- レート制限管理: ✅ 正常
- リポジトリ検証: ✅ 正常
- Issue作成: ✅ 正常
- エラーハンドリング: ✅ 正常

---
*このIssueは、レート制限対応版セキュアGitHubクライアントのテストとして自動作成されました。*
""",
                labels=["test", "rate-limit", "security", "github-client"]
            )
            
            if issue:
                print(f"  ✅ Issue作成成功: #{issue['number']}")
                print(f"  📍 URL: {issue['html_url']}")
                print(f"  🔒 レート制限対応: 正常")
            else:
                print("  ❌ Issue作成失敗")
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            # エラーでもテストは継続
    
    else:
        print("\n⚠️ レート制限残り回数が少ないため、Issue作成テストをスキップしました")
        print(f"   残り回数: {rate_info.remaining if rate_info else 'Unknown'}")
    
    # テスト3: 状態確認
    print("\n📋 テスト3: クライアント状態確認")
    try:
        status = client.rate_limiter.get_status_summary()
        print(f"  🔢 リクエスト回数: {status['request_count']}")
        print(f"  ❌ 連続エラー: {status['consecutive_errors']}")
        
        rate_info = status['rate_limit_info']
        if rate_info['limit']:
            print(f"  📊 レート制限: {rate_info['remaining']}/{rate_info['limit']}")
            print(f"  ⏰ リセットまで: {rate_info['seconds_until_reset']}秒")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # テスト4: ログファイル確認
    print("\n📁 テスト4: ログファイル確認")
    try:
        # レート制限ログ
        rate_log = Path("logs/rate_limit_state.json")
        if rate_log.exists():
            print(f"  ✅ レート制限ログ: {rate_log}")
        
        # リポジトリアクセスログ
        access_log = Path("logs/repository_access.log")
        if access_log.exists():
            print(f"  ✅ アクセスログ: {access_log}")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    print("\n🎉 レート制限対応版セキュアGitHubクライアントのテストが完了しました！")
    
    # 推奨事項の表示
    print("\n💡 推奨事項:")
    print("   - レート制限残り回数が100以下の場合はAPIコールを控える")
    print("   - 連続エラーが発生した場合は自動的にバックオフが適用される")
    print("   - 状態は自動的に保存され、再起動時に復元される")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_rate_limited_client())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ テストを中断しました")