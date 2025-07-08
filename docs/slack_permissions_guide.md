# Slack App 権限設定ガイド

## 1. OAuth & Permissions での権限設定

### アクセス方法
1. https://api.slack.com/apps にアクセス
2. アプリを選択
3. 左サイドバー「OAuth & Permissions」をクリック

### Bot Token Scopes（必須権限）
「Scopes」セクション → 「Bot Token Scopes」で「Add an OAuth Scope」をクリック

```
✅ channels:history     - パブリックチャンネルのメッセージ履歴
✅ channels:read        - パブリックチャンネル情報の読み取り
✅ chat:write          - メッセージの送信
✅ chat:write.public   - 未参加チャンネルへの投稿
✅ app_mentions:read   - @AI-PMメンションの検知
✅ users:read          - ユーザー情報の取得

🔵 groups:history      - プライベートチャンネル履歴（必要に応じて）
🔵 groups:read         - プライベートチャンネル情報（必要に応じて）
🔵 im:history          - DM履歴（DM対応時）
🔵 im:read             - DM情報（DM対応時）
🔵 im:write            - DM送信（DM対応時）
```

### 権限追加後の再インストール
⚠️ **重要**: 権限を追加した後は必ず再インストールが必要

1. 同じページの上部「Install to Workspace」をクリック
2. 権限の変更を承認

## 2. Event Subscriptions（イベント設定）

### アクセス方法
左サイドバー「Event Subscriptions」をクリック

### Enable Events
「Enable Events」をオンに切り替え

### Subscribe to bot events
「Subscribe to bot events」セクションで「Add Bot User Event」をクリック

```
✅ app_mention         - @AI-PMメンション
✅ message.channels    - パブリックチャンネルメッセージ
🔵 message.groups      - プライベートチャンネルメッセージ
🔵 message.im          - DMメッセージ
```

### Request URL（Socket Mode使用時は不要）
Socket Modeを使う場合、Request URLは設定不要

## 3. Socket Mode（推奨設定）

### アクセス方法
左サイドバー「Socket Mode」をクリック

### Enable Socket Mode
「Enable Socket Mode」をオンに切り替え

### App-Level Token作成
1. 「Generate Token and Scopes」をクリック
2. Token Name: `socket-mode-token`
3. Add Scope: `connections:write`
4. 「Generate」をクリック
5. トークン（xapp-...）をコピーして保存

## 4. App Home（オプション）

### アクセス方法
左サイドバー「App Home」をクリック

### Bot表示名設定
- Display Name: `AI-PM`
- Default Username: `ai-pm`

## 5. インストールと確認

### ワークスペースへのインストール
1. 「OAuth & Permissions」ページ
2. 「Install to Workspace」をクリック
3. 権限を確認して「許可する」

### 取得すべきトークン
1. **Bot User OAuth Token** (`xoxb-...`): メッセージ送信用
2. **App-Level Token** (`xapp-...`): Socket Mode用

### チャンネルへの招待
Slackで対象チャンネルにて：
```
/invite @AI-PM
```

## 6. 設定確認方法

```bash
# 接続テスト実行
python3 scripts/setup_slack_ai_pm.py
```

## よくある問題と解決方法

### 「missing_scope」エラー
- OAuth & Permissionsで必要な権限を追加
- 再インストールを実行

### 「channel_not_found」エラー
- チャンネルにBotを招待: `/invite @AI-PM`
- チャンネルIDが正しいか確認

### 「not_authed」エラー
- Bot Tokenが正しく設定されているか確認
- トークンの有効期限を確認

### イベントが受信されない
- Event Subscriptionsが有効になっているか確認
- Socket Modeが有効で、App-Level Tokenが設定されているか確認

## セキュリティのベストプラクティス

1. **最小権限の原則**: 必要な権限のみを付与
2. **トークンの管理**: 環境変数で管理、コードにハードコードしない
3. **定期的な監査**: 不要になった権限は削除