# 🎯 AI Company 統合ナレッジベース

生成日時: 2025-07-08 02:02:07

## 📊 エグゼクティブサマリー

- **プロジェクトバージョン**: 51807bd
- **総ファイル数**: 1302
- **総行数**: 244531
- **ワーカー数**: 27
- **マネージャー数**: 34
- **コマンド数**: 63

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
task_worker.py - Enhanced Task Workerへのエイリアス

既存のテストとの互換性のために作成
- クラス: 
- 関数数: 0
- 行数: 9

#### async_enhanced_task_worker
- クラス: FileChangeHandler, AsyncEnhancedTaskWorker
- 関数数: 0
- 行数: 468

#### intelligent_pm_worker
- クラス: IntelligentPMWorker
- 関数数: 0
- 行数: 459

#### slack_monitor_worker
- クラス: SlackMonitorWorker
- 関数数: 0
- 行数: 124

#### error_intelligence_worker
- クラス: ErrorIntelligenceWorker
- 関数数: 1
- 行数: 81

#### code_review_pm_worker
- クラス: CodeReviewPMWorker
- 関数数: 0
- 行数: 301

#### pm_worker
pm_worker.py - Enhanced PM Workerへのエイリアス

既存のテストとの互換性のために作成
- クラス: 
- 関数数: 0
- 行数: 9

#### rag_wizards_worker
- クラス: RAGWizardsWorker
- 関数数: 0
- 行数: 399

#### command_executor_worker
- クラス: CommandExecutorWorker
- 関数数: 0
- 行数: 312

#### code_review_task_worker
- クラス: CodeReviewTaskWorker
- 関数数: 0
- 行数: 284

#### slack_polling_worker
- クラス: SlackPollingWorker
- 関数数: 1
- 行数: 503

#### email_notification_worker
- クラス: AutoRepairedComponent
- 関数数: 0
- 行数: 26

#### test_generator_worker
- クラス: TestTestGeneratorWorker
- 関数数: 0
- 行数: 39

#### knowledge_scheduler_worker
- クラス: KnowledgeManagementScheduler
- 関数数: 1
- 行数: 246

#### image_pipeline_worker
- クラス: ImageProcessingWorker, ThumbnailWorker
- 関数数: 0
- 行数: 331

#### simple_task_worker
- クラス: SimpleTaskWorker
- 関数数: 2
- 行数: 400

#### code_review_result_worker
- クラス: CodeReviewResultWorker
- 関数数: 0
- 行数: 354

#### slack_pm_worker
- クラス: SlackPMWorker
- 関数数: 0
- 行数: 116

#### dialog_task_worker
- クラス: DialogTaskWorker
- 関数数: 0
- 行数: 250

#### enhanced_pm_worker
- クラス: EnhancedPMWorker
- 関数数: 0
- 行数: 748

#### todo_worker
- クラス: TodoWorker
- 関数数: 0
- 行数: 104

#### async_result_worker
- クラス: AsyncResultWorker, PeriodicReporter
- 関数数: 0
- 行数: 510

#### test_manager_worker
- クラス: TestTestManagerWorker
- 関数数: 0
- 行数: 39

#### result_worker
- クラス: ResultWorkerV2
- 関数数: 0
- 行数: 498

#### documentation_worker
- クラス: DocumentationWorker
- 関数数: 0
- 行数: 514

#### enhanced_task_worker
- クラス: EnhancedTaskWorker
- 関数数: 0
- 行数: 596

#### async_pm_worker
- クラス: TaskContext, MemoryManager, TaskPhaseManager, AsyncPMWorker
- 関数数: 0
- 行数: 602

### マネージャー実装
#### elf_forest_worker_manager
- クラス: WorkerStatus, WorkerFlowElf, WorkerTimeElf, WorkerBalanceElf, WorkerHealingElf, WorkerWisdomElf, ElfForestWorkerManager
- 関数数: 0

#### self_evolution_manager
- クラス: SelfEvolutionManager
- 関数数: 0

#### enhanced_git_manager
- クラス: EnhancedGitManager
- 関数数: 0

#### unified_config_manager
- クラス: ConfigSource, ConfigValidation, UnifiedConfigManager
- 関数数: 3

#### github_flow_manager
- クラス: GitHubFlowManager
- 関数数: 0

#### task_lock_manager
task_lock_manager - Auto-generated module
Created by Auto Repair Knight to prevent import errors
- クラス: TaskLockManager
- 関数数: 3

#### priority_queue_manager
Priority Queue Manager for API Rate Limiting
API制限時の優先度付きキュー管理システム
- クラス: TaskPriority, TaskStatus, QueuedTask, PriorityQueueManager
- 関数数: 0

#### queue_manager
- クラス: QueueManager
- 関数数: 0

#### ai_growth_todo_manager
- クラス: AIGrowthTodoManager
- 関数数: 2

#### rabbit_manager
- クラス: 
- 関数数: 0

#### incident_manager
- クラス: IncidentManager
- 関数数: 0

#### test_manager
- クラス: TestManager
- 関数数: 0

#### docker_template_manager
- クラス: DockerTemplate, DockerTemplateManager
- 関数数: 0

#### parallel_execution_manager
- クラス: ExecutionStatus, ResourceType, ExecutionGroup, ExecutionResult, ParallelExecutionManager
- 関数数: 0

#### database_manager
- クラス: ConnectionConfig, DatabaseError, ConnectionPoolError, TransactionError, ConnectionPool, Transaction, DatabaseManager
- 関数数: 1

#### api_key_manager
API Key Rotation Manager
複数のAPIキーを管理し、レート制限時の自動切り替えを行う
- クラス: RotationStrategy, APIKeyStatus, APIKeyInfo, APIKeyManager
- 関数数: 0

#### resource_isolation_manager
- クラス: ResourceType, IsolationType, ResourceStatus, ResourceQuota, ResourceUsage, IsolationContext, ResourceAlert, ResourceIsolationManager, ResourceMonitor, AlertManager
- 関数数: 0

#### auto_project_manager
- クラス: ProjectRisk, AutoProjectManager
- 関数数: 0

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

#### ai_project_placement_manager
- クラス: PlacementStrategy, ResourceType, PlacementCriteria, PlacementRecommendation, AIProjectPlacementManager
- 関数数: 0

#### localization_manager
- クラス: LocalizationManager
- 関数数: 3

#### knowledge_base_manager
- クラス: KnowledgeBaseManager, KnowledgeAwareMixin
- 関数数: 0

#### unified_entity_manager
unified_entity_manager - Auto-generated module
Created by Auto Repair Knight to prevent import errors
- クラス: UnifiedEntityManager
- 関数数: 3

#### project_design_manager
- クラス: ProjectDesignManager
- 関数数: 0

#### conversation_manager
- クラス: ConversationManager
- 関数数: 0

#### unified_item_manager
- クラス: ItemInfo, AllocationRecord, LegacySystemConnector, UnifiedItemManager
- 関数数: 1

#### slack_pm_manager
- クラス: AutoRepairedComponent
- 関数数: 0

#### log_manager
- クラス: LogManager
- 関数数: 1

#### autoscaling_manager
- クラス: AutoScalingManager, AutoScalableWorker
- 関数数: 0

#### enhanced_rag_manager
- クラス: VectorEmbedding, SearchResult, KnowledgeNode, KnowledgeEdge, LanguageCode, EnhancedRAGManager
- 関数数: 0

#### unified_rag_manager
unified_rag_manager - Auto-generated module
Created by Auto Repair Knight to prevent import errors
- クラス: UnifiedRagManager
- 関数数: 3

## 📚 ナレッジベース

### 含まれるドキュメント
- **SYSTEM_DUPLICATION_ANALYSIS.md** (194 lines)
- **four_sages_emergency_council_2025_07_06.md** (118 lines)
- **slack_worker_recovery_council_request.md** (162 lines)
- **KNIGHT_GITHUB_ACTIONS_STATUS_69a2077.md** (116 lines)
- **IMPLEMENTATION_SUMMARY_AI_EVOLUTION_2025_07.md** (207 lines)
- **PM_WORKER_SLACK_INTEGRATION_2025_07_06.md** (229 lines)
- **AI_COMPANY_MASTER_KB_v6.1.md** (252 lines)
- **elders_consultation_system_integration_2025_07_06.md** (264 lines)
- **INCIDENT_KNIGHTS_REMAINING_TASKS.md** (219 lines)
- **99999_uptime_phase1_completion_report.md** (96 lines)
- **council_20250708_014001_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **AI_Company_New_Features_Guide_v5.1.md** (389 lines)
- **RAG_WIZARDS_WEEK2_STRATEGIC_ROADMAP.md** (297 lines)
- **api_specifications.md** (331 lines)
- **worker_refactoring_design.md** (361 lines)
- **component_catalog_v6.1.md** (243 lines)
- **ELDER_MONITORING_RECOVERY_COMPLETE.md** (105 lines)
- **system_architecture.md** (296 lines)
- **fantasy_task_classification_system.md** (256 lines)
- **worker_auto_recovery_plan.md** (175 lines)
- **council_20250706_230642_test_coverage_critical_elder_council_request.md** (98 lines)
- **UPDATE_NOTES_v5.1.md** (160 lines)
- **council_20250708_015344_test_coverage_critical_elder_council_request.md** (98 lines)
- **council_20250706_230642_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **elder_council_request_99999_uptime_20250707.md** (135 lines)
- **TEST_COVERAGE_UNIFIED_BATTLE_PLAN.md** (179 lines)
- **Command_Executor_Repair_System_v2.0.md** (305 lines)
- **elder_council_response_20250707_024000.md** (80 lines)
- **SYSTEM_STATUS_202507.md** (121 lines)
- **Error_Intelligence_Phase2_Design.md** (257 lines)
- **KNOWLEDGE_UPDATE_TRIGGERS.md** (166 lines)
- **elders_critical_report_approval_system_gap_20250707.md** (160 lines)
- **council_20250707_233208_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **ELDER_COUNCIL_100_PERCENT_COVERAGE_STRATEGIC_PLAN.md** (316 lines)
- **elder_council_implementation_complete_2025_07_06.md** (255 lines)
- **component_catalog.md** (313 lines)
- **phase3_roadmap_20250707.md** (126 lines)
- **FOUR_SAGES_UNIFIED_WISDOM_INTEGRATION.md** (482 lines)
- **Error_Intelligence_Quick_Guide.md** (72 lines)
- **ELDER_TASK_DECISION_20250707.md** (59 lines)
- **MISSION_COMPLETE_100_PERCENT_AUTONOMOUS.md** (240 lines)
- **ERROR_HANDLING_KB_v1.0.md** (305 lines)
- **ELDER_REPORTING_RULES_DECISION.md** (77 lines)
- **AI_Command_Executor_Knowledge_v1.1.md** (420 lines)
- **council_request_processor_urgent_implementation.md** (151 lines)
- **council_20250708_015344_worker_system_critical_elder_council_request.md** (98 lines)
- **sage_coordination_update_2025_07_06.md** (50 lines)
- **TEST_GUARDIAN_KNIGHT_DOCUMENTATION.md** (128 lines)
- **incident_knights_deployment_report.md** (52 lines)
- **Error_Intelligence_System_Design_v1.0.md** (609 lines)
- **TEST_COVERAGE_PHASE1_BATTLE_REPORT.md** (157 lines)
- **INCIDENT_KNIGHTS_SUCCESS_REPORT.md** (156 lines)
- **knights_ai_debug_implementation_kickoff.md** (81 lines)
- **elders_consultation_2025_07_06_post_backup.md** (193 lines)
- **ELDER_SERVANT_TRAINING_MANUAL.md** (475 lines)
- **KB_GitCommitBestPractices.md** (337 lines)
- **creator_profile_and_vision.md** (114 lines)
- **test_coverage_progress_20250707.md** (102 lines)
- **council_20250708_014001_test_coverage_critical_elder_council_request.md** (98 lines)
- **RAG_WIZARDS_STRATEGIC_OPTIMIZATION_COMPLETE.md** (251 lines)
- **elder_council_strategic_progress_report_60_percent_mission.md** (169 lines)
- **DOCKER_API_DOCUMENTATION.md** (275 lines)
- **council_20250706_230433_test_coverage_critical_elder_council_request.md** (98 lines)
- **FEATURE_TREE.md** (157 lines)
- **MIGRATION_READY_ASSESSMENT.md** (164 lines)
- **GITHUB_FLOW_COMPLETE_KB.md** (268 lines)
- **commit_best_practices_kb.md** (323 lines)
- **ELF_FOREST_SYSTEM_DESIGN.md** (341 lines)
- **ai_elder_unified_command_implementation_report.md** (203 lines)
- **council_20250708_013926_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **environment_variables_rule.md** (130 lines)
- **implementation_complete_worker_recovery_2025_07_06.md** (200 lines)
- **council_20250708_015149_worker_system_critical_elder_council_request.md** (98 lines)
- **slack_dialogue_crisis_council_request.md** (146 lines)
- **data_structures.md** (332 lines)
- **daily_achievement_20250707.md** (108 lines)
- **SYSTEM_CONSOLIDATION_PLAN.md** (253 lines)
- **work_resumption_request_20250707.md** (71 lines)
- **ELDER_REPORTING_RULES_PROPOSAL.md** (215 lines)
- **final_status_20250707.md** (96 lines)
- **ELDER_COUNCIL_METHODOLOGY_INDEX.md** (56 lines)
- **ELDER_COUNCIL_SUMMONER_DOCUMENTATION.md** (441 lines)
- **emergency_elder_consultation_20250707.md** (176 lines)
- **incident_knights_request_ai_debug_20250707.md** (126 lines)
- **command_naming_conventions.md** (88 lines)
- **elder_council_response_20250707_012500.md** (101 lines)
- **NEXT_PLAN_AI_EVOLUTION.md** (309 lines)
- **elder_council_test_coverage_report_20250707.md** (124 lines)
- **elder_greetings_report.md** (116 lines)
- **INCIDENT_KNIGHTS_ELDER_COUNCIL_SUMMONING_COMPLETE.md** (198 lines)
- **council_20250708_013926_worker_system_critical_elder_council_request.md** (98 lines)
- **fantasy_incident_classification_proposal.md** (180 lines)
- **council_20250706_230433_worker_system_critical_elder_council_request.md** (98 lines)
- **elders_consistency_review_request_20250707.md** (161 lines)
- **PHASE_1_5_UNIFIED_BATTLE_COMPLETE_REPORT.md** (170 lines)
- **PM_WORKER_SLACK_INTEGRATION_COMPLETE.md** (231 lines)
- **KNOWLEDGE_MANAGEMENT_GUIDE.md** (141 lines)
- **elder_emergency_repair_success_report_20250707.md** (164 lines)
- **elders_special_consultation_consistency_check.md** (140 lines)
- **maru_personal_knowledge.md** (209 lines)
- **ELDER_COUNCIL_STRATEGIC_SESSION_RESPONSE.md** (304 lines)
- **WEEK2_VICTORY_REPORT_ELDER_SERVANTS.md** (162 lines)
- **README.md** (89 lines)
- **four_sages_meeting_worker_stability_2025_07_06.md** (286 lines)
- **cleanup_report_20250707.md** (166 lines)
- **council_20250708_015149_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **council_20250708_015344_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **COVERAGE_KNIGHTS_WEEK2_REPORT.md** (24 lines)
- **TEST_COVERAGE_IMPROVEMENT_KB.md** (159 lines)
- **council_20250708_013926_test_coverage_critical_elder_council_request.md** (98 lines)
- **council_20250707_233208_worker_system_critical_elder_council_request.md** (98 lines)
- **elder_council_knights_command_implementation_20250707_024500.md** (163 lines)
- **council_20250708_015149_test_coverage_critical_elder_council_request.md** (98 lines)
- **.elders_knowledge_index.md** (73 lines)
- **07_ai_git_best_practices_kb.md** (476 lines)
- **elder_council_reporting_rules_consultation.md** (173 lines)
- **SYSTEM_CONSOLIDATION_UPDATE_v6.1.md** (121 lines)
- **INCIDENT_KNIGHTS_GITHUB_ACTIONS_RESPONSIBILITY.md** (260 lines)
- **elders_report_2025_07_06_ai_report_implementation.md** (145 lines)
- **INCIDENT_KNIGHTS_COMMAND_GUARDIAN.md** (244 lines)
- **INCIDENT_SAGE_EVOLUTION_SUMMARY.md** (192 lines)
- **CLAUDE_CLI_NEXT_PLAN_INTEGRATION.md** (292 lines)
- **Error_Intelligence_Phase3_Design.md** (246 lines)
- **elder_servants_mission_orders_60_percent_coverage.md** (235 lines)
- **council_20250706_230243_simulation_test_elder_council_request.md** (58 lines)
- **elder_council_consultation_20250707_comprehensive.md** (162 lines)
- **INCIDENT_KNIGHTS_DESIGN.md** (327 lines)
- **AI_Company_Core_Knowledge_v5.1.md** (435 lines)
- **system_architecture_v6.1.md** (273 lines)
- **council_20250706_222326_simulation_test_elder_council_request.md** (58 lines)
- **elders_report_2025_07_06_2100.md** (106 lines)
- **elders_hierarchy_definition_20250707.md** (79 lines)
- **council_20250708_014001_worker_system_critical_elder_council_request.md** (98 lines)
- **PHASE6_MIGRATION_SUCCESS_REPORT.md** (308 lines)
- **GRIMOIRE_MIGRATION_PLAN.md** (332 lines)
- **ELDER_COUNCIL_OVERSIGHT_SYSTEM.md** (502 lines)
- **claude_awaiting_elders_guidance_2025_07_06.md** (72 lines)
- **ELF_FOREST_WORKER_FOCUSED_DESIGN.md** (270 lines)
- **UNIVERSAL_CLAUDE_ELDER_STANDARDS.md** (321 lines)
- **PHASE5_MIGRATION_ENGINE_SUMMARY.md** (200 lines)
- **council_20250706_230642_worker_system_critical_elder_council_request.md** (98 lines)
- **commit_best_practices_integration.md** (304 lines)
- **claude_task_request_to_elders.md** (166 lines)
- **elder_council_emergency_test_coverage_plan.md** (211 lines)
- **elder_servants_system_definition.md** (116 lines)
- **elders_consultation_2025_07_06_next_direction.md** (158 lines)
- **ELDER_COUNCIL_99999_AVAILABILITY_PLAN.md** (273 lines)
- **WORKER_AUTO_RECOVERY_DOCUMENTATION.md** (317 lines)
- **IMPLEMENTATION_SUMMARY_2025_07.md** (247 lines)
- **AI_EVOLUTION_SYSTEM_KB_v1.0.md** (298 lines)
- **SLACK_INTEGRATION_LESSONS_LEARNED_2025_07_06.md** (163 lines)
- **council_20250706_230433_resource_allocation_conflict_elder_council_request.md** (92 lines)
- **INCIDENT_PREVENTION_GUIDE.md** (243 lines)
- **sage_coordination_request_2025_07_06.md** (74 lines)
- **AI_Command_Executor_Complete_KB_v2.1.md** (333 lines)
- **CLAUDE_TDD_GUIDE.md** (303 lines)
- **elders_greeting_protocol_definition.md** (185 lines)
- **elder_hierarchy_coordination_success.md** (115 lines)
- **council_20250707_233208_test_coverage_critical_elder_council_request.md** (98 lines)
- **elders_report_20250707_hierarchy_update.md** (70 lines)
- **UNIVERSAL_CLAUDE_ELDER_STANDARDS_METHODOLOGY.md** (360 lines)
- **KNIGHT_SPIRIT_CORE_PHILOSOPHY.md** (157 lines)

## 📈 統計情報

### ファイルタイプ別統計
- .conf: 9 files
- .html: 5 files
- .j2: 7 files
- .json: 227 files
- .jsonl: 3 files
- .md: 371 files
- .new: 8 files
- .old: 1 files
- .py: 499 files
- .service: 3 files
- .sh: 43 files
- .wsgi: 1 files
- .yaml: 6 files
