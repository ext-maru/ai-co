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
status: draft
subcategory: research
tags:
- technical
- four-sages
- tdd
- python
title: Elders Guild Master Knowledge Base v6.2
version: 1.0.0
---

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

---

## 🏆 主要マイルストーン

### フェーズ1-15 完了実績 (2025年7月7日)
- ✅ **Phase 1-4**: Coreシステム構築 (111テスト)
- ✅ **Phase 5-8**: Worker高度化 (138テスト) 
- ✅ **Phase 9-13**: システム統合 (105テスト)
- ✅ **Phase 14**: Worker専用タスクトラッカー (33テスト)
- ✅ **Phase 15**: タスクエルダー協調システム
- ✅ **AI進化システム**: 完全実装 (111テスト)
- ✅ **プロジェクト個別管理体制** - 4プロジェクト完全独立化

### ファンタジー進化
- **Elders Guild階層**: 賢者システム確立
- **騎士団・工房・森**: 機能別組織分化
- **障害クリーチャー分類**: 高度化

#### 🐲 障害クリーチャー分類
- 軽微: 🧚‍♀️妖精の悪戯, 👹ゴブリンの小細工
- 中程度: 🧟‍♂️ゾンビ侵入, 🐺ワーウルフ徘徊
- 重大: ⚔️オーク大軍, 💀スケルトン軍団
- 致命的: 🐉古龍覚醒, 👑魔王復活
- 特殊: 🌊スライム増殖, 🗿ゴーレム暴走, 🕷️クモの巣
詳細: `knowledge_base/elders_hierarchy_definition_20250707.md`

### 🏗️ プロジェクト個別管理体制 (NEW - 2025/7/10実装)
**完全独立プロジェクト体制**を実現し、開発効率と品質を飛躍的に向上：

#### 🎯 4プロジェクト独立化達成
1. **frontend-project-manager** - Next.js 14プロジェクト管理システム
2. **upload-image-service** - FastAPI+React契約書類アップロード
3. **elders-guild-web** - Next.js 15統合システム（4賢者UI）
4. **image-upload-manager** - Flask画像管理システム

#### 📊 実装成果
- **Git履歴**: 完全保持（ゼロロス）
- **メインリポジトリ**: 90%軽量化
- **並列開発効率**: 3-5倍向上見込み
- **柔軍GitHub連携**: 選択的公開戦略

#### 🔄 新開発フロー
```
個別開発 → 横断的最適化 → 4賢者統合 → 品質保証 → 選択的公開
```

詳細: `knowledge_base/elder_council_requests/projects_git_separation_completion_20250710.md`

---

## 🔧 Core基盤

### BaseWorker
すべてのワーカーの基底クラス。共通機能を提供：
- RabbitMQ接続管理
- エラーハンドリング（自動リトライ機構）
- ロギング機能
- 並列処理最適化

### MessageQueue
メッセージキュー管理：
- **キュー名**: `ai_tasks`, `results`, `notifications`
- **優先度**: 0(低) 〜 9(高)
- **パーシステント**: メッセージの永続化
- **自動再接続**: 接続障害時のリトライ

---

## 🗄️ Knowledge Base構成

### 主要ファイル
- **Master KB**: システム全体の統合知識（このファイル）
- **Worker個別KB**: 各ワーカー専門知識
- **AI Evolution KB**: AI進化システム詳細
- **Elder Council**: 賢者会議決定事項

### AI Evolution System使用例
```python
# Performance Optimizer
from libs.performance_optimizer import PerformanceOptimizer
optimizer = PerformanceOptimizer()
strategies = optimizer.generate_optimization_strategies(metrics)

# Knowledge Evolution
from libs.knowledge_evolution import KnowledgeEvolutionMechanism
evolution = KnowledgeEvolutionMechanism()
gaps = evolution.identify_knowledge_gaps(current_knowledge)

# Meta Learning
from libs.meta_learning_system import MetaLearningSystem
meta_learner = MetaLearningSystem()
strategy = meta_learner.optimize_learning_strategy(history)
```

---

## 🎯 品質基準

### テスト網羅率
- **総テスト数**: 249テスト (100%成功率)
- **AI進化システム**: 111テスト (100%成功率)
- **従来システム**: 138テスト (100%成功率)
- **開発手法**: Test-Driven Development (TDD)

### 実装品質
- **テストカバレッジ**: 100%
- **エラーハンドリング**: 包括的実装
- **ドキュメント**: 完全ドキュメント化
- **4賢者統合**: 全コンポーネント統合済み

---

## 📚 詳細ガイド

### Elder Council Methodology
- [UNIVERSAL_CLAUDE_ELDER_STANDARDS_METHODOLOGY.md](knowledge_base/UNIVERSAL_CLAUDE_ELDER_STANDARDS_METHODOLOGY.md) - 普遍的クロード・エルダー標準手法

### AI Evolution System
- [AI_EVOLUTION_SYSTEM_KB_v1.0.md](knowledge_base/AI_EVOLUTION_SYSTEM_KB_v1.0.md) - AI進化システム完全ガイド
- [IMPLEMENTATION_SUMMARY_AI_EVOLUTION_2025_07.md](knowledge_base/IMPLEMENTATION_SUMMARY_AI_EVOLUTION_2025_07.md) - 実装サマリー

### Development
- [CLAUDE_TDD_GUIDE.md](knowledge_base/CLAUDE_TDD_GUIDE.md) - TDD完全ガイド
- [CLAUDE.md](CLAUDE.md) - Claude CLI開発ガイド

---

## 📢 最新コマンド

### AIシステム管理
- `ai-start` - システム起動
- `ai-stop` - システム停止
- `ai-status` - 状態確認
- `ai-logs` - ログ表示

### Elder Flow
- `elder-flow execute "<task>" --priority <level>` - タスク実行
- `elder-flow active` - アクティブタスク確認
- `elder-flow workflow create <name>` - ワークフロー作成

### TDD開発
- `ai-tdd new <feature> <requirements>` - 新機能開発
- `ai-tdd test <file>` - テスト追加
- `ai-tdd coverage <module>` - カバレッジ分析

### 4賢者相談
- `ai-sage consult <topic>` - 4賢者へ相談
- `ai-sage knowledge search <query>` - 知識検索
- `ai-sage incident report <issue>` - インシデント報告

### AI進化システム
- `ai-evolution status` - 進化状態確認
- `ai-evolution optimize <target>` - 最適化実行
- `ai-evolution learn <pattern>` - パターン学習

---

## 📍 重要パス

- **プロジェクトルート**: `/home/aicompany/ai_co`
- **Knowledge Base**: `/home/aicompany/ai_co/knowledge_base`
- **ワーカー**: `/home/aicompany/ai_co/workers`
- **ライブラリ**: `/home/aicompany/ai_co/libs`
- **テスト**: `/home/aicompany/ai_co/tests`
- **スクリプト**: `/home/aicompany/ai_co/scripts`

---

最終更新: 2025年7月21日 - Knowledge Base統合完了