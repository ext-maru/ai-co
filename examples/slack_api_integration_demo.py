#!/usr/bin/env python3
"""
Slack API Integration Demo Script
AI Company Slack API統合システムのデモンストレーション
"""

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.slack_api_integration import (
    create_slack_integration, SlackMessage, SlackMessageType,
    format_code_block, format_user_mention, format_channel_mention
)

async def basic_demo():
    """基本機能のデモ"""
    print("🚀 AI Company Slack API Integration Demo")
    print("=" * 50)
    
    # Slack統合システムの作成
    slack = await create_slack_integration()
    print("✅ Slack integration system created")
    
    # 接続テスト
    print("\n🔗 Testing connection...")
    test_results = await slack.test_connection()
    
    print("Connection Test Results:")
    for key, value in test_results.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")
    
    if not any(test_results.values()):
        print("\n⚠️  No valid Slack configuration found")
        print("Please set up environment variables or config file:")
        print("  - SLACK_BOT_TOKEN=xoxb-your-token")
        print("  - SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")
        return False
    
    return True

async def message_demo(slack):
    """メッセージ送信のデモ"""
    print("\n📨 Message Sending Demo")
    print("-" * 30)
    
    # 基本メッセージ
    print("Sending basic message...")
    message = SlackMessage(
        channel="general",
        text="Hello from AI Company! 🤖"
    )
    
    # 実際の送信はコメントアウト（テスト環境保護）
    # result = await slack.send_message(message)
    print("✅ Basic message prepared")
    
    # Block Kit メッセージ
    print("Creating Block Kit message...")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "AI Company System Status"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Status:* All systems operational ✅\n*Uptime:* 99.9%\n*Last Update:* 2025-07-09"
            }
        }
    ]
    
    block_message = SlackMessage(
        channel="general",
        text="System Status Update",  # フォールバック
        message_type=SlackMessageType.BLOCKS,
        blocks=blocks
    )
    print("✅ Block Kit message prepared")

async def format_demo():
    """フォーマット機能のデモ"""
    print("\n🎨 Formatting Demo")
    print("-" * 20)
    
    # コードブロック
    code = """
def hello_world():
    print("Hello from AI Company!")
    return "Success"
"""
    formatted_code = format_code_block(code, "python")
    print("Code block formatted:")
    print(formatted_code)
    
    # メンション
    user_mention = format_user_mention("U1234567890")
    channel_mention = format_channel_mention("C1234567890")
    print(f"User mention: {user_mention}")
    print(f"Channel mention: {channel_mention}")

async def sages_demo(slack):
    """4賢者システム連携のデモ"""
    print("\n🧙‍♂️ 4 Sages System Demo")
    print("-" * 25)
    
    sages = [
        ("Knowledge Sage", "New knowledge base article added: 'Slack Integration Best Practices'"),
        ("Task Oracle", "Task #12345 completed successfully - Slack API implementation"),
        ("Crisis Sage", "System alert: All monitoring systems are green"),
        ("Search Mystic", "RAG search optimization completed - 15% improvement in response time")
    ]
    
    for sage_type, message in sages:
        print(f"Preparing notification for {sage_type}...")
        # 実際の送信はコメントアウト
        # await slack.send_4sages_notification(sage_type, message, "normal")
        print(f"  📩 {sage_type}: {message[:50]}...")
    
    print("✅ All sage notifications prepared")

async def error_demo(slack):
    """エラーアラートのデモ"""
    print("\n🚨 Error Alert Demo")
    print("-" * 20)
    
    # テストエラーの作成
    try:
        # 意図的なエラー
        raise ValueError("This is a demo error for testing")
    except Exception as e:
        print(f"Caught error: {e}")
        
        # エラーアラート準備
        context = {
            'module': 'slack_demo',
            'function': 'error_demo',
            'user': 'claude_elder',
            'demo': True
        }
        
        print("Preparing error alert...")
        # 実際の送信はコメントアウト
        # await slack.send_error_alert(e, context)
        print("✅ Error alert prepared")

async def webhook_demo(slack):
    """Webhook デモ"""
    print("\n🪝 Webhook Demo")
    print("-" * 15)
    
    if not slack.webhook_url:
        print("❌ Webhook URL not configured")
        return
    
    print("Preparing webhook message...")
    # 実際の送信はコメントアウト
    # success = await slack.send_webhook_message(
    #     "🚀 AI Company Demo: Webhook integration test successful!"
    # )
    print("✅ Webhook message prepared")

async def history_demo(slack):
    """履歴管理のデモ"""
    print("\n📊 Message History Demo")
    print("-" * 25)
    
    # いくつかのダミー履歴を追加
    for i in range(5):
        slack.message_history.append({
            'timestamp': f'2025-07-09T12:{i:02d}:00',
            'channel': 'C1234567890',
            'message': f'Demo message {i+1}',
            'success': True,
            'ts': f'1720512000.{i+1:06d}',
            'message_type': 'text'
        })
    
    # 履歴取得
    history = await slack.get_message_history(3)
    print("Recent message history:")
    for entry in history:
        status = "✅" if entry['success'] else "❌"
        print(f"  {status} {entry['timestamp']}: {entry['message']}")

async def performance_demo():
    """パフォーマンス・設定のデモ"""
    print("\n⚡ Performance & Configuration Demo")
    print("-" * 35)
    
    # カスタム設定でインスタンス作成
    custom_config = {
        'rate_limit_per_minute': 30,
        'max_retries': 5,
        'max_history_size': 500,
        'sage_integration': True,
        'auto_escalation': True
    }
    
    custom_slack = await create_slack_integration(custom_config)
    print("✅ Custom configuration applied:")
    print(f"  Rate limit: {custom_slack.rate_limit_per_minute}/min")
    print(f"  Max retries: {custom_slack.max_retries}")
    print(f"  History size: {custom_slack.max_history_size}")
    print(f"  Sage integration: {custom_slack.sage_integration}")

async def main():
    """メインデモ実行"""
    try:
        # 基本接続テスト
        connection_ok = await basic_demo()
        
        # Slack統合システム作成
        slack = await create_slack_integration()
        
        # 各種デモ実行
        await message_demo(slack)
        await format_demo()
        await sages_demo(slack)
        await error_demo(slack)
        await webhook_demo(slack)
        await history_demo(slack)
        await performance_demo()
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"Slack API Integration System is ready for production use.")
        
        if connection_ok:
            print(f"\n💡 To send actual messages, uncomment the send methods in this demo.")
        else:
            print(f"\n💡 Configure Slack credentials to enable actual message sending.")
    
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("AI Company Slack API Integration Demo")
    print("Starting demo in 3 seconds...")
    
    import time
    time.sleep(1)
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    
    # Python 3.7+ 対応
    if sys.version_info >= (3, 7):
        asyncio.run(main())
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())