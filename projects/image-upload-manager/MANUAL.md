# 📸 画像アップロード管理システム - 使用マニュアル

## 🎯 システム概要

顧客が複数の画像をアップロードし、管理者が承認・却下を管理できるWebアプリケーションです。

### 主要機能
- 📸 **顧客機能**: 5-10種類の画像アップロード、進捗確認
- 👨‍💼 **管理者機能**: 画像確認、承認・却下、GoogleDrive連携
- 🔐 **セキュリティ**: Docker分離実行、ファイルサイズ制限
- ☁️ **クラウド連携**: GoogleDriveへの自動アップロード

---

## 🚀 セットアップ

### 1. システム要件
- Docker & Docker Compose
- 最小2GB RAM、5GB ディスク容量
- Google Drive API（オプション）

### 2. インストール
```bash
# プロジェクトディレクトリに移動
cd /home/aicompany/ai_co/projects/image-upload-manager

# Docker起動
docker-compose up -d

# 起動確認
docker-compose ps
```

### 3. 初回アクセス
- **システムURL**: http://localhost:5000
- **管理者ページ**: http://localhost:5000/admin
- **テスト顧客URL**: http://localhost:5000/customer/test-customer-001

---

## 👨‍💼 管理者操作

### 1. 顧客作成
1. http://localhost:5000/admin にアクセス
2. 「👤 顧客作成」をクリック
3. 顧客情報を入力
   - **顧客名**: 必須
   - **メール**: 任意
   - **電話番号**: 任意
4. 「✅ 顧客を作成」をクリック

### 2. 顧客URL送信
```
顧客専用URL例:
http://localhost:5000/customer/{顧客ID}

例: http://localhost:5000/customer/test-customer-001
```

### 3. 画像管理
1. 管理者ページで顧客一覧を確認
2. 「📁 詳細」から顧客の画像を確認
3. アップロード済み画像をクリックで表示
4. 「✅ 承認」または「❌ 却下」を選択
5. 必要に応じて管理者コメントを追加

### 4. ステータス管理
- **×** : 未アップロード
- **📤** : アップロード済み（確認待ち）
- **○** : 承認済み
- **×** : 却下（再アップロード可能）

---

## 👤 顧客操作

### 1. 画像アップロード
1. 管理者から送られたURLにアクセス
2. 各画像種類の「📁 ファイルを選択」をクリック
3. 画像ファイルを選択（JPG、PNG、GIF、最大16MB）
4. 自動的にアップロード開始
5. 進捗バーで完了を確認

### 2. ドラッグ&ドロップ
- ファイル選択エリアに画像をドラッグ&ドロップ
- 複数ファイルの同時アップロード対応

### 3. 進捗確認
- リアルタイムでアップロード状況を確認
- 管理者コメントの確認
- 却下の場合は再アップロード可能

---

## 📂 画像種類

### デフォルト設定（6種類）
1. **身分証明書** (identity_card)
2. **住民票** (residence_cert)  
3. **収入証明書** (income_proof)
4. **契約書** (contract)
5. **銀行明細** (bank_statement)
6. **その他書類** (other_document)

### カスタマイズ
```python
# app/models.py の ImageType を編集
class ImageType(Enum):
    # 新しい画像種類を追加
    NEW_DOCUMENT = "new_document"
```

---

## ☁️ Google Drive 連携

### 1. セットアップ
詳細は `config/google_drive_setup.md` を参照

#### 簡易手順
1. Google Cloud Console でプロジェクト作成
2. Google Drive API 有効化
3. サービスアカウント作成
4. 認証情報（JSON）をダウンロード
5. `config/google_credentials.json` に配置
6. Docker Compose 再起動

### 2. 設定ファイル
```yaml
# docker-compose.yml
environment:
  - GOOGLE_DRIVE_ENABLED=true
  - GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

### 3. フォルダ構成
```
Google Drive/
└── 画像アップロード管理システム/
    ├── 顧客A/
    │   ├── 身分証明書_20250709_120000_file.jpg
    │   └── 住民票_20250709_120100_file.jpg
    └── 顧客B/
        └── 契約書_20250709_120200_file.jpg
```

---

## 🔧 システム管理

### 1. ログ確認
```bash
# アプリケーションログ
docker logs image-upload-manager

# リアルタイム監視
docker logs -f image-upload-manager

# エラーログのみ
docker logs image-upload-manager 2>&1 | grep -i error
```

### 2. データベース管理
```bash
# データベースファイル確認
ls -la data/

# SQLiteコンソール
docker exec -it image-upload-manager sqlite3 /app/data/image_upload.db

# テーブル一覧
.tables

# 顧客一覧
SELECT * FROM customers;
```

### 3. バックアップ
```bash
# データベースバックアップ
cp data/image_upload.db data/backup_$(date +%Y%m%d).db

# アップロード画像バックアップ
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### 4. 復旧
```bash
# サービス停止
docker-compose down

# データ復旧
cp data/backup_20250709.db data/image_upload.db

# サービス再開
docker-compose up -d
```

---

## ⚙️ 設定・カスタマイズ

### 1. 基本設定
```python
# app/app.py
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大ファイルサイズ
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}   # 許可拡張子
```

### 2. 画像処理設定
```python
# resize_image() 関数
max_size = (1920, 1080)  # 最大解像度
quality = 85             # JPEG品質
```

### 3. セキュリティ設定
```python
# Docker Compose リソース制限
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

---

## 🛠️ トラブルシューティング

### よくある問題

#### 1. アップロードエラー
**症状**: ファイルアップロードに失敗する
**原因**: ファイルサイズ超過、対応形式外
**対処**: 
- ファイルサイズを16MB以下に調整
- JPG/PNG/GIF形式に変換
- ブラウザキャッシュクリア

#### 2. 画像が表示されない
**症状**: 管理者画面で画像が表示されない
**対処**:
```bash
# アップロードディレクトリ権限確認
ls -la uploads/

# Docker再起動
docker-compose restart
```

#### 3. データベースエラー
**症状**: 500エラーが頻発
**対処**:
```bash
# データベースファイル確認
ls -la data/image_upload.db

# 権限修正
chmod 664 data/image_upload.db

# コンテナ再作成
docker-compose down
docker-compose up -d
```

#### 4. Google Drive連携エラー
**症状**: 承認済み画像がGoogle Driveにアップロードされない
**対処**:
- 認証情報ファイルの確認
- フォルダ共有設定の確認
- APIキーの有効期限確認

### ログ分析

#### アプリケーションログ
```bash
# エラーログ抽出
docker logs image-upload-manager 2>&1 | grep -i "error\|exception\|failed"

# Google Drive関連ログ
docker logs image-upload-manager 2>&1 | grep -i "drive\|google"

# アップロード関連ログ
docker logs image-upload-manager 2>&1 | grep -i "upload"
```

#### システムリソース
```bash
# コンテナリソース使用量
docker stats image-upload-manager

# ディスク使用量
du -sh uploads/ data/
```

---

## 📈 運用・保守

### 1. 定期メンテナンス

#### 週次
- ログファイルのローテーション
- 一時ファイルのクリーンアップ
- システムリソース確認

#### 月次
- データベースバックアップ
- 不要な画像ファイル削除
- セキュリティアップデート

#### 年次
- Google Drive API認証更新
- システム全体のアップデート
- パフォーマンス最適化

### 2. 監視項目
- サーバーリソース（CPU、メモリ、ディスク）
- アップロード成功率
- 応答時間
- エラー発生率
- Google Drive使用量

### 3. スケーリング

#### 横スケール
```yaml
# docker-compose.yml
services:
  web:
    deploy:
      replicas: 3
  
  nginx:
    image: nginx
    # ロードバランサー設定
```

#### 縦スケール
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

---

## 🔒 セキュリティ

### 1. 基本対策
- Docker コンテナ分離
- ファイルサイズ制限
- 画像形式検証
- 自動画像圧縮

### 2. アクセス制御
- 顧客URLのUUID使用
- IPアドレス制限（オプション）
- レート制限

### 3. データ保護
- データベース暗号化
- Google Drive認証情報の保護
- ログの適切な管理

---

## 📞 サポート

### 技術サポート
- **ログ**: 詳細なエラーログを確認
- **環境**: OS、Docker版数、ブラウザ情報
- **再現手順**: 問題の発生手順を詳細に記録

### 緊急時対応
1. **サービス再起動**: `docker-compose restart`
2. **ログ確認**: エラー内容の特定
3. **バックアップ復旧**: 直近のバックアップから復旧
4. **一時的回避策**: 手動でのファイル処理

---

## 📝 更新履歴

### Version 1.0.0 (2025-07-09)
- 初回リリース
- 基本的な画像アップロード機能
- 管理者による承認・却下機能
- Google Drive連携機能
- Docker環境対応

### 今後の予定
- [ ] ユーザー認証機能
- [ ] 一括ダウンロード機能
- [ ] 画像プレビュー機能強化
- [ ] モバイル対応改善
- [ ] API拡張

---

**🏗️ 開発者**: Elders Guild Elder Hierarchy System  
**📧 サポート**: システム管理者まで  
**🔄 最終更新**: 2025年7月9日