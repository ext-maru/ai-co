---
audience: developers
author: claude-elder
category: guides
dependencies: []
description: No description available
difficulty: beginner
last_updated: '2025-07-23'
related_docs: []
reviewers: []
status: approved
subcategory: user-guides
tags:
- tdd
- testing
- python
- guides
title: 🧪 Claude CLI TDD完全ガイド - Elders Guild統一標準
version: 1.0.0
---

# 🧪 Claude CLI TDD完全ガイド - Elders Guild統一標準

**エルダー評議会令第401号 - TDD完全ガイド制定**  
**制定日**: 2025年7月22日  
**統合元**: CLAUDE_TDD_GUIDE.md, TDD_WITH_CLAUDE_CLI.md, TDD_WORKFLOW.md, TEST_PATTERNS_AND_BEST_PRACTICES.md

## 🎯 概要

このガイドは、Claude CLIを使用してElders Guild内で開発を行う際のTDD（テスト駆動開発）実践方法を定めた公式統一ガイドラインです。

### ⚠️ **絶対必須ルール**
- **すべての新規開発はTDDで行うことを必須とします**
- **テストなしでコードを書くことは絶対禁止**
- **Red→Green→Refactorサイクルの厳守**

---

## 🔴🟢🔵 TDD基本原則

### **TDDサイクル（Iron Will）**
1. **🔴 Red**: 失敗するテストを先に書く
2. **🟢 Green**: 最小限の実装でテストを通す  
3. **🔵 Refactor**: コードを改善する
4. **📤 Push**: GitHub Flowに従いコミット＆プッシュ

### **鉄則**
- ❌ **絶対にNG**: テストなしでコードを書く
- ✅ **必須**: テストが失敗することを確認してから実装
- 🔄 **継続**: Red→Green→Refactorサイクルを維持

---

## 📋 Claude CLIへの依頼方法

### **1. 基本的な依頼フォーマット**

```bash
ai-send "[機能名]をTDDで開発:
1. 機能要件: [具体的な要件]
2. 必要なテストケース:
   - 正常系: [期待される動作]
   - 異常系: [エラーケース]
   - 境界値: [エッジケース]
3. まずtest_*.pyを作成してテストが失敗することを確認
4. 最小限の実装でテストを通す
5. リファクタリングで品質向上"
```

### **2. 専用コマンド群**

```bash
# 新機能開発（TDD）
ai-tdd new EmailValidator "メールアドレスの形式を検証する機能"

# 既存コードへのテスト追加
ai-tdd test libs/data_processor.py

# カバレッジ改善
ai-tdd coverage workers

# 対話型TDD開発
ai-tdd session "CSV処理機能の設計と実装"

# TDDワークフロー開始
./scripts/tdd-new-feature.sh my_feature
```

---

## 🤖 Claude CLI特化TDD実践

### **1. Claude CLIでのTDDサイクル**

#### **🔴 Red Phase（失敗するテストを書く）**
```bash
# Claude CLIにTDDでの開発を依頼
ai-send "新しいデータ集計ワーカーをTDDで開発してください。まずテストから書いて、Red-Green-Refactorサイクルで実装してください"

# より具体的な依頼
ai-send "CSVファイルを読み込んで集計するDataAggregatorWorkerをTDDで作成。以下の要件で：
1. CSVファイルのパスを受け取る
2. 指定されたカラムの合計を計算
3. 結果をJSONで返す
まずtest_data_aggregator_worker.pyから作成してください"
```

```python
# Claude CLIが最初に生成するテスト例
def test_should_aggregate_csv_data():
    \"\"\"CSVデータを正しく集計できることを確認\"\"\"
    # Arrange
    aggregator = DataAggregatorWorker()
    csv_path = "test_data.csv"
    column_name = "amount"
    
    # Act
    result = aggregator.aggregate(csv_path, column_name)
    
    # Assert
    assert result["total"] == 150.0
    assert result["count"] == 3
```

#### **🟢 Green Phase（テストを通す最小限のコード）**
```python
# 最小限の実装例
class DataAggregatorWorker:
    def aggregate(self, csv_path, column_name):
        return {"total": 150.0, "count": 3}  # ハードコードでテストを通す
```

#### **🔵 Refactor Phase（コードを改善する）**
```python
# リファクタリング後の実装
class DataAggregatorWorker:
    def aggregate(self, csv_path, column_name):
        import pandas as pd
        df = pd.read_csv(csv_path)
        total = df[column_name].sum()
        count = len(df)
        return {"total": float(total), "count": count}
```

### **2. テスト実行とフィードバック**
```bash
# テストを実行（失敗することを確認）
pytest tests/unit/test_my_feature.py -v

# カバレッジレポート
ai-test-coverage --html

# Claude CLIへのフィードバック
ai-send "テストが以下のエラーで失敗しました: [エラー内容]
次のステップでGreenフェーズの実装をお願いします"
```

---

## 📝 良い依頼例と悪い依頼例

### ✅ **良い依頼例**
```bash
# 明確なテストケースを含む依頼
ai-send "UserManagerをTDDで作成:
1. 機能: ユーザーの作成・取得・削除
2. テストケース:
   - 正常系: 新規ユーザー作成成功、既存ユーザー取得成功
   - 異常系: 重複メール拒否、存在しないユーザー取得時None返却
   - 境界値: 空文字列、None値の処理
3. まずtest_user_manager.pyを作成し、Redフェーズから開始"

# 段階的な依頼
ai-send "Step 1: UserManagerのテストファイルを作成（すべて失敗するテスト）
Step 2: 最小限の実装でテストを通す  
Step 3: リファクタリングで品質向上"
```

### ❌ **悪い依頼例**
```bash
# テストなしの実装依頼
ai-send "UserManagerクラスを作成してください"

# 曖昧な要件
ai-send "何かユーザー管理的なものを作ってください"

# テストを後回しにする依頼
ai-send "まずUserManagerを実装して、後でテストを書いてください"
```

---

## 🧪 確立されたテストパターン集

### **1. 完全モック化パターン**

#### **1.1 RabbitMQ モックパターン**
```python
from unittest.mock import Mock, patch, MagicMock

class MockChannel:
    def __init__(self):
        self.queue_declare = Mock()
        self.basic_consume = Mock()
        self.basic_publish = Mock()
        self.start_consuming = Mock()
        self.stop_consuming = Mock()
        self.close = Mock()

class MockConnection:
    def __init__(self):
        self.channel = Mock(return_value=MockChannel())
        self.close = Mock()
        self.is_closed = False

@pytest.fixture
def mock_rabbitmq():
    with patch('pika.BlockingConnection', return_value=MockConnection()):
        yield
```

#### **1.2 データベースモックパターン**
```python
@pytest.fixture
def mock_database():
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        yield mock_cursor
```

#### **1.3 外部APIモックパターン**
```python
@pytest.fixture
def mock_api_client():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        yield mock_get
```

### **2. テストデータ管理パターン**

#### **2.1 ファクトリーパターン**
```python
class TestDataFactory:
    @staticmethod
    def create_user(name="Test User", email="test@example.com"):
        return {
            "name": name,
            "email": email,
            "id": random.randint(1, 1000)
        }
    
    @staticmethod
    def create_task(title="Test Task", status="pending"):
        return {
            "title": title,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
```

#### **2.2 フィクスチャパターン**
```python
@pytest.fixture
def sample_csv_data():
    return """name,age,city
John,25,Tokyo
Jane,30,Osaka
Bob,35,Kyoto"""

@pytest.fixture
def temp_csv_file(sample_csv_data):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_data)
        f.flush()
        yield f.name
    os.unlink(f.name)
```

### **3. 非同期テストパターン**

#### **3.1 AsyncWorkerテストパターン**
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_worker_processing():
    worker = AsyncWorker()
    
    # 非同期処理のテスト
    result = await worker.process_async("test_data")
    
    assert result is not None
    assert result["status"] == "completed"
```

#### **3.2 コルーチンモックパターン**
```python
@pytest.fixture
def mock_async_client():
    async def mock_async_method(*args, **kwargs):
        return {"result": "mocked"}
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.json = mock_async_method
        yield mock_get
```

---

## 🔧 Elders Guild特化TDDワークフロー

### **1. プロジェクト構造**
```
project/
├── libs/                      # 実装コード
│   └── my_feature.py
├── tests/                     # テストコード
│   ├── unit/                 # ユニットテスト
│   │   └── test_my_feature.py
│   └── integration/          # 統合テスト
│       └── test_my_feature_integration.py
└── scripts/
    └── tdd-new-feature.sh    # TDD開始スクリプト
```

### **2. 標準テストファイル命名規則**
- **実装ファイル**: `libs/feature_name.py`
- **テストファイル**: `tests/unit/test_feature_name.py`
- **統合テスト**: `tests/integration/test_feature_name_integration.py`

### **3. テスト実行コマンド**
```bash
# 単一テスト実行
pytest tests/unit/test_my_feature.py -v

# 全テスト実行
pytest tests/ -v

# カバレッジ付き実行
pytest tests/ --cov=libs --cov-report=html

# TDD用ウォッチモード
pytest-watch tests/unit/test_my_feature.py
```

---

## 📊 品質基準

### **最低テストカバレッジ要件**
| コンポーネント | 最小 | 目標 |
|-------------|-----|-----|
| 新規コード | 90% | 95% |
| Core機能 | 90% | 100% |
| Workers | 80% | 95% |
| Libs | 95% | 100% |

### **テスト品質チェックポイント**
- ✅ **独立性**: 各テストは他のテストに依存しない
- ✅ **再現性**: 何度実行しても同じ結果
- ✅ **高速性**: 1秒以内で実行完了
- ✅ **可読性**: テスト意図が明確
- ✅ **保守性**: 実装変更時の修正が最小限

---

## 🚨 よくある問題と解決策

### **問題1: テストが不安定**
```python
# ❌ 悪い例：時間依存テスト
def test_timestamp():
    result = generate_timestamp()
    assert result == "2025-07-22 10:00:00"  # 時刻に依存

# ✅ 良い例：モック使用
@patch('datetime.datetime')
def test_timestamp(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 7, 22, 10, 0, 0)
    result = generate_timestamp()
    assert result == "2025-07-22 10:00:00"
```

### **問題2: テストが遅い**
```python
# ❌ 悪い例：実際のファイルI/O
def test_file_processing():
    with open("large_file.csv", "r") as f:  # 遅い
        result = process_file(f)

# ✅ 良い例：StringIOを使用
def test_file_processing():
    from io import StringIO
    fake_file = StringIO("col1,col2\nval1,val2")
    result = process_file(fake_file)
```

### **問題3: モックが複雑**
```python
# ❌ 悪い例：過度なモック
@patch('module.ClassA')
@patch('module.ClassB')
@patch('module.ClassC')
def test_complex_interaction(mock_c, mock_b, mock_a):
    # 複雑すぎる

# ✅ 良い例：依存注入でシンプル化
def test_complex_interaction():
    mock_dependency = Mock()
    service = Service(dependency=mock_dependency)
    result = service.process()
    mock_dependency.method.assert_called_once()
```

---

## 📚 参考資料とコマンド

### **関連ドキュメント**
- [XP開発ガイド](XP_DEVELOPMENT_GUIDE.md)
- [エルダーサーバント役割定義](../../../docs/technical/ELDER_TREE_SERVANTS_ROLE_DEFINITION.md)
- [品質システム](../../../docs/ELDERS_GUILD_QUALITY_SYSTEM.md)

### **実用コマンド集**
```bash
# TDD開発フロー
ai-tdd new FeatureName "機能説明"        # 新機能TDD開始
ai-tdd test existing_file.py            # 既存コードテスト化
ai-tdd coverage module_name              # カバレッジ向上
ai-tdd session "対話型開発セッション"      # 対話型TDD

# テスト実行・管理
pytest tests/ -v --tb=short              # 詳細テスト実行
pytest-watch tests/unit/                 # ウォッチモード
ai-test-coverage --html                  # カバレッジレポート
ai-test-coverage --missing               # 未テスト箇所表示
```

---

**Remember**: No Code Without Test! 🧪  
**Iron Will**: Test First, Always! ⚡  
**Elders Legacy**: Quality Through Testing! 🏛️

---
**エルダーズギルド開発実行責任者**  
**クロードエルダー（Claude Elder）**

**最終更新**: 2025年7月22日  
**統合完了**: TDD関連4ファイル統合完了