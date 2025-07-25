---
audience: developers
author: claude-elder
category: technical
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: specifications
tags:
- technical
- python
title: Elders Guild API Specifications
version: 1.0.0
---

# Elders Guild API Specifications

## 外部API

### Claude API (Anthropic)

#### エンドポイント
- **Base URL**: `https://api.anthropic.com/v1/messages`
- **認証**: APIキーベース（環境変数: `ANTHROPIC_API_KEY`）

#### 使用モデル
- **モデル名**: `claude-3-5-sonnet-20241022`
- **最大トークン**: 4096

#### リクエスト形式
```python
{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
        {"role": "user", "content": "タスク内容"}
    ],
    "max_tokens": 4096,
    "temperature": 0.7
}
```

### Slack API

#### 認証
- **Bot Token**: 環境変数 `SLACK_BOT_TOKEN`
- **デフォルトチャンネル**: 環境変数 `SLACK_CHANNEL`

#### 主要メソッド
```python
# メッセージ送信
slack_client.chat_postMessage(
    channel=channel,
    text=message,
    blocks=blocks
)

# ファイルアップロード
slack_client.files_upload(
    channels=channel,
    file=file_path,
    title=title
)
```

## 内部API（ワーカー間通信）

### RabbitMQ メッセージフォーマット

#### タスク送信（ai_tasks キュー）
```json
{
    "task_id": "task_20250105_123456",
    "prompt": "タスクの内容",
    "priority": 5,
    "tags": ["development", "python"],
    "created_at": "2025-01-05T12:34:56Z",
    "metadata": {
        "source": "ai-send",
        "user": "aicompany"
    }
}
```

#### ワーカータスク（worker_tasks キュー）
```json
{
    "task_id": "task_20250105_123456",
    "task_type": "code_generation",
    "prompt": "詳細なタスク内容",
    "context": {
        "rag_results": [],
        "previous_attempts": 0
    },
    "assigned_worker": "worker-1",
    "assigned_at": "2025-01-05T12:35:00Z"
}
```

#### 結果通知（ai_results キュー）
```json
{
    "task_id": "task_20250105_123456",
    "task_type": "code_generation",
    "status": "completed",
    "worker_id": "worker-1",
    "rag_applied": true,
    "prompt": "元のプロンプト",
    "response": "処理結果",
    "files_created": ["path/to/file.py"],
    "output_file": "output/task_20250105_123456.txt",
    "duration": 25.3,
    "error": null,
    "error_trace": ""
}
```

#### 対話タスク（dialog_tasks キュー）
```json
{
    "conversation_id": "conv_20250105_123456",
    "task_id": "dialog_20250105_123456",
    "prompt": "ユーザーメッセージ",
    "context": {
        "history": [
            {"role": "user", "content": "前のメッセージ"},
            {"role": "assistant", "content": "前の応答"}
        ]
    },
    "max_turns": 10
}
```

#### エラー解析（error_intelligence キュー）
```json
{
    "error_id": "error_20250105_123456",
    "task_id": "関連タスクID",
    "error_type": "RuntimeError",
    "error_message": "エラーメッセージ",
    "stack_trace": "スタックトレース",
    "context": {
        "file": "問題のファイル",
        "line": 42,
        "code_snippet": "問題のコード"
    }
}
```

## コマンドラインインターフェース

### ai-send API
```bash
# 基本形式
ai-send "タスク内容"

# オプション付き
ai-send "タスク内容" --priority 7 --tags "python,debug"

# パイプ入力
echo "タスク内容" | ai-send --stdin
```

### ai-todo API
```bash
# リスト作成
ai-todo create "リスト名"

# タスク追加
ai-todo add "リスト名" "タスク説明" bash "実行コマンド"

# タスク実行
ai-todo run "リスト名"

# ステータス確認
ai-todo status
```

### ai-git API
```bash
# ステータス確認
ai-git status

# コミット（ベストプラクティス）
ai-git commit -m "メッセージ"
ai-git commit --preview  # メッセージプレビュー

# ブランチ操作
ai-git feature "ブランチ名"
ai-git merge "ブランチ名"

# リリース
ai-git release --version "1.0.0"
```

### ai-queue API
```bash
# キュー状態確認
ai-queue-status
ai-queue-status --json

# キュー監視
ai-queue-watch --interval 5

# キュークリア（注意）
ai-queue-clear "キュー名" --confirm
```

### ai-worker API
```bash
# ワーカー追加
ai-worker-add --type task --count 2

# ワーカー再起動
ai-worker-restart "worker-1"

# ワーカースケール
ai-worker-scale 5

# ワーカー間通信
ai-worker-comm status
ai-worker-comm send "worker-1" "メッセージ"
```

## Task Tracker Web API

### エンドポイント
- **Base URL**: `http://localhost:5555`

### タスク操作
```bash
# タスク作成
POST /api/tasks
{
    "title": "タスクタイトル",
    "description": "説明",
    "priority": 5,
    "assignee": "worker-1"
}

# タスク一覧
GET /api/tasks?status=in_progress&priority=5

# タスク詳細
GET /api/tasks/{task_id}

# ステータス更新
PUT /api/tasks/{task_id}/status
{
    "status": "completed"
}
```

## 環境変数API

### 必須環境変数
```bash
# Claude API
ANTHROPIC_API_KEY=your_api_key

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=#ai-notifications

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

### オプション環境変数
```bash
# 自動Git無効化
AI_AUTO_GIT_DISABLED=true

# 仮想環境フラグ
AI_VENV_ACTIVE=1

# ログレベル
LOG_LEVEL=INFO

# デバッグモード
DEBUG=true
```

## 設定ファイルAPI

### config.json
```json
{
  "workers": {
    "timeout": 300,
    "retry_count": 3,
    "retry_delay": 60,
    "max_workers": 10,
    "min_workers": 1
  },
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "slack": {
    "enabled": true,
    "rate_limit": 1
  },
  "rabbitmq": {
    "heartbeat": 600,
    "blocked_connection_timeout": 300
  }
}
```

### pm_test.json
```json
{
  "test_before_commit": true,
  "test_timeout": 300,
  "test_strategies": {
    "python_files": {
      "enabled": true,
      "actions": ["syntax_check", "unit_test", "import_check"]
    }
  },
  "skip_patterns": ["__pycache__", "*.pyc", "venv/"]
}
```

## エラーコード

### システムエラー
- `E001`: RabbitMQ接続エラー
- `E002`: Claude API接続エラー
- `E003`: Slack API接続エラー
- `E004`: ファイルシステムエラー

### タスクエラー
- `T001`: タスクタイムアウト
- `T002`: タスク解析エラー
- `T003`: タスク実行エラー
- `T004`: タスク結果保存エラー

### ワーカーエラー
- `W001`: ワーカー起動エラー
- `W002`: ワーカーヘルスチェック失敗
- `W003`: ワーカー通信エラー
- `W004`: ワーカースケーリングエラー
