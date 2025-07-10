# Google Drive API セットアップマニュアル

## 📋 概要
このマニュアルでは、Google Drive APIの設定方法を説明します。
承認済み画像を自動的にGoogle Driveにアップロードする機能を有効にするために必要です。

## 🔧 事前準備

### 1. Google Cloud Console でのプロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成、または既存のプロジェクトを選択
3. プロジェクト名: `image-upload-manager` (任意)

### 2. Google Drive API の有効化
1. Google Cloud Console で「APIとサービス」→「ライブラリ」
2. "Google Drive API" を検索
3. 「有効にする」をクリック

### 3. サービスアカウントの作成
1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「サービスアカウント」
3. サービスアカウント名: `image-upload-service`
4. 役割: `Editor` または `Drive File Access`

### 4. サービスアカウントキーの作成
1. 作成したサービスアカウントをクリック
2. 「キー」タブ→「キーを追加」→「新しいキーを作成」
3. キータイプ: `JSON`
4. ダウンロードされたJSONファイルを保存

## 📁 設定ファイルの配置

### 1. 認証情報の配置
```bash
# ダウンロードしたJSONファイルを以下に配置
cp path/to/downloaded-credentials.json /home/aicompany/ai_co/projects/image-upload-manager/config/google_credentials.json
```

### 2. 権限設定
```bash
chmod 600 /home/aicompany/ai_co/projects/image-upload-manager/config/google_credentials.json
```

## 🔧 Google Drive の設定

### 1. アップロード先フォルダの作成
1. Google Drive で新しいフォルダを作成
2. フォルダ名: `画像アップロード管理システム` (任意)
3. フォルダのIDをコピー（URLから取得）
   ```
   例: https://drive.google.com/drive/folders/1abcdefghijklmnopqrstuvwxyz
   フォルダID: 1abcdefghijklmnopqrstuvwxyz
   ```

### 2. サービスアカウントとの共有
1. 作成したフォルダを右クリック→「共有」
2. サービスアカウントのメールアドレスを追加
3. 権限: `編集者`
4. 「送信」をクリック

## ⚙️ アプリケーション設定

### 1. 環境変数の設定
```bash
# docker-compose.yml の環境変数を更新
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=1abcdefghijklmnopqrstuvwxyz  # 実際のフォルダIDに置き換え
GOOGLE_APPLICATION_CREDENTIALS=/app/config/google_credentials.json
```

### 2. Docker Compose の再起動
```bash
cd /home/aicompany/ai_co/projects/image-upload-manager
docker-compose down
docker-compose up -d
```

## 🧪 テスト

### 1. 接続テスト
```bash
# コンテナ内でPythonスクリプトを実行
docker exec -it image-upload-manager python -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# 認証情報の読み込み
credentials = service_account.Credentials.from_service_account_file(
    '/app/config/google_credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.file']
)

# Drive APIクライアント作成
service = build('drive', 'v3', credentials=credentials)

# フォルダ一覧取得テスト
results = service.files().list(q=\"mimeType='application/vnd.google-apps.folder'\").execute()
print('Google Drive接続成功!')
print('フォルダ一覧:', [f['name'] for f in results.get('files', [])])
"
```

### 2. アップロードテスト
1. 管理者画面で画像を承認
2. Google Driveの指定フォルダに画像が自動アップロードされることを確認

## 📂 フォルダ構成例

Google Drive 内の推奨フォルダ構成：
```
画像アップロード管理システム/
├── 2025/
│   ├── 01/  # 月別
│   │   ├── 顧客A/
│   │   │   ├── 身分証明書.jpg
│   │   │   ├── 住民票.jpg
│   │   │   └── ...
│   │   └── 顧客B/
│   └── 02/
└── archived/  # アーカイブ
```

## 🔒 セキュリティ注意事項

### 1. 認証情報の保護
- `google_credentials.json` は絶対に公開しない
- ファイル権限を適切に設定（600）
- バージョン管理システムに含めない

### 2. アクセス制御
- サービスアカウントには最小限の権限のみ付与
- 定期的にアクセスログを確認
- 不要になった認証情報は削除

## 🛠️ トラブルシューティング

### よくある問題

1. **認証エラー**
   ```
   google.auth.exceptions.DefaultCredentialsError
   ```
   - 認証情報ファイルのパスを確認
   - ファイルの権限を確認
   - JSON形式が正しいか確認

2. **権限エラー**
   ```
   googleapiclient.errors.HttpError: 403
   ```
   - Google Drive APIが有効になっているか確認
   - サービスアカウントがフォルダを共有されているか確認
   - 適切な権限（編集者）が付与されているか確認

3. **フォルダが見つからない**
   ```
   Folder not found
   ```
   - フォルダIDが正しいか確認
   - フォルダがサービスアカウントと共有されているか確認

### ログ確認
```bash
# アプリケーションログ
docker logs image-upload-manager

# Google Drive関連のログ
docker logs image-upload-manager 2>&1 | grep -i "drive\|google"
```

## ✅ チェックリスト

設定完了前に以下を確認してください：

- [ ] Google Cloud Console でプロジェクトを作成
- [ ] Google Drive API を有効化
- [ ] サービスアカウントを作成
- [ ] サービスアカウントキー（JSON）をダウンロード
- [ ] 認証情報を適切なパスに配置
- [ ] Google Drive でアップロード先フォルダを作成
- [ ] フォルダをサービスアカウントと共有
- [ ] 環境変数を設定
- [ ] Docker Compose を再起動
- [ ] 接続テストを実行
- [ ] アップロードテストを実行

## 📞 サポート

問題が解決しない場合は、以下の情報と併せてサポートにお問い合わせください：

- Google Cloud Console のプロジェクトID
- サービスアカウントのメールアドレス
- Google Drive フォルダID
- エラーメッセージの詳細
- アプリケーションログ