---
audience: developers
author: claude-elder
category: projects
dependencies: []
description: No description available
difficulty: intermediate
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: draft
subcategory: active
tags:
- docker
- postgresql
- projects
title: 🗂️ ナレッジベース再編成計画
version: 1.0.0
---

# 🗂️ ナレッジベース再編成計画

## 📊 現状分析
- **総ファイル数**: 527ファイル
- **散乱ファイル**: ルートに約250個
- **重複率**: 約30%（推定150ファイル）

## 🏗️ 新ディレクトリ構造（提案）

```
knowledge_base/
├── 📚 core/                     # コア知識（統合済み、最新版のみ）
│   ├── identity/               # アイデンティティ・組織構造
│   ├── protocols/              # プロトコル・ルール
│   └── guides/                 # 開発ガイド・ベストプラクティス
│
├── 🏛️ elder_council/            # エルダー評議会関連
│   ├── decisions/              # 決定事項
│   ├── requests/               # リクエスト
│   ├── reports/                # レポート
│   └── archives/               # 過去の評議会記録
│
├── 🧙‍♂️ four_sages/              # 4賢者システム
│   ├── knowledge_sage/         # ナレッジ賢者
│   ├── task_sage/              # タスク賢者
│   ├── incident_sage/          # インシデント賢者
│   └── rag_sage/               # RAG賢者
│
├── 🔧 technical/                # 技術文書
│   ├── infrastructure/         # インフラ（Docker, PostgreSQL等）
│   ├── implementations/        # 実装詳細
│   ├── architecture/           # アーキテクチャ設計
│   └── integrations/           # 統合・連携
│
├── 📈 projects/                 # プロジェクト管理
│   ├── phases/                 # フェーズ管理
│   ├── progress/               # 進捗レポート
│   └── retrospectives/         # 振り返り
│
├── 🗃️ archives/                 # アーカイブ（古いバージョン、非アクティブ）
│   ├── versions/               # 過去バージョン
│   ├── deprecated/             # 非推奨・廃止
│   └── historical/             # 歴史的記録
│
└── 📊 data/                     # データファイル
    ├── databases/              # .dbファイル
    └── configs/                # 設定・JSON等

```

## 🎯 整理原則

### 1. **統合優先度**
- 最新版を特定し、古いバージョンはarchivesへ
- 重複内容は統合してから分類
- council_*ファイルは日付と内容で整理

### 2. **命名規則**
```
- 日付: YYYY-MM-DD形式
- 大文字: ディレクトリ名は小文字、ファイル名は用途に応じて
- 言語: 原則英語（日本語は必要最小限）
```

### 3. **分類基準**
- **使用頻度**: 高頻度参照はcore/へ
- **更新頻度**: 頻繁に更新されるものは適切なactive directoryへ
- **重要度**: クリティカルな情報はcore/protocols/へ

## 📋 実行ステップ

### Phase 1: 準備（優先度: High）
1. バックアップ作成
2. 新ディレクトリ構造作成
3. 移動スクリプト準備

### Phase 2: 統合（優先度: High）
1. council_*ファイルの分類と移動
2. MASTER_KB系の統合
3. 重複ファイルの特定と統合

### Phase 3: 技術文書整理（優先度: Medium）
1. PostgreSQL関連統合
2. Docker関連統合
3. 実装文書の分類

### Phase 4: 最終整理（優先度: Low）
1. ファイル名統一
2. README作成
3. インデックス生成

## ⚠️ リスクと対策
- **リスク**: 参照破壊
- **対策**: シンボリックリンクで移行期間対応

## 📅 推定作業時間
- Phase 1: 30分
- Phase 2: 2時間
- Phase 3: 1時間
- Phase 4: 30分
- **合計**: 約4時間

## 🔍 成功基準
1. ルートディレクトリのファイル数 < 10
2. 重複ファイル 0
3. 明確な分類構造
4. 検索性の向上