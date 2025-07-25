#!/usr/bin/env python3
"""
GitHub APIレート制限管理システムのテスト
Test GitHub API Rate Limiter System
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from libs.integrations.github.rate_limiter import GitHubRateLimiter, get_rate_limiter, safe_github_request

async def test_rate_limiter():
    """レート制限管理システムのテスト"""
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 GitHub APIレート制限管理システムのテスト開始...")
    
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
    
    # レート制限管理インスタンス作成
    limiter = get_rate_limiter()
    
    print(f"📊 レート制限管理システム初期化完了")
    
    # テスト1: レート制限状況の取得
    print("\n🔍 テスト1: レート制限状況の取得")
    try:
        rate_info = await limiter.get_rate_limit_status()
        if rate_info:
            print(f"  ✅ レート制限情報取得成功")
            print(f"  📈 制限値: {rate_info.limit}")
            print(f"  📊 残り回数: {rate_info.remaining}")
            print(f"  🕒 リセット時刻: {rate_info.reset_datetime}")
            print(f"  ⏰ リセットまで: {rate_info.seconds_until_reset}秒")
        else:
            print("  ❌ レート制限情報取得失敗")
            return False
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False
    
    # テスト2: 安全なリクエストの実行
    print("\n🛡️ テスト2: 安全なリクエスト実行")
    try:
        # 比較的安全なエンドポイントをテスト
        response = await safe_github_request("GET", "https://api.github.com/user")
        
        if response and response.status_code == 200:
            user_data = response.json()
            print(f"  ✅ 安全なリクエスト成功")
            print(f"  👤 ユーザー: {user_data.get('login', 'Unknown')}")
            print(f"  📊 レスポンス: {response.status_code}")
        else:
            print("  ⚠️ リクエスト失敗またはレート制限")
            if response:
                print(f"  📊 ステータス: {response.status_code}")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # テスト3: レート制限状況の再確認
    print("\n🔄 テスト3: レート制限状況の再確認")
    try:
        rate_info = await limiter.get_rate_limit_status()
        if rate_info:
            print(f"  ✅ 更新後のレート制限情報")
            print(f"  📈 制限値: {rate_info.limit}")
            print(f"  📊 残り回数: {rate_info.remaining}")
            print(f"  🕒 リセット時刻: {rate_info.reset_datetime}")
        else:
            print("  ❌ レート制限情報取得失敗")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # テスト4: 状況サマリーの表示
    print("\n📋 テスト4: 状況サマリー")
    try:
        status = limiter.get_status_summary()
        print(f"  🔢 リクエスト回数: {status['request_count']}")
        print(f"  ❌ 連続エラー: {status['consecutive_errors']}")
        print(f"  🕒 最終リクエスト時刻: {status['last_request_time']}")
        
        rate_info = status['rate_limit_info']
        if rate_info['limit']:
            print(f"  📊 レート制限: {rate_info['remaining']}/{rate_info['limit']}")
            print(f"  ⏰ リセットまで: {rate_info['seconds_until_reset']}秒")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # テスト5: 状態ファイルの確認
    print("\n📁 テスト5: 状態ファイル確認")
    try:
        state_file = limiter.state_file
        if state_file.exists():
            print(f"  ✅ 状態ファイル存在: {state_file}")
            print(f"  📊 ファイルサイズ: {state_file.stat().st_size} bytes")
        else:
            print(f"  ⚠️ 状態ファイル未作成: {state_file}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    print("\n🎉 レート制限管理システムのテストが完了しました！")
    
    # 制限に近づいている場合の警告
    if rate_info and rate_info.remaining < 100:
        print(f"\n⚠️ 警告: レート制限残り回数が少なくなっています ({rate_info.remaining}回)")
        print(f"   しばらく待機することをお勧めします")
    
    return True

async def test_backoff_mechanism():
    """バックオフメカニズムのテスト"""
    print("\n🔄 バックオフメカニズムのテスト")
    
    limiter = get_rate_limiter()
    
    # 連続エラーをシミュレート
    original_errors = limiter.consecutive_errors
    limiter.consecutive_errors = 2
    
    print(f"  📊 連続エラー数を{limiter.consecutive_errors}に設定")
    
    start_time = asyncio.get_event_loop().time()
    await limiter.wait_if_needed()
    end_time = asyncio.get_event_loop().time()
    
    wait_time = end_time - start_time
    print(f"  ⏰ バックオフ待機時間: {wait_time:0.2f}秒")
    
    # 元に戻す
    limiter.consecutive_errors = original_errors
    
    return wait_time > 0

if __name__ == "__main__":
    async def main():
        """メイン処理"""
        print("🚀 GitHub APIレート制限管理システム テストスイート\n")
        
        # 基本テスト
        success = await test_rate_limiter()
        
        if success:
            # バックオフメカニズムテスト
            await test_backoff_mechanism()
            
            print("\n✅ すべてのテストが正常に完了しました！")
            print("\n💡 レート制限管理システムの使用方法:")
            print("   from libs.integrations.github.rate_limiter import safe_github_request")
            print("   response = await safe_github_request('GET', 'https://api.github.com/user')")
        else:
            print("\n❌ テストが失敗しました")
        
        return success
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ テストを中断しました")