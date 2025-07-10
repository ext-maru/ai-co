# Elders Guild TDD ワークフローガイド

## 📌 概要

このドキュメントは、Elders GuildプロジェクトにおけるTest Driven Development (TDD)の実践方法を説明します。

## 🔄 TDDサイクル

### 1. Red（失敗するテストを書く）
まず、実装する機能に対するテストを書きます。この時点では実装がないため、テストは失敗します。

```bash
# 新機能のTDD開発を開始
./scripts/tdd-new-feature.sh my_feature

# テストを実行（失敗することを確認）
pytest tests/unit/test_my_feature.py -v
```

### 2. Green（テストを通す最小限のコードを書く）
テストが通る最小限の実装を行います。

```python
# 最小限の実装例
def my_function():
    return "expected_result"  # テストが期待する値を返す
```

### 3. Refactor（コードを改善する）
テストが通った状態を維持しながら、コードを改善します。

## 🛠️ TDD開発フロー

### 1. 環境セットアップ

```bash
# 初回のみ実行
./scripts/setup-tdd.sh

# テスト依存関係のインストール
pip install -r test-requirements.txt

# pre-commitフックのインストール
pre-commit install
```

### 2. 新機能開発の開始

```bash
# TDD用のテストテンプレートを生成
./scripts/tdd-new-feature.sh worker_manager

# 生成されたテストファイルを編集
vim tests/unit/test_worker_manager.py
```

### 3. テストケースの作成

```python
import pytest
from unittest.mock import Mock, patch

class TestWorkerManager:
    """WorkerManagerのテストクラス"""
    
    def test_should_initialize_with_default_config(self):
        """デフォルト設定で初期化できることを確認"""
        # Arrange
        expected_config = {'max_workers': 10}
        
        # Act
        manager = WorkerManager()
        
        # Assert
        assert manager.config == expected_config
    
    def test_should_add_worker_successfully(self):
        """ワーカーを正常に追加できることを確認"""
        # Arrange
        manager = WorkerManager()
        worker = Mock()
        
        # Act
        result = manager.add_worker(worker)
        
        # Assert
        assert result is True
        assert worker in manager.workers
    
    def test_should_handle_worker_failure(self):
        """ワーカー障害を適切に処理できることを確認"""
        # Arrange
        manager = WorkerManager()
        failing_worker = Mock()
        failing_worker.health_check.side_effect = Exception("Worker failed")
        
        # Act & Assert
        with pytest.raises(WorkerFailureException):
            manager.check_worker_health(failing_worker)
```

### 4. 実装

```python
# libs/worker_manager.py

class WorkerManager:
    """ワーカー管理クラス"""
    
    def __init__(self, config=None):
        self.config = config or {'max_workers': 10}
        self.workers = []
    
    def add_worker(self, worker):
        """ワーカーを追加"""
        if len(self.workers) >= self.config['max_workers']:
            return False
        self.workers.append(worker)
        return True
    
    def check_worker_health(self, worker):
        """ワーカーの健全性をチェック"""
        try:
            worker.health_check()
        except Exception as e:
            raise WorkerFailureException(f"Worker health check failed: {e}")
```

### 5. テストの実行

```bash
# 単一ファイルのテスト
pytest tests/unit/test_worker_manager.py -v

# カバレッジ付きテスト
pytest tests/unit/test_worker_manager.py -v --cov=libs.worker_manager

# すべてのユニットテスト
./scripts/run-tdd-tests.sh unit

# 監視モード（ファイル変更時に自動実行）
./scripts/run-tdd-tests.sh watch
```

### 6. カバレッジの確認

```bash
# カバレッジレポートの生成
./scripts/coverage-report.py

# HTMLレポートを開く
ai-test-coverage --html

# カバレッジの継続的監視
ai-test-coverage --watch
```

## 📋 TDDベストプラクティス

### 1. テストの命名規則

```python
def test_should_[期待される動作]_when_[条件](self):
    """日本語での説明"""
    pass

# 例
def test_should_return_error_when_invalid_input(self):
    """無効な入力の場合エラーを返すことを確認"""
    pass
```

### 2. AAA パターンの使用

```python
def test_example(self):
    # Arrange（準備）
    test_data = {"key": "value"}
    mock_service = Mock()
    
    # Act（実行）
    result = process_data(test_data, mock_service)
    
    # Assert（検証）
    assert result["status"] == "success"
    mock_service.save.assert_called_once_with(test_data)
```

### 3. モックの適切な使用

```python
# 外部依存のモック
@patch('pika.BlockingConnection')
def test_rabbitmq_connection(self, mock_connection):
    # RabbitMQ接続をモック化
    pass

# 時間のモック
@patch('time.time', return_value=1234567890)
def test_timestamp_generation(self, mock_time):
    # 時間を固定してテスト
    pass
```

### 4. パラメータ化テスト

```python
@pytest.mark.parametrize("input,expected", [
    ("", ValueError),
    ("invalid", ValueError),
    ("valid_data", "processed_data"),
])
def test_input_validation(input, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            process_input(input)
    else:
        assert process_input(input) == expected
```

## 🚫 TDDアンチパターン

### 避けるべきこと

1. **テストの後付け**: 実装後にテストを書く
2. **過度に詳細なテスト**: 実装の詳細に依存したテスト
3. **テストの重複**: 同じことを複数のテストで確認
4. **遅いテスト**: 実行に時間がかかるテスト

### 推奨される対策

1. **テストファースト**: 常にテストから始める
2. **ブラックボックステスト**: インターフェースをテスト
3. **DRY原則**: テストコードも重複を避ける
4. **高速なテスト**: モックを活用して高速化

## 🔧 CI/CD統合

### GitHub Actionsでの自動テスト

```yaml
# .github/workflows/tdd.yml
name: TDD CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r test-requirements.txt
          pytest tests/unit -v --cov=. --cov-fail-under=80
```

### pre-commitフック

```bash
# コミット前に自動的にテストを実行
git commit -m "feat: 新機能追加"
# → pre-commitがテストを実行
# → テストが失敗したらコミットがブロックされる
```

## 📊 品質メトリクス

### 目標カバレッジ

| コンポーネント | 最小 | 推奨 |
|--------------|-----|------|
| Core (base_worker, base_manager) | 90% | 95% |
| Workers | 80% | 90% |
| Libs/Managers | 80% | 90% |
| Commands | 70% | 85% |

### メトリクス監視

```bash
# 品質メトリクスの確認
ai-metrics --component core

# テスト実行時間の分析
pytest tests/unit --durations=10

# 複雑度の分析
radon cc -s libs/ -a
```

## 🎯 TDD導入ロードマップ

### Phase 1: 基盤整備（完了）
- ✅ test-requirements.txt作成
- ✅ pre-commitフック設定
- ✅ カバレッジツール設定
- ✅ BaseWorker/BaseManagerテスト強化

### Phase 2: 文化構築（進行中）
- 📝 TDDワークフロー文書化
- 🔄 チーム教育とペアプロ
- 🤖 AIワーカーへのTDD統合

### Phase 3: CI/CD統合（予定）
- ⏳ GitHub Actions設定
- ⏳ カバレッジゲート
- ⏳ 自動デプロイ

### Phase 4: 継続的改善（予定）
- ⏳ メトリクス収集
- ⏳ パフォーマンス最適化
- ⏳ ベストプラクティス更新

## 📚 参考リソース

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [Test Driven Development: By Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Python Testing with pytest](https://pragprog.com/titles/bopytest/python-testing-with-pytest/)

---

**🎯 Remember: Red → Green → Refactor**