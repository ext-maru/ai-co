# 📚 Elders Guild 軽量標準化ガイド

## 🎯 概要

Phase 1の軽量標準化により、以下のコンポーネントを導入しました：

1. **BaseWorker** - すべてのワーカーの基底クラス
2. **BaseManager** - すべてのマネージャーの基底クラス
3. **common_utils** - 共通ユーティリティ関数

## 🏗️ 新しい構造

```
ai_co/
├── core/                    # 🆕 共通基盤
│   ├── __init__.py         # パッケージ初期化
│   ├── base_worker.py      # ワーカー基底クラス
│   ├── base_manager.py     # マネージャー基底クラス
│   └── common_utils.py     # 共通ユーティリティ
├── workers/                # 既存
├── libs/                   # 既存
└── ...
```

## 🔄 移行方法

### 1. 既存ワーカーの移行

**Before:**
```python
class TestWorker:
    def __init__(self):
        self.name = "test_worker"
        # 手動でRabbitMQ接続、ログ設定など
```

**After:**
```python
from core import BaseWorker

class TestWorker(BaseWorker):
    def __init__(self, worker_id="001"):
        super().__init__(
            worker_id=worker_id,
            worker_type="test",
            input_queue="test_queue",
            output_queue="test_results"
        )
    
    def process_message(self, message):
        # メッセージ処理ロジックのみに集中
        return {"processed": True}
```

### 2. 既存マネージャーの移行

**Before:**
```python
class TaskHistoryDB:
    def __init__(self):
        # 手動でDB接続、ログ設定など
```

**After:**
```python
from core import BaseManager

class TaskHistoryDB(BaseManager):
    def __init__(self):
        super().__init__(
            manager_name="TaskHistoryDB",
            db_path="task_history.db"
        )
    
    def setup_schema(self):
        # スキーマ定義
```

## 🎯 メリット

### 1. **コードの削減**
- 共通処理の重複を排除
- ボイラープレートコードの削減
- 各クラスは本質的なロジックに集中

### 2. **信頼性の向上**
- 統一されたエラーハンドリング
- 自動リトライ機能
- グレースフルシャットダウン

### 3. **保守性の向上**
- 一貫性のあるコード構造
- 共通機能の一元管理
- デバッグが容易

### 4. **自己進化との相性**
- シンプルなクラス構造を維持
- AIが理解しやすいパターン
- 柔軟な拡張が可能

## 📋 移行チェックリスト

### 優先度: 高
- [ ] TaskWorker → BaseWorker継承
- [ ] PMWorker → BaseWorker継承
- [ ] ResultWorker → BaseWorker継承

### 優先度: 中
- [ ] DialogTaskWorker → BaseWorker継承
- [ ] DialogPMWorker → BaseWorker継承
- [ ] TaskHistoryDB → BaseManager継承
- [ ] ConversationManager → BaseManager継承

### 優先度: 低
- [ ] その他のワーカー
- [ ] その他のマネージャー

## 🛠️ 実装のヒント

### 1. 段階的な移行
```bash
# 1. 新しいファイルとして作成
cp workers/task_worker.py workers/task_worker_refactored.py

# 2. BaseWorkerを使って書き換え

# 3. テスト
python3 workers/task_worker_refactored.py

# 4. 置き換え
mv workers/task_worker.py workers/task_worker.py.bak
mv workers/task_worker_refactored.py workers/task_worker.py
```

### 2. 共通パターンの活用
```python
# ログ出力
self.logger.info("✅ 処理完了")  # BaseWorkerのlogger使用

# エラーハンドリング
# BaseWorkerが自動的に処理、必要に応じてカスタマイズ

# 統計情報
def get_stats(self):
    stats = super().get_stats()  # 基本統計を継承
    stats['custom_metric'] = self.custom_value
    return stats
```

### 3. テストの実行
```bash
# コアコンポーネントのテスト
python3 scripts/test_core_components.py

# 個別ワーカーのテスト
python3 workers/test_worker_refactored.py --id test_001
```

## 🚀 今後の展開

### Phase 1.5（オプション）
- Pydanticによる設定管理
- より高度なエラーハンドリング
- メトリクス収集の統一

### Phase 2（将来）
- 部分的なフレームワーク導入
- パフォーマンス最適化
- 分散処理の強化

## 📝 注意事項

1. **後方互換性**
   - 既存のキュー名、メッセージ形式は変更しない
   - 段階的に移行し、システム全体の安定性を保つ

2. **自己進化システムとの整合性**
   - BaseWorkerのprocess_messageメソッドは必須
   - ファイル配置ルールは変更しない

3. **シンプルさの維持**
   - 過度な抽象化は避ける
   - AIが理解・生成しやすい構造を保つ

## 🎉 まとめ

この軽量標準化により、Elders Guildシステムは：
- より保守しやすく
- より信頼性が高く
- より拡張しやすく

なりました。自己進化システムとの相性も良好で、今後の発展に向けた良い基盤ができました！
