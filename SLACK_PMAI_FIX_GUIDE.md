# Slack PM-AI連携修正ガイド

## 問題
SlackでPM-AIにメンションしてもai-send的な動きが始まらない

## 原因
1. Slack Polling Workerが起動していない
2. ai-startにSlack Polling Workerが含まれていない

## 修正内容

### 1. 即時修正（推奨）
```bash
cd /home/aicompany/ai_co
python3 run_slack_fix_now.py
```

これにより：
- Slack Polling Workerが起動
- ai_start.pyにSlack Polling追加
- 設定確認とテスト準備

### 2. 手動で確認
```bash
# ワーカー状態確認
ps aux | grep slack_polling_worker

# ログ確認
tail -f logs/slack_polling_worker.log

# tmuxセッション確認
tmux ls | grep slack_polling
tmux attach -t slack_polling
```

### 3. テスト方法
Slackの #general チャンネルで：
```
@pm-ai Hello Worldを出力するPythonコードを作成
@pm-ai システム情報を取得するスクリプトを作って
```

20秒以内に：
- 👀 リアクションが付く
- タスクがai_tasksキューに投入される
- TaskWorkerが処理を開始する

### 4. 今後の起動方法
```bash
# Slack Pollingも含めて起動
ai-start --slack-polling

# 全ワーカー起動
ai-start --all-workers

# 基本ワーカーのみ（Slack Pollingなし）
ai-start
```

## 設定確認

- Bot Token: `xoxb-9133957021265-9120858383298-GzfwMNHREdN7oU4Amd6rVGHv`
- 監視チャンネル: `C0946R76UU8` (#general)
- ポーリング間隔: 20秒
- メンション必須: はい

## トラブルシューティング

### ワーカーが起動しない場合
```bash
# 手動起動
cd /home/aicompany/ai_co
source venv/bin/activate
python3 workers/slack_polling_worker.py
```

### メッセージが処理されない場合
1. Bot TokenとChannel IDが正しいか確認
2. Botがチャンネルに追加されているか確認
3. メンション形式が正しいか確認（@pm-ai）

### ログにエラーが出る場合
```bash
# データベース初期化
rm -f db/slack_messages.db
python3 -c "from workers.slack_polling_worker import SlackPollingWorker; w = SlackPollingWorker(); w._init_database()"
```

## 実装詳細

Slack Polling Workerは：
1. 20秒ごとにSlackメッセージをチェック
2. PM-AIへのメンションを検出
3. ai-send形式でタスクキューに投入
4. TaskWorkerが通常通り処理

これでSlackからの指示が自動的にAI Companyシステムで処理されます。
