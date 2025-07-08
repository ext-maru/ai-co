# 🧪 AI Company テストルール・ガイドライン ナレッジベース v1.0

## 📋 概要

AI Companyの品質を保証するための包括的なテストルールとガイドラインです。すべての開発者とAIは、コード変更時にこれらのルールに従ってテストを作成・実行する必要があります。

## 🎯 テストの基本原則

### 1. **テストファースト開発**
```
新機能追加 → テスト作成 → 実装 → テスト実行 → リファクタリング
```

### 2. **自動化の徹底**
- すべてのテストは自動実行可能
- 手動テストは最小限に
- CI/CD統合を前提に設計

### 3. **独立性の確保**
- 各テストは独立して実行可能
- テスト間の依存関係は禁止
- 外部サービスはモック化

## 📂 テストディレクトリ構造

```
tests/
├── __init__.py          # テストパッケージ初期化
├── test_base.py         # 基底テストクラス
├── run_tests.py         # テストランナー
├── unit/                # ユニットテスト
│   ├── test_base_worker.py
│   ├── test_base_manager.py
│   ├── test_task_worker.py
│   └── test_*.py
├── integration/         # 統合テスト
│   ├── test_message_flow.py
│   └── test_*.py
├── fixtures/            # テストフィクスチャ
│   ├── sample_data.json
│   └── mock_responses.py
└── performance/         # パフォーマンステスト
    └── test_load.py
```

## 🔧 テスト作成ルール

### 1. **命名規則**

```python
# テストファイル名
test_[テスト対象モジュール名].py

# テストクラス名
class Test[テスト対象クラス名](TestCase):
    pass

# テストメソッド名
def test_[テスト内容を説明する名前](self):
    """[日本語での説明]"""
    pass
```

### 2. **テストメソッドの構造（AAA パターン）**

```python
def test_worker_processes_message_successfully(self):
    """ワーカーがメッセージを正常に処理することを確認"""
    # Arrange（準備）
    worker = TestWorker()
    message = create_test_message()
    
    # Act（実行）
    result = worker.process_message(message)
    
    # Assert（検証）
    self.assertEqual(result['status'], 'success')
    self.assertIn('task_id', result)
```

### 3. **必須テストカテゴリ**

#### ユニットテスト（必須）
- **正常系**: 期待される入力での動作
- **異常系**: エラー処理、例外処理
- **境界値**: 限界値での動作
- **エッジケース**: 特殊な条件

```python
class TestTaskWorker(WorkerTestCase):
    def test_process_valid_task(self):
        """正常なタスクの処理"""
        
    def test_handle_invalid_json(self):
        """不正なJSONの処理"""
        
    def test_handle_empty_message(self):
        """空メッセージの処理"""
        
    def test_retry_on_failure(self):
        """失敗時のリトライ"""
```

#### 統合テスト（重要な機能）
- ワーカー間の連携
- データベースとの統合
- 外部サービスとの連携

#### パフォーマンステスト（主要コンポーネント）
- 処理速度
- メモリ使用量
- 並行処理性能

## 📏 カバレッジ基準

### 最小カバレッジ要件

| コンポーネント | 最小カバレッジ | 推奨カバレッジ |
|--------------|--------------|--------------|
| Core モジュール | 90% | 95% |
| Workers | 80% | 90% |
| Managers | 80% | 90% |
| Utilities | 70% | 85% |
| 全体 | 80% | 90% |

### カバレッジ除外対象
```python
# pragma: no cover を使用して除外
if __name__ == "__main__":  # pragma: no cover
    main()

# または .coveragerc で設定
[run]
omit = 
    */tests/*
    */venv/*
    */migrations/*
```

## 🎯 テスト実行ルール

### 1. **コミット前の必須テスト**

```bash
# 最低限実行すべきテスト
ai-test quick  # ユニットテストのクイック実行

# 推奨
ai-test all    # 全テスト実行
```

### 2. **新機能・修正時のテストフロー**

```bash
# 1. 関連テストの実行
ai-test -p [機能名]

# 2. 影響範囲の確認
ai-test unit

# 3. 統合テスト
ai-test integration

# 4. カバレッジ確認
ai-test coverage
```

### 3. **テスト失敗時の対応**

```python
# ❌ NG: テストを無効化
@unittest.skip("一時的にスキップ")  # 絶対ダメ

# ✅ OK: 問題を修正
def test_feature(self):
    # 実装を修正してテストを通す
    pass
```

## 🔍 モックとスタブのルール

### 1. **外部依存のモック化**

```python
# RabbitMQ接続のモック
@patch('pika.BlockingConnection')
def test_worker(self, mock_pika):
    mock_pika.return_value = Mock()

# HTTPリクエストのモック
@patch('requests.post')
def test_api_call(self, mock_post):
    mock_post.return_value.json.return_value = {'status': 'ok'}

# ファイルシステムのモック
@patch('builtins.open', mock_open(read_data='test data'))
def test_file_read(self):
    pass
```

### 2. **データベースのモック**

```python
# SQLiteメモリDBを使用
def setUp(self):
    self.conn = sqlite3.connect(':memory:')
    self.conn.executescript(SCHEMA)

# またはモックを使用
@patch('sqlite3.connect')
def test_db_operation(self, mock_connect):
    mock_cursor = Mock()
    mock_connect.return_value.cursor.return_value = mock_cursor
```

## 📝 テストドキュメンテーション

### 1. **テストケースの説明**

```python
class TestRAGManager(ManagerTestCase):
    """
    RAGManagerのテストスイート
    
    このテストでは以下を検証します：
    - 類似タスクの検索機能
    - プロンプト強化機能
    - データベース操作の正確性
    """
    
    def test_search_returns_relevant_results(self):
        """
        類似タスク検索が関連性の高い結果を返すことを確認
        
        期待される動作:
        1. 検索クエリに基づいて類似タスクを取得
        2. 関連性スコアでソート
        3. 指定された件数のみ返す
        """
```

### 2. **複雑なテストのコメント**

```python
def test_concurrent_message_processing(self):
    """並行メッセージ処理のテスト"""
    # 50個の並行タスクを作成して、
    # デッドロックや競合状態が発生しないことを確認
    
    # 共有リソースへのアクセスをシミュレート
    shared_resource = threading.Lock()
    
    # ... テストコード ...
```

## 🚀 継続的インテグレーション（CI）

### 1. **自動テスト実行**

```yaml
# .github/workflows/test.yml の例
name: Test AI Company

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          ai-test all
```

### 2. **テスト結果の通知**

```python
# Slack通知統合
if os.getenv('CI'):
    if test_failed:
        notify_slack(f"❌ テスト失敗: {failed_tests}")
    else:
        notify_slack("✅ 全テスト成功")
```

## 🎯 プログラム変更時の適用ルール

### 1. **必須テスト更新**

プログラムを変更する際は、以下のテストを必ず更新・追加する：

```python
# 変更前にテストを書く（TDD）
def test_new_feature(self):
    """新機能のテスト"""
    # 1. まずテストを書く（失敗する）
    result = new_feature()
    self.assertEqual(result, expected)

# 2. 機能を実装

# 3. テストが通ることを確認
```

### 2. **影響分析とテスト**

```bash
# 変更ファイルに関連するテストを実行
git diff --name-only | xargs -I {} ai-test -p {}

# 依存関係のあるコンポーネントのテスト
ai-test -p worker  # ワーカー変更時
ai-test -p manager # マネージャー変更時
```

### 3. **回帰テストの実施**

```python
# 既存機能が壊れていないことを確認
class TestRegression(IntegrationTestCase):
    """回帰テストスイート"""
    
    def test_existing_task_flow(self):
        """既存のタスクフローが正常に動作することを確認"""
        
    def test_backward_compatibility(self):
        """後方互換性の確認"""
```

## 📊 テストメトリクス

### 収集すべきメトリクス

1. **テスト実行時間**
   - 各テストの実行時間
   - 全体の実行時間
   - ボトルネックの特定

2. **テスト成功率**
   - 日次/週次の成功率
   - 失敗パターンの分析

3. **カバレッジ推移**
   - カバレッジの増減
   - 未テスト部分の特定

## 🔥 アンチパターン（避けるべきこと）

### 1. **テストの無効化**
```python
# ❌ NG
@unittest.skip("壊れているので後で修正")
@pytest.mark.skip(reason="時間がかかる")
```

### 2. **不適切なアサーション**
```python
# ❌ NG: 意味のないアサーション
self.assertTrue(True)
self.assertIsNotNone(None or "something")

# ✅ OK: 具体的なアサーション
self.assertEqual(result.status, 'completed')
self.assertGreater(len(results), 0)
```

### 3. **テスト間の依存**
```python
# ❌ NG: 順序依存のテスト
def test_1_create(self):
    self.id = create_object()
    
def test_2_delete(self):
    delete_object(self.id)  # test_1に依存

# ✅ OK: 独立したテスト
def test_create_and_delete(self):
    id = create_object()
    delete_object(id)
```

## 🎓 ベストプラクティス

1. **明確なテスト名**
   - 何をテストしているか一目で分かる
   - 日本語のdocstringで補足

2. **適切なテストデータ**
   - 現実的なデータを使用
   - エッジケースも考慮

3. **高速なテスト**
   - 個々のテストは高速に
   - 遅いテストは別カテゴリに

4. **保守しやすいテスト**
   - DRY原則の適用
   - ヘルパーメソッドの活用

---

**🧪 これらのルールに従うことで、AI Companyの品質と信頼性を継続的に向上させます**