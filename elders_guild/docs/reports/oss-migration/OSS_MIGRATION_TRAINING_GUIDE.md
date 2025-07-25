# 🎓 OSS移行プロジェクト チーム教育ガイド
**Issue #93: OSS移行実装プロジェクト**
**作成日**: 2025年7月19日

## 📚 目次
1. [pytest基本ガイド](#pytest基本ガイド)
2. [Celery/Ray使い分けガイド](#celeryray使い分けガイド)
3. [SonarQube活用ガイド](#sonarqube活用ガイド)
4. [移行実践演習](#移行実践演習)

---

## 🧪 pytest基本ガイド

### 概要
pytestは、Pythonの最も人気のあるテストフレームワークです。シンプルな記法と強力な機能を兼ね備えています。

### 主な特徴
- **自動テスト検出**: `test_`で始まるファイル・関数を自動認識
- **アサーションの簡潔性**: `assert`文のみで記述可能
- **フィクスチャ**: 再利用可能なテストセットアップ
- **パラメータ化**: 同じテストを異なるデータで実行

### 基本的な使い方

#### 1. シンプルなテスト
```python
# test_basic.py
def test_addition():
    assert 1 + 1 == 2

def test_string_contains():
    assert "hello" in "hello world"
```

#### 2. フィクスチャの使用
```python
import pytest

@pytest.fixture
def database():
    # セットアップ
    db = create_test_db()
    yield db
    # ティアダウン
    db.close()

def test_user_creation(database):
    user = database.create_user("test@example.com")
    assert user.email == "test@example.com"
```

#### 3. パラメータ化テスト
```python
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

#### 4. 非同期テスト
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == "success"
```

### pytest-oss.ini設定の理解
```ini
[tool:pytest]
# カバレッジ測定対象
--cov=libs
--cov=workers
# カバレッジ80%未満で失敗
--cov-fail-under=80
# 並列実行（pytest-xdist）
# 使用方法: pytest -n auto
```

### ベストプラクティス
1. **テストの独立性**: 各テストは他のテストに依存しない
2. **明確な命名**: `test_機能名_条件_期待結果`
3. **Given-When-Then**: 準備-実行-検証の構造
4. **フィクスチャスコープ**: session > module > class > function

---

## ⚡ Celery/Ray使い分けガイド

### Celery - 分散タスクキュー

#### 適用場面
- **非同期タスク**: メール送信、画像処理、レポート生成
- **定期タスク**: スケジュール実行（Celery Beat）
- **信頼性重視**: タスクの永続化とリトライ
- **既存システム統合**: Redis/RabbitMQと連携

#### 基本的な使い方
```python
# tasks.py
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def send_email(to, subject, body):
    # メール送信処理
    return f"Email sent to {to}"

# 使用例
result = send_email.delay("user@example.com", "Hello", "Body")
```

#### Flower監視
```bash
# Flower起動（docker-compose.oss.ymlに含まれる）
# ブラウザで http://localhost:5555 にアクセス
```

### Ray - 高性能分散処理

#### 適用場面
- **並列計算**: 機械学習、データ処理
- **低レイテンシ**: ミリ秒単位の処理
- **状態共有**: アクター間でのデータ共有
- **スケーラブル**: 動的なワーカー追加

#### 基本的な使い方
```python
import ray

ray.init()

@ray.remote
def parallel_function(x):
    return x * x

# 並列実行
futures = [parallel_function.remote(i) for i in range(10)]
results = ray.get(futures)
```

### 使い分けの指針

| 要件 | Celery | Ray |
|------|--------|-----|
| タスクの永続性 | ✅ 優秀 | ❌ 限定的 |
| 実行速度 | ⚡ 良好 | ⚡⚡ 高速 |
| スケジューリング | ✅ Celery Beat | ❌ 外部ツール必要 |
| 機械学習 | ⚡ 可能 | ✅ 最適化済み |
| 監視ツール | ✅ Flower | ✅ Ray Dashboard |
| 学習コスト | ⚡ 中程度 | ⚡⚡ やや高い |

---

## 🔍 SonarQube活用ガイド

### 概要
SonarQubeは、コード品質の継続的な検査プラットフォームです。

### 主要メトリクス
1. **バグ**: 潜在的なエラー
2. **脆弱性**: セキュリティリスク
3. **コードスメル**: 保守性の問題
4. **カバレッジ**: テストカバー率
5. **重複**: コードの重複
6. **技術的負債**: 修正にかかる時間

### Docker環境での使用
```bash
# SonarQube起動（docker-compose.oss.ymlで設定済み）
docker-compose -f docker-compose.oss.yml up sonarqube

# ブラウザで http://localhost:9000 にアクセス
# デフォルト: admin/admin
```

### プロジェクト設定
```bash
# sonar-project.properties
sonar.projectKey=elders-guild
sonar.projectName=Elders Guild OSS Migration
sonar.sources=libs,workers
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3.12
```

### CI/CD統合
```yaml
# GitHub Actions例
- name: SonarQube Scan
  uses: SonarSource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
    SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

### 品質ゲート設定
- **新規コード**: カバレッジ80%以上
- **全体**: 技術的負債比率5%未満
- **セキュリティ**: 脆弱性0
- **保守性**: A評価維持

---

## 🎯 移行実践演習

### 演習1: 既存テストのpytest移行

#### Before (unittest)
```python
import unittest

class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_add(self):
        self.assertEqual(self.calc.add(1, 2), 3)
```

#### After (pytest)
```python
import pytest

@pytest.fixture
def calc():
    return Calculator()

def test_add(calc):
    assert calc.add(1, 2) == 3
```

### 演習2: Celeryタスク実装

```python
# tasks.py
from celery import Celery

app = Celery('elders_guild', broker='redis://redis:6379/0')

@app.task(bind=True, max_retries=3)
def process_elder_request(self, request_id):
    try:
        # 処理実行
        result = elder_servant.process(request_id)
        return result
    except Exception as exc:
        # 指数バックオフでリトライ
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### 演習3: テストカバレッジ向上

```bash
# カバレッジ測定
pytest --cov=libs --cov-report=html

# レポート確認
open htmlcov/index.html

# 未カバー行の特定と改善
pytest --cov=libs --cov-report=term-missing
```

### 演習4: Docker環境での統合テスト

```python
# tests/integration/test_with_containers.py
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

def test_elder_servant_with_real_db():
    with PostgresContainer("postgres:15") as postgres:
        db_url = postgres.get_connection_url()
        # 実際のDBでテスト
        servant = ElderServant(db_url=db_url)
        result = servant.process_request(test_request)
        assert result.success
```

---

## 📅 学習スケジュール

### Week 1: pytest基礎
- Day 1-2: 基本構文とフィクスチャ
- Day 3-4: パラメータ化とマーカー
- Day 5: 実践演習

### Week 2: Celery/Ray
- Day 1-2: Celery基礎とFlower
- Day 3-4: Ray基礎とダッシュボード
- Day 5: 使い分け演習

### Week 3: SonarQube
- Day 1-2: メトリクス理解
- Day 3-4: 品質ゲート設定
- Day 5: CI/CD統合

---

## 🔗 参考リソース

### pytest
- [公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [testcontainers-python](https://github.com/testcontainers/testcontainers-python)

### Celery
- [公式ドキュメント](https://docs.celeryproject.org/)
- [Flower監視ツール](https://flower.readthedocs.io/)

### Ray
- [公式ドキュメント](https://docs.ray.io/)
- [Ray Core Walkthrough](https://docs.ray.io/en/latest/ray-core/walkthrough.html)

### SonarQube
- [公式ドキュメント](https://docs.sonarqube.org/)
- [Python Plugin](https://docs.sonarqube.org/latest/analysis/languages/python/)

---

**作成者**: クロードエルダー（Claude Elder）
**承認者**: グランドエルダーmaru
**最終更新**: 2025年7月19日
