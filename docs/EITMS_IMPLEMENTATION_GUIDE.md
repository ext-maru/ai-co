# EITMS (Elders Guild Integrated Task Management System) 実装ガイド

## 🏛️ 概要

EITMS は Todo・Issue・TaskTracker・Planning を統合するエルダーズギルド公式タスク管理システムです。

### 🎯 主要機能
- **統一データモデル**: 4つのタスク管理システムを1つのデータベースで統合
- **自動同期**: Issue→ProjectTask→Todoの自動カスケード連携
- **AI最適化**: 複雑度分析・工数見積もり・優先度最適化
- **GitHub統合**: Issues双方向同期・API連携
- **監視システム**: リアルタイム監視・自動修復・アラート

## 🔧 システム構成

### 📁 ファイル構造
```
ai_co/
├── libs/
│   ├── eitms_unified_data_model.py      # 統一データモデル
│   ├── eitms_auto_sync_foundation.py    # 自動連携基盤
│   ├── eitms_core_sync_engine.py        # コア同期エンジン
│   ├── eitms_api_sync_system.py         # API連携システム
│   ├── eitms_ai_optimization_engine.py  # AI最適化エンジン
│   ├── eitms_monitoring_system.py       # 監視システム
│   └── eitms_github_integration.py      # GitHub統合
├── scripts/
│   └── eitms                            # CLI管理ツール
├── config/
│   └── eitms_config.yaml               # システム設定
└── data/
    └── eitms.db                         # SQLite統合データベース
```

### 📊 データベーススキーマ
```sql
CREATE TABLE unified_tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT NOT NULL,  -- todo/project_task/issue/planning
    status TEXT NOT NULL,     -- created/in_progress/completed/blocked
    priority TEXT NOT NULL,   -- low/medium/high/critical
    created_at DATETIME,
    updated_at DATETIME,
    started_at DATETIME,
    completed_at DATETIME,
    time_estimated INTEGER,
    time_spent INTEGER,
    assigned_to TEXT,
    dependencies TEXT,        -- JSON array
    sub_tasks TEXT,           -- JSON array
    github_issue_number INTEGER,
    context TEXT              -- JSON object
);
```

## 🚀 インストール・セットアップ

### 1. 依存関係確認
```bash
# Python 3.8+
python3 --version

# SQLite
sqlite3 --version

# 必要パッケージ
pip install asyncio sqlite3 pyyaml requests
```

### 2. データベース初期化
```bash
# データベースディレクトリ作成
mkdir -p data

# EITMS初期化
python3 -c "
from libs.eitms_unified_data_model import EitmsUnifiedManager
import asyncio
async def init():
    manager = EitmsUnifiedManager()
    await manager.initialize_database()
    print('✅ EITMS データベース初期化完了')
asyncio.run(init())
"
```

### 3. 設定ファイル確認
```bash
# 設定ファイル確認
cat config/eitms_config.yaml
```

## 💻 使用方法

### CLI操作

#### 基本コマンド
```bash
# ヘルプ表示
./scripts/eitms help

# システム状態確認
./scripts/eitms status

# 統計情報表示
./scripts/eitms stats
```

#### タスク管理
```bash
# タスク作成
./scripts/eitms create "新機能実装" --type issue --priority high --description "OAuth2.0認証システム実装"

# タスク一覧表示
./scripts/eitms list                    # 全タスク
./scripts/eitms list --status open     # オープンタスクのみ

# タスク詳細表示
./scripts/eitms show task-123

# タスク検索
./scripts/eitms search "OAuth"
```

#### AI機能
```bash
# AI分析
./scripts/eitms analyze task-123

# AI推奨取得
./scripts/eitms recommend task-123

# AI最適化実行
./scripts/eitms optimize priorities
```

#### GitHub連携
```bash
# GitHub Issues同期
./scripts/eitms github sync

# 同期状態確認
./scripts/eitms github status
```

### Python API

#### 基本使用例
```python
import asyncio
from libs.eitms_unified_data_model import EitmsUnifiedManager, TaskType, Priority

async def main():
    # システム初期化
    manager = EitmsUnifiedManager()
    
    # タスク作成
    task_id = await manager.create_task(
        title="OAuth実装",
        task_type=TaskType.ISSUE,
        priority=Priority.HIGH,
        description="OAuth2.0認証システムの実装"
    )
    
    # タスク取得
    task = await manager.get_task(task_id)
    print(f"作成されたタスク: {task.title}")
    
    # タスク更新
    await manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
asyncio.run(main())
```

#### AI最適化
```python
from libs.eitms_ai_optimization_engine import EitmsAiEngine

async def ai_example():
    manager = EitmsUnifiedManager()
    ai_engine = EitmsAiEngine(manager)
    
    # タスク分析
    metrics = await ai_engine.analyze_task("task-123")
    print(f"複雑度: {metrics.complexity_score:.2f}")
    print(f"推定工数: {metrics.estimated_hours:.1f}時間")
    
    # AI推奨生成
    recommendations = await ai_engine.generate_recommendations("task-123")
    for rec in recommendations:
        print(f"推奨: {rec.recommendation_type} - {rec.reasoning}")

asyncio.run(ai_example())
```

## 🔧 設定

### config/eitms_config.yaml
```yaml
database:
  path: "data/eitms.db"
  connection_timeout: 30
  max_connections: 10

github:
  api_base_url: "https://api.github.com"
  repository: "ext-maru/ai-co"
  token_env_var: "GITHUB_TOKEN"
  sync_interval: 300

ai:
  optimization_enabled: true
  learning_enabled: true
  auto_recommendations: true
  complexity_threshold: 3.0

monitoring:
  enabled: true
  check_interval: 60
  alert_threshold: 0.1
  log_level: "INFO"

four_sages:
  knowledge_sage_path: "libs/claude_task_tracker.py"
  task_sage_path: "libs/claude_task_tracker.py"
  incident_sage_path: "libs/incident_manager.py"
  rag_sage_path: "libs/enhanced_rag_manager.py"
```

## 🧪 テスト

### 統合テスト実行
```bash
# 基本動作テスト
python3 -c "
import sqlite3, os
# データベーステスト
conn = sqlite3.connect('data/eitms.db')
print('✅ データベース接続成功')
conn.close()

# CLIテスト
import subprocess
result = subprocess.run(['./scripts/eitms', 'stats'], capture_output=True, text=True)
if result.returncode == 0:
    print('✅ CLI動作確認')
else:
    print('❌ CLI問題あり')
"
```

### 機能テスト
```bash
# タスク作成テスト
./scripts/eitms create "テストタスク" --type todo --priority medium

# 作成確認
./scripts/eitms list

# 統計確認
./scripts/eitms stats
```

## 🏛️ アーキテクチャ

### データフロー
```
入力 → 統一データモデル → AI分析 → 自動同期 → 監視
  ↓         ↓           ↓        ↓        ↓
Todo     SQLite      複雑度    GitHub    アラート
Issue    Database    工数      API       修復
Manual   Storage     優先度    同期      統計
```

### 4賢者統合
- **📚 ナレッジ賢者**: タスクパターン学習・ベストプラクティス
- **📋 タスク賢者**: 最適実行順序・依存関係管理
- **🚨 インシデント賢者**: リアルタイム監視・自動修復
- **🔍 RAG賢者**: 情報統合・最適化提案

### AI最適化エンジン
1. **複雑度分析**: キーワードベース・テキスト長・依存関係
2. **工数見積もり**: 過去データ学習・統計的調整
3. **優先度最適化**: コンテキスト分析・緊急度計算
4. **推奨システム**: 分解・スキルマッチング・最適化提案

## 📊 監視・運用

### ログ確認
```bash
# システムログ
./scripts/eitms logs system

# エラーログ
./scripts/eitms logs error

# 監視ログ
tail -f logs/eitms_monitoring.log
```

### パフォーマンス監視
```bash
# システム統計
./scripts/eitms stats

# データベースサイズ
du -h data/eitms.db

# プロセス状況
ps aux | grep eitms
```

## 🔄 同期・バックアップ

### GitHub同期
```bash
# 手動同期実行
./scripts/eitms github sync

# 同期状態確認
./scripts/eitms github status

# 同期ログ確認
./scripts/eitms logs github
```

### データバックアップ
```bash
# データベースバックアップ
cp data/eitms.db data/eitms_backup_$(date +%Y%m%d_%H%M%S).db

# 設定バックアップ
cp config/eitms_config.yaml config/eitms_config_backup.yaml
```

## 🚨 トラブルシューティング

### よくある問題

#### データベース接続エラー
```bash
# 権限確認
ls -la data/eitms.db

# データベース修復
sqlite3 data/eitms.db "PRAGMA integrity_check;"
```

#### CLI実行エラー
```bash
# 実行権限確認
chmod +x scripts/eitms

# パス確認
which sqlite3
```

#### GitHub同期エラー
```bash
# トークン確認
echo $GITHUB_TOKEN

# API接続テスト
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## 📈 拡張・カスタマイズ

### カスタムAI分析
```python
from libs.eitms_ai_optimization_engine import ComplexityAnalyzer

class CustomAnalyzer(ComplexityAnalyzer):
    def analyze_complexity(self, task):
        # カスタム複雑度分析
        custom_score = self.custom_analysis(task)
        return custom_score
```

### カスタム監視
```python
from libs.eitms_monitoring_system import EitmsMonitor

class CustomMonitor(EitmsMonitor):
    async def custom_health_check(self):
        # カスタム健全性チェック
        return await self.check_custom_metrics()
```

---

## 🏛️ エルダーズギルド認定

このシステムは**エルダーズギルド公式認定**を受けた統合タスク管理システムです。

- ✅ **TDD準拠**: 完全なテスト駆動開発
- ✅ **4賢者統合**: エルダーズギルド標準アーキテクチャ
- ✅ **Iron Will遵守**: 高品質コード基準
- ✅ **nWo対応**: New World Order戦略準拠

**バージョン**: 1.0.0  
**作成者**: クロードエルダー（Claude Elder）  
**承認**: エルダー評議会  
**更新日**: 2025年7月22日