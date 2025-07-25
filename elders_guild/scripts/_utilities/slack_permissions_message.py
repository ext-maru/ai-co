#!/usr/bin/env python3
"""
Slack権限一覧送信スクリプト
"""

import sys

sys.path.insert(0, "/home/aicompany/ai_co")

from libs.slack_channel_notifier import SlackChannelNotifier


def send_permissions_list():
    """Slack権限一覧をSlackで送信"""

    message = """🔐 Elders Guild Slack Bot 権限設定推奨一覧

"📊" 現在の問題:
❌ 現在のスコープ: incoming-webhook
✅ 必要なスコープ: 以下の段階的実装

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Phase 1: 緊急対応 (今すぐ設定)
• chat:write           - メッセージ送信
• chat:write.public    - パブリックチャンネル送信
• channels:read        - チャンネル情報読み取り
• channels:history     - チャンネル履歴読み取り
• channels:join        - チャンネル参加
• users:read          - ユーザー情報読み取り
• reactions:write     - 絵文字リアクション
• bot                 - ボットユーザー

🚀 Phase 2: 機能拡張 (近日中)
• groups:read         - プライベートチャンネル読み取り
• groups:history      - プライベートチャンネル履歴
• im:read            - DM読み取り
• im:history         - DM履歴
• im:write           - DM送信
• files:read         - ファイル読み取り
• files:write        - ファイルアップロード
• commands           - スラッシュコマンド
• interactive:write  - ボタン・メニュー

💡 Phase 3: 高度機能 (将来)
• users:read.email   - メールアドレス取得
• links:read         - URL解析
• links:write        - プレビュー表示
• rtm:stream        - リアルタイム通信
• channels:manage    - チャンネル管理
• team:read         - ワークスペース情報

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️ 設定方法:
1.0 Slack App管理画面 → OAuth & Permissions
2.0 Bot Token Scopes に上記を追加
3.0 ワークスペースに再インストール
4.0 新しいトークンを環境変数に設定

🎯 理由:
Elders Guildのファイル共有、DM機能、インタラクティブ要素の実装予定のため、今のうちに設定推奨。

🏛️ Elders Guild エルダーズより"""

    notifier = SlackChannelNotifier()

    # デフォルトチャンネルに送信
    success = notifier.send_to_channel(notifier.default_channel, message)

    if success:
        print("✅ Slack権限一覧の送信に成功しました")
    else:
        print("❌ Slack送信失敗 - トークンまたはWebhook URL未設定")
        print("メッセージ内容:")
        print(message)

    return success


if __name__ == "__main__":
    send_permissions_list()
