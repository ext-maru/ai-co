# 📚 Elders Guild Core 移行ガイド

## 🎯 概要

Elders Guild Coreは、ワーカーとマネージャーの共通処理を標準化し、コードの重複を削減するための基盤モジュールです。

## 🏗️ ディレクトリ構造

```
ai_co/
├── core/                    # 共通基盤（新規）
│   ├── __init__.py         # パッケージ初期化
│   ├── base_worker.py      # ワーカー基底クラス
│   ├── base_manager.py     # マネージャー基底クラス
│   ├── common_utils.py     # 共通ユーティリティ
│   ├── config.py           # 統合設定管理
│   └── examples/           # 実装例
│       ├── enhanced_task_worker.py
│       └── enhanced_rag_manager.py
├── workers/                # 既存ワーカー
├── libs/                   # 既存マネージャー
└── ...
```

## 📋 移行手順

### 1. ワーカーの移行

#### Before（既存の実装）
```python
import pika
import logging
from pathlib import Path

class TaskWorker:
    def __init__(self, worker_id="worker-1"):
        self.worker_id = worker_id
        # RabbitMQ接続、ログ設定等を個別実装...
```

#### After（基底クラス使用）
```python
from core import BaseWorker, get_config, EMOJI

class TaskWorker(BaseWorker):
    def __init__(self, worker_id=None):
        super().__init__(worker_type='task', worker_id=worker_id)
        self.config = get_config()
        # 固有の初期化のみ
    
    def process_message(self, ch, method, properties, body):
        # メッセージ処理の実装
        pass
```

### 2. マネージャーの移行

#### Before（既存の実装）
```python
import logging
from pathlib import Path

class SomeManager:
    def __init__(self):
        # ログ設定、パス設定等を個別実装...
```

#### After（基底クラス使用）
```python
from core import BaseManager, get_config

class SomeManager(BaseManager):
    def __init__(self):
        super().__init__("SomeManager")
        self.config = get_config()
    
    def initialize(self) -> bool:
        # 初期化処理
        return True
```

## 🎁 提供される機能

### BaseWorker
- ✅ RabbitMQ接続管理
- ✅ ログ設定
- ✅ シグナルハンドリング  
- ✅ エラーハンドリング
- ✅ キュー管理
- ✅ ヘルスチェック

### BaseManager
- ✅ ログ設定
- ✅ エラーハンドリング
- ✅ 統計管理
- ✅ 設定検証
- ✅ コンテキストマネージャー
- ✅ ヘルスチェック

### Common Utils
- ✅ プロジェクトパス管理
- ✅ ログセットアップ
- ✅ ファイル操作
- ✅ コマンド実行
- ✅ テキスト処理
- ✅ 絵文字定数

### Config
- ✅ 環境変数統合
- ✅ 設定ファイル読み込み
- ✅ 型安全な設定
- ✅ 検証機能

## 💡 実装のポイント

### 1. 必須メソッドの実装

**ワーカー**
```python
@abstractmethod
def process_message(self, ch, method, properties, body) -> None:
    """メッセージ処理（実装必須）"""
    pass
```

**マネージャー**
```python
@abstractmethod
def initialize(self) -> bool:
    """初期化処理（実装必須）"""
    pass
```

### 2. 設定の活用

```python
# グローバル設定の取得
from core import get_config

config = get_config()
model = config.worker.default_model
slack_enabled = config.slack.enabled
```

### 3. エラーハンドリング

```python
# BaseWorker/BaseManagerのメソッドを使用
self.handle_error(e, "operation_name", critical=True)
```

### 4. 統計情報

```python
# 自動的に統計が収集される
stats = self.get_stats()
health = self.health_check()
```

## 🔄 段階的移行

### Phase 1: 新規ワーカー/マネージャー
- 新しく作成するものから基底クラスを使用

### Phase 2: 主要コンポーネント
- TaskWorker
- PMWorker
- RAGManager
- SlackNotifier

### Phase 3: 全体移行
- すべてのワーカー/マネージャーを移行

## ⚠️ 注意事項

1. **既存の動作を維持**
   - 基底クラスは追加機能を提供するが、既存の動作を変更しない

2. **段階的な移行**
   - 一度にすべてを移行する必要はない
   - 動作確認しながら段階的に進める

3. **設定ファイル**
   - 既存の設定ファイルは引き続き使用可能
   - 新しい統合設定も並行して利用可能

## 📊 移行のメリット

- **コード削減**: 共通処理で約30-50%のコード削減
- **保守性向上**: 共通処理の一元管理
- **機能追加**: ヘルスチェック、統計等の自動提供
- **品質向上**: エラーハンドリングの統一

## 🚀 移行コマンド例

```bash
# 移行前のバックアップ
cp workers/task_worker.py workers/task_worker.py.bak

# 新しい実装のテスト
python3 core/examples/enhanced_task_worker.py --worker-id test-1

# 動作確認後、本番移行
mv core/examples/enhanced_task_worker.py workers/task_worker.py
```

## 📝 チェックリスト

移行時の確認項目：

- [ ] 基底クラスを継承
- [ ] 必須メソッドを実装
- [ ] super().__init__()を呼び出し
- [ ] 共通処理を削除（重複を避ける）
- [ ] 設定をget_config()から取得
- [ ] エラーハンドリングを統一
- [ ] テストを実行
- [ ] ログ出力を確認

---

**💡 Tips**: まずは`core/examples/`の実装例を参考に、小さなワーカーから移行を始めることをお勧めします。
