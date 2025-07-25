# Slack PM-AI診断ガイド

## 診断ツールの使い方

### 1. 基本診断（全体チェック）
```bash
cd /home/aicompany/ai_co
python3 run_slack_diagnosis.py
```

これにより：
- Bot認証の確認
- チャンネルアクセスの確認
- 過去5分のメッセージ取得
- メンション検出の確認
- データベース状態の確認
- ワーカープロセスの確認

結果は `slack_diagnosis.log` に保存されます。

### 2. シンプルなAPIテスト
```bash
cd /home/aicompany/ai_co
python3 test_slack_api_simple.py
```

最小限のコードでSlack APIが動作するか確認します。

### 3. リアルタイム監視モード
```bash
cd /home/aicompany/ai_co
python3 slack_diagnosis_tool.py --monitor
```

5秒ごとにSlackをチェックし、PM-AIへのメンションを検出したらログに出力します。

## テスト手順

1. **診断実行**
   ```bash
   python3 run_slack_diagnosis.py
   ```

2. **Slackでメッセージ送信**
   #generalチャンネルで：
   ```
   @pm-ai テストメッセージです
   ```

3. **監視モードで確認**
   別ターミナルで：
   ```bash
   python3 slack_diagnosis_tool.py --monitor
   ```

4. **ログ確認**
   ```bash
   tail -f slack_diagnosis.log
   ```

## チェックポイント

### ✅ 正常な場合
- Bot認証成功
- チャンネル情報取得成功
- メッセージ履歴取得成功
- PM-AIへのメンション検出

### ❌ 問題がある場合
- Bot Token無効 → Slackアプリの設定確認
- チャンネルアクセス不可 → BotをチャンネルにInvite
- メッセージ取得失敗 → 権限設定確認
- メンション検出しない → メンション形式確認

## ログの見方

```
[2025-01-02 12:34:56.789] 1. 設定読み込み
[2025-01-02 12:34:56.790]   Bot Token: 設定あり
[2025-01-02 12:34:56.790]   Channel ID: C0946R76UU8
[2025-01-02 12:34:57.123] 2. Bot認証テスト
[2025-01-02 12:34:57.456]   ✅ Bot認証成功
[2025-01-02 12:34:57.456]   Bot User ID: U09471BK5HB
```

各ステップでの処理内容と結果が時系列で記録されます。

## トラブルシューティング

### Bot Tokenが無効な場合
1. Slack App管理画面でTokenを再生成
2. `/home/aicompany/ai_co/config/slack.conf` を更新

### チャンネルにアクセスできない場合
1. Slackで `/invite @pm-ai` を実行
2. チャンネルIDが正しいか確認

### メッセージが取得できない場合
1. Slack Appの権限確認（channels:history, channels:read必要）
2. Tokenのスコープ確認

### Polling Workerが起動しない場合
1. 手動で起動してエラー確認：
   ```bash
   cd /home/aicompany/ai_co
   source venv/bin/activate
   python3 workers/slack_polling_worker.py
   ```

## 次のステップ

診断で問題が特定できたら：
1. 問題の修正
2. Polling Workerの再起動
3. 動作確認

問題が特定できない場合は、監視モードでリアルタイムログを見ながらデバッグしてください。
