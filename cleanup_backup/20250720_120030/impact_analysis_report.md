# A2A通信専用制限実装 - 影響分析レポート
## エルダー評議会令第30号 Phase 1ステップ1結果

### 📊 統計情報
- 分析対象ファイル数: 56
- 直接呼び出し総数: 288
- インポート総数: 156

### 📁 ファイル分類
- core_sages: 4ファイル
- integration_layers: 5ファイル
- test_files: 33ファイル
- elder_flow: 2ファイル
- backup_files: 4ファイル
- other: 8ファイル

### 🎯 重要度別影響分析
#### 🔴 高重要度 - コアシステム
- `./libs/four_sages/incident/incident_sage.py`: 1個の直接呼び出し, 0個のインポート
- `./libs/four_sages/knowledge/knowledge_sage.py`: 2個の直接呼び出し, 0個のインポート
- `./libs/four_sages/rag/rag_sage.py`: 4個の直接呼び出し, 3個のインポート
- `./libs/four_sages/task/task_sage.py`: 1個の直接呼び出し, 0個のインポート

#### 🟡 中重要度 - 統合レイヤー
- `./libs/utilities/common/phase3_four_sages_integration.py`: 0個の直接呼び出し, 0個のインポート
- `./libs/utilities/common/four_sages_rabbitmq_integration.py`: 0個の直接呼び出し, 0個のインポート
- `./libs/utilities/common/four_sages_simple_integration.py`: 4個の直接呼び出し, 0個のインポート
- `./libs/perfect_a2a/multiprocess_elder_flow_github_perfection.py`: 4個の直接呼び出し, 4個のインポート
- `./libs/elder_system/flow/elder_flow_code_generator.py`: 4個の直接呼び出し, 4個のインポート
- `./libs/elder_flow/integration/four_sages.py`: 4個の直接呼び出し, 4個のインポート
- `./libs/elder_flow/integration/four_sages_fixed.py`: 4個の直接呼び出し, 4個のインポート
- `./libs/elder_flow/execution/elder_code_generator.py`: 4個の直接呼び出し, 4個のインポート

#### 🟢 低重要度 - テストファイル
- 33個のテストファイル

### 🔍 詳細分析
#### ./libs/utilities/common/four_sages_simple_integration.py
**直接呼び出し:**
- Line 268: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 269: TaskSage() (引数: 0, キーワード: 0)
- Line 270: IncidentSage() (引数: 0, キーワード: 0)
- Line 271: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/perfect_a2a/multiprocess_elder_flow_github_perfection.py
**インポート:**
- Line 26: libs.four_sages.task.task_sage.TaskSage
- Line 27: libs.four_sages.incident.incident_sage.IncidentSage
- Line 28: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 29: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 54: TaskSage() (引数: 0, キーワード: 0)
- Line 55: IncidentSage() (引数: 0, キーワード: 0)
- Line 56: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 57: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/four_sages/incident/incident_sage.py
**直接呼び出し:**
- Line 1309: IncidentSage() (引数: 0, キーワード: 0)

#### ./libs/four_sages/knowledge/knowledge_sage.py
**直接呼び出し:**
- Line 865: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 876: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./libs/four_sages/rag/rag_sage.py
**インポート:**
- Line 1258: knowledge.knowledge_sage.KnowledgeSage
- Line 1266: task.task_sage.TaskSage
- Line 1274: incident.incident_sage.IncidentSage
**直接呼び出し:**
- Line 1259: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 1267: TaskSage() (引数: 0, キーワード: 0)
- Line 1275: IncidentSage() (引数: 0, キーワード: 0)
- Line 1593: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/four_sages/task/task_sage.py
**直接呼び出し:**
- Line 1114: TaskSage() (引数: 0, キーワード: 0)

#### ./libs/elder_system/flow/elder_flow_code_generator.py
**インポート:**
- Line 26: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 27: libs.four_sages.incident.incident_sage.IncidentSage
- Line 28: libs.four_sages.task.task_sage.TaskSage
- Line 29: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 63: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 64: IncidentSage() (引数: 0, キーワード: 0)
- Line 65: TaskSage() (引数: 0, キーワード: 0)
- Line 66: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/elder_flow/integration/four_sages.py
**インポート:**
- Line 32: knowledge_sage.KnowledgeSage
- Line 33: task_sage.TaskSage
- Line 34: incident_sage.IncidentSage
- Line 35: rag_sage.RAGSage
**直接呼び出し:**
- Line 90: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 91: TaskSage() (引数: 0, キーワード: 0)
- Line 92: IncidentSage() (引数: 0, キーワード: 0)
- Line 93: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/elder_flow/integration/four_sages_fixed.py
**インポート:**
- Line 18: core.sages.knowledge.KnowledgeSage
- Line 19: core.sages.task.TaskSage
- Line 20: core.sages.incident.IncidentSage
- Line 21: core.sages.rag.RAGSage
**直接呼び出し:**
- Line 47: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 48: TaskSage() (引数: 0, キーワード: 0)
- Line 49: IncidentSage() (引数: 0, キーワード: 0)
- Line 50: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/elder_flow/execution/elder_code_generator.py
**インポート:**
- Line 26: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 27: libs.four_sages.incident.incident_sage.IncidentSage
- Line 28: libs.four_sages.task.task_sage.TaskSage
- Line 29: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 63: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 64: IncidentSage() (引数: 0, キーワード: 0)
- Line 65: TaskSage() (引数: 0, キーワード: 0)
- Line 66: RAGSage() (引数: 0, キーワード: 0)

#### ./libs/ai_systems/automation/ai_priority_optimizer.py
**直接呼び出し:**
- Line 224: TaskSage() (引数: 0, キーワード: 0)
- Line 225: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 226: IncidentSage() (引数: 0, キーワード: 0)
- Line 227: RAGSage() (引数: 0, キーワード: 0)

#### ./perfect_real_truth_test.py
**インポート:**
- Line 117: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 170: libs.four_sages.task.task_sage.TaskSage
- Line 201: libs.four_sages.incident.incident_sage.IncidentSage
- Line 232: libs.four_sages.rag.rag_sage.RAGSage
- Line 573: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 574: libs.four_sages.task.task_sage.TaskSage
- Line 575: libs.four_sages.incident.incident_sage.IncidentSage
- Line 576: libs.four_sages.rag.rag_sage.RAGSage
- Line 838: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 904: libs.four_sages.rag.rag_sage.RAGSage
- Line 992: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 1080: libs.four_sages.task.task_sage.TaskSage
- Line 1165: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 1166: libs.four_sages.task.task_sage.TaskSage
- Line 1167: libs.four_sages.incident.incident_sage.IncidentSage
- Line 1168: libs.four_sages.rag.rag_sage.RAGSage
- Line 1267: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 119: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 172: TaskSage() (引数: 0, キーワード: 0)
- Line 203: IncidentSage() (引数: 0, キーワード: 0)
- Line 234: RAGSage() (引数: 0, キーワード: 0)
- Line 579: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 580: TaskSage() (引数: 0, キーワード: 0)
- Line 581: IncidentSage() (引数: 0, キーワード: 0)
- Line 582: RAGSage() (引数: 0, キーワード: 0)
- Line 840: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 906: RAGSage() (引数: 0, キーワード: 0)
- Line 994: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 1082: TaskSage() (引数: 0, キーワード: 0)
- Line 1171: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 1172: TaskSage() (引数: 0, キーワード: 0)
- Line 1173: IncidentSage() (引数: 0, キーワード: 0)
- Line 1174: RAGSage() (引数: 0, キーワード: 0)
- Line 1269: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./scripts/phase1_test_generator.py
**インポート:**
- Line 19: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 20: libs.four_sages.incident.incident_sage.IncidentSage
**直接呼び出し:**
- Line 27: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 28: IncidentSage() (引数: 0, キーワード: 0)

#### ./scripts/consult_ai_command_reorganization.py
**インポート:**
- Line 16: libs.incident_sage.IncidentSage
- Line 17: libs.knowledge_sage.KnowledgeSage
- Line 18: libs.rag_sage.RAGSage
**直接呼び出し:**
- Line 26: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 28: IncidentSage() (引数: 0, キーワード: 0)
- Line 29: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/integration/test_ai_evolution_foundation.py
**インポート:**
- Line 24: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 34: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./tests/test_four_sages_integration.py
**インポート:**
- Line 19: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 20: libs.four_sages.task.task_sage.TaskSage
- Line 21: libs.four_sages.incident.incident_sage.IncidentSage
- Line 22: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 40: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 41: TaskSage() (引数: 0, キーワード: 0)
- Line 42: IncidentSage() (引数: 0, キーワード: 0)
- Line 43: RAGSage() (引数: 0, キーワード: 0)
- Line 715: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 716: TaskSage() (引数: 0, キーワード: 0)
- Line 717: IncidentSage() (引数: 0, キーワード: 0)
- Line 718: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_sages_task.py
**インポート:**
- Line 17: core.sages.task.TaskSage
**直接呼び出し:**
- Line 25: TaskSage() (引数: 0, キーワード: 0)
- Line 34: TaskSage() (引数: 0, キーワード: 1)
- Line 42: TaskSage() (引数: 0, キーワード: 1)
- Line 49: TaskSage() (引数: 0, キーワード: 0)
- Line 75: TaskSage() (引数: 0, キーワード: 0)
- Line 88: TaskSage() (引数: 0, キーワード: 0)
- Line 101: TaskSage() (引数: 0, キーワード: 0)
- Line 110: TaskSage() (引数: 0, キーワード: 0)
- Line 130: TaskSage() (引数: 0, キーワード: 0)
- Line 140: TaskSage() (引数: 0, キーワード: 0)
- Line 160: TaskSage() (引数: 0, キーワード: 0)
- Line 188: TaskSage() (引数: 0, キーワード: 0)
- Line 197: TaskSage() (引数: 0, キーワード: 0)
- Line 209: TaskSage() (引数: 0, キーワード: 0)
- Line 218: TaskSage() (引数: 0, キーワード: 0)
- Line 237: TaskSage() (引数: 0, キーワード: 0)
- Line 250: TaskSage() (引数: 0, キーワード: 0)
- Line 262: TaskSage() (引数: 0, キーワード: 1)
- Line 310: TaskSage() (引数: 0, キーワード: 0)
- Line 337: TaskSage() (引数: 0, キーワード: 0)

#### ./tests/test_config.py
**インポート:**
- Line 188: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 189: libs.four_sages.task.task_sage.TaskSage
- Line 190: libs.four_sages.incident.incident_sage.IncidentSage
- Line 191: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 194: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 195: TaskSage() (引数: 0, キーワード: 0)
- Line 196: IncidentSage() (引数: 0, キーワード: 0)
- Line 197: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_error_cases_boundary_values.py
**インポート:**
- Line 25: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 26: libs.four_sages.task.task_sage.TaskSage
- Line 27: libs.four_sages.incident.incident_sage.IncidentSage
- Line 28: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 60: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 61: TaskSage() (引数: 0, キーワード: 0)
- Line 62: IncidentSage() (引数: 0, キーワード: 0)
- Line 63: RAGSage() (引数: 0, キーワード: 0)
- Line 644: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 645: TaskSage() (引数: 0, キーワード: 0)
- Line 646: IncidentSage() (引数: 0, キーワード: 0)
- Line 647: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_comprehensive_integration.py
**インポート:**
- Line 21: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 22: libs.four_sages.task.task_sage.TaskSage
- Line 23: libs.four_sages.incident.incident_sage.IncidentSage
- Line 24: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 62: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 63: TaskSage() (引数: 0, キーワード: 0)
- Line 64: IncidentSage() (引数: 0, キーワード: 0)
- Line 65: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_actual_working.py
**インポート:**
- Line 50: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 53: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_sages_incident.py
**インポート:**
- Line 16: core.sages.incident.IncidentSage
**直接呼び出し:**
- Line 24: IncidentSage() (引数: 0, キーワード: 0)
- Line 32: IncidentSage() (引数: 0, キーワード: 1)
- Line 39: IncidentSage() (引数: 0, キーワード: 1)
- Line 45: IncidentSage() (引数: 0, キーワード: 0)
- Line 61: IncidentSage() (引数: 0, キーワード: 0)
- Line 76: IncidentSage() (引数: 0, キーワード: 0)
- Line 88: IncidentSage() (引数: 0, キーワード: 0)
- Line 104: IncidentSage() (引数: 0, キーワード: 0)
- Line 116: IncidentSage() (引数: 0, キーワード: 0)
- Line 137: IncidentSage() (引数: 0, キーワード: 0)
- Line 161: IncidentSage() (引数: 0, キーワード: 0)
- Line 173: IncidentSage() (引数: 0, キーワード: 1)

#### ./tests/test_four_sages_system.py
**インポート:**
- Line 17: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 18: libs.four_sages.task.task_sage.TaskSage
- Line 19: libs.four_sages.incident.incident_sage.IncidentSage
- Line 20: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 29: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 215: TaskSage() (引数: 0, キーワード: 0)
- Line 372: IncidentSage() (引数: 0, キーワード: 0)
- Line 532: RAGSage() (引数: 0, キーワード: 0)
- Line 720: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 721: TaskSage() (引数: 0, キーワード: 0)
- Line 722: IncidentSage() (引数: 0, キーワード: 0)
- Line 723: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_four_sages_stage2_enhancement.py
**インポート:**
- Line 27: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 28: libs.four_sages.task.task_sage.TaskSage
- Line 29: libs.four_sages.incident.incident_sage.IncidentSage
- Line 30: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 39: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 137: TaskSage() (引数: 0, キーワード: 0)
- Line 245: IncidentSage() (引数: 0, キーワード: 0)
- Line 365: RAGSage() (引数: 0, キーワード: 0)
- Line 477: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 478: TaskSage() (引数: 0, キーワード: 0)
- Line 479: IncidentSage() (引数: 0, キーワード: 0)
- Line 480: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_high_coverage.py
**インポート:**
- Line 23: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 42: libs.four_sages.task.task_sage.TaskSage
- Line 48: libs.four_sages.incident.incident_sage.IncidentSage
- Line 54: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 24: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 43: TaskSage() (引数: 0, キーワード: 0)
- Line 49: IncidentSage() (引数: 0, キーワード: 0)
- Line 55: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_four_sages_comprehensive_fixed.py
**インポート:**
- Line 29: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 387: libs.four_sages.task.task_sage.TaskSage
- Line 509: libs.four_sages.incident.incident_sage.IncidentSage
- Line 616: libs.four_sages.rag.rag_sage.RAGSage
- Line 735: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 736: libs.four_sages.task.task_sage.TaskSage
- Line 737: libs.four_sages.incident.incident_sage.IncidentSage
- Line 738: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 30: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 388: TaskSage() (引数: 0, キーワード: 0)
- Line 510: IncidentSage() (引数: 0, キーワード: 0)
- Line 617: RAGSage() (引数: 0, キーワード: 0)
- Line 741: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 742: TaskSage() (引数: 0, キーワード: 0)
- Line 743: IncidentSage() (引数: 0, キーワード: 0)
- Line 744: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_core_systems_coverage.py
**インポート:**
- Line 23: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 29: libs.four_sages.task.task_sage.TaskSage
- Line 35: libs.four_sages.incident.incident_sage.IncidentSage
- Line 41: libs.four_sages.rag.rag_sage.RAGSage
- Line 178: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 24: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 30: TaskSage() (引数: 0, キーワード: 0)
- Line 36: IncidentSage() (引数: 0, キーワード: 0)
- Line 42: RAGSage() (引数: 0, キーワード: 0)
- Line 180: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_simple_coverage.py
**インポート:**
- Line 21: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 22: libs.four_sages.task.task_sage.TaskSage
- Line 23: libs.four_sages.incident.incident_sage.IncidentSage
- Line 24: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 27: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 28: TaskSage() (引数: 0, キーワード: 0)
- Line 29: IncidentSage() (引数: 0, キーワード: 0)
- Line 30: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_realistic_coverage.py
**インポート:**
- Line 24: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 43: libs.four_sages.task.task_sage.TaskSage
- Line 51: libs.four_sages.incident.incident_sage.IncidentSage
- Line 59: libs.four_sages.rag.rag_sage.RAGSage
- Line 333: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 334: libs.four_sages.task.task_sage.TaskSage
**直接呼び出し:**
- Line 25: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 44: TaskSage() (引数: 0, キーワード: 0)
- Line 52: IncidentSage() (引数: 0, キーワード: 0)
- Line 60: RAGSage() (引数: 0, キーワード: 0)
- Line 336: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 337: TaskSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_four_sages_realistic.py
**インポート:**
- Line 24: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 25: libs.four_sages.task.task_sage.TaskSage
- Line 26: libs.four_sages.incident.incident_sage.IncidentSage
- Line 27: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 36: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 129: TaskSage() (引数: 0, キーワード: 0)
- Line 204: IncidentSage() (引数: 0, キーワード: 0)
- Line 260: RAGSage() (引数: 0, キーワード: 0)
- Line 318: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 319: TaskSage() (引数: 0, キーワード: 0)
- Line 320: IncidentSage() (引数: 0, キーワード: 0)
- Line 321: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_four_sages_practical.py
**インポート:**
- Line 29: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 163: libs.four_sages.task.task_sage.TaskSage
- Line 221: libs.four_sages.incident.incident_sage.IncidentSage
- Line 279: libs.four_sages.rag.rag_sage.RAGSage
- Line 342: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 343: libs.four_sages.task.task_sage.TaskSage
- Line 344: libs.four_sages.incident.incident_sage.IncidentSage
- Line 345: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 30: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 164: TaskSage() (引数: 0, キーワード: 0)
- Line 222: IncidentSage() (引数: 0, キーワード: 0)
- Line 280: RAGSage() (引数: 0, キーワード: 0)
- Line 348: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 349: TaskSage() (引数: 0, キーワード: 0)
- Line 350: IncidentSage() (引数: 0, キーワード: 0)
- Line 351: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_coverage_boost.py
**インポート:**
- Line 22: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 42: libs.four_sages.task.task_sage.TaskSage
- Line 57: libs.four_sages.incident.incident_sage.IncidentSage
- Line 72: libs.four_sages.rag.rag_sage.RAGSage
- Line 435: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 24: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 44: TaskSage() (引数: 0, キーワード: 0)
- Line 59: IncidentSage() (引数: 0, キーワード: 0)
- Line 74: RAGSage() (引数: 0, キーワード: 0)
- Line 437: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_iron_will_coverage.py
**インポート:**
- Line 27: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 52: libs.four_sages.task.task_sage.TaskSage
- Line 61: libs.four_sages.incident.incident_sage.IncidentSage
- Line 70: libs.four_sages.rag.rag_sage.RAGSage
- Line 438: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 29: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 54: TaskSage() (引数: 0, キーワード: 0)
- Line 63: IncidentSage() (引数: 0, キーワード: 0)
- Line 72: RAGSage() (引数: 0, キーワード: 0)
- Line 440: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_four_sages_comprehensive.py
**インポート:**
- Line 26: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 319: libs.four_sages.task.task_sage.TaskSage
- Line 432: libs.four_sages.incident.incident_sage.IncidentSage
- Line 553: libs.four_sages.rag.rag_sage.RAGSage
- Line 726: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 727: libs.four_sages.task.task_sage.TaskSage
- Line 728: libs.four_sages.incident.incident_sage.IncidentSage
- Line 729: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 27: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 320: TaskSage() (引数: 0, キーワード: 0)
- Line 433: IncidentSage() (引数: 0, キーワード: 0)
- Line 554: RAGSage() (引数: 0, キーワード: 0)
- Line 732: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 733: TaskSage() (引数: 0, キーワード: 0)
- Line 734: IncidentSage() (引数: 0, キーワード: 0)
- Line 735: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/test_additional_coverage.py
**インポート:**
- Line 167: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 486: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 487: libs.four_sages.task.task_sage.TaskSage
- Line 488: libs.four_sages.incident.incident_sage.IncidentSage
- Line 489: libs.four_sages.rag.rag_sage.RAGSage
- Line 516: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 517: libs.four_sages.task.task_sage.TaskSage
**直接呼び出し:**
- Line 168: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 519: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 520: TaskSage() (引数: 0, キーワード: 0)

#### ./tests/unit/core/sages/test_incident_sage.py
**インポート:**
- Line 17: core.sages.incident.IncidentSage
**直接呼び出し:**
- Line 28: IncidentSage() (引数: 0, キーワード: 0)
- Line 197: IncidentSage() (引数: 0, キーワード: 0)

#### ./tests/unit/core/sages/test_rag_sage.py
**インポート:**
- Line 17: core.sages.rag.RAGSage
**直接呼び出し:**
- Line 28: RAGSage() (引数: 0, キーワード: 0)
- Line 202: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/unit/core/sages/test_task_sage.py
**インポート:**
- Line 17: core.sages.task.TaskSage
**直接呼び出し:**
- Line 28: TaskSage() (引数: 0, キーワード: 0)
- Line 178: TaskSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_modules/test_core_sages_task.py
**直接呼び出し:**
- Line 54: TaskSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_modules/test_core_sages_incident.py
**直接呼び出し:**
- Line 54: IncidentSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_modules/test_core_sages_rag.py
**直接呼び出し:**
- Line 54: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_sages_rag.py
**インポート:**
- Line 16: core.sages.rag.RAGSage
**直接呼び出し:**
- Line 24: RAGSage() (引数: 0, キーワード: 0)
- Line 32: RAGSage() (引数: 0, キーワード: 1)
- Line 39: RAGSage() (引数: 0, キーワード: 1)
- Line 45: RAGSage() (引数: 0, キーワード: 0)
- Line 58: RAGSage() (引数: 0, キーワード: 0)
- Line 70: RAGSage() (引数: 0, キーワード: 0)
- Line 81: RAGSage() (引数: 0, キーワード: 0)
- Line 95: RAGSage() (引数: 0, キーワード: 0)
- Line 106: RAGSage() (引数: 0, キーワード: 0)
- Line 117: RAGSage() (引数: 0, キーワード: 0)
- Line 132: RAGSage() (引数: 0, キーワード: 0)
- Line 149: RAGSage() (引数: 0, キーワード: 0)
- Line 170: RAGSage() (引数: 0, キーワード: 0)
- Line 188: RAGSage() (引数: 0, キーワード: 0)
- Line 197: RAGSage() (引数: 0, キーワード: 1)
- Line 213: RAGSage() (引数: 0, キーワード: 1)
- Line 236: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_e2e_full_workflow.py
**インポート:**
- Line 22: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 23: libs.four_sages.task.task_sage.TaskSage
- Line 24: libs.four_sages.incident.incident_sage.IncidentSage
- Line 25: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 65: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 66: TaskSage() (引数: 0, キーワード: 0)
- Line 67: IncidentSage() (引数: 0, キーワード: 0)
- Line 68: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_pgvector_elderflow_integration.py
**インポート:**
- Line 24: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 64: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_sages_enhanced.py
**インポート:**
- Line 16: core.sages.task.TaskSage
- Line 17: core.sages.rag.RAGSage
**直接呼び出し:**
- Line 26: TaskSage() (引数: 0, キーワード: 0)
- Line 38: TaskSage() (引数: 0, キーワード: 0)
- Line 70: TaskSage() (引数: 0, キーワード: 0)
- Line 97: TaskSage() (引数: 0, キーワード: 0)
- Line 114: TaskSage() (引数: 0, キーワード: 0)
- Line 131: TaskSage() (引数: 0, キーワード: 0)
- Line 164: TaskSage() (引数: 0, キーワード: 0)
- Line 188: RAGSage() (引数: 0, キーワード: 0)
- Line 206: RAGSage() (引数: 0, キーワード: 0)
- Line 225: RAGSage() (引数: 0, キーワード: 0)
- Line 246: RAGSage() (引数: 0, キーワード: 0)
- Line 272: RAGSage() (引数: 0, キーワード: 0)
- Line 298: RAGSage() (引数: 0, キーワード: 1)
- Line 310: RAGSage() (引数: 0, キーワード: 0)
- Line 357: TaskSage() (引数: 0, キーワード: 0)
- Line 358: RAGSage() (引数: 0, キーワード: 0)
- Line 388: TaskSage() (引数: 0, キーワード: 0)
- Line 389: RAGSage() (引数: 0, キーワード: 0)

#### ./tests/test_core_sages_incident_comprehensive.py
**インポート:**
- Line 19: core.sages.incident.IncidentSage
**直接呼び出し:**
- Line 27: IncidentSage() (引数: 0, キーワード: 0)
- Line 40: IncidentSage() (引数: 1, キーワード: 0)
- Line 49: IncidentSage() (引数: 1, キーワード: 0)
- Line 56: IncidentSage() (引数: 1, キーワード: 0)
- Line 63: IncidentSage() (引数: 0, キーワード: 0)
- Line 75: IncidentSage() (引数: 0, キーワード: 0)
- Line 92: IncidentSage() (引数: 0, キーワード: 0)
- Line 108: IncidentSage() (引数: 0, キーワード: 0)
- Line 120: IncidentSage() (引数: 0, キーワード: 0)
- Line 145: IncidentSage() (引数: 0, キーワード: 0)
- Line 162: IncidentSage() (引数: 0, キーワード: 0)
- Line 176: IncidentSage() (引数: 0, キーワード: 0)
- Line 199: IncidentSage() (引数: 0, キーワード: 0)
- Line 214: IncidentSage() (引数: 0, キーワード: 0)
- Line 226: IncidentSage() (引数: 0, キーワード: 0)
- Line 249: IncidentSage() (引数: 0, キーワード: 0)
- Line 263: IncidentSage() (引数: 0, キーワード: 0)
- Line 279: IncidentSage() (引数: 0, キーワード: 0)
- Line 302: IncidentSage() (引数: 1, キーワード: 0)
- Line 337: IncidentSage() (引数: 0, キーワード: 0)
- Line 368: IncidentSage() (引数: 0, キーワード: 0)
- Line 381: IncidentSage() (引数: 0, キーワード: 0)
- Line 403: IncidentSage() (引数: 1, キーワード: 0)
- Line 412: IncidentSage() (引数: 1, キーワード: 0)
- Line 437: IncidentSage() (引数: 1, キーワード: 0)
- Line 449: IncidentSage() (引数: 0, キーワード: 0)
- Line 457: IncidentSage() (引数: 0, キーワード: 0)
- Line 467: IncidentSage() (引数: 0, キーワード: 0)
- Line 479: IncidentSage() (引数: 0, キーワード: 0)
- Line 503: IncidentSage() (引数: 0, キーワード: 0)
- Line 533: IncidentSage() (引数: 0, キーワード: 0)

#### ./scan_remaining_issues.py
**インポート:**
- Line 21: libs.four_sages.knowledge.knowledge_sage.KnowledgeSage
- Line 34: libs.four_sages.task.task_sage.TaskSage
- Line 47: libs.four_sages.task.task_sage.TaskSage
- Line 60: libs.four_sages.incident.incident_sage.IncidentSage
- Line 73: libs.four_sages.incident.incident_sage.IncidentSage
- Line 86: libs.four_sages.rag.rag_sage.RAGSage
**直接呼び出し:**
- Line 22: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 35: TaskSage() (引数: 0, キーワード: 0)
- Line 48: TaskSage() (引数: 0, キーワード: 0)
- Line 61: IncidentSage() (引数: 0, キーワード: 0)
- Line 74: IncidentSage() (引数: 0, キーワード: 0)
- Line 87: RAGSage() (引数: 0, キーワード: 0)

#### ./backup/before_audit_integration/libs/four_sages/incident/incident_sage.py
**直接呼び出し:**
- Line 1220: IncidentSage() (引数: 0, キーワード: 0)

#### ./backup/before_audit_integration/libs/four_sages/knowledge/knowledge_sage.py
**直接呼び出し:**
- Line 784: KnowledgeSage() (引数: 0, キーワード: 0)
- Line 795: KnowledgeSage() (引数: 0, キーワード: 0)

#### ./backup/before_audit_integration/libs/four_sages/rag/rag_sage.py
**直接呼び出し:**
- Line 1174: RAGSage() (引数: 0, キーワード: 0)

#### ./backup/before_audit_integration/libs/four_sages/task/task_sage.py
**直接呼び出し:**
- Line 980: TaskSage() (引数: 0, キーワード: 0)

#### ./bin/ai_elder_summon.py
**インポート:**
- Line 15: libs.knowledge_sage.KnowledgeSage
**直接呼び出し:**
- Line 23: KnowledgeSage() (引数: 0, キーワード: 0)

### 💡 移行計画への提言
1. **優先順位**: コアシステム → 統合レイヤー → テストファイル
2. **リスク評価**: 高重要度ファイルは段階的移行が必要
3. **テスト戦略**: 各段階でリグレッションテストを実行
4. **バックアップ**: 既存のバックアップファイルは保持
