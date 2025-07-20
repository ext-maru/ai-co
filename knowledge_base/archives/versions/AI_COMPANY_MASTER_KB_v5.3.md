# Elders Guild Master Knowledge Base v5.3

## 🏢 システム概要

Elders Guildは、Claude APIを活用した自律的タスク処理システムです。

### 基本構成
- **環境**: Ubuntu 24.04 LTS (WSL2)
- **Python**: 3.12.3
- **ユーザー**: aicompany (パスワード: aicompany)
- **プロジェクトルート**: `/home/aicompany/ai_co`

## 🔧 Core基盤

### BaseWorker
すべてのワーカーの基底クラス。共通機能を提供：
- RabbitMQ接続管理
- エラーハンドリング
- ロギング
- Slack通知
- 自動リトライ

### BaseManager
マネージャークラスの基底クラス：
- 共通設定管理
- ロギング
- エラーハンドリング

## 🤖 ワーカー一覧

### 1. PM Worker (pm_worker.py)
- **役割**: タスクの分解と他のワーカーへの振り分け
- **キュー**: `ai_tasks`
- **機能**: タスク分析、優先度設定、ワーカー選定

### 2. Task Worker (task_worker.py)
- **役割**: 実際のタスク処理
- **キュー**: `worker_tasks`
- **機能**: Claude APIを使用したタスク実行

### 3. Result Worker (result_worker.py)
- **役割**: 結果の集約とSlack通知
- **キュー**: `results`
- **機能**: 結果フォーマット、通知送信

### 4. Dialog Task Worker (dialog_task_worker.py)
- **役割**: 対話型タスクの処理
- **キュー**: `dialog_tasks`
- **機能**: マルチターン対話、コンテキスト管理

### 5. Error Intelligence Worker (error_intelligence_worker.py)
- **役割**: エラーの自動解析と修正
- **キュー**: `error_intelligence`
- **機能**: エラーパターン認識、自動修正提案

## 📦 ライブラリ

### SlackNotifier
```python
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message("メッセージ")
```

### RAGManager
```python
from libs.rag_manager import RAGManager
rag = RAGManager()
rag.add_knowledge("知識", metadata={})
results = rag.search("クエリ")
```

### ConversationManager
```python
from libs.conversation_manager import ConversationManager
cm = ConversationManager()
cm.add_message(conv_id, role, content)
history = cm.get_conversation(conv_id)
```

## 🔄 GitHub Flow運用

### ブランチ戦略（GitHub Flow）
- `main`: メインブランチ（開発・本番統合）
- `feature/*`: 機能開発・バグ修正ブランチ

### コミット規約
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, chore

## 🛠️ コマンド一覧

### AI Command Executor
```bash
# タスク送信
ai-send "タスクの内容"

# ログ確認
ai-logs

# ステータス確認
ai-status

# TODO管理
ai-todo create "リスト名"
ai-todo add "リスト名" "タスク" bash "コマンド"
ai-todo run "リスト名"
ai-todo status  # ToDoリスト一覧
ai-todo list    # status のエイリアス
ai-todo learn   # 学習内容表示
```

### システム管理
```bash
# 起動/停止
ai-start
ai-stop

# GitHub Flow
gf feature <name>
gf fix <name>
gf commit -m "message"
```

## 📁 ディレクトリ構造

```
/home/aicompany/ai_co/
├── workers/          # ワーカー実装
├── libs/            # 共通ライブラリ
├── core/            # Core基盤
├── scripts/         # スクリプト
├── config/          # 設定ファイル
├── tests/           # テスト
├── logs/            # ログ
├── knowledge_base/  # ナレッジベース
├── web/             # Web UI
└── db/              # データベース
```

## 🔐 設定管理

### 環境変数管理ルール
**重要**: 環境変数は必ず `.env` ファイルに集約し、`libs/env_config.py` 経由でアクセスすること。

```python
# 正しい使用方法
from libs.env_config import get_config
config = get_config()
api_key = config.ANTHROPIC_API_KEY
```

### 環境変数 (.env)
```bash
# .env.template をコピーして作成
ANTHROPIC_API_KEY=your_key
SLACK_BOT_TOKEN=your_token
SLACK_CHANNEL=your_channel
RABBITMQ_HOST=localhost
```

### 管理コマンド
```bash
ai-setup      # 初回セットアップ
ai-env check  # 設定確認
ai-env verify # 必須変数検証
```

### config.json
```json
{
  "workers": {
    "timeout": 300,
    "retry_count": 3,
    "retry_delay": 60
  },
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096
  },
  "slack": {
    "enabled": true,
    "rate_limit": 1
  }
}
```

## 🚀 デプロイ手順

1. 環境準備
```bash
cd /home/aicompany/ai_co
source venv/bin/activate
pip install -r requirements.txt
```

2. 設定
```bash
cp .env.example .env
# .envを編集
```

3. データベース初期化
```bash
./scripts/setup_database.sh
```

4. 起動
```bash
ai-start
```

## 🐛 トラブルシューティング

### RabbitMQ接続エラー
```bash
sudo systemctl restart rabbitmq-server
```

### Python依存関係エラー
```bash
pip install -r requirements.txt --force-reinstall

# システムパッケージ不足の場合
sudo apt install python3-psutil python3-pika python3-rich python3-tabulate
```

### AIコマンド未実装エラー
**症状**: aiコマンドで「コマンドが見つかりません」エラー

## 🎯 AIコマンド完全ガイド

### ✅ コア機能（完全動作）
- `ai-status`: システム状態確認（CPU・メモリ・ワーカー・キュー）
- `ai-send`: タスク送信（優先度・タグ対応）
- `ai-start/ai-stop`: システム起動/停止（tmux管理）
- `ai-logs`: ログ確認（マルチファイル・リアルタイム）
- `ai-help`: ヘルプ表示（コマンド一覧・詳細）
- `ai-version`: バージョン表示（詳細システム情報）
- `ai-restart`: システム再起動（安全停止→起動）

### 🔧 開発・管理機能（動作確認済み）
- `ai-todo`: ToDoリスト管理（create/add/run/status/list/learn/daily）
- `ai-rag-search`: RAG検索（JSON/UI出力・GitHub統合）
- `ai-workers`: ワーカー状態確認（プロセス・メモリ監視）
- `ai-tasks`: タスク履歴確認（実行状況・統計）
- `ai-scale`: オートスケーリング管理（enable/disable/metrics）
- `ai-git`: Git操作管理（status/commit/feature/merge）

### 🗣️ 対話・通信機能
- `ai-code`: コード生成（ai-sendのショートカット）
- `ai-dialog`: 対話型タスク開始（マルチターン）
- `ai-reply`: 対話応答送信（会話ID指定）
- `ai-slack`: Slack統合（status/workers監視）

### ⚙️ 設定・監視機能
- `ai-config`: 設定確認（--list/--get/ファイル表示）
- `ai-config-edit`: 設定編集（wrapper）
- `ai-monitor`: リアルタイム監視（Ctrl+C終了）
- `ai-metrics`: 統計情報表示（period/format指定）
- `ai-stats`: システム統計（別実装）

### 🧪 テスト・品質機能
- `ai-test-autofix`: テスト自動修正（start/stop/monitor）
- `ai-test-watch`: テスト監視（自動実行・通知）
- `ai-quality-stats`: 品質統計（削除済み - ai-metricsで代替）

### 🔄 データ・知識管理
- `ai-knowledge`: ナレッジ管理（consolidate/evolve/schedule）
- `ai-language`: 言語設定管理（ja/en切替・翻訳テスト）
- `ai-conversations`: 会話管理（list/export/info）
- `ai-backup`: バックアップ（wrapper）

### 🔌 プラグイン・拡張機能
- `ai-plugin`: プラグイン管理（list/install/remove）
- `ai-schedule`: スケジュール管理（list/add/remove）
- `ai-evolve`: 自己進化実行（wrapper）
- `ai-venv`: 仮想環境管理（アクティベート・エイリアス）

### ⚡ 高度な機能
- `ai-worker-*`: ワーカー管理（add/restart/scale/comm）
- `ai-task-*`: タスク管理（cancel/info/retry）
- `ai-queue*`: キュー管理（status/clear・JSON/watch）
- `ai-prompt`: プロンプト管理（ai-sendエイリアス）

### ✨ 新規実装（2025-01-05）
- `ai-dlq`: Dead Letter Queue管理（実装完了）
- `ai-worker-comm`: ワーカー間通信管理（実装完了）

### ❌ 削除済みコマンド（2025-01-05）
- `ai-pm-test`: プレースホルダーのため削除
- `ai-quality-stats`: プレースホルダーのため削除
- `ai-test`: プレースホルダーのため削除（ai-test-autofixで代替）
- `ai-webui`: 未実装のため削除
- `ai-autoscale`: ai-gitの重複シンボリックリンクのため削除
- `ai-logs` (scripts): 循環シンボリックリンクのため削除
- `ai-stop` (scripts): 循環シンボリックリンクのため削除

**総計**: 68個のaiコマンドが稼働中（すべて動作確認済み）

### ログ確認
```bash
ai-logs
tail -f logs/workers/*.log
```

### AIコマンドメモリ急上昇問題
**症状**: `ai-todo` や `ai-rag-search` 実行時にメモリ使用量が急激に上昇し、WSL停止

**原因**: subprocess 無限ループによるプロセス大量生成

**対策**:
- 環境変数 `AI_VENV_ACTIVE` による無限ループ防止
- プロセス監視機能による異常検出
- 実行時安全性チェック

**修正済み**: 2025-01-05 v5.3で対応完了

## 📊 パフォーマンス指標

- タスク処理時間: 平均30秒
- 同時処理数: 最大10タスク
- メモリ使用量: 約500MB/ワーカー
- エラー率: < 1%

## 📋 Task Tracker システム

### 概要
簡易Redmine風のタスク管理システム。全てのAIタスクを追跡・管理。

### アクセス方法
- **Webダッシュボード**: http://localhost:5555
- **CLIコマンド**: `./scripts/task`

### 主な機能
- カンバン風のタスク表示
- ステータス管理（新規→進行中→レビュー→完了）
- 優先度システム（1-5の5段階）
- タスク履歴とタイムライン
- PMワーカーとの自動連携

### CLIコマンド
```bash
# タスク作成
./scripts/task create "タスクタイトル" -d "説明" -p 5

# タスク一覧
./scripts/task list

# タスク詳細
./scripts/task show [task_id]

# ステータス更新
./scripts/task update [task_id] in_progress

# レポート生成
./scripts/task report
```

### データベース
- **場所**: `/home/aicompany/ai_co/data/tasks.db`
- **形式**: SQLite3
- **テーブル**: tasks, task_logs

### Claude Desktop統合
Claude DesktopからElders Guildへのタスク送信時に自動的にTask Trackerで追跡：

```python
from claude_desktop_task_sender import ClaudeDesktopTaskSender
sender = ClaudeDesktopTaskSender()
task_id = sender.send_development_task("開発依頼", priority=4)
```

- すべての開発依頼を可視化
- 優先度に基づく処理順序管理
- エラー追跡とログ記録
- 進捗のリアルタイム確認

## 🔄 更新履歴

### v5.4 (2025-01-06)
- 環境変数管理ルール策定
- シンプルな単一ソース管理方式採用
- 複雑な自動検出機能を廃止
- `env_config.py` による統一アクセス実装
- `ai-setup`, `ai-env` コマンド追加

### v5.3 (2025-01-05)
- Task Tracker システム追加
- PMワーカーへのTask Tracker統合
- Webダッシュボード実装
- タスク履歴管理機能
- AIコマンドメモリ急上昇問題修正
- プロセス監視機能追加
- 全68個のAIコマンド包括的テスト完了
- 50個以上のコマンド動作確認・修正
- シンタックスエラー・依存関係エラー修正
- AIコマンド完全ガイド追加

### v5.3 (2025-01-05)
- 大規模クリーンアップ実施
  - バックアップファイル24個削除
  - ログファイル2,761個削除
  - 循環・重複シンボリックリンク削除
  - プレースホルダーコマンド削除
- ai-dlq, ai-worker-commコマンド実装
- AIコマンド体系の整理（68個に統合）

### v5.2 (2025-01-04)
- Error Intelligence Worker追加
- インシデント管理システム実装
- ナレッジベース自動更新機能

### v5.1 (2024-12-30)
- GitHub Flow統合
- 自動テストシステム
- コミット規約の導入

### v5.0 (2024-12-25)
- Core基盤の実装
- 統合設定管理
- Slack通知の改善
