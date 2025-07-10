# 🧪 TDD実行チェックリスト

## 📋 Phase 1: models.py修正

### Red段階（失敗確認）
- [ ] test_models.pyが失敗することを確認
- [ ] 具体的なエラー内容を記録

### Green段階（最小実装）
- [ ] server_default=func.now()を追加
- [ ] __repr__メソッドを実装
- [ ] 銀行明細表示名を修正
- [ ] テストがPASSすることを確認

### Refactor段階（改善）
- [ ] コードの可読性向上
- [ ] 重複の除去
- [ ] 型ヒントの追加

## 📋 Phase 2: google_drive_service.py修正

### Red段階
- [ ] test_google_drive_service.pyが失敗することを確認

### Green段階
- [ ] MediaFileUploadインポート追加
- [ ] create_folderメソッド実装
- [ ] upload_fileメソッド実装

### Refactor段階
- [ ] エラーハンドリング改善
- [ ] ドキュメント追加

## 📋 Phase 3: app.py修正

### Red段階
- [ ] 関連テストが失敗することを確認

### Green段階
- [ ] EXIF処理を新APIに更新
- [ ] review_imageの404処理追加

### Refactor段階
- [ ] コード整理

## 📋 Phase 4: conftest.py修正

### 実装
- [ ] reset_google_drive_singletonフィクスチャ追加

## 📊 最終確認
- [ ] 全テストがPASS（64/64）
- [ ] カバレッジ67%以上
- [ ] 新規失敗ゼロ
- [ ] 4賢者への報告完了