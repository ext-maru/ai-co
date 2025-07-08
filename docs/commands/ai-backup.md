# ai-backup コマンド

AI Companyシステムの包括的なバックアップ・復元機能を提供するコマンドです。

## 概要

`ai-backup`は、システムファイル、データベース、ナレッジベース、エルダーズデータなどを安全にバックアップし、必要に応じて復元する機能を提供します。フル、増分、差分バックアップをサポートし、圧縮、暗号化、クラウドアップロード機能も備えています。

## 基本使用法

```bash
# フルバックアップ作成
ai-backup create --type full --output backup_20250706.tar.gz

# 増分バックアップ作成
ai-backup create --type incremental --base-backup backup_20250706.tar.gz --output incremental_20250706.tar.gz

# バックアップ復元
ai-backup restore backup_20250706.tar.gz --restore-path /restored_data

# バックアップ一覧表示
ai-backup list

# バックアップ検証
ai-backup verify backup_20250706.tar.gz
```

## アクション一覧

### create - バックアップ作成

```bash
ai-backup create [オプション]
```

**オプション:**
- `--type, -t`: バックアップタイプ (full, incremental, differential)
- `--output, -o`: 出力ファイルパス
- `--base-backup`: 増分バックアップのベースファイル
- `--since`: 変更日時以降のファイル (YYYY-MM-DD形式)
- `--compression`: 圧縮形式 (none, gzip, bzip2, xz)
- `--compression-level`: 圧縮レベル (1-9)

**例:**
```bash
# 高圧縮でフルバックアップ
ai-backup create --type full --compression xz --compression-level 9

# 昨日以降の変更を増分バックアップ
ai-backup create --type incremental --since 2025-07-05 --base-backup full_backup.tar.gz
```

### restore - バックアップ復元

```bash
ai-backup restore <バックアップファイル> [オプション]
```

**オプション:**
- `--restore-path`: 復元先パス
- `--verify`: 復元後の検証実行
- `--dry-run`: 実際の復元をせずシミュレーション

**例:**
```bash
# 指定パスに復元
ai-backup restore backup.tar.gz --restore-path /backup_restore

# ドライラン実行
ai-backup restore backup.tar.gz --dry-run
```

### list - バックアップ一覧

```bash
ai-backup list [オプション]
```

**オプション:**
- `--backup-dir`: 検索対象ディレクトリ
- `--verbose`: 詳細情報表示

### verify - バックアップ検証

```bash
ai-backup verify <バックアップファイル> [オプション]
```

**オプション:**
- `--check-integrity`: 整合性チェック
- `--check-content`: コンテンツチェック

### cleanup - 古いバックアップ削除

```bash
ai-backup cleanup [オプション]
```

**オプション:**
- `--keep-days`: 保持日数
- `--keep-count`: 保持ファイル数
- `--dry-run`: 削除対象表示のみ

### schedule - 定期バックアップ設定

```bash
ai-backup schedule [オプション]
```

**オプション:**
- `--schedule-type`: 実行頻度 (daily, weekly, monthly)
- `--time`: 実行時刻
- `--backup-type`: バックアップタイプ
- `--retention-days`: 保持日数

### config - 設定管理

```bash
ai-backup config [オプション]
```

**オプション:**
- `--config-file`: 設定ファイルパス
- `--set-option`: 設定項目変更
- `--show-config`: 現在の設定表示

### database - データベースバックアップ

```bash
ai-backup database [オプション]
```

**オプション:**
- `--databases`: 対象データベース一覧
- `--output-dir`: 出力ディレクトリ
- `--compress`: 圧縮有効化

### cloud - クラウドバックアップ

```bash
ai-backup cloud [オプション]
```

**オプション:**
- `--provider`: クラウドプロバイダー (s3, gcs, azure)
- `--bucket`: バケット名
- `--backup-file`: アップロード対象ファイル
- `--encrypt`: 暗号化有効化

### elders - エルダーズデータバックアップ

```bash
ai-backup elders [オプション]
```

**オプション:**
- `--include-knowledge-base`: ナレッジベース含有
- `--include-learning-sessions`: 学習セッション含有
- `--output`: 出力ファイル

### monitor - バックアップ監視

```bash
ai-backup monitor [オプション]
```

**オプション:**
- `--alert-threshold`: アラート閾値時間
- `--check-integrity`: 整合性チェック有効化
- `--send-notifications`: 通知送信有効化

## 設定ファイル

デフォルト設定は `config/backup_config.json` に保存されます。

```json
{
  "backup_dir": "/backups",
  "compression": "gzip",
  "compression_level": 6,
  "include_databases": true,
  "include_knowledge": true,
  "include_logs": false,
  "exclude_patterns": ["*.tmp", "*.log", "__pycache__", ".git"],
  "retention_days": 30,
  "encryption": false,
  "cloud_backup": false
}
```

## バックアップタイプ

### フルバックアップ (full)
- すべてのシステムファイルを包含
- 独立したリストア可能
- サイズが大きい

### 増分バックアップ (incremental)
- 前回バックアップからの変更分のみ
- ベースバックアップが必要
- サイズが小さい

### 差分バックアップ (differential)
- 最初のフルバックアップからの変更分
- フルバックアップとの組み合わせでリストア
- 増分より大きく、フルより小さい

## 圧縮オプション

| 形式 | 圧縮率 | 速度 | 特徴 |
|------|--------|------|------|
| none | なし | 最速 | 圧縮なし |
| gzip | 中程度 | 高速 | 標準的 |
| bzip2 | 高い | 中程度 | 高圧縮 |
| xz | 最高 | 低速 | 最高圧縮率 |

## 暗号化

AES256による暗号化をサポート:

```bash
ai-backup create --encrypt --encryption-key keyfile.key --encryption-algorithm AES256
```

## クラウド統合

主要クラウドプロバイダーとの統合:

- **AWS S3**: `--provider s3 --bucket my-backup-bucket`
- **Google Cloud Storage**: `--provider gcs --bucket my-backup-bucket`
- **Azure Blob**: `--provider azure --bucket my-backup-container`

## エルダーズ統合

エルダーズシステムのデータを特別にバックアップ:

```bash
# エルダーズ専用バックアップ
ai-backup elders --include-knowledge-base --include-learning-sessions

# ナレッジベースのみ
ai-backup elders --include-knowledge-base --output knowledge_backup.tar.gz
```

## 定期実行

cronによる自動バックアップ設定:

```bash
# 毎日午前2時に増分バックアップ
ai-backup schedule --schedule-type daily --time 02:00 --backup-type incremental

# 毎週日曜にフルバックアップ
ai-backup schedule --schedule-type weekly --time 03:00 --backup-type full
```

## 監視とアラート

バックアップの健全性を監視:

```bash
# 24時間以上バックアップがない場合アラート
ai-backup monitor --alert-threshold 24 --send-notifications
```

## エラー処理

- 部分的な失敗でも継続実行
- 詳細なエラーログ出力
- ロールバック機能
- 自動復旧試行

## パフォーマンス

- 並列処理による高速化
- 重複排除による効率化
- プログレス表示
- 詳細統計レポート

## セキュリティ

- 暗号化サポート
- アクセス権限チェック
- 監査ログ出力
- セキュアな一時ファイル管理

## トラブルシューティング

### よくある問題

1. **権限エラー**
   ```bash
   # 読み書き権限を確認
   ls -la /path/to/backup/dir
   ```

2. **ディスク容量不足**
   ```bash
   # 利用可能容量を確認
   df -h
   ```

3. **破損したバックアップ**
   ```bash
   # 整合性チェック実行
   ai-backup verify backup.tar.gz --check-integrity
   ```

## 関連コマンド

- `ai-status`: システム状態確認
- `ai-logs`: ログ確認
- `ai-debug`: デバッグ情報取得

## 注意事項

- 大容量ファイルのバックアップには時間がかかります
- 暗号化は追加のCPU負荷を発生させます
- クラウドアップロードには適切な認証情報が必要です
- 定期バックアップはシステムリソースを考慮して設定してください