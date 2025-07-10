# ナレッジベース更新トリガー定義

最終更新: 2025-01-06

## 概要
Elders Guildシステムのナレッジベース自動更新をトリガーするイベントと更新方法を定義します。

## 自動更新トリガー

### 🚨 即座更新（Critical）
以下のイベント発生時、即座にナレッジベースを更新：

1. **新ワーカー追加**
   - ファイル: `workers/`配下の新規.pyファイル
   - 更新対象: `FEATURE_TREE.md`, `component_catalog.md`, `system_architecture.md`

2. **新AIコマンド追加**
   - ファイル: `commands/`配下の新規ファイル
   - 更新対象: `FEATURE_TREE.md`, `component_catalog.md`

3. **新ライブラリ追加**
   - ファイル: `libs/`配下の新規.pyファイル
   - 更新対象: `FEATURE_TREE.md`, `component_catalog.md`

4. **Core基盤変更**
   - ファイル: `core/base_worker.py`, `core/base_manager.py`
   - 更新対象: 全ナレッジファイル

### ⏰ 定期更新（Scheduled）

#### 毎日午前3時
- ナレッジ統合（`ai-knowledge consolidate`）
- 機能ツリー検証と更新
- 無効リンクのチェック

#### 6時間ごと
- 進化追跡（`ai-knowledge evolve`）
- 変更点の検出と記録

#### 毎週月曜9時
- 週次レポート生成
- ドキュメント間の整合性チェック

#### 毎月1日
- 月次アーカイブ作成
- バージョン番号更新

### 🔄 イベント駆動更新（Event-Driven）

1. **Git操作時**
   - `git add`/`commit`/`push`後
   - 変更ファイルに基づく選択的更新

2. **システム起動時**
   - `ai-start`実行時
   - 基本的な整合性チェック

3. **手動実行時**
   - `ai-knowledge`コマンド実行
   - `ai-send`で"ナレッジ更新"タスク送信時

## 更新対象とトリガーマップ

| トリガーイベント | FEATURE_TREE.md | component_catalog.md | system_architecture.md | API_specifications.md | data_structures.md | MASTER_KB.md |
|----------------|-----------------|---------------------|----------------------|---------------------|-------------------|--------------|
| 新ワーカー追加    | ✅ | ✅ | ✅ | ⚪ | ⚪ | ✅ |
| 新AIコマンド追加  | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ✅ |
| 新ライブラリ追加  | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ✅ |
| API仕様変更     | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ✅ |
| データ構造変更   | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ |
| 設定変更        | ⚪ | ⚪ | ✅ | ✅ | ⚪ | ✅ |

凡例: ✅必須更新 ⚪オプション更新

## 自動更新の実装方法

### 1. ファイル監視による更新
```bash
# inotifywait を使用したファイル監視
inotifywait -m -r -e create,modify,delete \
  /home/aicompany/ai_co/workers/ \
  /home/aicompany/ai_co/commands/ \
  /home/aicompany/ai_co/libs/ \
  --format '%w%f %e' | while read file event; do
    echo "$(date): $file $event" >> /tmp/knowledge_update.log
    /home/aicompany/ai_co/scripts/update_knowledge_trigger.sh "$file" "$event"
done
```

### 2. Git フック による更新
```bash
# .git/hooks/post-commit
#!/bin/bash
cd /home/aicompany/ai_co
changed_files=$(git diff --name-only HEAD~1 HEAD)
./scripts/update_knowledge_git.sh "$changed_files"
```

### 3. Cron による定期更新
```bash
# crontab 設定例
0 3 * * * cd /home/aicompany/ai_co && ./scripts/daily_knowledge_update.sh
0 */6 * * * cd /home/aicompany/ai_co && ai-knowledge evolve
0 9 * * 1 cd /home/aicompany/ai_co && ./scripts/weekly_knowledge_report.sh
0 0 1 * * cd /home/aicompany/ai_co && ./scripts/monthly_knowledge_archive.sh
```

### 4. AI タスク による更新
```bash
# Elders Guildシステム経由での更新
ai-send "ナレッジベースを更新してください：新機能XXXが追加されました" --priority 8 --tags "knowledge,update"
```

## 更新検証ルール

### 自動検証項目
1. **リンク整合性**: ドキュメント間の相互参照が正しいか
2. **バージョン同期**: 全ドキュメントの最終更新日が同期しているか
3. **構造一貫性**: ツリー構造が他のドキュメントと一致しているか
4. **内容重複**: 同じ情報が複数箇所に重複記載されていないか

### 検証失敗時の対応
1. **警告ログ出力**: 不整合を詳細ログに記録
2. **Slack通知**: 管理者に即座通知
3. **自動修正試行**: 可能な場合は自動で修正
4. **手動介入要求**: 修正不可能な場合は手動対応を要求

## 緊急時の手動更新手順

### 1. 全ナレッジベース強制更新
```bash
cd /home/aicompany/ai_co
ai-knowledge consolidate --force
./scripts/validate_knowledge_integrity.sh
```

### 2. 特定ファイルのみ更新
```bash
./scripts/update_specific_knowledge.sh FEATURE_TREE.md "新機能XXX追加"
```

### 3. 障害時の復旧
```bash
# バックアップからの復旧
./scripts/restore_knowledge_backup.sh $(date -d "1 day ago" +%Y%m%d)
```

## 監視とアラート

### 監視項目
- ナレッジファイルの最終更新時刻
- 自動更新プロセスの実行状況
- 更新失敗回数
- ドキュメント間の整合性

### アラート条件
- 24時間以上更新されていない
- 自動更新が3回連続失敗
- 重要なドキュメント間で情報が矛盾
- ファイルサイズが異常に増減

## 今後の改善点

1. **機械学習による更新予測**: 過去のパターンから更新タイミングを予測
2. **差分更新の高度化**: 変更部分のみを効率的に更新
3. **多言語対応**: 英語版ナレッジベースの自動生成
4. **APIドキュメント自動生成**: コードコメントからAPI仕様を自動更新