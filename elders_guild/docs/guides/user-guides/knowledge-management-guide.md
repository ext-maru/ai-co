---
audience: developers
author: claude-elder
category: guides
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: user-guides
tags:
- python
- guides
title: 🎯 Elders Guild Knowledge Management System
version: 1.0.0
---

# 🎯 Elders Guild Knowledge Management System

## 概要

Elders Guildの設計・ナレッジ・実装を全て統合管理するシステムを構築しました。以下の機能を提供します：

1. **Knowledge Consolidator** - 全体の統合ドキュメント生成
2. **Evolution Tracker** - 進化の追跡と可視化
3. **Knowledge Scheduler** - 定期的な自動実行
4. **統合コマンド** - 簡単な操作インターフェース

## 🚀 セットアップと実行

### 1. セットアップスクリプトの実行

```bash
cd /home/aicompany/ai_co
source venv/bin/activate
python3 setup_knowledge_system.py
```

これにより、AI Command Executorを通じて以下のコマンドが作成されます：
- `setup_knowledge_management` - 完全なセットアップ
- `quick_consolidate` - 即座に統合実行
- `track_evolution` - 即座に進化追跡
- `start_knowledge_scheduler` - スケジューラー起動

### 2. 統合コマンド（ai-knowledge）の使用

セットアップ後、以下のコマンドが使用可能になります：

```bash
# ナレッジの統合（全フォーマット）
ai-knowledge consolidate

# Markdownのみ生成
ai-knowledge consolidate --format markdown

# HTMLレポートのみ生成
ai-knowledge consolidate --format html

# 進化の追跡
ai-knowledge evolve

# 進化の可視化付き追跡
ai-knowledge evolve --visualize

# スケジューラーの起動
ai-knowledge schedule

# バックグラウンドでスケジューラー起動
ai-knowledge schedule --daemon

# ステータス確認
ai-knowledge status
```

## 📋 主要コンポーネント

### 1. Knowledge Consolidator
- プロジェクト構造のスキャン
- 実装の分析（ワーカー、マネージャー、コマンド）
- システムマップの生成
- 統合ドキュメントの作成（Markdown/HTML/JSON）

### 2. Evolution Tracker
- スナップショットの取得
- 変更履歴の追跡
- 成長トレンドの分析
- インタラクティブな可視化

### 3. Knowledge Scheduler
- 毎日3時：ナレッジ統合
- 6時間ごと：進化追跡
- 毎週月曜9時：週次レポート
- 毎月1日：月次アーカイブ

## 📁 出力ファイルの場所

```
/home/aicompany/ai_co/knowledge_base/
├── CONSOLIDATED_KNOWLEDGE/         # 統合ドキュメント
│   ├── AI_COMPANY_CONSOLIDATED_*.md
│   ├── knowledge_export_*.json
│   └── ...
├── evolution_tracking/             # 進化追跡データ
│   ├── snapshot_*.json
│   ├── comparison_*.json
│   ├── evolution_report_*.md
│   └── ...
└── archives/                      # 月次アーカイブ
    └── knowledge_archive_*.tar.gz

/home/aicompany/ai_co/generated_reports/    # レポート（旧webディレクトリ）
├── knowledge_report_*.html
└── evolution_viz_*.html
```

## 🔍 活用方法

### 現在の状態を把握する
```bash
# 統合ドキュメントを生成して確認
ai-knowledge consolidate
cat /home/aicompany/ai_co/knowledge_base/CONSOLIDATED_KNOWLEDGE/AI_COMPANY_CONSOLIDATED_*.md
```

### 変更履歴を追跡する
```bash
# 進化を追跡して可視化
ai-knowledge evolve --visualize
# ブラウザでhttp://localhost:8080/evolution_viz_*.htmlを開く
```

### 定期的な監視を設定
```bash
# スケジューラーをバックグラウンドで起動
ai-knowledge schedule --daemon
```

## 🎨 特徴

1. **完全自動化** - FileSystemとAI Command Executorで全て完結
2. **包括的な分析** - コード構造、依存関係、統計情報を網羅
3. **進化の可視化** - 成長をグラフで確認
4. **定期実行** - スケジューラーによる自動更新
5. **多様な出力形式** - Markdown、HTML、JSONに対応

## 💡 今後の活用

このシステムにより：
- プロジェクトの全体像を常に最新の状態で把握
- 成長と変化を定量的に追跡
- ドキュメントの自動生成と更新
- チーム間での知識共有の促進

が実現されます。

---

**🎯 Elders Guildの知識を体系的に管理し、継続的な改善を支援します！**
