#!/usr/bin/env python3
import sys
import os
import requests
sys.path.append('/root/ai_co')

def debug_slack_notification():
    """Slack通知のデバッグ"""
    print("=== 📱 Slack通知デバッグ開始 ===\n")
    
    # 1. 設定ファイル直接読み込み
    config = {}
    config_file = '/root/ai_co/config/slack.conf'
    
    if os.path.exists(config_file):
        print(f"✅ 設定ファイル発見: {config_file}")
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        print("\n📋 読み込んだ設定:")
        for k, v in config.items():
            if 'WEBHOOK' in k:
                print(f"  {k}: [HIDDEN]")
            else:
                print(f"  {k}: {v}")
    else:
        print("❌ 設定ファイルが見つかりません")
        return
    
    # 2. Webhook URLの検証
    webhook_url = config.get('SLACK_WEBHOOK_URL', '')
    if not webhook_url or webhook_url == 'YOUR_WEBHOOK_URL_HERE':
        print("\n❌ 有効なWebhook URLが設定されていません")
        print("設定方法:")
        print("1. Slackワークスペースで Incoming Webhooks を有効化")
        print("2. Webhook URLを取得")
        print("3. /root/ai_co/config/slack.conf に設定")
        return
    
    # 3. 実際にSlackに送信テスト
    print("\n🚀 実際のSlack送信テスト...")
    
    test_message = {
        "channel": config.get('SLACK_CHANNEL', '#general'),
        "username": config.get('SLACK_USERNAME', 'AI-Company-Bot'),
        "text": "🧪 AI Company Slack通知テスト\n\nこのメッセージが表示されれば、Slack通知は正常に動作しています！",
        "icon_emoji": ":robot_face:"
    }
    
    try:
        response = requests.post(webhook_url, json=test_message, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200 and response.text == 'ok':
            print("\n✅ Slack送信成功！Slackチャンネルを確認してください。")
        else:
            print("\n❌ Slack送信失敗")
            print("考えられる原因:")
            print("- Webhook URLが無効")
            print("- チャンネルが存在しない")
            print("- Slackワークスペースの設定問題")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 送信エラー: {e}")
        print("ネットワーク接続を確認してください")
    
    # 4. SlackNotifierクラスの動作確認
    print("\n📦 SlackNotifierクラステスト:")
    try:
        from libs.slack_notifier import SlackNotifier
        notifier = SlackNotifier()
        
        # 内部状態確認
        print(f"Enabled: {getattr(notifier, 'enabled', 'Unknown')}")
        print(f"Has webhook: {bool(getattr(notifier, 'webhook_url', None))}")
        
        # 実際の送信メソッドテスト
        result = notifier.send_notification("AI Company SlackNotifierクラス経由のテスト")
        print(f"送信結果: {result}")
        
    except Exception as e:
        print(f"❌ SlackNotifierエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_slack_notification()
