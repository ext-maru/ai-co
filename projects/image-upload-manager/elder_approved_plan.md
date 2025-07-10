# 🏛️ エルダーズギルド承認済み実行計画

## 📅 承認日時
2025年7月10日 03:10

## ✅ 承認者
エルダーズギルド4賢者評議会

## 📋 承認済み実行計画

### Phase 0: 環境準備（5分）
**目的**: テスト修正の前提条件を整える

1. **pytest-mockインストール**
   ```bash
   pip install pytest-mock==3.14.0 --break-system-packages
   ```

2. **現状記録**
   ```bash
   # 現在のテスト結果を保存
   python3 -m pytest tests/ -v > test_results_before.txt
   
   # 重要ファイルのバックアップ
   cp app/models.py app/models.py.bak
   cp app/google_drive_service.py app/google_drive_service.py.bak
   ```

3. **テストDB初期化**
   ```bash
   rm -f instance/test_*.db
   ```

### Phase 1: 基盤修正（15分）- 並列実行

#### タスク1: models.py修正（エルフ2名配置）
- server_default=func.now()追加
- __repr__メソッド実装
- 表示名修正（銀行明細）

#### タスク2: conftest.py修正（エルフ1名配置）
- reset_google_drive_singletonフィクスチャ追加
- autouseで自動適用

#### タスク3: google_drive_service.py修正（エルフ3名配置）
- MediaFileUploadインポート追加
- create_folderメソッド実装
- upload_fileメソッド実装

### Phase 2: 依存修正（10分）

#### タスク4: app.py修正（エルフ2名配置）
**依存**: models.py修正完了
- EXIF処理を新APIに更新
- review_imageの404処理追加

### Phase 3: 検証（5分）

1. **統合テスト実行**
   ```bash
   python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
   ```

2. **成功基準確認**
   - ✅ 19個の失敗テストがすべてPASS
   - ✅ カバレッジ67%以上（目標70%）
   - ✅ 新規失敗ゼロ

## 🚨 リスク対策

### 監視ポイント
1. **データベース互換性**
   - server_default追加による既存DBへの影響
   - 必要に応じてマイグレーション作成

2. **モック設定**
   - 過度なモッキングを避ける
   - 実装詳細への結合を防ぐ

3. **EXIF処理**
   - 新旧API差分による画像処理の違い
   - テスト画像での動作確認

### ロールバック計画
```bash
# 問題発生時の即時復旧
git stash
cp app/models.py.bak app/models.py
cp app/google_drive_service.py.bak app/google_drive_service.py
```

## 📊 進捗報告スケジュール

- **03:15** - Phase 0完了報告
- **03:30** - Phase 1完了報告（部分テスト結果含む）
- **03:40** - Phase 2完了報告
- **03:45** - 最終結果報告

## 🎯 タスクエルダー実行コマンド

```bash
# 承認済み計画でタスクエルダーに委任
ai-task-elder-execute --plan ./elder_approved_plan.md --parallel --monitor

# エルフ最適化
ai-elf-optimize --batch test_fix_batch_20250710 --approved

# リアルタイム監視
ai-task-monitor --batch test_fix_batch_20250710 --real-time
```

---
承認：エルダーズギルド4賢者評議会
実行責任者：クロードエルダー