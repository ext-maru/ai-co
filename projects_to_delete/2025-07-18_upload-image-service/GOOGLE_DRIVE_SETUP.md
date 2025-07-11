# Google Drive 連携設定ガイド

## 📋 必要な設定項目

1. **Google Cloud Console での設定**
2. **サービスアカウントキーの取得**
3. **Google Drive フォルダの準備**
4. **環境変数の設定**

## 🔧 詳細設定手順

### Step 1: Google Cloud Console でプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. 新しいプロジェクトを作成 または 既存プロジェクトを選択
   - プロジェクト名: `upload-image-service`

### Step 2: Google Drive API を有効化

```bash
# Google Cloud Console で以下のAPIを有効化:
# 1. Google Drive API
# 2. Google Sheets API (オプション)
```

1. 「APIとサービス」→「ライブラリ」
2. 「Google Drive API」を検索
3. 「有効にする」をクリック

### Step 3: サービスアカウント作成

1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「サービスアカウント」
3. サービスアカウント情報:
   - **名前**: `upload-service-drive`
   - **説明**: `Upload Image Service用Google Drive連携`
   - **ロール**: なし（後で設定）

### Step 4: サービスアカウントキー生成

1. 作成したサービスアカウントをクリック
2. 「キー」タブ → 「キーを追加」→「新しいキーを作成」
3. **JSON形式**を選択してダウンロード
4. ファイル名を `credentials.json` に変更

### Step 5: Google Drive でフォルダ準備

1. Google Drive にアクセス
2. 親フォルダを作成（例：`契約書類アップロード`）
3. フォルダを右クリック → 「共有」
4. サービスアカウントのメールアドレスを**編集者**として追加
   - サービスアカウントメール例: `upload-service-drive@project-id.iam.gserviceaccount.com`

### Step 6: フォルダIDの取得

1. Google Drive で作成したフォルダを開く
2. URLからフォルダIDをコピー
   ```
   https://drive.google.com/drive/folders/1ABC...xyz
   → フォルダID: 1ABC...xyz
   ```

## 🔑 環境変数設定

### バックエンドの`.env`ファイル

```bash
# Google Drive設定
GOOGLE_DRIVE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_DRIVE_PARENT_FOLDER_ID=1ABC...xyz
GOOGLE_DRIVE_ENABLED=true

# オプション設定
GOOGLE_DRIVE_FOLDER_NAME_FORMAT=[{session_id}]_{submitter_name}
GOOGLE_DRIVE_AUTO_CREATE_FOLDERS=true
```

### 本番環境での設定例

```bash
# /var/www/upload-image-service/backend/.env
GOOGLE_DRIVE_CREDENTIALS_PATH=/var/www/upload-image-service/credentials.json
GOOGLE_DRIVE_PARENT_FOLDER_ID=1ABC123def456GHI789jkl
GOOGLE_DRIVE_ENABLED=true
```

## 📁 ファイル配置

### 認証情報ファイルの配置

```bash
# 開発環境
/home/aicompany/ai_co/projects_to_delete/2025-07-18_upload-image-service/backend/credentials.json

# 本番環境
/var/www/upload-image-service/credentials.json
```

### 権限設定

```bash
# ファイル権限の設定
chmod 600 credentials.json
chown appuser:appuser credentials.json
```

## 🧪 テスト用設定スクリプト

```python
# test_google_drive.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

def test_google_drive_connection():
    """Google Drive接続テスト"""
    try:
        # 認証情報の読み込み
        credentials = service_account.Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/drive']
        )

        # Drive APIサービス構築
        service = build('drive', 'v3', credentials=credentials)

        # 親フォルダの確認
        parent_folder_id = os.getenv('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        folder = service.files().get(fileId=parent_folder_id).execute()

        print(f"✅ 接続成功: {folder['name']}")
        print(f"📁 フォルダID: {folder['id']}")

        # テストフォルダ作成
        test_folder = {
            'name': 'テスト_フォルダ',
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }

        created_folder = service.files().create(body=test_folder).execute()
        print(f"🆕 テストフォルダ作成: {created_folder['id']}")

        # テストフォルダ削除
        service.files().delete(fileId=created_folder['id']).execute()
        print("🗑️ テストフォルダ削除完了")

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    test_google_drive_connection()
```

## 🔒 セキュリティ設定

### 1. アクセス制限

```json
// credentials.json のサービスアカウントに最小権限のみ付与
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "upload-service-drive@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

### 2. フォルダ権限管理

```python
# 提出者に読み取り専用権限を付与
def share_folder_with_submitter(folder_id, email):
    permission = {
        'type': 'user',
        'role': 'reader',
        'emailAddress': email
    }
    service.permissions().create(
        fileId=folder_id,
        body=permission,
        sendNotificationEmail=False
    ).execute()
```

## 📊 フォルダ構造例

```
📁 契約書類アップロード (親フォルダ)
├── 📁 [session_001]_田中太郎
│   ├── 📄 住民票.pdf
│   ├── 📄 身分証明書.jpg
│   └── 📄 契約書.pdf
├── 📁 [session_002]_佐藤花子
│   ├── 📄 登記簿謄本.pdf
│   └── 📄 代表者身分証.jpg
└── 📁 アーカイブ
    └── 📁 2024年度
```

## ⚙️ 環境別設定

### 開発環境
```bash
GOOGLE_DRIVE_PARENT_FOLDER_ID=1DEV...folder  # 開発用フォルダ
GOOGLE_DRIVE_ENABLED=false  # 開発時は無効化
```

### 本番環境
```bash
GOOGLE_DRIVE_PARENT_FOLDER_ID=1PROD...folder  # 本番用フォルダ
GOOGLE_DRIVE_ENABLED=true
```

## 🔄 自動化機能

### 1. フォルダ自動作成
- セッション作成時に `[SessionID]_[提出者名]` フォルダを自動生成

### 2. ファイル自動アップロード
- アプリケーションでファイルアップロード時に自動的にGoogle Driveにも保存

### 3. 権限管理
- 提出者のメールアドレスが設定されている場合、自動的に読み取り権限を付与

これらの設定により、アップロードされたファイルは自動的にGoogle Driveにも保存され、管理者は使い慣れたGoogle Driveインターフェースでファイルを確認できます。
