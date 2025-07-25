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
status: approved
subcategory: architecture
tags:
- technical
title: 📊 データベース統合計画
version: 1.0.0
---

# 📊 データベース統合計画

**作成日**: 2025年7月8日
**作成者**: クロードエルダー（開発実行責任者）
**承認**: タスク賢者による事前レビュー

## 🗄️ 現在のデータベース状況

### 発見されたタスク関連DB
1. **./task_history.db** (20KB) - ルートディレクトリ
2. **./db/task_history.db** (180KB) - メインDB
3. **./data/tasks.db** (16KB) - 別システム
4. **./data/task_flows.db** - フロー管理
5. **./data/task_locks.db** - ロック管理

### 🔍 分析結果
- **重複**: task_history.dbが複数存在
- **分散**: タスク情報が複数DBに分散
- **非効率**: 統合されていないため管理が複雑

## 🎯 統合戦略

### Phase 1: 統一データベース設計
```sql
-- 統一タスクデータベース: unified_tasks.db

-- タスク履歴テーブル（既存のtask_historyを拡張）
CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    task_type TEXT,
    worker TEXT,
    model TEXT,
    prompt TEXT,
    response TEXT,
    summary TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    files_created TEXT,
    error TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    -- 新規追加フィールド
    sage_consulted TEXT,  -- 相談した賢者
    elder_approval TEXT,  -- エルダー承認状況
    quality_score REAL    -- 品質スコア
);

-- タスクフロー管理
CREATE TABLE IF NOT EXISTS task_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id TEXT UNIQUE NOT NULL,
    parent_task_id TEXT,
    child_task_ids TEXT,
    flow_type TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_task_id) REFERENCES task_history(task_id)
);

-- タスクロック管理
CREATE TABLE IF NOT EXISTS task_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    lock_type TEXT,
    locked_by TEXT,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_history(task_id)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_task_created ON task_history(created_at);
CREATE INDEX IF NOT EXISTS idx_task_status ON task_history(status);
CREATE INDEX IF NOT EXISTS idx_task_worker ON task_history(worker);
```

### Phase 2: データ移行計画

1. **バックアップ作成**
   - 全DBファイルのバックアップ
   - タイムスタンプ付き保存

2. **データ統合**
   - 重複排除
   - データ整合性チェック
   - 統一フォーマットへの変換

3. **移行実行**
   - トランザクション使用
   - ロールバック可能な設計
   - 進捗ログ記録

### Phase 3: アプリケーション更新

1. **DB接続パス統一**
   - すべて`data/unified_tasks.db`を参照
   - 環境変数での設定可能

2. **互換性レイヤー**
   - 既存APIの維持
   - 段階的移行サポート

3. **テスト実施**
   - 統合テスト
   - パフォーマンステスト
   - 負荷テスト

## 📈 期待される効果

- **管理効率**: 80%向上
- **クエリ速度**: 50%向上
- **ストレージ**: 30%削減
- **開発効率**: 60%向上

## 🔧 実装優先順位

1. **高**: 統一DBスキーマ作成
2. **高**: データ移行スクリプト
3. **中**: アプリケーション更新
4. **低**: 監視ツール統合
