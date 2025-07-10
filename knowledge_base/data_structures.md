# Elders Guild Data Structures

## タスクデータ構造

### Task Object
```python
{
    "task_id": str,              # 一意のタスクID (例: "task_20250105_123456")
    "prompt": str,               # タスクの内容/プロンプト
    "task_type": str,            # タスクタイプ (code_generation, dialog, analysis等)
    "priority": int,             # 優先度 (1-10, デフォルト5)
    "tags": List[str],           # タグリスト
    "status": str,               # ステータス (pending, in_progress, completed, failed)
    "created_at": datetime,      # 作成日時
    "updated_at": datetime,      # 更新日時
    "assigned_to": str,          # 割り当てワーカーID
    "metadata": dict,            # 追加メタデータ
    "result": Optional[dict],    # 実行結果
    "error": Optional[str],      # エラーメッセージ
    "retry_count": int,          # リトライ回数
    "parent_task_id": Optional[str],  # 親タスクID（サブタスクの場合）
}
```

### TaskResult Object
```python
{
    "task_id": str,
    "status": str,               # completed, failed, timeout
    "worker_id": str,            # 実行ワーカーID
    "start_time": datetime,
    "end_time": datetime,
    "duration": float,           # 実行時間（秒）
    "response": str,             # 処理結果テキスト
    "files_created": List[str],  # 作成されたファイルのパス
    "files_modified": List[str], # 変更されたファイルのパス
    "output_file": str,          # 出力ファイルパス
    "rag_applied": bool,         # RAG適用有無
    "tokens_used": int,          # 使用トークン数
    "cost": float,               # 推定コスト
}
```

## ワーカーデータ構造

### WorkerInfo Object
```python
{
    "worker_id": str,            # ワーカーID (例: "worker-1")
    "worker_type": str,          # ワーカータイプ (task, dialog, error等)
    "process_id": int,           # プロセスID
    "status": str,               # running, idle, stopped, error
    "start_time": datetime,
    "last_heartbeat": datetime,
    "current_task": Optional[str],  # 現在処理中のタスクID
    "tasks_completed": int,      # 完了タスク数
    "tasks_failed": int,         # 失敗タスク数
    "memory_usage": float,       # メモリ使用量(MB)
    "cpu_usage": float,          # CPU使用率(%)
}
```

### WorkerMetrics Object
```python
{
    "timestamp": datetime,
    "active_workers": int,       # アクティブワーカー数
    "idle_workers": int,         # アイドルワーカー数
    "queue_length": int,         # キュー内タスク数
    "avg_processing_time": float,  # 平均処理時間
    "throughput": float,         # スループット（タスク/分）
    "error_rate": float,         # エラー率
    "cpu_usage": float,          # 全体CPU使用率
    "memory_usage": float,       # 全体メモリ使用量
}
```

## 会話データ構造

### Conversation Object
```python
{
    "conversation_id": str,      # 会話ID
    "created_at": datetime,
    "updated_at": datetime,
    "status": str,               # active, completed, archived
    "messages": List[Message],   # メッセージリスト
    "metadata": dict,            # メタデータ
    "total_tokens": int,         # 総トークン数
    "max_turns": int,            # 最大ターン数
    "current_turn": int,         # 現在のターン数
}
```

### Message Object
```python
{
    "message_id": str,
    "conversation_id": str,
    "role": str,                 # user, assistant, system
    "content": str,              # メッセージ内容
    "timestamp": datetime,
    "tokens": int,               # トークン数
    "attachments": List[str],    # 添付ファイルパス
}
```

## RAGデータ構造

### Knowledge Object
```python
{
    "knowledge_id": str,         # 知識ID
    "content": str,              # 知識内容
    "embedding": List[float],    # ベクトル埋め込み
    "metadata": {
        "source": str,           # ソース（ファイルパス等）
        "type": str,             # タイプ（code, doc, config等）
        "tags": List[str],       # タグ
        "created_at": datetime,
        "updated_at": datetime,
        "version": int,          # バージョン
    },
    "references": List[str],     # 参照する他の知識ID
}
```

### SearchResult Object
```python
{
    "query": str,                # 検索クエリ
    "results": List[{
        "knowledge_id": str,
        "content": str,
        "score": float,          # 類似度スコア
        "metadata": dict,
    }],
    "total_results": int,
    "search_time": float,        # 検索時間（秒）
}
```

## Git/バージョン管理データ構造

### GitCommit Object
```python
{
    "commit_hash": str,
    "branch": str,
    "author": str,
    "timestamp": datetime,
    "message": str,
    "files_changed": List[str],
    "additions": int,
    "deletions": int,
    "task_id": Optional[str],    # 関連タスクID
}
```

### GitFlowState Object
```python
{
    "current_branch": str,
    "branches": {
        "main": str,             # 最新コミットハッシュ
        "develop": str,
        "features": List[str],   # feature/*ブランチリスト
        "releases": List[str],   # release/*ブランチリスト
    },
    "has_changes": bool,
    "uncommitted_files": List[str],
    "staged_files": List[str],
}
```

## エラー/インシデントデータ構造

### ErrorIncident Object
```python
{
    "incident_id": str,
    "task_id": Optional[str],
    "worker_id": Optional[str],
    "timestamp": datetime,
    "error_type": str,           # 例外クラス名
    "error_message": str,
    "stack_trace": str,
    "context": {
        "file": str,
        "line": int,
        "function": str,
        "code_snippet": str,
    },
    "severity": str,             # critical, high, medium, low
    "resolution_status": str,    # open, investigating, resolved
    "resolution_notes": str,
    "auto_fix_attempted": bool,
    "auto_fix_successful": bool,
}
```

## ToDoリストデータ構造

### TodoList Object
```python
{
    "list_id": str,
    "name": str,
    "created_at": datetime,
    "updated_at": datetime,
    "items": List[TodoItem],
    "progress": {
        "total": int,
        "completed": int,
        "percentage": float,
    },
    "auto_run": bool,            # 自動実行フラグ
}
```

### TodoItem Object
```python
{
    "item_id": str,
    "list_id": str,
    "description": str,
    "command_type": str,         # bash, python, ai等
    "command": str,              # 実行コマンド
    "status": str,               # pending, completed, failed
    "created_at": datetime,
    "completed_at": Optional[datetime],
    "output": Optional[str],
    "error": Optional[str],
    "retry_count": int,
    "dependencies": List[str],   # 依存する他のitem_id
}
```

## 設定データ構造

### SystemConfig Object
```python
{
    "version": str,
    "workers": {
        "timeout": int,          # タイムアウト（秒）
        "retry_count": int,      # リトライ回数
        "retry_delay": int,      # リトライ間隔（秒）
        "max_workers": int,      # 最大ワーカー数
        "min_workers": int,      # 最小ワーカー数
    },
    "claude": {
        "model": str,            # モデル名
        "max_tokens": int,       # 最大トークン数
        "temperature": float,    # 温度パラメータ
    },
    "slack": {
        "enabled": bool,
        "rate_limit": int,       # メッセージ/秒
    },
    "rabbitmq": {
        "heartbeat": int,
        "blocked_connection_timeout": int,
    },
    "scaling": {
        "enabled": bool,
        "check_interval": int,   # チェック間隔（秒）
        "scale_up_threshold": float,   # スケールアップ閾値
        "scale_down_threshold": float, # スケールダウン閾値
    },
}
```

## データベーススキーマ

### tasks テーブル
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    assignee TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSON
);
```

### task_logs テーブル
```sql
CREATE TABLE task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    details TEXT,
    worker_id TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
```

## ファイルシステム構造

### ログファイル形式
```
/home/aicompany/ai_co/logs/
├── pm_worker.log           # PMワーカーログ
├── task_worker_1.log       # タスクワーカーログ
├── result_worker.log       # 結果ワーカーログ
├── error_intelligence.log  # エラー解析ログ
└── system.log             # システム全体ログ
```

### 出力ファイル形式
```
/home/aicompany/ai_co/output/
├── task_20250105_123456.txt    # タスク結果
├── conv_20250105_123456.json   # 会話履歴
└── report_20250105.html        # レポート
```

### ナレッジベースファイル形式
```
/home/aicompany/ai_co/knowledge_base/
├── *.md                    # Markdownドキュメント
├── *.json                  # JSONデータ
└── embeddings/            # ベクトル埋め込みデータ
    └── *.npy              # NumPy配列
```