# 🧪 AI Company テストフレームワーク クイックガイド

## 🚀 クイックスタート

### 問題を修正して実行

```bash
# ワンクリック修正
chmod +x /home/aicompany/ai_co/fix_and_run_tests.sh
cd /home/aicompany/ai_co && ./fix_and_run_tests.sh
```

### 個別のテスト実行

```bash
# 動作確認用の簡単なテスト
ai-test tests/unit/test_simple.py

# BaseWorker実装テスト
ai-test tests/unit/test_base_worker_implementation.py

# ユニットテスト全体
ai-test unit
```

## 🔧 トラブルシューティング

### 1. ModuleNotFoundError: No module named 'tests.utils'

```bash
# 修正方法
cd /home/aicompany/ai_co
python scripts/setup_test_framework.py
```

### 2. 'unit' not found in markers configuration option

```bash
# pytest.iniを修正
cd /home/aicompany/ai_co
python scripts/diagnose_tests.py
```

### 3. import file mismatch エラー

```bash
# __pycache__をクリア
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### 4. テストが見つからない

```bash
# PYTHONPATHを設定
export PYTHONPATH="/home/aicompany/ai_co:$PYTHONPATH"
```

## 📝 新しいテストの作成

### 1. 自動生成

```bash
# ワーカーのテストを自動生成
python scripts/generate_test.py workers/new_worker.py
```

### 2. 手動作成（テンプレート）

```python
"""
[モジュール名]のテスト
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from workers.new_worker import NewWorker

@pytest.mark.unit
class TestNewWorker:
    """NewWorkerのテストクラス"""
    
    @pytest.fixture
    def worker(self):
        """テスト用ワーカー"""
        with patch('pika.BlockingConnection'):
            return NewWorker(worker_id="test-1")
    
    def test_initialization(self, worker):
        """初期化テスト"""
        assert worker.worker_id == "test-1"
        assert worker.worker_type == "new"
    
    def test_process_message(self, worker):
        """メッセージ処理テスト"""
        # テスト実装
        pass
```

## 📊 テストカバレッジ

### カバレッジ確認

```bash
# カバレッジ付きテスト実行
ai-test coverage

# HTMLレポート確認
# ブラウザで開く: htmlcov/index.html
```

### 目標カバレッジ

- **Core**: 90%以上
- **Workers**: 80%以上
- **Libs**: 80%以上
- **Scripts**: 60%以上

## 🎯 ベストプラクティス

### 1. テストファースト

```bash
# 1. テスト作成
python scripts/generate_test.py workers/new_feature.py

# 2. テスト実行（失敗確認）
ai-test tests/unit/test_new_feature.py

# 3. 実装
# workers/new_feature.py を実装

# 4. テスト再実行（成功確認）
ai-test tests/unit/test_new_feature.py
```

### 2. コミット前チェック

```bash
# pre-commitフック設定
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 3. 継続的テスト

```bash
# ファイル変更時に自動テスト
python scripts/apply_test_rules.py workers/task_worker.py
```

## 📚 詳細ドキュメント

- **テスト規約**: `docs/TEST_GUIDELINES.md`
- **pytest設定**: `pytest.ini`
- **共通fixture**: `tests/conftest.py`

---

**💡 ヒント**: 最初は `test_simple.py` でテストフレームワークの動作を確認してから、実際のテストを作成することをお勧めします。
