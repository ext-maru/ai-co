# 🏗️ AI Company Core - 共通基盤モジュール

## 概要

AI Company Coreは、ワーカーとマネージャーの共通処理を標準化するための基盤モジュールです。コードの重複を削減し、保守性を向上させます。

## 🚀 クイックスタート

### ワーカーの作成

```python
from core import BaseWorker

class MyWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type='my_worker')
    
    def process_message(self, ch, method, properties, body):
        # メッセージ処理を実装
        task = json.loads(body)
        # 処理...
        self.send_result({'status': 'completed'})
```

### マネージャーの作成

```python
from core import BaseManager

class MyManager(BaseManager):
    def __init__(self):
        super().__init__("MyManager")
    
    def initialize(self):
        # 初期化処理
        return True
```

## 📦 提供されるコンポーネント

### 1. BaseWorker
RabbitMQワーカーの基底クラス

**機能:**
- RabbitMQ接続管理
- キュー管理
- エラーハンドリング
- シグナルハンドリング
- ヘルスチェック

### 2. BaseManager
マネージャーの基底クラス

**機能:**
- ログ管理
- エラーハンドリング
- 統計情報
- 設定検証
- コンテキストマネージャー

### 3. Common Utils
共通ユーティリティ関数

**主な関数:**
- `get_project_paths()`: プロジェクトパス取得
- `setup_logging()`: ログ設定
- `generate_task_id()`: タスクID生成
- `format_filesize()`: ファイルサイズ整形
- `run_command()`: 外部コマンド実行

### 4. Config
統合設定管理

**機能:**
- 環境変数の読み込み
- 設定ファイルの統合
- 型安全な設定アクセス
- 設定の検証

## 🔧 設定

### 環境変数

```bash
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USER=guest
export RABBITMQ_PASS=guest
```

### 設定ファイル

- `config/slack.conf`: Slack設定
- `config/worker.json`: ワーカー設定
- `config/storage.json`: ストレージ設定
- `config/git.json`: Git設定

### 設定へのアクセス

```python
from core import get_config

config = get_config()

# 設定値の取得
model = config.worker.default_model
slack_enabled = config.slack.enabled

# ドット記法でのアクセス
timeout = config.get('worker.timeout', 300)
```

## 📋 使用例

### 完全なワーカー実装

```python
from core import BaseWorker, get_config, EMOJI

class DataProcessWorker(BaseWorker):
    def __init__(self):
        super().__init__(worker_type='data_process')
        self.config = get_config()
        
    def process_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            self.logger.info(f"{EMOJI['process']} Processing data...")
            
            # データ処理
            result = self.process_data(data)
            
            # 結果送信
            self.send_result({
                'task_id': data.get('task_id'),
                'status': 'completed',
                'result': result
            })
            
        except Exception as e:
            self.handle_error(e, "process_data")
            raise
    
    def process_data(self, data):
        # 実際の処理
        return {"processed": True}
```

### マネージャーの実装

```python
from core import BaseManager

class CacheManager(BaseManager):
    def __init__(self):
        super().__init__("CacheManager")
        self.cache = {}
        
    def initialize(self):
        # キャッシュの初期化
        self.logger.info("Cache initialized")
        return True
    
    def get(self, key):
        value = self.cache.get(key)
        self._increment_stats("get")
        return value
    
    def set(self, key, value):
        self.cache[key] = value
        self._increment_stats("set")
```

## 🧪 テスト

```bash
# ワーカーのテスト
python3 core/examples/enhanced_task_worker.py

# マネージャーのテスト  
python3 core/examples/enhanced_rag_manager.py

# ユニットテスト（将来実装）
python3 -m pytest tests/core/
```

## 📊 モニタリング

### ヘルスチェック

```python
# ワーカーのヘルスチェック
health = worker.health_check()
# {
#     'worker_id': 'task-12345',
#     'worker_type': 'task',
#     'is_running': True,
#     'is_connected': True,
#     'current_task': None,
#     'timestamp': '2025-07-01T12:00:00'
# }

# マネージャーのヘルスチェック
health = manager.health_check()
# {
#     'manager_name': 'MyManager',
#     'healthy': True,
#     'stats': {...},
#     'timestamp': '2025-07-01T12:00:00'
# }
```

### 統計情報

```python
stats = manager.get_stats()
# {
#     'created_at': '2025-07-01T12:00:00',
#     'operations': 1000,
#     'errors': 5,
#     'last_operation': {...},
#     'uptime_seconds': 3600
# }
```

## 🔍 トラブルシューティング

### RabbitMQ接続エラー

```python
# 接続リトライの調整
worker.connect(retry_count=5, retry_delay=2.0)
```

### ログレベルの変更

```python
import logging
from core import setup_logging

logger = setup_logging("MyWorker", level=logging.DEBUG)
```

### 設定の再読み込み

```python
from core import reload_config

config = reload_config()
```

## 🤝 貢献方法

1. 新しい共通機能の提案
2. バグ修正
3. ドキュメントの改善
4. テストの追加

## 📄 ライセンス

AI Company内部使用

---

**Version**: 1.0.0  
**Last Updated**: 2025-07-01
