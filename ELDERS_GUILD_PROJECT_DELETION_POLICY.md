# 🏛️ エルダーズギルド プロジェクト削除ポリシー

## 📋 削除ポリシー概要

エルダーズギルドでは、プロジェクトの安全な削除のため、**7日間の保護期間**を設けています。

## 🗂️ 削除待機フォルダ

### フォルダ構成
```
/home/aicompany/ai_co/projects_to_delete/
├── YYYY-MM-DD_プロジェクト名/  # 削除予定日_プロジェクト名
├── deletion_schedule.json       # 削除スケジュール管理
└── README.md                   # 削除ポリシー説明
```

## 📅 削除プロセス

### 1. **削除申請** (Day 0)
- プロジェクトを `projects_to_delete/` に移動
- フォルダ名: `YYYY-MM-DD_プロジェクト名` (7日後の日付)
- `deletion_schedule.json` に記録

### 2. **保護期間** (Day 1-6)
- 7日間の復旧可能期間
- インシデント賢者による監視
- 必要に応じて復旧可能

### 3. **自動削除** (Day 7)
- スケジュールに従い自動削除
- 削除ログを記録
- ナレッジ賢者に通知

## 🔄 復旧手順

```bash
# プロジェクトの復旧
mv projects_to_delete/YYYY-MM-DD_プロジェクト名 projects/プロジェクト名

# スケジュールから削除
python3 scripts/remove_from_deletion_schedule.py プロジェクト名
```

## 🤖 自動削除スクリプト

```bash
# 毎日0時に実行
0 0 * * * /home/aicompany/ai_co/scripts/elders_project_cleanup.py
```

## 📊 削除スケジュール管理

### deletion_schedule.json
```json
{
  "projects": [
    {
      "name": "upload-image-service",
      "moved_date": "2025-01-11",
      "deletion_date": "2025-01-18",
      "reason": "契約書類アップロードシステムと重複",
      "requested_by": "クロードエルダー"
    }
  ]
}
```

## ⚠️ 注意事項

1. **バックアップ確認**: 削除前に必ずバックアップ作成
2. **依存関係確認**: 他プロジェクトからの参照を確認
3. **本番環境確認**: 本番で稼働していないことを確認
4. **通知**: チームメンバーへの事前通知

## 🛡️ セーフティネット

- **インシデント賢者**: 異常な削除を検知・防止
- **ナレッジ賢者**: 削除履歴を永続保存
- **タスク賢者**: 削除スケジュール管理
- **RAG賢者**: 削除影響の事前分析

## 📝 削除ログ

すべての削除は以下に記録：
- `/home/aicompany/ai_co/logs/project_deletions.log`
- ナレッジベース: `knowledge_base/project_lifecycle/deletions/`

---
**制定日**: 2025年1月11日  
**承認**: エルダーズギルド評議会  
**管理**: インシデント賢者