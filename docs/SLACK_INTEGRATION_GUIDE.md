# 🔗 AI Company Slack連携強化ガイド

## 📋 概要

AI Company v3.0のSlack連携強化により、以下の機能が追加されました：

1. **Slackポーリングワーカー** - SlackメッセージをAIタスクとして自動処理
2. **Slack監視ワーカー** - システムエラーを検知してSlackへ自動通知

## 🚀 セットアップ手順

### 1. Slack Appの作成

1. [Slack API](https://api.slack.com/apps) にアクセス
2. "Create New App" → "From scratch"を選択
3. App名: `AI Company Bot`
4. ワークスペースを選択

### 2. Bot Tokenの取得

1. 左メニューの "OAuth & Permissions" を選択
2. "Bot Token Scopes" に以下を追加：
   - `channels:history` - チャンネルメッセージ読み取り
   - `channels:read` - チャンネル情報読み取り
   - `chat:write` - メッセージ送信
   - `chat:write.customize` - カスタマイズしたメッセージ送信
3. "Install to Workspace" をクリック
4. `xoxb-` で始まるBot Tokenをコピー

### 3. Webhook URLの取得

1. 左メニューの "Incoming Webhooks" を選択
2. "Activate Incoming Webhooks" をONに
3. "Add New Webhook to Workspace" をクリック
4. 通知先チャンネルを選択
5. Webhook URLをコピー

### 4. チャンネルIDの取得

1. Slackで対象チャンネルを右クリック
2. "Copy link" を選択
3. URLの最後の部分がチャンネルID（例: `C1234567890`）

### 5. 設定ファイルの更新

```bash
# 設定ファイルを編集
nano /home/aicompany/ai_co/config/slack.conf
```

以下を設定：

```bash
# 基本設定
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
ENABLE_SLACK=true

# Bot Token（ポーリング用）
SLACK_BOT_TOKEN="xoxb-your-bot-token"

# ポーリング設定
SLACK_POLLING_CHANNEL_ID="C1234567890"  # 監視するチャンネルID
SLACK_POLLING_ENABLED=true               # ポーリングを有効化

# 監視設定
SLACK_MONITOR_ENABLED=true               # エラー監視を有効化
SLACK_ERROR_CHANNEL="#ai-company-errors" # エラー通知先
```

## 📊 機能詳細

### Slackポーリングワーカー

**動作：**
- 指定チャンネルを20秒間隔で監視
- 新規メッセージを検出したらPMタスクとして投入
- Botメッセージは自動的に無視
- 処理済みメッセージはDBで管理（重複防止）

**データベース：**
- 場所: `/home/aicompany/ai_co/db/slack_messages.db`
- テーブル: `processed_messages`

### Slack監視ワーカー

**監視対象：**
- 全ワーカーのログファイル
- エラーキーワード: `CRITICAL`, `FATAL`, `ERROR`, `Exception`, `Traceback`
- システムリソース（CPU、メモリ、ディスク）

**通知レベル：**
- 🚨 **Critical**: 即座に通知（@channel メンション付き）
- ⚠️ **Error**: 閾値超過時に通知
- 🏥 **System**: リソース使用率90%超過時

## 🔧 管理コマンド

```bash
# Slackワーカーの管理
ai-slack start    # ワーカー起動
ai-slack stop     # ワーカー停止
ai-slack restart  # ワーカー再起動
ai-slack status   # 状態確認
ai-slack test     # 動作テスト
ai-slack logs     # ログ確認
ai-slack setup    # 初期設定ガイド
```

## 📈 使用例

### Slack経由でタスク実行

1. 監視チャンネルでBotをメンション：
   ```
   @pm-ai Pythonでファイル管理システムを作って
   ```

2. Slackポーリングワーカーが検出してPMタスクに変換
3. AIがタスク処理
4. 完了通知がSlackに送信

**メンション不要モード：**
```bash
# config/slack.confで設定
SLACK_REQUIRE_MENTION=false
```
この場合、チャンネル内のすべてのメッセージがタスク化されます。

### エラー監視

1. ワーカーでエラー発生
2. SlackMonitorWorkerが検出
3. エラーレベルに応じて適切なチャンネルに通知

## 🛠️ トラブルシューティング

### ポーリングが動作しない

```bash
# 設定確認
cat config/slack.conf | grep SLACK_

# Bot Tokenの権限確認
# Slack APIダッシュボードで権限を再確認

# ログ確認
tail -f logs/slack_polling_worker.log
```

### 通知が届かない

```bash
# Webhook URLテスト
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"Test message"}' \
YOUR_WEBHOOK_URL

# 設定確認
ai-slack test
```

### チャンネルIDが分からない

1. Slackデスクトップアプリで対象チャンネルを開く
2. チャンネル名をクリック → 「About」タブ
3. 最下部にチャンネルIDが表示される

## 📊 設定パラメータ一覧

| パラメータ | デフォルト | 説明 |
|---------|----------|-----|
| SLACK_POLLING_INTERVAL | 20 | ポーリング間隔（秒） |
| SLACK_REQUIRE_MENTION | true | Botメンション必須 |
| SLACK_MONITOR_INTERVAL | 10 | 監視間隔（秒） |
| SLACK_ERROR_THRESHOLD | 3 | エラー通知閾値 |
| SLACK_ERROR_SURGE_THRESHOLD | 20 | エラー急増閾値（/分） |
| SLACK_RATE_LIMIT_MAX | 10 | 最大メッセージ数（/分） |

## 🎯 ベストプラクティス

1. **専用チャンネルの作成**
   - `#ai-company-tasks` - タスク投入用
   - `#ai-company-errors` - エラー通知用
   - `#ai-company-notifications` - 一般通知用

2. **権限の最小化**
   - 必要なチャンネルのみアクセス許可
   - 不要なスコープは付与しない

3. **監視設定の調整**
   - 本番環境では閾値を適切に設定
   - 深夜帯はメンション通知を控える

---

**💡 Slack連携により、AI Companyがチームのコミュニケーションツールとシームレスに統合されます**
