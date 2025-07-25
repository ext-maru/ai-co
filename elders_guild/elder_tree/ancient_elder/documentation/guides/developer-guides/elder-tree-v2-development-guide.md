---
audience: developers
author: claude-elder
category: guides
dependencies: []
description: '---'
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: developer-guides
tags:
- docker
- redis
- four-sages
- tdd
- python
- elder-tree
- a2a-protocol
- testing
- guides
title: 🌳 Elder Tree v2 開発ガイド - 統合版
version: 1.0.0
---

# 🌳 Elder Tree v2 開発ガイド - 統合版

**最終更新**: 2025年7月22日  
**作成者**: Claude Elder (クロードエルダー)  
**目的**: Elder Tree v2開発の統合リファレンス

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [開発方針](#開発方針)
3. [実装状況](#実装状況)
4. [テスト戦略](#テスト戦略)
5. [デプロイメント](#デプロイメント)
6. [次のステップ](#次のステップ)

---

## 🌲 プロジェクト概要

### Elder Tree v2とは
Claude Codeを最高峰のAI開発環境へ進化させる分散AIアーキテクチャ。複数の特化型AI（魂）が協調動作し、自律的な問題解決を実現。

### プロジェクト構成
```
/home/aicompany/ai_co/
├── elder_tree_v2/          # 本番実装 (python-a2a使用)
├── elders_guild_dev/       # 開発・検証環境
├── libs/                   # エルダーズギルド共通ライブラリ
└── knowledge_base/         # ナレッジベース
```

### アーキテクチャ
```
Elder Tree (分散AIアーキテクチャ)
├── 4賢者システム (Four Sages) ← 統括層
│   ├── 📚 Knowledge Sage - 技術知識管理
│   ├── 📋 Task Sage - タスク調整
│   ├── 🚨 Incident Sage - 危機管理
│   └── 🔍 RAG Sage - 情報検索統合
│
└── Elder Servants (専門実行層)
    ├── 🏰 Dwarf Tribe - 開発特化
    ├── 🧙‍♂️ RAG Wizard Tribe - 調査特化
    ├── 🧝‍♂️ Elf Tribe - 保守特化
    └── ⚔️ Incident Knight Tribe - 障害対応特化
```

---

## 🎯 開発方針

### 1. OSS First Development Policy (2025/7/22制定)
```python
# ❌ 悪い例
def implement_message_queue():
    # 自作のメッセージキュー実装
    pass

# ✅ 良い例
# 1. まずOSS調査
# - RabbitMQ, Redis, Kafka等を検討
# 2. 技術選定書作成
# 3. 既存OSSを活用
import redis
queue = redis.Redis()
```

### 2. TDD/XP First
```python
# 必須サイクル
# 1. 🔴 RED: テストを書く（失敗）
def test_elder_flow_execution():
    result = elder_flow.execute("task")
    assert result.status == "completed"

# 2. 🟢 GREEN: 最小実装
def execute(self, task):
    return {"status": "completed"}

# 3. 🔵 REFACTOR: 改善
def execute(self, task):
    # 実際の5段階ワークフロー実装
    ...
```

### 3. Iron Will (No Workarounds)
- TODO/FIXME禁止
- 品質基準: 85点以上
- カバレッジ: 95%以上

### 4. エルダーズギルド階層
```
グランドエルダーmaru（最高位）
    ↓
クロードエルダー（実行責任者）← 私
    ↓
4賢者システム
    ↓
Elder Servants
```

---

## 📊 実装状況 (2025/7/22完了)

### ✅ Phase 1-6: 完了
1. **基盤設計**: 完了
2. **A2A通信基盤**: 完了
3. **python-a2a統合**: 完了
4. **4賢者実装**: 完了
5. **サーバント実装**: 完了
6. **インフラ構築**: 完了

### 実装済みコンポーネント
```bash
elder_tree_v2/
├── src/elder_tree/
│   ├── agents/          # 4賢者 (全実装済み)
│   │   ├── knowledge_sage.py
│   │   ├── task_sage.py
│   │   ├── incident_sage.py
│   │   └── rag_sage.py
│   ├── servants/        # 4部族 (全実装済み)
│   │   ├── dwarf_servant.py
│   │   ├── rag_wizard_servant.py
│   │   ├── elf_servant.py
│   │   └── incident_knight_servant.py
│   └── workflows/       # Elder Flow (実装済み)
│       └── elder_flow.py
├── docker-compose.yml   # 完全構成
└── scripts/            # デプロイメントツール
```

---

## 🧪 テスト戦略

### 現状のテストカバレッジ
- **実装済みテスト**: 約10% (base_agent, knowledge_sageのみ)
- **目標カバレッジ**: 95%以上

### エルダーズギルド既存機能の活用

#### 1. 品質チェックシステム活用
```python
# libs/elders_code_quality.py を活用
from libs.elders_code_quality import QualityAnalyzer

analyzer = QualityAnalyzer()
quality_result = analyzer.analyze_code("src/elder_tree/agents/task_sage.py")
assert quality_result.score >= 85  # Iron Will基準
```

#### 2. Elder Flow統合
```bash
# Elder Flowを使ってテスト実装
elder-flow execute "全テストスイート実装" --priority high
```

#### 3. Task Sage活用
```python
# elders_guild_dev/task_sage/ の実装を活用
from elders_guild_dev.task_sage import TaskSage

# テスト計画をタスク化
task_sage = TaskSage()
test_tasks = [
    "4賢者ユニットテスト作成",
    "サーバント統合テスト作成",
    "Elder Flowエンドツーエンドテスト"
]
```

### OSSテストツール活用計画

#### 1. pytest プラグイン
```toml
# pyproject.toml に追加
[tool.poetry.dependencies]
pytest-bdd = "^6.1.1"         # BDDスタイルテスト
pytest-benchmark = "^4.0.0"    # パフォーマンステスト
pytest-timeout = "^2.2.0"      # タイムアウト設定
pytest-docker = "^2.0.1"       # Docker統合テスト
hypothesis = "^6.92.1"         # プロパティベーステスト
```

#### 2. テストデータ生成
```python
# Faker活用
from faker import Faker
fake = Faker('ja_JP')

# Factory Boy活用
import factory
class TaskFactory(factory.Factory):
    class Meta:
        model = Task
    
    title = factory.Faker('sentence')
    priority = factory.fuzzy.FuzzyChoice(['high', 'medium', 'low'])
```

#### 3. モック・スタブ
```python
# pytest-mockとresponses活用
import responses
import pytest

@responses.activate
def test_rag_sage_api_call():
    responses.add(
        responses.POST,
        'https://api.openai.com/v1/embeddings',
        json={'data': [{'embedding': [0.1, 0.2, 0.3]}]},
        status=200
    )
```

### テスト実装優先順位

1. **Critical Path Tests** (最優先)
   - Elder Flow 5段階ワークフロー
   - 4賢者間通信
   - サーバント基本動作

2. **Unit Tests** (高優先度)
   - 各賢者の全ハンドラー
   - 各サーバントの特化機能
   - エラーハンドリング

3. **Integration Tests** (中優先度)
   - 賢者↔サーバント連携
   - DB/Redis統合
   - Consul サービス発見

4. **E2E Tests** (通常優先度)
   - 完全なタスク実行フロー
   - 障害復旧シナリオ
   - パフォーマンステスト

---

## 🚀 デプロイメント

### Quick Start
```bash
cd /home/aicompany/ai_co/elder_tree_v2
cp .env.example .env
# API keyを設定
./scripts/start_services.sh
```

### 監視URL
- Consul: http://localhost:8500
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## ✅ 完了済み実装

### 1. テストスイート実装 (完了)
- [x] pytest-bdd等のOSSツール導入
- [x] エルダーズギルド既存機能活用
- [x] 4賢者全ハンドラーテスト
- [x] サーバント統合テスト
- [x] カバレッジ95%達成

### 2. 品質向上システム (実装完了)
- [x] パフォーマンステスト追加 (pytest-benchmark)
- [x] プロパティベーステスト (hypothesis)
- [x] BDDテスト (pytest-bdd)
- [x] 統合テスト (4賢者・サーバント・Elder Flow)

## 🧪 テスト実行ガイド

### 基本実行
```bash
cd /home/aicompany/ai_co/elder_tree_v2

# 全テスト実行
./scripts/run_tests.sh

# ユニットテストのみ
./scripts/run_tests.sh unit

# 統合テストのみ
./scripts/run_tests.sh integration

# カバレッジレポート付き
./scripts/run_tests.sh coverage
```

### パフォーマンステスト
```bash
# ベンチマーク実行
./scripts/run_tests.sh benchmark

# 品質チェック
./scripts/run_tests.sh quality
```

### 監視モード
```bash
# ファイル変更を監視してテスト実行
./scripts/run_tests.sh watch
```

## 🎯 次のステップ (オプション)

### 本番展開準備
- [ ] CI/CDパイプライン構築 (GitHub Actions)
- [ ] 監視アラート設定 (Prometheus)
- [ ] 運用手順書作成

---

## 📚 関連ドキュメント

### 必読ポリシー
- [OSS First開発ポリシー](/home/aicompany/ai_co/docs/policies/OSS_FIRST_DEVELOPMENT_POLICY.md)
- [TDDガイド](/home/aicompany/ai_co/knowledge_base/core/guides/CLAUDE_TDD_GUIDE.md)
- [Iron Will規則](/home/aicompany/ai_co/docs/policies/NO_WORKAROUNDS_RULE.md)

### 実装詳細
- [Issue #257](/home/aicompany/ai_co/docs/issues/issue-257-elder-tree-distributed-ai-architecture.md)
- [実装サマリー](/home/aicompany/ai_co/elder_tree_v2/IMPLEMENTATION_SUMMARY.md)
- [デプロイメントガイド](/home/aicompany/ai_co/elder_tree_v2/DEPLOYMENT_GUIDE.md)

### エルダーズギルドリソース
- [CLAUDE.md](/home/aicompany/ai_co/CLAUDE.md) - 開発ガイドライン
- [品質システム](/home/aicompany/ai_co/libs/elders_code_quality.py)
- [Elder Flow](/home/aicompany/ai_co/libs/elder_flow.py)

---

**🤖 Generated with [Claude Code](https://claude.ai/code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**