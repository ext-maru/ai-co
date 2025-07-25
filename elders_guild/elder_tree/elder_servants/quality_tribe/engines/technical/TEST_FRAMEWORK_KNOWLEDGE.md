# 🧪 Elders Guild テストフレームワーク ナレッジベース v1.0

## 📋 概要

Elders Guildのテストフレームワークは、pytestベースの包括的なテストシステムです。コード品質を維持し、変更による影響を早期に検出するための自動化された仕組みを提供します。

### **基本原則**
- ✅ **テストファースト開発** - 実装前にテストを書く
- ✅ **高カバレッジ維持** - Core 90%、Workers/Libs 80%以上
- ✅ **独立性** - 各テストは他に依存しない
- ✅ **自動化** - コミット前チェック、CI/CD統合

## 🏗️ ディレクトリ構造

```
/home/aicompany/ai_co/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest設定・共通fixture
│   ├── utils.py                 # テストユーティリティ
│   ├── unit/                    # ユニットテスト
│   │   ├── __init__.py
│   │   ├── test_simple.py       # 基本動作確認
│   │   ├── test_standalone.py   # 独立テスト（conftest非依存）
│   │   ├── test_task_worker_minimal.py
│   │   └── test_base_worker_implementation.py
│   ├── integration/             # 統合テスト
│   │   ├── __init__.py
│   │   └── test_worker_integration.py
│   ├── e2e/                     # E2Eテスト
│   │   ├── __init__.py
│   │   └── test_full_workflow.py
│   └── fixtures/                # テストデータ
│       ├── __init__.py
│       ├── sample_tasks.json
│       └── mock_responses.json
├── pytest.ini                   # pytest設定ファイル
├── scripts/
│   ├── ai-test                  # テスト実行コマンド
│   ├── generate_test.py         # テスト自動生成
│   ├── apply_test_rules.py      # テストルール適用
│   ├── setup_test_framework.py  # フレームワークセットアップ
│   ├── fix_conftest.py          # conftest修正ツール
│   ├── test_diagnostic.py       # 診断ツール
│   └── check_test_structure.py  # 構造確認ツール
└── docs/
    ├── TEST_GUIDELINES.md       # テストガイドライン
    └── TEST_QUICK_GUIDE.md      # クイックガイド
```

## 🔧 主要コンポーネント

### 1. **conftest.py**
pytestの設定と共通fixtureを定義。

**重要な要素:**
```python
# カスタムオプション定義（必須）
def pytest_addoption(parser):
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow tests"
    )

# 共通fixture
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """テスト環境の自動セットアップ"""
    monkeypatch.setenv("AI_COMPANY_TEST_MODE", "1")
    monkeypatch.setenv("DISABLE_SLACK_IN_TEST", "1")
```

### 2. **pytest.ini**
pytest設定ファイル。

```ini
[tool:pytest]
minversion = 6.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    unit: marks tests as unit tests
```

### 3. **ai-test コマンド**
統一されたテスト実行インターフェース。

```bash
ai-test all          # 全テスト
ai-test unit         # ユニットテストのみ
ai-test coverage     # カバレッジ付き
ai-test quick        # 高速テスト（slowスキップ）
```

## 📝 テスト作成ルール

### 1. **ファイル名規則**
```python
# ユニットテスト
test_<module_name>.py  # 例: test_task_worker.py

# 統合テスト
test_<feature>_integration.py  # 例: test_rag_integration.py
```

### 2. **テスト構造**
```python
"""
[モジュール名]のテスト
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# プロジェクトルートをPythonパスに追加（必須）
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from workers.task_worker import TaskWorker

@pytest.mark.unit
class TestTaskWorker:
    """TaskWorkerのテストクラス"""

    @pytest.fixture
    def worker(self):
        """テスト用ワーカー"""
        with patch('pika.BlockingConnection'):
            return TaskWorker(worker_id="test-1")

    def test_initialization(self, worker):
        """初期化テスト"""
        assert worker.worker_id == "test-1"
        assert worker.worker_type == "task"
```

### 3. **モック使用規則**
```python
# 外部依存は必ずモック化
@patch('pika.BlockingConnection')
@patch('subprocess.run')
def test_with_mocks(mock_run, mock_connection):
    # RabbitMQとClaude CLIをモック
    mock_run.return_value = Mock(returncode=0, stdout="Success")
    # テスト実装
```

## 🚨 よくあるエラーと対処法

### 1. **ModuleNotFoundError: No module named 'tests.utils'**

**原因**: tests/utils.pyが存在しない、またはPYTHONPATHが設定されていない

**解決方法**:
```bash
# セットアップスクリプト実行
python scripts/setup_test_framework.py

# または手動でPYTHONPATH設定
export PYTHONPATH="/home/aicompany/ai_co:$PYTHONPATH"
```

### 2. **ValueError: no option named '--skip-slow'**

**原因**: conftest.pyでpytest_addoptionが定義されていない

**解決方法**:
```bash
# 自動修正
python scripts/fix_conftest.py

# または手動でconftest.pyに追加
def pytest_addoption(parser):
    parser.addoption("--skip-slow", action="store_true")
```

### 3. **import file mismatch**

**原因**: __pycache__や重複ファイルの存在

**解決方法**:
```bash
# キャッシュクリア
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 重複ファイル削除
rm -f tests/unit/test_task_worker_fixed.py
rm -rf tests/unit/workers
```

## 🎯 ベストプラクティス

### 1. **テスト駆動開発（TDD）**
```bash
# 1. テスト作成
python scripts/generate_test.py workers/new_feature.py

# 2. テスト実行（失敗を確認）
ai-test tests/unit/test_new_feature.py

# 3. 実装
# workers/new_feature.py を実装

# 4. テスト再実行（成功を確認）
ai-test tests/unit/test_new_feature.py
```

### 2. **コミット前チェック**
```bash
# pre-commitフック設定
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 3. **カバレッジ維持**
```python
# カバレッジ目標
COVERAGE_TARGETS = {
    "core": 90,      # Core モジュール: 90%以上
    "workers": 80,   # Workers: 80%以上
    "libs": 80,      # Libraries: 80%以上
    "scripts": 60    # Scripts: 60%以上
}
```

## 📊 コマンドリファレンス

### テスト実行
```bash
# 基本実行
ai-test all                      # 全テスト
ai-test unit                     # ユニットテストのみ
ai-test integration              # 統合テストのみ
ai-test e2e                      # E2Eテストのみ

# オプション付き
ai-test quick                    # 高速（slowスキップ）
ai-test coverage                 # カバレッジ付き
ai-test all --parallel           # 並列実行
ai-test unit --verbose           # 詳細出力

# 特定ファイル
ai-test tests/unit/test_task_worker.py
ai-test specific tests/unit/ -k test_init
```

### テスト管理
```bash
# テスト生成
python scripts/generate_test.py workers/new_worker.py

# テストルール適用
python scripts/apply_test_rules.py workers/task_worker.py

# 診断
python scripts/test_diagnostic.py

# 構造確認
python scripts/check_test_structure.py
```

## 🛠️ トラブルシューティング

### 緊急修正スクリプト
```bash
# 完全自動修正（推奨）
chmod +x FINAL_FIX_TESTS.sh
./FINAL_FIX_TESTS.sh

# 個別修正
./fix_conftest_error.sh          # conftest.py修正
./fix_test_errors.sh             # 一般的なエラー修正
```

### 診断フロー
1. **診断実行**: `python scripts/test_diagnostic.py`
2. **問題特定**: エラーメッセージ確認
3. **修正適用**: 推奨される解決策を実行
4. **動作確認**: `ai-test tests/unit/test_standalone.py`

## 📈 継続的改善

### メトリクス監視
- テスト実行時間
- カバレッジ推移
- 失敗率
- フレーキーテストの検出

### 定期メンテナンス
```bash
# 週次
- 不要なテストの削除
- 遅いテストの最適化

# 月次
- カバレッジレポート確認
- テストパターンのレビュー
- ベストプラクティスの更新
```

## 🎨 テストタイプ別ガイド

### ユニットテスト
- **目的**: 個別のクラス/関数の動作確認
- **スコープ**: 単一モジュール
- **実行時間**: < 0.1秒/テスト
- **モック**: 外部依存はすべてモック

### 統合テスト
- **目的**: モジュール間の連携確認
- **スコープ**: 複数モジュール
- **実行時間**: < 1秒/テスト
- **モック**: 外部サービスのみモック

### E2Eテスト
- **目的**: 完全なワークフロー確認
- **スコープ**: システム全体
- **実行時間**: < 10秒/テスト
- **モック**: 最小限（本番環境に近い状態）

## 🔒 重要な注意事項

1. **本番環境での実行禁止**
   - テスト時は必ず`AI_COMPANY_TEST_MODE=1`が設定される
   - Slack通知は自動的に無効化

2. **データの永続化禁止**
   - テストDBは一時的なもの（tmp_path使用）
   - 本番DBへの書き込みは厳禁

3. **外部API呼び出し禁止**
   - Claude APIは必ずモック
   - Slack APIは必ずモック

---

**🧪 このナレッジベースに従って、高品質なテストを維持してください**
