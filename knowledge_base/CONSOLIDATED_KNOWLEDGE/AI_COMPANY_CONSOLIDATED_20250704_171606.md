# 🎯 AI Company 統合ナレッジベース

生成日時: 2025-07-04 17:16:06

## 📊 エグゼクティブサマリー

- **プロジェクトバージョン**: 2e69db1
- **総ファイル数**: 438
- **総行数**: 63949
- **ワーカー数**: 19
- **マネージャー数**: 17
- **コマンド数**: 57

## 🏗️ システムアーキテクチャ

### レイヤー構成
- **Presentation**: commands, web, scripts
- **Application**: workers, managers
- **Domain**: core, libs
- **Infrastructure**: config, db, logs

### ワークフロー
```
User -> ai-send/ai-dialog
-> RabbitMQ
-> TaskWorker (Claude CLI)
-> PMWorker (File placement)
-> ResultWorker (Notification)
```

## 🔧 実装詳細

### ワーカー実装
#### task_worker
- クラス: TaskWorker
- 関数数: 2
- 行数: 477

#### slack_monitor_worker
- クラス: SlackMonitorWorker
- 関数数: 1
- 行数: 333

#### error_intelligence_worker
- クラス: ErrorIntelligenceWorker
- 関数数: 0
- 行数: 290

#### pm_worker
- クラス: PMWorker
- 関数数: 0
- 行数: 574

#### command_executor_worker
- クラス: CommandExecutorWorker
- 関数数: 0
- 行数: 247

#### slack_polling_worker
- クラス: SlackPollingWorker
- 関数数: 1
- 行数: 345

#### email_notification_worker
- クラス: EmailNotificationWorker
- 関数数: 0
- 行数: 288

#### se_tester_worker
- クラス: SEWorkerWithTesting
- 関数数: 0
- 行数: 324

#### test_generator_worker
- クラス: TestGeneratorWorker
- 関数数: 0
- 行数: 356

#### knowledge_scheduler_worker
- クラス: KnowledgeManagementScheduler, KnowledgeManagementService
- 関数数: 0
- 行数: 238

#### image_pipeline_worker
- クラス: ImageProcessingWorker, ThumbnailWorker
- 関数数: 0
- 行数: 269

#### quality_pm_worker
- クラス: QualityPMWorker
- 関数数: 0
- 行数: 352

#### quality_task_worker
- クラス: QualityTaskWorker
- 関数数: 0
- 行数: 318

#### dialog_task_worker
- クラス: DialogTaskWorker
- 関数数: 0
- 行数: 151

#### enhanced_pm_worker
- クラス: EnhancedPMWorker
- 関数数: 0
- 行数: 451

#### todo_worker
- クラス: TodoWorker
- 関数数: 0
- 行数: 78

#### test_manager_worker
- クラス: TestManagerWorker
- 関数数: 0
- 行数: 303

#### result_worker
- クラス: ResultWorker
- 関数数: 0
- 行数: 373

#### enhanced_task_worker
- クラス: EnhancedTaskWorker
- 関数数: 0
- 行数: 403

### マネージャー実装
#### self_evolution_manager
- クラス: SelfEvolutionManager
- 関数数: 0

#### enhanced_git_manager
- クラス: EnhancedGitManager
- 関数数: 0

#### queue_manager
- クラス: QueueManager
- 関数数: 0

#### ai_growth_todo_manager
- クラス: AIGrowthTodoManager
- 関数数: 2

#### test_manager
- クラス: TestManager
- 関数数: 0

#### database_manager
- クラス: ConnectionConfig, DatabaseError, ConnectionPoolError, TransactionError, ConnectionPool, Transaction, DatabaseManager
- 関数数: 1

#### rag_manager
- クラス: RAGManager
- 関数数: 0

#### error_intelligence_manager
- クラス: ErrorIntelligenceManager
- 関数数: 0

#### test_strategy_manager
- クラス: TestStrategyManager
- 関数数: 0

#### prompt_template_manager
- クラス: PromptTemplateManager
- 関数数: 0

#### localization_manager
- クラス: LocalizationManager
- 関数数: 3

#### git_flow_manager
- クラス: GitFlowManager
- 関数数: 0

#### knowledge_base_manager
- クラス: KnowledgeBaseManager, KnowledgeAwareMixin
- 関数数: 0

#### project_design_manager
- クラス: ProjectDesignManager
- 関数数: 0

#### conversation_manager
- クラス: ConversationManager
- 関数数: 0

#### log_manager
- クラス: LogManager
- 関数数: 1

#### autoscaling_manager
- クラス: AutoScalingManager, AutoScalableWorker
- 関数数: 0

## 📚 ナレッジベース

### 含まれるドキュメント
- **AI_Company_New_Features_Guide_v5.1.md** (389 lines)
- **UPDATE_NOTES_v5.1.md** (160 lines)
- **Error_Intelligence_Phase2_Design.md** (257 lines)
- **Error_Intelligence_Quick_Guide.md** (72 lines)
- **ERROR_HANDLING_KB_v1.0.md** (305 lines)
- **AI_Command_Executor_Knowledge_v1.1.md** (420 lines)
- **AI_COMPANY_MASTER_KB_v5.2.md** (526 lines)
- **Error_Intelligence_System_Design_v1.0.md** (609 lines)
- **KB_GitCommitBestPractices.md** (337 lines)
- **commit_best_practices_kb.md** (323 lines)
- **KNOWLEDGE_MANAGEMENT_GUIDE.md** (141 lines)
- **07_ai_git_best_practices_kb.md** (476 lines)
- **Error_Intelligence_Phase3_Design.md** (246 lines)
- **AI_Company_Core_Knowledge_v5.1.md** (435 lines)
- **commit_best_practices_integration.md** (304 lines)

## 📈 統計情報

### ファイルタイプ別統計
- .20250702_092452: 1 files
- .backup_20250703_011520: 2 files
- .backup_20250703_132211: 1 files
- .bak: 1 files
- .bak_20250703_145742: 1 files
- .conf: 7 files
- .j2: 7 files
- .json: 20 files
- .jsonl: 2 files
- .md: 18 files
- .py: 250 files
- .sh: 55 files
- .yaml: 3 files
