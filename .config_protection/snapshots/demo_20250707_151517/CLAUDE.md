# Claude CLI 開発ガイド - AI Company

## 🧙‍♂️ AI Company 4賢者システム

AI Companyは**4つの賢者**が連携して自律的に学習・進化するシステムです：

### 📚 **ナレッジ賢者** (Knowledge Sage)
- **場所**: `knowledge_base/` - ファイルベース知識管理
- **役割**: 過去の英知を蓄積・継承、学習による知恵の進化
- **主要ファイル**: `CLAUDE_TDD_GUIDE.md`, `IMPLEMENTATION_SUMMARY_2025_07.md`

### 📋 **タスク賢者** (Task Oracle)
- **場所**: `libs/claude_task_tracker.py`, `task_history.db`
- **役割**: プロジェクト進捗管理、最適な実行順序の導出
- **機能**: 計画立案、進捗追跡、優先順位判断

### 🚨 **インシデント賢者** (Crisis Sage)
- **場所**: `libs/incident_manager.py`, `knowledge_base/incident_management/`
- **役割**: 危機対応専門家、問題の即座感知・解決
- **機能**: エラー検知、自動復旧、インシデント履歴管理

### 🔍 **RAG賢者** (Search Mystic)
- **場所**: `libs/rag_manager.py`, `libs/enhanced_rag_manager.py`
- **役割**: 情報探索と理解、膨大な知識から最適解発見
- **機能**: コンテキスト検索、知識統合、回答生成

## ⚡ 4賢者の連携魔法
```
🧙‍♂️ 4賢者会議での問題解決 🧙‍♂️
ナレッジ: 「過去にこんな事例が記録されています...」
タスク: 「現在の優先順位と進捗状況は...」  
インシデント: 「緊急対応が必要です！」
RAG: 「最適解を発見しました」
→ 自動的に最良の解決策を実行
```

## 🎯 重要: TDD（テスト駆動開発）必須

**AI Companyのすべての開発はTDDで行います。コードを書く前に必ずテストを書いてください。**

### TDDサイクル
1. 🔴 **Red**: 失敗するテストを先に書く
2. 🟢 **Green**: 最小限の実装でテストを通す
3. 🔵 **Refactor**: コードを改善する

## 🚀 最新実装状況 (2025年7月)

### ✅ 完了済みフェーズ
1. **Phase 9: コードレビュー自動化システム** (21 tests) - `libs/automated_code_review.py`
2. **Phase 10: 非同期ワーカーパフォーマンス最適化** (21 tests) - `libs/async_worker_optimization.py`
3. **Phase 11: 統合テストフレームワーク構築** (19 tests) - `libs/integration_test_framework.py`
4. **Phase 12: 監視ダッシュボード高度化** (24 tests) - `libs/advanced_monitoring_dashboard.py`
5. **Phase 13: セキュリティ監査システム** (20 tests) - `libs/security_audit_system.py`
6. **Phase 14: Worker専用タスクトラッカー** (33 tests) - `libs/worker_status_monitor.py`, `libs/worker_task_flow.py`, `web/worker_dashboard.py`

**総計: 249テスト (Phase 1-4: 111 + Phase 14: 138)、100%成功率**

### 🚀 **ネクスト計画: AI学習・進化システム** ✅ 完了
**実装完了** - AI自己進化システムの実装
- **Claude CLI 統合**: `cc next-plan` コマンド群
- **ナレッジ賢者連携**: 自動学習データ保存・検索
- **4賢者協調進化**: 相互学習による自律改善システム

#### 実装済みフェーズ:
**Phase 2: パフォーマンス最適化基盤** (41 tests) ✅
- Performance Optimizer - 動的パフォーマンス最適化システム
- Hypothesis Generator - 仮説生成とA/Bテスト実験計画
- A/B Testing Framework - 統計的実験管理フレームワーク

**Phase 3: 自動適応・学習システム** (37 tests) ✅
- Auto Adaptation Engine - 自動パラメータ調整とロールバック
- Feedback Loop System - リアルタイムフィードバック処理
- Knowledge Evolution Mechanism - 知識進化とメタ知識生成

**Phase 4: Meta・クロス学習システム** (33 tests) ✅
- Meta Learning System - 学習方法の学習とループ防止
- Cross-Worker Learning System - Worker間知識共有
- Predictive Evolution System - 予測進化と先手最適化

## 📋 開発依頼の基本フォーマット

```bash
# TDD開発の明示的な依頼
ai-send "[機能名]をTDDで開発:
1. 要件: [具体的な要件]
2. テストケース:
   - 正常系: [期待動作]
   - 異常系: [エラーケース]
   - 境界値: [エッジケース]
3. まずtest_*.pyを作成
4. テスト失敗を確認
5. 実装してテストを通す
6. リファクタリング"

# 専用コマンド
ai-tdd new FeatureName "機能要件"
```

## 🛠️ 主要コマンド

### TDD開発
- `ai-tdd new <feature> <requirements>` - 新機能をTDDで開発
- `ai-tdd test <file>` - 既存コードにテスト追加
- `ai-tdd coverage <module>` - カバレッジ分析・改善
- `ai-tdd session <topic>` - 対話型TDD開発

### テスト実行
- `pytest tests/unit/` - ユニットテスト実行
- `pytest tests/unit/test_automated_code_review.py` - コードレビューシステムテスト
- `pytest tests/unit/test_async_worker_optimization.py` - パフォーマンス最適化テスト
- `pytest tests/unit/test_integration_test_framework.py` - 統合テストフレームワーク
- `pytest tests/unit/test_advanced_monitoring_dashboard.py` - 監視ダッシュボード
- `pytest tests/unit/test_security_audit_system.py` - セキュリティ監査システム
- `ai-test-coverage --html` - カバレッジレポート表示

### システム管理
- `ai-start` / `ai-stop` - システム起動/停止
- `ai-status` - システム状態確認
- `ai-logs` - ログ確認

## 📁 プロジェクト構造

```
/home/aicompany/ai_co/
├── workers/                    # ワーカー実装
├── libs/                      # 新規実装ライブラリ (2025年7月)
│   ├── automated_code_review.py          # コードレビュー自動化
│   ├── async_worker_optimization.py      # 非同期ワーカー最適化
│   ├── integration_test_framework.py     # 統合テストフレームワーク
│   ├── advanced_monitoring_dashboard.py  # 高度監視ダッシュボード
│   ├── security_audit_system.py          # セキュリティ監査システム
│   ├── performance_optimizer.py          # Phase 2: パフォーマンス最適化
│   ├── hypothesis_generator.py           # Phase 2: 仮説生成システム
│   ├── ab_testing_framework.py           # Phase 2: A/Bテストフレームワーク
│   ├── auto_adaptation_engine.py         # Phase 3: 自動適応エンジン
│   ├── feedback_loop_system.py           # Phase 3: フィードバックループ
│   ├── knowledge_evolution.py            # Phase 3: 知識進化メカニズム
│   ├── meta_learning_system.py           # Phase 4: メタ学習システム
│   ├── cross_worker_learning.py          # Phase 4: Worker間学習
│   └── predictive_evolution.py           # Phase 4: 予測進化システム
├── tests/                     # テスト（TDD必須）
│   ├── unit/                  # ユニットテスト
│   │   ├── test_automated_code_review.py
│   │   ├── test_async_worker_optimization.py
│   │   ├── test_integration_test_framework.py
│   │   ├── test_advanced_monitoring_dashboard.py
│   │   ├── test_security_audit_system.py
│   │   ├── test_performance_optimizer.py      # Phase 2
│   │   ├── test_hypothesis_generator.py       # Phase 2
│   │   ├── test_ab_testing_framework.py       # Phase 2
│   │   ├── test_auto_adaptation_engine.py     # Phase 3
│   │   ├── test_feedback_loop_system.py       # Phase 3
│   │   ├── test_knowledge_evolution.py        # Phase 3
│   │   ├── test_meta_learning_system.py       # Phase 4
│   │   ├── test_cross_worker_learning.py      # Phase 4
│   │   └── test_predictive_evolution.py       # Phase 4
│   └── TDD_TEST_RULES.md
├── templates/                 # TDDテンプレート
├── scripts/                   # ヘルパースクリプト
│   └── ai-tdd                # TDD専用コマンド
└── knowledge_base/           # ナレッジベース
    └── CLAUDE_TDD_GUIDE.md
```

## 📊 カバレッジ基準

| コンポーネント | 最小 | 目標 | 現状 |
|-------------|-----|-----|-----|
| 新規コード | 90% | 95% | 100% |
| Core | 90% | 100% | 95% |
| Workers | 80% | 95% | 90% |
| Libs | 95% | 100% | 100% |

## 🔧 実装済み主要機能

### コードレビュー自動化 (`libs/automated_code_review.py`)
- **CodeAnalyzer**: 静的解析、コードスメル検出、複雑度分析
- **SecurityScanner**: 脆弱性スキャン、依存関係チェック、機密データ検出
- **ReviewEngine**: 包括的レビュー、問題優先順位付け
- **AIReviewAssistant**: AI駆動の改善提案とリファクタリング
- **CodeReviewPipeline**: 自動修正とキャッシング

### 非同期ワーカー最適化 (`libs/async_worker_optimization.py`)
- **AsyncWorkerOptimizer**: バッチ処理、パイプライン、リソース管理
- **PerformanceProfiler**: 非同期プロファイリング、ボトルネック分析
- **AsyncBatchProcessor**: 自動バッチング、タイムアウト処理
- **ConnectionPoolOptimizer**: 動的プールサイジング、ヘルス監視
- **MemoryOptimizer**: データ構造最適化、リーク検出

### 統合テストフレームワーク (`libs/integration_test_framework.py`)
- **IntegrationTestRunner**: サービス統合、API、データベーステスト
- **ServiceOrchestrator**: サービス起動オーケストレーション、ヘルス監視
- **TestDataManager**: テストデータセットアップ、生成、検証
- **EnvironmentManager**: 環境分離、スナップショット、復元

### 監視ダッシュボード (`libs/advanced_monitoring_dashboard.py`)
- **MonitoringDashboard**: リアルタイムメトリクス、ウィジェット管理
- **MetricsCollector**: システム・アプリケーション・カスタムメトリクス
- **AlertingSystem**: ルールベースアラート、通知配信
- **VisualizationEngine**: チャート、ゲージ、ヒートマップ描画
- **RealTimeUpdates**: WebSocket配信、購読管理

### セキュリティ監査システム (`libs/security_audit_system.py`)
- **SecurityAuditor**: 脆弱性スキャン、権限監査、コンプライアンスチェック
- **ThreatDetector**: 異常検出、行動分析、侵入監視
- **ComplianceManager**: 標準評価、違反追跡、監査スケジューリング
- **SecurityReporter**: 包括的レポート、ダッシュボード、アラート

## 🔍 詳細ガイド

- [CLAUDE_TDD_GUIDE.md](knowledge_base/CLAUDE_TDD_GUIDE.md) - Claude CLI TDD完全ガイド
- [TDD_WORKFLOW.md](docs/TDD_WORKFLOW.md) - 一般的なTDDワークフロー
- [TDD_WITH_CLAUDE_CLI.md](docs/TDD_WITH_CLAUDE_CLI.md) - Claude CLI特有のTDD手法

## 🎯 実装成果

- **総テスト数**: 249テスト (全合格)
- **実装期間**: 2025年7月6日
- **開発手法**: 完全TDD (RED→GREEN→REFACTOR)
- **品質基準**: 100%テストカバレッジ達成
- **AI進化システム**: Phase 2-4 完全実装 (111テスト)

### 🧠 AI進化システム成果
- **Phase 2**: パフォーマンス最適化基盤 (41テスト)
- **Phase 3**: 自動適応・学習システム (37テスト)  
- **Phase 4**: Meta・クロス学習システム (33テスト)
- **4賢者統合**: 完全連携による自律学習実現

---
**Remember: No Code Without Test! 🧪**
**最新更新: 2025年7月6日 - AI進化システム実装完了**