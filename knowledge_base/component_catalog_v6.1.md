# AI Company Component Catalog v6.1

*最終更新: 2025年7月5日 - Phase 1-3 統合完了版*

## 🤖 ワーカーコンポーネント (14個)

### 🏗️ Core Workers

#### Enhanced PM Worker ⭐
- **パス**: `/home/aicompany/ai_co/workers/enhanced_pm_worker.py`
- **クラス**: `EnhancedPMWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_pm` ← `ai_results`
- **統合済み機能**:
  - Git Flow管理 (GitHubFlowManager)
  - プロジェクト設計 (ProjectDesignManager)
  - 品質管理 (QualityChecker) - quality_pm_worker統合
  - 自己進化 (SelfEvolutionManager)
  - Slack通知 (SlackNotifier)
- **主要メソッド**:
  - `_handle_project_mode()`: フルプロジェクトライフサイクル管理
  - `_phase_requirements()`: 要件定義フェーズ
  - `_phase_design()`: 設計フェーズ
  - `_phase_development()`: 開発フェーズ
  - `_phase_testing()`: テストフェーズ
  - `_phase_deployment()`: デプロイフェーズ
  - `_evaluate_project_quality()`: プロジェクト品質評価
  - `_check_task_quality_and_retry()`: 品質チェック・再実行

#### Enhanced Task Worker ⭐
- **パス**: `/home/aicompany/ai_co/workers/enhanced_task_worker.py`
- **クラス**: `EnhancedTaskWorker`
- **継承**: BaseWorker + PromptTemplateMixin ✅
- **キュー**: `ai_tasks` → `ai_pm`
- **依存関係**: 
  - PromptTemplateMixin (テンプレートシステム)
  - RAGManager (検索拡張生成)
  - SlackNotifier
  - TaskHistoryDB
- **主要メソッド**:
  - `_select_template()`: 適切なプロンプトテンプレート選択
  - `generate_prompt()`: RAG拡張プロンプト生成
  - `_execute_claude()`: Claude CLI実行
  - `evaluate_last_prompt()`: プロンプト品質評価

#### Result Worker
- **パス**: `/home/aicompany/ai_co/workers/result_worker.py`
- **クラス**: `ResultWorkerV2`
- **継承**: BaseWorker ✅
- **キュー**: `ai_results` (終端)
- **依存関係**: SlackNotifier, AICommandHelper
- **機能**: 結果集約、Slack通知、統計収集

### 🗣️ Interaction Workers

#### Dialog Task Worker
- **パス**: `/home/aicompany/ai_co/workers/dialog_task_worker.py`
- **クラス**: `DialogTaskWorker`
- **継承**: BaseWorker ✅ (Phase 2で修正)
- **キュー**: `ai_dialog` → `ai_results` + `ai_dialog_response`
- **依存関係**: ConversationManager, RAGManager
- **機能**: マルチターン対話、コンテキスト管理、会話履歴保持

#### Slack PM Worker
- **パス**: `/home/aicompany/ai_co/workers/slack_pm_worker.py`
- **クラス**: `SlackPMWorker`
- **継承**: 独自実装
- **キュー**: `ai_slack_pm` → `ai_results`
- **依存関係**: SlackPMManager, RateLimitQueueProcessor
- **機能**: Slack統合プロジェクト管理、対話型操作

#### Slack Polling Worker
- **パス**: `/home/aicompany/ai_co/workers/slack_polling_worker.py`
- **クラス**: `SlackPollingWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_slack_polling` → `ai_results`
- **機能**: Slack RTM監視、イベント処理

#### Slack Monitor Worker
- **パス**: `/home/aicompany/ai_co/workers/slack_monitor_worker.py`
- **クラス**: `SlackMonitorWorker`
- **継承**: BaseWorker ✅
- **キュー**: なし (監視専用)
- **依存関係**: SlackNotifier
- **機能**: ログ監視、エラー自動通知、閾値ベース検知

### 🔧 Utility Workers

#### Command Executor Worker
- **パス**: `/home/aicompany/ai_co/workers/command_executor_worker.py`
- **クラス**: `CommandExecutorWorker`
- **継承**: BaseWorker ✅ (Phase 2で確認)
- **キュー**: `ai_command` → `ai_results`
- **機能**: 
  - セキュリティチェック付きコマンド実行
  - 実行ログ保存 (ai_commands/logs/)
  - タイムアウト管理 (5分)
  - 危険コマンド検出

#### Email Notification Worker
- **パス**: `/home/aicompany/ai_co/workers/email_notification_worker.py`
- **クラス**: `EmailNotificationWorker`
- **継承**: BaseWorker ✅ (Phase 2で確認)
- **キュー**: `ai_email` → `ai_results`
- **依存関係**: Gmail API (オプション)
- **機能**: 
  - Gmail API連携
  - 添付ファイル対応
  - フォールバック (ログ保存)

#### Todo Worker
- **パス**: `/home/aicompany/ai_co/workers/todo_worker.py`
- **クラス**: `TodoWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_todo` → `ai_results`
- **依存関係**: AIGrowthTodoManager
- **機能**: ToDoリスト自律処理、学習機能

### 🔍 Intelligence Workers

#### Error Intelligence Worker
- **パス**: `/home/aicompany/ai_co/workers/error_intelligence_worker.py`
- **クラス**: `ErrorIntelligenceWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_error_intelligence` → `ai_results`
- **依存関係**: RAGManager, 複数の解析ライブラリ
- **機能**: 
  - エラーパターン認識
  - 自動修正提案
  - インシデント管理連携
  - 学習型エラー解析

#### Image Pipeline Worker
- **パス**: `/home/aicompany/ai_co/workers/image_pipeline_worker.py`
- **クラス**: `ImagePipelineWorker`
- **継承**: 独自実装
- **キュー**: `ai_image_pipeline` → `ai_results`
- **機能**: 画像処理ワークフロー、多段階パイプライン

### 🧪 Testing Workers

#### Test Manager Worker
- **パス**: `/home/aicompany/ai_co/workers/test_manager_worker.py`
- **クラス**: `TestManagerWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_test_manager` → `ai_se`
- **機能**: 
  - 自動テスト実行
  - SEワーカー連携
  - カバレッジ管理
  - 再試行制御

#### Test Generator Worker
- **パス**: `/home/aicompany/ai_co/workers/test_generator_worker.py`
- **クラス**: `TestGeneratorWorker`
- **継承**: BaseWorker ✅
- **キュー**: `ai_test_generator` → `ai_results`
- **機能**: テストコード自動生成、カバレッジ分析

## 📚 ライブラリコンポーネント

### Communication & Messaging
- **SlackNotifier** (`libs/slack_notifier.py`): Slack統合通知
- **WorkerCommunication** (`core/worker_communication.py`): ワーカー間通信
- **CommunicationMixin**: send_to_worker()機能提供

### Project Management
- **ProjectDesignManager** (`libs/project_design_manager.py`): プロジェクト設計管理
- **GitHubFlowManager** (`libs/github_flow_manager.py`): Git Flow自動化
- **QualityChecker** (`libs/quality_checker.py`): 品質管理システム

### Data & Knowledge Management  
- **RAGManager** (`libs/rag_manager.py`): 検索拡張生成
- **ConversationManager** (`libs/conversation_manager.py`): 対話管理
- **TaskHistoryDB** (`libs/task_history_db.py`): タスク履歴管理
- **KnowledgeAwareMixin**: ナレッジベース連携

### AI & Templates
- **PromptTemplateMixin** (`core/prompt_template_mixin.py`): プロンプトテンプレート
- **AICommandHelper** (`libs/ai_command_helper.py`): AIコマンド支援
- **ClaudeClientWithRotation**: Claude API管理

### System Management
- **SelfEvolutionManager** (`libs/self_evolution_manager.py`): システム自己進化
- **WorkerMonitor**: ワーカー監視
- **RateLimitQueueProcessor**: レート制限処理

## 🏗️ Core基盤

### BaseWorker
- **パス**: `/home/aicompany/ai_co/core/base_worker.py`
- **機能**: 
  - RabbitMQ接続管理 (統一キュー名: `ai_{worker_type}`)
  - 統一エラーハンドリング
  - 標準ロギング
  - Slack通知統合
  - 自動リトライ機構

### BaseWorker継承状況
```
✅ 継承済み (14/20): 70%
- enhanced_pm_worker
- enhanced_task_worker  
- result_worker
- dialog_task_worker (Phase 2で修正)
- command_executor_worker (Phase 2で確認)
- email_notification_worker (Phase 2で確認)
- error_intelligence_worker
- slack_monitor_worker
- slack_polling_worker
- todo_worker
- test_manager_worker
- test_generator_worker

❌ 未継承 (6/20): 30%  
- slack_pm_worker (独自実装)
- image_pipeline_worker (独自実装)
- [その他レガシーワーカー]
```

## 🔗 統合状況

### ✅ 統合完了
- **PMワーカー統合**: 4個 → 1個 (enhanced_pm_worker.py)
- **TaskWorker統合**: 4個 → 1個 (enhanced_task_worker.py)  
- **品質管理統合**: quality_pm_worker → enhanced_pm_worker
- **キュー名統一**: 100%完了
- **重複ライブラリ整理**: 完了

### 🔄 今後の統合予定
- エラーハンドリング標準化 (Phase 3)
- ログ出力統一 (Phase 3)
- 監視機能統合 (Phase 4)

## 📊 メトリクス

- **総ワーカー数**: 14個 (重複削除後)
- **BaseWorker継承率**: 70% (14/20)
- **キュー統一率**: 100%
- **重複削除効果**: 60%減
- **統合済みPM機能**: 6個の機能統合

---
*このカタログはPhase 1-3システム統合完了時点での最新情報です*