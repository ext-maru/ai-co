# タスク優先度管理機能 実装計画書

## 概要
現在のAI自動化システムに「タスクの優先度管理機能」を追加するための具体的な実装計画です。

## 現在のシステム分析

### 既存のタスク管理アーキテクチャ
- **キューシステム**: RabbitMQ ベースの非同期処理
- **データベース**: SQLite (`task_history.db`) でタスク履歴管理
- **ワーカー**: 動的スケーリング対応 (1-5ワーカー)
- **処理順序**: FIFO (First In, First Out)

### 現在のタスクデータ構造
```json
{
    "task_id": "general_20250701_212242",
    "type": "general|code",
    "prompt": "タスク内容",
    "created_at": "2025-07-01T21:22:42"
}
```

## 実装計画

### 1. データベーススキーマ変更

#### 1.1 task_history テーブル拡張
**ファイル**: `libs/task_history_db.py`

```sql
-- 既存テーブルに優先度カラム追加
ALTER TABLE task_history ADD COLUMN priority INTEGER DEFAULT 2;
ALTER TABLE task_history ADD COLUMN priority_label TEXT DEFAULT 'medium';
ALTER TABLE task_history ADD COLUMN deadline TIMESTAMP NULL;
ALTER TABLE task_history ADD COLUMN estimated_duration INTEGER NULL; -- 分単位

-- インデックス追加
CREATE INDEX IF NOT EXISTS idx_priority ON task_history(priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_deadline ON task_history(deadline ASC);
```

#### 1.2 実装変更箇所
**修正対象**: `libs/task_history_db.py:32-45`

```python
# 現在のテーブル作成SQL
CREATE TABLE IF NOT EXISTS task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    worker TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    summary TEXT,
    status TEXT DEFAULT 'completed',
    task_type TEXT DEFAULT 'general',
    priority INTEGER DEFAULT 2,           -- 新規追加
    priority_label TEXT DEFAULT 'medium', -- 新規追加
    deadline TIMESTAMP NULL,              -- 新規追加
    estimated_duration INTEGER NULL,      -- 新規追加
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 2. 優先度システム設計

#### 2.1 優先度レベル定義
```python
# 新規ファイル: libs/priority_manager.py
PRIORITY_LEVELS = {
    1: {'label': 'critical', 'color': '#FF4444', 'sla_hours': 1},
    2: {'label': 'high', 'color': '#FF8800', 'sla_hours': 4},
    3: {'label': 'medium', 'color': '#4488FF', 'sla_hours': 24},
    4: {'label': 'low', 'color': '#888888', 'sla_hours': 72},
    5: {'label': 'background', 'color': '#CCCCCC', 'sla_hours': 168}
}
```

#### 2.2 優先度管理クラス
**新規ファイル**: `libs/priority_manager.py`

```python
class PriorityManager:
    def calculate_priority_score(self, priority, created_at, deadline=None):
        """優先度スコア計算（低いほど高優先度）"""
        
    def get_next_task_by_priority(self):
        """優先度順でタスク取得"""
        
    def update_task_priority(self, task_id, new_priority):
        """タスク優先度更新"""
        
    def get_overdue_tasks(self):
        """期限切れタスク検出"""
```

### 3. メッセージキューシステム拡張

#### 3.1 優先度付きキュー実装
**修正対象**: `workers/task_worker.py:53-54`

```python
# 現在の単一キュー
self.channel.queue_declare(queue='task_queue', durable=True)

# 優先度別キューに変更
PRIORITY_QUEUES = [
    'task_queue_critical',   # priority 1
    'task_queue_high',       # priority 2  
    'task_queue_medium',     # priority 3
    'task_queue_low',        # priority 4
    'task_queue_background'  # priority 5
]

for queue in PRIORITY_QUEUES:
    self.channel.queue_declare(queue=queue, durable=True)
```

#### 3.2 タスク振り分けロジック
**新規ファイル**: `libs/task_dispatcher.py`

```python
class TaskDispatcher:
    def dispatch_task(self, task):
        """優先度に基づいてタスクを適切なキューに振り分け"""
        priority = task.get('priority', 3)
        queue_name = f'task_queue_{PRIORITY_LEVELS[priority]["label"]}'
        # キューに送信
```

### 4. ワーカー処理順序変更

#### 4.1 優先度順処理実装
**修正対象**: `workers/task_worker.py:61-67`

```python
def start_consuming(self):
    """優先度順でタスク処理"""
    # 現在のFIFO処理を優先度順に変更
    for queue in PRIORITY_QUEUES:
        self.channel.basic_consume(
            queue=queue,
            on_message_callback=self.process_task,
            auto_ack=False
        )
```

### 5. API拡張

#### 5.1 タスク送信API拡張
**修正対象**: `scripts/send_task.py:15-20`

```python
# 現在のタスク構造
task = {
    "task_id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "type": task_type,
    "prompt": prompt,
    "created_at": datetime.now().isoformat()
}

# 優先度対応版
task = {
    "task_id": f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "type": task_type,
    "prompt": prompt,
    "priority": kwargs.get('priority', 3),           # 新規追加
    "priority_label": kwargs.get('priority_label', 'medium'), # 新規追加
    "deadline": kwargs.get('deadline'),             # 新規追加
    "estimated_duration": kwargs.get('estimated_duration'), # 新規追加
    "created_at": datetime.now().isoformat()
}
```

#### 5.2 CLI拡張
**修正対象**: `scripts/pm_cli.py`

新機能追加:
- `priority <task_id> <level>` - タスク優先度変更
- `urgent <prompt>` - 緊急タスク作成 (priority=1)
- `schedule <prompt> <deadline>` - 期限付きタスク作成
- `queue status` - 優先度別キュー状況表示

### 6. 監視・通知機能拡張

#### 6.1 Slack通知拡張
**修正対象**: `libs/slack_notifier.py`

```python
def notify_high_priority_task(self, task):
    """高優先度タスク通知"""
    
def notify_overdue_task(self, task):
    """期限切れタスク警告"""
    
def notify_queue_status(self, queue_stats):
    """キュー状況レポート"""
```

#### 6.2 監視ダッシュボード
**新規ファイル**: `scripts/priority_monitor.py`

```python
class PriorityMonitor:
    def get_queue_statistics(self):
        """優先度別キュー統計"""
        
    def check_sla_violations(self):
        """SLA違反チェック"""
        
    def generate_priority_report(self):
        """優先度レポート生成"""
```

### 7. ワーカー動的調整

#### 7.1 優先度ベーススケーリング
**修正対象**: `libs/scaling_policy.py`

```python
def should_scale_up_priority_based(self, queue_stats):
    """優先度を考慮したスケールアップ判定"""
    # Critical/High優先度タスクが存在する場合は即座にスケールアップ
    
def calculate_worker_allocation(self, queue_stats):
    """優先度に基づくワーカー割り当て計算"""
    # 高優先度キューに多くのワーカーを割り当て
```

## 実装順序とファイル変更一覧

### Phase 1: データベース・基盤システム (1-2日)

1. **`libs/task_history_db.py`** - データベーススキーマ拡張
   - テーブル構造変更
   - 新しいインデックス追加
   - マイグレーション関数追加

2. **`libs/priority_manager.py`** - 新規作成
   - 優先度管理クラス実装
   - 優先度計算ロジック
   - SLA管理機能

3. **`libs/task_dispatcher.py`** - 新規作成
   - タスク振り分けロジック
   - キュー管理機能

### Phase 2: メッセージキューシステム (2-3日)

4. **`workers/task_worker.py`** - メジャー変更
   - 優先度付きキュー対応
   - 処理順序ロジック変更
   - 新しいメッセージ形式対応

5. **`workers/pm_worker.py`** - 部分変更
   - 優先度統計収集
   - スケーリング判定ロジック更新

6. **`libs/scaling_policy.py`** - 部分変更
   - 優先度ベーススケーリング実装

### Phase 3: API・UI拡張 (2-3日)

7. **`scripts/send_task.py`** - 部分変更
   - 優先度パラメータ追加
   - コマンドライン引数拡張

8. **`scripts/pm_cli.py`** - 機能追加
   - 優先度管理コマンド追加
   - キュー状況表示機能

9. **`libs/slack_notifier.py`** - 機能追加
   - 優先度別通知機能
   - SLA警告通知

### Phase 4: 監視・運用機能 (1-2日)

10. **`scripts/priority_monitor.py`** - 新規作成
    - 優先度監視ダッシュボード
    - SLA違反検出
    - レポート生成機能

## テスト計画

### 単体テスト
- `test_priority_manager.py` - 優先度計算ロジック
- `test_task_dispatcher.py` - タスク振り分け
- `test_priority_queue.py` - キュー処理順序

### 統合テスト
- 優先度別タスク処理フロー
- ワーカースケーリング動作
- SLA違反検出・通知

### 負荷テスト
- 高優先度タスク大量投入
- 混合優先度での処理性能
- ワーカー動的調整性能

## 運用・保守

### 設定管理
**新規ファイル**: `config/priority.conf`
```ini
[priority]
default_priority=3
sla_check_interval=300
max_priority_queues=5
worker_allocation_strategy=priority_weighted
```

### ログ・メトリクス
- 優先度別処理時間
- SLA達成率
- キュー待機時間統計

## 互換性保証

- 既存タスクは自動的にpriority=3（medium）で処理
- 既存API は引き続き動作（優先度パラメータは任意）
- 段階的移行により運用中断なし

## 期待される効果

1. **処理効率向上**: 重要タスクの優先処理
2. **SLA管理**: 期限内処理の保証
3. **リソース最適化**: 優先度に応じたワーカー配分
4. **運用可視化**: 優先度別の処理状況監視

## 推定工数

- **開発**: 8-10日（1名）
- **テスト**: 3-4日
- **デプロイ・調整**: 2-3日
- **合計**: 約2-3週間

この実装計画により、現在のシステムの安定性を保ちながら、効果的な優先度管理機能を追加できます。