# 📚 Week 2: チーム教育プログラム - OSS統合研修

**期間**: 2025年7月19日 - 7月26日（Week 2）
**対象**: エルダーズギルド開発チーム全員
**責任者**: クロードエルダー（Claude Elder）

## 🎯 教育目標

### 主要目標
1. **pytest基礎**: 現行テストフレームワークから移行準備
2. **Celery/Redis**: 非同期ワーカーシステム理解
3. **SonarQube**: コード品質管理の実践的操作
4. **品質フロー**: pre-commit → CI/CD統合理解

### 成功指標
- [ ] 全員がpytestでテスト作成可能
- [ ] Celeryタスクの基本操作習得
- [ ] SonarQube UI操作とメトリクス理解
- [ ] 品質ゲートの概念理解

## 📅 5日間研修スケジュール

### Day 1 (月): pytest基礎
**時間**: 10:00-12:00 (2時間)
**対象**: 全開発者

#### 🧪 pytest実習プログラム
```python
# 実習1: 基本テストの書き方
def test_basic_assertion():
    """基本的なアサーション"""
    assert 2 + 2 == 4
    assert "hello" in "hello world"

# 実習2: フィクスチャの使用
@pytest.fixture
def sample_data():
    return {"name": "エルダー", "level": 99}

def test_with_fixture(sample_data):
    assert sample_data["name"] == "エルダー"

# 実習3: パラメータ化テスト
@pytest.mark.parametrize("input,expected", [
    (2, 4), (3, 9), (4, 16)
])
def test_square(input, expected):
    assert input ** 2 == expected
```

#### 実習内容
1. **基本構文**: assert文、テスト関数命名規則
2. **フィクスチャ**: setup/teardown、データ準備
3. **マーク**: @pytest.mark.integration、@pytest.mark.slow
4. **実行オプション**: -v, -s, --tb=short

### Day 2 (火): Celery/Redis基礎
**時間**: 10:00-13:00 (3時間)
**対象**: バックエンド開発者

#### 🔄 Celery実習プログラム
```python
# 実習1: 基本的なタスク定義
from celery import Celery

app = Celery('elders_guild', broker='redis://localhost:6379')

@app.task
def add_numbers(x, y):
    """数値加算タスク"""
    return x + y

@app.task
def process_elder_data(elder_id):
    """エルダーデータ処理（重い処理のシミュレーション）"""
    import time
    time.sleep(2)  # 重い処理をシミュレート
    return f"Elder {elder_id} processed"

# 実習2: タスクの実行
result = add_numbers.delay(4, 4)
print(result.get())  # 8

# 実習3: 結果の取得とモニタリング
task_result = process_elder_data.delay("elder_001")
print(f"Task ID: {task_result.id}")
print(f"Status: {task_result.status}")
print(f"Result: {task_result.get(timeout=10)}")
```

#### 実習内容
1. **基本概念**: タスクキュー、ワーカー、ブローカー
2. **タスク定義**: @app.task デコレータ
3. **非同期実行**: .delay(), .apply_async()
4. **結果取得**: .get(), .ready(), .status
5. **監視**: Flower dashboard

### Day 3 (水): SonarQube UI操作
**時間**: 10:00-11:30 (1.5時間)
**対象**: 全員

#### 🔍 SonarQube実習
1. **ダッシュボード操作**
   - http://localhost:9000 にアクセス
   - プロジェクト一覧の確認
   - メトリクス読み方

2. **品質ゲート理解**
   - Coverage, Bugs, Vulnerabilities
   - Code Smells, Duplications
   - Technical Debt計算

3. **問題解決フロー**
   - Issues画面の使い方
   - ホットスポット特定
   - 優先度判断基準

#### 実習課題
```bash
# 課題1: プロジェクト分析実行
# curl -X POST -u admin:admin "http://localhost:9000/api/projects/create?project=team-training&name=Team%20Training"

# 課題2: 品質プロファイル確認
# Configuration > Quality Profiles > Python

# 課題3: ルール設定
# Rules > Language: Python > Quality Profile: Sonar way
```

### Day 4 (木): pre-commit実践
**時間**: 10:00-11:00 (1時間)
**対象**: 全開発者

#### 🧹 品質チェック実習
```bash
# 実習1: pre-commitフック体験
echo "def bad_function( ):" > test_quality.py
echo "    print('test')" >> test_quality.py
git add test_quality.py
git commit -m "test commit"  # フックが自動実行される

# 実習2: 手動品質チェック
pre-commit run --all-files

# 実習3: 個別ツール実行
black test_quality.py
flake8 test_quality.py
bandit test_quality.py
mypy test_quality.py
```

#### 学習内容
1. **自動品質チェック**: コミット時の自動実行
2. **各ツールの役割**: Black, Flake8, Bandit, Mypy
3. **修正方法**: 自動修正 vs 手動修正
4. **品質基準**: エルダーズギルド品質規約

### Day 5 (金): 統合演習
**時間**: 10:00-12:00 (2時間)
**対象**: 全員

#### 🚀 総合実習プロジェクト
**課題**: "Elder Data Processor" の実装

```python
# elder_processor.py - 実習課題
from celery import Celery
import pytest
import redis

class ElderDataProcessor:
    """エルダーデータ処理システム"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def process_elder(self, elder_id: str, data: dict) -> dict:
        """エルダーデータの処理"""
        # 実装課題1: データ検証
        if not elder_id or not data:
            raise ValueError("Invalid input")

        # 実装課題2: Redis保存
        self.redis.set(f"elder:{elder_id}", str(data))

        # 実装課題3: 処理結果返却
        return {
            "elder_id": elder_id,
            "status": "processed",
            "data_size": len(str(data))
        }

# test_elder_processor.py - テスト課題
@pytest.fixture
def redis_client():
    """テスト用Redisクライアント"""
    return redis.Redis(host='localhost', port=6379, db=1)

@pytest.fixture
def processor(redis_client):
    """プロセッサインスタンス"""
    return ElderDataProcessor(redis_client)

def test_process_elder_success(processor):
    """正常処理テスト"""
    result = processor.process_elder("elder_001", {"name": "テストエルダー"})
    assert result["status"] == "processed"
    assert result["elder_id"] == "elder_001"

@pytest.mark.parametrize("elder_id,data", [
    ("", {"name": "test"}),
    ("elder_001", {}),
    (None, {"name": "test"})
])
def test_process_elder_validation(processor, elder_id, data):
    """バリデーションテスト"""
    with pytest.raises(ValueError):
        processor.process_elder(elder_id, data)

# tasks.py - Celery課題
@app.task
def async_process_elder(elder_id: str, data: dict):
    """非同期エルダー処理タスク"""
    processor = ElderDataProcessor(redis.Redis())
    return processor.process_elder(elder_id, data)
```

#### 実習チェックリスト
- [ ] pytestテストが全て合格
- [ ] pre-commitフックが正常動作
- [ ] Celeryタスクが正常実行
- [ ] SonarQube分析でGreen判定

## 📋 評価基準

### 個人評価 (各日終了時)
| 項目 | 基準 | 配点 |
|------|------|------|
| 実習課題完了 | 全課題クリア | 25点 |
| 質疑応答 | 積極的参加 | 15点 |
| 理解度 | 概念説明可能 | 10点 |

### チーム評価 (Week 2終了時)
- [ ] 統合実習プロジェクト完了
- [ ] 品質基準クリア (SonarQube Green)
- [ ] 全メンバー基礎スキル習得

## 🛠️ 準備物・環境

### 事前準備
- [ ] Docker環境稼働確認 (Week 1完了済み)
- [ ] 実習用リポジトリ準備
- [ ] SonarQubeプロジェクト作成
- [ ] 教育資料配布

### 必要ツール
```bash
# 動作確認コマンド
python3 test_oss_stack.py  # 全サービス正常確認
pytest --version          # v8.4.1
celery --version          # v5.5.3
pre-commit --version      # 利用可能確認
```

## 📚 参考資料

### 公式ドキュメント
- [pytest Documentation](https://docs.pytest.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SonarQube Documentation](https://docs.sonarqube.org/)

### エルダーズギルド内部資料
- `docs/OSS_SELECTION_GUIDELINES.md` - OSS選定基準
- `libs/pytest_integration_poc.py` - pytest実装例
- `libs/celery_migration_poc.py` - Celery実装例

## 🚀 Week 3への準備

### Week 2終了時の到達目標
1. **技術スキル**: 3つのOSSツール基本操作習得
2. **品質意識**: 自動品質チェックの習慣化
3. **実装準備**: pytest移行作業への準備完了

### Week 3移行作業準備
- [ ] 移行対象ファイル特定: `libs/integration_test_framework.py`
- [ ] 既存テストケース棚卸し
- [ ] pytest形式変換計画策定

---

## ✅ 実施確認

**Week 2教育プログラム準備完了**
- 5日間カリキュラム策定済み
- 実習環境準備完了
- 評価基準設定済み

**次のアクション**: Day 1 pytest基礎研修実施開始

---

**作成者**: クロードエルダー（Claude Elder）
**承認**: エルダー評議会
