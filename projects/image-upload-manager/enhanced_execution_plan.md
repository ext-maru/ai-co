# 🏛️ ナレッジ賢者の魔法書を踏まえた強化実行計画

## 📅 計画更新日時
2025年7月10日 03:15

## 📜 魔法書からの重要事項
- TDDサイクル（Red→Green→Refactor）の厳守
- 失敗学習プロトコル（FAIL-LEARN-EVOLVE）の適用
- 🛡️ インシデント騎士団向け討伐任務として分類

## 🎯 強化実行計画

### Phase 0: 魔法書確認と環境準備（5分）
```bash
# TDDチェックリスト作成
cat > tdd_checklist.md << EOF
□ 失敗するテストを先に書いた
□ テストが失敗することを確認した
□ 最小限の実装でテストを通した
□ すべてのテストが通ることを確認した
□ リファクタリングを実施した
□ カバレッジが67%以上を維持
□ 4賢者への相談記録を残した
EOF

# 環境準備
pip install pytest-mock==3.14.0 --break-system-packages

# 現状記録（魔法書推奨）
python3 -m pytest tests/ -v > test_results_before_$(date +%Y%m%d_%H%M%S).txt
git stash save "テスト修正前の状態保存"
```

### Phase 1: 基盤修正（15分）- 並列実行 🛡️

#### タスク1: models.py修正【インシデント騎士2名配置】
```python
# TDDサイクル適用
# 1. Red: テストが失敗することを確認
python3 -m pytest tests/unit/test_models.py -v

# 2. Green: 最小限の修正
# - server_default=func.now()追加
# - __repr__メソッド実装
# - 銀行明細表示名修正

# 3. Refactor: コード品質向上
```

#### タスク2: conftest.py修正【エルフ1名配置】
```python
# 魔法書推奨: シングルトンリセット
@pytest.fixture(autouse=True)
def reset_google_drive_singleton():
    """Google Driveサービスのシングルトンをリセット"""
    from google_drive_service import GoogleDriveService
    if hasattr(GoogleDriveService, '_instance'):
        delattr(GoogleDriveService, '_instance')
```

#### タスク3: google_drive_service.py修正【ドワーフ工房3名配置】
```python
# 魔法書警告: MediaFileUploadインポートは必須
from googleapiclient.http import MediaFileUpload

# メソッド実装（伝説装備鍛造レベル）
def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None)
def upload_file(self, file_path: str, filename: str, folder_id: Optional[str] = None)
```

### Phase 2: 依存修正（10分）- 逐次実行

#### タスク4: app.py修正【RAGウィザード2名配置】
```python
# 魔法書注意: EXIF処理は最新APIを使用
try:
    exif = img.getexif()  # 新API
    # 旧API: img._getexif() は使用禁止
except:
    pass
```

### Phase 3: 品質検証（10分）

#### 3.1 段階的テスト実行（魔法書推奨）
```bash
# 個別テスト実行
python3 -m pytest tests/unit/test_models.py -v
python3 -m pytest tests/unit/test_google_drive_service.py -v
python3 -m pytest tests/unit/test_app_routes.py -v

# 統合テスト実行
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```

#### 3.2 成功基準確認（強化版）
- ✅ 19個の失敗テストがすべてPASS
- ✅ カバレッジ67%以上（目標70%）
- ✅ 新規失敗ゼロ
- ✅ TDDチェックリスト全項目クリア
- ✅ pre-commitチェックパス

### Phase 4: 失敗学習プロトコル適用（随時）

```bash
# エラー発生時の即時対応
if [ $? -ne 0 ]; then
    echo "🚨 エラー検知 - 失敗学習プロトコル発動"
    
    # Phase 1: 即座に作業停止
    git stash
    
    # Phase 2: 4賢者相談（5分以内）
    ai-incident-report --severity high --type test_failure
    
    # Phase 3: 知識記録
    cat > knowledge_base/failures/test_fix_$(date +%Y%m%d_%H%M%S).md << EOF
    ## 失敗内容
    [詳細記録]
    
    ## 原因分析
    [4賢者による分析]
    
    ## 解決策
    [実施した対策]
    
    ## 学習事項
    [今後の改善点]
    EOF
fi
```

## 🏆 タスク完了後の評議会報告

### 報告内容（魔法書テンプレート）
```markdown
# インシデント騎士団 討伐任務完了報告

## 任務概要
- 任務種別: テスト失敗バグ討伐（MEDIUM～HIGH）
- 討伐対象: 19体のテスト失敗モンスター
- 参加者: インシデント騎士、エルフ、ドワーフ、RAGウィザード

## 戦果
- 討伐成功数: X/19
- カバレッジ: XX%
- 新規発生: 0

## 使用した魔法・技術
- TDDサイクル魔法
- 並列処理エルフ術
- ドワーフ鍛造技術

## 獲得した知識
[ナレッジベースへの追加内容]
```

## 🎯 実行コマンド（強化版）

```bash
# 魔法書チェック付き実行
ai-task-elder-execute \
  --plan ./enhanced_execution_plan.md \
  --tdd-check \
  --fail-learn-protocol \
  --parallel \
  --monitor

# インシデント騎士団モード
ai-incident-knights \
  --quest subjugation \
  --target test_failures \
  --count 19
```

---
計画策定：クロードエルダー
魔法書監修：ナレッジ賢者
承認：エルダーズギルド4賢者評議会