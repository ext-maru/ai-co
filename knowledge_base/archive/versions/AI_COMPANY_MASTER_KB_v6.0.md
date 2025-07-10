# Elders Guild Master Knowledge Base v6.0

## 🏢 システム概要

Elders Guildは、Claude APIを活用した自律的タスク処理システムです。RabbitMQベースのメッセージキューアーキテクチャを採用し、複数の専門ワーカーが協調して動作します。

### 基本構成
- **OS**: Ubuntu 24.04 LTS (WSL2)
- **Python**: 3.12.3
- **ユーザー**: aicompany (パスワード: aicompany)
- **プロジェクトルート**: `/home/aicompany/ai_co`

### 主要技術スタック
- **メッセージキュー**: RabbitMQ
- **API**: Claude API (Anthropic)
- **通知システム**: Slack Integration
- **データベース**: SQLite3 (タスク管理用)
- **Webダッシュボード**: Task Tracker (ポート5555)

## 🔧 Core基盤

### BaseWorker
すべてのワーカーの基底クラス。共通機能を提供：
- RabbitMQ接続管理
- エラーハンドリング（自動リトライ機構）
- ロギング機能
- Slack通知
- ヘルスチェック

### BaseManager
マネージャークラスの基底クラス：
- 共通設定管理
- ロギング
- エラーハンドリング

## 🤖 ワーカーアーキテクチャ

### 1. PM Worker (pm_worker.py)
- **役割**: タスクの分解と他のワーカーへの振り分け
- **キュー**: `ai_tasks`, `pm_task_queue`, `result_queue`
- **主要機能**:
  - タスク分析と優先度設定
  - ワーカー選定とルーティング
  - Git Flow自動処理（テスト実行付き）
  - 自動スケーリング管理
  - ヘルスチェック監視
  - Task Tracker統合

### 2. Task Worker (task_worker.py)
- **役割**: 実際のタスク処理
- **キュー**: `worker_tasks`
- **主要機能**:
  - Claude APIを使用したタスク実行
  - ファイル操作
  - コード生成
  - RAG（検索拡張生成）連携

### 3. Result Worker (result_worker.py)
- **役割**: 結果の集約とSlack通知
- **キュー**: `results`, `ai_results`
- **主要機能**:
  - 結果フォーマット
  - 通知送信
  - ログ記録

### 4. Dialog Task Worker (dialog_task_worker.py)
- **役割**: 対話型タスクの処理
- **キュー**: `dialog_tasks`
- **主要機能**:
  - マルチターン対話
  - コンテキスト管理
  - 会話履歴保持

### 5. Error Intelligence Worker (error_intelligence_worker.py)
- **役割**: エラーの自動解析と修正
- **キュー**: `error_intelligence`
- **主要機能**:
  - エラーパターン認識
  - 自動修正提案
  - インシデント管理

## 📦 主要ライブラリ

### SlackNotifier
```python
from libs.slack_notifier import SlackNotifier
notifier = SlackNotifier()
notifier.send_message("メッセージ")
notifier.send_task_completion_simple(task_id, worker, prompt, response)
```

### RAGManager（ナレッジ管理）
```python
from libs.rag_manager import RAGManager
rag = RAGManager()

# 要約付きタスク保存
rag.save_task_with_summary(task_id, worker, prompt, response)

# 関連履歴検索
related = rag.get_related_history(current_prompt, limit=5)

# 文脈構築
context_prompt = rag.build_context_prompt(current_prompt)
```

**RAGManagerの主な機能**：
- タスク履歴の要約生成（Claude CLI使用）
- 関連履歴検索（キーワード抽出）
- コンテキスト構築（過去の関連タスクを含む）
- パフォーマンス統計

### ConversationManager
```python
from libs.conversation_manager import ConversationManager
cm = ConversationManager()
cm.add_message(conv_id, role, content)
history = cm.get_conversation(conv_id)
```

### GitFlowManager
```python
from libs.git_flow_manager import GitFlowManager
gf = GitFlowManager()
gf.create_feature_branch(name)
gf.merge_to_develop(branch)
```

### TestManager
```python
from libs.test_manager import TestManager
tm = TestManager()
tm.run_all_tests()
tm.get_test_coverage()
```

### CommitMessageGenerator
```python
from libs.commit_message_generator import CommitMessageGenerator
cmg = CommitMessageGenerator()
message = cmg.generate_commit_message()
```

## 🔄 Git Flow & GitHub統合

### ブランチ戦略
- `main`: 本番環境
- `develop`: 開発環境
- `feature/*`: 新機能開発
- `fix/*`: バグ修正
- `release/*`: リリース準備

### コミット規約
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, perf, test, chore

### 自動Git処理
- PMワーカーによるタスク完了時の自動コミット
- テスト実行とGit Flow連携
- ベストプラクティスに基づくコミットメッセージ生成

## 🛠️ AIコマンド体系（68個）

### ✅ コア機能（完全動作）
- `ai-status`: システム状態確認（CPU・メモリ・ワーカー・キュー）
- `ai-send`: タスク送信（優先度・タグ対応）
- `ai-start/ai-stop`: システム起動/停止（tmux管理）
- `ai-logs`: ログ確認（マルチファイル・リアルタイム）
- `ai-help`: ヘルプ表示（コマンド一覧・詳細）
- `ai-version`: バージョン表示（詳細システム情報）
- `ai-restart`: システム再起動（安全停止→起動）

### 🔧 開発・管理機能
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
- `ai-config-edit`: 設定編集
- `ai-monitor`: リアルタイム監視（Ctrl+C終了）
- `ai-metrics`: 統計情報表示（period/format指定）
- `ai-stats`: システム統計

### 🧪 テスト・品質機能
- `ai-test-autofix`: テスト自動修正（start/stop/monitor）
- `ai-test-watch`: テスト監視（自動実行・通知）

### 🔄 データ・知識管理
- `ai-knowledge`: ナレッジ管理（consolidate/evolve/schedule）
- `ai-language`: 言語設定管理（ja/en切替・翻訳テスト）
- `ai-conversations`: 会話管理（list/export/info）
- `ai-backup`: バックアップ

### 🔌 プラグイン・拡張機能
- `ai-plugin`: プラグイン管理（list/install/remove）
- `ai-schedule`: スケジュール管理（list/add/remove）
- `ai-evolve`: 自己進化実行
- `ai-venv`: 仮想環境管理

### ⚡ 高度な機能
- `ai-worker-*`: ワーカー管理（add/restart/scale/comm）
- `ai-task-*`: タスク管理（cancel/info/retry）
- `ai-queue*`: キュー管理（status/clear・JSON/watch）
- `ai-dlq`: Dead Letter Queue管理
- `ai-worker-comm`: ワーカー間通信管理

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

### データベース
- **場所**: `/home/aicompany/ai_co/data/tasks.db`
- **形式**: SQLite3
- **テーブル**: tasks, task_logs

### Claude Desktop統合
Claude DesktopからElders Guildへのタスク送信時に自動的にTask Trackerで追跡。

## 📁 ディレクトリ構造

```
/home/aicompany/ai_co/
├── workers/          # ワーカー実装
│   ├── pm_worker.py
│   ├── task_worker.py
│   ├── result_worker.py
│   ├── dialog_task_worker.py
│   └── error_intelligence_worker.py
├── libs/            # 共通ライブラリ
│   ├── slack_notifier.py
│   ├── rag_manager.py
│   ├── conversation_manager.py
│   ├── git_flow_manager.py
│   ├── test_manager.py
│   └── commit_message_generator.py
├── core/            # Core基盤
│   ├── base_worker.py
│   └── base_manager.py
├── scripts/         # スクリプト
├── commands/        # AIコマンド実装
├── config/          # 設定ファイル
│   ├── config.json
│   └── pm_test.json
├── tests/           # テスト
├── logs/            # ログファイル
├── knowledge_base/  # ナレッジベース
├── web/             # Web UI
├── data/            # データファイル
│   └── tasks.db
└── db/              # データベース
```

## 🔐 設定管理

### 環境変数 (.env)
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

# システム設定
AI_AUTO_GIT_DISABLED=false
AI_VENV_ACTIVE=1
LOG_LEVEL=INFO
DEBUG=false
```

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
  },
  "scaling": {
    "enabled": true,
    "check_interval": 60,
    "scale_up_threshold": 0.8,
    "scale_down_threshold": 0.2
  }
}
```

## 🚀 デプロイメント

### 起動プロセス
1. **環境準備**
   ```bash
   cd /home/aicompany/ai_co
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な環境変数を設定
   ```

3. **データベース初期化**
   ```bash
   ./scripts/setup_database.sh
   ```

4. **システム起動**
   ```bash
   ai-start
   ```

### プロセス管理
- **tmux**を使用した各ワーカーのセッション管理
- 各ワーカーは独立したプロセスとして動作
- `ai-status`コマンドで全体の稼働状況を確認

## 📊 データ構造

### Task Object
```python
{
    "task_id": str,              # 一意のタスクID
    "prompt": str,               # タスクの内容
    "task_type": str,            # タスクタイプ
    "priority": int,             # 優先度 (1-10)
    "tags": List[str],           # タグリスト
    "status": str,               # ステータス
    "created_at": datetime,      # 作成日時
    "updated_at": datetime,      # 更新日時
    "assigned_to": str,          # 割り当てワーカーID
    "metadata": dict,            # 追加メタデータ
    "result": Optional[dict],    # 実行結果
    "error": Optional[str],      # エラーメッセージ
}
```

### WorkerInfo Object
```python
{
    "worker_id": str,            # ワーカーID
    "worker_type": str,          # ワーカータイプ
    "process_id": int,           # プロセスID
    "status": str,               # running, idle, stopped, error
    "current_task": Optional[str], # 現在処理中のタスクID
    "tasks_completed": int,      # 完了タスク数
    "memory_usage": float,       # メモリ使用量(MB)
    "cpu_usage": float,          # CPU使用率(%)
}
```

## 🌐 API仕様

### Claude API
- **Base URL**: `https://api.anthropic.com/v1/messages`
- **Model**: `claude-3-5-sonnet-20241022`
- **Max Tokens**: 4096

### RabbitMQ メッセージフォーマット
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

### Task Tracker Web API
- **Base URL**: `http://localhost:5555`
- **Endpoints**:
  - `POST /api/tasks`: タスク作成
  - `GET /api/tasks`: タスク一覧
  - `GET /api/tasks/{task_id}`: タスク詳細
  - `PUT /api/tasks/{task_id}/status`: ステータス更新

## 🐛 トラブルシューティング

### RabbitMQ接続エラー
```bash
sudo systemctl restart rabbitmq-server
```

### Python依存関係エラー
```bash
pip install -r requirements.txt --force-reinstall
sudo apt install python3-psutil python3-pika python3-rich python3-tabulate
```

### メモリ急上昇問題
**症状**: aiコマンド実行時にメモリ使用量が急激に上昇
**対策**: 環境変数 `AI_VENV_ACTIVE` による無限ループ防止

## 📈 パフォーマンス指標

### システム指標
- タスク処理時間: 平均30秒
- 同時処理数: 最大10タスク
- メモリ使用量: 約500MB/ワーカー
- エラー率: < 1%

### 最適化戦略
- キューベースの非同期処理
- ワーカープールによる並列処理
- 自動リトライによる信頼性向上
- ヘルスチェックによる異常検知

## 🔄 更新履歴

### v6.0 (2025-01-05)
- ナレッジベース統合・再編成
- RAGManager機能の詳細化
- 全体的な情報統合と構造化

### v5.3 (2025-01-05)
- Task Tracker システム追加
- メモリ急上昇問題の修正
- 68個のAIコマンド体系整備
- 大規模クリーンアップ実施

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

---

**Elders Guild Master Knowledge Base v6.0**  
最終更新: 2025-01-05  
統合・再編成版