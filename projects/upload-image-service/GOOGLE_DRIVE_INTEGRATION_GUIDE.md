# Google Drive Integration Guide for Upload Image Service

## 概要
このガイドでは、提出セッションでアップロードされたファイルをGoogle Driveに自動保存する機能の実装方法を説明します。

## 実装フロー

### 1. Google Cloud Console設定

1. **プロジェクト作成**
   - [Google Cloud Console](https://console.cloud.google.com)にアクセス
   - 新規プロジェクトを作成（例: `upload-image-service`）

2. **Google Drive API有効化**
   ```
   APIs & Services > Enable APIs and Services > Google Drive API > Enable
   ```

3. **認証情報作成**
   - APIs & Services > Credentials > Create Credentials > Service Account
   - サービスアカウント名: `upload-service-drive`
   - ロール: なし（後で設定）
   - キーを作成（JSON形式）→ `credentials.json`として保存

4. **Google Driveフォルダ共有**
   - Google Driveで親フォルダを作成（例: `契約書類アップロード`）
   - サービスアカウントのメールアドレスに編集権限を付与

### 2. バックエンド実装

#### 必要なパッケージインストール
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

#### 環境変数設定（`.env`）
```env
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials.json
GOOGLE_DRIVE_PARENT_FOLDER_ID=1ABC...xyz  # 親フォルダのID
```

#### Google Driveサービスクラス作成
```python
# backend/app/services/google_drive_service.py

import os
import json
from typing import Optional, List, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

class GoogleDriveService:
    """Google Drive連携サービス"""
    
    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
        self.parent_folder_id = os.getenv('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        self.service = self._build_service()
    
    def _build_service(self):
        """Google Drive APIサービス構築"""
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    
    def create_session_folder(self, session_id: str, submitter_name: str) -> str:
        """セッション用フォルダ作成"""
        folder_name = f"[{session_id}]_{submitter_name}"
        
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.parent_folder_id]
        }
        
        try:
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
        except HttpError as error:
            print(f'フォルダ作成エラー: {error}')
            return None
    
    def upload_file(
        self, 
        file_path: str, 
        file_name: str,
        folder_id: str,
        mime_type: str = 'application/octet-stream'
    ) -> Optional[Dict]:
        """ファイルアップロード"""
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink'
            ).execute()
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
        except HttpError as error:
            print(f'ファイルアップロードエラー: {error}')
            return None
    
    def set_folder_permissions(self, folder_id: str, email: str) -> bool:
        """フォルダに特定ユーザーの閲覧権限を付与"""
        permission = {
            'type': 'user',
            'role': 'reader',
            'emailAddress': email
        }
        
        try:
            self.service.permissions().create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            return True
        except HttpError as error:
            print(f'権限設定エラー: {error}')
            return False
```

#### SubmissionServiceに統合
```python
# backend/app/services/submission_service.py に追加

from app.services.google_drive_service import GoogleDriveService

class SubmissionService:
    def __init__(self, db: Session):
        self.db = db
        self.drive_service = GoogleDriveService()
    
    async def create_session(
        self, 
        admin_id: str, 
        admin_name: str, 
        data: SubmissionSessionCreate
    ) -> SubmissionSessionResponse:
        """新規提出セッション作成（Google Driveフォルダ作成含む）"""
        
        # ... 既存のセッション作成コード ...
        
        # Google Driveフォルダ作成
        if self.drive_service:
            folder_id = self.drive_service.create_session_folder(
                session_id=session.id,
                submitter_name=session.submitter_name
            )
            
            if folder_id:
                # フォルダIDをセッションのメタデータに保存
                session.google_drive_folder_id = folder_id
                self.db.commit()
        
        return self._to_response(session)
    
    async def upload_file(
        self,
        session_url_key: str,
        file: UploadFile,
        upload_data: SubmissionUploadCreate
    ) -> SubmissionUploadResponse:
        """ファイルアップロード（Google Drive連携含む）"""
        
        # ... 既存のファイル保存コード ...
        
        # Google Driveへアップロード
        if self.drive_service and session.google_drive_folder_id:
            drive_result = self.drive_service.upload_file(
                file_path=file_path,
                file_name=file.filename,
                folder_id=session.google_drive_folder_id,
                mime_type=file.content_type
            )
            
            if drive_result:
                # Google DriveのリンクをDBに保存
                upload.google_drive_file_id = drive_result['id']
                upload.google_drive_view_link = drive_result['view_link']
                self.db.commit()
        
        return SubmissionUploadResponse.from_orm(upload)
```

### 3. データベーススキーマ更新

```python
# backend/app/models/submission.py に追加

class SubmissionSession(Base):
    # ... 既存のフィールド ...
    
    # Google Drive連携
    google_drive_folder_id = Column(String)
    google_drive_folder_link = Column(String)

class SubmissionUpload(Base):
    # ... 既存のフィールド ...
    
    # Google Drive連携
    google_drive_file_id = Column(String)
    google_drive_view_link = Column(String)
```

### 4. 管理画面での表示

管理画面（SessionDetailModal）にGoogle Driveリンクを表示：

```typescript
// Google Driveセクション追加
{session.google_drive_folder_id && (
  <div className="detail-section">
    <h3>Google Drive</h3>
    <div className="drive-info">
      <a 
        href={`https://drive.google.com/drive/folders/${session.google_drive_folder_id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="drive-link"
      >
        📁 Google Driveフォルダを開く
      </a>
    </div>
  </div>
)}
```

### 5. セキュリティ考慮事項

1. **認証情報の保護**
   - `credentials.json`は絶対にGitにコミットしない
   - 環境変数で管理する

2. **アクセス制限**
   - サービスアカウントには最小限の権限のみ付与
   - 特定のフォルダのみアクセス可能に設定

3. **エラーハンドリング**
   - Google Drive APIのエラーは適切にキャッチ
   - ローカル保存は維持（Google Driveは補助的）

### 6. 運用フロー

1. **セッション作成時**
   - 自動的に `[SessionID]_[提出者名]` フォルダ作成
   - 管理者にフォルダリンクを表示

2. **ファイルアップロード時**
   - ローカルとGoogle Drive両方に保存
   - 管理者画面でGoogle Driveリンク表示

3. **レビュー時**
   - 管理者はGoogle Drive上で直接ファイル確認可能
   - コメントや承認はシステム内で管理

### 7. 今後の拡張案

1. **自動フォルダ整理**
   - 月別/年別でフォルダを自動整理
   - 完了したセッションを自動アーカイブ

2. **権限管理強化**
   - 提出者にも読み取り専用権限を付与オプション
   - 期限切れ時に自動的にアクセス権限削除

3. **バックアップ連携**
   - 定期的にGoogle Driveからバックアップ取得
   - 災害復旧計画の一環として活用

## まとめ

この実装により、すべてのアップロードファイルが自動的にGoogle Driveに保存され、管理者は使い慣れたGoogle Driveインターフェースでファイルを確認できるようになります。