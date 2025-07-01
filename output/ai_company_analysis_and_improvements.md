# AI Companyシステム分析と改善提案

## システム全体構成分析

### 現在のアーキテクチャ
1. **コアワーカーシステム**: RabbitMQベースのメッセージキューシステム
   - `pm_worker.py`: プロジェクトマネージャーワーカー（動的スケーリング機能付き）
   - `task_worker.py`: タスク処理ワーカー（Claude CLI統合、RAG、自己進化機能）
   - `result_worker.py`: 結果処理ワーカー

2. **高度な機能システム**:
   - RAG（検索拡張生成）: GitHubリポジトリ統合
   - 自己進化システム: コード自動配置機能
   - Slack通知システム
   - 動的スケーリング（1-5ワーカー）

3. **データ管理**:
   - SQLiteデータベース（conversations.db, task_history.db）
   - ファイルベースのタスク管理（pending/completed/failed）

## 特定されたボトルネック

### 1. RabbitMQ接続の不安定性 
- ログから「RabbitMQ接続なし」エラーが頻発
- ワーカーの健康状態チェックで接続失敗が多発

### 2. タスク処理の単一点障害
- Claude CLI依存による処理ボトルネック
- タイムアウト設定（5分）による処理遅延

### 3. スケーリングの非効率性
- 固定的なスケーリング閾値（キュー長5で拡張）
- CPU/メモリリソース使用率の考慮不足

### 4. データベース同期問題
- 複数のデータベースファイルによる整合性リスク
- 履歴データの重複保存

### 5. エラーハンドリングの不完全さ
- 自己進化処理の失敗時の回復メカニズム不足
- ログファイルの肥大化

---

## 改善提案

### 1. 【RabbitMQ接続強化とコネクションプール実装】

#### 問題: RabbitMQ接続の不安定性
現在のシステムでは単一接続でRabbitMQにアクセスしており、接続が切れると処理が停止する。

#### 解決策: コネクションプール + 自動再接続機能

```python
# libs/rabbitmq_pool.py (新規作成)
import pika
import time
import logging
from threading import Lock
from queue import Queue, Empty

class RabbitMQConnectionPool:
    def __init__(self, host='localhost', max_connections=10):
        self.host = host
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.lock = Lock()
        self.logger = logging.getLogger('RabbitMQPool')
        
        # 初期接続プールを作成
        self._initialize_pool()
    
    def _initialize_pool(self):
        for _ in range(self.max_connections):
            try:
                connection = self._create_connection()
                if connection:
                    self.pool.put(connection)
            except Exception as e:
                self.logger.error(f"接続プール初期化エラー: {e}")
    
    def _create_connection(self):
        try:
            return pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    connection_attempts=3,
                    retry_delay=2
                )
            )
        except Exception as e:
            self.logger.error(f"RabbitMQ接続失敗: {e}")
            return None
    
    def get_connection(self):
        try:
            connection = self.pool.get(timeout=5)
            if connection.is_closed:
                connection = self._create_connection()
            return connection
        except Empty:
            return self._create_connection()
    
    def return_connection(self, connection):
        if connection and not connection.is_closed:
            try:
                self.pool.put(connection, timeout=1)
            except:
                connection.close()

# 既存ワーカーの修正（task_worker.py）
class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        self.model = "claude-sonnet-4-20250514"
        self.connection_pool = RabbitMQConnectionPool()
        
    def connect(self):
        self.connection = self.connection_pool.get_connection()
        if self.connection:
            self.channel = self.connection.channel()
            return True
        return False
```

#### 実装方法:
1. `libs/rabbitmq_pool.py`を作成
2. 全ワーカーファイルで`RabbitMQConnectionPool`を使用
3. 接続エラー時の自動再試行機能を追加
4. ヘルスチェック機能にプール状態監視を組み込み

---

### 2. 【非同期タスク処理とClaude API直接統合】

#### 問題: Claude CLI依存による処理ボトルネック
現在はClaude CLIのsubprocessを同期実行しているため、処理が遅く、障害耐性が低い。

#### 解決策: Claude API直接統合 + 非同期処理

```python
# libs/claude_api_client.py (新規作成)
import asyncio
import aiohttp
import os
from typing import Dict, Any

class ClaudeAPIClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_response(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "content": data["content"][0]["text"],
                        "usage": data.get("usage", {})
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error {response.status}: {error_text}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

# workers/async_task_worker.py (新規作成)
import asyncio
import aio_pika
from libs.claude_api_client import ClaudeAPIClient

class AsyncTaskWorker:
    def __init__(self, worker_id="async-worker-1"):
        self.worker_id = worker_id
        self.claude_client = ClaudeAPIClient()
        
    async def process_task_async(self, message: aio_pika.IncomingMessage):
        async with message.process():
            task_data = json.loads(message.body)
            
            # 複数タスクの並列処理
            tasks = []
            if isinstance(task_data, list):
                for task in task_data:
                    tasks.append(self._process_single_task(task))
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                result = await self._process_single_task(task_data)
                
    async def _process_single_task(self, task: dict):
        async with ClaudeAPIClient() as claude:
            result = await claude.generate_response(
                prompt=task.get('prompt', ''),
                model=self.model
            )
            return result
```

#### 実装方法:
1. Claude API直接統合用のクライアントライブラリ作成
2. 非同期処理対応のワーカー実装
3. 既存の同期ワーカーと並行運用
4. API使用量の監視とレート制限対応

---

### 3. 【インテリジェント・スケーリングシステム】

#### 問題: 固定的なスケーリング閾値による非効率性
現在のスケーリングはキュー長のみで判断しており、システムリソースや処理複雑度を考慮していない。

#### 解決策: ML駆動の動的スケーリング

```python
# libs/intelligent_scaling.py (新規作成)
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import deque
import psutil
import time

class IntelligentScaler:
    def __init__(self, history_size=100):
        self.history = deque(maxlen=history_size)
        self.model = LinearRegression()
        self.is_trained = False
        self.last_scaling_time = 0
        self.min_scaling_interval = 30  # 30秒
        
    def collect_metrics(self):
        """システムメトリクスを収集"""
        return {
            'timestamp': time.time(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'queue_length': self._get_queue_length(),
            'active_workers': self._get_active_workers(),
            'avg_task_duration': self._get_avg_task_duration(),
            'task_complexity_score': self._calculate_task_complexity()
        }
    
    def _calculate_task_complexity(self):
        """直近のタスクの複雑度スコアを計算"""
        # プロンプト長、コードブロック数、実行時間から複雑度を推定
        recent_tasks = self._get_recent_tasks(limit=10)
        if not recent_tasks:
            return 1.0
            
        complexity_scores = []
        for task in recent_tasks:
            score = 1.0
            # プロンプト長
            if len(task.get('prompt', '')) > 500:
                score += 0.5
            # コード生成タスク
            if 'code' in task.get('type', '').lower():
                score += 1.0
            # 実行時間
            if task.get('duration', 0) > 60:
                score += 1.0
            complexity_scores.append(score)
            
        return np.mean(complexity_scores)
    
    def should_scale_up(self, metrics):
        """スケールアップ判定"""
        if time.time() - self.last_scaling_time < self.min_scaling_interval:
            return False
            
        # 複数条件での判定
        conditions = [
            metrics['queue_length'] > 3,  # 基本的なキュー長
            metrics['cpu_percent'] > 70,  # CPU使用率
            metrics['memory_percent'] > 70,  # メモリ使用率
            metrics['task_complexity_score'] > 2.0  # タスク複雑度
        ]
        
        # 予測モデルが利用可能な場合
        if self.is_trained:
            predicted_load = self._predict_load(metrics)
            conditions.append(predicted_load > 0.8)
        
        # 条件の60%以上が満たされた場合スケールアップ
        return sum(conditions) >= len(conditions) * 0.6
    
    def _predict_load(self, current_metrics):
        """負荷予測"""
        features = np.array([[
            current_metrics['queue_length'],
            current_metrics['cpu_percent'],
            current_metrics['memory_percent'],
            current_metrics['task_complexity_score']
        ]])
        return self.model.predict(features)[0]
    
    def train_model(self):
        """履歴データから予測モデルを訓練"""
        if len(self.history) < 20:
            return
            
        X = []
        y = []
        for i in range(len(self.history) - 1):
            current = self.history[i]
            next_metrics = self.history[i + 1]
            
            X.append([
                current['queue_length'],
                current['cpu_percent'],
                current['memory_percent'],
                current['task_complexity_score']
            ])
            
            # 次の時点での負荷状態を予測対象とする
            load_score = (next_metrics['cpu_percent'] + next_metrics['memory_percent']) / 200
            y.append(load_score)
        
        if len(X) >= 10:
            self.model.fit(X, y)
            self.is_trained = True

# pm_worker.pyの修正
class PMWorker:
    def __init__(self):
        # 既存の初期化コード...
        self.intelligent_scaler = IntelligentScaler()
        
    def dynamic_scaling_check(self):
        """インテリジェントスケーリングチェック"""
        metrics = self.intelligent_scaler.collect_metrics()
        self.intelligent_scaler.history.append(metrics)
        
        # 定期的にモデルを再訓練
        if len(self.intelligent_scaler.history) % 50 == 0:
            self.intelligent_scaler.train_model()
        
        if self.intelligent_scaler.should_scale_up(metrics):
            self.scale_workers('up', metrics)
        elif self.intelligent_scaler.should_scale_down(metrics):
            self.scale_workers('down', metrics)
```

#### 実装方法:
1. `libs/intelligent_scaling.py`を新規作成
2. scikit-learnを`requirements.txt`に追加
3. PMワーカーにインテリジェントスケーラーを統合
4. メトリクス収集とモデル訓練の自動化

---

### 4. 【統合データベースとイベントソーシング】

#### 問題: 複数データベースによる整合性リスクとデータ重複
現在の`conversations.db`と`task_history.db`は別々に管理されており、データの整合性が保証されていない。

#### 解決策: 統合データベース + イベントソーシングパターン

```python
# libs/unified_database.py (新規作成)
import sqlite3
from datetime import datetime
import json
from typing import Dict, List, Any
import threading
from contextlib import contextmanager

class UnifiedDatabase:
    def __init__(self, db_path="/root/ai_co/db/unified.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """統合データベースの初期化"""
        with self.get_connection() as conn:
            conn.executescript("""
                -- イベントストア（全ての変更を記録）
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aggregate_id TEXT NOT NULL,
                    aggregate_type TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER NOT NULL,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, aggregate_type);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                
                -- タスク集約ビュー（最新状態）
                CREATE VIEW IF NOT EXISTS task_current_state AS
                WITH latest_events AS (
                    SELECT aggregate_id, MAX(version) as max_version
                    FROM events 
                    WHERE aggregate_type = 'task'
                    GROUP BY aggregate_id
                )
                SELECT 
                    e.aggregate_id as task_id,
                    json_extract(e.event_data, '$.status') as status,
                    json_extract(e.event_data, '$.worker_id') as worker_id,
                    json_extract(e.event_data, '$.prompt') as prompt,
                    json_extract(e.event_data, '$.response') as response,
                    e.timestamp
                FROM events e
                JOIN latest_events le ON e.aggregate_id = le.aggregate_id 
                                    AND e.version = le.max_version
                WHERE e.aggregate_type = 'task';
                
                -- 会話集約ビュー
                CREATE VIEW IF NOT EXISTS conversation_current_state AS
                WITH latest_events AS (
                    SELECT aggregate_id, MAX(version) as max_version
                    FROM events 
                    WHERE aggregate_type = 'conversation'
                    GROUP BY aggregate_id
                )
                SELECT 
                    e.aggregate_id as conversation_id,
                    json_extract(e.event_data, '$.status') as status,
                    json_extract(e.event_data, '$.summary') as summary,
                    json_extract(e.event_data, '$.participant_count') as participant_count,
                    e.timestamp
                FROM events e
                JOIN latest_events le ON e.aggregate_id = le.aggregate_id 
                                    AND e.version = le.max_version
                WHERE e.aggregate_type = 'conversation';
                
                -- パフォーマンス統計テーブル
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_performance_type_time ON performance_metrics(metric_type, timestamp);
            """)
    
    @contextmanager
    def get_connection(self):
        """スレッドセーフなDB接続"""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def save_event(self, aggregate_id: str, aggregate_type: str, 
                   event_type: str, event_data: Dict[str, Any], 
                   metadata: Dict[str, Any] = None):
        """イベントを保存"""
        with self.get_connection() as conn:
            # 現在のバージョンを取得
            cursor = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 as next_version "
                "FROM events WHERE aggregate_id = ? AND aggregate_type = ?",
                (aggregate_id, aggregate_type)
            )
            version = cursor.fetchone()['next_version']
            
            # イベントを保存
            conn.execute("""
                INSERT INTO events (aggregate_id, aggregate_type, event_type, 
                                  event_data, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                aggregate_id, aggregate_type, event_type,
                json.dumps(event_data), version,
                json.dumps(metadata) if metadata else None
            ))
            
            return version
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """タスクの完全な履歴を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT event_type, event_data, timestamp, version
                FROM events 
                WHERE aggregate_id = ? AND aggregate_type = 'task'
                ORDER BY version
            """, (task_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    AVG(CASE WHEN json_extract(event_data, '$.status') = 'completed' 
                        THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(CAST(json_extract(event_data, '$.duration') AS REAL)) as avg_duration
                FROM events 
                WHERE aggregate_type = 'task' 
                AND event_type = 'task_completed'
                AND timestamp > datetime('now', '-' || ? || ' hours')
            """, (hours,))
            
            return dict(cursor.fetchone())

# 既存システムとの統合
class TaskWorkerWithEvents(TaskWorker):
    def __init__(self, worker_id="worker-1"):
        super().__init__(worker_id)
        self.db = UnifiedDatabase()
    
    def process_task_with_events(self, ch, method, properties, body):
        """イベントソーシング対応のタスク処理"""
        task = json.loads(body)
        task_id = task.get('task_id')
        
        # タスク開始イベント
        self.db.save_event(
            aggregate_id=task_id,
            aggregate_type='task',
            event_type='task_started',
            event_data={
                'worker_id': self.worker_id,
                'prompt': task.get('prompt'),
                'task_type': task.get('type'),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        try:
            # タスク処理（既存ロジック）
            result = self._process_task_logic(task)
            
            # タスク完了イベント
            self.db.save_event(
                aggregate_id=task_id,
                aggregate_type='task',
                event_type='task_completed',
                event_data={
                    'status': 'completed',
                    'response': result['output'],
                    'duration': result['duration'],
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # タスク失敗イベント
            self.db.save_event(
                aggregate_id=task_id,
                aggregate_type='task',
                event_type='task_failed',
                event_data={
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            )
            raise
```

#### 実装方法:
1. `libs/unified_database.py`を新規作成
2. 既存のデータを新しいイベントストアに移行
3. 全ワーカーでイベントソーシングパターンを採用
4. 既存のデータベースファイルのバックアップと段階的移行

---

### 5. 【障害回復とサーキットブレーカーパターン】

#### 問題: エラーハンドリングの不完全さと自己回復能力の不足
現在のシステムではエラー時の回復メカニズムが不十分で、障害が連鎖的に影響を与える可能性がある。

#### 解決策: サーキットブレーカー + 自動回復システム

```python
# libs/circuit_breaker.py (新規作成)
import time
import logging
from enum import Enum
from collections import deque
from typing import Callable, Any, Optional
import threading

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # 正常状態
    OPEN = "open"          # 障害状態（処理をブロック）
    HALF_OPEN = "half_open"  # 回復試行状態

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception,
                 name: str = "CircuitBreaker"):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger(f'CircuitBreaker.{name}')
        
        # 統計情報
        self.success_count = 0
        self.total_calls = 0
        self.failure_history = deque(maxlen=100)
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self.lock:
            self.total_calls += 1
            
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.logger.info(f"{self.name}: HALF_OPEN状態に移行")
                else:
                    self.logger.warning(f"{self.name}: OPEN状態のため処理をスキップ")
                    raise Exception(f"Circuit breaker is OPEN for {self.name}")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.logger.info(f"{self.name}: CLOSED状態に回復")
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.failure_history.append(time.time())
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.error(f"{self.name}: OPEN状態に移行（連続失敗: {self.failure_count}）")
    
    def get_stats(self) -> dict:
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_calls': self.total_calls,
            'success_rate': self.success_count / max(self.total_calls, 1),
            'recent_failures': len([f for f in self.failure_history 
                                  if time.time() - f < 300])  # 5分以内の失敗
        }

# libs/recovery_system.py (新規作成)
import time
import subprocess
import psutil
from typing import List, Dict, Any
import logging

class AutoRecoverySystem:
    def __init__(self):
        self.logger = logging.getLogger('AutoRecovery')
        self.recovery_strategies = {
            'rabbitmq_down': self._recover_rabbitmq,
            'worker_crashed': self._recover_worker,
            'disk_full': self._cleanup_disk,
            'memory_high': self._reduce_memory_usage,
            'database_locked': self._recover_database
        }
        
        # 回復の試行履歴
        self.recovery_history = deque(maxlen=100)
        
    def detect_and_recover(self) -> List[str]:
        """問題を検出して自動回復を試行"""
        issues_detected = []
        issues_recovered = []
        
        # 各種問題の検出
        if not self._check_rabbitmq_health():
            issues_detected.append('rabbitmq_down')
            
        if not self._check_workers_health():
            issues_detected.append('worker_crashed')
            
        if self._check_disk_usage() > 90:
            issues_detected.append('disk_full')
            
        if self._check_memory_usage() > 85:
            issues_detected.append('memory_high')
            
        if not self._check_database_health():
            issues_detected.append('database_locked')
        
        # 回復処理の実行
        for issue in issues_detected:
            if issue in self.recovery_strategies:
                try:
                    if self.recovery_strategies[issue]():
                        issues_recovered.append(issue)
                        self.logger.info(f"回復成功: {issue}")
                    else:
                        self.logger.error(f"回復失敗: {issue}")
                except Exception as e:
                    self.logger.error(f"回復処理例外 {issue}: {e}")
        
        return issues_recovered
    
    def _recover_rabbitmq(self) -> bool:
        """RabbitMQの回復"""
        try:
            # RabbitMQサービスの再起動
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'rabbitmq-server'], 
                                  capture_output=True, timeout=30)
            if result.returncode == 0:
                time.sleep(5)  # 起動待ち
                return self._check_rabbitmq_health()
            return False
        except Exception as e:
            self.logger.error(f"RabbitMQ回復失敗: {e}")
            return False
    
    def _recover_worker(self) -> bool:
        """ワーカープロセスの回復"""
        try:
            # 停止中のワーカーを再起動
            subprocess.run(['tmux', 'new-session', '-d', '-s', 'recovery-worker', 
                          'python3', '/root/ai_co/workers/task_worker.py'], 
                         timeout=10)
            return True
        except Exception as e:
            self.logger.error(f"ワーカー回復失敗: {e}")
            return False
    
    def _cleanup_disk(self) -> bool:
        """ディスク容量の回復"""
        try:
            # 古いログファイルの削除
            subprocess.run(['find', '/root/ai_co/logs', '-name', '*.log', 
                          '-mtime', '+7', '-delete'], timeout=30)
            
            # 古い出力ファイルの削除
            subprocess.run(['find', '/root/ai_co/output', '-name', 'result.txt', 
                          '-mtime', '+30', '-delete'], timeout=30)
            
            return True
        except Exception as e:
            self.logger.error(f"ディスククリーンアップ失敗: {e}")
            return False

# 統合された障害検知・回復システム
class ResilientTaskWorker(TaskWorker):
    def __init__(self, worker_id="resilient-worker-1"):
        super().__init__(worker_id)
        
        # サーキットブレーカーを各種処理に適用
        self.claude_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120,
            name=f"Claude-{worker_id}"
        )
        
        self.rabbitmq_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            name=f"RabbitMQ-{worker_id}"
        )
        
        self.recovery_system = AutoRecoverySystem()
        
        # 定期的な健康チェック
        self.health_check_interval = 60
        self.last_health_check = 0
    
    @property
    def claude_api_call_with_breaker(self):
        return self.claude_breaker(self._claude_api_call)
    
    @property  
    def rabbitmq_publish_with_breaker(self):
        return self.rabbitmq_breaker(self._rabbitmq_publish)
    
    def process_task_resilient(self, ch, method, properties, body):
        """障害耐性を持つタスク処理"""
        try:
            # 定期的な健康チェック
            if time.time() - self.last_health_check > self.health_check_interval:
                self._perform_health_check()
                self.last_health_check = time.time()
            
            # 通常のタスク処理（サーキットブレーカー適用）
            task = json.loads(body)
            
            # Claude API呼び出し（サーキットブレーカー適用）
            response = self.claude_api_call_with_breaker(task.get('prompt'))
            
            # 結果の送信（サーキットブレーカー適用）
            self.rabbitmq_publish_with_breaker('result_queue', response)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"タスク処理エラー: {e}")
            # 自動回復を試行
            recovered_issues = self.recovery_system.detect_and_recover()
            if recovered_issues:
                self.logger.info(f"自動回復完了: {recovered_issues}")
                # 回復後に再試行
                try:
                    self.process_task_resilient(ch, method, properties, body)
                    return
                except:
                    pass
            
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _perform_health_check(self):
        """健康チェックと予防的措置"""
        # サーキットブレーカーの状態をログ出力
        claude_stats = self.claude_breaker.get_stats()
        rabbitmq_stats = self.rabbitmq_breaker.get_stats()
        
        self.logger.info(f"Claude Circuit Breaker: {claude_stats}")
        self.logger.info(f"RabbitMQ Circuit Breaker: {rabbitmq_stats}")
        
        # 問題の早期検出
        if claude_stats['success_rate'] < 0.5:
            self.logger.warning("Claude API成功率低下 - 予防的措置を実行")
            
        if rabbitmq_stats['recent_failures'] > 3:
            self.logger.warning("RabbitMQ接続問題 - 予防的措置を実行")
```

#### 実装方法:
1. `libs/circuit_breaker.py`と`libs/recovery_system.py`を新規作成
2. 既存のワーカーにサーキットブレーカーパターンを適用
3. 定期的な健康チェック機能を全コンポーネントに統合
4. 自動回復のログ記録とアラート機能を追加

---

## 実装優先順位

1. **最高優先度**: RabbitMQ接続強化（提案1）- システムの安定性に直結
2. **高優先度**: 障害回復システム（提案5）- 運用の自動化
3. **中優先度**: インテリジェントスケーリング（提案3）- パフォーマンス向上
4. **中優先度**: 統合データベース（提案4）- データ整合性
5. **低優先度**: 非同期処理（提案2）- 高度な最適化

## 期待される効果

- **可用性**: 99.9%以上のシステム稼働率
- **スケーラビリティ**: 負荷に応じた自動スケーリング
- **パフォーマンス**: タスク処理時間の30%短縮
- **運用性**: 手動介入の70%削減
- **データ整合性**: データ損失リスクの最小化