# AI Company Component Catalog (TDD対応版)

## 🧪 TDD開発ツール

### ai-tdd コマンド
- **パス**: `/home/aicompany/ai_co/scripts/ai-tdd`
- **用途**: Claude CLIでのTDD開発支援
- **主要機能**:
  ```bash
  ai-tdd new <feature> <requirements>  # 新機能TDD開発
  ai-tdd test <file>                   # テスト追加
  ai-tdd coverage <module>             # カバレッジ分析
  ai-tdd session <topic>               # 対話型TDD
  ```

### generate-tdd-worker.py
- **パス**: `/home/aicompany/ai_co/scripts/generate-tdd-worker.py`
- **用途**: ワーカーとテストの自動生成
- **使用例**:
  ```bash
  ./scripts/generate-tdd-worker.py DataProcessor data
  ```

### ai-test-coverage
- **パス**: `/home/aicompany/ai_co/commands/ai-test-coverage`
- **用途**: テストカバレッジの確認と可視化
- **主要機能**:
  ```bash
  ai-test-coverage              # カバレッジレポート生成
  ai-test-coverage --html       # HTMLレポートを開く
  ai-test-coverage --watch      # 継続的監視
  ```

### coverage-report.py
- **パス**: `/home/aicompany/ai_co/scripts/coverage-report.py`
- **用途**: 詳細なカバレッジ分析レポート生成
- **機能**: モジュール別分析、履歴追跡、改善提案

### setup-tdd.sh
- **パス**: `/home/aicompany/ai_co/scripts/setup-tdd.sh`
- **用途**: TDD環境の初期セットアップ
- **実行内容**:
  - test-requirements.txtのインストール
  - pre-commitフックの設定
  - テスト実行スクリプトの生成

### run-tdd-tests.sh
- **パス**: `/home/aicompany/ai_co/scripts/run-tdd-tests.sh`
- **用途**: TDDテストの実行
- **モード**:
  ```bash
  ./scripts/run-tdd-tests.sh unit       # ユニットテスト
  ./scripts/run-tdd-tests.sh integration # 統合テスト
  ./scripts/run-tdd-tests.sh all        # 全テスト
  ./scripts/run-tdd-tests.sh watch      # 監視モード
  ```

### tdd-new-feature.sh
- **パス**: `/home/aicompany/ai_co/scripts/tdd-new-feature.sh`
- **用途**: 新機能のTDD開発開始
- **機能**: テストテンプレート生成、Red-Green-Refactorガイド

## 🧪 TDDテンプレート

### tdd_worker_template.py
- **パス**: `/home/aicompany/ai_co/templates/tdd_worker_template.py`
- **用途**: TDD対応ワーカーのテンプレート
- **特徴**: テスタブルな設計、モック対応、エラーハンドリング

### tdd_worker_test_template.py
- **パス**: `/home/aicompany/ai_co/templates/tdd_worker_test_template.py`
- **用途**: ワーカーテストのテンプレート
- **特徴**: AAAパターン、包括的テストケース、モック使用例

## ワーカーコンポーネント

### PM Worker
- **パス**: `/home/aicompany/ai_co/workers/pm_worker.py`
- **テスト**: `/home/aicompany/ai_co/tests/unit/test_pm_worker.py`
- **クラス**: `PMWorker`
- **テストカバレッジ**: 目標85%以上
- **依存関係**: 
  - GitHubFlowManager
  - PMGitIntegration
  - TestManager
  - WorkerMonitor
  - SlackNotifier
- **主要メソッド**:
  - `handle_task_completion()`: タスク完了時の自動Git処理
  - `process_pm_task()`: PM専用タスク処理
  - `start_scaling_monitor()`: スケーリング監視
  - `start_health_monitor()`: ヘルスチェック監視

### Task Worker
- **パス**: `/home/aicompany/ai_co/workers/task_worker.py`
- **テスト**: `/home/aicompany/ai_co/tests/unit/test_task_worker.py`
- **クラス**: `TaskWorker`
- **テストカバレッジ**: 目標85%以上
- **依存関係**: Claude API, BaseWorker
- **キュー**: `worker_tasks`
- **機能**: タスク実行、ファイル操作、コード生成

### Result Worker
- **パス**: `/home/aicompany/ai_co/workers/result_worker.py`
- **テスト**: `/home/aicompany/ai_co/tests/unit/test_result_worker.py`
- **クラス**: `ResultWorker`
- **テストカバレッジ**: 目標85%以上
- **依存関係**: SlackNotifier, BaseWorker
- **キュー**: `results`, `ai_results`
- **機能**: 結果集約、通知送信

### Dialog Task Worker
- **パス**: `/home/aicompany/ai_co/workers/dialog_task_worker.py`
- **クラス**: `DialogTaskWorker`
- **依存関係**: ConversationManager, BaseWorker
- **キュー**: `dialog_tasks`
- **機能**: マルチターン対話、コンテキスト管理

### Error Intelligence Worker
- **パス**: `/home/aicompany/ai_co/workers/error_intelligence_worker.py`
- **クラス**: `ErrorIntelligenceWorker`
- **依存関係**: RAGManager, BaseWorker
- **キュー**: `error_intelligence`
- **機能**: エラー解析、自動修正提案

## Core基盤（TDD実装済み）

### BaseWorker
- **パス**: `/home/aicompany/ai_co/core/base_worker.py`
- **テスト**: `/home/aicompany/ai_co/tests/unit/core/test_base_worker_tdd.py`
- **テストカバレッジ**: 95%以上達成
- **TDD実装**: 完全なRed-Green-Refactorサイクルで開発

### BaseManager  
- **パス**: `/home/aicompany/ai_co/core/base_manager.py`
- **テスト**: `/home/aicompany/ai_co/tests/unit/core/test_base_manager_tdd.py`
- **テストカバレッジ**: 95%以上達成
- **TDD実装**: 完全なRed-Green-Refactorサイクルで開発

## ライブラリコンポーネント

### SlackNotifier
- **パス**: `/home/aicompany/ai_co/libs/slack_notifier.py`
- **用途**: Slack通知送信
- **主要メソッド**:
  ```python
  send_message(message: str)
  send_task_completion_simple(task_id, worker, prompt, response)
  ```

### RAGManager
- **パス**: `/home/aicompany/ai_co/libs/rag_manager.py`
- **用途**: ナレッジベース管理とRAG検索
- **主要メソッド**:
  ```python
  add_knowledge(content: str, metadata: dict)
  search(query: str) -> list
  update_knowledge(id: str, content: str)
  ```

### ConversationManager
- **パス**: `/home/aicompany/ai_co/libs/conversation_manager.py`
- **用途**: 対話履歴管理
- **主要メソッド**:
  ```python
  add_message(conv_id: str, role: str, content: str)
  get_conversation(conv_id: str) -> list
  create_conversation() -> str
  ```

### GitHubFlowManager
- **パス**: `/home/aicompany/ai_co/libs/github_flow_manager.py`
- **用途**: GitHub Flow操作管理
- **主要メソッド**:
  ```python
  create_feature_branch(name: str) -> str
  create_pull_request(branch: str, title: str, body: str) -> bool
  merge_to_main(branch: str) -> bool
  get_status() -> dict
  ```

### TestManager
- **パス**: `/home/aicompany/ai_co/libs/test_manager.py`
- **用途**: テスト実行管理
- **主要メソッド**:
  ```python
  run_all_tests() -> dict
  run_specific_test(file: str) -> dict
  get_test_coverage() -> float
  ```

### CommitMessageGenerator
- **パス**: `/home/aicompany/ai_co/libs/commit_message_generator.py`
- **用途**: ベストプラクティスに基づくコミットメッセージ生成
- **主要メソッド**:
  ```python
  generate_commit_message() -> str
  validate_message(message: str) -> tuple[bool, list]
  analyze_changes() -> dict
  ```

## コマンドコンポーネント（主要68個）

### コア機能コマンド
- **ai-status**: システム状態確認
- **ai-send**: タスク送信
- **ai-start/ai-stop**: システム起動/停止
- **ai-logs**: ログ確認
- **ai-help**: ヘルプ表示
- **ai-version**: バージョン表示
- **ai-restart**: システム再起動

### 開発・管理コマンド
- **ai-todo**: ToDoリスト管理
- **ai-rag-search**: RAG検索
- **ai-workers**: ワーカー状態確認
- **ai-tasks**: タスク履歴確認
- **ai-scale**: オートスケーリング管理
- **ai-git**: Git操作管理

### 対話・通信コマンド
- **ai-code**: コード生成
- **ai-dialog**: 対話型タスク開始
- **ai-reply**: 対話応答送信
- **ai-slack**: Slack統合

### 設定・監視コマンド
- **ai-config**: 設定確認
- **ai-config-edit**: 設定編集
- **ai-monitor**: リアルタイム監視
- **ai-metrics**: 統計情報表示
- **ai-stats**: システム統計

### テスト・品質コマンド
- **ai-test-autofix**: テスト自動修正
- **ai-test-watch**: テスト監視

### データ・知識管理コマンド
- **ai-knowledge**: ナレッジ管理
- **ai-language**: 言語設定管理
- **ai-conversations**: 会話管理
- **ai-backup**: バックアップ

### 高度な機能コマンド
- **ai-worker-***: ワーカー管理系
- **ai-task-***: タスク管理系
- **ai-queue***: キュー管理系
- **ai-dlq**: Dead Letter Queue管理
- **ai-worker-comm**: ワーカー間通信管理

## 設定ファイル

### config.json
- **パス**: `/home/aicompany/ai_co/config/config.json`
- **内容**: 
  - ワーカー設定（タイムアウト、リトライ）
  - Claude API設定
  - Slack設定

### pm_test.json
- **パス**: `/home/aicompany/ai_co/config/pm_test.json`
- **内容**:
  - テスト実行設定
  - テスト戦略
  - スキップパターン

### .env
- **パス**: `/home/aicompany/ai_co/.env`
- **内容**:
  - APIキー（ANTHROPIC_API_KEY）
  - Slackトークン
  - RabbitMQ設定

## Webコンポーネント

### Task Tracker
- **パス**: `/home/aicompany/ai_co/web/`
- **ポート**: 5555
- **機能**:
  - カンバン風タスク表示
  - ステータス管理
  - 優先度システム
  - タスク履歴

## データベース

### tasks.db
- **パス**: `/home/aicompany/ai_co/data/tasks.db`
- **形式**: SQLite3
- **テーブル**:
  - tasks: タスク情報
  - task_logs: タスクログ

## スクリプト

### setup_database.sh
- **パス**: `/home/aicompany/ai_co/scripts/setup_database.sh`
- **用途**: データベース初期化

### task
- **パス**: `/home/aicompany/ai_co/scripts/task`
- **用途**: CLIタスク管理ツール

## 仮想環境

### venv
- **パス**: `/home/aicompany/ai_co/venv`
- **Python**: 3.12.3
- **主要パッケージ**:
  - pika (RabbitMQ)
  - anthropic (Claude API)
  - slack-sdk
  - rich (UI)
  - tabulate (表表示)