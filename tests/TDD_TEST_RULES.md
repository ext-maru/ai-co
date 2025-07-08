# 🧪 AI Company TDDテストルール・ガイドライン v2.0

## 📋 概要

AI CompanyのTest Driven Development (TDD)に基づくテストルールとガイドラインです。**すべての開発はテストファーストで行います**。

## 🔴🟢🔵 TDD基本原則

### Red → Green → Refactor サイクル

1. **🔴 Red Phase（失敗するテストを書く）**
   ```bash
   # まずテストを書く
   ai-tdd new FeatureName "要件"
   # または手動で
   vim tests/unit/test_feature.py
   ```

2. **🟢 Green Phase（テストを通す）**
   ```bash
   # 最小限の実装でテストを通す
   pytest tests/unit/test_feature.py -v
   ```

3. **🔵 Refactor Phase（改善）**
   ```bash
   # コードの品質を向上
   ai-test-coverage --html
   ```

### TDDの鉄則

- ❌ **絶対にやってはいけないこと**: 実装を先に書く
- ✅ **必ず守ること**: テストが失敗することを確認してから実装

## 🎯 Claude CLIでのTDD実践

### 基本的な使い方

```bash
# TDD開発を明示的に依頼
ai-send "UserManagerをTDDで開発:
1. ユーザー登録機能
2. メールアドレス検証
3. 重複チェック
まずテストから書いてください"

# 専用コマンドを使用
ai-tdd new UserManager "ユーザー管理機能"
```

### Claude CLIへの効果的な指示

#### 良い例 ✅
```bash
ai-send "EmailValidatorをTDDで開発:
1. test_email_validator.pyを最初に作成
2. 以下のテストケース:
   - 正常なメールアドレス
   - @マークなし → ValueError
   - ドメインなし → ValueError
   - 空文字 → ValueError
3. テストが失敗することを確認
4. 最小限の実装
5. リファクタリング"
```

#### 悪い例 ❌
```bash
# 曖昧すぎる
ai-send "メール機能を作って"

# TDDを無視
ai-send "EmailValidatorを実装して、後でテストも書いて"
```

## 📂 テストディレクトリ構造

```
tests/
├── __init__.py
├── TDD_TEST_RULES.md    # このファイル
├── conftest.py          # pytest共通設定
├── unit/                # ユニットテスト（TDD必須）
│   ├── core/           # コアモジュールテスト
│   │   ├── test_base_worker_tdd.py
│   │   └── test_base_manager_tdd.py
│   ├── test_*.py
│   └── test_managers/
├── integration/         # 統合テスト
├── e2e/                # E2Eテスト
└── fixtures/           # テストデータ
```

## 🔧 テスト作成ルール

### 1. 命名規則

```python
# ファイル名: test_から始まる
test_user_manager.py

# クラス名: Testから始まる
class TestUserManager:

# メソッド名: test_should_で始まる（振る舞いを記述）
def test_should_create_user_with_valid_email(self):
    """有効なメールアドレスでユーザーを作成できることを確認"""
    pass

def test_should_raise_error_when_email_invalid(self):
    """無効なメールアドレスでエラーが発生することを確認"""
    pass
```

### 2. AAAパターンの徹底

```python
def test_should_process_message_successfully(self):
    """メッセージを正常に処理できることを確認"""
    # Arrange（準備）
    worker = Worker()
    message = {"task_id": "123", "action": "process"}
    
    # Act（実行）
    result = worker.process_message(message)
    
    # Assert（検証）
    assert result["status"] == "success"
    assert result["task_id"] == "123"
```

### 3. テストの独立性

```python
# ❌ 悪い例: 他のテストに依存
class TestBadExample:
    def test_1_create_user(self):
        self.user_id = create_user()  # 状態を保持
    
    def test_2_delete_user(self):
        delete_user(self.user_id)  # test_1に依存

# ✅ 良い例: 独立したテスト
class TestGoodExample:
    def test_should_create_and_delete_user(self):
        # Arrange
        user_id = create_user()
        
        # Act
        result = delete_user(user_id)
        
        # Assert
        assert result is True
```

## 📏 カバレッジ基準

### 最小カバレッジ要件

| コンポーネント | 最小 | 推奨 | TDD目標 |
|--------------|-----|------|--------|
| Core (BaseWorker/Manager) | 90% | 95% | 100% |
| Workers | 80% | 90% | 95% |
| Libs/Managers | 80% | 90% | 95% |
| Commands | 70% | 85% | 90% |
| 全体 | 80% | 90% | 95% |

### カバレッジ確認

```bash
# 基本的な確認
pytest --cov=. --cov-report=term

# 詳細なHTMLレポート
ai-test-coverage --html

# 特定モジュール
pytest --cov=workers.task_worker tests/unit/test_task_worker.py
```

## 🎯 必須テストカテゴリ

### 1. 初期化テスト
```python
def test_should_initialize_with_default_config(self):
    """デフォルト設定で初期化できることを確認"""

def test_should_initialize_with_custom_config(self):
    """カスタム設定で初期化できることを確認"""
```

### 2. 正常系テスト
```python
def test_should_process_valid_input(self):
    """正常な入力を処理できることを確認"""

def test_should_return_expected_output(self):
    """期待される出力を返すことを確認"""
```

### 3. 異常系テスト
```python
def test_should_handle_invalid_input(self):
    """無効な入力を適切に処理することを確認"""

def test_should_raise_error_on_missing_required_field(self):
    """必須フィールドが不足している場合エラーを発生させることを確認"""
```

### 4. 境界値テスト
```python
def test_should_handle_empty_list(self):
    """空のリストを処理できることを確認"""

def test_should_handle_maximum_size(self):
    """最大サイズを処理できることを確認"""
```

### 5. 統合テスト（TDD後）
```python
def test_should_integrate_with_rabbitmq(self):
    """RabbitMQと統合できることを確認"""

def test_should_send_slack_notification(self):
    """Slack通知を送信できることを確認"""
```

## 🔍 モックとスタブ

### 基本的なモック

```python
from unittest.mock import Mock, patch, MagicMock

@patch('pika.BlockingConnection')
def test_should_connect_to_rabbitmq(self, mock_connection):
    """RabbitMQに接続できることを確認"""
    # Arrange
    mock_channel = Mock()
    mock_connection.return_value.channel.return_value = mock_channel
    
    # Act
    worker = Worker()
    
    # Assert
    mock_connection.assert_called_once()
```

### 時間のモック

```python
@patch('time.time', return_value=1234567890)
def test_should_generate_timestamp(self, mock_time):
    """タイムスタンプを生成できることを確認"""
    # Act
    timestamp = generate_timestamp()
    
    # Assert
    assert timestamp == "2009-02-13T23:31:30"
```

## 🚀 TDD自動化

### pre-commitフック

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tdd-check
        name: TDD Test Check
        entry: pytest tests/unit -x --tb=short
        language: system
        stages: [commit]
```

### GitHub Actions

```yaml
name: TDD CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run TDD Tests
        run: |
          pip install -r test-requirements.txt
          pytest tests/unit -v --cov=. --cov-fail-under=80
```

## 📝 テストドキュメンテーション

### クラスレベル

```python
class TestEmailValidator:
    """EmailValidatorのテストスイート
    
    以下の機能をテスト:
    - メールアドレスの形式検証
    - ドメインの存在確認
    - 使い捨てメールアドレスの検出
    """
```

### メソッドレベル

```python
def test_should_validate_standard_email_format(self):
    """標準的なメールアドレス形式を検証できることを確認
    
    テストケース:
    - user@example.com → True
    - user.name@example.co.jp → True
    - user+tag@example.com → True
    """
```

## 🎓 TDDベストプラクティス

### 1. 小さなステップで進める
- 一度に1つのテストケースのみ追加
- テストが通ったら次へ進む

### 2. テストを信頼する
- テストが失敗 → 実装に問題あり
- テストが成功 → 実装は正しい

### 3. リファクタリングを恐れない
- テストがあれば安全に改善できる
- パフォーマンス改善も安心

### 4. テストもリファクタリング
- DRY原則はテストコードにも適用
- 共通処理はfixture化

## 🚫 アンチパターン

### 1. テスト後付け ❌
```python
# 実装してからテストを書く → TDD違反
```

### 2. 大きすぎるテスト ❌
```python
def test_everything(self):
    # 100行以上のテスト → 分割すべき
```

### 3. 実装詳細のテスト ❌
```python
def test_private_method(self):
    # プライベートメソッドをテスト → インターフェースをテスト
```

### 4. 不安定なテスト ❌
```python
def test_flaky(self):
    # 時々失敗する → 原因を特定して修正
```

## 🔧 便利なツール

### pytest-watch
```bash
# ファイル変更を監視して自動テスト
pytest-watch tests/unit -v
```

### pytest-xdist
```bash
# 並列実行で高速化
pytest -n auto tests/
```

### pytest-cov
```bash
# カバレッジレポート生成
pytest --cov=. --cov-report=html
```

## 📊 メトリクス

### 追跡すべき指標
- テスト実行時間
- テストカバレッジ
- テスト成功率
- コード品質スコア

### レポート生成
```bash
# TDDメトリクスレポート
ai-send "TDDメトリクスを分析:
- 各モジュールのカバレッジ
- テスト/コード比率
- 最も変更頻度の高いテスト
- 改善提案"
```

---

**Remember: Always Red → Green → Refactor** 🔴🟢🔵