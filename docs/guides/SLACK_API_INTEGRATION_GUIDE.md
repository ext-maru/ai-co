# Slack API Integration Guide v1.0

## 🚀 概要

Elders Guild Slack API Integration Systemは、SlackのWeb API、Webhooks、Socket Modeを統合した包括的なSlack統合システムです。4賢者システムとの連携機能も搭載しており、エラーアラート、タスク通知、システム状況報告を自動化します。

## 📋 機能

### ✅ 実装済み機能
- **Slack Web API統合**: チャンネル、ユーザー、メッセージ管理
- **Webhook サポート**: 高速メッセージ送信
- **4賢者システム連携**: Knowledge Sage、Task Oracle、Crisis Sage、Search Mystic
- **レート制限管理**: 自動レート制限とリトライ機能
- **メッセージ履歴**: 送信履歴の記録と管理
- **エラーアラート**: 自動エラー通知とエスカレーション
- **フォーマット機能**: Block Kit、Attachments、コードブロック
- **イベントハンドラ**: カスタムイベント処理

### 🔄 計画中機能
- **Socket Mode**: リアルタイム双方向通信
- **インタラクティブコンポーネント**: ボタン、モーダル、セレクト
- **スラッシュコマンド**: カスタムSlackコマンド
- **ワークフロー統合**: Slack Workflow Builder連携

## 🛠️ セットアップ

### 1. 依存関係のインストール

```bash
# 推奨: aiohttp（非同期HTTP）
pip install aiohttp

# フォールバック: requests（同期HTTP）
pip install requests
```

### 2. Slack アプリケーション設定

1. **Slack API**: https://api.slack.com/apps でアプリを作成
2. **Bot Tokens**: `xoxb-` で始まるボットトークンを取得
3. **App-Level Tokens**: `xapp-` で始まるアプリレベルトークンを取得（Socket Mode用）
4. **Webhook URLs**: `https://hooks.slack.com/services/...` のWebhook URLを取得

### 3. 環境変数設定

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_APP_TOKEN="xapp-your-app-token"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SLACK_SIGNING_SECRET="your-signing-secret"
```

### 4. 設定ファイル設定

`config/slack.conf` ファイルを作成:

```conf
BOT_TOKEN=xoxb-your-bot-token
APP_TOKEN=xapp-your-app-token
WEBHOOK_URL=https://hooks.slack.com/services/...
SIGNING_SECRET=your-signing-secret
```

## 🔧 使用方法

### 基本的な使用例

```python
import asyncio
from libs.slack_api_integration import create_slack_integration, SlackMessage, SlackMessageType

async def main():
    # Slack統合システムの作成
    slack = await create_slack_integration()

    # 接続テスト
    test_results = await slack.test_connection()
    print(f"Connection test: {test_results}")

    # 基本メッセージ送信
    message = SlackMessage(
        channel="general",
        text="Hello from Elders Guild!"
    )
    result = await slack.send_message(message)

    # フォーマット済みメッセージ
    await slack.send_formatted_message(
        channel="general",
        title="System Update",
        content="All systems are operational",
        color="good"
    )

    # 4賢者通知
    await slack.send_4sages_notification(
        "Knowledge Sage",
        "New knowledge base updated",
        "normal"
    )

# 実行
asyncio.run(main())
```

### Webhook 使用例

```python
async def webhook_example():
    slack = await create_slack_integration()

    # シンプルなWebhook送信
    success = await slack.send_webhook_message("Quick update!")

    # リッチフォーマット
    await slack.send_webhook_message(
        "Deployment completed",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Status:* ✅ Success"
                }
            }
        ]
    )
```

### エラーアラート

```python
async def error_handling():
    slack = await create_slack_integration()

    try:
        # 何らかの処理
        raise ValueError("Something went wrong")
    except Exception as e:
        # 自動エラーアラート
        await slack.send_error_alert(e, {
            'module': 'example_module',
            'function': 'error_handling',
            'user': 'claude_elder'
        })
```

### イベントハンドラ

```python
async def event_example():
    slack = await create_slack_integration()

    # イベントハンドラ登録
    def message_handler(event_data):
        print(f"Message received: {event_data}")

    slack.register_event_handler('message', message_handler)

    # イベント発火
    await slack.handle_event('message', {'text': 'Hello!'})
```

## 🏗️ データ構造

### SlackMessage

```python
@dataclass
class SlackMessage:
    channel: str                                  # チャンネルID/名前
    text: str = ""                               # メッセージテキスト
    message_type: SlackMessageType = TEXT        # メッセージタイプ
    blocks: Optional[List[Dict]] = None          # Block Kit ブロック
    attachments: Optional[List[Dict]] = None     # アタッチメント
    thread_ts: Optional[str] = None              # スレッドタイムスタンプ
    reply_broadcast: bool = False                # スレッド返信をブロードキャスト
    unfurl_links: bool = True                    # リンクの展開
    unfurl_media: bool = True                    # メディアの展開
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

### SlackUser

```python
@dataclass
class SlackUser:
    id: str                                      # ユーザーID
    name: str                                    # ユーザー名
    real_name: str                               # 実名
    email: Optional[str] = None                  # メールアドレス
    is_bot: bool = False                         # ボットフラグ
    is_admin: bool = False                       # 管理者フラグ
    is_owner: bool = False                       # オーナーフラグ
    timezone: Optional[str] = None               # タイムゾーン
    profile: Dict[str, Any] = field(default_factory=dict)
```

### SlackChannel

```python
@dataclass
class SlackChannel:
    id: str                                      # チャンネルID
    name: str                                    # チャンネル名
    channel_type: SlackChannelType               # チャンネルタイプ
    is_archived: bool = False                    # アーカイブ済みフラグ
    is_private: bool = False                     # プライベートフラグ
    member_count: int = 0                        # メンバー数
    topic: str = ""                              # トピック
    purpose: str = ""                            # 目的
    created: Optional[datetime] = None           # 作成日時
```

## 🎯 4賢者システム連携

### 賢者タイプと絵文字

| 賢者タイプ | 絵文字 | 役割 |
|----------|------|------|
| Knowledge Sage | 📚 | ナレッジベース管理 |
| Task Oracle | 📋 | タスク・プロジェクト管理 |
| Crisis Sage | 🚨 | インシデント・エラー対応 |
| Search Mystic | 🔍 | 情報検索・RAG |

### 優先度レベル

| 優先度 | 色 | 用途 |
|-------|---|------|
| low | good (緑) | 情報通知 |
| normal | #439FE0 (青) | 通常の更新 |
| high | warning (黄) | 注意が必要 |
| critical | danger (赤) | 緊急対応 |

## 📊 監視とメトリクス

### API 使用統計

```python
# 統計情報取得
integration = await create_slack_integration()

# リクエスト数
print(f"Request count: {integration.request_count}")

# メッセージ履歴
history = await integration.get_message_history(10)
for entry in history:
    print(f"{entry['timestamp']}: {entry['message']}")

# レート制限状況
print(f"Rate limit reset: {integration.rate_limit_reset_time}")
```

### エラー追跡

システムは自動的に以下を追跡します：

- API リクエストエラー
- レート制限
- Webhook 失敗
- 認証エラー
- ネットワークエラー

## 🔧 カスタマイズ

### 設定のカスタマイズ

```python
config = {
    'rate_limit_per_minute': 30,  # レート制限調整
    'max_retries': 5,             # リトライ回数
    'sage_integration': False,    # 4賢者連携無効
    'auto_escalation': False      # 自動エスカレーション無効
}

slack = SlackAPIIntegration(config)
```

### カスタムイベントハンドラ

```python
async def custom_handler(event_data):
    # カスタムロジック
    print(f"Custom event: {event_data}")

slack.register_event_handler('custom_event', custom_handler)
await slack.handle_event('custom_event', {'data': 'custom'})
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. "Bot token not configured"

**原因**: Botトークンが設定されていない

**解決**:
```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
```

#### 2. "No HTTP client available"

**原因**: aiohttp または requests がインストールされていない

**解決**:
```bash
pip install aiohttp requests
```

#### 3. "Rate limited"

**原因**: Slack API のレート制限に達した

**解決**: 自動的にリトライされます。設定で制限を調整可能。

#### 4. "Webhook failed"

**原因**: Webhook URL が無効または期限切れ

**解決**: 新しいWebhook URLを取得して設定

### デバッグモード

```python
import logging
logging.basicConfig(level=logging.DEBUG)

slack = await create_slack_integration()
# デバッグログが出力される
```

## 📚 API リファレンス

### SlackAPIIntegration クラス

#### 主要メソッド

| メソッド | 説明 | 戻り値 |
|---------|------|-------|
| `send_message(message)` | メッセージ送信 | Dict |
| `send_webhook_message(text, **kwargs)` | Webhook送信 | bool |
| `get_channels()` | チャンネル一覧 | List[SlackChannel] |
| `get_users()` | ユーザー一覧 | List[SlackUser] |
| `send_4sages_notification()` | 4賢者通知 | Dict |
| `send_error_alert()` | エラーアラート | bool |
| `test_connection()` | 接続テスト | Dict |

#### ユーティリティ関数

| 関数 | 説明 | 例 |
|-----|------|---|
| `format_code_block(code, lang)` | コードブロック | `format_code_block("print()", "python")` |
| `format_user_mention(user_id)` | ユーザーメンション | `format_user_mention("U123")` |
| `format_channel_mention(channel_id)` | チャンネルメンション | `format_channel_mention("C123")` |

## 🔗 関連リンク

- [Slack API Documentation](https://api.slack.com/)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Elders Guild 4賢者システム](../knowledge_base/FOUR_SAGES_UNIFIED_WISDOM_INTEGRATION.md)
- [Elders Guild アーキテクチャ](../knowledge_base/system_architecture.md)

## 📝 更新履歴

### v1.0 (2025-07-09)
- 初回リリース
- Slack Web API 統合
- Webhook サポート
- 4賢者システム連携
- レート制限管理
- エラーアラート機能
- イベントハンドラシステム

---

**Elders Guild Slack API Integration System v1.0**
*Generated with 🤖 Claude Code - Elders Guild 4 Sages System*
