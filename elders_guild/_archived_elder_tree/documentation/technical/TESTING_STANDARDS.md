# 🧪 Elders Guild テスト標準規約 v1.0

## 📋 概要

Elders Guildのすべてのコード変更に適用されるテスト標準規約です。新規作成・既存コード修正時は必ずこの規約に従ってテストを実装・実行します。

## 🎯 テストの基本原則

### 1. テストファースト開発
- コード変更前にテストケースを定義
- 実装後は必ずテストを実行
- テストなしのコードはマージしない

### 2. テストカバレッジ目標
- **Core modules**: 90%以上
- **Workers**: 80%以上
- **Managers**: 80%以上
- **Utilities**: 70%以上

### 3. テストの種類

| テストタイプ | 目的 | 実行タイミング | 所要時間 |
|------------|-----|--------------|---------|
| Unit Test | 個別機能の検証 | コード変更時 | < 1秒/test |
| Integration Test | コンポーネント連携 | PR作成時 | < 10秒/test |
| E2E Test | 全体フロー検証 | リリース前 | < 5分 |
| Performance Test | 性能検証 | 週次 | < 30分 |

## 🗂️ テストファイル構造

```
/home/aicompany/ai_co/
├── tests/                      # メインテストディレクトリ
│   ├── unit/                  # ユニットテスト
│   │   ├── test_workers/     # ワーカーのテスト
│   │   ├── test_managers/    # マネージャーのテスト
│   │   └── test_core/        # コアモジュールのテスト
│   ├── integration/           # 統合テスト
│   ├── e2e/                  # E2Eテスト
│   ├── fixtures/             # テストデータ
│   └── conftest.py          # pytest設定
├── test_utils/               # テスト用ユーティリティ
└── .coverage                # カバレッジ設定
```

## 📝 テストファイル命名規則

```python
# ユニットテスト
test_<module_name>.py           # 例: test_task_worker.py

# 統合テスト
test_integration_<feature>.py   # 例: test_integration_rag_flow.py

# E2Eテスト
test_e2e_<scenario>.py         # 例: test_e2e_code_generation.py

# テストクラス
class Test<ComponentName>:      # 例: class TestTaskWorker:

# テストメソッド
def test_<action>_<expected>(): # 例: def test_process_message_success():
```

## 🔧 必須テストケース

### 1. ワーカーテスト

```python
class TestWorker:
    """すべてのワーカーが実装すべきテスト"""

    def test_initialization(self):
        """初期化が正常に完了すること"""

    def test_rabbitmq_connection(self):
        """RabbitMQ接続が確立できること"""

    def test_process_message_success(self):
        """正常なメッセージを処理できること"""

    def test_process_message_invalid_json(self):
        """不正なJSONを適切に処理すること"""

    def test_error_handling(self):
        """エラーが適切にハンドリングされること"""

    def test_graceful_shutdown(self):
        """グレースフルシャットダウンが動作すること"""
```

### 2. マネージャーテスト

```python
class TestManager:
    """すべてのマネージャーが実装すべきテスト"""

    def test_initialization(self):
        """初期化が正常に完了すること"""

    def test_configuration_loading(self):
        """設定が正しく読み込まれること"""

    def test_main_functionality(self):
        """主要機能が動作すること"""

    def test_error_recovery(self):
        """エラーからの復旧が可能なこと"""
```

### 3. 統合テスト

```python
class TestIntegration:
    """ワーカー間の連携テスト"""

    def test_task_to_pm_flow(self):
        """TaskWorker→PMWorkerのフローが動作すること"""

    def test_complete_task_flow(self):
        """タスク送信から完了通知までの全フローが動作すること"""

    def test_error_propagation(self):
        """エラーが適切に伝播すること"""
```

## 🎨 テストコード記述標準

### 1. AAA原則（Arrange-Act-Assert）

```python
def test_task_processing():
    # Arrange（準備）
    worker = TaskWorker()
    test_task = {"task_id": "test_123", "prompt": "test prompt"}

    # Act（実行）
    result = worker.process_task(test_task)

    # Assert（検証）
    assert result["status"] == "completed"
    assert "response" in result
```

### 2. モックの使用

```python
from unittest.mock import Mock, patch

@patch('pika.BlockingConnection')
def test_with_mock_connection(mock_conn):
    # RabbitMQ接続をモック化
    mock_conn.return_value = Mock()
    worker = TaskWorker()
    assert worker.connection is not None
```

### 3. フィクスチャの活用

```python
import pytest

@pytest.fixture
def sample_task():
    """テスト用タスクデータ"""
    return {
        "task_id": "test_123",
        "task_type": "code",
        "prompt": "Create a test function"
    }

def test_with_fixture(sample_task):
    result = process_task(sample_task)
    assert result is not None
```

## 🚀 自動テスト実行

### 1. プレコミットフック

```bash
# .git/hooks/pre-commit
#!/bin/bash
# 変更されたPythonファイルのテストを実行
python -m pytest tests/unit/ -v --tb=short
```

### 2. CI/CDパイプライン

```yaml
# .github/workflows/test.yml
name: Elders Guild Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: pytest tests/unit/ --cov=.
      - name: Run Integration Tests
        run: pytest tests/integration/
      - name: Check Coverage
        run: pytest --cov=. --cov-report=html --cov-fail-under=80
```

## 📊 テストメトリクス

### 必須メトリクス
- カバレッジ率
- テスト実行時間
- 失敗率
- フレークィネス（不安定なテストの割合）

### レポート生成

```bash
# カバレッジレポート
pytest --cov=. --cov-report=html

# パフォーマンステスト結果
pytest tests/performance/ --benchmark-only

# テスト統計
ai-test-report generate
```

## 🔄 テスト駆動開発フロー

1. **要件定義** → テストケース作成
2. **テスト作成** → 失敗することを確認（Red）
3. **実装** → テストが通ることを確認（Green）
4. **リファクタリング** → テストが通り続けることを確認（Refactor）
5. **統合テスト** → 他コンポーネントとの連携確認
6. **デプロイ** → 本番環境でのスモークテスト

## 🎯 テストチェックリスト

### 新規コード作成時
- [ ] ユニットテストを作成した
- [ ] テストカバレッジ80%以上を達成した
- [ ] エラーケースをテストした
- [ ] 境界値テストを実施した
- [ ] モックを適切に使用した

### 既存コード修正時
- [ ] 既存のテストが通ることを確認した
- [ ] 修正に対応するテストを追加した
- [ ] リグレッションテストを実施した
- [ ] 影響範囲の統合テストを実行した

### リリース前
- [ ] 全テストスイートが通過した
- [ ] パフォーマンステストで劣化がない
- [ ] E2Eテストが成功した
- [ ] テストレポートを生成した

## 🛠️ テストツール

### 必須ツール
- **pytest**: メインテストフレームワーク
- **pytest-cov**: カバレッジ測定
- **pytest-mock**: モック機能
- **pytest-benchmark**: パフォーマンステスト
- **pytest-xdist**: 並列実行

### 補助ツール
- **factory_boy**: テストデータ生成
- **freezegun**: 時刻固定
- **responses**: HTTPモック
- **pytest-timeout**: タイムアウト設定

## 📝 テストドキュメント

### テストケース記述

```python
def test_critical_functionality():
    """
    重要機能のテスト

    Given: 正常な設定とデータ
    When: process_critical_task()を実行
    Then: 期待される結果が返される

    テストID: TC001
    重要度: Critical
    カテゴリ: Core機能
    """
```

### テスト仕様書

各機能に対して以下を記載：
1. テスト対象
2. テスト条件
3. 期待結果
4. 実行手順
5. 確認項目

---

**🧪 この規約により、Elders Guildは高品質で信頼性の高いシステムを維持します**
