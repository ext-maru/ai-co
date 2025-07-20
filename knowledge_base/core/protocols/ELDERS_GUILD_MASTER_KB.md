# Elders Guild Master Knowledge Base v6.2

## 🏢 システム概要

Elders Guildは、Claude APIを活用した自律的タスク処理システムです。RabbitMQベースのメッセージキューアーキテクチャを採用し、複数の専門ワーカーが協調して動作します。

### 🧠 **NEW**: AI Evolution System (ネクスト計画) 搭載
**実装完了**: 2025年7月6日 - 自律的学習・進化機能を実現
- **Phase 2-4**: 完全実装 (111テスト, 100%成功率)
- **4賢者統合**: Knowledge, RAG, Task, Incident Sages協調
- **自律学習**: システムが自ら学習し改善
- **予測進化**: 未来を予測した先手最適化

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
- **AI進化システム**: TDD実装, 4賢者統合

---

## 🧠 AI Evolution System (ネクスト計画)

### Phase 2: パフォーマンス最適化基盤 (41 tests)
- **Performance Optimizer** (`libs/performance_optimizer.py`) - 動的パフォーマンス最適化
- **Hypothesis Generator** (`libs/hypothesis_generator.py`) - データ駆動仮説生成
- **A/B Testing Framework** (`libs/ab_testing_framework.py`) - 統計的実験管理

### Phase 3: 自動適応・学習システム (37 tests)
- **Auto Adaptation Engine** (`libs/auto_adaptation_engine.py`) - 自動パラメータ調整
- **Feedback Loop System** (`libs/feedback_loop_system.py`) - リアルタイムフィードバック
- **Knowledge Evolution** (`libs/knowledge_evolution.py`) - 知識進化とメタ知識生成

### Phase 4: Meta・クロス学習システム (33 tests)
- **Meta Learning System** (`libs/meta_learning_system.py`) - 学習方法の学習
- **Cross-Worker Learning** (`libs/cross_worker_learning.py`) - Worker間知識共有
- **Predictive Evolution** (`libs/predictive_evolution.py`) - 予測進化と先手最適化

### 4賢者統合（エルダーズ）
- **Four Sages Integration** (`libs/four_sages_integration.py`) - 4賢者協調システム
- 📚 **ナレッジ賢者**: パターン蓄積・継承・学習履歴管理
- 🔍 **RAG賢者**: 類似ケース検索・コンテキスト最適化
- 📋 **タスク賢者**: 優先順位管理・実行計画最適化
- 🚨 **インシデント賢者**: エラー学習・予防措置強化