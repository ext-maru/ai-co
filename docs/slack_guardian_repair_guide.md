# 🔧 Slack API権限修復ガイド

## 緊急修復が必要な問題

Slack Guardian Knightが以下の問題を検出しました：

### 🚨 CRITICAL: API権限不足
- **現在のスコープ**: incoming-webhook のみ
- **不足スコープ**: channels:read, groups:read, mpim:read, im:read, channels:history

### 📱 修復手順

1. **Slack App設定に移動**
   ```
   https://api.slack.com/apps → Elders Guild app選択
   ```

2. **OAuth & Permissions**
   - "Scopes" > "Bot Token Scopes" に移動
   - 以下を追加:
     - channels:read
     - groups:read
     - mpim:read
     - im:read
     - channels:history

3. **アプリ再インストール**
   - "Reinstall App" ボタンクリック
   - 新しいBot Tokenを取得

4. **環境変数更新**
   ```bash
   # .envファイルのSLACK_BOT_TOKENを新しい値に更新
   vim .env
   ```

5. **ワーカー再起動**
   ```bash
   # Slackワーカーを再起動
   pkill -f slack_polling_worker
   python3 workers/slack_polling_worker.py &
   ```

## 🛡️ Guardian Knight Status
- Slack Monitor Worker: ✅ 復元完了
- PM Integration: ✅ 修復完了
- Configuration: ✅ 統合完了
- API Permissions: ⏳ 手動対応必要

修復完了後、Slack連携が完全復旧します。
