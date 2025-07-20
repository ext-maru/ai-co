# 🔄 pytest移行ガイドライン
**Issue #93: OSS移行プロジェクト**
**作成日**: 2025年7月19日

## 📋 移行原則

### 1. 段階的移行アプローチ
- 既存テストと新pytest版を並行運用
- 小さなモジュールから開始
- 動作確認後に既存版を段階的に削除

### 2. 命名規則
- 既存: `test_module.py`
- 移行中: `test_module_pytest.py`
- 完了後: `test_module.py` (既存版を削除)

### 3. ディレクトリ構造
```
tests/
├── legacy/        # 既存テスト（一時保管）
├── unit/          # ユニットテスト
├── integration/   # 統合テスト
├── e2e/          # E2Eテスト
└── conftest.py   # 共通フィクスチャ
```

## 🔧 移行パターン

### Pattern 1: クラスベース → 関数ベース

**Before (unittest style):**
```python
class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.runner = IntegrationTestRunner()

    def test_service_start(self):
        self.assertTrue(self.runner.start_service())
```

**After (pytest style):**
```python
@pytest.fixture
def runner():
    return IntegrationTestRunner()

def test_service_start(runner):
    assert runner.start_service() is True
```

### Pattern 2: 非同期テスト

**Before:**
```python
def test_async_operation(self):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(self.async_func())
    self.assertEqual(result, "expected")
```

**After:**
```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_func()
    assert result == "expected"
```

### Pattern 3: パラメータ化

**Before:**
```python
def test_multiple_inputs(self):
    for input_val in [1, 2, 3]:
        with self.subTest(input=input_val):
            self.assertEqual(func(input_val), input_val * 2)
```

**After:**
```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiple_inputs(input_val, expected):
    assert func(input_val) == expected
```

### Pattern 4: テストコンテナ統合

**Before:**
```python
def setUp(self):
    self.docker = DockerClient()
    self.redis = self.docker.run("redis:7")
    self.wait_for_port(6379)
```

**After:**
```python
@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer() as redis:
        yield redis

def test_with_redis(redis_container):
    client = redis_container.get_client()
    assert client.ping() is True
```

## 📊 移行優先順位

### 高優先度
1. **ユニットテスト** - 依存関係が少ない
2. **独立したモジュール** - 他への影響が最小
3. **頻繁に実行されるテスト** - 高速化の恩恵大

### 中優先度
1. **統合テスト** - Docker統合の恩恵
2. **APIテスト** - フィクスチャの再利用性
3. **データベーステスト** - トランザクション管理

### 低優先度
1. **E2Eテスト** - 複雑な依存関係
2. **レガシー専用テスト** - 廃止予定の機能
3. **特殊な環境依存テスト** - カスタム設定必要

## 🚀 移行手順

### Step 1: 分析
```bash
# テストファイルの複雑度分析
python scripts/analyze_test_complexity.py tests/unit/test_target.py

# 依存関係の確認
grep -r "import" tests/unit/test_target.py
```

### Step 2: 新規作成
```bash
# pytest版の作成
cp tests/unit/test_target.py tests/unit/test_target_pytest.py

# 基本構造の変換
python scripts/convert_to_pytest.py tests/unit/test_target_pytest.py
```

### Step 3: 並行実行
```bash
# 既存版
python -m pytest tests/unit/test_target.py

# pytest版
pytest tests/unit/test_target_pytest.py -v
```

### Step 4: パフォーマンス比較
```bash
# 比較スクリプト実行
python scripts/compare_test_performance.py \
    --old tests/unit/test_target.py \
    --new tests/unit/test_target_pytest.py
```

### Step 5: 移行完了
```bash
# バックアップ
mv tests/unit/test_target.py tests/legacy/

# リネーム
mv tests/unit/test_target_pytest.py tests/unit/test_target.py

# CI/CD更新
git add .github/workflows/tests.yml
```

## 📝 チェックリスト

### 移行前
- [ ] テストカバレッジの記録
- [ ] 実行時間の記録
- [ ] 依存関係の確認
- [ ] 特殊な設定の洗い出し

### 移行中
- [ ] pytestマーカーの適用
- [ ] フィクスチャの作成
- [ ] アサーションの変換
- [ ] 並行実行の確認

### 移行後
- [ ] カバレッジ維持/向上
- [ ] 実行時間の改善確認
- [ ] CI/CDの更新
- [ ] ドキュメント更新

## 🔍 トラブルシューティング

### よくある問題

1. **インポートエラー**
```python
# conftest.pyに追加
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
```

2. **フィクスチャスコープ**
```python
# セッションスコープで共有
@pytest.fixture(scope="session")
def expensive_resource():
    return create_resource()
```

3. **非同期テストのタイムアウト**
```python
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_long_running():
    await long_operation()
```

## 📚 参考リソース

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [testcontainers-python](https://github.com/testcontainers/testcontainers-python)
- [OSS_MIGRATION_TRAINING_GUIDE.md](./OSS_MIGRATION_TRAINING_GUIDE.md)

---

**作成者**: クロードエルダー（Claude Elder）
**承認者**: グランドエルダーmaru
**最終更新**: 2025年7月19日
